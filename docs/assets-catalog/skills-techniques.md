# مهارات وتقنيات المونتاج من طرف ثالث (skills-techniques)

المجموعة فيها **1,318 ملفاً**، منها **583 محتوى فريداً فقط**، والباقي (735) نسخ مطابقة بايتاً ببايت. الجدول الكامل في `skills-techniques.tsv`، وفيه صف لكل ملف. عمود meta يذكر الحجم والتبعيات (deps) أو المقاس أو المدة، و`=dup:` يدل على النسخة الأصلية.

اختصارات المسارات في هذا الملف (استبدلها بالمسار الكامل عند التحميل):
- `VA/` = `video-ad-editor-main/video-ad-editor/`
- `SK/` = `مهارات مفيدة/`

**قرأت الملفات فقط، ولم أثبّت أو أشغّل شيئاً منها** (CLAUDE.md: هذه المجلدات مرجع تقني). فحصت الصور ومعاينات الحركات بالعين عبر أوراق لقطات، ولم أستمع إلى الصوتيات.

## ما الذي في المجموعة

| المصدر | ما هو | الرخصة |
|---|---|---|
| `video-ad-editor-main/` | بلقن **majed-video v5.1.0** لماجد الزعابي، وفيه 6 سكلات عربية خليجية: ريل من فيديو متحدث، وشرح بالموشن، وبودكاست، ومونتاج، وكفر وثمبنيل، ودافنشي. يعمل بـ ffmpeg وwhisper ومحرّك كانفس في كروم. نسخه المنتهية بـ`(1)` هي الإصدار الأقدم v4.4.2، ومجلد `video-ad-editor-main/video-ad-editor-main/` نسخة مكررة كاملة | MIT |
| `مهارات مفيدة/` | مجلد مسطّح فيه 18 سكلاً مختلطة، والفهرس في `SK/README.md`. أهمها: **we-viral-editing** (دليل وكالة مبني على 1,088 فيديو)، و**Community Reels Engine** (يعمل بـ **HyperFrames** ونسخته 0.8.58)، وعائلة **albert-reel** (بطاقات HTML/GSAP تُرندر بـ hyperframes)، و**youtube-clean**، و**open-edit** (يعمل بمحرّك VEED). وفيه نسخة قديمة v4.3.5 من سكل ماجد | MIT أو CC0 أو بلا رخصة معلنة، حسب السكل |

## الخلاصة: ما يستحق النقل إلى خط النيرد

الترتيب حسب فائدته لخطوات CLAUDE.md. كل الملفات **آمنة للقراءة**، ولا يُشغَّل أي منها كما هو: الأفضل نسخ الفكرة أو الدالة إلى `scripts/` عندنا بعد مراجعتها.

| # | التقنية | الملف | ماذا يفعل | التبعيات | الحكم |
|---|---|---|---|---|---|
| 1 | **حذف السكتات** (الخطوة 5.2) | `SK/silence_edl.py` + `SK/cutting.md` | يحوّل silencedetect إلى نطاقات كلام. الافتراضي ‎-40dB، وفجوة 0.35ث، وحشوة 0.12ث (0.45ث لآخر كلمة)، ويرفض ‎-32dB لأنه يأكل أواخر الكلمات. `cutting.md` يضيف: اقطع في قاع RMS قبل بداية الكلمة بـ30ms، وتجنّب الشظايا الأقصر من 0.8ث، وفرّق الشهيق عن الحرف الاحتكاكي بمعدل عبور الصفر (ZCR) | python3, ffmpeg | **صالح.** نضبطه على عتبة 300ms وتنفّس 120ms |
| 2 | **تجميع القطع بلا طقطقة** | `SK/cutjoin(1).py` | ترميز واحد بـ concat filter، وتلاشٍ 4ms عند كل وصلة. لا يستعمل `concat -c copy` لأنه يزيح الصوت | python3, ffmpeg | **صالح** للجزء الصوتي |
| 3 | **منع بتر آخر الكلمة** | `SK/refine_cuts.py`، `SK/build_edl.py` | يمدّ القطعة لأول سكتة بعد الكلمة، ويضع نقطة القص على أهدأ إطار 5ms | numpy | فكرة صالحة |
| 4 | **فحص القص بعد التصحيح** | `SK/verify_cut.py` | يكشف: الفجوات الأطول من 0.30ث، والكلمات بعرض صفر، والشظايا، والتكرار بنافذة 5 كلمات (محاولة متعثرة بقيت)، والفواتح المكررة ("يعني… يعني")، والنهاية المبتورة، ونقص جمل من السكربت | python3 | **صالح جداً** بعد تحويل words.json لصيغته |
| 5 | **هلوسات whisper العربية** | `VA/scripts/18_long_transcribe.py` | يقطّع الملف عند السكتات (~20ث)، ويحذف "اشتركوا في القناة" و"ترجمة نانسي قنقر"، ويعيد تفريغ الفجوات الأطول من 7ث | whisper, numpy | الفكرة والقائمة صالحتان لخطوة 5.4 |
| 6 | **كابشن عربي** | `SK/captions.md`، `SK/captions(1).py`، `VA/scripts/02_captions.py` | قواعد RTL: الكلمة تتحرك كاملة، و`<bdi>` للأسماء اللاتينية والأرقام، وتباعد أسطر أكبر، وتقديم النص 0.13ث على الصوت. التقسيم يكسر العبارة عند فجوة ≥250ms أو علامة ترقيم (منها ؟). و`02_captions.py` يبقي توقيت whisper ويستبدل النص المصحّح، وهي قاعدتنا نفسها | python3 | **صالح.** نأخذ القواعد وخوارزمية التقسيم، أما الحرق فنعمله بـ HyperFrames لا ASS |
| 7 | **SRT ليوتيوب** | `VA/scripts/09_srt.py` | يحوّل الكابشن إلى SRT (سطران، 42 حرفاً) ونص كامل للوصف | python3 | صالح بتحويل بسيط |
| 8 | **معايرة العلو والدكينغ** (الخطوة 5.3، والموسيقى) | `SK/mix_audio.py`، `VA/scripts/06b_master.sh`، `VA/scripts/06c_loudfix.sh` | loudnorm بمرورين (قياس ثم linear)، وتخفيض الموسيقى بـ sidechaincompress أثناء الكلام، وalimiter بـ level=false، والفيديو يُنسخ دون إعادة ترميز. و`06c` يضغط ضغطاً خفيفاً إن علق العلو تحت الهدف | python3/bash, ffmpeg | **صالح** مع `--target -16 --tp -1 --duck`، والموسيقى عند نحو ‎-28 LUFS. افتراضيهم ‎-14 فلا تأخذه |
| 9 | **تنظيف صوت محافظ** | `VA/scripts/02c_denoise.py` (المسار الاحتياطي) | highpass 80Hz، ثم afftdn nf=-28، ثم ضغط خفيف. وDeepFilterNet3 اختياري | ffmpeg (+deep-filter) | سلسلة ffmpeg صالحة |
| 10 | **ورقة لقطات** (التسليم وفحص snapshot) | `VA/scripts/07_contact_sheet.sh`، `VA/scripts/32_midframes.py`، `SK/contact_sheet.py` | ورقة 3×2 عليها التوقيتات بـ PIL، ولقطة من **منتصف كل مشهد**، وورقة 12 إطاراً تقيس عدد القطعات في الدقيقة والعلو | ffmpeg, PIL | **صالح.** لقطة منتصف كل مشهد في STORYBOARD أفضل من لقطات عشوائية |
| 11 | **فحص ملف التصدير** | `SK/qc.py` | يفحص المقاس وfps والترميز وfaststart والعلو، ويطبع PASS/WARN/FAIL | ffmpeg | صالح على final.mp4 وfinal_send.mp4 |
| 12 | **فحص المنطقة الآمنة آلياً** | `VA/scripts/08_safe_check.js` | يرسم كل لحظة مرتين بلونين مسطّحين مكان الفيديو، فما لا يتغيّر بين الرسمتين هو الرسم نفسه. ثم يعدّ بكسلاته داخل مناطق الأزرار. الحدود في safe.json | node, puppeteer, Chrome | **التقنية صالحة**، تُطبَّق على snapshot HyperFrames بحدودنا (y<200، y>1480، x>900 مع y>850) |
| 13 | **صور حرّة من ويكيميديا** (المصدر B) | `VA/scripts/13_assets.py` | يبحث في Commons ويقبل PD وCC0 وCC BY وCC BY-SA فقط، ويكتب JSON بالرابط والمؤلف والرخصة، ويقصّ الخلفية بـ rembg اختيارياً | python3 (+rembg) | **صالح.** يملأ SOURCES.md تلقائياً |
| 14 | **بحث بالمعنى داخل فيديوهات الحلقة** | `VA/scripts/26_find_shots.py` | SigLIP2 محلي: تكتب وصفاً بالإنجليزية فيرجع أقرب اللقطات مع ورقة نتائج | torch, transformers (~1.5GB) | مفيد مع مجلد حلقة كبير، لكنه ثقيل التنزيل |
| 15 | **الصورة المصغّرة على الجوال** | `VA/scripts/34_phone_preview.py` + `VA/references/thumbnails.md` | يعاين الصورة بحجمها الحقيقي على شاشة الجوال. أحجام مقاسة: الكفر يُعرض بنحو 12%، وأصغر نص مقروء 81-91px | PIL فقط | **صالح مباشرة** |
| 16 | **تركيبة HyperFrames جاهزة** | `SK/composition.py`، `SK/motion.js`، `SK/stage.css` | يولّد index.html لـ HyperFrames: `@font-face` محلي، وكابشن `clip` بـ data-start وdata-duration وdir، وخط زمني GSAP واحد متوقف وقابل للبحث، وشريط تقدّم scaleX | python3, GSAP | **أقرب كود لمشروعنا** (CC0). بُني على 0.8.58 فتحقّق من التوافق مع 0.8.183. GSAP رخصته منفصلة |
| 17 | **أخطاء HyperFrames المعروفة** | `SK/albert-reel/SKILL.md` (جدول الأخطاء) | npx ETARGET، والإيموجي في الكروم بلا واجهة، والإخراج yuv420p بلا ألفا | — | مرجع مفيد |
| 18 | **قواعد الحركة** | `VA/references/motion-rules.md`، `SK/motion-design.md` | ease-out للدخول خلال 0.15-0.30ث، ولا تكبير من صفر، وتتابع 30-80ms، وأرقام tabular في العدّادات. ممنوع: حرف بحرف، والتوهج، والارتداد. ولكل رقم مصدر في facts.md. و3 عناصر كحد أقصى على الشاشة | — | **متوافقة مع هويتنا** |
| 19 | **مؤثرات بلا حقوق** | `VA/scripts/05_sfx.py` | يولّد whoosh وthud وtap وriser وsub وتكات عدّاد رياضياً بـ numpy | numpy | بديل طوارئ فقط، فمكتبة Motion Pro أفضل |

## الفئات

العدد = كل الصفوف / الفريد منها.

| category | العدد | ما هي | متى تستخدمها القناة | الحكم |
|---|---|---|---|---|
| silence-cut | 18 / 8 | كشف السكتات وبناء EDL وتحديد نقاط القص | الخطوة 5.2 (voice_tight) | **مفيد** |
| cut-assembly | 17 / 7 | تجميع القطع بلا انحراف تزامن | تجميع voice_tight | مفيد (`cutjoin`) |
| cut-verify | 19 / 9 | فحص الفجوات والتكرار والوصلات | بعد تصحيح الكلمات | **مفيد** (`verify_cut`) |
| transcription | 18 / 7 | ناسخات ElevenLabs وGroq وfaster-whisper | لدينا ناسخ محلي، فنأخذ الأفكار فقط | مرجع |
| arabic-captions | 33 / 16 | بناء الكابشن وقواعد RTL والكشيدة وSRT | الخطوة 7 وSRT | **مفيد** (قواعد وخوارزمية) |
| loudness-mix | 18 / 7 | loudnorm بمرورين، وducking، والترميز | الخطوة 5.3 والموسيقى | **مفيد** |
| voice-cleanup | 12 / 3 | إزالة الضجيج (محلياً أو بأدوبي) | تنظيف محافظ | جزئي |
| sfx-placement | 12 / 4 | توليد المؤثرات وتوقيتها بالكود | نادراً (حدّنا 3 مؤثرات) | مرجع |
| sfx-sample | 19 / 7 | 7 أصوات قصيرة (نقرة، وشش، ضربة) | نادراً | 4 منها مولّدة بالكود وحرّة، و3 رخصتها غير مؤكدة |
| music-bed | 4 / 1 | موسيقى افتراضية "placeholder" | لا | **تجنّب** |
| qc-contact-sheet | 21 / 10 | أوراق لقطات وفحص التصدير والإضاءة | قبل التسليم | **مفيد** |
| safe-zone | 7 / 3 | فحص المنطقة الآمنة | فحص snapshot | **مفيد** (التقنية) |
| thumbnail-cover | 24 / 7 | الكفر والثمبنيل ومعاينة الجوال | فكرة الصورة المصغّرة | مفيد جزئياً |
| image-sourcing | 16 / 4 | جلب صور ويكيميديا والبحث بالمعنى | المصدر B واختيار اللقطة | **مفيد** |
| archival-photo | 12 / 3 | 3 صور أرشيفية بالأبيض والأسود، ملكية عامة | حلقات تاريخ التقنية والفضاء | **صالحة** |
| hyperframes-engine | 32 / 32 | Community Reels Engine (CC0): مولّد تركيبة HyperFrames وأساليبه وعيّناته | قالب لبنية المشروع | **مفيد** |
| hyperframes-cards | 51 / 21 | مولّدات بطاقات HTML/GSAP لريلز ألبرت | أمثلة كود GSAP | مرجع |
| motion-engine | 99 / 40 | محرّك ماجد (كانفس) وحزمة الموشن ومكتبة الحركات | أفكار عناصر وقواعد | مرجع، وليس HyperFrames |
| motion-preview | 200 / 100 | معاينة 4ث صامتة لكل حركة من الـ100 (540×960) | اختيار فكرة حركة | مرجع (المفيد منها أدناه) |
| editing-playbook | 17 / 16 | دليل وكالة We Viral: القص، والأسلوب، والهندسة | قواعد عامة | مفيد (`cutting.md` و`engineering.md`) |
| ai-review | 8 / 8 | مراجعة بـ Gemini وبرومبتاتها | لا، نراجع بأعيننا | يحتاج مفتاحاً |
| ai-generation | 24 / 10 | مشاهد مولّدة (fal)، وأفاتار، وTTS، وHiggsfield | لا | **ممنوع** |
| talking-head | 112 / 38 | أدوات لمتحدث مصوَّر: قص الوجه والرأس، وبودكاست، وكولاج | لا (فراس صوت فقط) | لا يناسب |
| screen-demo | 35 / 16 | تسجيل شاشة وأجهزة 3D وتصوير مواقع | نادراً في حلقات التقنية | مرجع |
| montage-beat | 20 / 5 | مونتاج على الإيقاع | لا | لا يناسب |
| editor-integration | 97 / 39 | دافنشي، وCapCut، وRemotion، والاستوديو، وصفحات التعارف والمراجعة | لا | لا يناسب |
| font | 59 / 16 | 14 ملف خط برخصة OFL، وملفا رخص | لا (IBM Plex موجود في brand/) | تجنّب الباقي |
| brand-logo | 38 / 29 | شعارات شركات (Apple وOpenAI وMeta وGitHub…) | حلقة تقنية تذكر الشركة بالاسم فقط | علامة تجارية |
| promo-screenshot | 68 / 31 | صور تسويق وتوثيق بوجه صاحب السكل | لا | **تجنّب** |
| skill-doc | 39 / 24 | SKILL وREADME وSETUP لكل سكل | قراءة فقط | مرجع |
| setup-infra | 65 / 36 | سكربتات التثبيت والحزم والرخص والأدلة | لا | لا تشغّلها |
| vendor-lib | 104 / 26 | three.js (MIT) وlottie | لا | لا يلزم |

## أفضل الملفات لكل فئة

### silence-cut / cut-assembly / cut-verify
- `SK/silence_edl.py`: عتبات آمنة (‎-40dB، و0.35ث، و0.12ث)، ويرفض الإعدادات التي تبتر الكلمات.
- `SK/cutting.md`: أفضل وصف مكتوب لقص صوت متحدث: آخر محاولة تفوز، والقص في قاع RMS، ولا فجوة أطول من 0.30ث.
- `SK/cutjoin(1).py`: تلاشٍ 4ms عند الوصلات، وconcat filter.
- `SK/refine_cuts.py`: يمدّ القطعة حتى لا يُؤكل آخر الكلمة.
- `SK/verify_cut.py`: فحص التكرار والفجوات ومطابقة السكربت.
- `VA/scripts/19_seam_check.py`: يعيد تفريغ ±4ث حول كل وصلة.
- `SK/said_twice_check.py`: يكشف الجملة المعادة بإعادة صياغة (يحتاج تعديل المسارات).
- `VA/scripts/10_script_edit.py`: دالة كشف الجمل المعادة مع تطبيع عربي (الهمزات والتاء المربوطة).

### arabic-captions / transcription
- `SK/captions.md`: قواعد RTL و`bdi`، وتوحيد الأرقام، وتقديم النص 0.13ث.
- `SK/captions(1).py`: خوارزمية تقسيم العبارات (الكسر عند فجوة ≥250ms أو ترقيم).
- `VA/scripts/02_captions.py`: تصحيح الكلمات مع إبقاء توقيت whisper، وتوزيع نسبي عند الهلوسة.
- `VA/references/word-fx.md`: قواعد الكشيدة الصحيحة (بعد حرف يتصل فقط، وبعد التشكيل).
- `VA/scripts/09_srt.py`: ملف SRT.
- `VA/scripts/18_long_transcribe.py`: قائمة هلوسات whisper العربية، والتقطيع عند السكتات.

### loudness-mix / voice-cleanup / sfx
- `SK/mix_audio.py`: كل السلسلة في أمر واحد (‎--target ‎-16 ‎--tp ‎-1 ‎--duck).
- `VA/scripts/06b_master.sh`: loudnorm بمرورين، وsidechain.
- `VA/scripts/06c_loudfix.sh`: علاج القمم التي تمنع بلوغ الهدف.
- `SK/engineering.md`: alimiter بـ level=false، وamix بـ normalize=0، وzscale لصور HDR.
- `VA/scripts/02c_denoise.py`: سلسلة ffmpeg محافظة.
- `SK/mix_section.py`: قواعد مستوى المؤثر (whoosh عند ≈‎-31dBFS، ولا مؤثر في أول ثانية ولا آخرها).
- `VA/scripts/05_sfx.py`: مؤثرات مولّدة بلا حقوق (للطوارئ).

### qc-contact-sheet / safe-zone / thumbnail-cover
- `VA/scripts/07_contact_sheet.sh`: ورقة 6 لقطات عليها التوقيت.
- `VA/scripts/32_midframes.py`: لقطة من منتصف كل مشهد.
- `SK/contact_sheet.py`: 12 إطاراً، ومعدل القطعات، والعلو.
- `SK/qc.py`: مواصفات الملف وfaststart.
- `VA/scripts/25_scopes.py`: يكشف اللقطة الأرشيفية المظلمة أو الباهتة.
- `VA/scripts/08_safe_check.js`: تقنية الرسم مرتين بلونين.
- `VA/scripts/34_phone_preview.py`: معاينة الصورة المصغّرة بحجم الجوال.
- `VA/references/thumbnails.md`: أحجام نص مقاسة.

### image-sourcing / archival-photo
- `VA/scripts/13_assets.py`: ويكيميديا مع فلتر الرخص وملف المصدر.
- `VA/scripts/26_find_shots.py`: بحث بالمعنى داخل الفيديوهات.
- `VA/scripts/collage-assets/bug_note.jpg` (1728×669): سجل هارفارد 1947 و"أول حشرة حاسوب"، ملكية عامة.
- `VA/scripts/collage-assets/mcc_bw.jpg` (1536×1178): غرفة التحكم بمهمة أبولو 13، من ناسا، ملكية عامة.
- `VA/scripts/collage-assets/cards_bw.jpg` (1536×1213): مخزن بطاقات IBM المثقّبة، من الأرشيف الوطني الأمريكي، ملكية عامة. مصادرها في `VA/scripts/collage-assets/LICENSES.md`.

### hyperframes-engine / hyperframes-cards / motion
- `SK/composition.py`: مولّد index.html لـ HyperFrames مع كابشن بـ dir.
- `SK/motion.js`: خط GSAP واحد حتمي، وشريط تقدّم.
- `SK/faceless.md`: "قِس توقيت السرد الحقيقي ولا تقدّره من سرعة القراءة".
- `SK/styles.md`: الكلمات العربية كاملة، و`bdi`، وإبعاد الكابشن عن عمود الأزرار.
- `SK/gen.py` و`SK/card-snippets.md`: نمط ربط كل بطاقة بكلمة من التفريغ ثم رندر HyperFrames.
- `VA/references/motion-rules.md`: قواعد الحركة وقائمة الحقائق.
- `VA/scripts/motion-kit.js`: أفكار العدّاد odometer والختم المائل (تُعاد كتابتها بـ GSAP).
- `VA/motion/moves/catalog.json`: أسماء الحركات المئة ووصفها بالعربي.

**معاينات حركات تفيد النيرد** (في `VA/motion/moves/previews/NN.mp4`، تُعاد بـ GSAP):

| # | الحركة | الاستخدام |
|---|---|---|
| 07 | عدّاد | سنة أو رقم كبير |
| 16 | قلم تحديد | خلف الكلمة المفتاحية، بلون الموضوع |
| 24 | غمضة لون | التعتيم المسموح (6 فريمات) عند تغيّر الفصل |
| 26 | عقرب الساعة | الزمن ("بعد ساعة") |
| 32 | كين بيرنز | الصور الثابتة |
| 44 | اسم وتعريف | بطاقة الاسم |
| 45 | قائمة صح | المراحل ①② |
| 49 | حلقة نسبة | النسب المئوية |
| 50 | أعمدة تكبر | المقارنات |
| 62 | نقاط تنزل | حركة عربية أصيلة |
| 68 | شعاع الربط | شبكة علاقات في قضية |
| 69 | صفحة كتاب عربي | التاريخ |
| 73 | الحقيقة تنكشف | أشرطة حبر وختم "سري"، للجرائم والألغاز |
| 77 | خريطة نقاط | أقواس ودبابيس، للجغرافيا والحروب |
| 83 | خط يرتسم | الرسوم البيانية |
| 87 | خط المسح | قبل وبعد |

حركات **مخالفة** لقاعدة القطع الحاد أو لمنع الدوران والزوم المموّه: 8، 9، 10، 11، 14، 25، 27، 29، 30، 37، 51، 75، 76، 82، 92، 97، 99. وحركة 28 (قلتش) لمواضيع الاختراق فقط.

## الخطوط والصور والصوتيات المرفقة

- **الخطوط (14 ملفاً، كلها OFL). نصوص الرخص لتسعة منها في `VA/motion/fonts/LICENSES.txt`، أما Montserrat فلا يرافقه ملف رخصة:**
  - IBM Plex Sans Arabic بوزنين: Bold وRegular. **مطابقان بايتاً ببايت لما في `brand/fonts`**، فلا تحمّلهما. ولا يوجد SemiBold هنا.
  - **Cairo-VF، وهو ممنوع في الهوية.**
  - البقية خارج الهوية: Tajawal (Black وBold وRegular)، وLalezar، وNoto Kufi Arabic، وReadex Pro، وAref Ruqaa (Bold وRegular)، وAmiri Quran، وInter، وMontserrat.
- **صور:**
  - 3 صور أرشيفية صالحة (أعلاه).
  - 29 شعار شركة، بين 180 و640px، علامات تجارية.
  - 31 صورة تسويق أو توثيق، أغلبها بوجه صاحب السكل، وفي بعضها شعارا zorcha وmanychat.
  - `wave.png`: موجة صوتية برتقالية.
- **فيديو:**
  - 100 معاينة حركة: 4ث، 540×960، 60fps، صامتة.
  - 6 عيّنات من Community Reels: 8ث، 1080×1920، اصطناعية وبرخصة CC0.
- **صوت:**
  - `tap.wav` و`thud.wav` و`whoosh_up.wav` و`whoosh_down.wav`: من 0.09 إلى 0.34ث، مولّدة بالكود فهي حرّة الحقوق.
  - `caption-mouse-down.wav` و`first-click.wav` و`whoosh-snap.mp3`: رخصتها غير مؤكدة.
  - `bg-music.m4a`: نحو 5:03، وهو **placeholder** حسب README، ورخصته مجهولة.
- **أرشيف:** `video-ad-editor.skill` حزمة zip للسكل. لا تثبّتها ولا تفكّها.

## ما يحتاج مفاتيح API أو حسابات خارجية

| الخدمة | الملفات |
|---|---|
| ElevenLabs Scribe | `SK/albert-reel/scripts/transcribe.py`، و`SK/transcribe(1).py` (يرجع إلى faster-whisper المحلي إن لم يجد المفتاح)، وسكل youtube-clean (`SK/SKILL (11).md`) |
| Groq | `SK/transcribe_groq.py` |
| Google Gemini (`GEMINI_API_KEY`) | `SK/gemini.py`، و`SK/.env.example`، وسكلا community-eye وcommunity-decode، وبرومبتات `analyze.md` و`review.md` و`decode.md` |
| fal.ai (`FAL_KEY`، مدفوع) | `VA/scripts/17_gen_scenes.py`، و`VA/scripts/21_avatar_scene.py` |
| Higgsfield MCP | famous-reel-editor، وalbert-reel وalbert-reel-white وalbert-reel-white-screen (لقطات B-roll)، وyoutube-broll-maker، وyoutube-popup-graphic، وyoutube-clipper |
| حساب VEED | open-edit (`SK/SKILL(1).md`، و`CUT.md`، و`GENERATION.md`، و`TRANSCRIPTION.md`، و`DESIGN.md`، و`STYLE(1).md`، و`preflight.sh`) |
| كونكتور Adobe | `VA/scripts/02b_enhance_audio.sh` (المسار الأول فيه) |
| خدمة zorcha (اشتراك) | `VA/references/keyword-automation.md` |
| برامج مدفوعة | DaVinci Resolve Studio (`VA/scripts/davinci/*`)، وCapCut Desktop (`40_capcut.py`) |
| تنزيلات ثقيلة دون حساب | SigLIP2 (~1.5GB، `26_find_shots.py`)، وDeepFilterNet (`02c_denoise.py`)، وRemotion (~500MB) |

## ما يجب تجنّبه

- **لا تثبّت ولا تشغّل** `video-ad-editor.skill` ولا `00_setup.sh` ولا `build-release.sh` ولا `preflight.sh`. ولا تجعل ملفات `SK/CLAUDE.md` و`SK/AGENTS.md` و`ASSISTANT-PLAYBOOK.md` تلغي CLAUDE.md الخاص بالنيرد.
- **أدوات ماك فقط** (92 صفاً، علامتها `mac-only`): ملفات Swift التي تعتمد Vision (قص الشخص والوجه واليد، وhdr2sdr) لا تعمل على جهازنا (لينكس).
- **TTS ممنوع:** `VA/motion/voice.py` (edge-tts) وسكل motion-video.
- **افتراضيات تخالف هويتنا:**
  - العلو ‎-14 LUFS، وهدفنا ‎-16.
  - كابشن كاريوكي كلمة بكلمة بخط Montserrat.
  - كبسولات ملوّنة.
  - ارتداد.
  - "15 مؤثراً في الدقيقة" ونقرة تحت كل كابشن، وحدّنا 3 مؤثرات في الفيديو كله.
  - انتقالات الونشوت والزوم والقلتش.
  - صفحات التعارف والمراجعة، وأسئلة المستخدم، وبوابات الموافقة.
- **الحقوق:**
  - `bg-music.m4a` و3 أصوات youtube-clean عليها `copyright?`.
  - الشعارات عليها `trademark`، ولا تُستخدم إلا للإشارة إلى شركة مذكورة بالاسم.
  - صور `_pkg` و`img` عليها `promo`: وجه شخص حقيقي، وبانرات دورة مدفوعة.
- **النسخ:**
  - 735 صفاً `duplicate`.
  - 57 صفاً `old-version` (36 منها فريدة المحتوى): v4.3.5 في `SK/`، وv4.4.2 في الملفات المنتهية بـ`(1)` داخل `VA/`. استخدم دائماً النسخة غير المرقّمة في `VA/`.
- ملفات `compose_cfg-*.json` و`windows-*.json` فيها مسارات من جهاز صاحبها، ولا فائدة منها.
- **لا يوجد** دم ولا عنف، ولا روابط y2mate، ولا علامات مائية على صور قابلة للاستخدام.

## حدود الفحص

- لم أشغّل أي سكربت، فالأوصاف مأخوذة من رؤوس الملفات ومن الكود والتوثيق.
- لم أستمع إلى الصوتيات: الأوصاف من مولّد الكود (`05_sfx.py`) ومن أسماء الملفات ومدتها.
- لكل معاينة حركة نظرت إلى إطار واحد، وطابقته مع `catalog.json`.
- ملفات SVG الأربعة لم تُرسم في ورقة اللقطات، وتعرّفتها من أسمائها ومسارها `albert-reel/assets/logos`.
