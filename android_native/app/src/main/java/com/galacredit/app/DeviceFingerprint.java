package com.galacredit.app;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;

/** 生成不可逆的客户端设备摘要。 */
final class DeviceFingerprint {
    private DeviceFingerprint() {
    }

    /**
     * 生成 SHA-256 设备摘要。
     *
     * :param rawId: 系统设备标识
     * :param namespace: 应用命名空间，避免跨应用直接关联
     * :return: 十六进制摘要
     */
    static String hash(String rawId, String namespace) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] bytes = digest.digest((namespace + ":" + (rawId == null ? "" : rawId)).getBytes(StandardCharsets.UTF_8));
            StringBuilder result = new StringBuilder(bytes.length * 2);
            for (byte value : bytes) result.append(String.format("%02x", value & 0xff));
            return result.toString();
        } catch (Exception ignored) {
            return "";
        }
    }
}
