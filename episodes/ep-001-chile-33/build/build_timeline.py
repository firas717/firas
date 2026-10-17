#!/usr/bin/env python3
"""Episode 001 — 69 days underground. Builds build/timeline.js (render engine), build/timeline.json
(CLAUDE.md summary format) and build/audio_plan.json (mixer) from the word-aligned voice.

All times are seconds on the final video timeline (= cut voice timeline).
"""
import json, os, re
from PIL import Image

EP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(EP, 'build')
ROOT = os.path.dirname(os.path.dirname(EP))
F = lambda p: 'file://' + p

words = json.load(open(f'{B}/transcript/aligned.json'))
spoken = json.load(open(f'{B}/transcript/spoken.json'))
VOICE_END = json.load(open(f'{B}/transcript/cut.json'))['duration']
DUR = 146.4
MODE_SWITCH = 109.0

def norm(t):
    t = re.sub(r'[ً-ْٰـ]', '', t)
    return re.sub(r'[^ء-ي ]', '', t).strip()

def T(scene, phrase, which='s', nth=0):
    """time of a phrase (in 'say' spelling) inside a scene"""
    ws = [w for w in words if w['scene'] == scene]
    toks = norm(phrase).split()
    hits = []
    for i in range(len(ws) - len(toks) + 1):
        if all(ws[i + j]['w'] == toks[j] for j in range(len(toks))):
            hits.append((ws[i], ws[i + len(toks) - 1]))
    if not hits:
        raise KeyError(f'{scene}:{phrase}')
    a, b = hits[nth]
    return a['s'] if which == 's' else b['e']

# ---------------------------------------------------------------- assets
COM = f'{EP}/footage/commons'
THUMB = f'{B}/commons/thumbs'
_size = {}
def img(cid):
    p = f'{COM}/{cid}.jpg'
    try:
        if p not in _size:
            _size[p] = Image.open(p).size
    except Exception:                    # missing or partial download: fall back to the 500px thumbnail (flagged in QC)
        p = f'{THUMB}/{cid}.jpg'
        _size[p] = Image.open(p).size
    w, h = _size[p]
    return p, w, h

layers, shots = [], []
def add(**L):
    layers.append(L); return L

def photo(cid, a, b, layout='full', focus=(0.5, 0.5), kb=None, card=None, tin=None, tout=None, note=None):
    p, w, h = img(cid)
    grade = 'night' if a < MODE_SWITCH else 'day'
    kb = kb or {'from': [1.0, 0, 0], 'to': [1.07, 0, 0]}
    L = add(type='media', start=a, end=b, z=1, layout=layout, src=F(p), iw=w, ih=h, focus=list(focus),
            kb=kb, grade=grade, blurSrc=F(f'{THUMB}/{cid}.jpg'), card=card or {'w': 960, 'cy': 820},
            **({'in': tin} if tin else {}), **({'out': tout} if tout else {}))
    shots.append({'src': f'footage/commons/{cid}.jpg', 'cid': cid, 'in': round(a, 2), 'out': round(b, 2),
                  'motion': 'kenburns', 'grade': grade, 'layout': layout})
    return L

def video(name, a, b, kb=None, tin=None, src=None, speed=1.0):
    d = f'{B}/frames/{name}'
    n = len([f for f in os.listdir(d) if f.endswith('.jpg')])
    grade = 'night' if a < MODE_SWITCH else 'day'
    L = add(type='media', start=a, end=b, z=1, layout='full', kind='seq', seq={'dir': F(d), 'count': n, 'fps': 30, 'speed': speed},
            iw=1080, ih=1920, focus=[0.5, 0.5], kb=kb or {'from': [1.0, 0, 0], 'to': [1.04, 0, 0]}, grade=grade,
            **({'in': tin} if tin else {}))
    shots.append({'src': src or f'build/frames/{name}', 'in': round(a, 2), 'out': round(b, 2), 'motion': 'video', 'grade': grade, 'layout': 'full'})
    return L

def gfx(name, a, b, params, bg=None, z=2):
    if bg:
        add(type='bg', start=a, end=b, z=0, src=F(f'{ROOT}/brand/templates/backgrounds/{bg}'), from_=[0, 0], to=[0, -90], opacity=0.9)
    L = add(type='graphic', name=name, start=a, end=b, z=z, params=params)
    shots.append({'src': f'graphic:{name}', 'in': round(a, 2), 'out': round(b, 2), 'motion': 'motion-graphic', 'grade': 'none', 'layout': 'graphic'})
    return L

ON_PHOTO = {'color': '#F2EFE9', 'textShadow': '0 4px 22px rgba(0,0,0,.75), 0 1px 3px rgba(0,0,0,.6)'}
def text(html, a, b, style='keyword', top=330, anim='up', css=None, z=6, move=None):
    c = {'top': f'{top}px', **ON_PHOTO, **(css or {})}
    return add(type='text', html=html, start=a, end=b, z=z, style=style, anim=anim, css=c, **({'move': move} if move else {}))

def counter(a, b, frm, to, count_start, count_dur, unit=None, top=300, css=None, prefix='', suffix=''):
    c = {'top': f'{top}px', **ON_PHOTO, **(css or {})}
    if unit and 'span' not in unit:
        unit = f'<span style="color:rgba(242,239,233,.92)">{unit}</span>'
    return add(type='counter', start=a, end=b, z=6, style='stat', **{'from': frm}, to=to, countStart=count_start,
               countDur=count_dur, unit=unit, css=c, prefix=prefix, suffix=suffix)

sfx, music = [], []
def S(name, at, gain, **kw):
    sfx.append({'name': name, 'at': round(at, 3), 'gain': gain, **kw})

# ================================================================ SCENE 1 — hook (0 → 17.95)
s1_zoom = 3.95
video('headlamps', 0.0, s1_zoom, kb={'from': [1.02, 0, 0], 'to': [1.10, 0, -20]}, src='footage/inbox/2894897-hd_1920_1080_24fps.mp4 (2.6-6.9s)')
add(type='overlay', start=0, end=s1_zoom, z=3, cls='topscrim')
text('<span class="muted" style="color:#E9A13B">٢٠١٠</span>', T(1, 'ألفين') - 0.05, s1_zoom - 0.05, style='label', top=240, css={'fontSize': '64px'})
counter(T(1, 'ثلاثة') - 0.15, s1_zoom - 0.02, 1, 33, T(1, 'ثلاثة'), 0.8, unit='عاملًا', top=640,
        css={'color': '#E9A13B'})
S('impact_low', T(1, 'ثلاثة'), -14)
S('gravel', 1.2, -26, dur=2.6)
# satellite zoom (100 frames = 3.33 s) — NASA GIBS + EO-1
zoom_end = s1_zoom + 100 / 30
video('mapzoom', s1_zoom, zoom_end, kb={'from': [1, 0, 0], 'to': [1, 0, 0]}, src='NASA GIBS Blue Marble/MODIS + EO-1 ALI (build/frames/mapzoom)')
add(type='overlay', start=s1_zoom, end=zoom_end, z=3, cls='vignette')
text('تشيلي', T(1, 'تشيلي') - 0.05, zoom_end - 1.0, style='keyword', top=300)
add(type='graphic', name='mapPin', start=zoom_end - 0.95, end=zoom_end + 0.02, z=5,
    params={'x': 540, 'y': 960, 'tDot': 0.0, 'tLabel': 0.15, 'label': 'منجم سان خوسيه', 'sub': 'تشيلي · ٢٠١٠', 'labelY': -230})
S('whoosh_soft', s1_zoom - 0.25, -18)
S('wind', s1_zoom, -24, dur=3.6, fade=1.0)
S('rumble', T(1, 'انهيار'), -18, dur=2.2)
# depth cross-section
d1a, d1b = zoom_end, 13.02
gfx('depthSection', d1a, d1b, {'surfaceY': 560, 'depthPx': 600, 'tLine': [T(1, 'مئات') - d1a - 0.3, T(1, 'الأرض') - d1a + 0.2],
                               'tLabel': T(1, 'الأرض') - d1a + 0.15, 'label': '٧٠٠ متر تحت الأرض',
                               'question': True, 'tQuestion': T(1, 'ولم يكن') - d1a + 0.6, 'compare': False})
S('whoosh_down', T(1, 'مئات') - 0.3, -20)
# title / teaser
t1a, t1b = d1b, 17.98
photo('c273', t1a, t1b, 'full', focus=(0.47, 0.42), kb={'from': [1.0, 0, 0], 'to': [1.09, 0, 0]})
add(type='graphic', name='titleCard', start=T(1, 'تحول') - 0.05, end=T(1, 'تحول') + 2.45, z=6,
    params={'title': '٦٩ يومًا تحت الأرض', 'accent': '٦٩', 'y': 470, 'onPhoto': True})
S('riser', t1a + 0.1, -22, dur=T(1, 'تحول') - t1a - 0.1)
S('impact_mid', T(1, 'تحول') - 0.02, -15)

# ================================================================ SCENE 2 — collapse (17.98 → 35.30)
s2a, g2a = 17.98, 19.80
photo('c287', s2a, g2a, 'framed', focus=(0.5, 0.5), card={'w': 960, 'cy': 860}, kb={'from': [1.0, 0, 0], 'to': [1.06, 0, 0]})
text('٥ أغسطس ٢٠١٠', T(2, 'الخامس') - 0.12, g2a - 0.02, style='date', top=300,
     move={'at': T(2, 'أغسطس') + 0.45, 'dur': 0.45, 'to': [300, -110, 0.55]})
S('pop', T(2, 'الخامس') - 0.12, -20)
g2b = 25.85
gfx('mineSpiral', g2a, g2b, {'tDraw': [0, 0.9], 'tCollapse': T(2, 'منجم') - g2a - 0.05, 'tCut': T(2, 'انقطعت') - g2a,
                             'tTrapped': T(2, 'وأصبح') - g2a + 0.1,
                             'labels': {'portal': 'المدخل', 'collapse': 'الانهيار', 'refuge': 'الملجأ', 'trapped': '٣٣ عاملًا محاصرون'}})
# the collapse ends (0.4 s fade) when 'خوسيه' ends, so the 0.36 s before the reveal word 'انقطعت' is real silence
S('collapse', T(2, 'منجم') - 0.1, -12, dur=round(T(2, 'سان خوسيه', 'e') - T(2, 'منجم') + 0.1, 3), fade=0.4)
S('hit', T(2, 'انقطعت'), -16)
photo('c072', g2b, 28.62, 'full', focus=(0.62, 0.5), kb={'from': [1.0, 0, 0], 'to': [1.07, -30, 0]})
photo('c073', 28.62, 31.40, 'full', focus=(0.55, 0.45), kb={'from': [1.06, 0, 0], 'to': [1.0, 0, 0]})
S('drill', g2b, -24, dur=5.5, fade=1.0)
photo('c077', 31.40, 35.30, 'framed', focus=(0.5, 0.5), card={'w': 960, 'cy': 860})
text('لا أحد يعرف<br><span class="acc">إن كانوا أحياء</span>', T(2, 'ولا') - 0.05, 35.15, style='keyword', top=250, css={'fontSize': '104px'})

# ================================================================ SCENE 3 — the note (35.30 → 52.75)
fc = [35.30, 36.55, 37.80, 39.00]
photo('c135', fc[0], fc[1], 'full', focus=(0.5, 0.5), kb={'from': [1.04, 0, 0], 'to': [1.10, 0, 0]})
photo('c079', fc[1], fc[2], 'full', focus=(0.45, 0.55), kb={'from': [1.10, 0, 0], 'to': [1.04, 0, 0]})
photo('c075', fc[2], fc[3], 'full', focus=(0.5, 0.55), kb={'from': [1.04, 0, 0], 'to': [1.10, 0, 0]})
counter(T(3, 'مرت') - 0.1, fc[3] - 0.02, 1, 17, T(3, 'سبعة') - 0.1, 2.2, unit='يومًا بلا خبر', top=300)
for t in fc[1:3]:
    S('shutter', t, -20)
S('tick', T(3, 'سبعة') - 0.1, -24, dur=2.3)
n0 = 43.98
photo('c080', fc[3], n0, 'full', focus=(0.5, 0.45), kb={'from': [1.0, 0, 30], 'to': [1.12, 0, -10]}, tout={'type': 'fade', 'dur': 0.3})
S('whoosh_up', T(3, 'وعاد') - 0.2, -22)
# 0.5 s of silence before the reveal (voice pause) — dip to black
n1 = T(3, 'رسالة') - 0.02
add(type='bg', start=n0, end=n1, z=0, color='#000')
n2 = 48.45
gfx('noteReveal', n1, n2, {'paperSrc': F(f'{ROOT}/brand/templates/backgrounds/paper.png'), 'noteSrc': F(f'{THUMB}/c149.jpg'),
                           'tCard': 0, 'tWrite': 0.3, 'tHighlight': T(3, 'تقول') - n1, 'tTranslate': T(3, 'بخير') - n1 + 0.1,
                           'translation': '«نحن الـ٣٣ بخير في الملجأ»', 'source': 'نص رسالة العمال · ٢٢ أغسطس ٢٠١٠'})
S('impact_big', n1, -12, dur=0.9)                  # short tail: gone before 'العمال' in the reveal line
S('paper', n1 + 0.15, -18)
photo('c285', n2, 50.72, 'framed', focus=(0.5, 0.5), card={'w': 980, 'cy': 860}, kb={'from': [1.0, 0, 0], 'to': [1.12, 0, -40]})
text('الرسالة الأصلية بيد الرئيس التشيلي', n2 + 0.25, 50.6, style='label', top=330, css={'fontSize': '52px'})
photo('c289', 50.72, 52.75, 'framed', focus=(0.5, 0.5), card={'w': 980, 'cy': 860})
text('<span class="acc">أحياء</span>', T(3, 'كان العمال') - 0.05, 52.6, style='title', top=300, anim='pop')
S('impact_mid', T(3, 'كان العمال') - 0.05, -15)

# ================================================================ SCENE 4 — the second problem (52.75 → 74.75)
photo('c138', 52.75, 56.22, 'full', focus=(0.5, 0.5), kb={'from': [1.0, 0, 0], 'to': [1.06, 0, 20]})
d2a, d2b = 56.22, 62.05
gfx('depthSection', d2a, d2b, {'surfaceY': 520, 'depthPx': 620, 'tLine': [0.1, 1.0], 'tLabel': T(4, 'سبعمئة') - d2a,
                               'label': '٧٠٠ متر تحت الأرض', 'question': False, 'compare': True, 'tCompare': T(4, 'وكان') - d2a})
S('whoosh_down', d2a + 0.05, -20)
h2a, h2b = d2b, 66.18
gfx('holeCompare', h2a, h2b, {'tWalls': 0.2, 'tPerson': T(4, 'رفع') - h2a, 'tDims': T(4, 'فتحة') - h2a,
                              'shaftLabel': 'قطر الممر', 'shaftValue': '٧١ سم', 'personValue': '١٧٥ سم'})
S('thud', h2a + 0.2, -18)
S('hit', T(4, 'فتحة'), -18)
photo('c043', h2b, 69.40, 'framed', focus=(0.5, 0.5), card={'w': 960, 'cy': 860})
text('أنبوب الإمداد', h2b + 0.2, 69.3, style='label', top=330, css={'fontSize': '56px'})
video('packing', 69.40, 71.42, src='footage/inbox/6686925-hd_1920_1080_25fps.mp4 (1.0-3.4s)')
for i, (w, k) in enumerate([('الطعام', 'الطعام'), ('الماء', 'والماء'), ('الدواء', 'والأدوية')]):
    text(w, T(4, k) - 0.05, 71.38, style='keyword', top=300 + i * 150, css={'fontSize': '110px'})
    S('pop', T(4, k) - 0.05, -20)
photo('c303', 71.42, 74.75, 'full', focus=(0.5, 0.5), kb={'from': [1.0, 0, 0], 'to': [1.08, 0, 0]})

# ================================================================ SCENE 5 — the capsule (74.75 → 96.70)
video('weld_pipe', 74.75, 77.88, src='footage/inbox/11800598-hd_1920_1080_30fps.mp4 (2.0-5.4s)')
text('حل هندسي', T(5, 'حل') - 0.05, 77.8, style='keyword', top=320)
photo('c330', 77.88, 82.45, 'framed', focus=(0.5, 0.45), card={'w': 960, 'cy': 860}, kb={'from': [1.0, 0, 30], 'to': [1.08, 0, -20]})
text('فينيكس <span class="latin" style="font-family:\'Plex Sans\';direction:ltr;unicode-bidi:isolate;color:#9AA3B0">Fénix 2</span>',
     T(5, 'فينيكس') - 0.08, 82.35, style='keyword', top=300)
S('clang', T(5, 'فينيكس') - 0.05, -16)
c5a, c5b = 82.45, 87.18
gfx('capsuleSchematic', c5a, c5b, {'tDraw': [0, 1.0], 'tFill': 0.8, 'tDims': 1.9, 'heightLabel': 'نحو ٤ أمتار', 'diameterLabel': '٥٤ سم', 'name': None})
S('whoosh_up', c5a, -22)
video('weld_rebar', 87.18, 90.28, src='footage/inbox/17034343_1920_1080_30fps.mp4 (1.5-4.9s)')
photo('c361', 90.28, 93.00, 'framed', focus=(0.5, 0.5), card={'w': 960, 'cy': 860})
text('ناسا', T(5, 'ناسا') - 0.05, 92.95, style='title', top=290, anim='pop')
text('مهندسو ناسا الذين ساعدوا في التصميم', T(5, 'ناسا') + 0.3, 92.95, style='label', top=520, css={'fontSize': '46px'})
S('impact_mid', T(5, 'ناسا') - 0.05, -17)
photo('c092', 93.00, 96.70, 'full', focus=(0.5, 0.5), kb={'from': [1.0, 0, 0], 'to': [1.08, 0, 0]})
text('اختبار الكبسولة عند فوهة المنجم', 93.2, 96.55, style='label', top=320, css={'fontSize': '52px'})

# ================================================================ SCENE 6 — the rescue (96.70 → 119.40)
photo('c007', 96.70, 100.70, 'full', focus=(0.35, 0.5), kb={'from': [1.0, 0, 0], 'to': [1.07, 0, 0]})
text('١٣ أكتوبر ٢٠١٠', T(6, 'الثالث') - 0.1, 100.6, style='date', top=300,
     move={'at': T(6, 'أكتوبر') + 0.5, 'dur': 0.45, 'to': [300, -110, 0.55]})
S('pop', T(6, 'الثالث') - 0.1, -20)
S('winch', 99.0, -24, dur=9.0, fade=1.5)
photo('c251', 100.70, 103.00, 'full', focus=(0.5, 0.42), kb={'from': [1.08, 0, 0], 'to': [1.0, 0, 0]})
photo('c177', 103.00, 105.45, 'full', focus=(0.5, 0.45), kb={'from': [1.0, 0, 40], 'to': [1.07, 0, -20]})
photo('c234', 105.45, 107.10, 'full', focus=(0.5, 0.4))
photo('c217', 107.10, 109.00, 'full', focus=(0.5, 0.45), kb={'from': [1.0, 0, 0], 'to': [1.05, 0, 0]})
S('crowd_murmur', 105.4, -28, dur=3.4, fade=0.8)
# 0.45 s silence then wash (night -> day)
add(type='flash', start=MODE_SWITCH - 0.20, end=MODE_SWITCH + 0.20, z=9, color='#ffffff')
S('impact_big', MODE_SWITCH, -13)
S('cheer', MODE_SWITCH, -18, dur=9.5, fade=2.0, ramp=[-24, -14])
photo('c178', MODE_SWITCH, 112.42, 'full', focus=(0.45, 0.45), kb={'from': [1.0, 0, 0], 'to': [1.08, 0, 0]})
text('عاد الأول', MODE_SWITCH + 0.3, 112.3, style='keyword', top=300)
text('فلورنسيو أفالوس', MODE_SWITCH + 0.75, 112.3, style='label', top=450, css={'fontSize': '54px', 'color': '#E9A13B'})
rapid = ['c298', 'c281', 'c053', 'c153', 'c144']
rt = [112.42 + 1.2 * i for i in range(len(rapid) + 1)]
foc = {'c298': (0.5, 0.45), 'c281': (0.5, 0.45), 'c053': (0.5, 0.42), 'c153': (0.5, 0.5), 'c144': (0.45, 0.45)}
for i, cid in enumerate(rapid):
    photo(cid, rt[i], rt[i + 1], 'full', focus=foc[cid], kb={'from': [1.04 if i % 2 else 1.0, 0, 0], 'to': [1.0 if i % 2 else 1.06, 0, 0]})
    S('shutter', rt[i], -18)
photo('c159', rt[-1], 119.40, 'full', focus=(0.5, 0.45), kb={'from': [1.0, 0, 0], 'to': [1.05, 0, 0]})
counter(T(6, 'وبعد') - 0.1, 119.30, 1, 33, T(6, 'وبعد'), 3.3, suffix=' / ٣٣', unit='بعد نحو ٢٢ ساعة', top=300, css={'fontSize': '230px'})
S('impact_big', T(6, 'وبعد') + 3.3, -13)

# ================================================================ SCENE 7 — ending (119.40 → end)
photo('c279', 119.40, 123.30, 'full', focus=(0.42, 0.42), kb={'from': [1.0, 0, 0], 'to': [1.07, 0, 0]})
add(type='graphic', name='lowerThird', start=T(7, 'قائد') - 0.1, end=123.25, z=6,
    params={'name': 'لويس أورسوا', 'title': 'قائد المناوبة — آخر من خرج', 'y': 1040})
S('whoosh_soft', T(7, 'قائد') - 0.1, -24)
tl_a, tl_b = 123.30, 128.68
gfx('timelineV', tl_a, tl_b, {'items': [{'date': '٥ أغسطس', 'label': 'الانهيار'}, {'date': '٢٢ أغسطس', 'label': 'الرسالة'},
                                         {'date': '١٣ أكتوبر', 'label': 'الإنقاذ'}],
                              'tItems': [0.3, 1.3, 2.3], 'total': '٦٩ يومًا', 'tTotal': T(7, 'تسعة') - tl_a})
for t in (0.3, 1.3, 2.3):
    S('pop', tl_a + t, -22)
S('impact_mid', T(7, 'تسعة'), -17)
photo('c074', 128.68, 131.25, 'full', focus=(0.5, 0.5), kb={'from': [1.0, 0, 0], 'to': [1.07, 0, 0]})
photo('c012', 131.25, 134.45, 'framed', focus=(0.5, 0.45), card={'w': 960, 'cy': 860})
team = [('فرق الإنقاذ', 'فرق الإنقاذ'), ('المهندسون', 'والمهندسين'), ('الأطباء', 'والأطباء')]
for i, (w, k) in enumerate(team):     # one word at a time, swapping on the spoken word
    end = T(7, team[i + 1][1]) - 0.06 if i + 1 < len(team) else 136.85
    text(w, T(7, k) - 0.05, end, style='keyword', top=300, css={'fontSize': '112px'}, anim='pop')
    S('pop', T(7, k) - 0.05, -22)
photo('c371', 134.45, 136.92, 'full', focus=(0.5, 0.5), kb={'from': [1.0, 0, 0], 'to': [1.06, 0, 0]})
photo('c081', 136.92, 139.30, 'full', focus=(0.45, 0.5), kb={'from': [1.0, 0, 0], 'to': [1.05, 0, 0]})
photo('c277', 139.30, 142.45, 'framed', focus=(0.5, 0.5), card={'w': 980, 'cy': 990})
counter(T(7, 'أحياء') - 0.08, 142.40, 33, 33, T(7, 'أحياء'), 0.1, suffix=' / ٣٣', unit='<span style="color:#E9A13B;font:700 120px/1.2 Readex Pro">أحياء</span>', top=200, css={'fontSize': '220px'})
add(type='media', start=142.45, end=DUR, z=1, layout='blur', src=F(img('c277')[0]), iw=img('c277')[1], ih=img('c277')[2],
    grade='day', blurSrc=F(f'{THUMB}/c277.jpg'))
add(type='graphic', name='endCard', start=142.45, end=DUR, z=6,
    params={'question': 'برأيك، ما الذي أبقى هؤلاء الرجال على قيد الحياة ١٧ يومًا بلا أي اتصال بالعالم؟', 'cta': 'تابعنا للمزيد', 'tQ': 0.2, 'tCta': 1.3})
S('pop', 142.65, -22)

# ---------------------------------------------------------------- captions (script wording, aligned timing)
NUMS = {'٢٠١٠': 2, '٣٣': 2, '١٧': 2, '٧٠٠': 1, '٢٢': 2, '٦٩': 2}
cues = []
for sc in spoken['scenes']:
    for si, sent in enumerate(sc['sentences']):
        ws = [w for w in words if w['scene'] == sc['id'] and w['sent'] == si]
        toks = sent['show'].split()
        spans, k = [], 0
        for tk in toks:
            digits = re.sub(r'[^٠-٩]', '', tk)
            n = NUMS.get(digits, 1) if digits else 1
            seg_ = ws[k:k + n] or ws[-1:]
            spans.append((seg_[0]['s'], seg_[-1]['e'])); k += n
        assert k == len(ws), (sc['id'], si, k, len(ws), sent['show'])
        # split into phrases at punctuation, then balance long phrases into cues of <= 40 chars,
        # never ending a cue on a particle/preposition or splitting a name or number+unit pair
        BAD_END = {'في', 'على', 'من', 'إلى', 'عن', 'بعد', 'قبل', 'تحت', 'فوق', 'عبر', 'مع', 'إن', 'أن', 'لا', 'ما', 'قد',
                   'كل', 'هو', 'لم', 'لكن', 'ثم', 'و', 'باسم', 'لويس', 'سان', 'بشأن', 'نحو', 'إليهم', 'يقارب', 'تُعرف', 'قائد', 'فرق', 'تعاون', 'الثلاثة', 'تصميم', 'عملية', 'خبراء', 'طرق'}
        phrases, cur = [], []
        for tk, sp in zip(toks, spans):
            cur.append((tk, sp))
            if re.search(r'[،,:؛.]$', tk):
                phrases.append(cur); cur = []
        if cur: phrases.append(cur)
        def L(seg): return len(' '.join(t for t, _ in seg))
        def best_split(seg):
            n = L(seg)
            if n <= 40: return [seg]
            k = -(-n // 38)
            best = None
            def rec(rest, parts, cost):
                nonlocal best
                if len(parts) == k - 1:
                    c = cost + (L(rest) - n / k) ** 2 + (400 if L(rest) > 40 else 0) + (300 if L(rest) < 12 else 0)
                    if best is None or c < best[0]: best = (c, parts + [rest])
                    return
                for i in range(1, len(rest)):
                    left = rest[:i]
                    if L(left) > 40: break
                    pen = (L(left) - n / k) ** 2 + (500 if left[-1][0].strip('،,.:؛') in BAD_END else 0) + (300 if L(left) < 12 else 0)
                    rec(rest[i:], parts + [left], cost + pen)
            rec(seg, [], 0)
            return best[1]
        # merge tiny phrases with their neighbour when the result still fits
        merged = []
        for ph in phrases:
            if merged and (L(ph) < 14 or L(merged[-1]) < 14) and L(merged[-1]) + 1 + L(ph) <= 40:
                merged[-1] = merged[-1] + ph
            else:
                merged.append(ph)
        for ph in merged:
            for part in best_split(ph):
                cues.append({'s': part[0][1][0], 'e': part[-1][1][1], 'text': ' '.join(t for t, _ in part)})
for i, c in enumerate(cues):
    c['s'] = round(max(0, c['s'] - 0.08), 3)
    nxt = cues[i + 1]['s'] - 0.08 if i + 1 < len(cues) else c['e'] + 0.6
    c['e'] = round(min(max(c['e'] + 0.30, c['s'] + 1.2), nxt - 0.02), 3)
    c['text'] = c['text'].rstrip('،,.:؛')
# soft top scrim wherever on-screen text sits over a full-bleed photo/video
for M in [L for L in layers if L['type'] == 'media' and L.get('layout') == 'full']:
    if any(T_['type'] in ('text', 'counter') and T_['start'] < M['end'] and T_['end'] > M['start'] for T_ in layers):
        add(type='overlay', start=M['start'], end=M['end'], z=3, cls='topscrim', opacity=0.85)
# band behind captions whenever a photo/video is on screen
band = [[L['start'], L['end']] for L in layers if L['type'] == 'media'] + [[MODE_SWITCH, DUR]]   # day mode: light graphics need the band too
add(type='captions', start=0, end=DUR, z=8, cues=cues, bandRanges=band)

# global finishing layers
add(type='overlay', start=0, end=DUR, z=7, cls='vignette', opacity=0.85)
add(type='grain', start=0, end=DUR, z=7, dir=F(f'{ROOT}/brand/templates/grain'), count=8, fps=12, opacity=0.05)

# fix key name for bg drift
for L in layers:
    if 'from_' in L: L['from'] = L.pop('from_')

# ---------------------------------------------------------------- music plan
music = [
    {'track': 'Metaphysik', 'file': 'build/music/tracks/Metaphysik.mp3', 'start': 2.0, 'offset': 0.0, 'end': 75.6, 'fade_in': 1.2, 'fade_out': 1.6, 'gain': 1.5},
    {'track': 'Eternal Hope', 'file': 'build/music/tracks/Eternal Hope.mp3', 'start': 74.4, 'offset': 76.0, 'end': 109.15, 'fade_in': 1.5, 'fade_out': 0.25, 'gain': 0},
    {'track': 'Thaxted', 'file': 'build/music/tracks/Thaxted.mp3', 'start': 108.95, 'offset': 25.0, 'end': 138.35, 'fade_in': 0.05, 'fade_out': 1.2, 'gain': 0},
    {'track': 'Thaxted (final chord)', 'file': 'build/music/tracks/Thaxted.mp3', 'start': T(7, 'أحياء') - 0.05, 'offset': 137.5, 'end': DUR, 'fade_in': 0.08, 'fade_out': 1.2, 'gain': 0},
]
# silences the music must respect (seconds): before the note, after the collapse, before the wash, the closing pause
music_dips = [[T(2, 'سان خوسيه', 'e'), T(2, 'انقطعت') - 0.02], [n0 - 0.05, n1 + 0.02], [MODE_SWITCH - 0.5, MODE_SWITCH - 0.02], [138.35, T(7, 'وفي') - 0.02]]

timeline = {'duration': DUR, 'fps': 30, 'modeSwitch': MODE_SWITCH, 'layers': layers}
open(f'{B}/timeline.js', 'w').write('window.TL = ' + json.dumps(timeline, ensure_ascii=False) + ';\n')
# voice: Sidon-restored (with context) + narrator chain keyed by the raw take + 2 word patches (tools/enh_sidon.py,
# tools/narrator.py --key, tools/patch_voice.py 81.68-81.90 34.45-34.68); music level chosen by the owner:
# a faint bed ~31 LU under the voice during speech (tools/mix_report.py), darker (low-pass 3 kHz, high-pass 100 Hz) with gentle 6 dB ducking
VOICE = 'build/voice-narrator.wav'   # derived voice lives in build/; audio/ holds only the owner's inputs
MIX = {'music_db': -24, 'music_lp': 3000, 'music_hp': 100, 'duck_db': 6}
json.dump({'voice': VOICE, 'mix': MIX, 'duration': DUR, 'voice_end': VOICE_END, 'music': music, 'music_dips': music_dips, 'sfx': sfx},
          open(f'{B}/audio_plan.json', 'w'), ensure_ascii=False, indent=1)

# CLAUDE.md summary timeline
scenes_b = [0, 17.98, 35.30, 52.75, 74.75, 96.70, 119.40, DUR]
summary = {'episode': 'ep-001', 'title': '69 يومًا تحت الأرض — قصة الـ33', 'mode': 'night', 'mode_switch_at': MODE_SWITCH,
           'category': 'history', 'fps': 30, 'resolution': [1080, 1920], 'format': 'youtube-short', 'scenes': []}
for i in range(7):
    a, b = scenes_b[i], scenes_b[i + 1]
    summary['scenes'].append({
        'id': i + 1, 'audio': VOICE, 'start': a, 'end': b,
        'shots': [s for s in shots if a - 1e-6 <= s['in'] < b - 1e-6],
        'titles': [{'text': re.sub('<[^>]+>', '', L.get('html', '') or str(L.get('to', ''))), 'at': L['start'], 'dur': round(L['end'] - L['start'], 2), 'style': L.get('style')}
                   for L in layers if L['type'] in ('text', 'counter') and a <= L['start'] < b],
        'sfx': [x for x in sfx if a <= x['at'] < b],
        'transition_out': 'wash' if i == 4 else ('dip' if False else 'cut'),
    })
json.dump(summary, open(f'{B}/timeline.json', 'w'), ensure_ascii=False, indent=1)
json.dump(shots, open(f'{B}/shots.json', 'w'), ensure_ascii=False, indent=1)
lens = [s['out'] - s['in'] for s in shots]
print(f'layers={len(layers)} shots={len(shots)} avg={sum(lens)/len(lens):.2f}s max={max(lens):.2f}s cues={len(cues)} sfx={len(sfx)}')
for s in shots:
    if s['out'] - s['in'] > 6.0: print('  long shot:', s)
