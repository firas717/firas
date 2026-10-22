#!/usr/bin/env python3
"""Episode: Operation Mincemeat (عملية اللحم المفروم) — shot list for scripts/nerd/engine.py.

Run from the repo root:
  python3 videos/2026-10-22-operation-mincemeat/build.py work/2026-10-22-operation-mincemeat/edit
Times are seconds on voice_final.wav (captions.json word timings).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "nerd"))
from engine import Video  # noqa: E402

EDIT = Path(sys.argv[1] if len(sys.argv) > 1 else "work/2026-10-22-operation-mincemeat/edit")
V = Video(EDIT, duration=164.2, topic="war", title="كيف خدعت جثة\nجيش هتلر؟", voice_end=162.64)
V.audio("assets/audio/mix.wav")
V.use_map("assets/map.svg")
V.set_words(json.loads((Path(__file__).parent / "words_corrected.json").read_text()))
V.set_captions(json.loads((EDIT / "captions.json").read_text()), keywords=[(40.5, "خدعة"), (160.5, "حقيقية")])

P = V.map_proj
LONDON, HUELVA, SICILY, SARDINIA, GREECE, BERLIN, TUNIS, SPAIN = (
    (-0.12, 51.5), (-6.95, 37.26), (14.1, 37.6), (9.0, 40.1), (22.0, 39.3), (13.4, 52.5), (10.2, 36.8), (-3.7, 40.2))


def narr(pose, x=200, y=665, **kw):
    return dict(type="narr", pose=pose, x=x, y=y, **kw)


def char(name, x, y=665, **kw):
    return dict(type="char", name=name, x=x, y=y, **kw)


def photo(src, **kw):
    return dict(type="photo", src=f"assets/img/{src}.jpg", **kw)


def icon(name, x, y, s=200, **kw):
    return dict(type="icon", name=name, x=x, y=y, s=s, **kw)


def text(t, x=540, y=340, **kw):
    return dict(type="text", text=t, x=x, y=y, **kw)


def ring(x, y, w, h, at=0.3, **kw):
    return dict(type="ring", x=x, y=y, w=w, h=h, at=at, **kw)


def pin(lonlat, label=None, side="left", at=0.0):
    return dict(type="pin", lon=lonlat[0], lat=lonlat[1], label=label, side=side, at=at)


def route(a, b, at=0.0, dur=0.9, **kw):
    return dict(type="route", path=[a, b], at=at, dur=dur, **kw)


def hl(ids, at=0.0, **kw):
    return dict(type="highlight", ids=ids, at=at, **kw)


SICILY_ID, SARDINIA_ID = ["c-ITA-sicily"], ["c-ITA-sardinia"]
DEAD = "dead-officer-lifejacket-briefcase"
SAND = dict(type="html", html="", style="left:0;top:560px;width:380px;height:140px;background:#5b5442;border-top:5px solid #1B1D1E;"
            "border-radius:0 120px 0 0", at=0)

S = V.shot
# ---- 1. The body on the beach -------------------------------------------------------------
S(0.00, 2.34, "1943", bg="scene", layers=[
    dict(type="sea", top=420), char(DEAD, 560, 560, scale=0.3, bob=True, enter="fade"),
    text("1943", 540, 190, style="year", enter="slam", at=0.15)])
S(2.34, 6.26, "جثة على الشاطئ", layers=[
    dict(type="sea", top=430), SAND, char("fisherman-pointing-shocked", 210, 600, enter="left"),
    char(DEAD, 700, 600, scale=0.32, bob=True, enter="fade"), ring(530, 470, 340, 170, at=1.4)])
S(6.26, 7.80, "الزي العسكري", bg="dark", layers=[photo("body", pos="50% 30%", kb="in", dim=0.1)])
S(7.80, 9.46, "صورة خطيبته", bg="dark", layers=[
    photo("fiancee", frame="archive", box=(330, 70, 520, 380), rot=-4), narr("present-right-pocket", 170, enter="left")])
S(9.46, 11.46, "رسائل وفواتير", layers=[
    narr("count-on-fingers", 190, enter="left"), icon("letter", 600, 300, 250, rot=-8),
    icon("receipt", 860, 330, 230, rot=7, at=0.95)])
S(11.46, 15.52, "سقوط طائرة", layers=[
    dict(type="sea", top=470), narr("point-right", 160, enter="left"),
    icon("plane", 860, 120, 230, rot=18, enter="fade", move=dict(dx=-260, dy=330, rot=24, dur=2.2, at=0.3)),
    icon("wave", 610, 470, 200, at=2.5)])
S(15.52, 19.36, "انتباه السلطات", layers=[
    SAND | dict(style=SAND["style"].replace("width:380px", "width:1080px").replace("border-radius:0 120px 0 0", "border-radius:0")),
    char(DEAD, 380, 640, scale=0.36, enter="fade"),
    char("spanish-official-briefcase", 940, 650, enter="right", move=dict(dx=-170, dur=1.6, at=0.2)),
    icon("qmark", 380, 190, 170, at=2.0, float=True)])
# ---- 2. The briefcase ------------------------------------------------------------------------
S(19.36, 21.72, "حقيبة مربوطة بيده", layers=[
    char(DEAD, 480, 483, scale=1.0, enter="fade", breathe=False), ring(370, 240, 380, 280, at=0.6)])
S(21.72, 25.68, "وثائق سرية", layers=[
    icon("doc", 600, 330, 430, enter="drop"), narr("magnifying-glass", 190, enter="left", at=0.3),
    text("سري للغاية", 610, 360, style="stamp", rot=-12, size=72, enter="slam", at=1.85)])
S(25.68, 29.94, "الهجوم القادم", bg="map", layers=[
    pin(TUNIS, "الحلفاء", side="down", at=0.2),
    icon("qmark", P(*SICILY)[0] + 10, P(*SICILY)[1] - 70, s=110, at=1.2), icon("qmark", P(*SARDINIA)[0], P(*SARDINIA)[1] - 70, s=100, at=1.7),
    icon("qmark", P(*GREECE)[0], P(*GREECE)[1] - 70, s=110, at=2.2)])
S(30.00, 33.80, "مسار الحرب", bg="dark", layers=[
    photo("warship-guns", kb="right", dim=0.25), narr("stress-hands-on-cap", 180, enter="left", at=1.3)])
# ---- 3. The twist -----------------------------------------------------------------------------
S(33.80, 35.06, "المفاجأة", bg="dark", chapter=True, layers=[
    narr("shocked-hands-up", 540, enter="pop"), icon("excl", 330, 200, 150, at=0.15), icon("excl", 760, 170, 150, at=0.3)])
S(35.06, 37.34, "لم يكن موجوداً", layers=[
    char(DEAD, 540, 560, scale=0.5, fade_to=0.18, fade_at=0.7), icon("qmark", 540, 250, 220, at=1.2, float=True)])
S(37.34, 39.98, "مزيّف", layers=[
    icon("idcard", 330, 320, 330, rot=-5, l1="الاسم", l2="؟؟؟"),
    icon("polaroid", 770, 320, 300, rot=6, src="assets/img/fiancee.jpg", at=0.9),
    text("مزيّف", 360, 470, style="stamp", rot=-14, size=64, enter="slam", at=0.45),
    text("مزيّف", 790, 480, style="stamp", rot=10, size=64, enter="slam", at=1.5)])
S(39.98, 41.82, "خدعة", bg="dark", layers=[
    narr("point-right", 190, enter="left"), text("خدعة", 650, 330, style="stamp", rot=-8, size=150, enter="slam", at=0.6)])
S(41.82, 44.14, "ليس ضابطاً", layers=[
    char(DEAD, 600, 600, scale=0.44, enter="fade"), narr("refuse-x-arms", 150, enter="left", at=0.4),
    text("ضابط", 600, 170, style="strike", size=120, enter="fade", strike_at=1.1)])
# ---- 4. Sicily ----------------------------------------------------------------------------------
S(44.14, 47.46, "صقلية", bg="map", layers=[
    pin(LONDON, "بريطانيا", side="left", at=0.2), route(LONDON, SICILY, at=1.0, dur=1.4, dashed=True),
    hl(SICILY_ID, at=2.6), pin(SICILY, "صقلية", side="down", at=2.6)])
S(47.46, 50.04, "الألمان ينتظرون", layers=[
    char("german-officer-reading", 330, enter="left"), char("german-officer-pointing", 760, enter="right", at=0.3)])
S(50.04, 52.66, "قوات هتلر", bg="map", layers=[
    hl(["c-DEU"], at=0.1, pulse=False), pin(BERLIN, "ألمانيا", side="right", at=0.1),
    route(BERLIN, SICILY, at=0.9, dur=1.2, color="#FFFFFF", width=8), hl(SICILY_ID, at=1.9)])
S(52.66, 54.82, "كارثة", bg="dark", layers=[
    narr("warning-sign", 540, enter="pop"), text("كارثة", 540, 110, style="stamp", rot=-5, size=80, enter="slam", at=0.7)])
S(54.82, 59.34, "الخطة الكبرى", layers=[
    narr("idea-lightbulb", 240, enter="left"), char("german-officer-reading", 790, enter="right", at=1.6),
    icon("qmark", 790, 120, 130, at=2.8, float=True)])
S(59.34, 61.86, "ليس صقلية", bg="map", layers=[
    hl(SICILY_ID, at=0.0, cross=0.55, pulse=False), hl(["c-GRC"], at=1.55),
    pin(GREECE, "اليونان", side="right", at=1.55)])
# ---- 5. Building Major Martin -------------------------------------------------------------------
S(61.86, 63.50, "الخطة", bg="dark", chapter=True, layers=[
    narr("finger-raise-talk", 220, enter="left"), text("الخطة", 640, 330, style="tag", size=110, enter="pop", at=0.2)])
S(63.50, 67.70, "جثة مجهولة", layers=[
    dict(type="html", html="", style="left:120px;top:520px;width:640px;height:40px;background:#6b5a43;border:5px solid #1B1D1E;border-radius:8px", at=0),
    char(DEAD, 440, 535, scale=0.42, enter="fade", opacity=0.8), char("uk-intel-officer-photo-letters", 880, enter="right", at=0.5),
    text("من الصفر", 440, 140, style="label", enter="up", at=2.1)])
S(67.70, 70.40, "ويليام مارتن", layers=[
    narr("present-right-2", 170, enter="left"), icon("idcard", 630, 330, 560, enter="drop", at=1.5, l1="الرائد", l2="ويليام مارتن")])
S(70.40, 72.50, "زي ضابط", layers=[
    char("uk-naval-officer-salute", 640, enter="pop"), narr("thumbs-up", 200, enter="left", at=0.4)])
S(72.50, 74.66, "في جيوبه", layers=[
    narr("count-on-fingers", 190, enter="left"), icon("polaroid", 640, 320, 340, rot=-6, src="assets/img/fiancee.jpg", enter="drop", at=0.9)])
S(74.66, 77.00, "في جيوبه", layers=[
    narr("count-on-fingers", 190, enter="none"), icon("letter", 520, 320, 250, rot=-6),
    icon("ticket", 830, 330, 260, rot=8, at=1.2)])
S(77.00, 78.60, "في جيوبه", layers=[
    narr("count-on-fingers", 190, enter="none"), icon("receipt", 520, 340, 270, rot=-4), icon("ring", 830, 330, 220, at=0.6)])
S(78.60, 83.02, "التفاصيل", layers=[
    narr("magnifying-glass", 300, enter="left"), icon("ticket", 760, 520, 140, rot=12, at=0.6),
    icon("ring", 900, 540, 110, at=1.0), ring(660, 430, 330, 190, at=2.2)])
S(83.02, 87.62, "التفاصيل", layers=[
    narr("finger-up", 180, enter="left"), text("التفاصيل", 650, 170, style="big", size=110, enter="up", at=0.9),
    icon("polaroid", 400, 470, 150, rot=-8, src="assets/img/fiancee.jpg", at=1.6), icon("letter", 560, 480, 140, at=1.9),
    icon("ticket", 720, 480, 140, rot=8, at=2.2), icon("receipt", 860, 470, 140, at=2.5), icon("ring", 980, 480, 110, at=2.8)])
# ---- 6. Into the sea near Spain -----------------------------------------------------------------
S(87.62, 89.80, "الوثائق المزيفة", layers=[
    icon("briefcase", 600, 450, 330), icon("doc", 600, 230, 230, enter="drop", at=0.3, move=dict(dy=170, dur=0.6, at=1.3, ease="power2.in")),
    text("مزيّفة", 860, 200, style="stamp", rot=10, size=60, enter="slam", at=0.9)])
S(89.80, 91.00, "قرب إسبانيا", bg="dark", layers=[photo("sub-seraph", kb="in", pos="40% 50%", dim=0.12)])
S(91.00, 92.12, "قرب إسبانيا", bg="map", layers=[
    hl(["c-ESP"], at=0.0, pulse=False), route((-2, 49.5), HUELVA, at=0.0, dur=0.9, dashed=True),
    pin(HUELVA, "إسبانيا", side="right", at=0.7)])
S(92.12, 95.30, "محايدة", bg="map", layers=[
    hl(["c-ESP"], at=0.0), text("محايدة؟", *P(*SPAIN), style="tag", size=50, enter="pop", at=1.5)])
S(95.30, 98.04, "عيون ألمانية", bg="map", layers=[
    hl(["c-ESP"], at=0.0, pulse=False), icon("eye", *P(*SPAIN), s=150, at=0.2),
    route(SPAIN, BERLIN, at=1.0, dur=1.4, dashed=True, color="#FFFFFF"), pin(BERLIN, "الألمان", side="right", at=2.2)])
# ---- 7. The question ------------------------------------------------------------------------------
S(98.04, 101.10, "سؤال واحد", bg="dark", layers=[
    narr("think-chin", 300, enter="left"), icon("qmark", 730, 300, 320, at=0.6, float=True)])
S(101.10, 103.76, "هل ستصل؟", layers=[
    icon("doc", 290, 330, 270), char("german-officer-reading", 820, enter="right", at=0.2),
    dict(type="arrow", **{"from": (420, 260), "to": (690, 240)}, at=0.7, dashed=True, color="#FFFFFF")])
S(103.76, 105.68, "هل سيصدّقونها؟", layers=[
    char("german-officer-reading", 540, enter="fade"), icon("qmark", 360, 200, 150, at=0.3), icon("qmark", 740, 170, 170, at=1.0)])
# ---- 8. The act -----------------------------------------------------------------------------------
S(105.68, 108.38, "عثر الإسبان", layers=[
    SAND | dict(style=SAND["style"].replace("width:380px", "width:1080px").replace("border-radius:0 120px 0 0", "border-radius:0")),
    char(DEAD, 330, 640, scale=0.34, enter="fade"),
    char("spanish-official-briefcase", 900, 650, enter="right", move=dict(dx=-160, dur=1.4, at=0.2))])
S(108.38, 112.92, "القلق", layers=[
    char("uk-intel-officer-worried-telegram", 560, enter="pop", shake_at=3.9), icon("excl", 760, 150, 130, at=3.9)])
S(112.92, 115.92, "برقية عاجلة", bg="dark", layers=[
    icon("telegram", 560, 340, 420, enter="drop"), text("عاجل", 760, 160, style="stamp", rot=12, size=78, enter="slam", at=0.9)])
S(115.92, 119.98, "تمثيلية", layers=[
    narr("stress-hands-on-cap", 280, enter="left"), icon("doc", 760, 330, 300, rot=8, at=0.6), ring(590, 160, 340, 360, at=2.0)])
S(119.98, 124.08, "عاد كل شيء", layers=[
    char(DEAD, 540, 300, scale=0.36, enter="pop", at=0.1), ring(290, 90, 500, 250, at=1.85),
    icon("briefcase", 330, 500, 200, at=2.6),
    icon("doc", 760, 500, 200, rot=6, at=3.4)])
S(124.08, 126.82, "لم تُفتح", layers=[
    narr("magnifying-glass", 220, enter="left"), icon("briefcase", 690, 360, 420), ring(560, 260, 270, 180, at=1.2)])
# ---- 9. The signal and the invasion -----------------------------------------------------------------
S(126.82, 130.72, "الإشارة", layers=[
    narr("listen-ear", 220, enter="left"), icon("radio", 680, 330, 360, at=1.5)])
S(130.72, 134.16, "صدّقوها", layers=[
    char("german-officer-reading", 480, enter="fade"), icon("check", 790, 210, 200, at=2.45)])
S(134.16, 138.02, "اليونان وسردينيا", bg="map", layers=[
    pin(BERLIN, "الألمان", side="right", at=0.0), route(BERLIN, GREECE, at=0.4, dur=1.0, color="#FFFFFF", width=7),
    route(BERLIN, SARDINIA, at=0.9, dur=1.0, color="#FFFFFF", width=7, bend=-0.15),
    hl(["c-GRC"], at=2.6), hl(SARDINIA_ID, at=3.3)])
S(138.02, 140.88, "المكان الخطأ", layers=[
    char("german-soldiers-running", 200, 650, scale=0.45, enter="none", move=dict(dx=700, dur=2.8, at=0.0)),
    text("المكان الخطأ", 540, 130, style="stamp", rot=-6, size=64, enter="slam", at=1.7)])
S(140.88, 142.30, "الحلفاء", bg="dark", layers=[photo("ship-officer", kb="in", dim=0.15)])
S(142.30, 143.70, "صقلية", bg="map", layers=[
    pin(TUNIS, "الحلفاء", side="down", at=0.0), route(TUNIS, SICILY, at=0.1, dur=0.8, width=8), hl(SICILY_ID, at=0.8),
    pin(SICILY, "صقلية", side="right", at=0.8)])
S(143.70, 145.56, "يوليو 1943", bg="dark", chapter=True, layers=[
    icon("calendar", 540, 330, 380, month="يوليو", year="1943")])
S(145.56, 147.72, "الغزو", bg="dark", layers=[photo("beach-day1", kb="in", dim=0.12)])
S(147.72, 149.30, "الغزو", bg="dark", layers=[photo("uk-troops-landing", kb="out", pos="50% 40%", dim=0.12)])
S(149.30, 150.92, "ويليام مارتن", layers=[
    char(DEAD, 540, 590, scale=0.42, opacity=0.35, enter="fade"), icon("idcard", 540, 250, 420, enter="pop", l1="الرائد", l2="ويليام مارتن")])
S(150.92, 154.06, "مهمة ناجحة", bg="dark", layers=[
    photo("canadians-advance", kb="left", dim=0.2), narr("thumbs-up", 170, enter="left", at=0.8)])
S(154.06, 156.66, "خدع جيشاً", layers=[
    char("german-soldiers-running", 820, 650, scale=0.45, flip=True, enter="right", move=dict(dx=-260, dur=2.4, at=0.2)),
    narr("laugh-hand-on-belly", 190, enter="left", at=0.3)])
S(156.66, 158.84, "ليست كذبة", layers=[
    icon("doc", 540, 330, 360), icon("cross", 720, 200, 170, at=1.0)])
S(158.84, 162.69, "قصة كاملة", layers=[
    narr("arms-wide-open", 540, enter="pop"),
    icon("polaroid", 170, 200, 200, rot=-8, src="assets/img/fiancee.jpg", at=0.2), icon("letter", 900, 180, 190, rot=6, at=0.5),
    icon("ticket", 160, 470, 190, rot=8, at=0.8), icon("receipt", 920, 460, 180, rot=-6, at=1.1),
    icon("idcard", 540, 110, 260, l1="الرائد", l2="ويليام مارتن", at=1.4)])

V.build("index.html")
print("shots:", len(V.shots), "timeline statements:", len(V.js))
