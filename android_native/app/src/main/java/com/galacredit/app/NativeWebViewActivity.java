package com.galacredit.app;

import android.app.Activity;
import android.Manifest;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.os.Bundle;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.GeolocationPermissions;
import android.webkit.WebChromeClient;
import android.view.ViewGroup;

/** 在应用内部承载尚未迁移为原生组件的业务页面，避免跳出到系统浏览器。 */
public final class NativeWebViewActivity extends Activity {
    private static final int LOCATION_PERMISSION_REQUEST = 401;
    private WebView webView;
    private boolean sessionInjected;
    private GeolocationPermissions.Callback pendingLocationCallback;
    private String pendingLocationOrigin;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        webView = new WebView(this);
        webView.setBackgroundColor(Color.rgb(247, 251, 255));
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setGeolocationEnabled(true);
        settings.setLoadWithOverviewMode(false);
        settings.setUseWideViewPort(false);
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
        });
        webView.setWebViewClient(new WebViewClient() {
            @Override
            public void onPageFinished(WebView view, String url) {
                if (!sessionInjected) {
                    sessionInjected = true;
                    String token = getSharedPreferences("galacredit_mobile", MODE_PRIVATE).getString("token", "");
                    String script = "localStorage.setItem('token'," + JSONObjectEscaper.quote(token) + ");";
                    view.evaluateJavascript(script, ignored -> view.reload());
                }
            }
        });
        setContentView(webView, new ViewGroup.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        String path = getIntent().getStringExtra("path");
        webView.loadUrl(AppConfig.WEB_BASE_URL + (path == null || path.isEmpty() ? "/home" : path));
    }

    private boolean hasLocationPermission() {
        return checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED
            || checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED;
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode != LOCATION_PERMISSION_REQUEST || pendingLocationCallback == null) return;
        boolean granted = hasLocationPermission();
        pendingLocationCallback.invoke(pendingLocationOrigin, granted, false);
        pendingLocationCallback = null;
        pendingLocationOrigin = null;
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
            if (value == null) return "\"\"";
            return "\"" + value.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n") + "\"";
        }
    }
}
