# PCM Trading Generator V3

Telegram-ready image generator for PCM Trading, built for GitHub + Render.

## What changed in V3

- No strategy label in the artwork
- Daily, weekly and monthly posters are treated as standalone outputs
- Monthly poster now shows only the result, without trades, win rate or drawdown
- PNG is returned as an automatic file download in the browser

## Features

- 1080x1350 PNG output
- Daily result poster
- Weekly result poster
- Monthly performance poster
- 5 randomized profit texts and 5 randomized loss texts for daily posts
- Randomized badges for variation
- Uses your selected PCM logo
- Ready for GitHub + Render

## Local run

```bash
pip install -r requirements.txt
python app.py
```

Open:

```bash
http://127.0.0.1:5000/
```

## Render deploy

If Render does not auto-read `render.yaml`, use:

```bash
Build Command: pip install -r requirements.txt
Start Command: gunicorn --bind 0.0.0.0:$PORT app:app
```

## Example URLs

### Daily

```text
/generate?result=3.74&brand=PCM%20Trading&seed=2026-03-09
```

### Weekly

```text
/generate/weekly?result=10.60&period_label=Weekly%20Performance&brand=PCM%20Trading&seed=2026-week-10
```

### Monthly

```text
/generate/monthly?result=12.40&period_label=Monthly%20Performance&brand=PCM%20Trading&seed=2026-03
```
