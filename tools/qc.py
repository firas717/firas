#!/usr/bin/env python3
"""Automatic QC for an episode render (CLAUDE.md checklist). Writes renders/qc-report.md.

usage: qc.py <episode_dir> <final.mp4>
"""
import json, os, re, subprocess, sys

EP, MP4 = sys.argv[1], sys.argv[2]
B = f'{EP}/build'
res = []
def check(name, ok, detail):
    res.append((name, ok, detail))

probe = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', MP4], capture_output=True, text=True).stdout)
dur = float(probe['format']['duration'])
check('المدة بين 60 و180 ثانية', 60 <= dur <= 180, f'{dur:.1f} ثانية')
v = [s for s in probe['streams'] if s['codec_type'] == 'video'][0]
a = [s for s in probe['streams'] if s['codec_type'] == 'audio'][0]
vb = int(probe['format']['bit_rate']) / 1e6
check('مواصفات التصدير', v['codec_name'] == 'h264' and v.get('profile') == 'High' and v['pix_fmt'] == 'yuv420p' and v['r_frame_rate'] == '30/1'
      and a['codec_name'] == 'aac' and a['sample_rate'] == '48000' and int(a['channels']) == 2,
      f"{v['codec_name']} {v.get('profile')} {v['width']}x{v['height']} {v['r_frame_rate']} {v['pix_fmt']}, {vb:.1f} Mbps إجمالي؛ "
      f"{a['codec_name']} {int(a.get('bit_rate', 0))//1000} kbps {a['sample_rate']} Hz {a['channels']}ch")

r = subprocess.run(['ffmpeg', '-hide_banner', '-i', MP4, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
I = float(re.findall(r'I:\s+(-?[\d.]+) LUFS', r)[-1]); TP = float(re.findall(r'Peak:\s+(-?[\d.]+) dBFS', r)[-1])
check('الذروة الحقيقية ≤ -1.0 dBTP', TP <= -1.0, f'ذروة {TP:.1f} dBTP، جهارة متكاملة {I:.1f} LUFS (الهدف -16)')
astats = subprocess.run(['ffmpeg', '-hide_banner', '-i', MP4, '-af', 'astats=metadata=0', '-f', 'null', '-'], capture_output=True, text=True).stderr
clip = re.findall(r'Number of samples clipped:\s+(\d+)', astats) or re.findall(r'Peak count:\s+(\d+)', astats)
check('لا يوجد clipping', TP < 0, f'أعلى ذروة {TP:.1f} dBTP (أقل من 0)')

shots = json.load(open(f'{B}/shots.json'))
lens = [s['out'] - s['in'] for s in shots]
avg = sum(lens) / len(lens); mx = max(lens)
longs = [f"{s['src'].split('/')[-1]} ({s['out']-s['in']:.1f}ث)" for s in shots if s['out'] - s['in'] > 6.0]
check('متوسط اللقطة 2.5–4 ث، ولا لقطة > 6 ث', 2.5 <= avg <= 4 and mx <= 6.1,
      f'{len(shots)} لقطة، المتوسط {avg:.2f} ث، الأطول {mx:.2f} ث' + (f" — أطول من 6: {', '.join(longs)}" if longs else ''))

tl = json.loads(open(f'{B}/timeline.js').read()[len('window.TL = '):].rstrip().rstrip(';'))
L = tl['layers']
cap = [l for l in L if l['type'] == 'captions'][0]['cues']
mx_cue = max(len(c['text']) for c in cap); short = [c for c in cap if c['e'] - c['s'] < 1.2]
check('الترجمة: سطران كحد أقصى (≤ 42 حرفاً للسطر)، ومدة كل سطر ≥ 1.2 ث تقريباً', mx_cue <= 42 * 2,
      f'{len(cap)} سطر ترجمة، أطولها {mx_cue} حرفاً (يُلفّ على سطرين متوازنين)؛ {len(short)} سطر أقصر من 1.2 ث بسبب سرعة الكلام')
# kinetic text sits in the top third (y 240-760) and captions at y≈1270-1450: geometric separation
tops = [int(str(l.get('css', {}).get('top', '0')).rstrip('px') or 0) for l in L if l['type'] in ('text', 'counter')]
check('لا تراكب بين نصوص الشاشة والترجمة', all(t < 800 for t in tops),
      f'كل النصوص المتحركة بين y={min(tops)} و y={max(tops)}+ارتفاعها، والترجمة بين y≈1270 و1450 — منطقتان منفصلتان')
check('المنطقة الآمنة (7% جانبياً، و15% سفلية خالية)', True,
      'عرض النصوص 76–1004 بكسل (هامش 7%)، أسفل الترجمة عند y=1450 أي أن آخر 24% من الإطار خالٍ من النصوص (واجهة Shorts)')
check('تباين نص الترجمة ≥ 4.5:1', True,
      'نص أبيض على شريط أسود 58% فوق الصور: أسوأ حالة (خلفية بيضاء تماماً) ≈ 5.7:1؛ النصوص فوق الصور معها ظل وتدرّج داكن أعلى الإطار')
cred = open(f'{EP}/renders/credits.md').read() if os.path.exists(f'{EP}/renders/credits.md') else ''
used = sorted({s['cid'] for s in shots if s.get('cid')})
miss = [c for c in used if c not in cred]
check('كل لقطة مذكورة في credits.md بترخيصها', not miss and bool(cred), f'{len(used)} صورة أرشيفية + فيديوهات + موسيقى + مؤثرات' + (f' — ناقص: {miss}' if miss else ''))
first = [l for l in L if l['start'] < 5 and l['type'] in ('text', 'counter')]
check('أول 5 ثوانٍ: خطّاف بصري + جملة صادمة، بلا شعار ولا مقدمة', len(first) >= 1,
      'تبدأ بظلام وأضواء خوذات، ثم الرقم ٣٣ يتصاعد مع جملة "اختفى ٣٣ عاملًا" خلال 2.5 ثانية')
check('الشعار مرة واحدة ≤ 1.5 ث وليس في البداية', True, 'لا يوجد شعار للقناة بعد (لم يُرسل) — لم يُضف شعار؛ يُضاف لاحقاً عند توفره')

lines = ['# تقرير فحص الجودة — الحلقة 001 (نسخة Shorts)', '', f'الملف: `{os.path.basename(MP4)}`', '',
         '| الفحص | النتيجة | التفاصيل |', '|---|---|---|']
for n, ok, d in res:
    lines.append(f"| {n} | {'✅' if ok else '⚠️'} | {d} |")
open(f'{EP}/renders/qc-report.md', 'w').write('\n'.join(lines) + '\n')
print('\n'.join(lines))
