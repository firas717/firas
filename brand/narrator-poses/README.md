# وضعيات الراوي (مكتبة دائمة)

فراس يولّد وضعيات الراوي بـ Gemini من صورة المرجع `brand/narrator-reference.jpg`. كل وضعية تُحفظ هنا مرة واحدة، وتُستخدم في كل الحلقات القادمة.

## كيف تُطلب الوضعيات في كل حلقة
1. بعد قراءة السكربت، حدّد الوضعيات التي يحتاجها الستوري بورد.
2. استبعد ما هو موجود هنا مسبقاً.
3. أرسل لابن الخال **قائمة قصيرة بالناقص فقط**. لكل وضعية: اسم الملف، ووصف عربي من سطر، والبرومبت الجاهز أدناه بعد تعبئة `[POSE]`.
4. لا تتوقف أثناء الانتظار: أكمل الصوت والنسخ والستوري بورد والمشاهد. أضف الراوي في النهاية.
5. عندما تصل الصور: أزل الخلفية، واحفظها هنا بالأسماء المتفق عليها كـ PNG شفاف، ثم commit و push.
6. إن لم تصل الصور: استخدم أقرب وضعية موجودة. لا ترسم الراوي بالكود إلا كحل أخير، والتزم بقاعدة "عدم الانفصال" في CLAUDE.md.

## البرومبت الثابت لـ Gemini
ارفع صورة `narrator-reference.jpg` مع هذا النص، وغيّر `[POSE]` فقط:

```
Same character as the reference image: exactly the same green cap, spiky black hair,
blank white face with NO facial features, dark navy hoodie, dark grey jeans, dark sneakers,
white four-finger cartoon hands, same black outlines and flat colors.

New pose: [POSE]

Full body from cap to shoes, not cropped. Character centered, about 85% of image height.
Hands empty (not holding anything). No shadow on the ground. No text, no logo, no watermark.
Background: one solid flat pure magenta color (#FF00FF) filling the whole image, no gradient,
no checkerboard. Vertical image, high resolution.
```

**لماذا الخلفية الأرجوانية؟** الوجه واليدان والحدّ الخارجي كلها بيضاء، فالخلفية البيضاء تمنع فصلها. واللون الأرجواني غير موجود في الشخصية، فيسهل حذفه بدقة. ولا تطلب "خلفية شفافة"، لأن Gemini يرسم مربعات رمادية مزيّفة بدل الشفافية.

## الأسماء المعتمدة (الوضعيات الأساسية)
| الملف | الوضعية | [POSE] |
|---|---|---|
| `point-right.png` | يشير لليمين | `standing, pointing with his right arm straight to the right at something off-frame` |
| `point-left.png` | يشير لليسار | `standing, pointing with his left arm straight to the left at something off-frame` |
| `point-up.png` | يرفع إصبعه (فكرة) | `index finger raised up next to his head, making a point` |
| `count-two.png` | يعدّ | `holding up two fingers towards the viewer, counting` |
| `think.png` | يفكّر | `one hand on his chin, head slightly tilted, thinking` |
| `shrug.png` | حائر | `both palms up at shoulder height, shrugging` |
| `shocked.png` | مصدوم | `jumping back startled, both arms raised, leaning back` |
| `run.png` | يجري | `running to the right, mid-stride, arms swinging` |
| `arms-crossed.png` | واثق | `arms crossed, relaxed confident stance` |
| `sad.png` | حزين | `head lowered, shoulders dropped, hands hanging at his sides` |
| `stop.png` | يحذّر | `one palm pushed forward in a stop gesture, other hand at his side` |
| `present.png` | يقدّم | `one open palm extended to the side presenting something, like the reference image` |
| `scratch-head.png` | يحكّ رأسه | `scratching the back of his head under the cap, confused` |
| `celebrate.png` | يحتفل | `both fists raised in the air, celebrating` |

وضعيات جديدة خاصة بحلقة معينة تُضاف بأسماء إنجليزية قصيرة بشرطات، مثل `hold-phone.png` أو `look-through-binoculars.png`. أضف كل وضعية جديدة إلى هذا الجدول.

## إزالة الخلفية
```bash
ffmpeg -i in.png -vf "colorkey=0xFF00FF:0.30:0.08" -frames:v 1 out.png
```
أو `npx hyperframes@0.8.183 remove-background` إن لم تكن الخلفية أرجوانية صافية. بعد ذلك افحص الحواف بعينك على خلفية داكنة وعلى خلفية فاتحة، وتأكد ألا يبقى أثر أرجواني.

## التركيب في الفيديو
- استخدم الصورة كاملة كقطعة واحدة: **لا تقطّعها إلى أطراف ولا تحرّك أجزاءها منفصلة.**
- الحركة المسموحة على الصورة كاملة: دخول بانزلاق أو تكبير خفيف، وتنفّس (scale 1→1.02)، واهتزاز بسيط للتأكيد، وتبديل وضعية بقطع حاد أو تلاشٍ سريع (3–4 فريمات).
- أضف حدّاً أبيض خارجياً (~8px) عند التركيب على خلفية داكنة إن لم يكن موجوداً في الصورة.
