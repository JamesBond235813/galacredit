package com.juxin.xiaohebao.admin;

import android.content.Context;
import android.content.SharedPreferences;

import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.Map;

final class ApiClient {
    static final String API_BASE = AppConfig.API_BASE;
    private static final String PREFS = "xhb_admin_native";
    private static final String TOKEN = "token";

    private final SharedPreferences prefs;

    ApiClient(Context context) {
        this.prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    String token() {
        return prefs.getString(TOKEN, "");
    }

    void saveToken(String token) {
        prefs.edit().putString(TOKEN, token == null ? "" : token).apply();
    }

    void logout() {
        prefs.edit().remove(TOKEN).apply();
    }

    JSONObject login(String username, String password) throws Exception {
        JSONObject body = new JSONObject();
        body.put("username", username);
        body.put("password", password);
        body.put("client_type", "MOBILE");
        JSONObject result = request("POST", "/admin/login", null, body);
        saveToken(result.optString("access_token", ""));
        return result;
    }

    JSONObject get(String path, Map<String, String> params) throws Exception {
        return request("GET", path, params, null);
    }

    JSONObject post(String path, JSONObject body) throws Exception {
        return request("POST", path, null, body == null ? new JSONObject() : body);
    }

    JSONObject patch(String path, JSONObject body) throws Exception {
        return request("PATCH", path, null, body == null ? new JSONObject() : body);
    }

    private JSONObject request(String method, String path, Map<String, String> params, JSONObject body) throws Exception {
        URL url = new URL(API_BASE + path + query(params));
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setRequestMethod(method);
        conn.setConnectTimeout(15000);
        conn.setReadTimeout(20000);
        conn.setRequestProperty("Accept", "application/json");
        String token = token();
        if (!token.isEmpty()) {
            conn.setRequestProperty("Authorization", "Bearer " + token);
        }
        if (body != null) {
            byte[] bytes = body.toString().getBytes(StandardCharsets.UTF_8);
            conn.setRequestProperty("Content-Type", "application/json; charset=utf-8");
            conn.setDoOutput(true);
            try (OutputStream output = conn.getOutputStream()) {
                output.write(bytes);
            }
        }

        int code = conn.getResponseCode();
        String text = read(code >= 200 && code < 300 ? conn.getInputStream() : conn.getErrorStream());
        JSONObject result = text.isEmpty() ? new JSONObject() : new JSONObject(text);
        if (code < 200 || code >= 300) {
            String message = result.optString("msg", result.optString("detail", "请求失败：" + code));
            throw new ApiException(code, message);
        }
        return result;
    }

    private static String query(Map<String, String> params) throws Exception {
        if (params == null || params.isEmpty()) {
            return "";
        }
        StringBuilder builder = new StringBuilder("?");
        boolean first = true;
        for (Map.Entry<String, String> entry : params.entrySet()) {
            String value = entry.getValue();
            if (value == null || value.trim().isEmpty()) {
                continue;
            }
            if (!first) {
                builder.append('&');
            }
            first = false;
            builder.append(URLEncoder.encode(entry.getKey(), "UTF-8"));
            builder.append('=');
            builder.append(URLEncoder.encode(value, "UTF-8"));
        }
        return first ? "" : builder.toString();
    }

    private static String read(InputStream input) throws Exception {
        if (input == null) {
            return "";
        }
        StringBuilder builder = new StringBuilder();
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(input, StandardCharsets.UTF_8))) {
            String line;
            while ((line = reader.readLine()) != null) {
                builder.append(line);
            }
        }
        return builder.toString();
    }

    static final class ApiException extends Exception {
        final int status;

        ApiException(int status, String message) {
            super(message);
            this.status = status;
        }
    }
}
