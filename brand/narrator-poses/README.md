# وضعيات الراوي (مكتبة دائمة)

فراس يولّد وضعيات الراوي بـ Gemini من صورة المرجع `brand/narrator-reference.jpg`، ثم تُقصّ وتُحفظ هنا مرة واحدة وتُستخدم في كل الحلقات.

- **المكتبة الحالية: 120 وضعية.** انظر `_index.jpg` لترى كل وضعية مع اسمها، وكلها بنفس المقياس.
- كل ملف PNG شفاف بحدّ أبيض خارجي جاهز للتركيب على الخلفيات الداكنة.
- **كل الوضعيات بمقياس واحد:** الوقوف ارتفاعه ~900px، والجلوس والزحف والاستلقاء أقصر بحجمها الحقيقي. عند التركيب استخدم **معامل تكبير واحداً لكل المشهد** (مثلاً 0.55 ليصير طول الوقوف ~500px)، ولا تجعل كل وضعية بنفس الارتفاع، وإلا كبر رأس الراوي في وضعيات الجلوس.
- الاتجاه في الأسماء (right/left) هو اتجاه الصورة كما يراها المشاهد.
- بعض الوضعيات فيها أغراض (لابتوب، كاميرا، مكبّرة، خريطة، كتاب، صندوق، جوال، مفتاح، لافتة تحذير...). **فراس ولّدها بنفسه فهي معتمدة**، رغم أن ملف `02-الشخصيات.md` يقول إن الراوي لا يحمل شيئاً.
- `panic-hands-on-head.png` كان فيه فم، و`panic-run-arms-up.png` كان فيه ظل يشبه الفم. مُسحا لأن الوجه يجب أن يبقى بلا ملامح. افحص كل دفعة جديدة لهذا الخطأ.

## الفهرس حسب الاستخدام
| الغرض | الوضعيات |
|---|---|
| يشير إلى الموضوع | `point-right` `point-right-2` `point-right-3` `point-left` `point-left-2` `point-left-3` `explain-point-right` `point-chart` |
| يشير للأسفل (شيء على الأرض أو خريطة) | `point-down-right` `point-down-right-2` `point-down-right-3` |
| يقدّم أو يشرح | `present-right-pocket` `present-right-2..5` `present-low-right` `explain-hands` `count-on-fingers` `finger-raise-talk` `mic-stand-present` `arms-wide-open` |
| فكرة أو معلومة | `finger-up` `finger-up-2..4` `idea-lightbulb` |
| يفكّر أو يتساءل | `think-chin` `think-chin-2` `think-chin-3` `think-chin-side` `think-head-down` `listen-ear` `listen-ear-2` `listen-ear-3` |
| حيرة | `shrug` `shrug-2..6` `sit-crosslegged-shrug` |
| صدمة أو خوف | `shocked-hands-up` `recoil-scared` `panic-hands-on-head` `stress-hands-on-cap` `facepalm` |
| حزن أو تعب أو مأساة | `sad-head-down` `sad-head-down-2` `tired-bent-over` `hand-on-chest` `hand-on-chest-lean` |
| تحذير أو رفض | `stop-palm` `refuse-x-arms` `warning-sign` `thumbs-down` `thumbs-down-2` |
| موافقة أو فرح أو نجاح | `thumbs-up` `thumbs-up-2` `clap` `clap-2` `fist-pump` `kneel-celebrate` `jump-joy` `peace-sign` `laugh-hand-on-belly` |
| تحيّة (بداية أو نهاية) | `wave` `wave-2` `hello-both-hands` |
| ثقة أو وقوف هادئ | `stand-pockets` `stand-pockets-2..4` `hands-on-hips` `hands-on-hips-2..4` `hands-on-hips-stride` `arms-crossed` `arms-crossed-2` `arms-crossed-3` `lean-casual` |
| مشي | `walk-right` `walk-right-2` `walk-right-3` `walk-toward-camera` `walk-away` |
| ركض وهروب | `run-right` `run-right-2` (إطاران لدورة ركض) `panic-run-arms-up` (هروب مذعور) |
| زحف وتسلّل | `crawl-right` `crawl-right-2` (إطاران لدورة زحف) `sneak` `lean-forward-peek` `crouch` |
| سقوط وانهيار | `stumble` `fall-backward` `fall-on-knees` `lying-down` `sit-floor-sad` |
| تسلّق وجلوس | `climb-back-view` (من الخلف) `sit` `sit-crosslegged-shrug` |
| تحقيق أو بحث | `magnifying-glass` `binoculars` `look-far` `read-map` `check-watch` |
| أغراض | `laptop` `look-phone` `look-phone-2` `look-phone-3` `read-book` `read-book-2` `read-book-3` `write-notepad` `write-clipboard` `photo-camera` `hold-box` `hold-box-2` `hold-key` |

## الشخصيات تمثّل الحدث (ما أعجب فراس في الحلقة الأولى)
في الحلقة الأولى **كانت الشخصيات تتحرك وتتفاعل مع الموقف**: تركض، وتزحف، وتقف، وتنهار، وتهرب. وكانت النتيجة جميلة. لذلك لا تكتفِ بصورة ثابتة تقف في المشهد، بل اجعل الشخصية **تمثّل** ما يُقال:
- **التنقّل:** حرّك الصورة كاملة عبر البطاقة (من خارج الإطار إلى داخله، أو عبره). بدّل بين إطارات المشي `walk-right` و`walk-right-2` و`walk-right-3` بمعدل 6–8 تبديلات في الثانية، مع اهتزاز رأسي خفيف (2–4px) يحاكي الخطوة. للركض بدّل بين `run-right` و`run-right-2` (8–10 تبديلات في الثانية) مع حركة أسرع وخطوط سرعة خلفه. وللزحف بدّل بين `crawl-right` و`crawl-right-2` ببطء (3–4 في الثانية).
- **الاتجاه المعاكس:** اقلب الصورة أفقياً (`scaleX(-1)`)، إلا الوضعيات التي فيها كتابة أو شعار (`laptop` و`warning-sign` و`point-chart`).
- **الانفعال:** انتقل بين وضعيتين بقطع حاد في لحظة الكلمة. أمثلة: `stand-pockets` ← `shocked-hands-up` عند المفاجأة، و`recoil-scared` ← `run-right` عند الهروب، و`tired-bent-over` ← `sad-head-down` عند الانهيار. أضف "ارتداداً" صغيراً (scale 0.96→1.02→1 خلال 6 فريمات) عند كل تبديل.
- **التأكيد:** هزّة خفيفة، أو قفزة صغيرة، أو علامة `!` أو `?` ليمونية فوق الرأس.
- **ممنوع:** تقطيع الصورة إلى أطراف وتحريكها منفصلة. هذا ما جعل أجزاء الجسم تنفصل في الحلقة الأولى.
- **أمثلة لسلاسل جاهزة:**
  - الانهيار: `stumble` ← `fall-on-knees` ← `lying-down`.
  - الهروب: `recoil-scared` ← `panic-run-arms-up` ← `run-right`/`run-right-2` مع خروج من الإطار.
  - التسلّل: `sneak` ← `lean-forward-peek`.
  - الإغماء: `shocked-hands-up` ← `fall-backward` ← `lying-down`.
- إن احتاج الحدث حركة غير موجودة، فاطلبها من فراس بالبرومبت أدناه.

## الحركة الحية (طلب فراس بعد الحلقة الثانية)
قال فراس: "الشخصيات واقفة ولا تتحرك... أريدها أن تتحرك وكأن شخصاً حقيقياً يحرّك جسده". لذلك كل وضعية على الشاشة **حيّة طوال ظهورها**:
- `scripts/nerd/alive.py` يثني الصورة كاملة (warp) حول نقاط تحكم: القدمان ثابتتان، ويتحرك الورك والصدر والرأس واليدان. الصورة لا تُقطَّع، فلا تنفصل أجزاء الجسم أبداً.
- **الحركة الأساسية لكل شخصية:** تنفّس، وتمايل خفيف في الوزن، وميل للرأس.
- **فوقها حركة حسب الوضعية** (`style_for`):
  - `point`: اليد المشيرة تندفع.
  - `count` و`present` و`talk`: اليدان تتحركان على الكلمات المنبورة، مع إيماءة رأس.
  - `tremble`: ارتجاف وتراجع عند الصدمة.
  - `laugh`: اهتزاز الضحك.
  - `think`: ميل بطيء للرأس.
  - `search`: مسح بالمكبّرة.
  - `shake`: هزّ الرأس رفضاً أو قلقاً.
  - `cheer`: اندفاع الإبهام.
  - `wide`: رفع الذراعين.
  - `hop`: قفزة صغيرة عند الفكرة.
  - `walk`: مشي بارتداد، ويُختار تلقائياً عند وجود `move`.
  - `run`: ركض لمجموعة.
- نقاط التحكم تُكشف من الوجه واليدين البيضاء. التصحيحات في `rig.json` هنا وفي `brand/characters/*/rig.json`، وراجعها بـ:
  `python3 scripts/nerd/alive.py sheet <out.jpg> <صور...>`
- لمعاينة حركة وضعية واحدة: `python3 scripts/nerd/alive.py demo <png> <style> <out.mp4>`.
- **الجسد لا يتقطّع أبداً** (طلب فراس):
  - كل مقطع يُفحص آلياً إطاراً إطاراً بحثاً عن تمزّق، أو انطواء، أو تمدّد موضعي، أو قصّ عند الحافة، والبناء يتوقف إن فشل أي إطار.
  - الذراع تدور حول الكتف ولا تتمدد.
  - النقاط المتجاورة مقيّدة بحد أقصى للشد (`MAX_STRAIN`).
- الثني يناسب الحركة المتوسطة. أما الحركة الكبيرة (رفع ذراع من الأسفل إلى الأعلى، أو خطوة كاملة) فتحتاج وضعية جديدة أو إطارات مشي، فاطلبها من فراس.

## كيف تُطلب الوضعيات في كل حلقة
1. بعد قراءة السكربت، حدّد الوضعيات والحركات التي يحتاجها الستوري بورد.
2. استبعد ما هو موجود في المكتبة.
3. أرسل لابن الخال **قائمة قصيرة بالناقص فقط**: اسم الملف، ووصف عربي من سطر، والبرومبت الجاهز أدناه بعد تعبئة `[POSE]`. يمكن طلب عدة وضعيات في صورة واحدة (شبكة)، كما فعل فراس، والسكربت يقصّها تلقائياً.
4. لا تتوقف أثناء الانتظار: أكمل الصوت والنسخ والستوري بورد والمشاهد، وأضف الراوي في النهاية.
5. عندما تصل الصور، شغّل:
   `python3 scripts/poses/extract_poses.py <مجلد مؤقت> <صورة1> <صورة2> ...`
   ثم انظر إلى `_preview_*.jpg`، وسمِّ كل ملف، وانقله إلى هنا. بعدها ضغطه بـ `pngquant --quality=80-95 --ext .png --force`، وأعد بناء `_index.jpg`، وحدّث الجدول أعلاه، ثم commit و push.

## البرومبت الثابت لـ Gemini (الراوي)
ارفع صورة `narrator-reference.jpg` مع هذا النص، وغيّر `[POSE]` فقط:

```
Same character as the reference image: exactly the same green cap, spiky black hair,
blank white face with NO facial features (no eyes, no mouth), dark navy hoodie, dark grey jeans,
dark sneakers, white four-finger cartoon hands, same black outlines and flat colors.

New pose: [POSE]

Full body from cap to shoes, not cropped. No text, no logo, no watermark.
Background: one solid flat pure magenta color (#FF00FF) filling the whole image, no gradient,
no checkerboard, no floor, no wall. High resolution.
```
لطلب عدة وضعيات دفعة واحدة: `A grid of N separate poses of the same character, well spaced, not touching: 1) ... 2) ...`

**لماذا الخلفية الأرجوانية؟** الوجه واليدان بيضاء، فالخلفية البيضاء تمنع فصلها. والأرجواني لا يوجد في الشخصية. ولا تطلب "خلفية شفافة"، لأن Gemini يرسم مربعات مزيفة بدل الشفافية. الظل البنفسجي تحت القدمين يُحذف تلقائياً.

## الشخصيات الثانوية (سجين، شرطي، ضحية، جندي...)
نفس الطريقة، لكن ببرومبت مختلف حتى **لا تشبه الراوي**:
```
Same cartoon style as the reference image (blank white face with NO facial features, even black
outlines, flat colors, white four-finger hands), but a DIFFERENT person: [وصف الشخصية: الشعر،
غطاء الرأس، اللباس، البنية، الألوان]. He must NOT wear a green cap or a navy hoodie.

Poses: [POSE LIST]

Full body, not cropped. No text, no logo. Background: solid flat pure magenta (#FF00FF).
```
تُحفظ في `brand/characters/<اسم-الشخصية>/` إن تكررت في حلقات أخرى، وإلا في مجلد الحلقة.

## إزالة الخلفية يدوياً (لصورة واحدة)
```bash
ffmpeg -i in.png -vf "colorkey=0xFF00FF:0.30:0.08" -frames:v 1 out.png
```
لكن `extract_poses.py` أفضل: يحذف الظل البنفسجي أيضاً، ويضيف الحدّ الأبيض.
