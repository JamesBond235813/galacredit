package com.juxin.xiaohebao.admin;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.DatePickerDialog;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.text.Editable;
import android.text.InputType;
import android.text.TextWatcher;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.drawable.GradientDrawable;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import org.json.JSONArray;
import org.json.JSONObject;

import java.text.NumberFormat;
import java.io.InputStream;
import java.net.URL;
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
    private final ExecutorService worker = Executors.newSingleThreadExecutor();
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
    private String repaymentOverdueFilter = "ALL";
    private String financeOverdueFilter = "ALL";
    private String repaymentStartDate = "";
    private String repaymentEndDate = "";
    private boolean detailOpen = false;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        api = new ApiClient(this);
        if (api.token().isEmpty()) {
            showLogin();
        } else {
            loadMe();
        }
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

        TextView subtitle = text("Stripe 风格 · 玻璃拟态 · 移动审批", 13, Ui.MUTED, Typeface.BOLD);
        subtitle.setGravity(Gravity.CENTER);
        subtitle.setPadding(0, 0, 0, dp(28));
        root.addView(subtitle, matchWrap());

        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(dp(20), dp(20), dp(20), dp(20));
        card.setBackground(glassCardDrawable());
        card.setElevation(dp(10));
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

        LinearLayout header = new LinearLayout(this);
        header.setOrientation(LinearLayout.HORIZONTAL);
        header.setGravity(Gravity.CENTER_VERTICAL);
        header.setPadding(dp(18), dp(18), dp(18), dp(12));
        page.addView(header, matchWrap());

        LinearLayout titleBox = new LinearLayout(this);
        titleBox.setOrientation(LinearLayout.VERTICAL);
        TextView brand = text("小荷包", 13, Ui.MUTED, 1);
        TextView title = text(tabTitle(activeTab), 28, Ui.TEXT, 1);
        titleBox.addView(brand);
        titleBox.addView(title);
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
        fixed.setBackground(softPanelDrawable());
        page.addView(fixed, matchWrap());
        addSummaryStrip(fixed);
        addSearchControls(fixed);

        ScrollView scroll = new ScrollView(this);
        LinearLayout list = new LinearLayout(this);
        list.setOrientation(LinearLayout.VERTICAL);
        list.setPadding(dp(16), dp(6), dp(16), dp(12));
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
        row.addView(left, new LinearLayout.LayoutParams(0, dp(76), 1));
        row.addView(space(10));
        row.addView(right, new LinearLayout.LayoutParams(0, dp(76), 1));
        content.addView(row);
        content.addView(space(12));

        TextView leftValue = (TextView) left.getChildAt(1);
        TextView rightValue = (TextView) right.getChildAt(1);
        boolean needsRepaymentStats = "repayments".equals(activeTab) || "finance".equals(activeTab);
        if (statsCache != null && (!needsRepaymentStats || repaymentStatsCache != null)) {
            updateSummaryValues(leftValue, rightValue, statsCache, repaymentStatsCache == null ? new JSONObject() : repaymentStatsCache);
            return;
        }
        worker.execute(() -> {
            try {
                JSONObject stats = api.get("/admin/stats", null);
                JSONObject repayment = ("repayments".equals(activeTab) || "finance".equals(activeTab)) ? api.get("/admin/repayment-stats", null) : new JSONObject();
                statsCache = stats;
                repaymentStatsCache = repayment;
                main.post(() -> updateSummaryValues(leftValue, rightValue, stats, repayment));
            } catch (Exception ignored) {
                main.post(() -> { leftValue.setText("--"); rightValue.setText("--"); });
            }
        });
    }

    private LinearLayout metricCard(String label, String value, String tip) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(dp(12), dp(10), dp(12), dp(10));
        card.setBackground(tintGlassDrawable(Color.argb(168, 255, 255, 255)));
        card.setElevation(dp(8));
        TextView labelView = text(label, 12, Ui.MUTED, Typeface.NORMAL);
        TextView valueView = text(value, 23, Ui.TEXT, Typeface.BOLD);
        valueView.setPadding(0, dp(6), 0, 0);
        card.addView(labelView);
        card.addView(valueView);
        return card;
    }

    private String[] summaryLabels() {
        if ("applications".equals(activeTab)) return new String[]{"待审批", "今日申请", "需要核验资料", "当天提交"};
        if ("cards".equals(activeTab)) return new String[]{"待发卡", "今日发卡额", "等待卡池匹配", "已发放面值"};
        if ("repayments".equals(activeTab)) return new String[]{"今日到期", "逾期订单", "当日应跟进", "催收优先处理"};
        if ("finance".equals(activeTab)) return new String[]{"列表订单", "已收金额", "可财务处理", "财务累计确认"};
        return new String[]{"总档案", "今日新增", "全部注册客户", "今天进入系统"};
    }

    private void updateSummaryValues(TextView left, TextView right, JSONObject stats, JSONObject repayment) {
        if ("applications".equals(activeTab)) {
            left.setText(String.valueOf(stats.optInt("reviewing_loans", 0)));
            right.setText(String.valueOf(stats.optInt("today_applications", 0)));
        } else if ("cards".equals(activeTab)) {
            left.setText(String.valueOf(stats.optInt("withdrawing_loans", 0)));
            right.setText(formatMoney(stats.optDouble("today_disbursed_amount", 0)));
        } else if ("repayments".equals(activeTab)) {
            left.setText(String.valueOf(stats.optInt("due_today_loans", 0)));
            right.setText(String.valueOf(stats.optInt("overdue_loans", 0)));
        } else if ("finance".equals(activeTab)) {
            left.setText("--");
            right.setText(formatMoney(repayment.optDouble("received_amount", 0)));
        } else {
            left.setText(String.valueOf(stats.optInt("total_users", 0)));
            right.setText(String.valueOf(stats.optInt("today_new_users", 0)));
        }
    }

    private void addSearchControls(LinearLayout content) {
        if ("profiles".equals(activeTab)) {
            addKeywordSearch(content, "搜索手机号 / 姓名 / 身份证");
        } else if ("applications".equals(activeTab)) {
            addStatusFilter(content, new String[][]{{"ALL", "全部"}, {"REVIEWING", "审核中"}, {"APPROVED", "已通过"}, {"REJECTED", "未通过"}}, applicationStatusFilter, value -> {
                applicationStatusFilter = value;
                showWorkspace();
            });
        } else if ("repayments".equals(activeTab)) {
            addDateRangeSearch(content);
            addOverdueFilter(content, repaymentOverdueFilter, value -> {
                repaymentOverdueFilter = value;
                segmentScope = "OVERDUE".equals(value) ? "OVERDUE" : "REPAYMENTS";
                showWorkspace();
            });
        } else if ("finance".equals(activeTab)) {
            addKeywordSearch(content, "搜索手机号 / 姓名 / 身份证");
            addOverdueFilter(content, financeOverdueFilter, value -> {
                financeOverdueFilter = value;
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
        EditText start = input("开始日期 yyyy-MM-dd");
        EditText end = input("结束日期 yyyy-MM-dd");
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
            if ("applications".equals(activeTab) && !"ALL".equals(applicationStatusFilter)) q.put("status", applicationStatusFilter);
            applyOverdueQuery(q);
            if (!keyword.isEmpty()) q.put("phone", keyword);
            JSONObject result = api.get("/admin/loans", q);
            if ("applications".equals(activeTab)) enrichApplicationItems(result);
            return "repayments".equals(activeTab) ? filterByRepaymentDate(result) : result;
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
        return activeTab + "|" + keyword + "|" + applicationStatusFilter + "|" + repaymentOverdueFilter + "|" + financeOverdueFilter + "|" + repaymentStartDate + "|" + repaymentEndDate;
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
        card.setPadding(dp(16), dp(14), dp(16), dp(14));
        card.setBackground(glassCardDrawable());
        card.setElevation(dp(7));
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
        card.addView(space(6));
        card.addView(hint);
        card.setOnClickListener(v -> openDetail(item));
    }

    private void addApplicationCard(LinearLayout content, JSONObject item) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(dp(16), dp(14), dp(16), dp(14));
        card.setBackground(glassCardDrawable());
        card.setElevation(dp(7));
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
                detail.put("_ip_audit", ipAudit);
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
        titleBox.addView(text(subtitle(item), 13, Ui.MUTED, Typeface.NORMAL));
        header.addView(back, square(44));
        header.addView(titleBox, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        page.addView(header, matchWrap());
        back.setOnClickListener(v -> showWorkspace());

        ScrollView scroll = new ScrollView(this);
        LinearLayout content = new LinearLayout(this);
        content.setOrientation(LinearLayout.VERTICAL);
        content.setPadding(dp(16), 0, dp(16), dp(16));
        scroll.addView(content);
        page.addView(scroll, new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, 0, 1));

        addPhotosSection(content, user);
        addInfoSection(content, "核心信息", coreRows(item));
        addInfoSection(content, "紧急联系人", emergencyRows(user));
        addInfoSection(content, "地理位置", locationRows(user));
        addInfoSection(content, "IP记录", ipRows(user));
        addInfoSection(content, "订单状态及审核批注", orderAuditRows(item));
        addActionDock(page, item);
    }

    private void addInfoSection(LinearLayout content, String title, String[][] rows) {
        TextView heading = text(title, 15, Ui.TEXT, Typeface.BOLD);
        heading.setPadding(0, dp(12), 0, dp(8));
        content.addView(heading);
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(dp(16), dp(12), dp(16), dp(12));
        box.setBackground(glassCardDrawable());
        box.setElevation(dp(7));
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
        row.addView(photoBox(photos, 0), new LinearLayout.LayoutParams(0, dp(88), 1));
        row.addView(space(8));
        row.addView(photoBox(photos, 1), new LinearLayout.LayoutParams(0, dp(88), 1));
        row.addView(space(8));
        row.addView(photoBox(photos, 2), new LinearLayout.LayoutParams(0, dp(88), 1));
        content.addView(row);
    }

    private LinearLayout photoBox(String[][] photos, int index) {
        String label = photos[index][0];
        String url = photos[index][1];
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setGravity(Gravity.CENTER);
        box.setPadding(dp(6), dp(6), dp(6), dp(6));
        box.setBackground(tintGlassDrawable(Color.argb(188, 248, 250, 255)));
        box.setElevation(dp(4));
        View media;
        if (isBlank(url) || "null".equalsIgnoreCase(url)) {
            TextView empty = text("暂无", 13, Ui.MUTED, Typeface.NORMAL);
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
        TextView caption = text(label, 11, Ui.MUTED, Typeface.NORMAL);
        caption.setGravity(Gravity.CENTER);
        box.addView(media, new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, 0, 1));
        box.addView(caption, matchWrap());
        return box;
    }

    private void showPhotoPreview(String[][] photos, int startIndex) {
        final int[] index = new int[]{startIndex};
        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setPadding(dp(12), dp(12), dp(12), dp(8));
        TextView title = text(photos[index[0]][0], 16, Ui.TEXT, Typeface.BOLD);
        title.setGravity(Gravity.CENTER);
        ImageView image = new ImageView(this);
        image.setScaleType(ImageView.ScaleType.FIT_CENTER);
        image.setBackgroundColor(Color.rgb(248, 251, 255));
        panel.addView(title, matchWrap());
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
        AlertDialog dialog = new AlertDialog.Builder(this).setView(panel).create();
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
        dialog.setOnShowListener(d -> render.run());
        dialog.show();
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
        dock.setPadding(dp(16), dp(12), dp(16), dp(12));
        dock.setBackground(softPanelDrawable());
        dock.setElevation(dp(10));
        TextView title = text("可执行操作", 14, Ui.TEXT, Typeface.BOLD);
        dock.addView(title);
        LinearLayout row = null;
        int index = 0;
        for (String[] action : actionsForCurrentTab(item)) {
            if (index % 2 == 0) {
                row = row();
                row.setPadding(0, dp(8), 0, 0);
                dock.addView(row);
            }
            Button button = "blacklist".equals(action[0]) || "reject".equals(action[0]) || "reject-card".equals(action[0]) ? dangerButton(action[1]) : actionButton(action[1]);
            row.addView(button, new LinearLayout.LayoutParams(0, dp(44), 1));
            if (index % 2 == 0) row.addView(space(8));
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
        new AlertDialog.Builder(this)
            .setTitle(displayName(item))
            .setItems(labels.toArray(new String[0]), (dialog, which) -> prepareAction(keys.get(which), item))
            .setNegativeButton("取消", null)
            .show();
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
        if ("ack".equals(action) || "settle".equals(action) || "refresh".equals(action) || "reissue-card".equals(action) || "close-reissue".equals(action)) {
            confirmAction(action, item, new JSONObject());
            return;
        }
        EditText input = input(defaultHint(action));
        input.setMinLines("reconcile".equals(action) || "approve".equals(action) || "extend".equals(action) ? 3 : 1);
        input.setText(defaultValue(action, item));
        new AlertDialog.Builder(this)
            .setTitle(actionTitle(action))
            .setView(input)
            .setPositiveButton("提交", (d, w) -> {
                JSONObject body = new JSONObject();
                try {
                    fillPayload(action, input.getText().toString().trim(), item, body);
                    confirmAction(action, item, body);
                } catch (Exception e) {
                    toast(e.getMessage());
                }
            })
            .setNegativeButton("取消", null)
            .show();
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
        AlertDialog dialog = new AlertDialog.Builder(this).setTitle("审批通过").setView(panel).create();
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

    private void showReconcileDialog(JSONObject item) {
        LinearLayout panel = dialogPanel();
        EditText received = input("登记收款");
        EditText reduction = input("减免金额");
        EditText otherFee = input("其他费用");
        EditText note = input("平账说明");
        received.setInputType(InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_FLAG_DECIMAL);
        reduction.setInputType(InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_FLAG_DECIMAL);
        otherFee.setInputType(InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_FLAG_DECIMAL);
        note.setMinLines(3);
        received.setText(String.valueOf(item.optDouble("remaining_repayment_amount", 0)));
        reduction.setText(String.valueOf(item.optDouble("reduction_amount", 0)));
        otherFee.setText("0");
        note.setText("安卓端登记平账");
        panel.addView(fieldBox("登记收款", received));
        panel.addView(fieldBox("减免金额", reduction));
        panel.addView(fieldBox("其他费用", otherFee));
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

        AlertDialog dialog = new AlertDialog.Builder(this).setTitle("登记平账").setView(panel).create();
        panel.addView(dialogButtons("关闭", "提交", dialog, () -> {
            JSONObject body = new JSONObject();
            body.put("received_amount", numberOr(received.getText().toString(), 0));
            body.put("reduction_amount", numberOr(reduction.getText().toString(), 0));
            body.put("other_fee_amount", numberOr(otherFee.getText().toString(), 0));
            body.put("note", note.getText().toString().trim().isEmpty() ? "安卓端登记平账" : note.getText().toString().trim());
            confirmAction("reconcile", item, body);
        }));
        dialog.setOnShowListener(d -> render.run());
        dialog.show();
    }

    private void showNoteSubmitDialog(String title, String label, String initialValue, DialogSubmit submit) {
        LinearLayout panel = dialogPanel();
        EditText note = input(label);
        note.setMinLines(3);
        note.setText(initialValue);
        panel.addView(fieldBox(label, note));
        AlertDialog dialog = new AlertDialog.Builder(this).setTitle(title).setView(panel).create();
        panel.addView(dialogButtons("关闭", "提交", dialog, () -> {
            JSONObject body = new JSONObject();
            body.put("review_note", note.getText().toString().trim());
            submit.apply(body);
        }));
        dialog.show();
    }

    private LinearLayout dialogPanel() {
        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setPadding(dp(16), dp(8), dp(16), dp(4));
        return panel;
    }

    private LinearLayout fieldBox(String label, EditText input) {
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.addView(text(label, 13, Ui.MUTED, Typeface.BOLD));
        box.addView(space(6));
        box.addView(input, matchHeight(input.getMinLines() > 1 ? 96 : 44));
        box.addView(space(12));
        return box;
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
        if ("profiles".equals(activeTab)) {
            actions.add(new String[]{"refresh", "刷新档案"});
            if (item.optBoolean("location_risk_blocked") && item.optBoolean("can_unlock_location_risk")) actions.add(new String[]{"unlock-location", "解除位置风控"});
            actions.add(new String[]{item.optBoolean("blacklist_hit") ? "remove-blacklist" : "blacklist", item.optBoolean("blacklist_hit") ? "移出黑名单" : "一键拉黑"});
            if (item.optInt("current_loan_id", 0) > 0) actions.add(new String[]{"reissue-card", "开启二次发卡"});
            if (item.optInt("current_loan_id", 0) > 0) actions.add(new String[]{"close-reissue", "退回待下单"});
        } else if ("applications".equals(activeTab)) {
            actions.add(new String[]{"approve", "审批通过"});
            actions.add(new String[]{"reject", "审批拒绝"});
            actions.add(new String[]{"set-credit", "调整授信"});
            actions.add(new String[]{"adjust-credit", "增加可用额度"});
            actions.add(new String[]{"save-note", "审批备注"});
            actions.add(new String[]{"blacklist", "一键拉黑"});
        } else if ("cards".equals(activeTab)) {
            actions.add(new String[]{"disburse", "确认发卡"});
            actions.add(new String[]{"reject-card", "拒绝发卡"});
            actions.add(new String[]{"close-reissue", "退回待下单"});
            actions.add(new String[]{"save-note", "保存备注"});
            actions.add(new String[]{"blacklist", "一键拉黑"});
        } else if ("repayments".equals(activeTab)) {
            actions.add(new String[]{"OVERDUE".equals(segmentScope) ? "collect" : "remind", "OVERDUE".equals(segmentScope) ? "登记催收" : "登记提醒"});
            actions.add(new String[]{"ack", "确认还款申请"});
            actions.add(new String[]{"extend", "账单展期"});
            actions.add(new String[]{"adjust-credit", "增加可用额度"});
            actions.add(new String[]{"blacklist", "一键拉黑"});
        } else {
            actions.add(new String[]{"reconcile", "登记平账"});
            actions.add(new String[]{"settle", "确认结清"});
            actions.add(new String[]{"extend", "账单展期"});
        }
        return actions;
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
        tabs.setPadding(dp(10), dp(8), dp(10), dp(8));
        tabs.setBackground(softPanelDrawable());
        tabs.setElevation(dp(12));
        page.addView(tabs, matchWrap());
        for (String[] tab : visibleTabs()) {
            boolean active = tab[0].equals(activeTab);
            TextView button = text(tabIcon(tab[0]) + "\n" + tab[1], 12, active ? 0xffffffff : Ui.MUTED, active ? Typeface.BOLD : Typeface.NORMAL);
            button.setGravity(Gravity.CENTER);
            button.setClickable(true);
            button.setBackground(active ? gradientRect(new int[]{Ui.BLUE, Ui.INDIGO}, dp(18), GradientDrawable.Orientation.LEFT_RIGHT) : roundRect(0x00000000, dp(18), 0));
            tabs.addView(button, new LinearLayout.LayoutParams(0, dp(56), 1));
            button.setOnClickListener(v -> { activeTab = tab[0]; keyword = ""; showWorkspace(); });
        }
    }

    private List<String[]> visibleTabs() {
        List<String[]> tabs = new ArrayList<>();
        if (hasAny("ADMIN", "REVIEW", "BUSINESS_CONSULTANT")) tabs.add(new String[]{"profiles", "档案"});
        if (hasAny("ADMIN", "REVIEW")) tabs.add(new String[]{"applications", "申请"});
        if (hasAny("ADMIN", "FINANCE")) tabs.add(new String[]{"cards", "发卡"});
        if (hasAny("ADMIN", "REVIEW", "COLLECTION")) tabs.add(new String[]{"repayments", "回款"});
        if (hasAny("ADMIN", "FINANCE")) tabs.add(new String[]{"finance", "平账"});
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

    private JSONObject filterByRepaymentDate(JSONObject result) throws Exception {
        if (isBlank(repaymentStartDate) && isBlank(repaymentEndDate)) return result;
        JSONArray items = result.optJSONArray("items");
        if (items == null) return result;
        JSONArray filtered = new JSONArray();
        for (int i = 0; i < items.length(); i++) {
            JSONObject item = items.optJSONObject(i);
            if (item != null && inRepaymentDateRange(item)) filtered.put(item);
        }
        result.put("items", filtered);
        result.put("total", filtered.length());
        return result;
    }

    private boolean inRepaymentDateRange(JSONObject item) {
        String value = item.optString("due_date", "");
        if (value.length() < 10) return false;
        String day = value.substring(0, 10);
        if (!isBlank(repaymentStartDate) && day.compareTo(repaymentStartDate) < 0) return false;
        if (!isBlank(repaymentEndDate) && day.compareTo(repaymentEndDate) > 0) return false;
        return true;
    }

    private String scopeForTab(String tab) {
        if ("applications".equals(tab)) return "REVIEWING";
        if ("cards".equals(tab)) return "WITHDRAWING";
        if ("repayments".equals(tab)) return segmentScope;
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

    private String subtitle(JSONObject item) {
        String phone = "profiles".equals(activeTab) ? item.optString("phone", "") : item.optString("user_phone", "");
        String channel = item.optString("source_channel_name", item.optString("user_source_channel_name", "自然流量"));
        return displayPhoneByTab(phone) + " · " + (channel.isEmpty() ? "自然流量" : channel);
    }

    private String rawUserPhone(JSONObject item) {
        String phone = "profiles".equals(activeTab) ? item.optString("phone", "") : item.optString("user_phone", "");
        return valueOr(phone);
    }

    private String displayPhoneByTab(String phone) {
        return "profiles".equals(activeTab) ? maskPhone(phone) : valueOr(phone);
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
            appendPart(builder, event.optString("lon_lat_province", ""));
            appendPart(builder, event.optString("lon_lat_city", ""));
            appendPart(builder, event.optString("lon_lat_district", ""));
            appendPart(builder, event.optString("lon_lat_detail", ""));
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
        return note.isEmpty() ? "点击查看处理动作" : note;
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
                {"手机号", maskPhone(user.optString("phone", ""))},
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
            {"提交时间", dateText(item)},
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
        return valueOr(name) + " / " + valueOr(relation) + " / " + maskPhone(phone);
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
        appendPart(builder, user.optString("location_province", ""));
        appendPart(builder, user.optString("location_city", ""));
        appendPart(builder, user.optString("location_district", ""));
        appendPart(builder, user.optString("location_street", ""));
        appendPart(builder, user.optString("location_address", ""));
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
        appendPart(builder, item.optString("country", ""));
        appendPart(builder, item.optString("province", ""));
        appendPart(builder, item.optString("city", ""));
        appendPart(builder, item.optString("district", ""));
        appendPart(builder, item.optString("address", ""));
        return builder.length() == 0 ? "--" : builder.toString();
    }

    private static void appendPart(StringBuilder builder, String value) {
        if (isBlank(value) || "null".equalsIgnoreCase(value)) return;
        if (builder.indexOf(value) >= 0) return;
        builder.append(value);
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
        map.put("remove-blacklist", "移出黑名单"); map.put("unlock-location", "解除位置风控");
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
        input.setPadding(dp(14), 0, dp(14), 0);
        return input;
    }

    private Button primaryButton(String text) {
        Button button = new Button(this);
        button.setText(text);
        button.setTextColor(0xffffffff);
        button.setTextSize(16);
        button.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        button.setBackgroundResource(getResources().getIdentifier("primary_button", "drawable", getPackageName()));
        button.setElevation(dp(6));
        return button;
    }

    private Button actionButton(String text) {
        Button button = new Button(this);
        button.setText(text);
        button.setTextColor(Ui.BLUE);
        button.setTextSize(14);
        button.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        button.setBackground(tintGlassDrawable(Color.argb(205, 238, 242, 255)));
        return button;
    }

    private Button dangerButton(String text) {
        Button button = new Button(this);
        button.setText(text);
        button.setTextColor(Ui.RED);
        button.setTextSize(14);
        button.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        button.setBackground(tintGlassDrawable(Color.argb(220, 255, 236, 239)));
        return button;
    }

    private Button circleButton(String text) {
        Button button = new Button(this);
        button.setText(text);
        button.setTextColor(Ui.BLUE);
        button.setTextSize(16);
        button.setBackground(tintGlassDrawable(Color.argb(226, 255, 255, 255)));
        button.setElevation(dp(7));
        return button;
    }

    private Button avatarButton(String text) {
        Button button = circleButton(text);
        button.setTextColor(0xffffffff);
        button.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        button.setBackground(gradientRect(new int[]{Ui.BLUE, Ui.INDIGO}, dp(999), GradientDrawable.Orientation.LEFT_RIGHT));
        return button;
    }

    private Button segment(String text, boolean active) {
        Button button = new Button(this);
        button.setText(text);
        button.setTextColor(active ? 0xffffffff : Ui.BLUE);
        button.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        button.setBackground(active ? gradientRect(new int[]{Ui.BLUE, Ui.INDIGO}, dp(15), GradientDrawable.Orientation.LEFT_RIGHT) : tintGlassDrawable(Color.argb(188, 255, 255, 255)));
        return button;
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
        return glassCardDrawable();
    }

    private GradientDrawable stripeBackground() {
        return gradientRect(
            new int[]{Color.rgb(247, 250, 255), Color.rgb(235, 244, 255), Color.rgb(246, 237, 255)},
            0,
            GradientDrawable.Orientation.TL_BR
        );
    }

    private GradientDrawable glassCardDrawable() {
        return glassDrawable(Ui.GLASS, dp(22), Color.argb(112, 255, 255, 255));
    }

    private GradientDrawable softPanelDrawable() {
        return glassDrawable(Ui.GLASS_SOFT, dp(24), Color.argb(80, 255, 255, 255));
    }

    private GradientDrawable tintGlassDrawable(int color) {
        return glassDrawable(color, dp(18), Color.argb(90, 255, 255, 255));
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
