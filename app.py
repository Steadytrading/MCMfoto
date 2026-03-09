from flask import Flask, request, send_file, render_template
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os, re, random, tempfile

app = Flask(__name__)

WIDTH, HEIGHT = 1080, 1350
HANDLE = "@mcm_trading"
SITE = "mcmtrading.netlify.app"
LOGO_PATH = os.path.join(os.path.dirname(__file__), "static", "mcm_logo.png")

POSITIVE_TEXTS = [
    "Today we closed the day at {profit}% profit. Our strategy stays focused on low risk, controlled entries, and safe trade management.",
    "Today we secured {profit}% profit through disciplined execution, low risk exposure, and patient setups.",
    "Another strong day at {profit}% profit. We continue to prioritize capital protection and safe, selective trades.",
    "Today's result came in at {profit}% profit. Our approach remains the same: low risk, consistency, and control.",
    "We finished the day with {profit}% profit. Smart capital management and low-risk setups stay at the core of our strategy."
]

NEGATIVE_TEXTS = [
    "Today we closed with a small loss of {profit}%. Protecting capital always comes first in our strategy.",
    "Today's result was {profit}%. We kept the loss controlled to preserve capital for stronger setups ahead.",
    "We ended the day at {profit}%. Some sessions are about protecting the account and staying disciplined.",
    "Today came in at {profit}%. The loss was small and controlled because risk management always comes first.",
    "We finished at {profit}%. Even on red days, our focus stays on low risk and protecting assets."
]

THEMES = [
    {"top": (7, 14, 28), "bottom": (10, 25, 48), "gold": (232, 194, 66), "card": (16, 23, 39), "line": (44, 62, 98)},
    {"top": (8, 16, 32), "bottom": (16, 30, 58), "gold": (244, 208, 92), "card": (15, 24, 40), "line": (52, 70, 108)},
    {"top": (10, 18, 34), "bottom": (18, 34, 62), "gold": (226, 186, 64), "card": (17, 25, 42), "line": (50, 68, 104)},
]

def load_font(name, size):
    try:
        return ImageFont.truetype(name, size)
    except Exception:
        return ImageFont.load_default()

FONT_RESULT = load_font("DejaVuSans-Bold.ttf", 56)
FONT_PROFIT = load_font("DejaVuSans-Bold.ttf", 122)
FONT_BODY = load_font("DejaVuSans.ttf", 34)
FONT_SMALL = load_font("DejaVuSans.ttf", 24)
FONT_BADGE = load_font("DejaVuSans-Bold.ttf", 30)
FONT_FOOT = load_font("DejaVuSans.ttf", 26)

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
        t = y / max(1, height - 1)
        color = (
            int(top[0] * (1 - t) + bottom[0] * t),
            int(top[1] * (1 - t) + bottom[1] * t),
            int(top[2] * (1 - t) + bottom[2] * t),
        )
        draw.line((0, y, width, y), fill=color)

def add_logo_background(img):
    if not os.path.exists(LOGO_PATH):
        return
    logo = Image.open(LOGO_PATH).convert("RGBA")
    bg_logo = logo.copy()
    max_w = int(WIDTH * 0.72)
    scale = max_w / bg_logo.size[0]
    bg_logo = bg_logo.resize((int(bg_logo.size[0] * scale), int(bg_logo.size[1] * scale)))
    alpha = bg_logo.split()[-1].point(lambda p: int(p * 0.16))
    bg_logo.putalpha(alpha)
    bg_logo = bg_logo.filter(ImageFilter.GaussianBlur(2))
    img.alpha_composite(bg_logo, ((WIDTH - bg_logo.size[0]) // 2, 70))

    sharp = logo.copy()
    max_w2 = int(WIDTH * 0.42)
    scale2 = max_w2 / sharp.size[0]
    sharp = sharp.resize((int(sharp.size[0] * scale2), int(sharp.size[1] * scale2)))
    img.alpha_composite(sharp, ((WIDTH - sharp.size[0]) // 2, 45))

def draw_subtle_chart(draw, is_negative, accent):
    pts_up = [(80, 1020), (200, 970), (320, 995), (440, 915), (560, 940), (680, 860), (800, 810), (940, 740)]
    pts_down = [(80, 740), (200, 790), (320, 770), (440, 860), (560, 900), (680, 980), (800, 1020), (940, 1080)]
    pts = pts_down if is_negative else pts_up
    color = (225, 95, 95) if is_negative else accent
    for i in range(len(pts)-1):
        draw.line((pts[i], pts[i+1]), fill=color, width=8)

def generate_image(profit_input):
    raw = clean_profit(profit_input)
    try:
        val = float(raw)
    except Exception:
        val = 0.0

    is_negative = val < 0
    abs_text = f"{abs(val):.2f}"
    shown_profit = f"-{abs_text}" if is_negative else f"+{abs_text}"
    theme = random.choice(THEMES)
    body_template = random.choice(NEGATIVE_TEXTS if is_negative else POSITIVE_TEXTS)
    body = body_template.format(profit=abs_text)

    img = Image.new("RGBA", (WIDTH, HEIGHT), theme["top"] + (255,))
    draw = ImageDraw.Draw(img)
    draw_gradient(draw, WIDTH, HEIGHT, theme["top"], theme["bottom"])

    for x in range(0, WIDTH, 90):
        draw.line((x, 0, x, HEIGHT), fill=(24, 34, 54), width=1)
    for y in range(0, HEIGHT, 90):
        draw.line((0, y, WIDTH, y), fill=(24, 34, 54), width=1)

    add_logo_background(img)
    draw_subtle_chart(draw, is_negative, theme["gold"])

    result_label = "TODAY'S RESULT"
    bbox = draw.textbbox((0, 0), result_label, font=FONT_RESULT)
    draw.text(((WIDTH - (bbox[2]-bbox[0]))/2, 420), result_label, font=FONT_RESULT, fill=(240, 243, 247))

    badge_text = "CAPITAL PROTECTION DAY" if is_negative else "LOW RISK STRATEGY"
    badge_fill = (170, 42, 42) if is_negative else theme["gold"]
    badge_fg = (245, 245, 245) if is_negative else (22, 18, 8)
    bb = draw.textbbox((0, 0), badge_text, font=FONT_BADGE)
    bw = (bb[2]-bb[0]) + 38
    bh = (bb[3]-bb[1]) + 22
    bx = (WIDTH - bw) / 2
    by = 500
    draw.rounded_rectangle((bx, by, bx + bw, by + bh), radius=18, fill=badge_fill)
    draw.text((bx + bw/2, by + bh/2), badge_text, font=FONT_BADGE, fill=badge_fg, anchor="mm")

    profit_color = (225, 95, 95) if is_negative else theme["gold"]
    pb = draw.textbbox((0, 0), shown_profit + "%", font=FONT_PROFIT)
    draw.text(((WIDTH - (pb[2]-pb[0]))/2, 585), shown_profit + "%", font=FONT_PROFIT, fill=profit_color)

    card = (90, 790, 990, 1115)
    draw.rounded_rectangle(card, radius=28, fill=theme["card"], outline=theme["line"], width=3)

    lines = wrap_text(draw, body, FONT_BODY, 760)
    y = 860
    for line in lines:
        lb = draw.textbbox((0, 0), line, font=FONT_BODY)
        draw.text(((WIDTH - (lb[2]-lb[0]))/2, y), line, font=FONT_BODY, fill=(240, 243, 247))
        y += 52

    footer = f"{HANDLE}  •  {SITE}"
    fb = draw.textbbox((0, 0), footer, font=FONT_FOOT)
    draw.text(((WIDTH - (fb[2]-fb[0]))/2, 1235), footer, font=FONT_FOOT, fill=(180, 190, 210))

    fd, out_path = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    img.convert("RGB").save(out_path, format="PNG")
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
