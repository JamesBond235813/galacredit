package com.galacredit.app;

import android.content.Context;
import android.content.SharedPreferences;

import org.json.JSONArray;
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
    private static final String PREFS = "galacredit_mobile";
    private static final String TOKEN = "token";
    private static final String PHONE = "phone";

    private final SharedPreferences prefs;

    ApiClient(Context context) {
        this.prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    String token() {
        return prefs.getString(TOKEN, "");
    }

    String phone() {
        return prefs.getString(PHONE, "");
    }

    void saveSession(String token, String phone) {
        prefs.edit().putString(TOKEN, token == null ? "" : token).putString(PHONE, phone == null ? "" : phone).apply();
    }

    void logout() {
        prefs.edit().remove(TOKEN).remove(PHONE).apply();
    }

    JSONObject createCaptcha(String phone, int width) throws Exception {
        JSONObject body = new JSONObject();
        body.put("phone", requirePhone(phone));
        body.put("width", width);
        return post("/auth/slider-captcha/create", body, false);
    }

    JSONObject verifyCaptcha(String phone, String captchaId, float offsetX, int elapsedMs) throws Exception {
        JSONObject body = new JSONObject();
        body.put("phone", requirePhone(phone));
        body.put("captcha_id", captchaId);
        body.put("offset_x", offsetX);
        body.put("elapsed_ms", elapsedMs);
        return post("/auth/slider-captcha/verify", body, false);
    }

    JSONObject sendCode(String phone, String captchaTicket) throws Exception {
        JSONObject body = new JSONObject();
        body.put("phone", requirePhone(phone));
        body.put("captcha_ticket", captchaTicket);
        JSONObject result = post("/auth/send-code", body, false);
        ensureBusinessSuccess(result);
        return result;
    }

    JSONObject smsLogin(String phone, String smsCode, String inviteCode) throws Exception {
        JSONObject body = new JSONObject();
        String resolvedPhone = requirePhone(phone);
        body.put("phone", resolvedPhone);
        body.put("sms_code", smsCode);
        if (inviteCode != null && !inviteCode.trim().isEmpty()) {
            body.put("invite_code", inviteCode.trim());
        }
        JSONObject result = post("/auth/sms-login", body, false);
        ensureBusinessSuccess(result);
        saveSession(result.optString("access_token", ""), resolvedPhone);
        return result;
    }

    /** 校验统一响应中的业务状态，避免将 code/msg 错误响应误当作成功。
     *
     * :param result: 接口 JSON 响应
     * :return: None
     * :raises ApiException: 业务 code 表示失败时抛出
     */
    private static void ensureBusinessSuccess(JSONObject result) throws ApiException {
        if (result != null && result.has("code") && result.optInt("code", 200) != 200) {
            throw new ApiException(result.optInt("code", 400), result.optString("msg", "Request failed."));
        }
    }

    private String requirePhone(String value) throws ApiException {
        String resolved = value == null || value.trim().isEmpty() ? phone() : value.trim();
        if (resolved.isEmpty()) {
            throw new ApiException(0, "请输入正确的手机号");
        }
        return resolved;
    }

    JSONObject submitRiskSignals(String phone, JSONObject devicePayload) throws Exception {
        String resolvedPhone = phone == null || phone.trim().isEmpty() ? this.phone() : phone.trim();
        JSONObject body = new JSONObject();
        body.put("phone", resolvedPhone);
        body.put("accepted_user_agreement", true);
        body.put("accepted_personal_authorization", true);
        body.put("accepted_sensitive_collection", true);
        body.put("device_payload", devicePayload == null ? new JSONObject() : devicePayload);
        return post("/user/risk-signals", body, true);
    }

    JSONObject getUserInfo() throws Exception {
        return get("/user/info");
    }

    JSONObject getLoanStatus() throws Exception {
        return get("/loan/status");
    }

    JSONArray getProducts() throws Exception {
        return getArray("/loan/products");
    }

    JSONObject get(String path) throws Exception {
        return request("GET", path, null, true);
    }

    JSONArray getArray(String path) throws Exception {
        String text = requestText("GET", path, null, true);
        return text.isEmpty() ? new JSONArray() : new JSONArray(text);
    }

    private JSONObject post(String path, JSONObject body, boolean withToken) throws Exception {
        String text = requestText("POST", path, body, withToken);
        return text.isEmpty() ? new JSONObject() : new JSONObject(text);
    }

    private JSONObject request(String method, String path, JSONObject body, boolean withToken) throws Exception {
        String text = requestText(method, path, body, withToken);
        return text.isEmpty() ? new JSONObject() : new JSONObject(text);
    }

    private String requestText(String method, String path, JSONObject body, boolean withToken) throws Exception {
        URL url = new URL(AppConfig.API_BASE + path);
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setRequestMethod(method);
        conn.setConnectTimeout(15000);
        conn.setReadTimeout(20000);
        conn.setRequestProperty("Accept", "application/json");
        conn.setRequestProperty("client-id", "galacredit-android");
        if (withToken) {
            String token = token();
            if (!token.isEmpty()) {
                conn.setRequestProperty("Authorization", "Bearer " + token);
            }
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
        if (code < 200 || code >= 300) {
            JSONObject result = text.isEmpty() ? new JSONObject() : new JSONObject(text);
            String message = result.optString("msg", result.optString("detail", "请求失败：" + code));
            throw new ApiException(code, message);
        }
        return text;
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

    static String query(Map<String, String> params) throws Exception {
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
}
