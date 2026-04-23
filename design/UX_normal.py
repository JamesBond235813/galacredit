# -*- coding: utf-8 -*-
# File: generate_dataplayer_brand_manual.py
# Purpose: Generate "DataPlayer Brand Visual Identity Guide" (A4 PDF)

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
import os

# --- Page size ---
A4_W, A4_H = A4

# --- Brand metadata ---

BRAND_CN = "小荷包"
SLOGAN_CN = "解生活之所急"

# --- Color system (confirmed) ---
DATA_BLUE = colors.HexColor("#1E90FF")   # Primary blue
FLOW_GREEN = colors.HexColor("#30D7A9")  # Flow green
NEUTRAL_GRAY = colors.HexColor("#3C3C3C")
BG_LIGHT = colors.HexColor("#F5F8FA")
TEXT_DIM = colors.HexColor("#4B5563")
TEXT_DIM2 = colors.HexColor("#6B7280")
INK_DARK = colors.HexColor("#0F172A")

# --- Fonts ---
def register_fonts():
    """Register primary font with simplified Chinese support."""

    here = os.path.dirname(os.path.abspath(__file__))
    candidate_names = [
        "NotoSansSC-Regular.otf",
        "NotoSansSC-Regular.ttf",
        os.path.join("fonts", "NotoSansSC-Regular.otf"),
        os.path.join("fonts", "NotoSansSC-Regular.ttf"),
        os.path.join("font", "NotoSansSC-Regular.otf"),
        os.path.join("font", "NotoSansSC-Regular.ttf"),
        os.path.join("font", "Noto_Sans_SC", "static", "NotoSansSC-Regular.otf"),
        os.path.join("font", "Noto_Sans_SC", "static", "NotoSansSC-Regular.ttf"),
        os.path.join(here, "NotoSansSC-Regular.otf"),
        os.path.join(here, "NotoSansSC-Regular.ttf"),
        os.path.join(here, "fonts", "NotoSansSC-Regular.otf"),
        os.path.join(here, "fonts", "NotoSansSC-Regular.ttf"),
        os.path.join(here, "font", "NotoSansSC-Regular.otf"),
        os.path.join(here, "font", "NotoSansSC-Regular.ttf"),
        os.path.join(here, "font", "Noto_Sans_SC", "static", "NotoSansSC-Regular.otf"),
        os.path.join(here, "font", "Noto_Sans_SC", "static", "NotoSansSC-Regular.ttf"),
    ]

    for font_path in candidate_names:
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont('CN', font_path))
                return 'CN'
            except Exception:
                continue

    # Fallback to built-in Unicode CID fonts provided by ReportLab
    for builtin in ('STSong-Light', 'HeiseiMin-W3'):
        try:
            pdfmetrics.registerFont(UnicodeCIDFont(builtin))
            return builtin
        except Exception:
            continue

    # Last resort: Helvetica (may not render Chinese)
    return 'Helvetica'

FONT_MAIN = register_fonts()

# --- Utilities ---
def draw_gradient_rect(c, x, y, w, h, start_color, end_color, steps=80, horizontal=True):
    """
    Approximate linear gradient by narrow rect strips.
    horizontal=True: left->right gradient
    """
    for i in range(steps):
        ratio = i / float(max(steps - 1, 1))
        r = start_color.red + ratio * (end_color.red - start_color.red)
        g = start_color.green + ratio * (end_color.green - start_color.green)
        b = start_color.blue + ratio * (end_color.blue - start_color.blue)
        c.setFillColor(colors.Color(r, g, b))
        if horizontal:
            c.rect(x + w * ratio, y, w / steps + 0.2, h, stroke=0, fill=1)
        else:
            c.rect(x, y + h * ratio, w, h / steps + 0.2, stroke=0, fill=1)

def draw_header_footer(c, page_no=None):
    # header rule
    c.setStrokeColor(NEUTRAL_GRAY)
    c.setLineWidth(0.5)
    c.line(20*mm, A4_H - 15*mm, A4_W - 20*mm, A4_H - 15*mm)

    # footer: left text + right page number
    c.setFont(FONT_MAIN, 9)
    c.setFillColor(NEUTRAL_GRAY)
    c.drawString(20*mm, 12*mm, f"{BRAND_EN} | Brand Visual Identity Guide")
    if page_no is not None:
        c.drawRightString(A4_W - 20*mm, 12*mm, f"{page_no}")

def draw_title_block(c, title_cn, title_en, x, y, w):
    c.setFillColor(NEUTRAL_GRAY)
    c.setFont(FONT_MAIN, 20)
    c.drawString(x, y, title_cn)

    c.setFont(FONT_MAIN, 12)
    c.setFillColor(TEXT_DIM2)
    c.drawString(x, y - 12*mm, title_en)

    # separator rule
    c.setStrokeColor(BG_LIGHT)
    c.setLineWidth(1)
    c.line(x, y - 16*mm, x + w, y - 16*mm)

def draw_logo_mark(c, cx, cy, size=36*mm):
    """
    Draw simplified icon: play-triangle + rising bars (data growth).
    """
    # Play triangle (DATA_BLUE)
    c.setFillColor(DATA_BLUE)
    tri = [
        (cx - 0.22*size, cy - 0.30*size),
        (cx + 0.32*size, cy),
        (cx - 0.22*size, cy + 0.30*size)
    ]
    path = c.beginPath()
    path.moveTo(*tri[0])
    path.lineTo(*tri[1])
    path.lineTo(*tri[2])
    path.close()
    c.drawPath(path, stroke=0, fill=1)

    # Rising bars (FLOW_GREEN)
    bar_w = 0.08 * size
    gap = 0.04 * size
    base_x = cx - 0.12 * size
    base_y = cy - 0.20 * size
    heights = [0.20 * size, 0.30 * size, 0.42 * size]
    for i, h in enumerate(heights):
        c.setFillColor(FLOW_GREEN)
        c.rect(base_x + i * (bar_w + gap), base_y, bar_w, h, stroke=0, fill=1)

def cover_page(c):
    # background gradient
    draw_gradient_rect(c, 0, 0, A4_W, A4_H, DATA_BLUE, FLOW_GREEN, steps=140, horizontal=True)

    # white panel (no alpha to maximize compatibility)
    panel_w = A4_W * 0.72
    panel_h = A4_H * 0.56
    panel_x = (A4_W - panel_w) / 2
    panel_y = (A4_H - panel_h) / 2

    c.setFillColor(colors.white)
    c.roundRect(panel_x, panel_y, panel_w, panel_h, 10*mm, stroke=0, fill=1)

    # logo icon
    draw_logo_mark(c, panel_x + 25*mm, panel_y + panel_h - 30*mm, size=30*mm)

    # title
    c.setFillColor(NEUTRAL_GRAY)
    c.setFont(FONT_MAIN, 28)
    c.drawString(panel_x + 60*mm, panel_y + panel_h - 28*mm, BRAND_EN)

    c.setFont(FONT_MAIN, 16)
    c.setFillColor(TEXT_DIM)
    c.drawString(panel_x + 60*mm, panel_y + panel_h - 42*mm, BRAND_CN)

    c.setFont(FONT_MAIN, 14)
    c.setFillColor(NEUTRAL_GRAY)
    c.drawString(panel_x + 20*mm, panel_y + panel_h - 65*mm, "Brand Visual Identity Guide")

    # slogan
    c.setFont(FONT_MAIN, 13)
    c.setFillColor(colors.HexColor("#1F2937"))
    c.drawString(panel_x + 20*mm, panel_y + 20*mm, SLOGAN_CN + "  |  " + SLOGAN_EN)

def page_logo_standards(c, page_no):
    c.setFillColor(BG_LIGHT)
    c.rect(0, 0, A4_W, A4_H, stroke=0, fill=1)
    draw_header_footer(c, page_no)
    draw_title_block(c, "LOGO 标准 / Logo Standards", "Construction • Clear Space • Versions",
                     20*mm, A4_H - 30*mm, A4_W - 40*mm)

    # Full color (on light)
    c.setFillColor(colors.white)
    c.roundRect(20*mm, A4_H - 110*mm, 80*mm, 60*mm, 4*mm, stroke=0, fill=1)
    draw_logo_mark(c, 20*mm + 20*mm, A4_H - 80*mm, size=22*mm)

    c.setFillColor(NEUTRAL_GRAY)
    c.setFont(FONT_MAIN, 14)
    c.drawString(20*mm + 45*mm, A4_H - 70*mm, BRAND_EN)
    c.setFont(FONT_MAIN, 10)
    c.setFillColor(TEXT_DIM2)
    c.drawString(20*mm + 45*mm, A4_H - 82*mm, BRAND_CN)

    c.setFont(FONT_MAIN, 10)
    c.setFillColor(NEUTRAL_GRAY)
    c.drawString(20*mm, A4_H - 115*mm, "全彩主版 / Full Color")

    # Reversed (on dark)
    c.setFillColor(INK_DARK)
    c.roundRect(115*mm, A4_H - 110*mm, 80*mm, 60*mm, 4*mm, stroke=0, fill=1)
    # simulate reversed by drawing white text; icon仍按全彩演示（简化）
    draw_logo_mark(c, 115*mm + 40*mm, A4_H - 80*mm, size=22*mm)
    c.setFillColor(colors.white)
    c.setFont(FONT_MAIN, 14)
    c.drawString(115*mm + 65*mm, A4_H - 70*mm, BRAND_EN)
    c.setFont(FONT_MAIN, 10)
    c.drawString(115*mm + 65*mm, A4_H - 82*mm, BRAND_CN)

    c.setFont(FONT_MAIN, 10)
    c.setFillColor(NEUTRAL_GRAY)
    c.drawString(115*mm, A4_H - 115*mm, "反白版 / Reversed")

    # Monochrome
    c.setFillColor(colors.white)
    c.roundRect(20*mm, A4_H - 185*mm, 80*mm, 60*mm, 4*mm, stroke=0, fill=1)
    # monochrome: use neutral gray for both icon and text (简化)
    draw_logo_mark(c, 20*mm + 40*mm, A4_H - 155*mm, size=22*mm)
    c.setFont(FONT_MAIN, 10)
    c.setFillColor(NEUTRAL_GRAY)
    c.drawString(20*mm, A4_H - 190*mm, "单色版 / Monochrome")

    # Clear space & min size
    c.setFont(FONT_MAIN, 10)
    c.setFillColor(colors.HexColor("#374151"))
    c.drawString(115*mm, A4_H - 185*mm, "安全区（Clear Space）建议：LOGO 高度的 1/4")
    c.drawString(115*mm, A4_H - 195*mm, "最小显示宽度：20 mm")

def page_colors(c, page_no):
    c.setFillColor(colors.white)
    c.rect(0, 0, A4_W, A4_H, stroke=0, fill=1)
    draw_header_footer(c, page_no)
    draw_title_block(c, "品牌色彩 / Color System", "Primary • Secondary • Gradient",
                     20*mm, A4_H - 30*mm, A4_W - 40*mm)

    # Swatches
    def swatch(x, y, w, h, color, label):
        c.setFillColor(color)
        c.roundRect(x, y, w, h, 3*mm, stroke=0, fill=1)
        c.setFillColor(NEUTRAL_GRAY)
        c.setFont(FONT_MAIN, 10)
        c.drawString(x, y - 5*mm, label)

    swatch(20*mm, A4_H - 85*mm, 45*mm, 25*mm, DATA_BLUE, "Data Blue  #1E90FF")
    swatch(70*mm, A4_H - 85*mm, 45*mm, 25*mm, FLOW_GREEN, "Flow Green #30D7A9")
    swatch(120*mm, A4_H - 85*mm, 45*mm, 25*mm, NEUTRAL_GRAY, "Neutral Gray #3C3C3C")
    swatch(170*mm, A4_H - 85*mm, 25*mm, 25*mm, BG_LIGHT, "BG Light #F5F8FA")

    # Gradient example
    c.setFont(FONT_MAIN, 10)
    c.setFillColor(NEUTRAL_GRAY)
    c.drawString(20*mm, A4_H - 105*mm, "主渐变方向：左→右（45° 近似）")
    draw_gradient_rect(c, 20*mm, A4_H - 150*mm, 175*mm, 30*mm, DATA_BLUE, FLOW_GREEN, steps=140, horizontal=True)

def page_typography(c, page_no):
    c.setFillColor(BG_LIGHT)
    c.rect(0, 0, A4_W, A4_H, stroke=0, fill=1)
    draw_header_footer(c, page_no)
    draw_title_block(c, "字体系统 / Typography", "Chinese & English Families • Hierarchy",
                     20*mm, A4_H - 30*mm, A4_W - 40*mm)

    c.setFillColor(NEUTRAL_GRAY)
    c.setFont(FONT_MAIN, 18)
    c.drawString(20*mm, A4_H - 60*mm, "中文：思源黑体 / HarmonyOS Sans SC（建议）")
    c.setFont(FONT_MAIN, 12)
    c.setFillColor(TEXT_DIM)
    c.drawString(20*mm, A4_H - 70*mm, "层级建议：H1 加粗 28–32px；H2 中粗 22–26px；正文字号 14–16px")

    c.setFillColor(NEUTRAL_GRAY)
    c.setFont(FONT_MAIN, 18)
    c.drawString(20*mm, A4_H - 95*mm, "English: Inter / Helvetica Neue")
    c.setFont(FONT_MAIN, 12)
    c.setFillColor(TEXT_DIM)
    c.drawString(20*mm, A4_H - 105*mm, "Heading 28–32px; Subheading 22–26px; Body 14–16px")

    # example line
    c.setFillColor(NEUTRAL_GRAY)
    c.setFont(FONT_MAIN, 14)
    c.drawString(20*mm, A4_H - 135*mm, "示例 / Example:")
    c.setFont(FONT_MAIN, 20)
    c.drawString(20*mm, A4_H - 150*mm, "小荷包 解生活之所急")
    c.setFont(FONT_MAIN, 12)
    c.setFillColor(TEXT_DIM2)
    c.drawString(20*mm, A4_H - 162*mm, SLOGAN_EN)

def page_usage_examples(c, page_no):
    c.setFillColor(colors.white)
    c.rect(0, 0, A4_W, A4_H, stroke=0, fill=1)
    draw_header_footer(c, page_no)
    draw_title_block(c, "应用示例 / Usage Examples", "Website • App Icon • Business Card • Banner",
                     20*mm, A4_H - 30*mm, A4_W - 40*mm)

    # Website header mock
    c.setFont(FONT_MAIN, 10)
    c.setFillColor(NEUTRAL_GRAY)
    c.drawString(20*mm, A4_H - 55*mm, "网站页眉 / Website Header")
    c.setFillColor(BG_LIGHT)
    c.roundRect(20*mm, A4_H - 95*mm, 170*mm, 25*mm, 3*mm, stroke=0, fill=1)
    draw_logo_mark(c, 28*mm, A4_H - 82*mm, size=14*mm)
    c.setFillColor(NEUTRAL_GRAY)
    c.setFont(FONT_MAIN, 12)
    c.drawString(38*mm, A4_H - 78*mm, BRAND_EN + "  |  " + BRAND_CN)

    # App icon mock
    c.setFont(FONT_MAIN, 10)
    c.setFillColor(NEUTRAL_GRAY)
    c.drawString(20*mm, A4_H - 115*mm, "App 图标 / App Icon")
    draw_gradient_rect(c, 20*mm, A4_H - 165*mm, 35*mm, 35*mm, DATA_BLUE, FLOW_GREEN, steps=80, horizontal=True)
    draw_logo_mark(c, 37.5*mm, A4_H - 147.5*mm, size=16*mm)

    # Business card mock
    c.setFillColor(NEUTRAL_GRAY)
    c.setFont(FONT_MAIN, 10)
    c.drawString(70*mm, A4_H - 115*mm, "名片 / Business Card")
    c.setFillColor(colors.HexColor("#F9FAFB"))
    c.roundRect(70*mm, A4_H - 165*mm, 60*mm, 35*mm, 3*mm, stroke=0, fill=1)
    draw_logo_mark(c, 78*mm, A4_H - 147.5*mm, size=12*mm)
    c.setFillColor(NEUTRAL_GRAY)
    c.setFont(FONT_MAIN, 9)
    c.drawString(92*mm, A4_H - 142*mm, "DataPlayer")
    c.setFillColor(TEXT_DIM2)
    c.drawString(92*mm, A4_H - 150*mm, "数据智能分发 · Smart Flow")

    # Banner mock
    c.setFillColor(NEUTRAL_GRAY)
    c.setFont(FONT_MAIN, 10)
    c.drawString(135*mm, A4_H - 115*mm, "横幅 / Banner")
    draw_gradient_rect(c, 135*mm, A4_H - 165*mm, 55*mm, 35*mm, DATA_BLUE, FLOW_GREEN, steps=80, horizontal=True)
    c.setFillColor(colors.white)
    c.setFont(FONT_MAIN, 10)
    c.drawCentredString(135*mm + 27.5*mm, A4_H - 147.5*mm, SLOGAN_EN)

def page_dos_donts(c, page_no):
    c.setFillColor(BG_LIGHT)
    c.rect(0, 0, A4_W, A4_H, stroke=0, fill=1)
    draw_header_footer(c, page_no)
    draw_title_block(c, "Do / Don’t", "Usage Guidance & Misuse Examples",
                     20*mm, A4_H - 30*mm, A4_W - 40*mm)

    c.setFont(FONT_MAIN, 11)
    c.setFillColor(NEUTRAL_GRAY)
    c.drawString(20*mm, A4_H - 55*mm, "Do：保持安全区、使用标准色、遵循最小尺寸、复杂背景使用反白版或描边。")
    c.drawString(20*mm, A4_H - 65*mm, "Don’t：拉伸变形、随意换色、过度阴影、旋转倾斜、在低对比背景直接使用主版。")

    # Do panel
    c.setFillColor(colors.white)
    c.roundRect(20*mm, A4_H - 160*mm, 80*mm, 80*mm, 4*mm, stroke=0, fill=1)
    draw_logo_mark(c, 20*mm + 40*mm, A4_H - 120*mm, size=20*mm)
    c.setFillColor(NEUTRAL_GRAY)
    c.setFont(FONT_MAIN, 10)
    c.drawCentredString(20*mm + 40*mm, A4_H - 165*mm, "正确用法 / Do")

    # Don’t panel
    c.setFillColor(colors.white)
    c.roundRect(115*mm, A4_H - 160*mm, 80*mm, 80*mm, 4*mm, stroke=0, fill=1)
    # intentionally wrong example (rotate + wrong color)
    c.saveState()
    c.translate(115*mm + 40*mm, A4_H - 120*mm)
    c.rotate(20)
    c.setFillColor(colors.magenta)
    # replace with a wrong circle to indicate misuse
    c.circle(0, 0, 10*mm, stroke=0, fill=1)
    c.restoreState()
    c.setFillColor(NEUTRAL_GRAY)
    c.setFont(FONT_MAIN, 10)
    c.drawCentredString(115*mm + 40*mm, A4_H - 165*mm, "错误用法 / Don’t")

def page_legal(c, page_no):
    c.setFillColor(colors.white)
    c.rect(0, 0, A4_W, A4_H, stroke=0, fill=1)
    draw_header_footer(c, page_no)

    c.setFont(FONT_MAIN, 18)
    c.setFillColor(NEUTRAL_GRAY)
    c.drawString(20*mm, A4_H - 40*mm, "版权与使用 / Legal & Usage")

    c.setFont(FONT_MAIN, 11)
    c.setFillColor(colors.HexColor("#374151"))
    text1 = (
        f"本手册用于 {BRAND_EN}（{BRAND_CN}）品牌视觉识别的设计与落地执行，"
        "未经许可不得修改、分发或用于与公司无关的商用目的。LOGO、图形语言、配色与排版规范须严格遵守本手册规定。"
    )
    c.drawString(20*mm, A4_H - 55*mm, text1)

    text2 = (
        "如需在特殊背景或尺寸下使用，请联系品牌管理人获取适配稿或审批。"
        "本文件中示例仅为演示用途，实际落地请以矢量源文件为准。"
    )
    c.drawString(20*mm, A4_H - 65*mm, text2)

    c.setFont(FONT_MAIN, 10)
    c.setFillColor(TEXT_DIM2)
    c.drawString(20*mm, 20*mm, f"© 2025 {BRAND_EN}. All rights reserved.")

def build_pdf(output="DataPlayer_Brand_Manual.pdf"):
    c = canvas.Canvas(output, pagesize=A4)
    cover_page(c);             c.showPage()
    page_logo_standards(c, 2); c.showPage()
    page_colors(c, 3);         c.showPage()
    page_typography(c, 4);     c.showPage()
    page_usage_examples(c, 5); c.showPage()
    page_dos_donts(c, 6);      c.showPage()
    page_legal(c, 7);          c.showPage()
    c.save()
    print(f"OK -> {output}")

if __name__ == "__main__":
    build_pdf()
