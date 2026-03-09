
from flask import Flask, request, send_file, render_template
from PIL import Image, ImageDraw, ImageFont
import os, re, random, tempfile

app = Flask(__name__)

WIDTH, HEIGHT = 1080, 1080
BRAND = "MCM TRADING"
HANDLE = "@mcm_trading"
SITE = "mcmtrading.netlify.app"

POSITIVE_TEXTS = [
    "Today we closed the day at {profit}% profit. Our strategy focuses on low risk and controlled trades.",
    "Today we achieved {profit}% profit using our disciplined low‑risk trading strategy.",
    "Another solid day: {profit}% profit. Consistency and safe trades remain our focus.",
    "Today's result: {profit}% profit. We always prioritize risk management.",
    "We secured {profit}% profit today through patient, low‑risk setups."
]

NEGATIVE_TEXTS = [
    "Today ended with a small loss of {profit}%. Protecting capital always comes first.",
    "We closed today at {profit}%. Losses are kept small thanks to strict risk management.",
    "Today's result was {profit}%. Some days we step back to protect our capital.",
    "We finished at {profit}% today. Our strategy always protects the account first.",
    "Today came in at {profit}%. Small losses are part of disciplined trading."
]

def load_font(name, size):
    try:
        return ImageFont.truetype(name, size)
    except:
        return ImageFont.load_default()

FONT_TITLE = load_font("DejaVuSans-Bold.ttf", 70)
FONT_PROFIT = load_font("DejaVuSans-Bold.ttf", 140)
FONT_BODY = load_font("DejaVuSans.ttf", 42)
FONT_SMALL = load_font("DejaVuSans.ttf", 32)

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
        bbox = draw.textbbox((0,0), test, font=font)
        if bbox[2]-bbox[0] <= max_width:
            current = test
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines

def generate_image(profit_input):

    raw = clean_profit(profit_input)

    try:
        val = float(raw)
    except:
        val = 0

    is_negative = val < 0
    abs_text = f"{abs(val):.2f}"
    shown_profit = f"-{abs_text}" if is_negative else f"+{abs_text}"

    template = random.choice(NEGATIVE_TEXTS if is_negative else POSITIVE_TEXTS)
    body = template.format(profit=abs_text)

    img = Image.new("RGB",(WIDTH,HEIGHT),(10,14,24))
    draw = ImageDraw.Draw(img)

    title = "DAILY RESULT"
    bbox = draw.textbbox((0,0),title,font=FONT_TITLE)
    draw.text(((WIDTH-(bbox[2]-bbox[0]))/2,70),title,font=FONT_TITLE,fill=(235,235,235))

    profit_color = (230,195,70) if not is_negative else (220,90,90)
    bbox = draw.textbbox((0,0),shown_profit+"%",font=FONT_PROFIT)
    draw.text(((WIDTH-(bbox[2]-bbox[0]))/2,190),shown_profit+"%",font=FONT_PROFIT,fill=profit_color)

    bbox = draw.textbbox((0,0),BRAND,font=FONT_SMALL)
    draw.text(((WIDTH-(bbox[2]-bbox[0]))/2,350),BRAND,font=FONT_SMALL,fill=(210,215,230))

    lines = wrap_text(draw, body, FONT_BODY, 900)

    y = 450
    for line in lines:
        bbox = draw.textbbox((0,0),line,font=FONT_BODY)
        draw.text(((WIDTH-(bbox[2]-bbox[0]))/2,y),line,font=FONT_BODY,fill=(240,240,240))
        y += 60

    footer = f"{HANDLE} • {SITE}"
    bbox = draw.textbbox((0,0),footer,font=FONT_SMALL)
    draw.text(((WIDTH-(bbox[2]-bbox[0]))/2,940),footer,font=FONT_SMALL,fill=(180,185,200))

    fd,out_path = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    img.save(out_path,"PNG")

    return out_path


@app.route("/")
def home():
    return render_template("image_index.html")


@app.route("/generate-image",methods=["POST"])
def generate():
    profit = request.form.get("profit","")

    if not profit.strip():
        return render_template("image_index.html",error="Enter today's profit")

    img = generate_image(profit)

    return send_file(img,as_attachment=True,download_name="daily_result.png")


if __name__ == "__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)))
