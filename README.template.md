<p align="center">
  <strong style="font-size:1.9rem;">Threat Intel Atlas · Daily Signal Briefing</strong><br />
  <span style="font-size:1rem;color:#6ecff6;">Compiled from {{ feeds_count }} intelligence sources · refreshed {{ generated_at.strftime("%Y-%m-%d %H:%M UTC") }}</span>
</p>

---

### Collection Snapshot

| Metric | Value |
| --- | --- |
| Total signals retained | {{ summary.total_count }} |
| Signals detected in the last 24h | {{ summary.recent_count }} |
| Signals surfaced in this report | {{ daily_count }} |

---

### Daily Signals (UTC newest → oldest)

{{ markdown_snippet | safe }}

{% if errors %}
---

<details>
<summary><strong>Feeds that returned errors this run</strong></summary>

{% for name, message in errors.items() %}
- {{ name }} — {{ message }}
{% endfor %}
</details>
{% endif %}

---

<p align="center">
  <sub>Signals older than 24 hours are automatically moved to the archive.</sub>
</p>
