package com.galacredit.app;

import android.Manifest;
import android.content.Context;
import android.content.pm.PackageManager;
import android.database.Cursor;
import android.net.Uri;
import android.provider.Telephony;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.TimeZone;
import java.util.regex.Pattern;

/** 受授权 Android 内部版本的短信最小化采集器。 */
final class SmsCollector {
    private static final int WINDOW_DAYS = 90;
    private static final int MAX_ROWS = 5000;
    private static final String KEYWORD_ASSET = "sms_keys20260602.csv";

    private SmsCollector() {
    }

    /**
     * 判断当前安装包是否声明并获得短信读取权限。
     *
     * :param context: Android 上下文
     * :return: 当前可以读取短信时返回 True
     */
    static boolean isPermissionGranted(Context context) {
        return isInternalChannel(context)
            && context.checkSelfPermission(permissionName()) == PackageManager.PERMISSION_GRANTED;
    }

    /**
     * 返回当前构建允许使用的短信权限名称。
     *
     * :return: Internal 构建返回 READ_SMS；Play 构建不会编译此真实实现
     */
    static String permissionName() {
        return Manifest.permission.READ_SMS;
    }

    /**
     * 判断当前上下文是否属于内部授权渠道。
     *
     * :param context: Android 上下文
     * :return: 包名以 .internal 结尾时返回 True
     */
    static boolean isInternalChannel(Context context) {
        return context != null && context.getPackageName().endsWith(".internal");
    }

    /**
     * 从最近90天短信中筛选命中关键词的最小字段。
     *
     * :param context: Android 上下文
     * :return: 仅含 address、body、type、time、read、keywords 的 JSON 数组
     */
    static JSONArray collect(Context context) {
        return collectWithStats(context).messages;
    }

    /**
     * 读取并过滤短信，同时返回扫描数量，供风险页面展示最小化采集结果。
     *
     * :param context: Android 上下文
     * :return: 过滤结果及扫描数量
     */
    static CollectionResult collectWithStats(Context context) {
        JSONArray result = new JSONArray();
        if (!isPermissionGranted(context)) {
            return new CollectionResult(result, 0);
        }
        long now = System.currentTimeMillis();
        long cutoff = now - WINDOW_DAYS * 24L * 60L * 60L * 1000L;
        List<KeywordPattern> patterns = loadPatterns(context);
        if (patterns.isEmpty()) {
            return new CollectionResult(result, 0);
        }
        Cursor cursor = null;
        int scanned = 0;
        try {
            Uri uri = Telephony.Sms.CONTENT_URI;
            String[] projection = {Telephony.Sms.ADDRESS, Telephony.Sms.BODY, Telephony.Sms.TYPE, Telephony.Sms.DATE, Telephony.Sms.READ};
            cursor = context.getContentResolver().query(uri, projection, Telephony.Sms.DATE + " >= ? AND " + Telephony.Sms.DATE + " <= ?", new String[]{String.valueOf(cutoff), String.valueOf(now)}, Telephony.Sms.DATE + " DESC");
            if (cursor == null) {
                return new CollectionResult(result, 0);
            }
            int addressIndex = cursor.getColumnIndex(Telephony.Sms.ADDRESS);
            int bodyIndex = cursor.getColumnIndex(Telephony.Sms.BODY);
            int typeIndex = cursor.getColumnIndex(Telephony.Sms.TYPE);
            int dateIndex = cursor.getColumnIndex(Telephony.Sms.DATE);
            int readIndex = cursor.getColumnIndex(Telephony.Sms.READ);
            while (cursor.moveToNext()) {
                if (scanned >= MAX_ROWS) {
                    break;
                }
                scanned++;
                long timestamp = dateIndex >= 0 ? cursor.getLong(dateIndex) : 0L;
                if (timestamp < cutoff || timestamp > now) {
                    continue;
                }
                String address = addressIndex >= 0 ? safe(cursor.getString(addressIndex)) : "";
                String body = bodyIndex >= 0 ? safe(cursor.getString(bodyIndex)) : "";
                String text = address + " " + body;
                JSONArray hits = matchedKeywords(text, patterns);
                if (hits.length() == 0) {
                    continue;
                }
                JSONObject item = new JSONObject();
                item.put("address", truncate(address, 120));
                item.put("body", truncate(body, 2000));
                item.put("type", typeIndex >= 0 && cursor.getInt(typeIndex) == 2 ? 2 : 1);
                item.put("time", formatTime(timestamp));
                item.put("read", readIndex >= 0 && cursor.getInt(readIndex) == 1 ? 1 : 0);
                item.put("keywords", hits);
                result.put(item);
            }
        } catch (Exception ignored) {
            // 权限、ROM 短信数据库或字段差异不能阻断登录和贷款主流程。
        } finally {
            if (cursor != null) {
                cursor.close();
            }
        }
        return new CollectionResult(result, scanned);
    }

    private static List<KeywordPattern> loadPatterns(Context context) {
        List<KeywordPattern> patterns = new ArrayList<>();
        Set<String> seen = new HashSet<>();
        try (InputStream input = context.getAssets().open(KEYWORD_ASSET);
             BufferedReader reader = new BufferedReader(new InputStreamReader(input, "UTF-8"))) {
            String line;
            while ((line = reader.readLine()) != null) {
                String keyword = line.trim().toLowerCase(Locale.ROOT);
                if (keyword.isEmpty() || !seen.add(keyword)) {
                    continue;
                }
                String escaped = Pattern.quote(keyword);
                Pattern pattern = keyword.matches("[a-z0-9][a-z0-9'-]*")
                    ? Pattern.compile("(?i)(?<![A-Za-z0-9_])" + escaped + "(?![A-Za-z0-9_])")
                    : Pattern.compile("(?i)" + escaped);
                patterns.add(new KeywordPattern(keyword, pattern));
            }
        } catch (IOException ignored) {
            // 关键词资源缺失时返回空集合，宁可不上报也不扩大短信采集范围。
        }
        return patterns;
    }

    private static JSONArray matchedKeywords(String text, List<KeywordPattern> patterns) {
        JSONArray hits = new JSONArray();
        for (KeywordPattern item : patterns) {
            if (item.pattern.matcher(text).find()) {
                hits.put(item.keyword);
            }
        }
        return hits;
    }

    private static String formatTime(long timestamp) {
        SimpleDateFormat format = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.ROOT);
        format.setTimeZone(TimeZone.getDefault());
        return format.format(new Date(timestamp));
    }

    private static String safe(String value) {
        return value == null ? "" : value.trim();
    }

    private static String truncate(String value, int maxLength) {
        return value.length() <= maxLength ? value : value.substring(0, maxLength);
    }

    private static final class KeywordPattern {
        private final String keyword;
        private final Pattern pattern;

        private KeywordPattern(String keyword, Pattern pattern) {
            this.keyword = keyword;
            this.pattern = pattern;
        }
    }

    static final class CollectionResult {
        final JSONArray messages;
        final int scannedCount;

        CollectionResult(JSONArray messages, int scannedCount) {
            this.messages = messages;
            this.scannedCount = scannedCount;
        }
    }
}
