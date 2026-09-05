package com.galacredit.app;

import android.content.Context;
import android.content.SharedPreferences;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.util.Base64;

import java.nio.charset.StandardCharsets;
import java.security.KeyStore;

import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;

/** 使用 Android Keystore 加密保存用户会话，避免令牌以明文落入普通偏好设置。 */
final class SecureSessionStore {
    private static final String KEYSTORE = "AndroidKeyStore";
    private static final String KEY_ALIAS = "galacredit.session.v1";
    private static final String PREFS = "galacredit_secure_session";
    private static final String TOKEN = "token";
    private static final String PHONE = "phone";
    private static final String TRANSFORMATION = "AES/GCM/NoPadding";

    private final SharedPreferences preferences;

    SecureSessionStore(Context context) {
        preferences = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    /**
     * 读取加密会话字段。
     *
     * :param key: 会话字段名
     * :return: 解密后的值；不存在或解密失败时返回空字符串
     */
    String read(String key) {
        String encoded = preferences.getString(key, "");
        if (encoded.isEmpty()) return "";
        try {
            byte[] packed = Base64.decode(encoded, Base64.NO_WRAP);
            if (packed.length <= 12) return "";
            byte[] iv = new byte[12];
            byte[] ciphertext = new byte[packed.length - iv.length];
            System.arraycopy(packed, 0, iv, 0, iv.length);
            System.arraycopy(packed, iv.length, ciphertext, 0, ciphertext.length);
            Cipher cipher = Cipher.getInstance(TRANSFORMATION);
            cipher.init(Cipher.DECRYPT_MODE, getKey(), new GCMParameterSpec(128, iv));
            return new String(cipher.doFinal(ciphertext), StandardCharsets.UTF_8);
        } catch (Exception ignored) {
            // 密钥被系统清除或数据损坏时清理失效会话，避免反复触发异常。
            preferences.edit().remove(key).apply();
            return "";
        }
    }

    /**
     * 加密写入会话字段。
     *
     * :param key: 会话字段名
     * :param value: 要保存的值
     * :return: 无
     */
    void write(String key, String value) {
        try {
            Cipher cipher = Cipher.getInstance(TRANSFORMATION);
            cipher.init(Cipher.ENCRYPT_MODE, getKey());
            byte[] iv = cipher.getIV();
            byte[] ciphertext = cipher.doFinal((value == null ? "" : value).getBytes(StandardCharsets.UTF_8));
            byte[] packed = new byte[iv.length + ciphertext.length];
            System.arraycopy(iv, 0, packed, 0, iv.length);
            System.arraycopy(ciphertext, 0, packed, iv.length, ciphertext.length);
            preferences.edit().putString(key, Base64.encodeToString(packed, Base64.NO_WRAP)).apply();
        } catch (Exception ignored) {
            // 无法使用 Keystore 时不保存会话，强制用户重新登录比降级明文存储更安全。
            preferences.edit().remove(key).apply();
        }
    }

    /**
     * 删除全部会话字段。
     *
     * :return: 无
     */
    void clear() {
        preferences.edit().clear().apply();
    }

    private SecretKey getKey() throws Exception {
        KeyStore keyStore = KeyStore.getInstance(KEYSTORE);
        keyStore.load(null);
        if (keyStore.containsAlias(KEY_ALIAS)) {
            return ((KeyStore.SecretKeyEntry) keyStore.getEntry(KEY_ALIAS, null)).getSecretKey();
        }
        KeyGenerator generator = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, KEYSTORE);
        generator.init(new KeyGenParameterSpec.Builder(
            KEY_ALIAS,
            KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT
        ).setBlockModes(KeyProperties.BLOCK_MODE_GCM)
            .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
            .setUserAuthenticationRequired(false)
            .build());
        return generator.generateKey();
    }
}
