#!/usr/bin/env python3
"""Contact sheet of puppet actions over time, to check motion and joints by eye before rendering.

  python3 scripts/nerd/puppet_sheet.py out.png                      # every action, narrator
  python3 scripts/nerd/puppet_sheet.py out.png german-soldier:run uk-naval:salute narrator:crawl

Each row is one costume:action, each column a moment (0 to 1.5 s). Props: costume:action:F=paper,B=briefcase
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
ALL = ["idle", "talk", "present", "point", "pointDown", "count", "thumbsUp", "think", "listen", "search", "shocked",
       "handsOnHead", "refuse", "laugh", "idea", "wide", "wave", "salute", "read", "worried", "walk", "run", "crawl",
       "lie", "fall", "sad", "cheer"]
TIMES = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.85, 1.0, 1.2, 1.5]


def main():
    out = Path(sys.argv[1]).resolve()
    rows = []
    for spec in sys.argv[2:] or [f"narrator:{a}" for a in ALL]:
        parts = spec.split(":")
        props = dict(kv.split("=") for kv in parts[2].split(",")) if len(parts) > 2 else {}
        rows.append([parts[0], parts[1], {"beats": [0.2, 0.7], "speed": 650 if parts[1] == "run" else 300}, props])
    page = f"""<!doctype html><html><head><meta charset="utf-8"><style>
body{{margin:0;background:#2A2B20;width:2400px}}
.row{{display:flex;align-items:flex-end;height:250px;border-bottom:1px solid #444;position:relative}}
.lab{{position:absolute;left:4px;top:2px;color:#ddd;font:14px sans-serif}}
svg{{width:200px;height:250px;overflow:visible}}</style>
<script>{(HERE / "puppet.js").read_text()}</script></head><body><div id="g"></div><script>
const rows={json.dumps(rows)}, ts={json.dumps(TIMES)}, G=document.getElementById("g");
for (const [cos, act, opt, props] of rows) {{
  const r=document.createElement("div"); r.className="row"; G.appendChild(r);
  const l=document.createElement("div"); l.className="lab"; l.textContent=cos+" / "+act; r.appendChild(l);
  for (const t of ts) {{
    const svg=document.createElementNS("http://www.w3.org/2000/svg","svg");
    svg.setAttribute("viewBox","-220 -560 440 600"); r.appendChild(svg);
    const pp=NerdPuppet.build(svg, cos, {{props}});
    const res=NerdPuppet.poseAt([{{t:0, act, opt}}], t); NerdPuppet.apply(pp, res.P, res.ground);
  }}
}}</script></body></html>"""
    with tempfile.TemporaryDirectory() as d:
        html = Path(d) / "sheet.html"
        html.write_text(page)
        subprocess.run([CHROME, "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
                        f"--window-size=2400,{250 * len(rows) + 10}", f"--screenshot={out}", html.as_uri()],
                       check=True, capture_output=True)
    print(out)


if __name__ == "__main__":
    main()
