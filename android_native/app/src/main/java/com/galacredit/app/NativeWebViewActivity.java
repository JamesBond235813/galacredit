package com.galacredit.app;

import android.app.Activity;
import android.Manifest;
import android.content.Intent;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.database.Cursor;
import android.graphics.Color;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.provider.Settings;
import android.provider.ContactsContract;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.CookieManager;
import android.webkit.GeolocationPermissions;
import android.webkit.WebChromeClient;
import android.webkit.JavascriptInterface;
import android.webkit.ValueCallback;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceError;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.view.ViewGroup;

import org.json.JSONArray;
import org.json.JSONObject;

import java.util.Locale;
import java.util.TimeZone;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;

/** 在应用内部承载尚未迁移为原生组件的业务页面，避免跳出到系统浏览器。 */
public final class NativeWebViewActivity extends Activity {
    private static final int LOCATION_PERMISSION_REQUEST = 401;
    private static final int CONTACT_PICKER_REQUEST = 402;
    private static final int FILE_CHOOSER_REQUEST = 403;
    private static final int SMS_PERMISSION_REQUEST = 404;
    private WebView webView;
    private boolean sessionInjected;
    private GeolocationPermissions.Callback pendingLocationCallback;
    private String pendingLocationOrigin;
    private ValueCallback<Uri[]> pendingFileCallback;
    private String pendingSmsCallback;
    private volatile boolean smsReviewInFlight;
    private boolean contactPickerInFlight;
    private Runnable smsTimeoutRunnable;
    private final Handler mainHandler = new Handler(Looper.getMainLooper());
    private final ExecutorService smsExecutor = Executors.newSingleThreadExecutor();
    private Future<?> smsFuture;
    private volatile boolean destroyed;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        destroyed = false;
        webView = new WebView(this);
        webView.setBackgroundColor(Color.rgb(255, 250, 242));
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setGeolocationEnabled(true);
        settings.setLoadWithOverviewMode(false);
        settings.setUseWideViewPort(false);
        // 业务页面只允许通过 HTTPS 访问，避免混合内容和本地文件扩大 WebView 攻击面。
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        settings.setAllowFileAccess(false);
        settings.setAllowFileAccessFromFileURLs(false);
        settings.setAllowUniversalAccessFromFileURLs(false);
        if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.O) {
            settings.setSafeBrowsingEnabled(true);
        }
        // H5 通过 navigator.geolocation 请求位置；原生容器必须把系统权限结果回传给 WebView。
        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onGeolocationPermissionsShowPrompt(String origin, GeolocationPermissions.Callback callback) {
                pendingLocationOrigin = origin;
                pendingLocationCallback = callback;
                if (hasLocationPermission()) {
                    callback.invoke(origin, true, false);
                } else {
                    requestPermissions(new String[]{
                        Manifest.permission.ACCESS_FINE_LOCATION,
                        Manifest.permission.ACCESS_COARSE_LOCATION
                    }, LOCATION_PERMISSION_REQUEST);
                }
            }

            @Override
            public boolean onShowFileChooser(WebView view, ValueCallback<Uri[]> callback, FileChooserParams params) {
                if (pendingFileCallback != null) pendingFileCallback.onReceiveValue(null);
                pendingFileCallback = callback;
                try {
                    Intent intent = params != null ? params.createIntent() : new Intent(Intent.ACTION_OPEN_DOCUMENT);
                    intent.addCategory(Intent.CATEGORY_OPENABLE);
                    intent.setType("image/*");
                    // 按页面请求决定单图或多图，避免人脸上传意外打开多选并造成额外内存占用。
                    intent.putExtra(Intent.EXTRA_ALLOW_MULTIPLE,
                        params != null && params.getMode() == WebChromeClient.FileChooserParams.MODE_OPEN_MULTIPLE);
                    startActivityForResult(intent, FILE_CHOOSER_REQUEST);
                    return true;
                } catch (Exception ignored) {
                    pendingFileCallback = null;
                    callback.onReceiveValue(null);
                    return false;
                }
            }
        });
        // 只打开系统联系人选择器，不申请 READ_CONTACTS，也不读取完整通讯录。
        webView.addJavascriptInterface(new ContactPickerBridge(), "GalaCreditContacts");
        // 风险页只通过受信任桥接获取已授权、已完成本地关键词过滤的最小短信集合。
        webView.addJavascriptInterface(new RiskBridge(), "GalaCreditRisk");
        // H5 退出时同步清理原生 Keystore 会话，避免下次启动恢复旧账号。
        webView.addJavascriptInterface(new SessionBridge(), "GalaCreditSession");
        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                return request == null || !allowNavigation(request.getUrl());
            }

            /**
             * Android 6/7 仍可能调用旧版 URL 回调；统一走同一套来源校验。
             *
             * :param view: 当前 WebView
             * :param url: 目标地址
             * :return: 已拦截时返回 True
             */
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, String url) {
                return url == null || !allowNavigation(Uri.parse(url));
            }

            @Override
            public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
                if (request != null && request.isForMainFrame()) {
                    showOfflineState();
                }
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                if (!sessionInjected) {
                    sessionInjected = true;
                    String token = new ApiClient(NativeWebViewActivity.this).token();
                    String riskTask = new ApiClient(NativeWebViewActivity.this).riskTask();
                    String script = "window.GalaCreditNativeInfo=" + buildNativeInfo() + ";"
                        + "localStorage.setItem('token'," + JSONObjectEscaper.quote(token) + ");"
                        + (riskTask.isEmpty() ? "" : "localStorage.setItem('galacredit_risk_task'," + JSONObjectEscaper.quote(riskTask) + ");");
                    view.evaluateJavascript(script, ignored -> view.reload());
                }
            }
        });
        setContentView(webView, new ViewGroup.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        webView.loadUrl(resolveInitialUrl(getIntent()));
    }

    @Override
    protected void onResume() {
        super.onResume();
        // 回到前台时恢复 WebView 的脚本计时器，避免验证码倒计时、桥接超时和页面异步任务永久停滞。
        if (webView != null && !destroyed) {
            webView.onResume();
            webView.resumeTimers();
            webView.evaluateJavascript("window.dispatchEvent(new Event('galacredit:resume'));", null);
        }
    }

    @Override
    protected void onPause() {
        // 切到后台时暂停网页脚本，减少无意义的网络轮询和后台功耗；原生权限回调仍由 Activity 生命周期接管。
        if (webView != null && !destroyed) {
            webView.onPause();
            webView.pauseTimers();
        }
        super.onPause();
    }

    /**
     * 只允许配置源站的 HTTPS 页面，并将电话链接交给系统拨号器。
     *
     * :param target: 待访问地址
     * :return: 允许 WebView 继续加载时返回 True
     */
    private boolean allowNavigation(Uri target) {
        if (target == null) return false;
        if ("tel".equalsIgnoreCase(target.getScheme())) {
            try {
                startActivity(new Intent(Intent.ACTION_DIAL, target));
            } catch (Exception ignored) {
                // 设备没有可用拨号器时保持页面可用，不让 WebView 崩溃。
            }
            return false;
        }
        if (!"https".equalsIgnoreCase(target.getScheme())) return false;
        Uri base = Uri.parse(AppConfig.WEB_BASE_URL);
        return base.getHost() != null
            && base.getHost().equalsIgnoreCase(target.getHost())
            && (base.getPort() == -1 || base.getPort() == target.getPort());
    }

    /**
     * 解析原生壳入口地址，并限制到配置的 HTTPS 源站。
     *
     * :param intent: 启动业务页的 Intent
     * :return: 可安全加载的完整 URL
     */
    private String resolveInitialUrl(Intent intent) {
        Uri base = Uri.parse(AppConfig.WEB_BASE_URL);
        String supplied = intent == null ? "" : intent.getStringExtra("url");
        if (supplied == null || supplied.trim().isEmpty()) {
            String path = intent == null ? "" : intent.getStringExtra("path");
            supplied = AppConfig.WEB_BASE_URL + (path == null || path.isEmpty() ? "/home" : path);
        }
        Uri target;
        try {
            target = Uri.parse(supplied);
        } catch (Exception ignored) {
            return AppConfig.WEB_BASE_URL + "/home";
        }
        if (!"https".equalsIgnoreCase(target.getScheme())
            || target.getHost() == null
            || base.getHost() == null
            || !base.getHost().equalsIgnoreCase(target.getHost())
            || (base.getPort() != -1 && base.getPort() != target.getPort())) {
            return AppConfig.WEB_BASE_URL + "/home";
        }
        return target.toString();
    }

    /** 显示可重试的离线状态，避免 WebView 白屏且用户无法判断发生了什么。 */
    private void showOfflineState() {
        LinearLayout fallback = new LinearLayout(this);
        fallback.setOrientation(LinearLayout.VERTICAL);
        fallback.setGravity(android.view.Gravity.CENTER);
        fallback.setPadding(48, 24, 48, 24);
        TextView message = new TextView(this);
        message.setText("Unable to load GalaCredit. Check your connection and try again.");
        message.setTextColor(Ui.TEXT);
        message.setTextSize(16);
        message.setGravity(android.view.Gravity.CENTER);
        fallback.addView(message, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        Button retry = Ui.primaryButton(this, "Try again");
        retry.setOnClickListener(view -> {
            setContentView(webView, new ViewGroup.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
            webView.reload();
        });
        LinearLayout.LayoutParams retryParams = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        retryParams.topMargin = 24;
        fallback.addView(retry, retryParams);
        setContentView(fallback, new ViewGroup.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
    }

    /**
     * 提供给 H5/UniApp 页面的一次性联系人选择桥接。
     *
     * :return: 无；结果通过 JavaScript 回调返回
     */
    private final class ContactPickerBridge {
        @JavascriptInterface
        public void pick(String requestId) {
            runOnUiThread(() -> {
                if (contactPickerInFlight) {
                    if (webView != null) {
                        webView.evaluateJavascript("window.__gcContactPickerReject && window.__gcContactPickerReject();", null);
                    }
                    return;
                }
                contactPickerInFlight = true;
                Intent intent = new Intent(Intent.ACTION_PICK, ContactsContract.CommonDataKinds.Phone.CONTENT_URI);
                try {
                    startActivityForResult(intent, CONTACT_PICKER_REQUEST);
                } catch (Exception ignored) {
                    contactPickerInFlight = false;
                    if (webView != null) {
                        webView.evaluateJavascript("window.__gcContactPickerReject && window.__gcContactPickerReject();", null);
                    }
                }
            });
        }
    }

    /**
     * 接收 H5/UniApp 的退出请求并清理原生会话。
     *
     * :return: 无；清理后回到原生登录页
     */
    private final class SessionBridge {
        @JavascriptInterface
        public String getRiskTask() {
            // 风控提交在后台线程完成，页面首次加载时可能尚未完成 localStorage 注入。
            return new ApiClient(NativeWebViewActivity.this).riskTask();
        }

        @JavascriptInterface
        public void logout() {
            runOnUiThread(() -> {
                clearWebViewSession(() -> {
                    new ApiClient(NativeWebViewActivity.this).logout();
                    Intent intent = new Intent(NativeWebViewActivity.this, MainActivity.class);
                    intent.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
                    startActivity(intent);
                    finish();
                });
            });
        }
    }

    /**
     * 清理 WebView 的会话、Cookie 和缓存，防止退出后恢复上一个用户的网页状态。
     *
     * :param onComplete: 清理完成后的回调
     * :return: 无
     */
    private void clearWebViewSession(Runnable onComplete) {
        if (webView == null) {
            onComplete.run();
            return;
        }
        webView.evaluateJavascript("localStorage.clear();sessionStorage.clear();", ignored -> {
            CookieManager cookies = CookieManager.getInstance();
            cookies.removeAllCookies(value -> {
                cookies.flush();
                webView.clearCache(true);
                webView.clearHistory();
                onComplete.run();
            });
        });
    }

    /**
     * 为受信任的 UniApp/H5 风险页提供一次性短信采集桥接。
     *
     * :return: 无；结果通过约定的 JavaScript 回调返回
     */
    private final class RiskBridge {
        /**
         * 返回不含原始设备标识的原生环境摘要，供共用页面识别 Android 壳。
         *
         * :return: JSON 格式的最小环境摘要
         */
        @JavascriptInterface
        public String getNativeInfo() {
            return buildNativeInfo().toString();
        }

        @JavascriptInterface
        public String getAppChannel() {
            // 页面层不能自行推断渠道；由原生包名返回当前构建渠道，供服务端授权审计使用。
            return getPackageName().endsWith(".internal") ? "internal" : "play";
        }

        @JavascriptInterface
        public void startSmsReview(String callbackName, boolean consentAccepted) {
            if (destroyed || !isSafeCallbackName(callbackName)) {
                return;
            }
            if (smsReviewInFlight) {
                deliverSmsResultTo(callbackName, true, "busy", new JSONArray(), 0, "SMS_REVIEW_BUSY");
                return;
            }
            smsReviewInFlight = true;
            pendingSmsCallback = callbackName;
            smsTimeoutRunnable = () -> {
                if (smsReviewInFlight) {
                    deliverSmsResult(false, "timeout", new JSONArray(), 0, "SMS_BRIDGE_TIMEOUT");
                }
            };
            mainHandler.postDelayed(smsTimeoutRunnable, 20000L);
            if (!consentAccepted) {
                deliverSmsResult(false, "consent_required", new JSONArray(), 0, "SMS_CONSENT_REQUIRED");
                return;
            }
            // manifest 声明只是构建配置，运行时仍需绑定 internal 包，防止错误包或重打包版本读取短信。
            if (!SmsCollector.isInternalChannel(NativeWebViewActivity.this) || !hasSmsPermissionDeclaration()) {
                deliverSmsResult(false, "not_declared", new JSONArray(), 0, "CHANNEL_OR_CONSENT");
                return;
            }
            if (SmsCollector.isPermissionGranted(NativeWebViewActivity.this)) {
                collectSmsInBackground();
                return;
            }
            runOnUiThread(() -> requestPermissions(new String[]{SmsCollector.permissionName()}, SMS_PERMISSION_REQUEST));
        }
    }

    /**
     * 构造供页面和服务端风控使用的 Android 环境摘要。
     *
     * 原始 Android ID 只在本地参与不可逆哈希，避免通过 WebView 或网络暴露原始标识。
     *
     * :return: 最小环境摘要
     */
    private JSONObject buildNativeInfo() {
        JSONObject info = new JSONObject();
        try {
            String rawAndroidId = Settings.Secure.getString(getContentResolver(), Settings.Secure.ANDROID_ID);
            info.put("platform", "android");
            info.put("app_channel", getPackageName().endsWith(".internal") ? "internal" : "play");
            info.put("source", "NATIVE_ANDROID");
            info.put("native_bridge", "GalaCreditNativeRisk");
            info.put("model", Build.MODEL == null ? "" : Build.MODEL);
            info.put("system", "Android " + (Build.VERSION.RELEASE == null ? "" : Build.VERSION.RELEASE));
            info.put("device_type", "phone");
            info.put("brand", Build.MANUFACTURER == null ? "" : Build.MANUFACTURER);
            info.put("language", Locale.getDefault().toLanguageTag());
            info.put("screen_width", getResources().getDisplayMetrics().widthPixels);
            info.put("screen_height", getResources().getDisplayMetrics().heightPixels);
            info.put("timezone", TimeZone.getDefault().getID());
            info.put("app_version", String.valueOf(readVersionCode()));
            info.put("device_fingerprint", DeviceFingerprint.hash(rawAndroidId, getPackageName()));
        } catch (Exception ignored) {
            // 环境摘要仅用于补充风控，构造失败时仍不影响登录和页面加载。
        }
        return info;
    }

    private long readVersionCode() {
        try {
            PackageInfo info = getPackageManager().getPackageInfo(getPackageName(), 0);
            return Build.VERSION.SDK_INT >= 28 ? info.getLongVersionCode() : info.versionCode;
        } catch (Exception ignored) {
            return 0L;
        }
    }

    private boolean hasSmsPermissionDeclaration() {
        try {
            android.content.pm.PackageInfo info = getPackageManager().getPackageInfo(getPackageName(), PackageManager.GET_PERMISSIONS);
            if (info.requestedPermissions == null) return false;
            for (String permission : info.requestedPermissions) {
                if (SmsCollector.permissionName().equals(permission)) return true;
            }
        } catch (Exception ignored) {
            // 权限清单读取失败时按安全默认值处理，避免 WebView 触发系统权限请求。
        }
        return false;
    }

    private boolean isSafeCallbackName(String callbackName) {
        return callbackName != null && callbackName.matches("^[A-Za-z_$][A-Za-z0-9_$]{0,80}$");
    }

    private void collectSmsInBackground() {
        final String callbackName = pendingSmsCallback;
        if (callbackName == null || destroyed) return;
        if (smsFuture != null && !smsFuture.isDone()) {
            return;
        }
        smsFuture = smsExecutor.submit(() -> {
            if (destroyed) return;
            SmsCollector.CollectionResult result = SmsCollector.collectWithStats(NativeWebViewActivity.this);
            if (destroyed) return;
            deliverSmsResult(true, "granted", result.messages, result.scannedCount, "OK");
        });
    }

    private void deliverSmsResult(boolean supported, String permission, JSONArray messages, int scannedCount, String reason) {
        final String callbackName = pendingSmsCallback;
        pendingSmsCallback = null;
        smsReviewInFlight = false;
        if (smsTimeoutRunnable != null) {
            mainHandler.removeCallbacks(smsTimeoutRunnable);
            smsTimeoutRunnable = null;
        }
        deliverSmsResultTo(callbackName, supported, permission, messages, scannedCount, reason);
    }

    private void deliverSmsResultTo(String callbackName, boolean supported, String permission, JSONArray messages, int scannedCount, String reason) {
        if (destroyed || callbackName == null || webView == null) return;
        try {
            JSONObject payload = new JSONObject();
            payload.put("supported", supported);
            payload.put("permission", permission);
            payload.put("scannedCount", scannedCount);
            payload.put("messages", messages == null ? new JSONArray() : messages);
            payload.put("reason", reason);
            String script = "window[" + JSONObjectEscaper.quote(callbackName) + "] && window[" + JSONObjectEscaper.quote(callbackName) + "](" + payload + ");";
            mainHandler.post(() -> {
                if (webView != null) webView.evaluateJavascript(script, null);
            });
        } catch (Exception ignored) {
            // 桥接序列化失败时不向页面注入不完整数据，页面会按无短信结果降级。
        }
    }

    private boolean hasLocationPermission() {
        return checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED
            || checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED;
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (destroyed) return;
        if (requestCode == LOCATION_PERMISSION_REQUEST && pendingLocationCallback != null) {
            boolean granted = hasLocationPermission();
            pendingLocationCallback.invoke(pendingLocationOrigin, granted, false);
            pendingLocationCallback = null;
            pendingLocationOrigin = null;
            return;
        }
        if (requestCode == SMS_PERMISSION_REQUEST) {
            if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                collectSmsInBackground();
            } else {
                deliverSmsResult(true, "denied", new JSONArray(), 0, "PERMISSION_DENIED");
            }
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == FILE_CHOOSER_REQUEST) {
            if (pendingFileCallback == null) return;
            Uri[] result = null;
            if (resultCode == RESULT_OK && data != null) {
                if (data.getClipData() != null) {
                    int count = data.getClipData().getItemCount();
                    result = new Uri[count];
                    for (int index = 0; index < count; index++) result[index] = data.getClipData().getItemAt(index).getUri();
                } else if (data.getData() != null) {
                    result = new Uri[]{data.getData()};
                }
            }
            pendingFileCallback.onReceiveValue(result);
            pendingFileCallback = null;
            return;
        }
        if (requestCode != CONTACT_PICKER_REQUEST) return;
        contactPickerInFlight = false;
        if (webView == null) return;
        if (resultCode != RESULT_OK || data == null || data.getData() == null) {
            webView.evaluateJavascript("window.__gcContactPickerReject && window.__gcContactPickerReject();", null);
            return;
        }
        String name = "";
        String phone = "";
        try (Cursor cursor = getContentResolver().query(
            data.getData(),
            new String[]{ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME, ContactsContract.CommonDataKinds.Phone.NUMBER},
            null,
            null,
            null
        )) {
            if (cursor != null && cursor.moveToFirst()) {
                name = cursor.getString(cursor.getColumnIndexOrThrow(ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME));
                phone = cursor.getString(cursor.getColumnIndexOrThrow(ContactsContract.CommonDataKinds.Phone.NUMBER));
            }
        } catch (Exception ignored) {
            // ROM 联系人 provider 差异不能阻塞贷款主流程。
        }
        String script = "window.__gcContactPickerResolve && window.__gcContactPickerResolve({name:" + JSONObjectEscaper.quote(name) + ",phone:" + JSONObjectEscaper.quote(phone) + "});";
        webView.evaluateJavascript(script, null);
    }

    @Override
    protected void onDestroy() {
        destroyed = true;
        // WebView 持有较大的渲染和 JS 资源，离开页面时主动释放，降低多次打开业务页的内存峰值。
        if (pendingFileCallback != null) {
            pendingFileCallback.onReceiveValue(null);
            pendingFileCallback = null;
        }
        contactPickerInFlight = false;
        if (smsTimeoutRunnable != null) {
            mainHandler.removeCallbacks(smsTimeoutRunnable);
            smsTimeoutRunnable = null;
        }
        if (pendingLocationCallback != null) {
            try {
                pendingLocationCallback.invoke(pendingLocationOrigin, false, false);
            } catch (Exception ignored) {
                // 页面已销毁时 WebView 回调可能已失效，不能让生命周期清理过程崩溃。
            }
            pendingLocationCallback = null;
            pendingLocationOrigin = null;
        }
        if (smsFuture != null) {
            smsFuture.cancel(true);
            smsFuture = null;
        }
        smsExecutor.shutdownNow();
        if (webView != null) {
            webView.stopLoading();
            webView.removeJavascriptInterface("GalaCreditContacts");
            webView.removeJavascriptInterface("GalaCreditSession");
            webView.removeJavascriptInterface("GalaCreditRisk");
            webView.destroy();
            webView = null;
        }
        pendingSmsCallback = null;
        smsReviewInFlight = false;
        super.onDestroy();
    }

    @Override
    public void onBackPressed() {
        if (webView != null && webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }

    private static final class JSONObjectEscaper {
        private JSONObjectEscaper() {
        }

        static String quote(String value) {
            return JSONObject.quote(value == null ? "" : value);
        }
    }
}
