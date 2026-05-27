package com.juxin.xiaohebao.admin;

import android.graphics.Color;
import android.graphics.Typeface;
import android.view.Gravity;
import android.view.View;
import android.widget.TextView;

final class Ui {
    static final int BLUE = Color.rgb(26, 115, 232);
    static final int INDIGO = Color.rgb(66, 133, 244);
    static final int VIOLET = Color.rgb(103, 58, 183);
    static final int SKY = Color.rgb(66, 133, 244);
    static final int CYAN = Color.rgb(66, 133, 244);
    static final int MINT = Color.rgb(52, 168, 83);
    static final int TEXT = Color.rgb(32, 33, 36);
    static final int MUTED = Color.rgb(95, 99, 104);
    static final int SLATE = Color.rgb(60, 64, 67);
    static final int BORDER = Color.rgb(218, 220, 224);
    static final int GLASS = Color.rgb(255, 255, 255);
    static final int GLASS_SOFT = Color.rgb(255, 255, 255);
    static final int GLASS_TINT = Color.rgb(255, 255, 255);
    static final int RED = Color.rgb(220, 38, 38);
    static final int ORANGE = Color.rgb(245, 158, 11);

    private Ui() {}

    static int dp(View view, int value) {
        return Math.round(value * view.getResources().getDisplayMetrics().density);
    }

    static TextView text(View parent, String value, int sp, int color, int style) {
        TextView view = new TextView(parent.getContext());
        view.setText(value);
        view.setTextSize(sp);
        view.setTextColor(color);
        view.setTypeface(Typeface.DEFAULT, style);
        view.setGravity(Gravity.START);
        return view;
    }
}
