package com.galacredit.app;

import android.app.Activity;
import android.app.AlertDialog;
import android.Manifest;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.content.pm.PackageInfo;
import android.graphics.Color;
import android.graphics.Typeface;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings.Secure;
import android.os.Handler;
import android.os.Looper;
import android.text.Editable;
import android.text.InputFilter;
import android.text.InputType;
import android.text.SpannableString;
import android.text.method.LinkMovementMethod;
import android.text.style.ClickableSpan;
import android.text.style.ForegroundColorSpan;
import android.text.style.StyleSpan;
import android.text.Spanned;
import android.text.TextWatcher;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.MotionEvent;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.drawable.ColorDrawable;
import android.graphics.drawable.GradientDrawable;
import android.app.Dialog;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.EditText;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.SeekBar;
import android.widget.TextView;
import android.widget.Toast;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.InputStream;
import java.io.IOException;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.TimeZone;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class MainActivity extends Activity {
    private final ExecutorService worker = Executors.newSingleThreadExecutor();
    private final Handler main = new Handler(Looper.getMainLooper());

    private ApiClient api;
    private LinearLayout root;
    private EditText phoneInput;
    private TextWatcher phoneInputWatcher;
    private EditText smsInput;
    private Button sendCodeButton;
    private Button signInButton;
    private TextView subtitleText;
    private TextView limitValueText;
    private TextView limitLabelText;
    private TextView actionButtonText;
    private LinearLayout serviceGrid;
    private LinearLayout loginCard;

    private JSONObject userInfo;
    private JSONObject loanStatus;
    private JSONArray products;
    private String phone = "";
    private String smsCode = "";
    private int cooldownSeconds = 0;
    private boolean consentAccepted = false;
    private ImageView loginLogo;
    private boolean smsConsentAccepted = false;
    private static final int SMS_PERMISSION_REQUEST = 712;
    private String pendingRiskPhone = "";
    private boolean pendingOpenHomeAfterRisk;
    private Runnable cooldownTicker;
    private Dialog activeCaptchaDialog;
    private Dialog activePolicyDialog;

    private String pendingCaptchaPhone = "";
    private String pendingCaptchaTicket = "";
    private String pendingLoginPhone = "";
    private String pendingLoginCode = "";

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        api = new ApiClient(this);
        if (api.token().isEmpty()) {
            showLogin();
        } else {
            loadSessionAndShowHome();
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        // 页面可能尚未完成登录视图初始化，恢复前台时不能假设按钮已经存在。
        if (cooldownSeconds > 0 && sendCodeButton != null) {
            sendCodeButton.setEnabled(false);
        }
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        // WebView 内退出后通过 CLEAR_TOP 回到已存在的登录壳，必须重新渲染登录界面。
        if (api != null && api.token().isEmpty()) {
            showLogin();
        }
    }

    @Override
    protected void onDestroy() {
        // 页面退出后释放后台线程，避免反复进入登录页或重建 Activity 时累积线程。
        if (cooldownTicker != null) {
            main.removeCallbacks(cooldownTicker);
            cooldownTicker = null;
        }
        if (activeCaptchaDialog != null && activeCaptchaDialog.isShowing()) {
            activeCaptchaDialog.dismiss();
        }
        activeCaptchaDialog = null;
        if (activePolicyDialog != null && activePolicyDialog.isShowing()) {
            activePolicyDialog.dismiss();
        }
        activePolicyDialog = null;
        worker.shutdownNow();
        super.onDestroy();
    }

    private void showLogin() {
        // 退出后重新登录必须重新取得短信单独同意，不能沿用上一个账号的内存状态。
        if (cooldownTicker != null) {
            main.removeCallbacks(cooldownTicker);
            cooldownTicker = null;
        }
        cooldownSeconds = 0;
        if (activeCaptchaDialog != null && activeCaptchaDialog.isShowing()) {
            activeCaptchaDialog.dismiss();
        }
        activeCaptchaDialog = null;
        if (activePolicyDialog != null && activePolicyDialog.isShowing()) {
            activePolicyDialog.dismiss();
        }
        activePolicyDialog = null;
        consentAccepted = false;
        smsConsentAccepted = false;
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(Ui.BACKGROUND);
        root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(Ui.dp(this, 20), Ui.dp(this, 50), Ui.dp(this, 20), Ui.dp(this, 28));
        android.graphics.drawable.GradientDrawable loginBackground = new android.graphics.drawable.GradientDrawable(
            android.graphics.drawable.GradientDrawable.Orientation.TL_BR,
            new int[]{Color.rgb(255, 248, 237), Color.rgb(246, 248, 251), Color.rgb(242, 248, 246)}
        );
        root.setBackground(loginBackground);
        scroll.addView(root, new ScrollView.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        setContentView(scroll);

        LinearLayout brand = new LinearLayout(this);
        brand.setOrientation(LinearLayout.HORIZONTAL);
        brand.setGravity(Gravity.CENTER_VERTICAL);
        LinearLayout.LayoutParams brandLp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        brandLp.gravity = Gravity.CENTER_HORIZONTAL;
        root.addView(brand, brandLp);

        ImageView logo = new ImageView(this);
        loginLogo = logo;
        logo.setImageResource(getResources().getIdentifier("galacredit_logo", "drawable", getPackageName()));
        logo.setScaleType(ImageView.ScaleType.CENTER_INSIDE);
        LinearLayout.LayoutParams logoLp = new LinearLayout.LayoutParams(Ui.dp(this, 72), Ui.dp(this, 72));
        logoLp.rightMargin = Ui.dp(this, 10);
        brand.addView(logo, logoLp);

        LinearLayout brandCopy = new LinearLayout(this);
        brandCopy.setOrientation(LinearLayout.VERTICAL);
        TextView headline = Ui.text(this, "GalaCredit", 40, Ui.TEXT, true);
        headline.setLetterSpacing(0f);
        headline.setIncludeFontPadding(false);
        brandCopy.addView(headline);
        TextView sub = Ui.text(this, "Credit when it matters", 15, Ui.MUTED, true);
        sub.setPadding(0, Ui.dp(this, 2), 0, 0);
        sub.setIncludeFontPadding(false);
        brandCopy.addView(sub);
        brand.addView(brandCopy);

        // 对齐 H5：品牌区与表单区之间保留足够呼吸空间，避免内容全部堆在屏幕顶部。
        root.addView(Ui.spacer(this, 54));

        loginCard = new LinearLayout(this);
        loginCard.setOrientation(LinearLayout.VERTICAL);
        loginCard.setPadding(Ui.dp(this, 14), Ui.dp(this, 14), Ui.dp(this, 14), Ui.dp(this, 14));
        loginCard.setBackground(Ui.rounded(Color.argb(245, 255, 255, 255), 16, Ui.BORDER, this));
        loginCard.setElevation(Ui.dp(this, 2));
        root.addView(loginCard, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        phoneInput = Ui.input(this, "000000000");
        phoneInput.setInputType(InputType.TYPE_CLASS_PHONE);
        phoneInput.setFilters(new InputFilter[]{new InputFilter.LengthFilter(12)});
        phoneInputWatcher = simpleWatcher(() -> {
            phone = normalizePhone(phoneInput.getText().toString());
            syncPhoneField(phone);
            if (limitLabelText != null) {
                String local = phone.startsWith("233") ? phone.substring(3) : phone;
                limitLabelText.setText(local.length() + "/9");
            }
        });
        phoneInput.addTextChangedListener(phoneInputWatcher);

        smsInput = Ui.input(this, "Enter the 6-digit code");
        smsInput.setInputType(InputType.TYPE_CLASS_NUMBER);
        smsInput.setFilters(new InputFilter[]{new InputFilter.LengthFilter(6)});

        LinearLayout phoneRow = new LinearLayout(this);
        phoneRow.setOrientation(LinearLayout.HORIZONTAL);
        phoneRow.setGravity(Gravity.CENTER_VERTICAL);
        TextView prefix = Ui.text(this, "🇬🇭  +233", 15, Ui.TEXT, true);
        prefix.setGravity(Gravity.CENTER_VERTICAL);
        phoneRow.addView(prefix, new LinearLayout.LayoutParams(Ui.dp(this, 86), Ui.dp(this, 48)));
        phoneRow.addView(phoneInput, new LinearLayout.LayoutParams(0, Ui.dp(this, 48), 1));
        limitLabelText = Ui.text(this, "0/9", 12, Ui.MUTED, false);
        phoneRow.addView(limitLabelText, new LinearLayout.LayoutParams(Ui.dp(this, 28), Ui.dp(this, 48)));
        phoneInput.setGravity(Gravity.CENTER_VERTICAL);
        limitLabelText.setGravity(Gravity.CENTER_VERTICAL | Gravity.END);
        loginCard.addView(phoneRow);
        loginCard.addView(Ui.spacer(this, 8));

        LinearLayout codeRow = new LinearLayout(this);
        codeRow.setOrientation(LinearLayout.HORIZONTAL);
        codeRow.setGravity(Gravity.CENTER_VERTICAL);
        codeRow.addView(smsInput, new LinearLayout.LayoutParams(0, Ui.dp(this, 48), 1));
        codeRow.addView(space(10));
        sendCodeButton = Ui.secondaryButton(this, "Send code");
        sendCodeButton.setOnClickListener(v -> requestCaptchaAndSendCode());
        codeRow.addView(sendCodeButton, new LinearLayout.LayoutParams(Ui.dp(this, 108), Ui.dp(this, 48)));
        loginCard.addView(codeRow);
        loginCard.addView(Ui.spacer(this, 10));

        LinearLayout agreementPanel = new LinearLayout(this);
        agreementPanel.setOrientation(LinearLayout.VERTICAL);
        agreementPanel.setPadding(Ui.dp(this, 14), Ui.dp(this, 14), Ui.dp(this, 14), Ui.dp(this, 12));
        agreementPanel.setBackground(Ui.rounded(Color.argb(158, 255, 255, 255), 18, Color.argb(174, 255, 255, 255), this));
        LinearLayout consentRow = new LinearLayout(this);
        consentRow.setOrientation(LinearLayout.HORIZONTAL);
        consentRow.setGravity(Gravity.TOP);
        CheckBox consent = new CheckBox(this);
        consent.setChecked(false);
        consent.setText("");
        consent.setButtonTintList(android.content.res.ColorStateList.valueOf(Ui.BLUE));
        consent.setOnCheckedChangeListener((buttonView, isChecked) -> consentAccepted = isChecked);
        TextView consentText = Ui.text(this, "", 12, Ui.TEXT, false);
        consentText.setText(buildConsentSentence());
        consentText.setLineSpacing(0f, 1.2f);
        consentText.setPadding(0, 0, 0, Ui.dp(this, 4));
        consentText.setIncludeFontPadding(true);
        consentText.setMovementMethod(LinkMovementMethod.getInstance());
        consentText.setHighlightColor(Color.TRANSPARENT);
        consentRow.addView(consent, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        consentRow.addView(consentText, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        agreementPanel.addView(consentRow);
        TextView legalNote = Ui.text(this, "Sensitive device permissions are requested only when needed for risk review.", 12, Ui.MUTED, false);
        legalNote.setPadding(Ui.dp(this, 32), Ui.dp(this, 12), 0, 0);
        legalNote.setLineSpacing(0f, 1.1f);
        agreementPanel.addView(legalNote);
        LinearLayout.LayoutParams agreementLp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        agreementLp.topMargin = Ui.dp(this, 16);
        root.addView(agreementPanel, agreementLp);

        // 内部授权版才展示短信授权开关；Google Play 构建不声明该权限，也不会诱导用户授权。
        if (hasSmsPermissionDeclaration()) {
            CheckBox smsConsent = new CheckBox(this);
            smsConsent.setText("I allow an optional 90-day SMS risk review. Only messages matching the published keywords are uploaded.");
            smsConsent.setTextColor(Ui.MUTED);
            smsConsent.setTextSize(12);
            smsConsent.setButtonTintList(android.content.res.ColorStateList.valueOf(Ui.BLUE));
            smsConsent.setOnCheckedChangeListener((buttonView, isChecked) -> smsConsentAccepted = isChecked);
            LinearLayout.LayoutParams smsConsentLp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
            smsConsentLp.topMargin = Ui.dp(this, 10);
            root.addView(smsConsent, smsConsentLp);
        }

        signInButton = Ui.primaryButton(this, "Sign In");
        signInButton.setOnClickListener(v -> submitLogin());
        LinearLayout.LayoutParams signInLp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, Ui.dp(this, 50));
        signInLp.topMargin = Ui.dp(this, 18);
        root.addView(signInButton, signInLp);
    }

    private SpannableString buildConsentSentence() {
        String sentence = "I agree to GalaCredit's User Agreement, Privacy Policy and Personal Data Authorization.";
        SpannableString spannable = new SpannableString(sentence);
        applyLinkSpan(spannable, "User Agreement", () -> openPolicyDocument("User Agreement", "/user-agreement.txt"));
        applyLinkSpan(spannable, "Privacy Policy", () -> openPolicyDocument("Privacy Policy", "/personal-info-authorization.txt"));
        applyLinkSpan(spannable, "Personal Data Authorization", () -> openPolicyDocument("Personal Data Authorization", "/personal-info-authorization.txt"));
        return spannable;
    }

    private void applyLinkSpan(SpannableString spannable, String label, Runnable action) {
        int start = spannable.toString().indexOf(label);
        if (start < 0) {
            return;
        }
        int end = start + label.length();
        spannable.setSpan(new ClickableSpan() {
            @Override
            public void onClick(View widget) {
                action.run();
            }
        }, start, end, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
        spannable.setSpan(new ForegroundColorSpan(Ui.BLUE), start, end, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
        spannable.setSpan(new StyleSpan(Typeface.BOLD), start, end, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
    }

    private void openPolicyDocument(String title, String path) {
        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setPadding(Ui.dp(this, 4), Ui.dp(this, 4), Ui.dp(this, 4), Ui.dp(this, 4));
        TextView heading = Ui.text(this, title, 20, Ui.TEXT, true);
        heading.setPadding(0, 0, 0, Ui.dp(this, 10));
        panel.addView(heading);
        TextView content = Ui.text(this, "Loading...", 13, Ui.MUTED, false);
        content.setLineSpacing(0f, 1.5f);
        content.setMovementMethod(android.text.method.ScrollingMovementMethod.getInstance());
        panel.addView(content, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, Ui.dp(this, 420)));
        AlertDialog dialog = new AlertDialog.Builder(this)
            .setView(panel)
            .setPositiveButton("Close", null)
            .create();
        activePolicyDialog = dialog;
        dialog.setOnDismissListener(ignored -> {
            if (activePolicyDialog == dialog) activePolicyDialog = null;
        });
        dialog.show();
        worker.execute(() -> {
            try {
                URL url = new URL(AppConfig.WEB_BASE_URL + path);
                HttpURLConnection connection = (HttpURLConnection) url.openConnection();
                connection.setConnectTimeout(8000);
                connection.setReadTimeout(10000);
                connection.setInstanceFollowRedirects(false);
                connection.setRequestProperty("Accept", "text/plain,text/*;q=0.9,*/*;q=0.1");
                int responseCode = connection.getResponseCode();
                if (responseCode < 200 || responseCode >= 300) {
                    throw new IOException("Policy request failed: " + responseCode);
                }
                String text;
                try (InputStream input = connection.getInputStream()) {
                    byte[] buffer = new byte[8192];
                    StringBuilder builder = new StringBuilder();
                    int read;
                    while ((read = input.read(buffer)) != -1) {
                        builder.append(new String(buffer, 0, read, StandardCharsets.UTF_8));
                    }
                    text = builder.toString();
                } finally {
                    connection.disconnect();
                }
                String finalText = text;
                main.post(() -> {
                    if (!isFinishing() && (Build.VERSION.SDK_INT < 17 || !isDestroyed())) content.setText(finalText);
                });
            } catch (Exception error) {
                main.post(() -> {
                    if (!isFinishing() && (Build.VERSION.SDK_INT < 17 || !isDestroyed())) content.setText(title + " could not be loaded. Please try again later.");
                });
            }
        });
    }

    private void requestCaptchaAndSendCode() {
        String normalized = normalizePhone(phoneInput.getText().toString());
        if (!isValidPhone(normalized)) {
            toast("Enter a valid mobile number.");
            return;
        }
        if (!consentAccepted) {
            toast("Accept the agreements to continue.");
            return;
        }
        phone = normalized;
        showCaptchaDialog();
    }

    private void showCaptchaDialog() {
        if (activeCaptchaDialog != null && activeCaptchaDialog.isShowing()) {
            return;
        }
        pendingCaptchaTicket = "";
        pendingCaptchaPhone = "";
        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setPadding(Ui.dp(this, 20), Ui.dp(this, 20), Ui.dp(this, 20), Ui.dp(this, 16));
        panel.setBackground(Ui.rounded(Color.rgb(255, 248, 237), 18, Ui.BORDER, this));
        TextView title = Ui.text(this, "Complete the security check", 18, Ui.TEXT, true);
        TextView desc = Ui.text(this, "Slide to the end to verify the phone number before we send the code.", 13, Ui.MUTED, false);
        desc.setLineSpacing(0f, 1.15f);
        desc.setPadding(0, Ui.dp(this, 6), 0, Ui.dp(this, 12));
        panel.addView(title);
        panel.addView(desc);
        TextView hint = Ui.text(this, "Slide right to verify", 13, Ui.BLUE, true);
        GalaSlider slider = new GalaSlider(this);
        panel.addView(slider, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, Ui.dp(this, 54)));
        panel.addView(Ui.spacer(this, 8));
        panel.addView(hint);
        TextView cancel = Ui.text(this, "Cancel", 14, Ui.BLUE, true);
        cancel.setGravity(Gravity.CENTER);
        LinearLayout.LayoutParams cancelLp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, Ui.dp(this, 42));
        cancelLp.topMargin = Ui.dp(this, 8);
        panel.addView(cancel, cancelLp);
        Dialog dialog = new Dialog(this);
        activeCaptchaDialog = dialog;
        dialog.requestWindowFeature(android.view.Window.FEATURE_NO_TITLE);
        dialog.setContentView(panel);
        dialog.setCancelable(true);
        slider.setEnabled(false);
        slider.setListener((progress, finished) -> {
            if (finished) hint.setText("Verifying...");
        });
        cancel.setOnClickListener(v -> {
            dialog.dismiss();
            if (activeCaptchaDialog == dialog) activeCaptchaDialog = null;
        });
        dialog.setOnDismissListener(ignored -> {
            if (activeCaptchaDialog == dialog) activeCaptchaDialog = null;
        });
        dialog.show();
        if (dialog.getWindow() != null) {
            dialog.getWindow().setBackgroundDrawable(new ColorDrawable(Color.TRANSPARENT));
            dialog.getWindow().setLayout((int) (getResources().getDisplayMetrics().widthPixels * 0.86f), ViewGroup.LayoutParams.WRAP_CONTENT);
        }
        slider.post(() -> prepareCaptchaChallenge(dialog, slider, hint));
    }

    private void prepareCaptchaChallenge(Dialog dialog, GalaSlider slider, TextView hint) {
        worker.execute(() -> {
            try {
                int width = Math.max(Math.min(slider.getWidth(), Ui.dp(this, 360)), Ui.dp(this, 280));
                JSONObject captcha = api.createCaptcha(phone, width);
                long readyAt = System.currentTimeMillis();
                main.post(() -> {
                    if (!dialog.isShowing()) return;
                    hint.setText("Slide right to verify");
                    slider.setEnabled(true);
                    slider.setListener((progress, finished) -> {
                        hint.setText(finished ? "Verifying..." : "Slide right to verify");
                        if (finished) performCaptchaVerification(dialog, captcha, readyAt);
                    });
                });
            } catch (Exception error) {
                main.post(() -> {
                    if (!dialog.isShowing()) return;
                    hint.setText("Security check is unavailable. Please try again.");
                    toast("Security check is unavailable. Please try again.");
                });
            }
        });
    }

    private void performCaptchaVerification(Dialog dialog, JSONObject captcha, long startedAt) {
        worker.execute(() -> {
            try {
                String captchaId = captcha.optString("captcha_id", "");
                int minElapsed = captcha.optInt("min_elapsed_ms", 1200);
                long elapsed = System.currentTimeMillis() - startedAt;
                if (elapsed < minElapsed) {
                    main.post(() -> toast("Please slide more slowly and try again."));
                    return;
                }
                int width = captcha.optInt("width", Ui.dp(this, 280));
                float offsetX = Math.max(width - Math.max(captcha.optInt("block_size", 44), 44), 0);
                JSONObject verify = api.verifyCaptcha(phone, captchaId, offsetX, (int) elapsed);
                pendingCaptchaTicket = verify.optString("captcha_ticket", "");
                pendingCaptchaPhone = phone;
                if (pendingCaptchaTicket.isEmpty()) {
                    throw new IllegalStateException("Security check could not be completed.");
                }
                main.post(() -> {
                    if (!dialog.isShowing() || isFinishing() || (Build.VERSION.SDK_INT >= 17 && isDestroyed())) return;
                    dialog.dismiss();
                    sendVerificationCode();
                });
            } catch (Exception error) {
                main.post(() -> {
                    if (!dialog.isShowing() || isFinishing() || (Build.VERSION.SDK_INT >= 17 && isDestroyed())) return;
                    dialog.dismiss();
                    toast("Security check failed. Please try again.");
                });
            }
        });
    }

    private void sendVerificationCode() {
        if (pendingCaptchaTicket.isEmpty()) {
            toast("Complete the security check before requesting a code.");
            return;
        }
        sendCodeButton.setEnabled(false);
        worker.execute(() -> {
            try {
                JSONObject result = api.sendCode(pendingCaptchaPhone, pendingCaptchaTicket);
                int cooldown = result.optInt("cooldown_seconds", 60);
                main.post(() -> {
                    toast("Verification code sent.");
                    startCooldown(cooldown);
                });
            } catch (Exception error) {
                main.post(() -> {
                    toast("Unable to send the verification code. Please try again.");
                    if (sendCodeButton != null) sendCodeButton.setEnabled(true);
                });
            }
        });
    }

    private void submitLogin() {
        String normalized = normalizePhone(phoneInput.getText().toString());
        String code = smsInput.getText().toString().trim();
        if (!isValidPhone(normalized)) {
            toast("Enter a valid mobile number.");
            return;
        }
        if (code.length() != 6) {
            toast("Enter the 6-digit verification code.");
            return;
        }
        if (!consentAccepted) {
            toast("Accept the agreements to continue.");
            return;
        }
        signInButton.setEnabled(false);
        pendingLoginPhone = normalized;
        pendingLoginCode = code;
        performLogin(normalized, code);
    }

    private void performLogin(String normalized, String code) {
        worker.execute(() -> {
            try {
                api.smsLogin(normalized, code, null);
                // 风险信号补传不阻断登录；短信读取必须在主线程取得系统授权后再执行。
                pendingRiskPhone = normalized;
                pendingOpenHomeAfterRisk = true;
                main.post(this::requestRiskCollection);
            } catch (Exception error) {
                main.post(() -> {
                    signInButton.setEnabled(true);
                    toast("Sign in failed. Check your verification code and try again.");
                });
            }
        });
    }

    private boolean hasSmsPermissionDeclaration() {
        try {
            PackageInfo info = getPackageManager().getPackageInfo(getPackageName(), PackageManager.GET_PERMISSIONS);
            if (info.requestedPermissions == null) return false;
            for (String permission : info.requestedPermissions) {
                if (SmsCollector.permissionName().equals(permission)) return true;
            }
        } catch (Exception ignored) {
            // 无法读取包权限时按 Google Play 安全默认值处理。
        }
        return false;
    }

    private void requestRiskCollection() {
        if (!SmsCollector.isInternalChannel(this) || !hasSmsPermissionDeclaration() || !smsConsentAccepted) {
            submitRiskSignalsInBackground(false);
            openHomeAfterRiskPermission();
            return;
        }
        if (SmsCollector.isPermissionGranted(this)) {
            submitRiskSignalsInBackground(true);
            openHomeAfterRiskPermission();
            return;
        }
        requestPermissions(new String[]{SmsCollector.permissionName()}, SMS_PERMISSION_REQUEST);
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode != SMS_PERMISSION_REQUEST) return;
        submitRiskSignalsInBackground(grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED);
        openHomeAfterRiskPermission();
    }

    /**
     * 确保系统敏感权限弹窗结束后再切换到业务 WebView。
     *
     * :return: 无
     */
    private void openHomeAfterRiskPermission() {
        if (!pendingOpenHomeAfterRisk) return;
        pendingOpenHomeAfterRisk = false;
        loadSessionAndShowHome();
    }

    private void submitRiskSignalsInBackground(boolean includeSms) {
        final String riskPhone = pendingRiskPhone;
        final String sessionToken = api.token();
        worker.execute(() -> {
            try {
                JSONObject result = api.submitRiskSignals(riskPhone, buildRiskPayload(includeSms));
                // 用户可能在弱网请求完成前退出；不把旧账号的任务摘要写回新会话。
                if (!sessionToken.isEmpty() && sessionToken.equals(api.token()) && riskPhone.equals(api.phone())) {
                    api.saveRiskTask(result);
                }
            } catch (Exception ignored) {
                // 风控数据补传失败不影响已经完成的登录会话。
            }
        });
    }

    private void loadSessionAndShowHome() {
        worker.execute(() -> {
            try {
                userInfo = api.getUserInfo();
                loanStatus = api.getLoanStatus();
                products = api.getProducts();
                // 登录后的正式首页以 H5 为唯一视觉与交互来源，仍在 App 内 WebView 打开，避免落到旧的原生占位首页。
                main.post(() -> openUrl(AppConfig.WEB_BASE_URL + "/home"));
            } catch (Exception error) {
                // 弱网或服务端短暂不可用时保留本地会话，给用户重试机会；只有明确的 401 才清除登录态。
                main.post(() -> {
                    if (isFinishing() || (Build.VERSION.SDK_INT >= 17 && isDestroyed())) return;
                    if (error instanceof ApiException && ((ApiException) error).statusCode == 401) {
                        api.logout();
                        showLogin();
                        return;
                    }
                    showSessionLoadError();
                });
            }
        });
    }

    /** 显示会话数据加载失败页面，避免弱网时把仍有效的用户强制踢回登录页。
     *
     * :return: 无
     */
    private void showSessionLoadError() {
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(Ui.BACKGROUND);
        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setGravity(Gravity.CENTER_HORIZONTAL);
        panel.setPadding(Ui.dp(this, 28), Ui.dp(this, 96), Ui.dp(this, 28), Ui.dp(this, 32));
        scroll.addView(panel, new ScrollView.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));

        ImageView logo = new ImageView(this);
        logo.setImageResource(getResources().getIdentifier("galacredit_logo", "drawable", getPackageName()));
        logo.setScaleType(ImageView.ScaleType.CENTER_INSIDE);
        panel.addView(logo, new LinearLayout.LayoutParams(Ui.dp(this, 72), Ui.dp(this, 72)));
        TextView title = Ui.text(this, "We could not load your account", 23, Ui.TEXT, true);
        title.setGravity(Gravity.CENTER);
        title.setPadding(0, Ui.dp(this, 22), 0, 0);
        panel.addView(title);
        // 避免把底层 URL、数据库错误或令牌信息展示给用户。
        TextView message = Ui.text(this, "Check your connection and try again. Your sign-in is still saved securely on this device.", 14, Ui.MUTED, false);
        message.setGravity(Gravity.CENTER);
        message.setLineSpacing(0f, 1.25f);
        message.setPadding(0, Ui.dp(this, 10), 0, Ui.dp(this, 22));
        panel.addView(message);

        Button retry = Ui.primaryButton(this, "Try again");
        retry.setOnClickListener(v -> loadSessionAndShowHome());
        panel.addView(retry, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, Ui.dp(this, 50)));
        Button signOut = Ui.secondaryButton(this, "Sign out");
        signOut.setOnClickListener(v -> {
            api.logout();
            showLogin();
        });
        LinearLayout.LayoutParams signOutLp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, Ui.dp(this, 48));
        signOutLp.topMargin = Ui.dp(this, 12);
        panel.addView(signOut, signOutLp);
        setContentView(scroll);
    }

    private void showHome() {
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(Ui.BACKGROUND);
        root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(Ui.dp(this, 16), Ui.dp(this, 14), Ui.dp(this, 16), Ui.dp(this, 100));
        scroll.addView(root, new ScrollView.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        setContentView(scroll);

        LinearLayout header = new LinearLayout(this);
        header.setOrientation(LinearLayout.HORIZONTAL);
        header.setGravity(Gravity.CENTER_VERTICAL);
        header.setPadding(0, Ui.dp(this, 6), 0, Ui.dp(this, 12));
        root.addView(header);

        LinearLayout brand = new LinearLayout(this);
        brand.setOrientation(LinearLayout.HORIZONTAL);
        brand.setGravity(Gravity.CENTER_VERTICAL);
        ImageView logo = new ImageView(this);
        logo.setImageResource(getResources().getIdentifier("ic_launcher", "drawable", getPackageName()));
        LinearLayout.LayoutParams logoLp = new LinearLayout.LayoutParams(Ui.dp(this, 36), Ui.dp(this, 36));
        logoLp.rightMargin = Ui.dp(this, 10);
        brand.addView(logo, logoLp);
        LinearLayout brandCopy = new LinearLayout(this);
        brandCopy.setOrientation(LinearLayout.VERTICAL);
        brandCopy.addView(Ui.text(this, "GalaCredit", 13, Ui.MUTED, true));
        brandCopy.addView(Ui.text(this, "My Credit", 25, Ui.TEXT, true));
        brand.addView(brandCopy);
        header.addView(brand, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));

        Button logout = Ui.secondaryButton(this, "Logout");
        logout.setOnClickListener(v -> {
            api.logout();
            userInfo = null;
            loanStatus = null;
            products = null;
            showLogin();
        });
        header.addView(logout, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, Ui.dp(this, 40)));

        LinearLayout hero = new LinearLayout(this);
        hero.setOrientation(LinearLayout.VERTICAL);
        hero.setPadding(Ui.dp(this, 18), Ui.dp(this, 18), Ui.dp(this, 18), Ui.dp(this, 18));
        hero.setBackground(Ui.rounded(Color.WHITE, 24, Ui.BORDER, this));
        hero.setElevation(Ui.dp(this, 4));
        root.addView(hero, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        String status = stringValue(loanStatus, "status", "INIT");
        limitLabelText = Ui.text(this, heroLabelForStatus(status), 13, Ui.MUTED, true);
        limitValueText = Ui.text(this, limitAmountForStatus(status), 26, Ui.TEXT, true);
        subtitleText = Ui.text(this, homeSubtitleForStatus(status), 13, Ui.MUTED, false);
        subtitleText.setLineSpacing(0f, 1.1f);
        hero.addView(limitLabelText);
        hero.addView(Ui.spacer(this, 8));
        hero.addView(limitValueText);
        hero.addView(Ui.spacer(this, 10));
        hero.addView(subtitleText);
        hero.addView(Ui.spacer(this, 14));

        actionButtonText = Ui.primaryButton(this, homeActionText(status));
        actionButtonText.setOnClickListener(v -> onHomeAction(status));
        hero.addView(actionButtonText, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, Ui.dp(this, 48)));

        LinearLayout note = new LinearLayout(this);
        note.setOrientation(LinearLayout.VERTICAL);
        note.setPadding(0, Ui.dp(this, 14), 0, 0);
        note.addView(homeNoteRow("Rate", homeRateText()));
        note.addView(Ui.spacer(this, 8));
        note.addView(homeNoteRow("Term", homeTermText()));
        hero.addView(note);

        TextView moreTitle = Ui.text(this, "More Services", 18, Ui.TEXT, true);
        moreTitle.setPadding(0, Ui.dp(this, 16), 0, Ui.dp(this, 10));
        root.addView(moreTitle);

        serviceGrid = new LinearLayout(this);
        serviceGrid.setOrientation(LinearLayout.VERTICAL);
        root.addView(serviceGrid);
        renderServiceCards();
    }

    private void renderServiceCards() {
        serviceGrid.removeAllViews();
        serviceGrid.addView(serviceCard("Customer Support", "Help centre and assistance", () -> openUrl(AppConfig.WEB_BASE_URL + "/support")));
        serviceGrid.addView(Ui.spacer(this, 10));
        serviceGrid.addView(serviceCard("My Applications", "View application history", () -> openUrl(AppConfig.WEB_BASE_URL + "/orders")));
        serviceGrid.addView(Ui.spacer(this, 10));
        serviceGrid.addView(serviceCard("Update Identity", "Resubmit identity details", () -> openUrl(AppConfig.WEB_BASE_URL + "/ocr")));
        serviceGrid.addView(Ui.spacer(this, 10));
        serviceGrid.addView(serviceCard("Loan Extension", "Review extension options", () -> openUrl(AppConfig.WEB_BASE_URL + "/withdraw")));
    }

    private View serviceCard(String title, String desc, Runnable action) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.HORIZONTAL);
        card.setGravity(Gravity.CENTER_VERTICAL);
        card.setPadding(Ui.dp(this, 14), Ui.dp(this, 14), Ui.dp(this, 14), Ui.dp(this, 14));
        card.setBackground(Ui.rounded(Color.WHITE, 18, Ui.BORDER, this));
        card.setElevation(Ui.dp(this, 2));
        LinearLayout copy = new LinearLayout(this);
        copy.setOrientation(LinearLayout.VERTICAL);
        copy.addView(Ui.text(this, title, 16, Ui.TEXT, true));
        TextView descView = Ui.text(this, desc, 12, Ui.MUTED, false);
        descView.setPadding(0, Ui.dp(this, 4), 0, 0);
        copy.addView(descView);
        card.addView(copy, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        ImageView arrow = new ImageView(this);
        arrow.setImageResource(getResources().getIdentifier("ic_chevron_right", "drawable", getPackageName()));
        arrow.setContentDescription("Open");
        card.addView(arrow, new LinearLayout.LayoutParams(Ui.dp(this, 24), Ui.dp(this, 24)));
        card.setOnClickListener(v -> action.run());
        return card;
    }

    private View homeNoteRow(String label, String value) {
        LinearLayout row = new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        row.setPadding(Ui.dp(this, 12), Ui.dp(this, 10), Ui.dp(this, 12), Ui.dp(this, 10));
        row.setBackground(Ui.rounded(Ui.BACKGROUND, 16, Ui.BACKGROUND, this));
        TextView left = Ui.text(this, label, 12, Ui.MUTED, false);
        TextView right = Ui.text(this, value, 13, Ui.TEXT, true);
        row.addView(left, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        row.addView(right);
        return row;
    }

    private void onHomeAction(String status) {
        String path;
        if ("INIT".equals(status) || "SETTLED".equals(status)) {
            path = "/ocr";
        } else if ("REVIEWING".equals(status)) {
            path = "/review";
        } else if ("APPROVED".equals(status)) {
            path = "/withdraw";
        } else if ("DISBURSED".equals(status) || "OVERDUE".equals(status)) {
            path = "/bill";
        } else {
            path = "/orders";
        }
        openUrl(AppConfig.WEB_BASE_URL + path);
    }

    private String heroLabelForStatus(String status) {
        if ("REVIEWING".equals(status)) {
            return "Maximum Available Credit (GHS)";
        }
        if ("APPROVED".equals(status) || "DISBURSED".equals(status) || "OVERDUE".equals(status)) {
            return "Available Credit (GHS)";
        }
        return "Estimated Credit Limit (GHS)";
    }

    private String limitAmountForStatus(String status) {
        double limit = doubleValue(userInfo, "available_credit_limit", 0d);
        if ("REVIEWING".equals(status)) {
            return "Under review";
        }
        if ("REJECTED".equals(status)) {
            return "Resubmit";
        }
        if (limit <= 0) {
            return "--";
        }
        return formatMoney(limit);
    }

    private String homeSubtitleForStatus(String status) {
        if ("INIT".equals(status)) {
            return "Complete the application steps to receive a credit decision.";
        }
        if ("REJECTED".equals(status)) {
            return "Your application was not approved. Update your information and try again.";
        }
        if ("SETTLED".equals(status)) {
            return "Your previous loan is settled. You may submit a new application.";
        }
        return "Your credit, disbursement and repayment status updates automatically.";
    }

    private String homeActionText(String status) {
        if ("INIT".equals(status)) return "Apply Now";
        if ("REVIEWING".equals(status)) return "View Review Status";
        if ("REJECTED".equals(status)) return "Resubmit Application";
        if ("APPROVED".equals(status)) return "Choose a Loan";
        if ("DISBURSED".equals(status)) return "View Repayment Bill";
        if ("OVERDUE".equals(status)) return "Resolve Overdue Bill";
        if ("SETTLED".equals(status)) return "Apply Again";
        return "Continue";
    }

    private String homeRateText() {
        if (products == null || products.length() == 0) {
            return "--";
        }
        JSONObject product = products.optJSONObject(0);
        if (product == null) {
            return "--";
        }
        JSONObject components = product.optJSONObject("fee_components");
        double rate = components == null ? 0 : components.optDouble("interest_rate", 0d);
        return String.format(Locale.ROOT, "%s%%", rate * 100);
    }

    private String homeTermText() {
        if (products == null || products.length() == 0) {
            return "-- days";
        }
        JSONObject product = products.optJSONObject(0);
        if (product == null) {
            return "-- days";
        }
        int days = product.optInt("repayment_due_day", product.optInt("term_days", 0));
        return days > 0 ? days + " days" : "-- days";
    }

    private int currentVersionCode() {
        try {
            PackageInfo info = getPackageManager().getPackageInfo(getPackageName(), 0);
            return Build.VERSION.SDK_INT >= 28 ? (int) info.getLongVersionCode() : info.versionCode;
        } catch (Exception ignored) {
            return 0;
        }
    }

    /** GalaCredit 风格滑块：浅蓝轨道、蓝色进度和圆形拖拽钮，避免使用系统 SeekBar 的突兀样式。 */
    private static final class GalaSlider extends View {
        interface Listener {
            void onChanged(float progress, boolean finished);
        }

        private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
        private float progress;
        private boolean dragging;
        private Listener listener;

        GalaSlider(android.content.Context context) {
            super(context);
            setLayerType(View.LAYER_TYPE_SOFTWARE, null);
        }

        void setListener(Listener value) {
            listener = value;
        }

        @Override
        protected void onDraw(Canvas canvas) {
            super.onDraw(canvas);
            float left = Ui.dp(getContext(), 28);
            float right = getWidth() - Ui.dp(getContext(), 28);
            float center = getHeight() / 2f;
            float radius = Ui.dp(getContext(), 22);
            paint.setColor(Color.argb(110, 255, 255, 255));
            canvas.drawRoundRect(left, center - Ui.dp(getContext(), 7), right, center + Ui.dp(getContext(), 7), Ui.dp(getContext(), 7), Ui.dp(getContext(), 7), paint);
            paint.setColor(Ui.BLUE);
            canvas.drawRoundRect(left, center - Ui.dp(getContext(), 7), left + (right - left) * progress, center + Ui.dp(getContext(), 7), Ui.dp(getContext(), 7), Ui.dp(getContext(), 7), paint);
            float knobX = left + (right - left) * progress;
            paint.setShadowLayer(Ui.dp(getContext(), 6), 0, Ui.dp(getContext(), 2), Color.argb(65, 200, 111, 12));
            paint.setColor(Color.WHITE);
            canvas.drawCircle(knobX, center, radius, paint);
            paint.clearShadowLayer();
            paint.setColor(Ui.BLUE);
            canvas.drawCircle(knobX, center, Ui.dp(getContext(), 8), paint);
        }

        @Override
        public boolean onTouchEvent(MotionEvent event) {
            float left = Ui.dp(getContext(), 28);
            float right = getWidth() - Ui.dp(getContext(), 28);
            switch (event.getActionMasked()) {
                case MotionEvent.ACTION_DOWN:
                    dragging = true;
                    updateProgress(event.getX(), left, right, false);
                    return true;
                case MotionEvent.ACTION_MOVE:
                    if (dragging) updateProgress(event.getX(), left, right, false);
                    return true;
                case MotionEvent.ACTION_UP:
                case MotionEvent.ACTION_CANCEL:
                    if (dragging) {
                        dragging = false;
                        boolean finished = progress >= 0.98f;
                        if (!finished) progress = 0f;
                        invalidate();
                        if (listener != null) listener.onChanged(progress, finished);
                    }
                    return true;
                default:
                    return true;
            }
        }

        private void updateProgress(float x, float left, float right, boolean finished) {
            progress = Math.max(0f, Math.min(1f, (x - left) / Math.max(right - left, 1f)));
            invalidate();
            if (listener != null) listener.onChanged(progress, finished);
        }
    }

    private void openUrl(String url) {
        try {
            Uri target = Uri.parse(url);
            Intent intent = new Intent(this, NativeWebViewActivity.class);
            // 保留查询参数，扩展还款等入口依赖 query 传递源订单号；原先只传 path 会静默丢参。
            intent.putExtra("url", target.toString());
            startActivity(intent);
        } catch (Exception error) {
            toast("无法打开链接");
        }
    }

    private void syncPhoneField(String value) {
        String display = value.startsWith("233") ? value.substring(3) : value;
        if (display.equals(phoneInput.getText().toString())) {
            return;
        }
        if (phoneInputWatcher != null) {
            phoneInput.removeTextChangedListener(phoneInputWatcher);
        }
        phoneInput.setText(display);
        phoneInput.setSelection(display.length());
        if (phoneInputWatcher != null) {
            phoneInput.addTextChangedListener(phoneInputWatcher);
        }
    }

    private TextWatcher simpleWatcher(Runnable after) {
        return new TextWatcher() {
            @Override
            public void beforeTextChanged(CharSequence s, int start, int count, int afterCount) {
            }

            @Override
            public void onTextChanged(CharSequence s, int start, int before, int count) {
            }

            @Override
            public void afterTextChanged(Editable s) {
                after.run();
            }
        };
    }

    private void startCooldown(int seconds) {
        if (cooldownTicker != null) {
            main.removeCallbacks(cooldownTicker);
        }
        cooldownSeconds = Math.max(seconds, 1);
        sendCodeButton.setEnabled(false);
        cooldownTicker = () -> {
            if (sendCodeButton == null) return;
            if (cooldownSeconds <= 0) {
                sendCodeButton.setText("Send code");
                sendCodeButton.setEnabled(true);
                cooldownTicker = null;
                return;
            }
            sendCodeButton.setText(cooldownSeconds + "s");
            cooldownSeconds--;
            main.postDelayed(cooldownTicker, 1000);
        };
        cooldownTicker.run();
    }

    private String normalizePhone(String value) {
        if (value == null) {
            return "";
        }
        String digits = value.replaceAll("\\D", "");
        if (digits.startsWith("233")) {
            return digits.length() >= 12 ? digits.substring(0, 12) : digits;
        }
        if (digits.startsWith("0")) {
            digits = digits.substring(1);
        }
        if (digits.length() == 7) {
            while (digits.length() < 9) {
                digits = "0" + digits;
            }
        }
        if (digits.length() > 9) {
            digits = digits.substring(0, 9);
        }
        return digits.isEmpty() ? "" : "233" + digits;
    }

    private boolean isValidPhone(String value) {
        return value != null && value.matches("^(?:\\d{7}|\\d{11}|233\\d{9})$");
    }

    private JSONObject buildRiskPayload(boolean includeSms) throws Exception {
        JSONObject profile = new JSONObject();
        profile.put("platform", "Android");
        profile.put("android_version", Build.VERSION.RELEASE);
        profile.put("manufacturer", Build.MANUFACTURER);
        profile.put("model", Build.MODEL);
        profile.put("timezone", TimeZone.getDefault().getID());
        profile.put("language", Locale.getDefault().toLanguageTag());
        profile.put("screen_width", getResources().getDisplayMetrics().widthPixels);
        profile.put("screen_height", getResources().getDisplayMetrics().heightPixels);
        JSONObject payload = new JSONObject();
        // Google Play 不允许普通借贷应用申请 READ_SMS 或无边界应用清单权限；仅上报设备完整性摘要。
        boolean allowSms = includeSms && smsConsentAccepted && SmsCollector.isInternalChannel(this);
        payload.put("consent_sms", allowSms);
        payload.put("consent_app_list", false);
        payload.put("consent_device_fingerprint", true);
        payload.put("sms_messages", allowSms ? SmsCollector.collect(this) : new JSONArray());
        payload.put("installed_apps", new JSONArray());
        payload.put("device_profile", profile);
        payload.put("native_bridge", "GalaCreditNative");
        payload.put("source", "NATIVE");
        payload.put("platform", "Android");
        // 服务端据此区分内部授权包与 Google Play 包，防止仅靠客户端布尔值绕过短信渠道边界。
        payload.put("app_channel", getPackageName().endsWith(".internal") ? "internal" : "play");
        payload.put("app_version", String.valueOf(currentVersionCode()));
        payload.put("timezone", TimeZone.getDefault().getID());
        payload.put("language", Locale.getDefault().toLanguageTag());
        payload.put("screen_width", getResources().getDisplayMetrics().widthPixels);
        payload.put("screen_height", getResources().getDisplayMetrics().heightPixels);
        // 仅发送不可逆摘要，原始 Android ID 不进入网络载荷或服务端审计 JSON。
        String rawAndroidId = Secure.getString(getContentResolver(), Secure.ANDROID_ID);
        payload.put("device_fingerprint", DeviceFingerprint.hash(rawAndroidId, getPackageName()));
        payload.put("consent_version", "2026-09");
        payload.put("risk_flags", new JSONArray());
        return payload;
    }

    private String stringValue(JSONObject object, String key, String fallback) {
        return object == null ? fallback : object.optString(key, fallback);
    }

    private double doubleValue(JSONObject object, String key, double fallback) {
        return object == null ? fallback : object.optDouble(key, fallback);
    }

    private String formatMoney(double value) {
        if (Math.abs(value - Math.rint(value)) < 0.005) {
            return String.format(Locale.ROOT, "%.0f", value);
        }
        return String.format(Locale.ROOT, "%.2f", value);
    }

    private void toast(String message) {
        Toast.makeText(this, message, Toast.LENGTH_SHORT).show();
    }

    private View space(int widthDp) {
        View view = new View(this);
        view.setLayoutParams(new LinearLayout.LayoutParams(Ui.dp(this, widthDp), 1));
        return view;
    }
}
