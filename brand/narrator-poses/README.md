# وضعيات الراوي (مكتبة دائمة)

فراس يولّد وضعيات الراوي بـ Gemini من صورة المرجع `brand/narrator-reference.jpg`، ثم تُقصّ وتُحفظ هنا مرة واحدة وتُستخدم في كل الحلقات.

- **المكتبة الحالية: 108 وضعيات.** انظر `_index.jpg` لترى كل وضعية مع اسمها.
- كل ملف PNG شفاف، بارتفاع ~900px، بحدّ أبيض خارجي جاهز للتركيب على الخلفيات الداكنة.
- الاتجاه في الأسماء (right/left) هو اتجاه الصورة كما يراها المشاهد.
- بعض الوضعيات فيها أغراض (لابتوب، كاميرا، مكبّرة، خريطة، كتاب، صندوق، جوال، مفتاح، لافتة تحذير...). **فراس ولّدها بنفسه فهي معتمدة**، رغم أن ملف `02-الشخصيات.md` يقول إن الراوي لا يحمل شيئاً.
- `panic-hands-on-head.png` كان فيه فم مرسوم، فمُسح لأن الوجه يجب أن يبقى بلا ملامح. افحص كل دفعة جديدة لهذا الخطأ.

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
| حركة في المكان | `walk-right` `walk-right-2` `walk-right-3` `walk-toward-camera` `walk-away` `run-right` `crouch` `sit` |
| تحقيق أو بحث | `magnifying-glass` `binoculars` `look-far` `read-map` `check-watch` |
| أغراض | `laptop` `look-phone` `look-phone-2` `look-phone-3` `read-book` `read-book-2` `read-book-3` `write-notepad` `write-clipboard` `photo-camera` `hold-box` `hold-box-2` `hold-key` |

## الشخصيات تمثّل الحدث (ما أعجب فراس في الحلقة الأولى)
في الحلقة الأولى **كانت الشخصيات تتحرك وتتفاعل مع الموقف**: تركض، وتزحف، وتقف، وتنهار، وتهرب. وكانت النتيجة جميلة. لذلك لا تكتفِ بصورة ثابتة تقف في المشهد، بل اجعل الشخصية **تمثّل** ما يُقال:
- **التنقّل:** حرّك الصورة كاملة عبر البطاقة (من خارج الإطار إلى داخله، أو عبره). بدّل بين إطارات المشي `walk-right` و`walk-right-2` و`walk-right-3` بمعدل 6–8 تبديلات في الثانية، مع اهتزاز رأسي خفيف (2–4px) يحاكي الخطوة. للركض استخدم `run-right` مع حركة أسرع وخطوط سرعة خلفه.
- **الاتجاه المعاكس:** اقلب الصورة أفقياً (`scaleX(-1)`)، إلا الوضعيات التي فيها كتابة أو شعار (`laptop` و`warning-sign` و`point-chart`).
- **الانفعال:** انتقل بين وضعيتين بقطع حاد في لحظة الكلمة. أمثلة: `stand-pockets` ← `shocked-hands-up` عند المفاجأة، و`recoil-scared` ← `run-right` عند الهروب، و`tired-bent-over` ← `sad-head-down` عند الانهيار. أضف "ارتداداً" صغيراً (scale 0.96→1.02→1 خلال 6 فريمات) عند كل تبديل.
- **التأكيد:** هزّة خفيفة، أو قفزة صغيرة، أو علامة `!` أو `?` ليمونية فوق الرأس.
- **ممنوع:** تقطيع الصورة إلى أطراف وتحريكها منفصلة. هذا ما جعل أجزاء الجسم تنفصل في الحلقة الأولى.
- إن احتاج الحدث حركة لا توجد لها وضعية (زحف، سقوط، استلقاء، تسلّق...)، فاطلبها من فراس (انظر "الدفعة القادمة"). وأثناء الانتظار استخدم أقرب بديل: `crouch` بدل الزحف، و`tired-bent-over` ثم `sad-head-down` بدل الانهيار.

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

## الدفعة القادمة المقترحة (حركات ناقصة)
| الملف | [POSE] |
|---|---|
| `crawl-right.png` و`crawl-right-2.png` | `crawling on hands and knees to the right` (frame 1 and frame 2 of the crawl) |
| `run-right-2.png` | `running to the right, opposite leg forward than the first run pose` |
| `run-away-looking-back.png` | `running to the right in panic while looking back over his shoulder` |
| `stumble.png` | `stumbling forward, losing balance, arms flailing` |
| `fall-on-knees.png` | `collapsed on his knees, hands on the ground, head down` |
| `lying-down.png` | `lying flat on the ground on his back, exhausted` |
| `sneak.png` | `sneaking on tiptoes to the right, crouched, careful` |
| `hide-peek.png` | `hiding and peeking out from the side, half body visible` |
| `climb.png` | `climbing up, both arms reaching above his head` |
| `sit-floor-sad.png` | `sitting on the floor hugging his knees, sad` |

## إزالة الخلفية يدوياً (لصورة واحدة)
```bash
ffmpeg -i in.png -vf "colorkey=0xFF00FF:0.30:0.08" -frames:v 1 out.png
```
لكن `extract_poses.py` أفضل: يحذف الظل البنفسجي أيضاً، ويضيف الحدّ الأبيض.
