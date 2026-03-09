from flask import Flask, request, send_file, render_template
from PIL import Image, ImageDraw, ImageFont
import os, re, random, tempfile

app = Flask(__name__)

WIDTH, HEIGHT = 1080, 1350
BRAND = "MCM TRADING"
HANDLE = "@mcm_trading"
SITE = "mcmtrading.netlify.app"

POSITIVE_TEXTS = [
    "Today we closed the day at {profit}% profit. Our strategy is built on low risk, controlled entries, and safe trades.",
    "Today we secured {profit}% profit through disciplined execution and a low-risk trading approach.",
    "Another strong day: {profit}% profit. We stay focused on capital protection and safe setups.",
    "Today's result came in at {profit}% profit. Steady growth and risk control remain our priority.",
    "We finished the day with {profit}% profit. Our strategy favors patience, precision, and low-risk trades."
]

NEGATIVE_TEXTS = [
    "Today we closed with a small loss of {profit}%. Protecting capital always comes first in our strategy.",
    "Today's result was {profit}%. We kept the loss controlled to preserve capital for stronger setups.",
    "We ended the day at {profit}%. Some sessions are about protecting the account and staying disciplined.",
    "Today came in at {profit}%. The loss was small and controlled because risk management comes first.",
    "We finished at {profit}%. Even on red days, our focus stays on low risk and protecting assets."
]

THEMES = [
    {"bg_top": (8, 12, 22), "bg_bottom": (17, 28, 46), "accent": (232, 194, 66), "card": (16, 22, 36), "outline": (48, 64, 96)},
    {"bg_top": (9, 14, 26), "bg_bottom": (25, 35, 58), "accent": (246, 214, 107), "card": (18, 25, 40), "outline": (58, 74, 110)},
    {"bg_top": (10, 16, 30), "bg_bottom": (18, 32, 52), "accent": (221, 183, 58), "card": (14, 22, 38), "outline": (44, 60, 92)},
    {"bg_top": (7, 11, 20), "bg_bottom": (20, 30, 50), "accent": (240, 200, 90), "card": (15, 20, 34), "outline": (50, 66, 100)},
    {"bg_top": (11, 15, 24), "bg_bottom": (22, 33, 53), "accent": (230, 190, 72), "card": (17, 24, 39), "outline": (52, 68, 102)},
]

def load_font(name, size):
    try:
        return ImageFont.truetype(name, size)
    except Exception:
        return ImageFont.load_default()

FONT_TITLE = load_font("DejaVuSans-Bold.ttf", 68)
FONT_PROFIT = load_font("DejaVuSans-Bold.ttf", 124)
FONT_BODY = load_font("DejaVuSans.ttf", 36)
FONT_SMALL = load_font("DejaVuSans.ttf", 26)
FONT_BADGE = load_font("DejaVuSans-Bold.ttf", 34)

def clean_profit(value):
    s = (value or "").strip().replace(",", ".")
    s = re.sub(r"[^0-9.\-+]", "", s)
    return s or "0"

def wrap_text(draw, text, font, max_width):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = word if not current else current + " " + word
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines

def draw_gradient(draw, width, height, top, bottom):
    for y in range(height):
        t = y / max(height - 1, 1)
        r = int(top[0] * (1 - t) + bottom[0] * t)
        g = int(top[1] * (1 - t) + bottom[1] * t)
        b = int(top[2] * (1 - t) + bottom[2] * t)
        draw.line((0, y, width, y), fill=(r, g, b))

def draw_candles(draw, is_negative, accent):
    start_x = 70
    candle_w = 42
    gap = 18
    data_up = [
        (860, 930, 820, 960), (820, 900, 790, 930), (780, 860, 750, 890),
        (800, 870, 760, 900), (740, 810, 700, 840), (700, 760, 670, 790),
        (730, 780, 690, 820), (660, 720, 630, 750), (620, 690, 590, 720),
        (590, 660, 560, 690), (610, 670, 570, 700)
    ]
    data_down = [
        (620, 700, 590, 730), (650, 730, 620, 760), (690, 770, 660, 800),
        (670, 740, 640, 770), (720, 790, 690, 820), (760, 840, 730, 870),
        (740, 820, 710, 850), (790, 870, 760, 900), (830, 910, 800, 940),
        (860, 940, 830, 970), (900, 980, 870, 1010)
    ]
    data = data_down if is_negative else data_up
    for i, (o, c, h, l) in enumerate(data):
        x = start_x + i * (candle_w + gap)
        color = (220, 90, 90) if c > o else (0, 210, 130)
        draw.line((x + candle_w // 2, h, x + candle_w // 2, l), fill=(220, 225, 235), width=3)
        top = min(o, c)
        bottom = max(o, c)
        draw.rounded_rectangle((x, top, x + candle_w, bottom), radius=6, fill=color)
    pts = [(60, 880), (180, 820), (300, 850), (420, 760), (540, 790), (660, 700), (780, 620), (930, 560)]
    if is_negative:
        pts = [(60, 560), (180, 610), (300, 590), (420, 700), (540, 730), (660, 820), (780, 900), (930, 980)]
    for i in range(len(pts)-1):
        draw.line((pts[i], pts[i+1]), fill=accent if not is_negative else (225, 95, 95), width=7)

def generate_image(profit_input):
    raw = clean_profit(profit_input)
    try:
        val = float(raw)
    except Exception:
        val = 0.0
    is_negative = val < 0
    abs_text = f"{abs(val):.2f}"
    shown_profit = f"-{abs_text}" if is_negative else f"+{abs_text}"
    body_template = random.choice(NEGATIVE_TEXTS if is_negative else POSITIVE_TEXTS)
    body = body_template.format(profit=abs_text)
    theme = random.choice(THEMES)

    img = Image.new("RGB", (WIDTH, HEIGHT), theme["bg_top"])
    draw = ImageDraw.Draw(img)
    draw_gradient(draw, WIDTH, HEIGHT, theme["bg_top"], theme["bg_bottom"])

    for x in range(0, WIDTH, 90):
        draw.line((x, 0, x, HEIGHT), fill=(26, 34, 50), width=1)
    for y in range(0, HEIGHT, 90):
        draw.line((0, y, WIDTH, y), fill=(26, 34, 50), width=1)

    draw_candles(draw, is_negative, theme["accent"])

    title = "DAILY TRADING RESULT"
    bbox = draw.textbbox((0, 0), title, font=FONT_TITLE)
    draw.text(((WIDTH - (bbox[2]-bbox[0]))/2, 60), title, font=FONT_TITLE, fill=(238, 240, 245))

    badge_text = "LOSS DAY" if is_negative else "LOW RISK STRATEGY"
    badge_fill = (170, 40, 40) if is_negative else theme["accent"]
    badge_text_color = (245, 245, 245) if is_negative else (25, 20, 8)
    bb = draw.textbbox((0, 0), badge_text, font=FONT_BADGE)
    bw = (bb[2]-bb[0]) + 44
    bh = (bb[3]-bb[1]) + 26
    bx = (WIDTH - bw) / 2
    by = 170
    draw.rounded_rectangle((bx, by, bx + bw, by + bh), radius=20, fill=badge_fill)
    draw.text((bx + bw/2, by + bh/2), badge_text, font=FONT_BADGE, fill=badge_text_color, anchor="mm")

    profit_color = (225, 95, 95) if is_negative else theme["accent"]
    bbox = draw.textbbox((0, 0), shown_profit + "%", font=FONT_PROFIT)
    draw.text(((WIDTH - (bbox[2]-bbox[0]))/2, 270), shown_profit + "%", font=FONT_PROFIT, fill=profit_color)

    bbox = draw.textbbox((0, 0), BRAND, font=FONT_SMALL)
    draw.text(((WIDTH - (bbox[2]-bbox[0]))/2, 430), BRAND, font=FONT_SMALL, fill=(210, 218, 232))

    card = (80, 520, 1000, 900)
    draw.rounded_rectangle(card, radius=30, fill=theme["card"], outline=theme["outline"], width=3)

    lines = wrap_text(draw, body, FONT_BODY, 780)
    y = 600
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=FONT_BODY)
        draw.text(((WIDTH - (bbox[2]-bbox[0]))/2, y), line, font=FONT_BODY, fill=(240, 242, 246))
        y += 54

    footer = f"{HANDLE}  •  {SITE}"
    bbox = draw.textbbox((0, 0), footer, font=FONT_SMALL)
    draw.text(((WIDTH - (bbox[2]-bbox[0]))/2, 1240), footer, font=FONT_SMALL, fill=(178, 188, 208))

    fd, out_path = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    img.save(out_path, format="PNG")
    return out_path

@app.get("/")
def home():
    return render_template("image_index.html")

@app.post("/generate-image")
def generate_image_route():
    profit = request.form.get("profit", "")
    if not profit.strip():
        return render_template("image_index.html", error="Skriv in dagens profit, t.ex. 4.12 eller -1.20")
    out_path = generate_image(profit)
    return send_file(out_path, as_attachment=True, download_name="mcm_daily_result.png")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)
