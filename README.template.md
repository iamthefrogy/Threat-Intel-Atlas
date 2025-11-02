<div align="center">
  <h1 style="color:#78f7ff;font-family:'Space Mono',monospace;background:#050914;padding:24px 32px;border-radius:16px;border:1px solid #1b2c4a;box-shadow:0 0 30px rgba(120,247,255,0.35);">
    ⚡ Threat&nbsp;Intel&nbsp;Atlas ⚡
  </h1>
  <p style="color:#8af8d3;font-size:1.1rem;">
    Continuously harvested cyber threat intelligence — aggregated, deduplicated, and curated with a neon glow.
  </p>
</div>

---

- `last build`: {{ generated_at.strftime("%Y-%m-%d %H:%M UTC") }}
- `feeds monitored`: {{ feeds_count }}
- `signals in cache`: {{ summary.total_count }}
- `fresh past 24h`: {{ summary.recent_count }}

{% if summary.top_sources %}
<details>
  <summary><strong>Top sources (24h)</strong></summary>

{% for name, count in summary.top_sources %}
- {{ name }} · {{ count }}
{% endfor %}
</details>
{% endif %}

{% if summary.top_tags %}
<details>
  <summary><strong>Hot tags (24h)</strong></summary>

{% for tag, count in summary.top_tags %}
- {{ tag }} · {{ count }}
{% endfor %}
</details>
{% endif %}

## 🛰️ Fresh Signals

{{ markdown_snippet }}

{% if errors %}
## ⚠️ Feed Issues

The following sources could not be refreshed during the last run:

{% for name, message in errors.items() %}
- **{{ name }}** – {{ message }}
{% endfor %}
{% endif %}

---

## 🛠️ How it works

- Scheduled GitHub Actions workflow pulls ~400 intelligence feeds daily.
- Python pipeline (`scripts/run_pipeline.py`) harmonises entries, deduplicates them, and stores structured JSON in `data/`.
- README and `site/index.html` are auto-rendered from templates with the newest signals.
- Cyberpunk UI lives in `site/` and is GitHub Pages-ready.

## 🚦 Local run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/run_pipeline.py
```

## ➕ Add / update feeds

1. Edit `feeds.yaml` and append new sources under the `feeds:` list.
2. Keep the format:
   ```yaml
   - name: Your Feed Name
     url: https://example.com/feed
     category: vendor  # optional
   ```
3. Commit, push, or let the automated workflow pick it up on the next run.

## 🧪 Testing ideas

- Add pytest coverage for parsing if you extend the pipeline.
- Drop in custom tagging heuristics in `scripts/run_pipeline.py` to enrich metadata.

---

<p align="center" style="color:#7af0ff;font-size:0.9rem;">
  “Track the signal. Ignore the noise.” — Threat Intel Atlas
</p>
