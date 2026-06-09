package com.juxin.xiaohebao.admin;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.DatePickerDialog;
import android.content.Intent;
import android.content.pm.PackageInfo;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.provider.Settings;
import android.text.Editable;
import android.text.InputType;
import android.text.SpannableString;
import android.text.Spanned;
import android.text.TextWatcher;
import android.text.style.RelativeSizeSpan;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.drawable.ColorDrawable;
import android.graphics.drawable.GradientDrawable;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import org.json.JSONArray;
import org.json.JSONObject;

import java.text.NumberFormat;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Calendar;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class MainActivity extends Activity {
    private final ExecutorService worker = Executors.newFixedThreadPool(4);
    private final Handler main = new Handler(Looper.getMainLooper());
    private ApiClient api;
    private JSONObject admin;
    private LinearLayout root;
    private final Map<String, JSONObject> listCache = new HashMap<>();
    private final Map<Integer, JSONObject> userDetailCache = new HashMap<>();
    private JSONObject statsCache;
    private JSONObject repaymentStatsCache;
    private String activeTab = "profiles";
    private String segmentScope = "REPAYMENTS";
    private String keyword = "";
    private String applicationStatusFilter = "REVIEWING";
    private boolean applicationTakeoverPool = false;
    private String repaymentOverdueFilter = "ALL";
    private String financeOverdueFilter = "ALL";
    private String repaymentStartDate = "";
    private String repaymentEndDate = "";
    private boolean detailOpen = false;
    private File pendingUpdateApk;
    private boolean updateDialogVisible = false;
    private int promptedUpdateVersionCode = 0;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        api = new ApiClient(this);
        continueStartup();
        main.postDelayed(this::checkAppUpdate, 800);
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (pendingUpdateApk != null && canInstallDownloadedApk()) {
            File apk = pendingUpdateApk;
            pendingUpdateApk = null;
            installApk(apk);
        } else {
            main.postDelayed(this::checkAppUpdate, 800);
        }
    }

    private void continueStartup() {
        if (api.token().isEmpty()) {
            showLogin();
        } else {
            loadMe();
        }
    }

    private void checkAppUpdate() {
        worker.execute(() -> {
            try {
                JSONObject update = fetchUpdateInfo();
                int versionCode = update.optInt("versionCode", 0);
                if (versionCode > currentVersionCode() && versionCode != promptedUpdateVersionCode && !updateDialogVisible) {
                    promptedUpdateVersionCode = versionCode;
                    main.post(() -> showUpdateDialog(update));
                }
            } catch (Exception ignored) {
            }
        });
    }

    private JSONObject fetchUpdateInfo() throws Exception {
        URL url = new URL(AppConfig.ASSET_BASE + "/download/android-version.json?t=" + System.currentTimeMillis());
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setConnectTimeout(8000);
        conn.setReadTimeout(8000);
        conn.setRequestProperty("Accept", "application/json");
        int code = conn.getResponseCode();
        if (code < 200 || code >= 300) {
            throw new IllegalStateException("版本检查失败");
        }
        return new JSONObject(readText(conn.getInputStream()));
    }

    private String readText(InputStream input) throws Exception {
        StringBuilder builder = new StringBuilder();
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(input, StandardCharsets.UTF_8))) {
            String line;
            while ((line = reader.readLine()) != null) {
                builder.append(line);
            }
        }
        return builder.toString();
    }

    private int currentVersionCode() {
        try {
            PackageInfo info = getPackageManager().getPackageInfo(getPackageName(), 0);
            return versionCodeOf(info);
        } catch (Exception ignored) {
            return 0;
        }
    }

    private int versionCodeOf(PackageInfo info) {
        if (Build.VERSION.SDK_INT >= 28) {
            return (int) info.getLongVersionCode();
        }
        return info.versionCode;
    }

    private void showUpdateDialog(JSONObject update) {
        boolean force = update.optBoolean("force", false);
        String versionName = update.optString("versionName", "");
        String notes = update.optString("notes", "发现新版小荷包管理端，请更新后继续使用。");
        updateDialogVisible = true;
        AlertDialog.Builder builder = new AlertDialog.Builder(this)
            .setTitle(isBlank(versionName) ? "发现新版本" : "发现新版本 " + versionName)
            .setMessage(notes)
            .setPositiveButton("升级", (dialog, which) -> downloadAndInstall(update));
        if (!force) {
            builder.setNegativeButton("稍后", null);
        }
        AlertDialog dialog = builder.create();
        dialog.setCancelable(!force);
        dialog.setOnDismissListener(d -> updateDialogVisible = false);
        dialog.show();
    }

    private void downloadAndInstall(JSONObject update) {
        String apkUrl = update.optString("apkUrl", AppConfig.ASSET_BASE + "/download/xiaohebao.apk");
        int expectedVersionCode = update.optInt("versionCode", 0);
        String expectedSha256 = update.optString("sha256", "");
        LinearLayout panel = dialogPanel();
        TextView message = text("正在下载升级包，请保持网络连接稳定。", 13, Ui.MUTED, Typeface.NORMAL);
        message.setSingleLine(false);
        TextView percent = text("0%", 22, Ui.BLUE, Typeface.BOLD);
        percent.setGravity(Gravity.CENTER);
        ProgressBar bar = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        bar.setMax(100);
        bar.setProgress(0);
        panel.addView(message);
        panel.addView(space(14));
        panel.addView(bar, matchHeight(18));
        panel.addView(space(10));
        panel.addView(percent, matchWrap());
        AlertDialog progress = buildGlassDialog("正在升级", panel);
        progress.setCancelable(false);
        progress.show();
        worker.execute(() -> {
            try {
                File apk = downloadApk(apkUrl, expectedVersionCode, expectedSha256, bar, percent);
                main.post(() -> {
                    progress.dismiss();
                    installApk(apk);
                });
            } catch (Exception error) {
                main.post(() -> {
                    progress.dismiss();
                    toast(error.getMessage() == null ? "更新下载失败" : error.getMessage());
                    if (!update.optBoolean("force", false)) continueStartup();
                });
            }
        });
    }

    private File downloadApk(String apkUrl, int expectedVersionCode, String expectedSha256, ProgressBar progress, TextView percentText) throws Exception {
        URL url = validateUpdateUrl(apkUrl);
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setConnectTimeout(15000);
        conn.setReadTimeout(30000);
        int code = conn.getResponseCode();
        if (code < 200 || code >= 300) {
            throw new IllegalStateException("下载失败：" + code);
        }
        File dir = new File(getCacheDir(), "xhb-updates");
        if (!dir.exists() && !dir.mkdirs()) {
            throw new IllegalStateException("无法创建更新目录");
        }
        File apk = new File(dir, "xiaohebao-update-" + Math.max(expectedVersionCode, currentVersionCode() + 1) + ".apk");
        int total = conn.getContentLength();
        if (total <= 0) {
            main.post(() -> {
                progress.setIndeterminate(true);
                percentText.setText("下载中");
            });
        }
        byte[] buffer = new byte[8192];
        int downloaded = 0;
        try (InputStream input = conn.getInputStream(); FileOutputStream output = new FileOutputStream(apk)) {
            int read;
            while ((read = input.read(buffer)) != -1) {
                output.write(buffer, 0, read);
                downloaded += read;
                if (total > 0) {
                    int percent = Math.min(100, Math.round(downloaded * 100f / total));
                    main.post(() -> {
                        progress.setProgress(percent);
                        percentText.setText(percent + "%");
                    });
                }
            }
        }
        validateDownloadedApk(apk, expectedVersionCode);
        String actualSha256 = sha256(apk);
        if (!isBlank(expectedSha256) && !expectedSha256.equalsIgnoreCase(actualSha256)) {
            throw new IllegalStateException("升级包校验失败，请稍后重试");
        }
        main.post(() -> {
            progress.setIndeterminate(false);
            progress.setProgress(100);
            percentText.setText("100%");
        });
        return apk;
    }

    private URL validateUpdateUrl(String apkUrl) throws Exception {
        URL url = new URL(apkUrl);
        URL assetBase = new URL(AppConfig.ASSET_BASE);
        if (!"https".equalsIgnoreCase(url.getProtocol()) || !assetBase.getHost().equalsIgnoreCase(url.getHost())) {
            throw new IllegalStateException("升级包来源不可信");
        }
        return url;
    }

    private void validateDownloadedApk(File apk, int expectedVersionCode) {
        PackageInfo info = getPackageManager().getPackageArchiveInfo(apk.getAbsolutePath(), 0);
        if (info == null || !getPackageName().equals(info.packageName)) {
            throw new IllegalStateException("升级包不是小荷包管理端");
        }
        int apkVersionCode = versionCodeOf(info);
        if (expectedVersionCode > 0 && apkVersionCode != expectedVersionCode) {
            throw new IllegalStateException("升级包版本与版本清单不一致");
        }
        if (apkVersionCode <= currentVersionCode()) {
            throw new IllegalStateException("升级包版本未高于当前版本");
        }
    }

    private String sha256(File file) throws Exception {
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        byte[] buffer = new byte[8192];
        try (InputStream input = new java.io.FileInputStream(file)) {
            int read;
            while ((read = input.read(buffer)) != -1) {
                digest.update(buffer, 0, read);
            }
        }
        StringBuilder builder = new StringBuilder();
        for (byte value : digest.digest()) {
            builder.append(String.format(Locale.ROOT, "%02x", value & 0xff));
        }
        return builder.toString();
    }

    private void installApk(File apk) {
        if (!canInstallDownloadedApk()) {
            pendingUpdateApk = apk;
            toast("请先允许小荷包安装应用更新");
            Intent settings = new Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES);
            settings.setData(Uri.parse("package:" + getPackageName()));
            startActivity(settings);
            return;
        }
        Uri uri = Uri.parse("content://" + ApkInstallProvider.AUTHORITY + "/" + apk.getName());
        Intent intent = new Intent(Intent.ACTION_VIEW);
        intent.setDataAndType(uri, "application/vnd.android.package-archive");
        intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        startActivity(intent);
    }

    private boolean canInstallDownloadedApk() {
        return Build.VERSION.SDK_INT < 26 || getPackageManager().canRequestPackageInstalls();
    }

    private void showLogin() {
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackground(stripeBackground());
        root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER_HORIZONTAL);
        root.setPadding(dp(22), dp(70), dp(22), dp(32));
        scroll.addView(root, new ScrollView.LayoutParams(ScrollView.LayoutParams.MATCH_PARENT, ScrollView.LayoutParams.WRAP_CONTENT));
        setContentView(scroll);
        main.postDelayed(this::checkAppUpdate, 600);

        ImageView logo = new ImageView(this);
        logo.setImageResource(getResources().getIdentifier("ic_launcher", "drawable", getPackageName()));
        root.addView(logo, new LinearLayout.LayoutParams(dp(72), dp(72)));

        TextView title = new TextView(this);
        title.setText("小荷包移动工作台");
        title.setTextSize(28);
        title.setTextColor(Ui.TEXT);
        title.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        title.setGravity(Gravity.CENTER);
        title.setPadding(0, dp(12), 0, dp(6));
        root.addView(title, matchWrap());

        TextView subtitle = text("移动审批 · 运营管理", 13, Ui.MUTED, Typeface.NORMAL);
        subtitle.setGravity(Gravity.CENTER);
        subtitle.setPadding(0, 0, 0, dp(24));
        root.addView(subtitle, matchWrap());

        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(dp(20), dp(20), dp(20), dp(20));
        card.setBackground(gcpCardDrawable());
        card.setElevation(dp(3));
        root.addView(card, matchWrap());

        EditText username = input("账号");
        EditText password = input("密码");
        password.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD);
        card.addView(text("账号", 13, Ui.MUTED, Typeface.BOLD));
        card.addView(space(6));
        card.addView(username, matchHeight(44));
        card.addView(space(14));
        card.addView(text("密码", 13, Ui.MUTED, Typeface.BOLD));
        card.addView(space(6));
        card.addView(password, matchHeight(44));
        card.addView(space(18));

        Button login = primaryButton("登录");
        card.addView(login, matchHeight(44));
        login.setOnClickListener(v -> {
            String u = username.getText().toString().trim();
            String p = password.getText().toString().trim();
            if (u.isEmpty() || p.isEmpty()) {
                toast("请输入账号和密码");
                return;
            }
            run("登录中...", () -> {
                api.login(u, p);
                admin = api.get("/admin/me", null);
                return null;
            }, ignored -> showWorkspace());
        });
    }

    private void loadMe() {
        run(null, () -> api.get("/admin/me", null), result -> {
            admin = result;
            showWorkspace();
        });
    }

    private void showWorkspace() {
        detailOpen = false;
        LinearLayout page = new LinearLayout(this);
        page.setOrientation(LinearLayout.VERTICAL);
        page.setBackground(stripeBackground());
        setContentView(page);
        main.postDelayed(this::checkAppUpdate, 600);

        LinearLayout header = new LinearLayout(this);
        header.setOrientation(LinearLayout.HORIZONTAL);
        header.setGravity(Gravity.CENTER_VERTICAL);
        header.setPadding(dp(18), dp(18), dp(18), dp(12));
        page.addView(header, matchWrap());

        LinearLayout titleBox = new LinearLayout(this);
        titleBox.setOrientation(LinearLayout.VERTICAL);
        TextView brand = text("小荷包", 13, Ui.MUTED, 1);
        TextView title = text(tabTitle(activeTab), 28, Ui.TEXT, 1);
        TextView subtitle = text("运营管理工作台", 11, Ui.MUTED, Typeface.NORMAL);
        titleBox.addView(brand);
        titleBox.addView(title);
        titleBox.addView(subtitle);
        header.addView(titleBox, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));

        Button refresh = circleButton("↻");
        Button user = avatarButton(adminInitial());
        header.addView(refresh, square(44));
        header.addView(space(10));
        header.addView(user, square(44));
        refresh.setOnClickListener(v -> { clearPageCache(); showWorkspace(); });
        user.setOnClickListener(v -> confirmLogout());

        LinearLayout fixed = new LinearLayout(this);
        fixed.setOrientation(LinearLayout.VERTICAL);
        fixed.setPadding(dp(16), 0, dp(16), dp(6));
        fixed.setBackground(roundRect(Color.TRANSPARENT, 0, 0));
        page.addView(fixed, matchWrap());
        addSummaryStrip(fixed);
        addSearchControls(fixed);

        ScrollView scroll = new ScrollView(this);
        LinearLayout list = new LinearLayout(this);
        list.setOrientation(LinearLayout.VERTICAL);
        list.setPadding(dp(16), dp(6), dp(16), dp(96));
        scroll.setClipToPadding(false);
        scroll.addView(list);
        page.addView(scroll, new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, 0, 1));
        loadList(list);
        addTabs(page);
    }

    private void addSummaryStrip(LinearLayout content) {
        LinearLayout row = row();
        row.setGravity(Gravity.CENTER);
        String[] labels = summaryLabels();
        LinearLayout left = metricCard(labels[0], "...", labels[2]);
        LinearLayout right = metricCard(labels[1], "...", labels[3]);
        row.addView(left, new LinearLayout.LayoutParams(0, dp(98), 1));
        row.addView(space(10));
        row.addView(right, new LinearLayout.LayoutParams(0, dp(98), 1));
        content.addView(row);
        content.addView(space(12));

        TextView leftValue = (TextView) left.getChildAt(1);
        TextView rightValue = (TextView) right.getChildAt(1);
        TextView leftTip = (TextView) left.getChildAt(3);
        TextView rightTip = (TextView) right.getChildAt(3);
        boolean needsRepaymentStats = "repayments".equals(activeTab) || "finance".equals(activeTab);
        if (statsCache != null && (!needsRepaymentStats || repaymentStatsCache != null)) {
            updateSummaryValues(leftValue, rightValue, leftTip, rightTip, statsCache, repaymentStatsCache == null ? new JSONObject() : repaymentStatsCache);
            return;
        }
        worker.execute(() -> {
            try {
                JSONObject stats = api.get("/admin/stats", null);
                JSONObject repayment = ("repayments".equals(activeTab) || "finance".equals(activeTab))
                    ? api.get("/admin/repayment-stats", repaymentStatsQuery())
                    : new JSONObject();
                statsCache = stats;
                repaymentStatsCache = repayment;
                main.post(() -> updateSummaryValues(leftValue, rightValue, leftTip, rightTip, stats, repayment));
            } catch (Exception ignored) {
                main.post(() -> { leftValue.setText("--"); rightValue.setText("--"); });
            }
        });
    }

    private LinearLayout metricCard(String label, String value, String tip) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(dp(16), dp(14), dp(16), dp(14));
        card.setBackground(gcpCardDrawable());
        card.setElevation(dp(3));
        TextView labelView = text(label, 12, Ui.MUTED, Typeface.NORMAL);
        TextView valueView = text(value, 24, Ui.TEXT, Typeface.BOLD);
        TextView tipView = text(tip, 11, Ui.MUTED, Typeface.NORMAL);
        valueView.setIncludeFontPadding(true);
        valueView.setPadding(0, dp(1), 0, 0);
        tipView.setIncludeFontPadding(true);
        card.addView(labelView);
        card.addView(valueView);
        card.addView(space(1));
        card.addView(tipView);
        return card;
    }

    private String[] summaryLabels() {
        if ("applications".equals(activeTab)) return new String[]{"待审批", "今日申请", "需要核验资料", "当天提交"};
        if ("cards".equals(activeTab)) return new String[]{"待发卡", "可用卡池", "等待发卡订单", "可用张数/金额"};
        if ("repayments".equals(activeTab)) {
            if ("OVERDUE".equals(repaymentOverdueFilter)) return new String[]{"累计逾期人数", "累计逾期金额", "未转催收逾期客户", "未转催收逾期金额"};
            if ("NOT_OVERDUE".equals(repaymentOverdueFilter)) return new String[]{"待回款人数", "待回总金额", "未到期且应回款非零", "未到期待回金额"};
            return new String[]{"今日回款进度", "今日回款金额", "实际/应回款人数", "实际/应回款金额"};
        }
        if ("finance".equals(activeTab)) return new String[]{"累计结清/部分结清订单", "已收金额", "用户数", "累计登记收款"};
        return new String[]{"总档案", "今日新增", "全部注册客户", "今天进入系统"};
    }

    private void updateSummaryValues(TextView left, TextView right, TextView leftTip, TextView rightTip, JSONObject stats, JSONObject repayment) {
        if ("applications".equals(activeTab)) {
            left.setText(String.valueOf(stats.optInt("reviewing_loans", 0)));
            right.setText(String.valueOf(stats.optInt("today_applications", 0)));
            leftTip.setText("需要核验资料");
            rightTip.setText("当天提交");
        } else if ("cards".equals(activeTab)) {
            left.setText(String.valueOf(stats.optInt("withdrawing_loans", 0)));
            right.setText(String.valueOf(stats.optInt("ecard_pool_available_count", 0)));
            leftTip.setText("等待发卡订单");
            rightTip.setText("可用卡池金额 " + formatMoney(stats.optDouble("ecard_pool_available_amount", 0)));
        } else if ("repayments".equals(activeTab)) {
            if ("OVERDUE".equals(repaymentOverdueFilter)) {
                left.setText(String.valueOf(repayment.optInt("overdue_user_count", 0)));
                right.setText(formatMoney(repayment.optDouble("overdue_amount", 0)));
                leftTip.setText("未转催收逾期客户");
                rightTip.setText("未转催收逾期金额");
            } else if ("NOT_OVERDUE".equals(repaymentOverdueFilter)) {
                left.setText(String.valueOf(repayment.optInt("pending_repayment_user_count", 0)));
                right.setText(formatMoney(repayment.optDouble("pending_repayment_amount", 0)));
                leftTip.setText("未到期且应回款非零");
                rightTip.setText("未到期待回金额");
            } else {
                setDueTodayProgress(left, leftTip, repayment);
                right.setText(dueTodayAmountProgressText(repayment));
                rightTip.setText("实际/应回款金额");
            }
        } else if ("finance".equals(activeTab)) {
            left.setText(repayment.optInt("settled_user_count", 0) + "/" + repayment.optInt("partial_repaid_unsettled_user_count", 0));
            right.setText(formatMoney(repayment.optDouble("received_amount", 0)));
            leftTip.setText("用户数");
            rightTip.setText("其他费用 " + formatMoney(repayment.optDouble("other_fee_amount", 0)));
        } else {
            left.setText(String.valueOf(stats.optInt("total_users", 0)));
            right.setText(String.valueOf(stats.optInt("today_new_users", 0)));
            leftTip.setText("全部注册客户");
            rightTip.setText("今天进入系统");
        }
    }

    private void setDueTodayProgress(TextView value, TextView tip, JSONObject repayment) {
        int dueTodayUsers = repayment.optInt("due_today_user_count", 0);
        int paidDueTodayUsers = repayment.optInt(
            "due_today_actual_repayment_user_count",
            repayment.optInt("today_actual_repayment_user_count", 0)
        );
        value.setText(paidDueTodayUsers + "/" + dueTodayUsers);
        tip.setText("实际/应回款人数");
    }

    private double dueTodayActualRepaymentAmount(JSONObject repayment) {
        return repayment.optDouble(
            "due_today_actual_repayment_amount",
            repayment.optDouble("today_actual_repayment_amount", 0)
        );
    }

    private String dueTodayAmountProgressText(JSONObject repayment) {
        return formatMoney(dueTodayActualRepaymentAmount(repayment)) + "/" + formatMoney(repayment.optDouble("due_today_amount", 0));
    }

    private void addSearchControls(LinearLayout content) {
        if ("profiles".equals(activeTab)) {
            addKeywordSearch(content, "搜索手机号 / 姓名 / 身份证");
        } else if ("applications".equals(activeTab)) {
            String[][] options = canUseReviewTakeoverPool()
                ? new String[][]{{"ALL", "全部"}, {"REVIEWING", "审核中"}, {"TAKEOVER", "可转入"}, {"APPROVED", "已通过"}, {"REJECTED", "未通过"}}
                : new String[][]{{"ALL", "全部"}, {"REVIEWING", "审核中"}, {"APPROVED", "已通过"}, {"REJECTED", "未通过"}};
            addStatusFilter(content, options, applicationTakeoverPool ? "TAKEOVER" : applicationStatusFilter, value -> {
                applicationTakeoverPool = "TAKEOVER".equals(value);
                applicationStatusFilter = applicationTakeoverPool ? "REVIEWING" : value;
                clearPageCache();
                showWorkspace();
            });
        } else if ("repayments".equals(activeTab)) {
            addDateRangeSearch(content);
            addOverdueFilter(content, repaymentOverdueFilter, value -> {
                repaymentOverdueFilter = value;
                segmentScope = "REPAYMENTS";
                clearPageCache();
                showWorkspace();
            });
        } else if ("finance".equals(activeTab)) {
            addKeywordSearch(content, "搜索手机号 / 姓名 / 身份证");
            addOverdueFilter(content, financeOverdueFilter, value -> {
                financeOverdueFilter = value;
                clearPageCache();
                showWorkspace();
            });
        }
    }

    private void addKeywordSearch(LinearLayout content, String hint) {
        EditText search = input(hint);
        search.setSingleLine(true);
        search.setText(keyword);
        Button query = primaryButton("查询");
        LinearLayout searchRow = row();
        searchRow.addView(search, new LinearLayout.LayoutParams(0, dp(48), 1));
        searchRow.addView(space(8));
        searchRow.addView(query, new LinearLayout.LayoutParams(dp(78), dp(48)));
        content.addView(searchRow);
        content.addView(space(12));
        query.setOnClickListener(v -> {
            keyword = search.getText().toString().trim();
            showWorkspace();
        });
    }

    private void addDateRangeSearch(LinearLayout content) {
        EditText start = input("开始日期");
        EditText end = input("结束日期");
        start.setSingleLine(true);
        end.setSingleLine(true);
        start.setText(repaymentStartDate);
        end.setText(repaymentEndDate);
        bindDatePicker(start);
        bindDatePicker(end);
        Button query = primaryButton("查询");
        LinearLayout row = row();
        row.addView(start, new LinearLayout.LayoutParams(0, dp(48), 1));
        row.addView(space(8));
        row.addView(end, new LinearLayout.LayoutParams(0, dp(48), 1));
        row.addView(space(8));
        row.addView(query, new LinearLayout.LayoutParams(dp(70), dp(48)));
        content.addView(row);
        content.addView(space(8));
        query.setOnClickListener(v -> {
            repaymentStartDate = start.getText().toString().trim();
            repaymentEndDate = end.getText().toString().trim();
            clearPageCache();
            showWorkspace();
        });
    }

    private void addOverdueFilter(LinearLayout content, String current, FilterSetter setter) {
        addStatusFilter(content, new String[][]{{"ALL", "全部"}, {"OVERDUE", "已逾期"}, {"NOT_OVERDUE", "未逾期"}}, current, setter);
    }

    private void bindDatePicker(EditText input) {
        input.setFocusable(false);
        input.setInputType(InputType.TYPE_NULL);
        input.setOnClickListener(v -> showDatePicker(input));
    }

    private void showDatePicker(EditText input) {
        Calendar calendar = Calendar.getInstance();
        String value = input.getText().toString().trim();
        if (value.length() >= 10) {
            try {
                calendar.set(Calendar.YEAR, Integer.parseInt(value.substring(0, 4)));
                calendar.set(Calendar.MONTH, Integer.parseInt(value.substring(5, 7)) - 1);
                calendar.set(Calendar.DAY_OF_MONTH, Integer.parseInt(value.substring(8, 10)));
            } catch (Exception ignored) {
                calendar = Calendar.getInstance();
            }
        }
        DatePickerDialog dialog = new DatePickerDialog(this, (view, year, month, dayOfMonth) -> {
            String date = String.format(Locale.ROOT, "%04d-%02d-%02d", year, month + 1, dayOfMonth);
            input.setText(date);
        }, calendar.get(Calendar.YEAR), calendar.get(Calendar.MONTH), calendar.get(Calendar.DAY_OF_MONTH));
        dialog.show();
    }

    private void addStatusFilter(LinearLayout content, String[][] options, String current, FilterSetter setter) {
        LinearLayout row = row();
        for (int i = 0; i < options.length; i++) {
            String value = options[i][0];
            Button button = segment(options[i][1], value.equals(current));
            row.addView(button, new LinearLayout.LayoutParams(0, dp(42), 1));
            if (i < options.length - 1) row.addView(space(8));
            button.setOnClickListener(v -> setter.apply(value));
        }
        content.addView(row);
        content.addView(space(12));
    }

    private void loadList(LinearLayout content) {
        String cacheKey = listCacheKey();
        JSONObject cached = listCache.get(cacheKey);
        if (cached != null) {
            renderList(content, cached);
            return;
        }
        TextView loading = text("加载中...", 14, Ui.MUTED, 0);
        loading.setGravity(Gravity.CENTER);
        content.addView(loading, matchHeight(72));
        run(null, () -> {
            if ("profiles".equals(activeTab)) {
                Map<String, String> q = baseQuery();
                if (!keyword.isEmpty()) q.put("keyword", keyword);
                return api.get("/admin/users", q);
            }
            Map<String, String> q = baseQuery();
            q.put("scope", scopeForTab(activeTab));
            if ("applications".equals(activeTab)) {
                if (applicationTakeoverPool) {
                    q.put("status", "REVIEWING");
                    q.put("takeover_pool", "true");
                } else if (!"ALL".equals(applicationStatusFilter)) {
                    q.put("status", applicationStatusFilter);
                }
            }
            applyOverdueQuery(q);
            applyDueDateQuery(q);
            if (!keyword.isEmpty()) q.put("phone", keyword);
            JSONObject result = api.get("/admin/loans", q);
            if ("applications".equals(activeTab)) enrichApplicationItems(result);
            return result;
        }, result -> {
            content.removeView(loading);
            listCache.put(cacheKey, result);
            renderList(content, result);
        });
    }

    private void renderList(LinearLayout content, JSONObject result) {
        content.removeAllViews();
        JSONArray items = result.optJSONArray("items");
        if (items == null || items.length() == 0) {
            TextView empty = text("暂无数据", 15, Ui.MUTED, 0);
            empty.setGravity(Gravity.CENTER);
            content.addView(empty, matchHeight(96));
            return;
        }
        for (int i = 0; i < items.length(); i++) {
            JSONObject row = items.optJSONObject(i);
            if (row != null) addCard(content, row);
        }
    }

    private String listCacheKey() {
        return activeTab + "|" + keyword + "|" + applicationStatusFilter + "|" + applicationTakeoverPool + "|" + repaymentOverdueFilter + "|" + financeOverdueFilter + "|" + repaymentStartDate + "|" + repaymentEndDate;
    }

    private void clearPageCache() {
        listCache.clear();
        statsCache = null;
        repaymentStatsCache = null;
    }

    private void enrichApplicationItems(JSONObject result) throws Exception {
        JSONArray items = result.optJSONArray("items");
        if (items == null) return;
        for (int i = 0; i < items.length(); i++) {
            JSONObject item = items.optJSONObject(i);
            int userId = resolveUserId(item);
            if (item == null || userId <= 0) continue;
            JSONObject detail = userDetailCache.get(userId);
            if (detail == null) {
                detail = api.get("/admin/users/" + userId, null);
                JSONObject ipAudit = api.get("/admin/users/" + userId + "/ip-audit", null);
                detail.put("_ip_audit", ipAudit);
                userDetailCache.put(userId, detail);
            }
            item.put("_user_detail", detail);
        }
    }

    private void addCard(LinearLayout content, JSONObject item) {
        if ("applications".equals(activeTab)) {
            addApplicationCard(content, item);
            return;
        }
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(dp(18), dp(16), dp(18), dp(16));
        card.setBackground(gcpCardDrawable());
        card.setElevation(dp(3));
        LinearLayout.LayoutParams lp = matchWrap();
        lp.setMargins(0, 0, 0, dp(12));
        content.addView(card, lp);

        LinearLayout head = row();
        head.setGravity(Gravity.CENTER_VERTICAL);
        TextView name = text(displayName(item), 19, Ui.TEXT, Typeface.BOLD);
        TextView status = pill(statusText(item), statusColor(item), statusTextColor(item));
        head.addView(name, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        addRiskTags(head, item, false);
        head.addView(status);
        TextView sub = text(subtitle(item), 13, Ui.MUTED, 0);
        LinearLayout grid = row();
        grid.setPadding(0, dp(14), 0, 0);
        grid.addView(gridCell(formatMoney(amount(item)), amountLabel()), new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        grid.addView(gridCell(dateText(item), dateLabel(item)), new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        TextView hint = text(noteText(item), 13, Ui.MUTED, 0);
        card.addView(head);
        card.addView(space(6));
        card.addView(sub);
        card.addView(grid);
        if (!isBlank(hint.getText().toString())) {
            card.addView(space(6));
            card.addView(hint);
        }
        card.setOnClickListener(v -> openDetail(item));
    }

    private void addApplicationCard(LinearLayout content, JSONObject item) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(dp(18), dp(16), dp(18), dp(16));
        card.setBackground(gcpCardDrawable());
        card.setElevation(dp(3));
        LinearLayout.LayoutParams lp = matchWrap();
        lp.setMargins(0, 0, 0, dp(12));
        content.addView(card, lp);

        LinearLayout head = row();
        TextView name = text(displayName(item), 19, Ui.TEXT, Typeface.BOLD);
        TextView status = pill(statusText(item), statusColor(item), statusTextColor(item));
        head.addView(name, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        addRiskTags(head, item, false);
        head.addView(status);
        card.addView(head);
        card.addView(space(6));
        card.addView(text(rawUserPhone(item) + " · " + channelText(item), 13, Ui.MUTED, Typeface.NORMAL));
        card.addView(space(8));
        addCardLine(card, "申请时间", dateTimeText(item.optString("application_submitted_at", item.optString("created_at", ""))));
        addCardLine(card, "最新IP", latestIpText(item));
        addCardLine(card, "IP位置", latestIpLocationText(item));
        addCardLine(card, "最新GPS", latestGpsText(item));
        addCardLine(card, "GPS位置", latestGpsLocationText(item));
        card.setOnClickListener(v -> openDetail(item));
    }

    private void addCardLine(LinearLayout card, String label, String value) {
        LinearLayout line = row();
        line.setPadding(0, dp(3), 0, 0);
        TextView labelView = text(label, 12, Ui.MUTED, Typeface.NORMAL);
        TextView valueView = text(value == null ? "" : value, 13, Ui.TEXT, Typeface.BOLD);
        valueView.setSingleLine(false);
        line.addView(labelView, new LinearLayout.LayoutParams(dp(62), LinearLayout.LayoutParams.WRAP_CONTENT));
        line.addView(valueView, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        card.addView(line);
    }

    private LinearLayout gridCell(String value, String label) {
        LinearLayout cell = new LinearLayout(this);
        cell.setOrientation(LinearLayout.VERTICAL);
        TextView valueView = text(value, 18, Ui.TEXT, Typeface.NORMAL);
        TextView labelView = text(label, 12, Ui.MUTED, Typeface.NORMAL);
        cell.addView(valueView);
        cell.addView(labelView);
        return cell;
    }

    private void openDetail(JSONObject item) {
        showDetail(item);
        int userId = resolveUserId(item);
        if (userId <= 0) return;
        worker.execute(() -> {
            try {
                JSONObject detail = api.get("/admin/users/" + userId, null);
                JSONObject ipAudit = api.get("/admin/users/" + userId + "/ip-audit", null);
                JSONObject riskReq = new JSONObject();
                riskReq.put("user_id", userId);
                detail.put("_ip_audit", ipAudit);
                try {
                    detail.put("_composite_risk_report", api.post("/admin/risk/composite-report", riskReq));
                } catch (Exception riskError) {
                    JSONObject riskState = new JSONObject();
                    riskState.put("_load_error", riskError.getMessage() == null ? "风控报告加载失败" : riskError.getMessage());
                    detail.put("_composite_risk_report", riskState);
                }
                if (!"profiles".equals(activeTab)) {
                    item.put("_user_detail", detail);
                    main.post(() -> showDetail(item));
                } else {
                    main.post(() -> showDetail(detail));
                }
            } catch (Exception error) {
                main.post(() -> toast(error.getMessage() == null ? "详情加载失败" : error.getMessage()));
            }
        });
    }

    private void showDetail(JSONObject item) {
        detailOpen = true;
        JSONObject user = detailUser(item);
        LinearLayout page = new LinearLayout(this);
        page.setOrientation(LinearLayout.VERTICAL);
        page.setBackground(stripeBackground());
        setContentView(page);

        LinearLayout header = row();
        header.setPadding(dp(14), dp(16), dp(14), dp(10));
        Button back = circleButton("‹");
        LinearLayout titleBox = new LinearLayout(this);
        titleBox.setOrientation(LinearLayout.VERTICAL);
        LinearLayout nameRow = row();
        nameRow.addView(text(displayName(item), 22, Ui.TEXT, Typeface.BOLD), new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        addRiskTags(nameRow, user, true);
        titleBox.addView(nameRow);
        addDetailSubtitle(titleBox, item);
        header.addView(back, square(44));
        header.addView(titleBox, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        page.addView(header, matchWrap());
        back.setOnClickListener(v -> showWorkspace());

        ScrollView scroll = new ScrollView(this);
        LinearLayout content = new LinearLayout(this);
        content.setOrientation(LinearLayout.VERTICAL);
        content.setPadding(dp(16), 0, dp(16), dp(18));
        scroll.setClipToPadding(false);
        scroll.addView(content);
        page.addView(scroll, new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, 0, 1));

        addPhotosSection(content, user);
        addInfoSection(content, "核心信息", coreRows(item));
        addRiskReportSection(content, item);
        addInfoSection(content, "紧急联系人", emergencyRows(user));
        addInfoSection(content, "地理位置", locationRows(user));
        addInfoSection(content, "IP记录", ipRows(user));
        addInfoSection(content, "订单状态及审核批注", orderAuditRows(item));
        addActionDock(page, item);
    }

    private void addDetailSubtitle(LinearLayout titleBox, JSONObject item) {
        if (!"applications".equals(activeTab)) {
            titleBox.addView(text(subtitle(item), 13, Ui.MUTED, Typeface.NORMAL));
            return;
        }
        LinearLayout line = row();
        line.setGravity(Gravity.CENTER_VERTICAL);
        TextView channel = text("渠道：" + channelText(item), 13, Ui.MUTED, Typeface.NORMAL);
        TextView reviewer = text("审核员：" + reviewerName(item), 13, Ui.BLUE, Typeface.BOLD);
        reviewer.setGravity(Gravity.CENTER);
        reviewer.setPadding(dp(10), dp(4), dp(10), dp(4));
        reviewer.setBackground(roundRect(Color.argb(130, 232, 240, 254), dp(999), Ui.BORDER));
        if (hasAny("ADMIN")) {
            reviewer.setOnClickListener(v -> showReviewerAssignDialog(item));
        } else if (canTakeOverReview(item)) {
            reviewer.setText("审核员：" + reviewerName(item) + " · 转给我");
            reviewer.setOnClickListener(v -> takeOverReviewer(item));
        }
        line.addView(channel, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        line.addView(reviewer, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        titleBox.addView(line);
    }

    private void addInfoSection(LinearLayout content, String title, String[][] rows) {
        TextView heading = text(title, 15, Ui.TEXT, Typeface.BOLD);
        heading.setPadding(0, dp(12), 0, dp(8));
        content.addView(heading);
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(dp(16), dp(12), dp(16), dp(12));
        box.setBackground(gcpCardDrawable());
        box.setElevation(dp(3));
        for (String[] row : rows) {
            LinearLayout line = row();
            line.setPadding(0, dp(5), 0, dp(5));
            TextView label = text(row[0], 13, Ui.MUTED, Typeface.NORMAL);
            TextView value = text(row[1], 14, Ui.TEXT, Typeface.BOLD);
            value.setGravity(Gravity.START);
            value.setSingleLine(false);
            line.addView(label, new LinearLayout.LayoutParams(dp(88), LinearLayout.LayoutParams.WRAP_CONTENT));
            line.addView(value, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
            box.addView(line);
        }
        content.addView(box, matchWrap());
    }

    private void addPhotosSection(LinearLayout content, JSONObject item) {
        TextView heading = text("认证照片", 15, Ui.TEXT, Typeface.BOLD);
        heading.setPadding(0, dp(12), 0, dp(8));
        content.addView(heading);
        String[][] photos = new String[][]{
            {"身份证正面", item.optString("id_card_front_image_url", "")},
            {"身份证反面", item.optString("id_card_back_image_url", "")},
            {"人脸照", item.optString("face_image_url", "")}
        };
        LinearLayout row = row();
        row.addView(photoBox(photos, 0), new LinearLayout.LayoutParams(0, dp(108), 1));
        row.addView(space(8));
        row.addView(photoBox(photos, 1), new LinearLayout.LayoutParams(0, dp(108), 1));
        row.addView(space(8));
        row.addView(photoBox(photos, 2), new LinearLayout.LayoutParams(0, dp(108), 1));
        content.addView(row);
    }

    private void addRiskReportSection(LinearLayout content, JSONObject item) {
        TextView heading = text("风控报告", 15, Ui.TEXT, Typeface.BOLD);
        heading.setPadding(0, dp(12), 0, dp(8));
        content.addView(heading);

        JSONObject report = compositeRiskReport(item);
        if (report == null) {
            content.addView(riskReportStateCard("风控数据加载中", "正在汇总系统核查、全景雷达和探针C结果。"), matchWrap());
            return;
        }
        if (!isBlank(report.optString("_load_error", ""))) {
            content.addView(riskReportStateCard("风控数据暂不可用", report.optString("_load_error", "风控报告加载失败")), matchWrap());
            return;
        }
        JSONObject payload = compositeRiskPayload(report);
        if (payload == null) {
            content.addView(riskReportStateCard("暂无风控报告", "当前用户还没有可展示的综合风控结果。"), matchWrap());
            return;
        }
        content.addView(riskReportCard(payload, report), matchWrap());
    }

    private LinearLayout riskReportStateCard(String title, String message) {
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(dp(16), dp(14), dp(16), dp(14));
        box.setBackground(gcpCardDrawable());
        box.setElevation(dp(3));
        box.addView(text(title, 15, Ui.TEXT, Typeface.BOLD));
        TextView detail = text(message, 12, Ui.MUTED, Typeface.NORMAL);
        detail.setPadding(0, dp(6), 0, 0);
        detail.setSingleLine(false);
        box.addView(detail);
        return box;
    }

    private LinearLayout riskReportCard(JSONObject payload, JSONObject report) {
        JSONObject systemRisk = payload.optJSONObject("system_risk");
        if (systemRisk == null) systemRisk = new JSONObject();
        JSONObject panorama = payload.optJSONObject("panorama");
        JSONObject panoramaPayload = panorama == null ? null : panorama.optJSONObject("payload");
        JSONObject panoramaData = panoramaPayload == null ? null : panoramaPayload.optJSONObject("data");
        JSONObject applyDetail = panoramaData == null ? null : panoramaData.optJSONObject("apply_report_detail");
        if (applyDetail == null && panoramaPayload != null) applyDetail = panoramaPayload.optJSONObject("apply_report_detail");
        if (applyDetail == null) applyDetail = new JSONObject();
        JSONObject behaviorDetail = panoramaData == null ? null : panoramaData.optJSONObject("behavior_report_detail");
        if (behaviorDetail == null && panoramaPayload != null) behaviorDetail = panoramaPayload.optJSONObject("behavior_report_detail");
        if (behaviorDetail == null) behaviorDetail = new JSONObject();
        JSONObject probeC = payload.optJSONObject("probe_c");
        if (probeC == null) probeC = new JSONObject();
        JSONObject probeData = probeC.optJSONObject("payload");
        probeData = probeData == null ? null : probeData.optJSONObject("data");
        if (probeData == null) probeData = new JSONObject();

        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(dp(16), dp(14), dp(16), dp(14));
        card.setBackground(gcpCardDrawable());
        card.setElevation(dp(3));

        JSONObject latestOrder = payload.optJSONObject("latest_order");
        if (latestOrder == null) latestOrder = new JSONObject();

        LinearLayout firstRow = row();
        firstRow.setGravity(Gravity.TOP);
        firstRow.addView(riskMiniMetric("报告时间", dateTimeText(report.optString("query_time", payload.optString("query_time", "")))), new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        firstRow.addView(space(8));
        firstRow.addView(riskMiniMetric("报告评估结论", riskSummaryBadge(systemRisk, behaviorDetail, probeC)), new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        card.addView(firstRow);

        card.addView(space(10));
        LinearLayout scoreRow = row();
        scoreRow.setGravity(Gravity.TOP);
        scoreRow.addView(riskScoreMetric("申请准入分", riskMetricValue(applyDetail, "A22160001")), new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        scoreRow.addView(space(8));
        scoreRow.addView(riskScoreMetric("信用行为分", riskMetricValue(behaviorDetail, "B22170001")), new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        card.addView(scoreRow);

        card.addView(space(10));
        LinearLayout serviceRow = row();
        serviceRow.setGravity(Gravity.TOP);
        serviceRow.addView(riskMiniMetric("最近放款", latestDisbursementText(latestOrder, behaviorDetail)), new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        serviceRow.addView(space(8));
        serviceRow.addView(riskMiniMetric("探查结果", valueOr(probeC.optString("result_label", ""))), new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        serviceRow.addView(space(8));
        serviceRow.addView(riskMiniMetric("正常还款比例", riskMetricValue(behaviorDetail, "B22170034")), new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        card.addView(serviceRow);

        card.addView(space(12));
        card.addView(text("风险维度", 14, Ui.TEXT, Typeface.BOLD));
        LinearLayout grid = new LinearLayout(this);
        grid.setOrientation(LinearLayout.VERTICAL);
        grid.setPadding(0, dp(8), 0, 0);
        LinearLayout top = row();
        top.addView(riskDimensionBox("系统核查", riskSystemStatus(systemRisk), riskSystemDescription(systemRisk)), new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        top.addView(space(8));
        top.addView(riskDimensionBox("位置 / IP", riskLocationStatus(systemRisk), riskLocationDescription(systemRisk)), new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        LinearLayout bottom = row();
        bottom.setPadding(0, dp(8), 0, 0);
        bottom.addView(riskDimensionBox("履约行为", riskBehaviorStatus(behaviorDetail), riskBehaviorDescription(behaviorDetail)), new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        bottom.addView(space(8));
        bottom.addView(riskDimensionBox("探针C", riskProbeStatus(probeC), riskProbeDescription(probeC, probeData)), new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        grid.addView(top);
        grid.addView(bottom);
        card.addView(grid);

        card.addView(space(12));
        card.addView(text("命中原因", 14, Ui.TEXT, Typeface.BOLD));
        LinearLayout reasonsBox = new LinearLayout(this);
        reasonsBox.setOrientation(LinearLayout.VERTICAL);
        reasonsBox.setPadding(0, dp(6), 0, 0);
        List<String> reasons = riskReasons(systemRisk, behaviorDetail, probeC, probeData);
        for (int i = 0; i < reasons.size(); i++) {
            TextView reason = text("• " + reasons.get(i), 12, Ui.MUTED, Typeface.NORMAL);
            reason.setSingleLine(false);
            if (i > 0) reason.setPadding(0, dp(6), 0, 0);
            reasonsBox.addView(reason);
        }
        card.addView(reasonsBox);

        return card;
    }

    private LinearLayout riskMiniMetric(String label, String value) {
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(dp(12), dp(10), dp(12), dp(10));
        box.setBackground(roundRect(Color.rgb(249, 250, 252), dp(16), Ui.BORDER));
        TextView labelView = text(label, 11, Ui.MUTED, Typeface.NORMAL);
        TextView valueView = text(valueOr(value), 13, Ui.TEXT, Typeface.BOLD);
        valueView.setPadding(0, dp(5), 0, 0);
        valueView.setSingleLine(false);
        box.addView(labelView);
        box.addView(valueView);
        return box;
    }

    private LinearLayout riskScoreMetric(String label, String value) {
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(dp(16), dp(14), dp(16), dp(14));
        box.setBackground(roundRect(Color.rgb(236, 244, 255), dp(18), 0));
        TextView labelView = text(label, 12, Ui.MUTED, Typeface.NORMAL);
        TextView valueView = text(valueOr(value), 26, Ui.VIOLET, Typeface.BOLD);
        valueView.setPadding(0, dp(6), 0, 0);
        box.addView(labelView);
        box.addView(valueView);
        return box;
    }

    private String latestDisbursementText(JSONObject latestOrder, JSONObject behaviorDetail) {
        String disbursedAt = latestOrder.optString("disbursed_at", "");
        if (!isBlank(disbursedAt)) return dateTimeText(disbursedAt);
        return riskMetricValue(behaviorDetail, "B22170054");
    }

    private LinearLayout riskMetricHighlightBox(String label, String value, String tip) {
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(dp(16), dp(14), dp(16), dp(14));
        box.setBackground(roundRect(Color.rgb(236, 244, 255), dp(18), 0));
        TextView labelView = text(label, 12, Ui.MUTED, Typeface.NORMAL);
        TextView valueView = text(value, 26, Ui.VIOLET, Typeface.BOLD);
        valueView.setPadding(0, dp(6), 0, dp(2));
        TextView tipView = text(tip, 11, Ui.MUTED, Typeface.NORMAL);
        tipView.setSingleLine(false);
        box.addView(labelView);
        box.addView(valueView);
        box.addView(tipView);
        return box;
    }

    private LinearLayout riskMetricLine(String label, String value) {
        LinearLayout line = new LinearLayout(this);
        line.setOrientation(LinearLayout.VERTICAL);
        line.setPadding(dp(14), dp(10), dp(14), dp(10));
        line.setBackground(roundRect(Color.rgb(249, 250, 252), dp(16), Ui.BORDER));
        TextView labelView = text(label, 12, Ui.MUTED, Typeface.NORMAL);
        TextView valueView = text(value, 14, Ui.TEXT, Typeface.BOLD);
        valueView.setPadding(0, dp(4), 0, 0);
        line.addView(labelView);
        line.addView(valueView);
        LinearLayout.LayoutParams lp = matchWrap();
        lp.setMargins(0, 0, 0, dp(8));
        line.setLayoutParams(lp);
        return line;
    }

    private LinearLayout riskDimensionBox(String title, String status, String desc) {
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(dp(14), dp(12), dp(14), dp(12));
        box.setBackground(roundRect(Color.rgb(249, 250, 252), dp(16), Ui.BORDER));
        TextView titleView = text(title, 12, Ui.MUTED, Typeface.NORMAL);
        TextView statusView = text(status, 14, riskStatusColor(status), Typeface.BOLD);
        statusView.setPadding(0, dp(6), 0, 0);
        TextView descView = text(desc, 11, Ui.MUTED, Typeface.NORMAL);
        descView.setPadding(0, dp(6), 0, 0);
        descView.setSingleLine(false);
        box.addView(titleView);
        box.addView(statusView);
        box.addView(descView);
        return box;
    }

    private TextView riskBadge(String text, int[] colors) {
        TextView view = this.text(text, 12, colors[0], Typeface.BOLD);
        view.setPadding(dp(12), dp(6), dp(12), dp(6));
        view.setBackground(roundRect(colors[1], dp(999), 0));
        return view;
    }

    private LinearLayout buildRiskDetailArea(
        JSONObject payload,
        JSONObject report,
        JSONObject systemRisk,
        JSONObject applyDetail,
        JSONObject behaviorDetail,
        JSONObject probeC,
        JSONObject probeData
    ) {
        LinearLayout area = new LinearLayout(this);
        area.setOrientation(LinearLayout.VERTICAL);
        area.setPadding(0, dp(12), 0, 0);

        JSONObject profile = payload.optJSONObject("user_profile");
        if (profile == null) profile = new JSONObject();
        JSONObject latestOrder = payload.optJSONObject("latest_order");
        if (latestOrder == null) latestOrder = new JSONObject();

        area.addView(riskSubSection(
            "客户摘要",
            "用于快速确认当前报告对应的客户身份。",
            new String[][]{
                {"姓名", valueOr(profile.optString("name", report.optString("name", "")))},
                {"手机号", valueOr(profile.optString("phone", report.optString("phone", "")))},
                {"身份证号", valueOr(profile.optString("id_card", report.optString("id_card", "")))},
                {"报告时间", dateTimeText(report.optString("query_time", payload.optString("query_time", "")))}
            }
        ));
        area.addView(riskSubSection(
            "系统风险核查",
            "来自本系统黑名单、位置风控、登录拦截与手机号绑定记录。",
            new String[][]{
                {"黑名单", systemRisk.optBoolean("blacklist_hit") ? "命中" : "未命中"},
                {"风险地址", systemRisk.optBoolean("location_risk_hit") ? "命中" : "未命中"},
                {"登录位置拦截", systemRisk.optBoolean("login_location_blocked") ? "触发" : "未触发"},
                {"同手机号绑定", String.valueOf(systemRisk.optInt("same_phone_binding_count", 0)) + " 条"},
                {"黑名单原因", valueOr(systemRisk.optString("blacklist_reason", ""))},
                {"风险地址明细", valueOr(systemRisk.optString("location_risk_detail", ""))},
                {"登录拦截原因", valueOr(systemRisk.optString("login_location_reason", ""))},
                {"风险关键词", joinJsonArray(systemRisk.optJSONArray("location_risk_keywords"))}
            }
        ));
        area.addView(riskSubSection(
            "当前订单摘要",
            "展示客户最近一笔订单的当前状态。",
            new String[][]{
                {"订单状态", valueOr(latestOrder.optString("status", ""))},
                {"授信额度", formatMoney(latestOrder.optDouble("credit_limit", 0))},
                {"可用额度", formatMoney(latestOrder.optDouble("available_credit_limit", 0))},
                {"商品名称", valueOr(latestOrder.optString("product_name", ""))},
                {"应付金额", formatMoney(latestOrder.optDouble("payment_amount", latestOrder.optDouble("product_total_price", 0)))},
                {"到期日", dateTimeText(latestOrder.optString("due_date", ""))}
            }
        ));
        area.addView(riskSubSection(
            "全景雷达摘要",
            "保留 Web 端同口径字段，便于移动端核查。",
            new String[][]{
                {"申请准入分", riskMetricValue(applyDetail, "A22160001")},
                {"申请准入置信度", riskMetricValue(applyDetail, "A22160002")},
                {"申请命中机构数", riskMetricValue(applyDetail, "A22160003")},
                {"申请命中消金机构数", riskMetricValue(applyDetail, "A22160004")},
                {"申请命中网络信用机构数", riskMetricValue(applyDetail, "A22160005")},
                {"机构总查询次数", riskMetricValue(applyDetail, "A22160006")},
                {"最近一次查询时间", riskMetricValue(applyDetail, "A22160007")},
                {"近1个月机构总查询笔数", riskMetricValue(applyDetail, "A22160008")},
                {"近3个月机构总查询笔数", riskMetricValue(applyDetail, "A22160009")},
                {"近6个月机构总查询笔数", riskMetricValue(applyDetail, "A22160010")},
                {"信用行为分", riskMetricValue(behaviorDetail, "B22170001")},
                {"信用行为置信度", riskMetricValue(behaviorDetail, "B22170051")},
                {"最近一次服务发放时间", riskMetricValue(behaviorDetail, "B22170054")},
                {"已结清订单数", riskMetricValue(behaviorDetail, "B22170052")},
                {"信用服务时长", riskMetricValue(behaviorDetail, "B22170053")},
                {"最近一次履约距今天数", riskMetricValue(behaviorDetail, "B22170050")},
                {"正常付款订单占比", riskMetricValue(behaviorDetail, "B22170034")},
                {"近12个月M0+逾期订单笔数", riskMetricValue(behaviorDetail, "B22170026")},
                {"近12个月M1+逾期订单笔数", riskMetricValue(behaviorDetail, "B22170029")},
                {"近12个月累计逾期金额", riskMetricValue(behaviorDetail, "B22170032")},
                {"近24个月M0+逾期订单笔数", riskMetricValue(behaviorDetail, "B22170027")},
                {"近24个月M1+逾期订单笔数", riskMetricValue(behaviorDetail, "B22170030")},
                {"近24个月累计逾期金额", riskMetricValue(behaviorDetail, "B22170033")}
            }
        ));
        area.addView(riskSubSection(
            "探针C摘要",
            "展示探针C返回的履约与逾期概况。",
            new String[][]{
                {"结果", valueOr(probeC.optString("result_label", ""))},
                {"最大逾期金额", riskMetricValue(probeData, "max_overdue_amt")},
                {"最长逾期天数", riskMetricValue(probeData, "max_overdue_days")},
                {"最近逾期时间", riskMetricValue(probeData, "latest_overdue_time")},
                {"当前逾期机构数", riskMetricValue(probeData, "currently_overdue")},
                {"当前履约机构数", riskMetricValue(probeData, "currently_performance")},
                {"异常还款机构数", riskMetricValue(probeData, "acc_exc")},
                {"睡眠机构数", riskMetricValue(probeData, "acc_sleep")},
                {"报告来源", valueOr(probeC.optString("source", ""))},
                {"最大履约金额", riskMetricValue(probeData, "max_performance_amt")},
                {"最近履约时间", riskMetricValue(probeData, "latest_performance_time")},
                {"履约笔数", riskMetricValue(probeData, "count_performance")}
            }
        ));
        area.addView(riskAccessSection(payload.optJSONArray("recent_access")));
        return area;
    }

    private LinearLayout riskSubSection(String title, String tip, String[][] rows) {
        LinearLayout section = new LinearLayout(this);
        section.setOrientation(LinearLayout.VERTICAL);
        section.setPadding(dp(14), dp(12), dp(14), dp(12));
        section.setBackground(roundRect(Color.rgb(250, 251, 253), dp(18), Ui.BORDER));
        LinearLayout.LayoutParams lp = matchWrap();
        lp.setMargins(0, 0, 0, dp(10));
        section.setLayoutParams(lp);

        TextView titleView = text(title, 14, Ui.TEXT, Typeface.BOLD);
        section.addView(titleView);
        TextView tipView = text(tip, 11, Ui.MUTED, Typeface.NORMAL);
        tipView.setPadding(0, dp(4), 0, dp(8));
        tipView.setSingleLine(false);
        section.addView(tipView);

        for (String[] row : rows) {
            LinearLayout line = row();
            line.setPadding(0, dp(4), 0, dp(4));
            TextView label = text(row[0], 12, Ui.MUTED, Typeface.NORMAL);
            TextView value = text(row[1], 13, Ui.TEXT, Typeface.BOLD);
            value.setSingleLine(false);
            line.addView(label, new LinearLayout.LayoutParams(dp(108), LinearLayout.LayoutParams.WRAP_CONTENT));
            line.addView(value, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
            section.addView(line);
        }
        return section;
    }

    private LinearLayout riskAccessSection(JSONArray recentAccess) {
        LinearLayout section = new LinearLayout(this);
        section.setOrientation(LinearLayout.VERTICAL);
        section.setPadding(dp(14), dp(12), dp(14), dp(12));
        section.setBackground(roundRect(Color.rgb(250, 251, 253), dp(18), Ui.BORDER));

        TextView titleView = text("最近访问记录", 14, Ui.TEXT, Typeface.BOLD);
        section.addView(titleView);
        TextView tipView = text("按时间由近到远展示最近访问、IP 和经纬度解析结果。", 11, Ui.MUTED, Typeface.NORMAL);
        tipView.setPadding(0, dp(4), 0, dp(8));
        tipView.setSingleLine(false);
        section.addView(tipView);

        if (recentAccess == null || recentAccess.length() == 0) {
            section.addView(text("暂无访问记录", 12, Ui.MUTED, Typeface.NORMAL));
            return section;
        }
        int count = Math.min(recentAccess.length(), 5);
        for (int i = 0; i < count; i++) {
            JSONObject row = recentAccess.optJSONObject(i);
            if (row == null) continue;
            String detail = valueOr(row.optString("title", "")) + " / "
                + valueOr(row.optString("ip", "")) + " / "
                + valueOr(row.optString("ip_address", "")) + " / "
                + dateTimeText(row.optString("created_at", ""));
            LinearLayout line = this.row();
            line.setPadding(0, dp(4), 0, dp(4));
            line.addView(text("记录" + (i + 1), 12, Ui.MUTED, Typeface.NORMAL), new LinearLayout.LayoutParams(dp(56), LinearLayout.LayoutParams.WRAP_CONTENT));
            TextView value = text(detail, 12, Ui.TEXT, Typeface.BOLD);
            value.setSingleLine(false);
            line.addView(value, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
            section.addView(line);
        }
        return section;
    }

    private JSONObject compositeRiskReport(JSONObject item) {
        JSONObject user = detailUser(item);
        JSONObject report = user == null ? null : user.optJSONObject("_composite_risk_report");
        if (report != null) return report;
        return item.optJSONObject("_composite_risk_report");
    }

    private JSONObject compositeRiskPayload(JSONObject report) {
        if (report == null) return null;
        Object payload = report.opt("report_json");
        if (payload instanceof JSONObject) return (JSONObject) payload;
        if (payload instanceof String) {
            try {
                return new JSONObject((String) payload);
            } catch (Exception ignored) {
                return null;
            }
        }
        return null;
    }

    private String riskMetricValue(JSONObject source, String key) {
        if (source == null) return "--";
        Object value = source.opt(key);
        if (value == null || JSONObject.NULL.equals(value)) return "--";
        String text = String.valueOf(value).trim();
        return text.isEmpty() || "null".equalsIgnoreCase(text) ? "--" : text;
    }

    private String riskSummaryBadge(JSONObject systemRisk, JSONObject behaviorDetail, JSONObject probeC) {
        if (systemRisk.optBoolean("blacklist_hit") || systemRisk.optBoolean("login_location_blocked")) return "评分偏高";
        if (systemRisk.optBoolean("location_risk_hit")) return "建议复核";
        String probeLabel = probeC.optString("result_label", "");
        if ("逾期未还款".equals(probeLabel)) return "评分偏高";
        String overdueCount = riskMetricValue(behaviorDetail, "B22170026");
        if (!"--".equals(overdueCount) && !"0".equals(overdueCount)) return "建议复核";
        return "风险可控";
    }

    private int[] riskSummaryBadgeColor(JSONObject systemRisk, JSONObject behaviorDetail, JSONObject probeC) {
        String badge = riskSummaryBadge(systemRisk, behaviorDetail, probeC);
        if ("评分偏高".equals(badge)) return new int[]{Ui.RED, Color.rgb(252, 236, 236)};
        if ("建议复核".equals(badge)) return new int[]{Ui.ORANGE, Color.rgb(255, 245, 224)};
        return new int[]{Ui.MINT, Color.rgb(232, 248, 239)};
    }

    private String riskSystemStatus(JSONObject systemRisk) {
        if (systemRisk.optBoolean("blacklist_hit")) return "高风险";
        if (systemRisk.optBoolean("risk_list_hit")) return "建议复核";
        return "正常";
    }

    private String riskSystemDescription(JSONObject systemRisk) {
        if (systemRisk.optBoolean("blacklist_hit")) return valueOr(systemRisk.optString("blacklist_reason", "命中系统黑名单"));
        if (systemRisk.optBoolean("risk_list_hit")) return valueOr(systemRisk.optString("risk_list_reason", "命中风险名单，建议人工复核"));
        int bindingCount = systemRisk.optInt("same_phone_binding_count", 0);
        return bindingCount > 1 ? "同手机号曾绑定 " + bindingCount + " 个账号" : "黑名单与风险名单均未命中";
    }

    private String riskLocationStatus(JSONObject systemRisk) {
        if (systemRisk.optBoolean("login_location_blocked")) return "高风险";
        if (systemRisk.optBoolean("location_risk_hit")) return "偏高";
        return "正常";
    }

    private String riskLocationDescription(JSONObject systemRisk) {
        if (systemRisk.optBoolean("login_location_blocked")) return valueOr(systemRisk.optString("login_location_reason", "登录位置已被系统拦截"));
        if (systemRisk.optBoolean("location_risk_hit")) return valueOr(systemRisk.optString("location_risk_detail", "命中风险地址关键词"));
        return "定位与 IP 暂未发现明显异常";
    }

    private String riskBehaviorStatus(JSONObject behaviorDetail) {
        String overdueCount = riskMetricValue(behaviorDetail, "B22170026");
        if (!"--".equals(overdueCount) && !"0".equals(overdueCount)) return "偏高";
        String score = riskMetricValue(behaviorDetail, "B22170001");
        if (!"--".equals(score) && parseIntSafely(score) >= 700) return "正常";
        return "--".equals(score) ? "待补充" : "建议关注";
    }

    private String riskBehaviorDescription(JSONObject behaviorDetail) {
        String score = riskMetricValue(behaviorDetail, "B22170001");
        String overdueCount = riskMetricValue(behaviorDetail, "B22170026");
        String overdueAmount = riskMetricValue(behaviorDetail, "B22170032");
        if (!"--".equals(overdueCount) && !"0".equals(overdueCount)) {
            return "近12个月 M0+ 逾期 " + overdueCount + " 笔，累计 " + overdueAmount;
        }
        String ratio = riskMetricValue(behaviorDetail, "B22170034");
        return "信用行为分 " + score + "，正常付款占比 " + ratio;
    }

    private String riskProbeStatus(JSONObject probeC) {
        String label = probeC.optString("result_label", "");
        if ("逾期未还款".equals(label)) return "高风险";
        if ("逾期后已还款".equals(label) || "无法确认".equals(label)) return "建议复核";
        if ("正常履约".equals(label)) return "正常";
        return "待补充";
    }

    private String riskProbeDescription(JSONObject probeC, JSONObject probeData) {
        String label = valueOr(probeC.optString("result_label", ""));
        String overdue = riskMetricValue(probeData, "currently_overdue");
        String performance = riskMetricValue(probeData, "currently_performance");
        return "探针结果 " + label + "，当前逾期机构 " + overdue + "，履约机构 " + performance;
    }

    private List<String> riskReasons(JSONObject systemRisk, JSONObject behaviorDetail, JSONObject probeC, JSONObject probeData) {
        List<String> reasons = new ArrayList<>();
        if (systemRisk.optBoolean("blacklist_hit")) {
            reasons.add("系统黑名单命中：" + valueOr(systemRisk.optString("blacklist_reason", "存在历史风险记录")));
        }
        if (systemRisk.optBoolean("risk_list_hit")) {
            reasons.add("风险名单命中：" + valueOr(systemRisk.optString("risk_list_reason", "外部风险名单命中")));
        }
        if (systemRisk.optBoolean("location_risk_hit")) {
            reasons.add(valueOr(systemRisk.optString("location_risk_detail", "申请定位或访问 IP 命中风险地址关键词")));
        }
        if (systemRisk.optBoolean("login_location_blocked")) {
            reasons.add("登录位置拦截：" + valueOr(systemRisk.optString("login_location_reason", "当前登录环境存在异常")));
        }
        String overdueCount = riskMetricValue(behaviorDetail, "B22170026");
        if (!"--".equals(overdueCount) && !"0".equals(overdueCount)) {
            reasons.add("履约行为显示近12个月 M0+ 逾期 " + overdueCount + " 笔，累计金额 " + riskMetricValue(behaviorDetail, "B22170032"));
        }
        String probeLabel = probeC.optString("result_label", "");
        if (!isBlank(probeLabel) && !"正常履约".equals(probeLabel)) {
            reasons.add("探针C结果为“" + probeLabel + "”，最长逾期天数 " + riskMetricValue(probeData, "max_overdue_days"));
        }
        if (reasons.isEmpty()) {
            reasons.add("系统核查、位置/IP 与外部履约探查暂未发现明显强风险信号。");
            reasons.add("建议结合认证照片、联系人与订单信息继续人工审核。");
        }
        return reasons;
    }

    private int riskStatusColor(String status) {
        if ("高风险".equals(status)) return Ui.RED;
        if ("偏高".equals(status) || "建议复核".equals(status) || "建议关注".equals(status)) return Ui.ORANGE;
        if ("正常".equals(status)) return Ui.MINT;
        return Ui.MUTED;
    }

    private static int parseIntSafely(String value) {
        try {
            return Integer.parseInt(value.trim());
        } catch (Exception ignored) {
            return 0;
        }
    }

    private String joinJsonArray(JSONArray items) {
        if (items == null || items.length() == 0) return "--";
        List<String> values = new ArrayList<>();
        for (int i = 0; i < items.length(); i++) {
            String value = items.optString(i, "").trim();
            if (!isBlank(value) && !"null".equalsIgnoreCase(value)) values.add(value);
        }
        return values.isEmpty() ? "--" : String.join("、", values);
    }

    private LinearLayout photoBox(String[][] photos, int index) {
        String label = photos[index][0];
        String url = photos[index][1];
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setGravity(Gravity.CENTER);
        box.setPadding(dp(6), dp(6), dp(6), dp(6));
        box.setBackground(roundRect(Color.WHITE, dp(16), Ui.BORDER));
        box.setElevation(dp(2));
        View media;
        if (isBlank(url) || "null".equalsIgnoreCase(url)) {
            TextView empty = text("暂无照片", 13, Ui.MUTED, Typeface.NORMAL);
            empty.setGravity(Gravity.CENTER);
            media = empty;
        } else {
            ImageView image = new ImageView(this);
            image.setScaleType(ImageView.ScaleType.CENTER_CROP);
            image.setBackgroundColor(Color.rgb(232, 238, 255));
            media = image;
            loadImage(image, url);
            box.setClickable(true);
            box.setOnClickListener(v -> showPhotoPreview(photos, index));
        }
        TextView caption = text(label, 11, Ui.MUTED, Typeface.BOLD);
        caption.setGravity(Gravity.CENTER);
        caption.setPadding(0, dp(5), 0, 0);
        box.addView(media, new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, 0, 1));
        box.addView(caption, matchWrap());
        return box;
    }

    private void showPhotoPreview(String[][] photos, int startIndex) {
        final int[] index = new int[]{startIndex};
        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setPadding(dp(2), dp(4), dp(2), dp(2));
        TextView title = text(photos[index[0]][0], 16, Ui.TEXT, Typeface.BOLD);
        title.setGravity(Gravity.CENTER);
        ImageView image = new ImageView(this);
        image.setScaleType(ImageView.ScaleType.FIT_CENTER);
        image.setBackgroundColor(Color.rgb(248, 251, 255));
        panel.addView(title, matchWrap());
        panel.addView(space(10));
        panel.addView(image, new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, dp(420)));
        LinearLayout actions = row();
        Button prev = actionButton("上一张");
        Button close = dangerButton("关闭");
        Button next = actionButton("下一张");
        actions.addView(prev, new LinearLayout.LayoutParams(0, dp(44), 1));
        actions.addView(space(8));
        actions.addView(close, new LinearLayout.LayoutParams(0, dp(44), 1));
        actions.addView(space(8));
        actions.addView(next, new LinearLayout.LayoutParams(0, dp(44), 1));
        panel.addView(actions);
        AlertDialog dialog = buildGlassDialog("照片预览", panel);
        Runnable render = () -> {
            title.setText(photos[index[0]][0]);
            image.setImageDrawable(null);
            loadImage(image, photos[index[0]][1]);
        };
        prev.setOnClickListener(v -> {
            index[0] = (index[0] + photos.length - 1) % photos.length;
            render.run();
        });
        next.setOnClickListener(v -> {
            index[0] = (index[0] + 1) % photos.length;
            render.run();
        });
        close.setOnClickListener(v -> dialog.dismiss());
        final float[] downX = new float[1];
        image.setOnTouchListener((view, event) -> {
            if (event.getAction() == MotionEvent.ACTION_DOWN) {
                downX[0] = event.getX();
                return true;
            }
            if (event.getAction() == MotionEvent.ACTION_UP) {
                float delta = event.getX() - downX[0];
                if (Math.abs(delta) > dp(40)) {
                    if (delta > 0) prev.performClick(); else next.performClick();
                    return true;
                }
            }
            return true;
        });
        dialog.show();
        render.run();
    }

    private void loadImage(ImageView image, String rawUrl) {
        worker.execute(() -> {
            try {
                String url = rawUrl.startsWith("http") ? rawUrl : AppConfig.ASSET_BASE + rawUrl;
                try (InputStream input = new URL(url).openStream()) {
                    Bitmap bitmap = BitmapFactory.decodeStream(input);
                    main.post(() -> image.setImageBitmap(bitmap));
                }
            } catch (Exception ignored) {
                main.post(() -> image.setImageDrawable(null));
            }
        });
    }

    private void addActionDock(LinearLayout page, JSONObject item) {
        LinearLayout dock = new LinearLayout(this);
        dock.setOrientation(LinearLayout.VERTICAL);
        dock.setPadding(dp(16), dp(12), dp(16), dp(16));
        dock.setBackground(gcpCardDrawable());
        dock.setElevation(dp(2));
        TextView title = text("可执行操作", 14, Ui.TEXT, Typeface.BOLD);
        dock.addView(title);
        LinearLayout row = null;
        int index = 0;
        List<String[]> availableActions = actionsForCurrentTab(item);
        if (availableActions.isEmpty()) {
            TextView empty = text("当前状态暂无可执行操作", 13, Ui.MUTED, Typeface.NORMAL);
            empty.setPadding(0, dp(8), 0, 0);
            dock.addView(empty);
            page.addView(dock, matchWrap());
            return;
        }
        for (String[] action : availableActions) {
            if (index % 2 == 0) {
                row = row();
                row.setPadding(0, dp(8), 0, 0);
                dock.addView(row);
            }
            Button button = isDangerAction(action[0]) ? dangerButton(action[1]) : actionButton(action[1]);
            row.addView(button, new LinearLayout.LayoutParams(0, dp(44), 1));
            if (index % 2 == 0 && index < availableActions.size() - 1) row.addView(space(8));
            button.setOnClickListener(v -> prepareAction(action[0], item));
            index++;
        }
        page.addView(dock, matchWrap());
    }

    private void showActions(JSONObject item) {
        List<String> labels = new ArrayList<>();
        List<String> keys = new ArrayList<>();
        for (String[] action : actionsForCurrentTab(item)) {
            labels.add(action[1]);
            keys.add(action[0]);
        }
        LinearLayout panel = dialogPanel();
        for (int i = 0; i < labels.size(); i++) {
            final int index = i;
            Button button = actionButton(labels.get(i));
            panel.addView(button, matchHeight(44));
            panel.addView(space(8));
            button.setOnClickListener(v -> prepareAction(keys.get(index), item));
        }
        AlertDialog dialog = buildGlassDialog(displayName(item), panel);
        panel.addView(dialogButtons("关闭", "返回", dialog, () -> {}));
        dialog.show();
    }

    private void prepareAction(String action, JSONObject item) {
        if ("approve".equals(action)) {
            showApproveDialog(item);
            return;
        }
        if ("reject".equals(action)) {
            showRejectDialog(item);
            return;
        }
        if ("save-note".equals(action)) {
            showReviewNoteDialog(item);
            return;
        }
        if ("reconcile".equals(action)) {
            showReconcileDialog(item);
            return;
        }
        if ("disburse".equals(action)) {
            showDisburseDialog(item);
            return;
        }
        if ("extend".equals(action)) {
            showExtendDialog(item);
            return;
        }
        if ("adjust-credit".equals(action)) {
            showCreditAdjustDialog(item);
            return;
        }
        if ("set-credit".equals(action)) {
            showCreditSetDialog(item);
            return;
        }
        if ("takeover-review".equals(action)) {
            takeOverReviewer(item);
            return;
        }
        if ("reject-card".equals(action)) {
            showNoteActionDialog(action, item, "拒绝发卡", "拒绝原因", "卡池或订单信息不符合发卡要求", "note");
            return;
        }
        if ("remind".equals(action)) {
            showNoteActionDialog(action, item, "登记提醒", "提醒备注", "已完成还款提醒", "note");
            return;
        }
        if ("collect".equals(action)) {
            showNoteActionDialog(action, item, "登记催收", "催收备注", item.optString("collection_note", "已执行逾期催收"), "note");
            return;
        }
        if ("blacklist".equals(action)) {
            showNoteActionDialog(action, item, "一键拉黑", "拉黑原因", "后台一键拉黑", "note");
            return;
        }
        if ("remove-blacklist".equals(action)) {
            showNoteActionDialog(action, item, "移出黑名单", "移出说明", "后台移出黑名单", "note");
            return;
        }
        if ("unlock-location".equals(action)) {
            showNoteActionDialog(action, item, "解除位移风控", "解除说明", "管理员确认解除4小时位移风控", "note");
            return;
        }
        if ("ack".equals(action) || "settle".equals(action) || "refresh".equals(action) || "reissue-card".equals(action) || "close-reissue".equals(action)) {
            confirmAction(action, item, new JSONObject());
            return;
        }
        EditText input = input(defaultHint(action));
        input.setMinLines("reconcile".equals(action) || "approve".equals(action) || "extend".equals(action) ? 3 : 1);
        input.setText(defaultValue(action, item));
        LinearLayout panel = dialogPanel();
        panel.addView(fieldBox(defaultHint(action), input));
        AlertDialog dialog = buildGlassDialog(actionTitle(action), panel);
        panel.addView(dialogButtons("取消", "提交", dialog, () -> {
            JSONObject body = new JSONObject();
            fillPayload(action, input.getText().toString().trim(), item, body);
            confirmAction(action, item, body);
        }));
        dialog.show();
    }

    private void showApproveDialog(JSONObject item) {
        LinearLayout panel = dialogPanel();
        EditText credit = input("授信额度");
        EditText discount = input("减免额度");
        EditText term = input("期限天数");
        credit.setInputType(InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_FLAG_DECIMAL);
        discount.setInputType(InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_FLAG_DECIMAL);
        term.setInputType(InputType.TYPE_CLASS_NUMBER);
        credit.setText(defaultValue("approve", item));
        discount.setText(String.valueOf(item.optDouble("approval_discount_amount", 0)));
        term.setText(String.valueOf(item.optInt("term_days", item.optInt("product_term_days", 7))));
        panel.addView(fieldBox("授信额度", credit));
        panel.addView(fieldBox("减免额度", discount));
        panel.addView(fieldBox("期限", term));
        AlertDialog dialog = buildGlassDialog("审批通过", panel);
        panel.addView(dialogButtons("关闭", "提交", dialog, () -> {
            JSONObject body = new JSONObject();
            body.put("approved", true);
            body.put("credit_limit", numberOr(credit.getText().toString(), item.optDouble("approved_credit_limit", 1000)));
            body.put("approval_discount_amount", numberOr(discount.getText().toString(), 0));
            body.put("term_days", (int) numberOr(term.getText().toString(), 7));
            body.put("review_note", "安卓端审批通过");
            confirmAction("approve", item, body);
        }));
        dialog.show();
    }

    private void showDisburseDialog(JSONObject item) {
        LinearLayout panel = dialogPanel();
        EditText term = input("账期天数");
        term.setInputType(InputType.TYPE_CLASS_NUMBER);
        term.setText(defaultValue("disburse", item));
        panel.addView(compactSummaryBox(new String[][]{
            {"客户", displayName(item)},
            {"手机号", valueOr(item.optString("user_phone", ""))},
            {"下单商品", valueOr(item.optString("product_name", ""))},
            {"E卡面值", formatMoney(item.optDouble("ecard_face_value", item.optDouble("credit_limit", 0)))},
            {"信用支付金额", formatMoney(amount(item))}
        }));
        panel.addView(fieldBox("账期天数", term));
        AlertDialog dialog = buildGlassDialog("确认发卡", panel);
        panel.addView(dialogButtons("取消", "确认发卡", dialog, () -> {
            JSONObject body = new JSONObject();
            body.put("term_days", (int) numberOr(term.getText().toString(), item.optInt("term_days", item.optInt("product_term_days", 7))));
            confirmAction("disburse", item, body);
        }));
        dialog.show();
    }

    private void showExtendDialog(JSONObject item) {
        LinearLayout panel = dialogPanel();
        final String[] extensionType = {"FREE"};
        EditText days = input("展期天数");
        EditText reduction = input("减免金额");
        EditText note = input("展期备注");
        days.setInputType(InputType.TYPE_CLASS_NUMBER);
        reduction.setInputType(InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_FLAG_DECIMAL);
        note.setMinLines(3);
        days.setText(defaultValue("extend", item));
        reduction.setText("0");
        note.setText("安卓端账单展期");
        LinearLayout typeRow = row();
        Button free = segment("免费展期", true);
        Button fee = segment("付费展期", false);
        typeRow.addView(free, new LinearLayout.LayoutParams(0, dp(44), 1));
        typeRow.addView(space(8));
        typeRow.addView(fee, new LinearLayout.LayoutParams(0, dp(44), 1));
        free.setOnClickListener(v -> {
            extensionType[0] = "FREE";
            setSegmentActive(free, true);
            setSegmentActive(fee, false);
            note.setText("安卓端免费展期");
        });
        fee.setOnClickListener(v -> {
            extensionType[0] = "FEE";
            setSegmentActive(free, false);
            setSegmentActive(fee, true);
            note.setText("安卓端付费展期");
        });
        panel.addView(text("展期类型", 13, Ui.MUTED, Typeface.BOLD));
        panel.addView(space(6));
        panel.addView(typeRow, matchHeight(44));
        panel.addView(space(12));
        panel.addView(fieldBox("展期天数", days));
        panel.addView(fieldBox("减免金额", reduction));
        panel.addView(fieldBox("备注", note));
        AlertDialog dialog = buildGlassDialog("账单展期", panel);
        panel.addView(dialogButtons("取消", "确认展期", dialog, () -> {
            JSONObject body = new JSONObject();
            body.put("extension_type", extensionType[0]);
            body.put("days", (int) numberOr(days.getText().toString(), 3));
            body.put("reduction_amount", numberOr(reduction.getText().toString(), 0));
            body.put("note", note.getText().toString().trim());
            confirmAction("extend", item, body);
        }));
        dialog.show();
    }

    private void showCreditAdjustDialog(JSONObject item) {
        LinearLayout panel = dialogPanel();
        EditText amount = input("增加可用额度");
        EditText note = input("额度调整备注");
        amount.setInputType(InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_FLAG_DECIMAL);
        note.setMinLines(3);
        amount.setText(defaultValue("adjust-credit", item));
        note.setText("安卓端增加可用额度");
        panel.addView(fieldBox("增加可用额度", amount));
        panel.addView(fieldBox("备注", note));
        AlertDialog dialog = buildGlassDialog("增加可用额度", panel);
        panel.addView(dialogButtons("取消", "提交", dialog, () -> {
            double value = numberOr(amount.getText().toString(), 0);
            if (value <= 0) throw new IllegalArgumentException("请填写大于 0 的额度");
            JSONObject body = new JSONObject();
            body.put("amount", value);
            body.put("note", note.getText().toString().trim());
            confirmAction("adjust-credit", item, body);
        }));
        dialog.show();
    }

    private void showCreditSetDialog(JSONObject item) {
        LinearLayout panel = dialogPanel();
        EditText credit = input("授信额度");
        EditText note = input("授信调整备注");
        credit.setInputType(InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_FLAG_DECIMAL);
        note.setMinLines(3);
        credit.setText(defaultValue("set-credit", item));
        note.setText("安卓端调整授信");
        panel.addView(fieldBox("授信额度", credit));
        panel.addView(fieldBox("备注", note));
        AlertDialog dialog = buildGlassDialog("调整授信", panel);
        panel.addView(dialogButtons("取消", "提交", dialog, () -> {
            JSONObject body = new JSONObject();
            body.put("credit_limit", numberOr(credit.getText().toString(), item.optDouble("approved_credit_limit", 1000)));
            body.put("note", note.getText().toString().trim());
            confirmAction("set-credit", item, body);
        }));
        dialog.show();
    }

    private void showRejectDialog(JSONObject item) {
        showNoteSubmitDialog("审批拒绝", "审批备注", defaultValue("reject", item), body -> {
            body.put("approved", false);
            String note = body.optString("review_note", "").trim();
            body.put("review_note", note.isEmpty() ? "资料不符合要求" : note);
            confirmAction("reject", item, body);
        });
    }

    private void showReviewNoteDialog(JSONObject item) {
        showNoteSubmitDialog("审批备注", "审批意见", item.optString("review_note", ""), body -> confirmAction("save-note", item, body));
    }

    private void showReviewerAssignDialog(JSONObject item) {
        run("加载审核员...", () -> {
            Map<String, String> params = new LinkedHashMap<>();
            params.put("stage", "review");
            JSONArray assignees = api.getArray("/admin/loan-assignees", params);
            JSONObject result = new JSONObject();
            result.put("items", assignees);
            return result;
        }, result -> renderReviewerAssignDialog(item, result.optJSONArray("items")));
    }

    private void renderReviewerAssignDialog(JSONObject item, JSONArray assignees) {
        LinearLayout panel = dialogPanel();
        TextView tip = text("先选择审核员，再点击确定完成转单。", 13, Ui.MUTED, Typeface.NORMAL);
        tip.setSingleLine(false);
        panel.addView(tip);
        panel.addView(space(8));
        AlertDialog dialog = buildGlassDialog("选择审核员", panel);
        if (assignees == null || assignees.length() == 0) {
            panel.addView(text("暂无可分配审核员", 14, Ui.MUTED, Typeface.NORMAL));
        } else {
            final int[] selectedId = new int[]{item.optInt("review_admin_id", 0)};
            final String[] selectedName = new String[]{item.optString("review_admin_name", "")};
            List<Button> buttons = new ArrayList<>();
            for (int i = 0; i < assignees.length(); i++) {
                JSONObject assignee = assignees.optJSONObject(i);
                if (assignee == null) continue;
                int adminId = assignee.optInt("id", 0);
                String username = assignee.optString("username", "");
                Button row = actionButton((adminId == selectedId[0] ? "已选 · " : "") + valueOr(username));
                LinearLayout.LayoutParams lp = matchHeight(44);
                lp.setMargins(0, 0, 0, dp(8));
                panel.addView(row, lp);
                buttons.add(row);
                row.setOnClickListener(v -> {
                    selectedId[0] = adminId;
                    selectedName[0] = username;
                    for (int j = 0; j < buttons.size(); j++) {
                        Button button = buttons.get(j);
                        JSONObject target = assignees.optJSONObject(j);
                        if (target == null) continue;
                        boolean selected = target.optInt("id", 0) == selectedId[0];
                        button.setText((selected ? "已选 · " : "") + valueOr(target.optString("username", "")));
                    }
                });
            }
            LinearLayout actions = row();
            Button cancel = dangerButton("取消");
            Button submit = primaryButton("确定");
            actions.addView(cancel, new LinearLayout.LayoutParams(0, dp(44), 1));
            actions.addView(space(8));
            actions.addView(submit, new LinearLayout.LayoutParams(0, dp(44), 1));
            panel.addView(actions);
            cancel.setOnClickListener(v -> dialog.dismiss());
            submit.setOnClickListener(v -> assignReviewer(item, selectedId[0], selectedName[0], dialog));
        }
        dialog.show();
    }

    private void assignReviewer(JSONObject item, int adminId, String username, AlertDialog dialog) {
        if (adminId <= 0) {
            toast("审核员无效");
            return;
        }
        JSONObject body = new JSONObject();
        try {
            body.put("stage", "review");
            body.put("admin_id", adminId);
        } catch (Exception ignored) {
            toast("转单参数生成失败");
            return;
        }
        int loanId = item.optInt("id", item.optInt("current_loan_id", 0));
        run("转单中...", () -> api.post("/admin/loans/" + loanId + "/assign", body), result -> {
            try {
                item.put("review_admin_id", result.optInt("assignee_id", adminId));
                item.put("review_admin_name", result.optString("assignee_name", username));
            } catch (Exception ignored) {
            }
            clearPageCache();
            if (dialog != null) dialog.dismiss();
            toast("转单完成");
            showDetail(item);
        });
    }

    private void takeOverReviewer(JSONObject item) {
        if (!canTakeOverReview(item)) {
            toast("当前申请不能转给自己");
            return;
        }
        assignReviewer(item, currentAdminId(), admin == null ? "" : admin.optString("username", ""), null);
    }

    private void showReconcileDialog(JSONObject item) {
        LinearLayout panel = dialogPanel();
        EditText received = input("登记收款");
        EditText reduction = input("减免金额");
        EditText otherFee = input("其他费用");
        EditText actualDate = input("实际还款日期");
        EditText note = input("平账说明");
        received.setInputType(InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_FLAG_DECIMAL);
        reduction.setInputType(InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_FLAG_DECIMAL);
        otherFee.setInputType(InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_FLAG_DECIMAL);
        actualDate.setSingleLine(true);
        actualDate.setText(defaultActualRepaymentDate(item));
        bindDatePicker(actualDate);
        note.setMinLines(3);
        received.setText(String.valueOf(item.optDouble("remaining_repayment_amount", 0)));
        reduction.setText(String.valueOf(item.optDouble("reduction_amount", 0)));
        otherFee.setText("0");
        note.setText("安卓端登记平账");
        panel.addView(fieldBox("登记收款", received));
        panel.addView(fieldBox("减免金额", reduction));
        panel.addView(fieldBox("其他费用", otherFee));
        panel.addView(fieldBox("实际还款日期", actualDate));
        panel.addView(fieldBox("备注", note));

        TextView receivedPreview = text("", 13, Ui.TEXT, Typeface.BOLD);
        TextView reductionPreview = text("", 13, Ui.TEXT, Typeface.BOLD);
        TextView otherFeePreview = text("", 13, Ui.TEXT, Typeface.BOLD);
        TextView totalPreview = text("", 13, Ui.TEXT, Typeface.BOLD);
        TextView remainingPreview = text("", 13, Ui.TEXT, Typeface.BOLD);
        LinearLayout preview = new LinearLayout(this);
        preview.setOrientation(LinearLayout.VERTICAL);
        preview.setPadding(dp(12), dp(10), dp(12), dp(10));
        preview.setBackground(tintGlassDrawable(Color.argb(188, 248, 250, 255)));
        preview.setElevation(dp(4));
        preview.addView(previewRow("平账后已还款额", receivedPreview));
        preview.addView(previewRow("平账后减免金额", reductionPreview));
        preview.addView(previewRow("平账后其他费用", otherFeePreview));
        preview.addView(previewRow("本次实际到账合计", totalPreview));
        preview.addView(previewRow("平账后剩余还款额", remainingPreview));
        panel.addView(preview);

        Runnable render = () -> {
            double nextReceived = item.optDouble("repaid_amount", 0) + numberOr(received.getText().toString(), 0);
            double nextReduction = item.optDouble("reduction_amount", 0) + numberOr(reduction.getText().toString(), 0);
            double nextOtherFee = item.optDouble("other_fee_amount", 0) + numberOr(otherFee.getText().toString(), 0);
            double totalRepayment = item.optDouble("total_repayment_amount", 0);
            double remaining = Math.max(totalRepayment - nextReceived - nextReduction, 0);
            receivedPreview.setText(formatMoney(nextReceived));
            reductionPreview.setText(formatMoney(nextReduction));
            otherFeePreview.setText(formatMoney(nextOtherFee));
            totalPreview.setText(formatMoney(numberOr(received.getText().toString(), 0) + numberOr(otherFee.getText().toString(), 0)));
            remainingPreview.setText(formatMoney(remaining));
        };
        TextWatcher watcher = new SimpleTextWatcher(render);
        received.addTextChangedListener(watcher);
        reduction.addTextChangedListener(watcher);
        otherFee.addTextChangedListener(watcher);

        AlertDialog dialog = buildGlassDialog("登记平账", panel);
        panel.addView(dialogButtons("关闭", "提交", dialog, () -> {
            JSONObject body = new JSONObject();
            body.put("received_amount", numberOr(received.getText().toString(), 0));
            body.put("reduction_amount", numberOr(reduction.getText().toString(), 0));
            body.put("other_fee_amount", numberOr(otherFee.getText().toString(), 0));
            body.put("actual_repayment_date", actualDate.getText().toString().trim());
            body.put("note", note.getText().toString().trim().isEmpty() ? "安卓端登记平账" : note.getText().toString().trim());
            confirmAction("reconcile", item, body);
        }));
        dialog.setOnShowListener(d -> render.run());
        dialog.show();
    }

    private String defaultActualRepaymentDate(JSONObject item) {
        String value = item.optString("actual_repayment_date", "");
        if (!isBlank(value) && value.length() >= 10) return value.substring(0, 10);
        return todayDateText();
    }

    private String todayDateText() {
        Calendar calendar = Calendar.getInstance();
        return String.format(
            Locale.ROOT,
            "%04d-%02d-%02d",
            calendar.get(Calendar.YEAR),
            calendar.get(Calendar.MONTH) + 1,
            calendar.get(Calendar.DAY_OF_MONTH)
        );
    }

    private void showNoteSubmitDialog(String title, String label, String initialValue, DialogSubmit submit) {
        LinearLayout panel = dialogPanel();
        EditText note = input(label);
        note.setMinLines(3);
        note.setText(initialValue);
        panel.addView(fieldBox(label, note));
        AlertDialog dialog = buildGlassDialog(title, panel);
        panel.addView(dialogButtons("关闭", "提交", dialog, () -> {
            JSONObject body = new JSONObject();
            body.put("review_note", note.getText().toString().trim());
            submit.apply(body);
        }));
        dialog.show();
    }

    private void showNoteActionDialog(String action, JSONObject item, String title, String label, String initialValue, String bodyKey) {
        LinearLayout panel = dialogPanel();
        EditText note = input(label);
        note.setMinLines(3);
        note.setText(initialValue);
        panel.addView(fieldBox(label, note));
        AlertDialog dialog = buildGlassDialog(title, panel);
        panel.addView(dialogButtons("取消", isDangerAction(action) ? "确认" : "提交", dialog, () -> {
            JSONObject body = new JSONObject();
            String value = note.getText().toString().trim();
            body.put(bodyKey, value.isEmpty() ? initialValue : value);
            confirmAction(action, item, body);
        }));
        dialog.show();
    }

    private LinearLayout dialogPanel() {
        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setPadding(0, dp(8), 0, 0);
        return panel;
    }

    private LinearLayout fieldBox(String label, EditText input) {
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.addView(text(label, 13, Ui.MUTED, Typeface.BOLD));
        box.addView(space(6));
        input.setGravity(input.getMinLines() > 1 ? (Gravity.TOP | Gravity.START) : Gravity.CENTER_VERTICAL);
        box.addView(input, matchHeight(input.getMinLines() > 1 ? 112 : 48));
        box.addView(space(12));
        return box;
    }

    private AlertDialog buildGlassDialog(String title, LinearLayout body) {
        LinearLayout shell = new LinearLayout(this);
        shell.setOrientation(LinearLayout.VERTICAL);
        shell.setPadding(dp(18), dp(18), dp(18), dp(16));
        shell.setBackground(gcpCardDrawable());
        TextView titleView = text(title, 22, Ui.TEXT, Typeface.BOLD);
        titleView.setPadding(dp(2), 0, dp(2), dp(8));
        shell.addView(titleView, matchWrap());
        shell.addView(body, matchWrap());
        AlertDialog dialog = new AlertDialog.Builder(this).setView(shell).create();
        dialog.setOnShowListener(d -> {
            if (dialog.getWindow() != null) {
                dialog.getWindow().setBackgroundDrawable(new ColorDrawable(Color.TRANSPARENT));
                dialog.getWindow().setDimAmount(0.48f);
            }
        });
        return dialog;
    }

    private LinearLayout compactSummaryBox(String[][] rows) {
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(dp(12), dp(10), dp(12), dp(10));
        box.setBackground(roundRect(Color.WHITE, dp(16), Ui.BORDER));
        box.setElevation(dp(2));
        for (String[] row : rows) {
            box.addView(previewRow(row[0], text(row[1], 13, Ui.TEXT, Typeface.BOLD)));
        }
        LinearLayout.LayoutParams lp = matchWrap();
        lp.setMargins(0, 0, 0, dp(12));
        box.setLayoutParams(lp);
        return box;
    }

    private boolean isDangerAction(String action) {
        return "blacklist".equals(action) || "reject".equals(action) || "reject-card".equals(action);
    }

    private LinearLayout previewRow(String label, TextView valueView) {
        LinearLayout line = row();
        line.setPadding(0, dp(4), 0, dp(4));
        line.addView(text(label, 12, Ui.MUTED, Typeface.NORMAL), new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        line.addView(valueView);
        return line;
    }

    private LinearLayout dialogButtons(String cancelText, String submitText, AlertDialog dialog, DialogAction action) {
        LinearLayout row = row();
        Button cancel = dangerButton(cancelText);
        Button submit = actionButton(submitText);
        row.addView(cancel, new LinearLayout.LayoutParams(0, dp(44), 1));
        row.addView(space(8));
        row.addView(submit, new LinearLayout.LayoutParams(0, dp(44), 1));
        cancel.setOnClickListener(v -> dialog.dismiss());
        submit.setOnClickListener(v -> {
            try {
                action.run();
                dialog.dismiss();
            } catch (Exception error) {
                toast(error.getMessage() == null ? "提交失败" : error.getMessage());
            }
        });
        return row;
    }

    private void confirmAction(String action, JSONObject item, JSONObject body) {
        run("处理中...", () -> {
            int loanId = item.optInt("id", item.optInt("current_loan_id"));
            int userId = item.optInt("user_id", item.optInt("owner_id", item.optInt("id")));
            String status = actionStatus(item);
            if ("disburse".equals(action) && !"WITHDRAWING".equals(status)) {
                throw new IllegalArgumentException("当前订单状态不是待发卡，请刷新后再处理");
            }
            if ("reject-card".equals(action) && !"WITHDRAWING".equals(status)) {
                throw new IllegalArgumentException("当前订单状态不是待发卡，不能拒绝发卡");
            }
            if ("reissue-card".equals(action) && !"CARD_REJECTED".equals(status)) {
                throw new IllegalArgumentException("仅拒发卡订单支持二次发卡");
            }
            if ("close-reissue".equals(action) && !("WITHDRAWING".equals(status) || "CARD_REJECTED".equals(status))) {
                throw new IllegalArgumentException("当前订单无需退回待下单");
            }
            if ("approve".equals(action)) api.post("/admin/loans/" + loanId + "/review", body);
            else if ("reject".equals(action)) api.post("/admin/loans/" + loanId + "/review", body);
            else if ("disburse".equals(action)) api.post("/admin/loans/" + loanId + "/disburse", body);
            else if ("reject-card".equals(action)) api.post("/admin/loans/" + loanId + "/reject-card", body);
            else if ("save-note".equals(action)) api.patch("/admin/loans/" + loanId, body);
            else if ("remind".equals(action)) api.post("/admin/loans/" + loanId + "/remind", body);
            else if ("collect".equals(action)) api.post("/admin/loans/" + loanId + "/collect", body);
            else if ("ack".equals(action)) api.post("/admin/loans/" + loanId + "/ack-repay-attempt", body);
            else if ("reconcile".equals(action)) api.post("/admin/loans/" + loanId + "/finance-reconcile", body);
            else if ("settle".equals(action)) api.post("/admin/loans/" + loanId + "/settle", body);
            else if ("extend".equals(action)) api.post("/admin/loans/" + loanId + "/extend", body);
            else if ("adjust-credit".equals(action)) api.post("/admin/loans/" + loanId + "/available-credit/adjust", body);
            else if ("set-credit".equals(action)) api.post("/admin/loans/" + loanId + "/approved-credit/set", body);
            else if ("blacklist".equals(action)) api.post("/admin/users/" + userId + "/blacklist", body);
            else if ("remove-blacklist".equals(action)) api.post("/admin/users/" + userId + "/blacklist/remove", body);
            else if ("unlock-location".equals(action)) api.post("/admin/users/" + userId + "/location-risk/unlock", body);
            else if ("reissue-card".equals(action)) api.post("/admin/loans/" + loanId + "/reissue-card", body);
            else if ("close-reissue".equals(action)) api.post("/admin/loans/" + loanId + "/close-card-reissue", body);
            return null;
        }, ignored -> {
            clearPageCache();
            toast("处理完成");
            showWorkspace();
        });
    }

    private List<String[]> actionsForCurrentTab(JSONObject item) {
        List<String[]> actions = new ArrayList<>();
        String status = actionStatus(item);
        if ("profiles".equals(activeTab)) {
            if (hasPermission("user-location-risk-unlock") && hasLoginDisplacementRisk(item)) actions.add(new String[]{"unlock-location", "解除位移风控"});
            if (hasPermission("blacklist")) actions.add(blacklistAction(item));
            if (hasPermission("disbursements") && item.optInt("current_loan_id", 0) > 0 && "CARD_REJECTED".equals(status)) actions.add(new String[]{"reissue-card", "开启二次发卡"});
            if ((hasPermission("users") || hasPermission("disbursements")) && item.optInt("current_loan_id", 0) > 0 && ("WITHDRAWING".equals(status) || "CARD_REJECTED".equals(status))) actions.add(new String[]{"close-reissue", "退回待下单"});
        } else if ("applications".equals(activeTab)) {
            if (canTakeOverReview(item)) actions.add(new String[]{"takeover-review", "转给我"});
            if (hasPermission("applications") && "REVIEWING".equals(status)) {
                actions.add(new String[]{"approve", "审批通过"});
                actions.add(new String[]{"reject", "审批拒绝"});
                actions.add(new String[]{"set-credit", "调整授信"});
                actions.add(new String[]{"adjust-credit", "增加可用额度"});
            }
            if (hasPermission("applications")) actions.add(new String[]{"save-note", "审批备注"});
            if (hasPermission("blacklist")) actions.add(blacklistAction(item));
        } else if ("cards".equals(activeTab)) {
            if (hasPermission("disbursements") && "WITHDRAWING".equals(status)) {
                actions.add(new String[]{"disburse", "确认发卡"});
                actions.add(new String[]{"reject-card", "拒绝发卡"});
                actions.add(new String[]{"close-reissue", "退回待下单"});
            }
            if (hasPermission("disbursements")) actions.add(new String[]{"save-note", "保存备注"});
            if (hasPermission("blacklist")) actions.add(blacklistAction(item));
        } else if ("repayments".equals(activeTab)) {
            if (hasPermission("collections") && "OVERDUE".equals(status)) {
                actions.add(new String[]{"collect", "登记催收"});
            } else if (hasPermission("repayments") && "DISBURSED".equals(status)) {
                actions.add(new String[]{"remind", "登记提醒"});
            }
            if ((hasPermission("repayments") || hasPermission("collections")) && item.optInt("repay_attempt_count", 0) > 0) actions.add(new String[]{"ack", "确认还款申请"});
            if ((hasPermission("repayments") || hasPermission("collections")) && ("DISBURSED".equals(status) || "OVERDUE".equals(status))) {
                actions.add(new String[]{"extend", "账单展期"});
            }
            if (("OVERDUE".equals(status) ? hasPermission("collections") : hasPermission("applications")) && ("DISBURSED".equals(status) || "OVERDUE".equals(status))) actions.add(new String[]{"adjust-credit", "增加可用额度"});
            if (hasPermission("blacklist")) actions.add(blacklistAction(item));
        } else {
            if (hasPermission("financials") && ("DISBURSED".equals(status) || "OVERDUE".equals(status))) {
                actions.add(new String[]{"reconcile", "登记平账"});
                actions.add(new String[]{"settle", "确认结清"});
            }
        }
        return actions;
    }

    private boolean hasLoginDisplacementRisk(JSONObject item) {
        if (!item.optBoolean("location_risk_blocked")) return false;
        String reason = item.optString("location_risk_reason", "");
        return isBlank(reason)
            || reason.contains("登录位置异常")
            || reason.contains("小时内")
            || reason.contains("公里");
    }

    private String[] blacklistAction(JSONObject item) {
        boolean hit = item.optBoolean("blacklist_hit")
            || item.optBoolean("user_blacklist_hit")
            || item.optBoolean("current_blacklist_hit");
        return new String[]{hit ? "remove-blacklist" : "blacklist", hit ? "移出黑名单" : "一键拉黑"};
    }

    private String actionStatus(JSONObject item) {
        String status = item.optString("status", "");
        if (isBlank(status)) status = item.optString("current_loan_status", "");
        return status == null ? "" : status.toUpperCase(Locale.ROOT);
    }

    private void fillPayload(String action, String text, JSONObject item, JSONObject body) throws Exception {
        if ("approve".equals(action)) {
            body.put("approved", true);
            body.put("credit_limit", numberOr(text, item.optDouble("approved_credit_limit", 1000)));
            body.put("approval_discount_amount", 0);
            body.put("term_days", item.optInt("term_days", item.optInt("product_term_days", 7)));
            body.put("review_note", "安卓端审批通过");
        } else if ("reject".equals(action)) {
            body.put("approved", false);
            body.put("review_note", text.isEmpty() ? "资料不符合要求" : text);
        } else if ("disburse".equals(action)) {
            body.put("term_days", (int) numberOr(text, item.optInt("term_days", item.optInt("product_term_days", 7))));
        } else if ("reconcile".equals(action)) {
            body.put("received_amount", numberOr(text, item.optDouble("remaining_repayment_amount", 0)));
            body.put("reduction_amount", 0);
            body.put("note", "安卓端登记平账");
        } else if ("extend".equals(action)) {
            body.put("extension_type", "FREE");
            body.put("days", (int) numberOr(text, 3));
            body.put("reduction_amount", 0);
            body.put("note", "安卓端账单展期");
        } else if ("adjust-credit".equals(action)) {
            body.put("amount", numberOr(text, 100));
            body.put("note", "安卓端增加可用额度");
        } else if ("set-credit".equals(action)) {
            body.put("credit_limit", numberOr(text, item.optDouble("approved_credit_limit", 1000)));
            body.put("note", "安卓端调整授信");
        } else if ("save-note".equals(action)) {
            body.put("review_note", text);
        } else {
            body.put("note", text.isEmpty() ? actionTitle(action) : text);
        }
    }

    private void addSegment(LinearLayout content) {
        LinearLayout row = row();
        Button today = segment("当日还款", "REPAYMENTS".equals(segmentScope));
        Button overdue = segment("逾期催收", "OVERDUE".equals(segmentScope));
        row.addView(today, new LinearLayout.LayoutParams(0, dp(42), 1));
        row.addView(space(8));
        row.addView(overdue, new LinearLayout.LayoutParams(0, dp(42), 1));
        content.addView(row);
        content.addView(space(12));
        today.setOnClickListener(v -> { segmentScope = "REPAYMENTS"; showWorkspace(); });
        overdue.setOnClickListener(v -> { segmentScope = "OVERDUE"; showWorkspace(); });
    }

    private void addTabs(LinearLayout page) {
        LinearLayout tabs = new LinearLayout(this);
        tabs.setOrientation(LinearLayout.HORIZONTAL);
        tabs.setPadding(dp(12), dp(8), dp(12), dp(8));
        tabs.setBackground(roundRect(Color.WHITE, 0, 0));
        tabs.setElevation(dp(2));
        page.addView(tabs, matchWrap());
        for (String[] tab : visibleTabs()) {
            boolean active = tab[0].equals(activeTab);
            TextView button = text("", 12, active ? Ui.BLUE : Ui.MUTED, active ? Typeface.BOLD : Typeface.NORMAL);
            button.setText(tabLabel(tab[0], tab[1]));
            button.setGravity(Gravity.CENTER);
            button.setClickable(true);
            button.setLineSpacing(dp(2), 1.0f);
            button.setBackground(roundRect(0x00000000, 0, 0));
            tabs.addView(button, new LinearLayout.LayoutParams(0, dp(58), 1));
            button.setOnClickListener(v -> { activeTab = tab[0]; keyword = ""; showWorkspace(); });
        }
    }

    private SpannableString tabLabel(String tab, String label) {
        String icon = tabIcon(tab);
        SpannableString text = new SpannableString(icon + "\n" + label);
        text.setSpan(new RelativeSizeSpan(1.85f), 0, icon.length(), Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
        return text;
    }

    private List<String[]> visibleTabs() {
        List<String[]> tabs = new ArrayList<>();
        if (hasPermission("users")) tabs.add(new String[]{"profiles", "档案"});
        if (hasPermission("applications")) tabs.add(new String[]{"applications", "申请"});
        if (hasPermission("disbursements")) tabs.add(new String[]{"cards", "发卡"});
        if (hasPermission("repayments") || hasPermission("collections")) tabs.add(new String[]{"repayments", "回款"});
        if (hasPermission("financials")) tabs.add(new String[]{"finance", "平账"});
        if (tabs.isEmpty()) tabs.add(new String[]{"profiles", "档案"});
        boolean found = false;
        for (String[] tab : tabs) found = found || tab[0].equals(activeTab);
        if (!found) activeTab = tabs.get(0)[0];
        return tabs;
    }

    private boolean hasAny(String... values) {
        JSONArray roles = admin == null ? null : admin.optJSONArray("roles");
        if (roles == null) return false;
        for (int i = 0; i < roles.length(); i++) {
            String role = roles.optString(i);
            for (String value : values) if (value.equals(role)) return true;
        }
        return false;
    }

    private int currentAdminId() {
        return admin == null ? 0 : admin.optInt("id", 0);
    }

    private boolean canUseReviewTakeoverPool() {
        return !hasAny("ADMIN") && hasAny("REVIEW") && hasPermission("loan-review-takeover");
    }

    private boolean canTakeOverReview(JSONObject item) {
        int currentId = currentAdminId();
        int reviewAdminId = item == null ? 0 : item.optInt("review_admin_id", 0);
        return canUseReviewTakeoverPool()
            && currentId > 0
            && item != null
            && "REVIEWING".equals(actionStatus(item))
            && reviewAdminId != currentId;
    }

    private boolean hasPermission(String permission) {
        if (hasAny("ADMIN")) return true;
        JSONArray permissions = admin == null ? null : admin.optJSONArray("permissions");
        if (permissions != null) {
            for (int i = 0; i < permissions.length(); i++) {
                if (permission.equals(permissions.optString(i))) return true;
            }
            return false;
        }
        if ("users".equals(permission)) return hasAny("REVIEW", "BUSINESS_CONSULTANT");
        if ("applications".equals(permission)) return hasAny("REVIEW");
        if ("disbursements".equals(permission) || "financials".equals(permission)) return hasAny("FINANCE");
        if ("repayments".equals(permission)) return hasAny("REVIEW");
        if ("collections".equals(permission)) return hasAny("COLLECTION");
        if ("blacklist".equals(permission)) return hasAny("REVIEW", "FINANCE", "COLLECTION");
        if ("loan-review-takeover".equals(permission)) return hasAny("REVIEW");
        return false;
    }

    private void confirmLogout() {
        new AlertDialog.Builder(this)
            .setTitle("退出当前账号？")
            .setPositiveButton("登出", (d, w) -> { api.logout(); admin = null; showLogin(); })
            .setNegativeButton("取消", null)
            .show();
    }

    @Override
    public void onBackPressed() {
        if (detailOpen) {
            showWorkspace();
            return;
        }
        super.onBackPressed();
    }

    private interface Task { JSONObject run() throws Exception; }
    private interface Done { void apply(JSONObject result); }
    private interface FilterSetter { void apply(String value); }
    private interface DialogAction { void run() throws Exception; }
    private interface DialogSubmit { void apply(JSONObject body) throws Exception; }

    private void run(String loading, Task task, Done done) {
        if (loading != null) toast(loading);
        worker.execute(() -> {
            try {
                JSONObject result = task.run();
                main.post(() -> done.apply(result));
            } catch (Exception error) {
                main.post(() -> {
                    if (error instanceof ApiClient.ApiException && ((ApiClient.ApiException) error).status == 401) {
                        api.logout();
                        showLogin();
                    }
                    toast(error.getMessage() == null ? "请求失败" : error.getMessage());
                });
            }
        });
    }

    private Map<String, String> baseQuery() {
        Map<String, String> q = new LinkedHashMap<>();
        q.put("skip", "0");
        q.put("limit", "20");
        return q;
    }

    private void applyOverdueQuery(Map<String, String> q) {
        String value = "finance".equals(activeTab) ? financeOverdueFilter : repaymentOverdueFilter;
        if ("OVERDUE".equals(value)) {
            q.put("status", "OVERDUE");
        } else if ("NOT_OVERDUE".equals(value)) {
            q.put("status", "DISBURSED");
        }
    }

    private void applyDueDateQuery(Map<String, String> q) {
        if ("repayments".equals(activeTab)) {
            if (!isBlank(repaymentStartDate)) q.put("due_date_start", repaymentStartDate);
            if (!isBlank(repaymentEndDate)) q.put("due_date_end", repaymentEndDate);
        }
    }

    private Map<String, String> repaymentStatsQuery() {
        Map<String, String> q = new LinkedHashMap<>();
        if ("repayments".equals(activeTab)) {
            if (!isBlank(repaymentStartDate)) q.put("due_date_start", repaymentStartDate);
            if (!isBlank(repaymentEndDate)) q.put("due_date_end", repaymentEndDate);
        }
        return q.isEmpty() ? null : q;
    }

    private boolean hasRepaymentDateRange() {
        return !isBlank(repaymentStartDate) || !isBlank(repaymentEndDate);
    }

    private String scopeForTab(String tab) {
        if ("applications".equals(tab)) return "REVIEWING";
        if ("cards".equals(tab)) return "WITHDRAWING";
        if ("repayments".equals(tab)) return "REPAYMENTS";
        if ("finance".equals(tab)) return "FINANCE";
        return "";
    }

    private String tabTitle(String tab) {
        if ("applications".equals(tab)) return "申请审批";
        if ("cards".equals(tab)) return "待发卡";
        if ("repayments".equals(tab)) return "回款管理";
        if ("finance".equals(tab)) return "财务平账";
        return "客户档案";
    }

    private String tabIcon(String tab) {
        if ("applications".equals(tab)) return "▣";
        if ("cards".equals(tab)) return "▱";
        if ("repayments".equals(tab)) return "↩";
        if ("finance".equals(tab)) return "▤";
        return "□";
    }

    private String displayName(JSONObject item) {
        String value = "profiles".equals(activeTab) ? item.optString("name", "未实名") : item.optString("user_name", "未实名");
        return isBlank(value) || "null".equalsIgnoreCase(value) ? "未实名" : value;
    }

    private String riskText(JSONObject item) {
        List<String> tags = new ArrayList<>();
        if (item.optBoolean("blacklist_hit") || item.optBoolean("user_blacklist_hit") || item.optBoolean("current_blacklist_hit")) tags.add("黑名单");
        if (item.optBoolean("risk_list_hit") || item.optBoolean("user_risk_list_hit") || item.optBoolean("current_risk_list_hit")) tags.add("风险名单");
        if (item.optBoolean("user_location_risk_hit") || item.optBoolean("location_risk_hit")) tags.add("风险地区");
        if (item.optBoolean("location_risk_blocked")) tags.add("位置风控");
        if (tags.isEmpty()) return "";
        StringBuilder builder = new StringBuilder("  ");
        for (int i = 0; i < tags.size(); i++) {
            if (i > 0) builder.append(' ');
            builder.append(tags.get(i));
        }
        return builder.toString();
    }

    private void addRiskTags(LinearLayout row, JSONObject item, boolean detail) {
        List<String> tags = riskLabels(item);
        for (String tag : tags) {
            TextView view = riskPill(tag, detail);
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(LinearLayout.LayoutParams.WRAP_CONTENT, LinearLayout.LayoutParams.WRAP_CONTENT);
            lp.setMargins(dp(5), 0, 0, 0);
            row.addView(view, lp);
        }
    }

    private List<String> riskLabels(JSONObject item) {
        List<String> tags = new ArrayList<>();
        if (item.optBoolean("blacklist_hit") || item.optBoolean("user_blacklist_hit") || item.optBoolean("current_blacklist_hit")) tags.add("黑名单");
        if (item.optBoolean("risk_list_hit") || item.optBoolean("user_risk_list_hit") || item.optBoolean("current_risk_list_hit")) tags.add("风险名单");
        if (item.optBoolean("user_location_risk_hit") || item.optBoolean("location_risk_hit")) tags.add("风险地区");
        if (item.optBoolean("location_risk_blocked")) tags.add("位置风控");
        return tags;
    }

    private TextView riskPill(String label, boolean detail) {
        int bg = Color.rgb(252, 232, 230);
        int fg = Ui.RED;
        if ("风险地区".equals(label) || "位置风控".equals(label)) {
            bg = Color.rgb(254, 247, 224);
            fg = Color.rgb(176, 96, 0);
        }
        TextView view = text(label, detail ? 11 : 10, fg, Typeface.BOLD);
        view.setGravity(Gravity.CENTER);
        view.setPadding(dp(7), dp(3), dp(7), dp(3));
        view.setBackground(roundRect(bg, dp(999), 0));
        return view;
    }

    private TextView glassBadge(String value) {
        TextView view = text(value, 12, Ui.BLUE, Typeface.BOLD);
        view.setPadding(dp(14), 0, dp(14), 0);
        view.setBackground(roundRect(Color.WHITE, dp(14), Ui.BORDER));
        return view;
    }

    private String subtitle(JSONObject item) {
        String phone = "profiles".equals(activeTab) ? item.optString("phone", "") : item.optString("user_phone", "");
        String channel = item.optString("source_channel_name", item.optString("user_source_channel_name", "自然流量"));
        return valueOr(phone) + " · " + (channel.isEmpty() ? "自然流量" : channel);
    }

    private String reviewerName(JSONObject item) {
        return valueOr(item.optString("review_admin_name", ""));
    }

    private String rawUserPhone(JSONObject item) {
        String phone = "profiles".equals(activeTab) ? item.optString("phone", "") : item.optString("user_phone", "");
        return valueOr(phone);
    }

    private String detailPrimaryTimeText(JSONObject item) {
        if ("profiles".equals(activeTab)) {
            return dateTimeText(detailUser(item).optString("created_at", item.optString("created_at", "")));
        }
        if ("applications".equals(activeTab)) {
            return dateTimeText(item.optString("application_submitted_at", item.optString("created_at", "")));
        }
        if ("cards".equals(activeTab)) {
            return dateTimeText(
                item.optString(
                    "ordered_at",
                    item.optString("application_submitted_at", item.optString("created_at", ""))
                )
            );
        }
        if ("repayments".equals(activeTab) || "finance".equals(activeTab)) {
            return dateTimeText(item.optString("due_date", ""));
        }
        return dateTimeText(item.optString("created_at", ""));
    }

    private String detailPrimaryTimeLabel() {
        if ("profiles".equals(activeTab)) return "注册时间";
        if ("applications".equals(activeTab)) return "申请时间";
        if ("cards".equals(activeTab)) return "下单时间";
        if ("repayments".equals(activeTab) || "finance".equals(activeTab)) return "应还款时间";
        return "提交时间";
    }

    private String channelText(JSONObject item) {
        return valueOr(item.optString("source_channel_name", item.optString("user_source_channel_name", item.optString("user_source_channel_sales_name", "自然流量"))));
    }

    private String latestIpText(JSONObject item) {
        JSONObject latest = latestIpEvent(item);
        return latest == null ? "--" : valueOr(latest.optString("ip", ""));
    }

    private String latestIpLocationText(JSONObject item) {
        JSONObject latest = latestIpEvent(item);
        return latest == null ? "" : auditAddressText(latest);
    }

    private String latestGpsText(JSONObject item) {
        JSONObject event = latestGpsEvent(item);
        if (event == null) return "--";
        String lonLat = event.optString("lon_lat", "");
        if (!isBlank(lonLat)) return lonLat;
        JSONObject user = detailUser(item);
        return coordinateText(user);
    }

    private String latestGpsLocationText(JSONObject item) {
        JSONObject event = latestGpsEvent(item);
        if (event != null) {
            StringBuilder builder = new StringBuilder();
            appendAddressPart(builder, event.optString("lon_lat_province", ""));
            appendAddressPart(builder, event.optString("lon_lat_city", ""));
            appendAddressPart(builder, event.optString("lon_lat_district", ""));
            appendAddressPart(builder, event.optString("lon_lat_detail", ""));
            return builder.toString();
        }
        String location = locationText(detailUser(item));
        return "--".equals(location) ? "" : location;
    }

    private JSONObject latestIpEvent(JSONObject item) {
        JSONObject user = detailUser(item);
        JSONObject audit = user.optJSONObject("_ip_audit");
        JSONArray items = audit == null ? null : audit.optJSONArray("items");
        return items == null || items.length() == 0 ? null : items.optJSONObject(0);
    }

    private JSONObject latestGpsEvent(JSONObject item) {
        JSONObject user = detailUser(item);
        JSONArray events = user.optJSONArray("events");
        if (events == null) return null;
        for (int i = 0; i < events.length(); i++) {
            JSONObject event = events.optJSONObject(i);
            if (event != null && !isBlank(event.optString("lon_lat", ""))) return event;
        }
        return null;
    }

    private String dateText(JSONObject item) {
        String value = item.optString("due_date", item.optString("application_submitted_at", item.optString("created_at", "")));
        return value.length() >= 10 ? value.substring(0, 10) : "--";
    }

    private String dateLabel(JSONObject item) {
        if ("profiles".equals(activeTab)) return "注册时间";
        return item.optString("due_date", "").isEmpty() ? "提交时间" : "还款日";
    }

    private String amountLabel() {
        if ("profiles".equals(activeTab)) return "授信额度";
        if ("cards".equals(activeTab)) return "订单支付";
        return "待处理金额";
    }

    private String noteText(JSONObject item) {
        String note = item.optString("product_name", "");
        if (note.isEmpty()) note = item.optString("review_note", "");
        if (note.isEmpty()) note = item.optString("collection_note", "");
        return note;
    }

    private double amount(JSONObject item) {
        String[] keys = {"remaining_repayment_amount", "product_total_price", "total_repayment_amount", "approved_credit_limit", "credit_limit", "approved_limit"};
        for (String key : keys) if (item.optDouble(key, 0) > 0) return item.optDouble(key, 0);
        return 0;
    }

    private String statusText(JSONObject item) {
        JSONObject latest = item.optJSONObject("latest_loan");
        String status = item.optString("status", "");
        if (isBlank(status)) {
            status = latest != null ? latest.optString("status", item.optString("face_auth_status", "")) : item.optString("face_auth_status", "");
        }
        Map<String, String> map = new HashMap<>();
        map.put("INIT", "待补资料"); map.put("REVIEWING", "审核中"); map.put("APPROVED", "待下单");
        map.put("REJECTED", "未通过"); map.put("WITHDRAWING", "待发卡"); map.put("DISBURSED", "待付款");
        map.put("SETTLED", "已结清"); map.put("OVERDUE", "已逾期"); map.put("CARD_REJECTED", "拒发卡");
        return map.containsKey(status) ? map.get(status) : (status.isEmpty() ? "--" : status);
    }

    private int statusColor(JSONObject item) {
        String status = item.optString("status", "");
        if ("OVERDUE".equals(status) || "REJECTED".equals(status) || "CARD_REJECTED".equals(status)) return Color.rgb(252, 232, 230);
        if ("REVIEWING".equals(status) || "WITHDRAWING".equals(status)) return Color.rgb(254, 247, 224);
        if ("DISBURSED".equals(status) || "APPROVED".equals(status)) return Color.rgb(230, 244, 234);
        return Color.rgb(241, 243, 244);
    }

    private int statusTextColor(JSONObject item) {
        String status = item.optString("status", "");
        if ("OVERDUE".equals(status) || "REJECTED".equals(status) || "CARD_REJECTED".equals(status)) return Ui.RED;
        if ("REVIEWING".equals(status) || "WITHDRAWING".equals(status)) return Color.rgb(176, 96, 0);
        if ("DISBURSED".equals(status) || "APPROVED".equals(status)) return Color.rgb(19, 115, 51);
        return Ui.MUTED;
    }

    private String[][] coreRows(JSONObject item) {
        JSONObject user = detailUser(item);
        if ("profiles".equals(activeTab)) {
            JSONObject latest = user.optJSONObject("latest_loan");
            return new String[][]{
                {"手机号", valueOr(user.optString("phone", ""))},
                {"身份证", valueOr(user.optString("id_card_num", ""))},
                {"渠道", valueOr(user.optString("source_channel_name", user.optString("source_channel_sales_name", "")))},
                {"最新状态", statusText(user)},
                {"授信额度", formatMoney(user.optDouble("approved_limit", latest == null ? 0 : latest.optDouble("approved_credit_limit", 0)))},
                {"注册时间", dateTimeText(user.optString("created_at", ""))},
                {"位置风控", user.optBoolean("location_risk_blocked") ? valueOr(user.optString("location_risk_reason", "已锁定")) : "未锁定"},
                {"风险校验", riskText(user).trim().isEmpty() ? "未命中" : riskText(user).trim()}
            };
        }
        return new String[][]{
            {"状态", statusText(item)},
            {"手机号", valueOr(item.optString("user_phone", ""))},
            {"身份证", valueOr(item.optString("user_id_card_num", ""))},
            {"渠道", valueOr(item.optString("user_source_channel_name", item.optString("user_source_channel_sales_name", "")))},
            {"复购", valueOr(item.optString("relend_label", "初借"))},
            {detailPrimaryTimeLabel(), detailPrimaryTimeText(item)},
            {"其他费用", formatMoney(item.optDouble("other_fee_amount", 0))},
            {"风险校验", riskText(item).trim().isEmpty() ? "未命中" : riskText(item).trim()}
        };
    }

    private String[][] emergencyRows(JSONObject user) {
        return new String[][]{
            {"联系人1", contactText(user, "emergency_contact1")},
            {"联系人2", contactText(user, "emergency_contact2")}
        };
    }

    private String contactText(JSONObject user, String prefix) {
        String name = user.optString(prefix + "_name", "");
        String relation = user.optString(prefix + "_relation", "");
        String phone = user.optString(prefix + "_phone", "");
        if (isBlank(name) && isBlank(relation) && isBlank(phone)) return "--";
        return valueOr(name) + " / " + valueOr(relation) + " / " + valueOr(phone);
    }

    private String[][] locationRows(JSONObject user) {
        return new String[][]{
            {"定位地址", locationText(user)},
            {"经纬度", coordinateText(user)},
            {"定位精度", valueOr(user.optString("location_accuracy", ""))},
            {"定位来源", valueOr(user.optString("location_source", ""))},
            {"更新时间", dateTimeText(user.optString("location_updated_at", ""))},
            {"位置风控", user.optBoolean("location_risk_blocked") ? valueOr(user.optString("location_risk_reason", "已锁定")) : "未锁定"}
        };
    }

    private String[][] ipRows(JSONObject user) {
        JSONObject audit = user.optJSONObject("_ip_audit");
        JSONArray items = audit == null ? null : audit.optJSONArray("items");
        if (items == null || items.length() == 0) {
            return new String[][]{{"最近记录", "--"}};
        }
        int count = Math.min(items.length(), 3);
        String[][] rows = new String[count][];
        for (int i = 0; i < count; i++) {
            JSONObject item = items.optJSONObject(i);
            String address = auditAddressText(item);
            rows[i] = new String[]{"记录" + (i + 1), valueOr(item.optString("ip", "")) + " / " + address + " / " + dateTimeText(item.optString("created_at", ""))};
        }
        return rows;
    }

    private String[][] orderAuditRows(JSONObject item) {
        JSONObject loan = latestLoanForDetail(item);
        return new String[][]{
            {"订单状态", statusText(loan)},
            {"复购", valueOr(loan.optString("relend_label", item.optString("relend_label", "初借")))},
            {"审批备注", valueOr(loan.optString("review_note", item.optString("review_note", "")))},
            {"催收备注", valueOr(loan.optString("collection_note", item.optString("collection_note", "")))},
            {"提交时间", dateTimeText(loan.optString("application_submitted_at", item.optString("application_submitted_at", item.optString("created_at", ""))))},
            {"还款日", dateTimeText(loan.optString("due_date", item.optString("due_date", "")))}
        };
    }

    private String[][] orderRows(JSONObject item) {
        return new String[][]{
            {"商品", valueOr(item.optString("product_name", ""))},
            {"订单金额", formatMoney(amount(item))},
            {"剩余应还", formatMoney(item.optDouble("remaining_repayment_amount", 0))},
            {"还款日", valueOr(item.optString("due_date", "").length() >= 10 ? item.optString("due_date", "").substring(0, 10) : "")},
            {"审批备注", valueOr(item.optString("review_note", ""))},
            {"催收备注", valueOr(item.optString("collection_note", ""))}
        };
    }

    private JSONObject detailUser(JSONObject item) {
        JSONObject user = item.optJSONObject("_user_detail");
        return user == null ? item : user;
    }

    private JSONObject latestLoanForDetail(JSONObject item) {
        if (!"profiles".equals(activeTab) && !item.has("latest_loan")) return item;
        JSONObject latest = detailUser(item).optJSONObject("latest_loan");
        return latest == null ? item : latest;
    }

    private int resolveUserId(JSONObject item) {
        int userId = item.optInt("user_id", 0);
        if (userId <= 0) userId = item.optInt("owner_id", 0);
        if (userId <= 0) userId = item.optInt("id", 0);
        return userId;
    }

    private String locationText(JSONObject user) {
        StringBuilder builder = new StringBuilder();
        appendAddressPart(builder, user.optString("location_province", ""));
        appendAddressPart(builder, user.optString("location_city", ""));
        appendAddressPart(builder, user.optString("location_district", ""));
        appendAddressPart(builder, user.optString("location_street", ""));
        appendAddressPart(builder, user.optString("location_address", ""));
        return builder.length() == 0 ? "--" : builder.toString();
    }

    private String coordinateText(JSONObject user) {
        String lat = user.optString("location_latitude", "");
        String lng = user.optString("location_longitude", "");
        if (isBlank(lat) && isBlank(lng)) return "--";
        return valueOr(lat) + ", " + valueOr(lng);
    }

    private String auditAddressText(JSONObject item) {
        StringBuilder builder = new StringBuilder();
        appendSlashPart(builder, item.optString("country", ""));
        appendSlashPart(builder, item.optString("province", ""));
        appendSlashPart(builder, item.optString("city", ""));
        appendSlashPart(builder, item.optString("district", ""));
        return builder.length() == 0 ? "--" : builder.toString();
    }

    private static void appendSlashPart(StringBuilder builder, String value) {
        if (isBlank(value) || "null".equalsIgnoreCase(value)) return;
        String normalized = value.trim().replace("中国", "中国/").replace("广东", "广东/").replace("深圳", "深圳/");
        String[] parts = normalized.split("[/\\s]+");
        for (String part : parts) {
            if (isBlank(part) || "null".equalsIgnoreCase(part)) continue;
            if (builder.indexOf(part) >= 0) continue;
            if (builder.length() > 0) builder.append("/");
            builder.append(part);
        }
    }

    private static void appendPart(StringBuilder builder, String value) {
        if (isBlank(value) || "null".equalsIgnoreCase(value)) return;
        if (builder.indexOf(value) >= 0) return;
        builder.append(value);
    }

    private static void appendAddressPart(StringBuilder builder, String value) {
        if (isBlank(value) || "null".equalsIgnoreCase(value)) return;
        String text = value.trim();
        if (builder.length() == 0) {
            builder.append(text);
            return;
        }
        String current = builder.toString();
        if (current.contains(text)) return;
        // GPS 解析地址常把“省市区”完整带回；前面已拼过行政区划时只补后续详细地址。
        if (text.startsWith(current)) {
            builder.append(text.substring(current.length()));
            return;
        }
        if (current.startsWith(text)) return;
        builder.append(text);
    }

    private String dateTimeText(String value) {
        if (isBlank(value) || "null".equalsIgnoreCase(value)) return "--";
        String normalized = value.replace('T', ' ');
        return normalized.length() >= 19 ? normalized.substring(0, 19) : normalized;
    }

    private static String valueOr(String value) {
        return isBlank(value) || "null".equalsIgnoreCase(value) ? "--" : value;
    }

    private String adminInitial() {
        String username = admin == null ? "管" : admin.optString("username", "管");
        return isBlank(username) ? "管" : username.substring(0, 1).toUpperCase(Locale.ROOT);
    }

    private static boolean isBlank(String value) {
        return value == null || value.trim().isEmpty();
    }

    private static String maskPhone(String phone) {
        if (phone == null || phone.length() < 7) return phone == null ? "--" : phone;
        return phone.substring(0, 3) + " **** " + phone.substring(phone.length() - 4);
    }

    private static String formatMoney(double value) {
        NumberFormat nf = NumberFormat.getCurrencyInstance(Locale.CHINA);
        nf.setMaximumFractionDigits(value % 1 == 0 ? 0 : 2);
        return nf.format(value);
    }

    private String actionTitle(String action) {
        Map<String, String> map = new HashMap<>();
        map.put("approve", "审批通过"); map.put("reject", "审批拒绝"); map.put("disburse", "确认发卡");
        map.put("reject-card", "拒绝发卡"); map.put("save-note", "保存备注"); map.put("remind", "登记提醒");
        map.put("collect", "登记催收"); map.put("reconcile", "登记平账"); map.put("extend", "账单展期");
        map.put("adjust-credit", "增加可用额度"); map.put("set-credit", "调整授信"); map.put("blacklist", "一键拉黑");
        map.put("remove-blacklist", "移出黑名单"); map.put("unlock-location", "解除位移风控");
        return map.containsKey(action) ? map.get(action) : "业务处理";
    }

    private String defaultHint(String action) {
        if ("approve".equals(action) || "set-credit".equals(action)) return "输入授信额度";
        if ("disburse".equals(action) || "extend".equals(action)) return "输入天数";
        if ("reconcile".equals(action) || "adjust-credit".equals(action)) return "输入金额";
        return "输入处理说明";
    }

    private String defaultValue(String action, JSONObject item) {
        if ("approve".equals(action) || "set-credit".equals(action)) return String.valueOf((int) item.optDouble("approved_credit_limit", 1000));
        if ("disburse".equals(action)) return String.valueOf(item.optInt("term_days", item.optInt("product_term_days", 7)));
        if ("reconcile".equals(action)) return String.valueOf(item.optDouble("remaining_repayment_amount", 0));
        if ("adjust-credit".equals(action)) return "100";
        if ("extend".equals(action)) return "3";
        return "";
    }

    private static double numberOr(String text, double fallback) {
        if (text == null || text.trim().isEmpty()) return fallback;
        try { return Double.parseDouble(text.trim()); } catch (Exception ignored) { return fallback; }
    }

    private static class SimpleTextWatcher implements TextWatcher {
        private final Runnable afterChanged;

        SimpleTextWatcher(Runnable afterChanged) {
            this.afterChanged = afterChanged;
        }

        @Override
        public void beforeTextChanged(CharSequence s, int start, int count, int after) {}

        @Override
        public void onTextChanged(CharSequence s, int start, int before, int count) {}

        @Override
        public void afterTextChanged(Editable s) {
            if (afterChanged != null) afterChanged.run();
        }
    }

    private EditText input(String hint) {
        EditText input = new EditText(this);
        input.setHint(hint);
        input.setTextSize(16);
        input.setTextColor(Ui.TEXT);
        input.setHintTextColor(Color.argb(150, 100, 116, 139));
        input.setSingleLine(false);
        input.setBackgroundResource(getResources().getIdentifier("input_bg", "drawable", getPackageName()));
        input.setGravity(Gravity.CENTER_VERTICAL);
        input.setPadding(dp(14), dp(6), dp(14), dp(6));
        return input;
    }

    private Button primaryButton(String text) {
        Button button = new Button(this);
        button.setText(text);
        button.setTextColor(0xffffffff);
        button.setTextSize(16);
        button.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        button.setAllCaps(false);
        button.setBackgroundResource(getResources().getIdentifier("primary_button", "drawable", getPackageName()));
        button.setElevation(dp(2));
        return button;
    }

    private Button actionButton(String text) {
        Button button = new Button(this);
        button.setText(text);
        button.setTextColor(Ui.BLUE);
        button.setTextSize(14);
        button.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        button.setAllCaps(false);
        button.setBackground(roundRect(Color.WHITE, dp(16), Ui.BORDER));
        return button;
    }

    private Button dangerButton(String text) {
        Button button = new Button(this);
        button.setText(text);
        button.setTextColor(Ui.RED);
        button.setTextSize(14);
        button.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        button.setAllCaps(false);
        button.setBackground(roundRect(Color.WHITE, dp(16), Ui.BORDER));
        return button;
    }

    private Button circleButton(String text) {
        Button button = new Button(this);
        button.setText(text);
        button.setTextColor(Ui.SLATE);
        button.setTextSize(16);
        button.setAllCaps(false);
        button.setBackground(roundRect(Color.WHITE, dp(22), Ui.BORDER));
        button.setElevation(dp(2));
        return button;
    }

    private Button avatarButton(String text) {
        Button button = circleButton(text);
        button.setTextColor(Ui.BLUE);
        button.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        return button;
    }

    private Button segment(String text, boolean active) {
        Button button = new Button(this);
        button.setText(text);
        button.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        button.setAllCaps(false);
        setSegmentActive(button, active);
        return button;
    }

    private void setSegmentActive(Button button, boolean active) {
        button.setTextColor(active ? Ui.BLUE : Ui.SLATE);
        button.setBackground(active ? roundRect(Color.rgb(232, 240, 254), dp(18), Ui.BORDER) : roundRect(Color.WHITE, dp(18), Ui.BORDER));
    }

    private LinearLayout row() {
        LinearLayout row = new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        row.setGravity(Gravity.CENTER_VERTICAL);
        return row;
    }

    private TextView text(String value, int sp, int color, int style) {
        TextView view = new TextView(this);
        view.setText(value);
        view.setTextSize(sp);
        view.setTextColor(color);
        view.setTypeface(null, style);
        return view;
    }

    private TextView pill(String value, int bg, int fg) {
        TextView view = text(value, 12, fg, Typeface.BOLD);
        view.setGravity(Gravity.CENTER);
        view.setPadding(dp(10), dp(4), dp(10), dp(4));
        view.setBackground(roundRect(bg, dp(999), 0));
        return view;
    }

    private GradientDrawable cardDrawable() {
        return gcpCardDrawable();
    }

    private GradientDrawable stripeBackground() {
        return roundRect(Color.rgb(246, 248, 252), 0, 0);
    }

    private GradientDrawable glassCardDrawable() {
        return gcpCardDrawable();
    }

    private GradientDrawable softPanelDrawable() {
        return gcpCardDrawable();
    }

    private GradientDrawable tintGlassDrawable(int color) {
        return roundRect(color, dp(16), Ui.BORDER);
    }

    private GradientDrawable gcpCardDrawable() {
        return roundRect(Color.WHITE, dp(18), Ui.BORDER);
    }

    private GradientDrawable glassDrawable(int color, int radius, int strokeColor) {
        GradientDrawable drawable = roundRect(color, radius, strokeColor);
        drawable.setDither(true);
        return drawable;
    }

    private GradientDrawable gradientRect(int[] colors, int radius, GradientDrawable.Orientation orientation) {
        GradientDrawable drawable = new GradientDrawable(orientation, colors);
        drawable.setCornerRadius(radius);
        drawable.setDither(true);
        return drawable;
    }

    private GradientDrawable roundRect(int color, int radius, int strokeColor) {
        GradientDrawable drawable = new GradientDrawable();
        drawable.setColor(color);
        drawable.setCornerRadius(radius);
        if (strokeColor != 0) drawable.setStroke(dp(1), strokeColor);
        return drawable;
    }

    private View space(int size) {
        View view = new View(this);
        view.setLayoutParams(new LinearLayout.LayoutParams(dp(size), dp(size)));
        return view;
    }

    private LinearLayout.LayoutParams matchWrap() { return new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT); }
    private LinearLayout.LayoutParams matchHeight(int h) { return new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, dp(h)); }
    private LinearLayout.LayoutParams square(int size) { return new LinearLayout.LayoutParams(dp(size), dp(size)); }
    private int dp(int value) { return Math.round(value * getResources().getDisplayMetrics().density); }
    private void toast(String message) { Toast.makeText(this, message, Toast.LENGTH_SHORT).show(); }
}
