<div align="center" style="margin-bottom:32px;">
  <div style="display:inline-block;padding:22px 32px;border-radius:20px;background:linear-gradient(135deg,#051026,#0b0f23 52%,#061f2f);border:1px solid rgba(122,240,255,0.35);box-shadow:0 0 42px rgba(122,240,255,0.28);color:#7af0ff;font-family:'Courier New',monospace;font-size:1.55rem;letter-spacing:0.18rem;text-transform:uppercase;">
    Threat Intel Atlas · Weekly Signal Briefing
  </div>
  <p style="margin-top:18px;color:#8cf6d6;font-size:1rem;font-family:'Trebuchet MS',sans-serif;letter-spacing:0.05rem;">
    A rolling seven-day intercept of the most urgent threat intelligence drops — neon grade, field ready.
  </p>
  <div style="margin-top:12px;padding:10px 18px;border-radius:999px;background:rgba(8,24,48,0.8);border:1px solid rgba(122,240,255,0.25);color:#7ae7ff;font-family:'Courier New',monospace;font-size:0.9rem;">
    updated {{ generated_at.strftime("%Y-%m-%d %H:%M UTC") }} | monitoring {{ feeds_count }} sources | current haul {{ weekly_count }} signals
  </div>
</div>

<div style="height:3px;width:100%;background:linear-gradient(90deg,rgba(122,240,255,0) 0%,rgba(122,240,255,0.65) 45%,rgba(255,122,217,0.65) 55%,rgba(255,122,217,0) 100%);margin-bottom:32px;"></div>

<div style="display:flex;flex-direction:column;gap:18px;">
{{ markdown_snippet | safe }}
</div>

<div style="margin-top:48px;padding:12px 18px;border-radius:14px;border:1px solid rgba(122,240,255,0.2);background:rgba(6,16,30,0.85);color:#73ecff;font-family:'Courier New',monospace;font-size:0.85rem;text-align:center;">
  Weekly archive auto-purges entries older than seven days — stay sharp, stay current.
</div>
