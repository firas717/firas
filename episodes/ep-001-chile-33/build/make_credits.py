#!/usr/bin/env python3
"""Write renders/credits.md from shots.json + the Commons metadata + fixed sources (music, NASA, stock, SFX)."""
import json, os
EP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = f'{EP}/build'
shots = json.load(open(f'{B}/shots.json'))
cred = json.load(open(f'{B}/credits_commons.json'))
used = []
for s in shots:
    if s.get('cid') and s['cid'] not in used:
        used.append(s['cid'])
extra = ['c149']  # handwriting of the note (vector redraw), used inside the note graphic

def fmt_time(t):
    return f'{int(t // 60)}:{t % 60:04.1f}'

L = ['# المصادر والتراخيص — الحلقة 001: «69 يومًا تحت الأرض» (نسخة Shorts)', '',
     '> كل لقطة في الفيديو مذكورة هنا مع مصدرها ورخصتها. الصور الرسمية للحكومة التشيلية منشورة برخصة CC BY 2.0 (يجب ذكر المصدر).', '',
     '## نص جاهز للصقه في وصف الفيديو', '', '```',
     'الصور: Gobierno de Chile / Secretaría de Comunicaciones — Hugo Infante وآخرون (CC BY 2.0) عبر Wikimedia Commons',
     'صور الأقمار الصناعية: NASA Earth Observatory (EO-1 ALI)، NASA GIBS / Worldview (Blue Marble، MODIS Terra) — ملكية عامة',
     'Music: "Metaphysik", "Eternal Hope", "Thaxted" — Kevin MacLeod (incompetech.com)',
     'Licensed under Creative Commons: By Attribution 4.0 License — http://creativecommons.org/licenses/by/4.0/',
     'لقطات فيديو عامة: Pexels (Pexels License)',
     'مؤثرات صوتية: Wikimedia Commons (CC0 / ملكية عامة) + مكتبة القناة',
     '```', '',
     '## الصور الأرشيفية (Wikimedia Commons)', '',
     '| # | الظهور في الفيديو | الملف | المصوّر/المصدر | الرخصة | التاريخ |', '|---|---|---|---|---|---|']
for i, cid in enumerate(used + extra, 1):
    c = cred.get(cid) or {}
    times = ', '.join(f"{fmt_time(s['in'])}–{fmt_time(s['out'])}" for s in shots if s.get('cid') == cid) or 'داخل رسم «الرسالة»'
    page = c.get('page') or ''
    L.append(f"| {i} | {times} | [{c.get('file', cid)[5:]}]({page}) `{cid}` | {c.get('artist', '')[:60]} | {c.get('license', '')} | {c.get('date', '')[:10]} |")
L += ['', '## صور الأقمار الصناعية والخرائط', '',
      '| الظهور | المصدر | الرخصة |', '|---|---|---|',
      '| 0:04–0:07 (الطيران من الفضاء) | NASA GIBS: Blue Marble Next Generation (NASA Earth Observatory) | ملكية عامة (NASA) |',
      '| 0:04–0:07 | NASA GIBS: MODIS Terra Corrected Reflectance، 16 سبتمبر 2010 | ملكية عامة (NASA) |',
      '| 0:05–0:07 | NASA Earth Observatory — EO-1 ALI، منجم سان خوسيه 16 سبتمبر 2010 (Jesse Allen & Robert Simmon) — https://earthobservatory.nasa.gov/images/46018 | ملكية عامة (NASA) |',
      '', '## لقطات فيديو عامة (أرسلها المالك — Pexels)', '',
      '| الظهور | الملف | الرخصة |', '|---|---|---|']
for s in shots:
    if s['motion'] == 'video' and 'inbox' in s['src']:
        L.append(f"| {fmt_time(s['in'])}–{fmt_time(s['out'])} | {s['src']} | Pexels License (رقم المقطع في اسم الملف) |")
L += ['', '## الرسوم المتحركة', '', 'كل الرسوم (مقطع العمق، مخطط المنجم، الكبسولة، الممر، الخط الزمني، البطاقات) مرسومة بالبرمجة لهذه الحلقة — لا صور مولّدة بالذكاء الاصطناعي.',
      'الخلفيات (الخطوط الطبوغرافية، الورق) أُعيد رسمها بالبرمجة بناءً على مراجع المالك.', '',
      '## الموسيقى', '', '| الظهور | المقطوعة | المؤلف | الرخصة |', '|---|---|---|---|',
      '| 0:02–1:15 | Metaphysik | Kevin MacLeod (incompetech.com) | CC BY 4.0 |',
      '| 1:14–1:49 | Eternal Hope | Kevin MacLeod (incompetech.com) | CC BY 4.0 |',
      '| 1:49–2:18 و 2:21–النهاية | Thaxted (Holst، توزيع Kevin MacLeod) | Kevin MacLeod (incompetech.com) | CC BY 4.0 |',
      '', '## المؤثرات الصوتية', '', '| المؤثر | المصدر | الرخصة |', '|---|---|---|',
      '| رياح | Wikimedia Commons: Howling wind.ogg (Tvabutzku1234) | CC0 |',
      '| تصفيق وهتاف | Wikimedia Commons: Slow starting applause.ogg (stephan)، Applause i.ogg (thore) | ملكية عامة |',
      '| ورق | Wikimedia Commons: Food wrapper crumpling.ogg (stilgar) | ملكية عامة |',
      '| ضربات، ووش، نقرات، رعد، ومضات كاميرا، رايزر | مكتبة المؤثرات التي أرسلها المالك (المجموعات A–M) | ⚠️ يؤكد المالك مصدرها |',
      '', '## الخطوط', '', 'Readex Pro، IBM Plex Sans Arabic، IBM Plex Sans — Google Fonts (SIL Open Font License 1.1).', '',
      '## معلومات القصة (مراجع للتحقق)', '',
      '- Wikipedia: 2010 Copiapó mining accident؛ Fénix capsules (قطر الكبسولة 54 سم، طولها 3.98 م وفق ويكيبيديا الإسبانية، قطر ممر الخطة B = 71 سم، الرسالة وصلت يوم 22 أغسطس من عمق 688 م).',
      '- السكربت الأصلي ذكر «قطر 66 سم» — صُحّح إلى 71 سم حسب المصدر.']
open(f'{EP}/renders/credits.md', 'w').write('\n'.join(L) + '\n')
print(len(used), 'photos credited')
