package com.galacredit.app;

import android.content.Context;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;

final class Ui {
    static final int BLUE = Color.rgb(26, 115, 232);
    static final int BLUE_LIGHT = Color.rgb(232, 240, 254);
    static final int TEXT = Color.rgb(32, 33, 36);
    static final int MUTED = Color.rgb(95, 99, 104);
    static final int BORDER = Color.rgb(218, 220, 224);
    static final int BACKGROUND = Color.rgb(248, 250, 255);
    static final int CARD = Color.WHITE;
    static final int DANGER = Color.rgb(217, 48, 37);
    static final int SUCCESS = Color.rgb(52, 168, 83);

    private Ui() {
    }

    static int dp(Context context, int value) {
        return Math.round(TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP, value, context.getResources().getDisplayMetrics()));
    }

    static GradientDrawable rounded(int fillColor, int radiusDp, int strokeColor, Context context) {
        GradientDrawable drawable = new GradientDrawable();
        drawable.setColor(fillColor);
        drawable.setCornerRadius(dp(context, radiusDp));
        drawable.setStroke(dp(context, 1), strokeColor);
        return drawable;
    }

    static TextView text(Context context, String value, int sizeSp, int color, boolean bold) {
        TextView view = new TextView(context);
        view.setText(value);
        view.setTextSize(TypedValue.COMPLEX_UNIT_SP, sizeSp);
        view.setTextColor(color);
        view.setTypeface(Typeface.DEFAULT, bold ? Typeface.BOLD : Typeface.NORMAL);
        view.setGravity(Gravity.START);
        return view;
    }

    static Button primaryButton(Context context, String value) {
        Button button = new Button(context);
        button.setAllCaps(false);
        button.setText(value);
        button.setTextColor(Color.WHITE);
        button.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        button.setBackground(rounded(BLUE, 18, BLUE, context));
        button.setPadding(dp(context, 12), 0, dp(context, 12), 0);
        button.setMinHeight(0);
        button.setMinWidth(0);
        button.setGravity(Gravity.CENTER);
        button.setIncludeFontPadding(false);
        return button;
    }

    static Button secondaryButton(Context context, String value) {
        Button button = new Button(context);
        button.setAllCaps(false);
        button.setText(value);
        button.setTextColor(BLUE);
        button.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        button.setBackground(rounded(Color.WHITE, 18, BLUE_LIGHT, context));
        button.setPadding(dp(context, 10), 0, dp(context, 10), 0);
        button.setTextSize(TypedValue.COMPLEX_UNIT_SP, 15);
        button.setMinHeight(0);
        button.setMinWidth(0);
        button.setGravity(Gravity.CENTER);
        button.setIncludeFontPadding(false);
        return button;
    }

    static EditText input(Context context, String hint) {
        EditText editText = new EditText(context);
        editText.setHint(hint);
        editText.setTextColor(TEXT);
        editText.setHintTextColor(MUTED);
        editText.setTextSize(TypedValue.COMPLEX_UNIT_SP, 16);
        editText.setBackgroundColor(Color.TRANSPARENT);
        editText.setPadding(0, 0, 0, 0);
        editText.setMinHeight(0);
        editText.setMinWidth(0);
        editText.setIncludeFontPadding(false);
        editText.setSingleLine(true);
        return editText;
    }

    static View spacer(Context context, int heightDp) {
        View view = new View(context);
        view.setLayoutParams(new android.widget.LinearLayout.LayoutParams(-1, dp(context, heightDp)));
        return view;
    }
}
