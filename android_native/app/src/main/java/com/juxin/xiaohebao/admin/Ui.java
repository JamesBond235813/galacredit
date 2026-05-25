package com.juxin.xiaohebao.admin;

import android.graphics.Color;
import android.graphics.Typeface;
import android.view.Gravity;
import android.view.View;
import android.widget.TextView;

final class Ui {
    static final int BLUE = Color.rgb(26, 115, 232);
    static final int TEXT = Color.rgb(32, 33, 36);
    static final int MUTED = Color.rgb(95, 99, 104);
    static final int BORDER = Color.rgb(218, 220, 224);
    static final int RED = Color.rgb(197, 34, 31);
    static final int ORANGE = Color.rgb(245, 167, 61);

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
