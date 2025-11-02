<p align="center">
  <strong style="font-size:1.9rem;">Threat Intel Atlas · Weekly Signal Briefing</strong><br />
  <span style="font-size:1rem;color:#6ecff6;">Compiled from {{ feeds_count }} intelligence sources · refreshed {{ generated_at.strftime("%Y-%m-%d %H:%M UTC") }}</span>
</p>

---

### Collection Snapshot

| Metric | Value |
| --- | --- |
| Total signals retained | {{ summary.total_count }} |
| Signals detected in the last 24h | {{ summary.recent_count }} |
| Entries captured this week | {{ weekly_count }} |

---

### Weekly Signals (UTC newest → oldest)

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
  <sub>Signals older than seven days are automatically moved to the archive.</sub>
</p>
