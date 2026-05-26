package com.juxin.xiaohebao.admin;

import android.graphics.Color;
import android.graphics.Typeface;
import android.view.Gravity;
import android.view.View;
import android.widget.TextView;

final class Ui {
    static final int BLUE = Color.rgb(99, 91, 255);
    static final int INDIGO = Color.rgb(67, 56, 202);
    static final int CYAN = Color.rgb(0, 212, 255);
    static final int MINT = Color.rgb(0, 214, 143);
    static final int TEXT = Color.rgb(18, 24, 38);
    static final int MUTED = Color.rgb(100, 116, 139);
    static final int BORDER = Color.argb(90, 148, 163, 184);
    static final int GLASS = Color.argb(226, 255, 255, 255);
    static final int GLASS_SOFT = Color.argb(178, 255, 255, 255);
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
