# مكتبة الملمس والإضاءة والمؤثرات (textures-light-effects)

صور ثابتة من 8 مجلدات داخل `13 - أكثر من 6300 ملحق للمونتاج مجاني/`. المسارات نسبية لجذر `assets/` (نفس جذر مشاركة OneDrive)، فتعمل مباشرة مع `scripts/fetch_onedrive.py`. الجدول الكامل صفاً صفاً في `textures-light-effects.tsv`.

## الخلاصة

- **1013 صورة**. نحو ثلثها لا يصلح للقناة: 143 دم (ممنوع)، 132 نسخة مكررة، وعشرات بأسلوب ألعاب أو أنمي (نيون، خطوط مانجا، انفجارات ملونة، إطارات كرتونية).
- **أفيد ما فيها:** كشافات الإضاءة والتوهجات، الدخان والضباب، تعتيم الأطراف وأقواس زوايا الكاميرا، ورق قديم وجرائد، شبكات وخريطة كنتور، سياج السجن، علامات التحويط والتسطير والصواعق، وأشكال بيضاء تصلح ماسكات.
- مجلد `Overlay` (فيديوهات) خارج هذه المجموعة، أما هنا فالمجلد هو `Overlays` (صور).

## المجلدات

| المجلد | العدد | ماذا فيه |
|---|---|---|
| `Brushs/Brushs` | 397 | فرش PNG شفافة: أشكال بيضاء مسطحة، علامات يدوية، ضربات فرشاة بيضاء وسوداء، هافتون، وبعض الرشات الحمراء الشبيهة بالدم |
| `Effets (Effects)` | 143 | دخان وغيوم، جزيئات، خطوط مانجا، حلقات نيون، انفجارات، ومضات، أشعة |
| `Overlays` | 64 | خلفيات كاملة على أسود (screen): بلازما وفراكتال وانفجارات ملونة، وسياج شبكي، وبرق |
| `اضائة` | 164 | تسربات ضوء شفافة (كثير منها مكرر)، تدرجات مصمتة، ومضات عدسة، توهجات، كشاف علوي |
| `تأثيرات` | 65 | معظمه نسخ من `اضائة` و`Effets` (Light و Brush Light و Flare)، وتوهجات دائرية، وأسهم، وبرق كهربائي |
| `تكتسشر` | 41 | ملامس كاملة: ورق مجعد أبيض وأسود، جرائد قديمة، حبيبات وغبار، خرسانة، شبكات، خريطة كنتور، تعتيم |
| `اطارات` | 7 | إطارات بيضاء/خضراء بسيطة وإطارات خطوط مانجا |
| `تأثيرات دم` | 132 | رذاذ وسيلان دم (سيلويت أسود يُلوَّن أحمر). **ممنوع** |

## طريقة الدمج (عمود meta)

- `alpha`: PNG شفاف حقيقي (813 ملفاً)، يوضع فوق المشهد مباشرة.
- `black→screen`: المؤثر على خلفية سوداء (125)، يُدمج بـ `mix-blend-mode: screen` فيختفي الأسود.
- `white→multiply`: ملمس على أبيض (23)، يُدمج بـ `multiply` (ورق وجرائد).
- `opaque`: صورة كاملة تملأ الإطار (52)، تُستخدم خلفية أو بـ `overlay` بنسبة قليلة.

## الفئات

| الفئة | العدد | الشكل | متى تستخدمها القناة |
|---|---|---|---|
| `spotlight-rays` | 8 | كشافات وأشعة وظلال ضوء | إضاءة الراوي والعناصر (مثل المرجع) |
| `glow-orb` | 21 | توهجات دائرية ناعمة | كشاف خلف عنصر في مشهد مرسوم |
| `smoke-fog` | 24 | دخان وضباب وغيوم | مشاهد ليل وحرب وغموض |
| `frame-border` | 24 | إطارات، تعتيم أطراف، أقواس زوايا | إطار شاشة الكاميرا وتعتيم البطاقة |
| `paper-texture` | 21 | ورق مجعد، ورق قديم، جرائد | وثائق، ملفات قضايا، أخبار تاريخية |
| `grunge-texture` | 18 | حبيبات، غبار، خرسانة، تشويش | ملمس خفيف فوق البطاقة أو لقطة أرشيفية |
| `grid-texture` | 10 | شبكات، ورق بياني، خريطة كنتور، سياج | خرائط ومخططات وسجون |
| `doodle-mark` | 101 | علامات يدوية صغيرة: X، +، أسهم، برق، تحويط، زجاج مكسور | تعليم عنصر في البطاقة، علامات فوق رأس الراوي |
| `shape-matte` | 107 | أشكال بيضاء مسطحة: دوائر، أشرطة، موجات، سداسيات | ماسك انتقال، خلفية وسم أو بطاقة اسم |
| `brush-white` | 39 | ضربات ورشات فرشاة بيضاء | خلفية كلمة مفتاحية أو ماسك كشف |
| `halftone` | 31 | نقاط هافتون وتدرجات نقطية | ملمس طباعة قديمة خفيف |
| `lightning` | 8 | برق واقعي | عاصفة/طبيعة |
| `particles-bokeh` | 52 | جزيئات، بوكيه، جمر، نجوم، ثلج | جو خفيف لمشهد حرب/ليل/شتاء |
| `lens-flare` | 26 | ومضات عدسة ولمعات نجمية | ومضة كشف واحدة |
| `glitch` | 18 | كتل وخطوط تشويش رقمي | لحظة شاشة/VHS لسبب واضح |
| `light-leak` | 96 | تسربات ضوء ملونة شفافة في الزوايا أو الأسفل | نادراً، على لقطة حقيقية فقط |
| `brush-black` | 62 | بقع وضربات فرشاة سوداء | قليل الفائدة على خلفية داكنة |
| `neon-shape` | 51 | حلقات وخطوط وأشكال نيون/كهرباء ملونة | لا يناسب (أسلوب ألعاب) |
| `energy-burst` | 29 | انفجارات خطوط طاقة وبرق ملون على أسود | لا يناسب |
| `speed-lines` | 27 | خطوط سرعة/تركيز مانجا | لا يناسب غالباً |
| `sunburst-spiral` | 21 | أشعة إشعاعية ودوامات | لا يناسب |
| `abstract-bg` | 32 | خلفيات بلازما وفراكتال ملونة | لا يناسب |
| `gradient-fill` | 19 | ألوان وتدرجات مصمتة | لا حاجة (تُبنى في CSS) |
| `gaming-frame` | 8 | إطارات كرتونية بسحب نارية ومجرات | لا يناسب |
| `paint-splash` | 5 | رشات طلاء ملونة | لا يناسب |
| `misc` | 12 | أشياء متفرقة: شعارات أنمي، قبعة، رموز | لا يناسب |
| `blood-splatter` | 143 | رذاذ وبقع وسيلان دم (أسود يُلوَّن أحمر) + رشات حمراء | ممنوع تماماً |

## أفضل الملفات لكل فئة

الأمثلة كلها ليست مكررة، والمسار يبدأ من `13 - أكثر من 6300 ملحق للمونتاج مجاني/`. لوّن الأشكال البيضاء بلون الحلقة أو بالليموني `#ABDB61`، وبالأحمر `#C33B3F` للتحويط.

### كشافات وأشعة (`spotlight-rays`)

- `اضائة/GandroidPacks (25).png` (1280x720 alpha): كشاف أبيض ناعم من الأعلى، شفاف؛ يطابق إضاءة الكشاف في المرجع
- `اضائة/white top.png` (1280x720 alpha): إضاءة علوية عريضة ناعمة لبطاقة مرسومة
- `اضائة/1-2.png` (1772x591 alpha): توهج علوي خافت لشريط ضيق
- `Brushs/Brushs/Ajay GFX064.png` (1280x720 alpha): أشعة كشاف من الزاوية على عنصر
- `Brushs/Brushs/Ajay GFX062.png` (1280x720 alpha): خيوط ضوء قطرية خفيفة
- `Effets (Effects)/2-2.png` (1439x1057 alpha): أشعة بيضاء من المركز للحظة كشف
- `اضائة/lune_blanche.png` (877x494 alpha): إضاءة أرضية خافتة تحت الراوي
- `تكتسشر/a1eac9ff489f6b3ad0997a2b0c255f3f.jpg` (540x360 white→multiply): ظل ستائر لمشهد تحقيق (دقته منخفضة: صغّره أو موّهه)

### توهجات (`glow-orb`)

- `اضائة/white glow.png` (755x720 alpha): توهج أبيض دائري نظيف خلف عنصر
- `اضائة/yellow glow.png` (755x720 alpha): توهج أصفر يناسب العنوان البرتقالي
- `اضائة/red glow.png` (755x720 alpha): توهج أحمر لتنبيه أو خطر
- `تأثيرات/1600228438858.png` (1080x1080 alpha): توهج أزرق 1080px لمشهد ليلي
- `اضائة/18.jpg` (1280x720 black→screen): نقاط ضوء في الظلام لمشهد غموض
- `Brushs/Brushs/Ajay GFX124.png` (1280x720 alpha): توهج أبيض صغير خلف أيقونة

### دخان وضباب (`smoke-fog`)

- `Effets (Effects)/7-1.png` (1915x1068 alpha): ضباب أبيض كثيف شفاف بعرض الإطار
- `Effets (Effects)/8-1.png` (1080x1080 black→screen): عمود دخان على أسود لحريق أو مدخنة
- `Effets (Effects)/1.png` (1114x626 alpha): سحابة دخان واقعية شفافة
- `Effets (Effects)/smok.png` (1920x1080 alpha): دخان شفاف خفيف للطبقة العليا
- `Effets (Effects)/Fumee-Transparentes-PNG.png` (1024x648 alpha): سحابة دخان ناعمة
- `Effets (Effects)/22-1.png` (820x359 alpha): دخان رمادي طويل لانفجار
- `Brushs/Brushs/Ajay GFX370.png` (960x540 alpha): خيط دخان رفيع (سيجارة/شمعة)
- `Effets (Effects)/Smoke3_VENGEANCE.png` (1280x720 alpha): دخان خفيف أسفل الإطار

### إطارات وتعتيم (`frame-border`)

- `تكتسشر/VIGNETTE.png` (1920x1080 alpha): تعتيم أطراف شفاف جاهز (Vignette)
- `تكتسشر/خلفية متدرجة.png` (1920x1080 alpha): تدرج أسود من الأسفل لدمج اللقطة مع شريط الكابشن
- `Effets (Effects)/20190201_212623.png` (1280x720 alpha): أقواس زوايا بيضاء لإطار شاشة الكاميرا/REC
- `Brushs/Brushs/Ajay GFX008.jpg` (626x808 white→multiply): إطار جرنج لصورة أرشيفية (multiply)
- `Effets (Effects)/9-1.png` (1918x1062 alpha): دخان على الأطراف لمشهد غموض
- `Overlays/overlays23.png` (1280x720 alpha): خيوط دخان حول الإطار
- `Brushs/Brushs/Ajay GFX007.png` (1000x1000 alpha): مسطرة تدريج لمشاهد القياس
- `اطارات/1.png` (1280x720 alpha): إطار أبيض رفيع لصورة داخل البطاقة

### ورق وجرائد (`paper-texture`)

- `تكتسشر/pngwing.com (4).png` (1024x1499 alpha): ورقة قديمة محروقة الحواف لوثيقة تاريخية (عمودية)
- `تكتسشر/text 1.jpg` (3456x2439 white→multiply): جريدة قديمة حقيقية لخبر تاريخي
- `تكتسشر/vecteezy_paper-wrinkled-and-crumped-texture-transparent-glued-poster_41643335.png` (5000x3500 alpha): ملمس ملصق مجعّد شفاف فوق لوحة المطلوبين
- `تكتسشر/images (1) (31).jpg` (701x438 opaque): ورق أسود مجعد لخلفية ملف قضية
- `تكتسشر/rm218batch7-katie-43.jpg` (800x533 opaque): ورق أسود مجعد ناعم
- `تكتسشر/images (2) (1).jpg` (626x417 opaque): ورق أسود مجعد كثيف
- `تكتسشر/Paper-Texture-3.jpg` (2000x1500 white→multiply): ورق أبيض ناعم عالي الدقة

### ملمس وحبيبات (`grunge-texture`)

- `تكتسشر/1.png` (800x800 alpha): غبار وخدوش فيلم شفافة فوق لقطة أرشيفية
- `تكتسشر/film_texture___grain_explosion_by_stephanepellennec_d37pwfa-fullview.jpg` (1024x768 opaque): حبيبات فيلم (overlay بنسبة قليلة)
- `تكتسشر/pexels-hoang-le-978462.jpg` (2000x2000 opaque): خرسانة 2000px لجدار زنزانة
- `تكتسشر/black-texture-background-high-res-thumb33.jpg` (800x600 opaque): ملمس أسود محبب لخلفية البطاقة
- `تكتسشر/photo-1602475063211-3d98d60e3b1f.jpeg` (1000x606 opaque): ملمس أسود محبب بديل
- `Brushs/Brushs/Ajay GFX408.jpg` (508x680 opaque): هافتون متسخ لطابع طباعة قديمة
- `تكتسشر/czNmcy1wcml2YXRlL3Jhd3BpeGVsX2ltYWdlcy93ZWJzaXRlX2NvbnRlbnQvbHIvdjExMTEtMDEyYS5wbmc.webp` (800x533 opaque): تشويش رمادي لشاشة قديمة

### شبكات وخرائط (`grid-texture`)

- `Overlays/overlays10.jpg` (5120x2880 black→screen): سياج شبكي معدني 5K على أسود: مثالي لمشاهد السجن
- `تكتسشر/WhatsApp Image 2023-02-14 at 13.59.38.jpg` (736x1472 opaque): خريطة طبوغرافية عمودية على كحلي لمشاهد الجغرافيا
- `تكتسشر/16358390_rm301-eye-10-c.jpg` (4000x2665 opaque): شبكة داكنة 4000px لخلفية مخطط أو شاشة مراقبة
- `تكتسشر/Grid Black.jpg` (1920x1274 opaque): شبكة سوداء دقيقة
- `تكتسشر/grid-over-horizontal-rectangle-paper-size-6x4-inch-or-postcard-size-free-vector.jpg` (1920x1274 white→multiply): ورق رسم بياني أبيض لمخطط
- `تكتسشر/2115011_7800.jpg` (5000x5000 white→multiply): شبكة متساوية القياس لرسوم تقنية
- `Brushs/Brushs/Ajay GFX386.png` (1280x720 alpha): شبكة منظور بدخان لمشهد تقني/مستقبلي

### علامات يدوية (`doodle-mark`)

- `Brushs/Brushs/Ajay GFX044.png` (1280x720 alpha): تحويط يدوي حول الشخص المقصود (يُلوَّن #C33B3F)
- `Brushs/Brushs/Ajay GFX042.png` (1280x720 alpha): تسطير يدوي تحت اسم أو رقم
- `Brushs/Brushs/Ajay GFX050.png` (1280x720 alpha): صاعقة صدمة فوق رأس الراوي (ليموني)
- `Brushs/Brushs/Ajay GFX046.png` (1280x720 alpha): صاعقة بديلة أنحف
- `Brushs/Brushs/Ajay GFX333.png` (403x306 alpha): زجاج مكسور بثقب لمشهد جريمة (صغير: كعنصر لا كخلفية)
- `Brushs/Brushs/Ajay GFX255.png` (800x480 alpha): شقوق زجاج
- `Brushs/Brushs/Ajay GFX070.png` (1920x1155 alpha): علامات X متناثرة للنفي/الخطأ
- `Brushs/Brushs/Ajay GFX048.png` (1280x720 alpha): رأس سهم للإشارة
- `Brushs/Brushs/Ajay GFX224.png` (1280x720 alpha): دائرة هدف للتصويب على عنصر
- `Brushs/Brushs/Ajay GFX164.png` (750x750 alpha): دائرة HUD لشاشة مراقبة

### أشكال وماسكات (`shape-matte`)

- `Brushs/Brushs/Ajay GFX222.png` (800x480 alpha): شريط متوازي أضلاع لبطاقة اسم
- `Brushs/Brushs/Ajay GFX223.png` (800x480 alpha): مستطيل لخلفية وسم
- `Brushs/Brushs/Ajay GFX017.png` (1000x1000 alpha): شريط قطري لانتقال wipe
- `Brushs/Brushs/Ajay GFX016.png` (750x750 alpha): حلقة سميكة لتأطير رقم مرحلة
- `Brushs/Brushs/Ajay GFX020.png` (2560x1440 alpha): دائرة مصمتة لماسك صورة دائرية
- `Brushs/Brushs/Ajay GFX181.png` (2560x1440 alpha): موجة سفلية لماسك
- `Brushs/Brushs/Ajay GFX157.png` (1280x720 alpha): سداسيات مفرغة لخلفية تقنية
- `Brushs/Brushs/Ajay GFX173.png` (1920x1080 alpha): ماسك فتحات لعرض عدة صور

### فرش بيضاء (`brush-white`)

- `Brushs/Brushs/Ajay GFX038.png` (1280x720 alpha): ضربتا فرشاة لخلفية كلمة مفتاحية
- `Brushs/Brushs/Ajay GFX395.png` (1920x1080 alpha): ضربة فرشاة طويلة تحت عنوان فرعي
- `Brushs/Brushs/Ajay GFX225.png` (800x480 alpha): ضربة عريضة لكشف صورة
- `Brushs/Brushs/Ajay GFX226.png` (800x480 alpha): ضربة عريضة بديلة
- `Brushs/Brushs/Ajay GFX396.png` (1920x1080 alpha): دائرة فرشاة يدوية لتحويط عنصر
- `Brushs/Brushs/Ajay GFX121.png` (1920x1080 alpha): ضربة عمودية لماسك
- `Brushs/Brushs/Ajay GFX109.png` (1920x1080 alpha): رشة طلاء لظهور عنصر

### هافتون (`halftone`)

- `Brushs/Brushs/Ajay GFX111.png` (1280x720 alpha): تدرج نقاط لخلفية بطاقة اسم
- `Brushs/Brushs/Ajay GFX367.png` (720x712 alpha): دائرة هافتون خلف رقم أو سنة
- `Brushs/Brushs/Ajay GFX135.png` (1280x720 alpha): دائرة نقاط صغيرة
- `Brushs/Brushs/Ajay GFX230.png` (800x480 alpha): قوس نقاط زخرفي
- `تكتسشر/images (1) (28).jpeg` (612x408 opaque): تدرج نقاط على أبيض (multiply)

### برق (`lightning`)

- `Overlays/overlays8.jpg` (1920x1357 black→screen): برق في سماء زرقاء داكنة لمشهد عاصفة
- `Brushs/Brushs/Ajay GFX337.png` (1280x720 alpha): برق واقعي عمودي شفاف
- `Brushs/Brushs/Ajay GFX339.png` (1280x720 alpha): برق صغير في الزاوية

### جزيئات (باعتدال) (`particles-bokeh`)

- `Effets (Effects)/19.jpg` (1280x720 black→screen): جمر أحمر على أسود لمشهد حرب/حريق (screen)
- `Overlays/overlays18.jpg` (1280x720 black→screen): شرر انفجار على أسود
- `Overlays/overlays19.jpg` (1280x720 black→screen): جمر برتقالي
- `Effets (Effects)/PARTICULES_1.png` (2201x1240 black→screen): سماء نجوم لمشهد ليلي
- `Effets (Effects)/neige.png` (600x600 alpha): ثلج متساقط شفاف
- `Effets (Effects)/Skype_Picture-2.jpeg` (852x480 black→screen): بوكيه ذهبي خافت
- `Brushs/Brushs/Ajay GFX002.jpg` (612x466 black→screen): ريش متطاير على أسود

### ومضات (باعتدال) (`lens-flare`)

- `اضائة/mixo-6.png` (1421x1080 alpha): وهج عدسة أزرق كبير لومضة كشف
- `اضائة/mixo-4.png` (1920x1080 black→screen): لمعة نجمية زرقاء صغيرة
- `اضائة/mixo-11.png` (1920x1080 black→screen): وهج برتقالي بحلقات
- `اضائة/mixo-12.png` (830x240 black→screen): وهج أنامورفي سماوي رفيع
- `Effets (Effects)/brillo4.png` (500x500 alpha): لمعة رباعية بيضاء (صغيرة الدقة)

### جليتش (لسبب واضح فقط) (`glitch`)

- `Effets (Effects)/Glitch_Legend_14.jpg` (852x480 black→screen): كتل جليتش RGB على أسود لانقطاع شاشة مراقبة
- `Brushs/Brushs/Ajay GFX083.png` (1920x1080 alpha): أشرطة جليتش بيضاء شفافة
- `Overlays/overlays39.png` (1280x720 black→screen): ملمس رقمي أحمر لاختراق
- `اضائة/COREPACK (33).png` (1280x720 alpha): شرطات ضوء سماوية

### تسربات ضوء (نادراً) (`light-leak`)

- `اضائة/Light (2).png` (1920x1080 alpha): تسرب برتقالي في الزاوية يتماشى مع العنوان
- `اضائة/Light (7).png` (1920x1080 alpha): تسرب رمادي محايد
- `اضائة/Light (5).png` (1920x1080 alpha): تسرب أزرق لمشهد ليلي
- `اضائة/Brush Light (13).png` (1920x1080 alpha): تسرب أحمر أسفل الإطار (بحذر)

## تجنّب

- **الدم (gore):** مجلد `تأثيرات دم` كاملاً (132 ملفاً)، والرشات الحمراء في `Brushs`: `Ajay GFX399/401/402.png` و`Ajay GFX139.png` (تمزق مخالب أحمر) وسمها `gore`، و`Ajay GFX033/035/039/041/063/065/104.png` تشبه الدم وسمها `gore?`. ملفات `تأثيرات دم` سوداء في الأصل، لكن شكلها شكل الدم، فلا تستخدمها حتى كحبر.
- **علامات مائية:** `تكتسشر/image_search_1642348174307.jpg` (شعارات Freepik ظاهرة)، و`تكتسشر/images (25).jpeg` و`تكتسشر/images (6).jpeg` (علامات باهتة تظهر عند رفع التباين).
- **حقوق محتملة (`copyright?`):** `تكتسشر/istockphoto-1167399672-612x612.jpg` (معاينة iStock غير مرخصة)، و`تكتسشر/film-grain-texture-white-decay-footage-148776575_iconl.webp` (معاينة موقع صور)، و`Effets (Effects)/maxresdefault (2).jpg` (صورة مصغّرة منسوخة من يوتيوب)، وشعارا الأنمي `Brushs/Brushs/Ajay GFX231.png` (كونوها/ناروتو) و`Ajay GFX259.png` (فيري تيل).
- **أسلوب لا يناسب الهوية:** `neon-shape` و`energy-burst` و`speed-lines` و`sunburst-spiral` و`abstract-bg` و`gaming-frame` (منها `Effets (Effects)/EFFETS.jpg` بشارة LIVE، و`اضائة/image0-*.jpg` و`modif_color_ptdrtkt-3.jpg`)، و`paint-splash` و`misc` (قبعة YOLO `Ajay GFX342.png`، ونقش قطط `Overlays/overlays38.png`، وعين أنمي `Effets (Effects)/OVERLAY BY SUMAN (33).png`). والشكل الأحمر المخيف `Overlays/overlays20.png` لا يناسب القناة.
- **دقة منخفضة (`lowres`، 81 ملفاً أقصر من 600px):** لا تملأ بها البطاقة (1080×680). المقبول منها العناصر الصغيرة فقط.
- **نسخ مكررة (`dup`، 132 ملفاً):** أغلبها `تأثيرات/Designer Studio_effects_vid1 (*)` (نسخ من `اضائة/Light` و`Brush Light` و`Effets/Flare`)، وأرقام `اضائة` العارية (`25.png` = `25-1.png`...)، ونسخ داخل `Brushs`. عمود `desc_ar` يذكر الأصل، فاستخدم الأصل دائماً.
- **شبه فارغة (`uncertain`):** 8 ملفات شبه شفافة بالكامل أو باهتة جداً لا يظهر محتواها في الشيت.
- **التسربات والجزيئات والومضات** موجودة بكثرة، لكن المرجع لا يستخدمها تقريباً. لا تضعها على كل مشهد، فالقاعدة: لا جزيئات عشوائية ولا مؤثرات بلا سبب.
