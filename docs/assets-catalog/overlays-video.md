# مكتبة الطبقات والانتقالات (Overlay + أيقونات متحركة)

المجموعة: كل الفيديوهات في `13 - أكثر من 6300 ملحق للمونتاج مجاني/Overlay/` (152 ملفاً)، والفيديوهات والـ gif والـ webm في `.../ايقونات/` (36 ملفاً: 18 mp4 و4 webm و14 gif). المجموع **188 ملفاً**. الجدول الكامل ملف بملف في `overlays-video.tsv`.

## الخلاصة

- **الحكم:** 19 ملفاً مناسباً، و93 محدود الاستخدام، و76 للتجنّب. أغلب المجلد حروق فيلم وتسرّبات ضوء وglitch صاخبة، وكلها ممنوعة في أسلوب النيرد (الافتراضي قطع حادّ).
- **ما يصلح فعلاً:** حبيبات وغبار وخدوش فيلم خافتة، وإطارات عرض أرشيفية، وضباب أو ثلج أو عاصفة لمشهد بعينه، وأسهم ودوائر مرسومة باليد (تُلوَّن بالأحمر `#C33B3F`).
- **لا شفافية في مجلد Overlay:** كل الملفات بلا قناة ألفا. الخلفية السوداء تُدمج بـ `screen`، والبيضاء بـ `multiply`، والرمادية بـ `overlay`/`soft-light`، والخضراء تحتاج مفتاح لون. الشفافية الحقيقية موجودة فقط في 4 ملفات webm من الأيقونات (VP9 alpha).
- **المقاس:** كلها 16:9 أفقية (غالباً 1280x720) عدا ملف عمودي واحد. هذا يناسب **بطاقة المشهد 1080x680** (قصّ بسيط بـ `object-fit: cover`)، ولا يناسب ملء الشاشة 1080x1920.
- **العلامات والحقوق:** 81 ملفاً فيها بطاقات قنوات يوتيوب ("Think Make Push"، أو "NEW OVERLAYS EACH WEEK"، أو أزرار اشتراك، أو RUSH.FX، أو AVFX). و162 ملفاً منزّلة على الأرجح من يوتيوب (`(720P_HD)` و`y2mate.com` وعناوين يوتيوب)، أو من Envato Elements (أسماء تنتهي بتاريخ `-utc`)، أو أيقونات بأسلوب Flaticon (غالباً تحتاج نسب الحقوق). ولا يوجد دم حقيقي، لكن `GRUNGE Film Overlay Effect` رذاذه الأحمر يشبه الدم.
- **الصوت:** ملفات كثيرة اسمها "with SOUND" وفيها مؤثرات (عارض أفلام، whoosh). **اكتم صوتها دائماً** (`muted`)، فالمؤثرات تُختار من مكتبة الصوت ضمن حدّ 3 مؤثرات للفيديو.

## طريقة الاستخدام في HyperFrames

- ضع الطبقة `<video muted loop playsinline>` داخل بطاقة المشهد فوق الصورة، مع `object-fit: cover` و`mix-blend-mode` حسب عمود blend في الـ TSV، وشفافية 15–40%.
- **قصّ بطاقات القنوات:** في عمود meta قيمة `trim≈a-b s` تقريبية لكل ملف معلَّم. نمط Think Make Push: أول 5.5 ثانية بطاقة كحلية، وآخر 5–9 ثوانٍ صورة ختام عليها الشعار. نمط NEW OVERLAYS: أول 2–3 ثوانٍ وآخر 3–5 ثوانٍ. **راجع أول وآخر فريم بعد القص بلقطة snapshot.**
- **تلوين الخطوط اليدوية بالأحمر:** `ffmpeg -i in.mp4 -an -vf "colorchannelmixer=rr=0.765:gg=0.231:bb=0.247" out.mp4` يحوّل الأبيض إلى `#C33B3F` ويُبقي الأسود أسود، ثم استخدم `screen`.
- **الشاشة الخضراء:** فرّغها مسبقاً إلى webm بشفافية: `ffmpeg -i in.mp4 -an -vf "chromakey=0x158C30:0.15:0.05,format=yuva420p" -c:v libvpx-vp9 out.webm`. الأخضر مقاس من الملفات: الدخان `Fumaça` ≈ `0x158C30`، و`VHS Overlay Green Screen` ≈ `0x06B400`، و`Aesthetic Overlay Green Screen` ≈ `0x00AF3F`، وإطارات `Matte Boxes` ≈ `0x08FD08`.
- **"انتقال" مسموح وحيد:** dip إلى الأسود 6 فريمات عند تغيّر الفصل، ويُبنى في HTML ولا يحتاج ملفاً من هنا. لا تستخدم حروق الفيلم أو glitch أو الوهج كانتقالات.

## الفئات

| category | العدد | الشكل | متى تستخدمه القناة | الحكم |
|---|---|---|---|---|
| `film-grain-dust` | 16 | حبيبات فيلم، وغبار، وشعيرات، وخدوش على أسود أو أبيض أو رمادي | طبقة دائمة خفيفة فوق المشاهد الواقعية والأرشيفية (شفافية 15–30%) | ✅ الأهم |
| `film-gate-frame` | 10 | نافذة عارض أفلام، وحواف شريط فيلم وثقوب، وإطارات مقسّمة، وتعتيم حواف | صورة أرشيفية قديمة داخل البطاقة، أو مقارنة 4 صور | 🟡 محدود |
| `weather-atmosphere` | 6 | ضباب، وغبار في شعاع ضوء، وثلج، وعاصفة وبرق | جو مشهد بعينه (غموض، أو شتاء، أو ليلة عاصفة) | ✅ حسب الموضوع |
| `hand-drawn-marks` | 4 | أسهم ودوائر ومربعات وخربشات بالطباشير الأبيض تُرسم | الدائرة أو السهم الأحمر على الشخص المقصود بعد التلوين | ✅ الأفضل منها اثنان |
| `particles-fire` | 10 | شرر، وجمر، ولهب حقيقي، وجزيئات ذهبية | مشهد حريق أو حرب فقط، بشفافية منخفضة | 🟡 محدود |
| `shapes-flares-hud` | 11 | خطوط سداسية، ومدارات منقطة تقنية، ووهج عدسة، وزجاج يتحطم | خلفية خافتة لموضوع تقني أو فضائي، أو لحظة كسر محددة | 🟡 محدود |
| `glitch-vhs-static` | 10 | تشويش تلفاز، وأشرطة ألوان، وخطوط CRT، وglitch رقمي، ونيون | داخل إطار "شاشة كاميرا" أو تلفاز قديم فقط، كعنصر من القصة | ⛔ غالباً |
| `film-burn-leak` | 63 | حروق فيلم وتسرّبات ضوء ملونة وساطعة | لا شيء تقريباً؛ ربما ضوء دافئ خافت جداً في لحظة كشف | ⛔ ممنوع |
| `film-leader-countdown` | 13 | عدّ تنازلي، وحروف ونصوص بداية الفيلم، وعلامات حرق السيجارة | لا (القناة تبدأ بالخطّاف مباشرة وبلا مقدمة) | ⛔ ممنوع |
| `greenscreen-chroma` | 5 | شاشات خضراء: دخان، وإطارات matte، وشاشة VHS "PLAY" | دخان أو "تشغيل شريط" بعد التفريغ | 🟡 محدود |
| `tutorial-compilation` | 4 | دروس يوتيوب وتجميعات بشعارات | لا | ⛔ ممنوع |
| `animated-icon` | 36 | أيقونات خطية متحركة (أسود + تركوازي) على أبيض، و4 بشفافية | نادراً: أسلوبها يخالف رسوم القناة المسطحة ذات الحدّ الأبيض | 🟡 ضعيف |

## أفضل الملفات لكل فئة

### `film-grain-dust`

| الملف | meta | لماذا |
|---|---|---|
| `13 - أكثر من 6300 ملحق للمونتاج مجاني/Overlay/Noise new.mp4` | 30.0s 1920x1080 30fps alpha=no blend=overlay audio | أنظف لوح حبيبات (رمادي متوسط، 1080p، 30 ثانية): `overlay` بشفافية 10–20% فوق البطاقة كلها |
| `13 - أكثر من 6300 ملحق للمونتاج مجاني/Overlay/Film Noise.mp4` | 8.2s 1920x1080 25fps alpha=no blend=overlay audio | حبيبات وخدوش على رمادي فاتح، 1080p، حلقة 8 ثوانٍ: `soft-light` |
| `13 - أكثر من 6300 ملحق للمونتاج مجاني/Overlay/Dust.mov` | 60.0s 1920x1080 30fps alpha=no blend=screen audio | غبار وخدوش عمودية عابرة على أسود، 1080p، 60 ثانية، بلا علامات: `screen` |
| `13 - أكثر من 6300 ملحق للمونتاج مجاني/Overlay/4K_Dirt_vintage_film_dust_hair_damage_35mm_footage_FREE_noise_overlay.mp4` | 10.4s 1280x676 30fps alpha=no blend=screen audio | غبار وشعيرات 35mm واضحة لكنها هادئة |
| `13 - أكثر من 6300 ملحق للمونتاج مجاني/Overlay/Grunge Elements.mp4` | 10.0s 1892x1080 30fps alpha=no blend=screen | غبار وشعيرات خافتة جداً، 1080p، بلا علامات |
| `13 - أكثر من 6300 ملحق للمونتاج مجاني/Overlay/فيلم_سينمائي_قديم_بدقة_4K_🎞_تأثير_تراكب_مجاني_🎞_الغبار_والحبوب_لمحرري.mp4` | 160.2s 1280x720 30fps alpha=no blend=overlay audio | نسيج سينما قديمة رمادي داكن مع خدوش ترتعش (دقيقتان و40 ثانية) |
| `13 - أكثر من 6300 ملحق للمونتاج مجاني/Overlay/Old_Film_Grain_Overlay_Black_and_White_Grain_4K_Snowman_Digital720P.mp4` | 120.1s 1280x720 25fps alpha=no blend=screen audio | غبار وخدوش مع تعتيم حواف مدوّر لصور الأرشيف |
| `13 - أكثر من 6300 ملحق للمونتاج مجاني/Overlay/y2mate.com - part 2 Free amazing video effect dust cinematic textureفديو للمونتاج مؤثراتنقاط سوداء تطير للتصميم_1080p.mp4` | 50.1s 1920x1080 25fps alpha=no blend=multiply audio | غبار داكن على أبيض: `multiply` فوق المشاهد الفاتحة |
| `13 - أكثر من 6300 ملحق للمونتاج مجاني/Overlay/Particle_01.mp4` | 11.0s 3840x2160 30fps alpha=no blend=screen | ذرات غبار وbokeh تطفو على كحلي (4K) لجو ليلي هادئ |
| `13 - أكثر من 6300 ملحق للمونتاج مجاني/Overlay/the_BEST_film_damage_OVERLAY_grain_dust_scratches720P_HD.mp4` | 30.1s 1280x720 24fps alpha=no blend=multiply audio trim≈5.5-27.0s | غبار بنسختين (أبيض وأسود)؛ استخدم المقطع بين 5.5 و27 ثانية فقط |

### `film-gate-frame`

| الملف | meta | لماذا |
|---|---|---|
| `13 - أكثر من 6300 ملحق للمونتاج مجاني/Overlay/FREE old FILM OVERLAY with SOUND FX_(720P_HD).mp4` | 600.6s 1280x720 24fps alpha=no blend=screen audio | حواف شريط فيلم داكنة على الجانبين (10 دقائق) تعطي إحساس الأرشيف دون أن تغطي الصورة |
| `13 - أكثر من 6300 ملحق للمونتاج مجاني/Overlay/y2mate.com - تأثير الفيلم القديم فى البريمير  HD Old Film Effect كروما سينما رهيبه للمونتاج مؤثرات افلام قديمة_1080p.mp4` | 160.1s 1920x1080 25fps alpha=no blend=multiply audio | نافذة عارض رمادية مدوّرة على أسود: صورة أرشيفية كأنها معروضة |
| `13 - أكثر من 6300 ملحق للمونتاج مجاني/Overlay/y2mate.com - Old Film Projector Green Screen Effect  كروما شاشة سوداء لجهاز عرض الفيلم القديم  السينما القديمة_1080p.mp4` | 173.8s 1920x1080 25fps alpha=no blend=multiply audio | ضوء عارض دافئ بحواف غير منتظمة ورجفة؛ مناسب لصورة قديمة بالأبيض والأسود |
| `13 - أكثر من 6300 ملحق للمونتاج مجاني/Overlay/vintage-film-split-screens-2023-11-27-05-31-15-utc.mov` | 10.0s 3840x2160 24fps alpha=no blend=multiply | شبكة 2×2 من إطارات فيلم (4K): مقارنة أربعة مشتبهين أو أدلة. الترخيص من Envato |
| `13 - أكثر من 6300 ملحق للمونتاج مجاني/Overlay/8mm-film-reel-frame-2023-11-27-05-05-05-utc.mov` | 9.8s 3840x2160 24fps alpha=no blend=multiply | نافذة 8mm بثقب (4K ProRes): جودة عالية، لكن الملف 384MB وترخيصه من Envato |
| `13 - أكثر من 6300 ملحق للمونتاج مجاني/Overlay/FILM Overlay SOUND EFFECT(720P_HD).mp4` | 35.7s 1280x720 24fps alpha=no blend=screen audio trim≈6.5-30.0s | تعتيم داكن بتوهّج برتقالي خافت عند الحواف؛ قصّ البطاقات |

### `weather-atmosphere`

| الملف | meta | لماذا |
|---|---|---|
| `13 - أكثر من 6300 ملحق للمونتاج مجاني/Overlay/Glowing Dust - Free Stock Video(720P_HD).mp4` | 30.3s 1280x720 30fps alpha=no blend=screen audio | غبار يطفو في شعاع ضوء: أفضل جو لغرفة مهجورة أو تحقيق |
| `13 - أكثر من 6300 ملحق للمونتاج مجاني/Overlay/Fog 03 - Free compositing footage(720P_HD).mp4` | 48.6s 1280x720 25fps alpha=no blend=screen audio | ضباب رمادي بطيء يملأ الإطار؛ `screen` بشفافية 20–30% |
| `13 - أكثر من 6300 ملحق للمونتاج مجاني/Overlay/Stormy_cloud_and_lightening_compositing_in_after_effects720P_HD.mp4` | 7.7s 1280x720 25fps alpha=no blend=normal audio | سحب عاصفة داكنة وبرق واحد عند الثانية 2: ليلة الحادثة أو البحر |
| `13 - أكثر من 6300 ملحق للمونتاج مجاني/Overlay/snow.mp4` | 9.1s 1920x1080 30fps alpha=no blend=screen | ثلج خفيف مائل، 1080p، بلا صوت |
| `13 - أكثر من 6300 ملحق للمونتاج مجاني/Overlay/[Free Download] Falling Snow Realistic Overlay Loop(720P_HD).mp4` | 10.1s 1280x720 30fps alpha=no blend=screen audio | ثلج كثيف صغير، حلقة 10 ثوانٍ |
| `13 - أكثر من 6300 ملحق للمونتاج مجاني/Overlay/_The_Perfect_Snowstorm_a_realistic_particle_animation_Royalty_Free.mp4` | 82.5s 1280x720 24fps alpha=no blend=screen audio | عاصفة ثلجية تشتد ثم تهدأ؛ قصّ اللحظة المطلوبة |

### `hand-drawn-marks`

الباقيان (`Pencil Scratch`، و`Super 8 Film CINEMARKS`) خلفيتهما ملونة أو فيهما وجه مقدّم، فلا يصلحان.

| الملف | meta | لماذا |
|---|---|---|
| `13 - أكثر من 6300 ملحق للمونتاج مجاني/Overlay/Handwritten_Elements_SFX_FRAMES_ARROWS_CIRCLES720P_HD.mp4` | 44.3s 1280x720 24fps alpha=no blend=screen audio trim≈6.5-39.5s | أسهم ودوائر ومستطيلات وعلامة استفهام تُرسم: لوّنها بـ `#C33B3F` وقصّ من 6.5 إلى 39.5 ثانية |
| `13 - أكثر من 6300 ملحق للمونتاج مجاني/Overlay/Hand_Drawn_Scribble_Overlay_with_Sound_Effects_Unique_Video_Enhancements720P.mp4` | 47.3s 1280x720 24fps alpha=no blend=screen audio trim≈7.5-38.0s | دوائر خربشة تُرسم: لتحديد شيء بعد التلوين؛ قصّ من 7.5 إلى 38 ثانية تقريباً |

### `particles-fire`

| الملف | meta | لماذا |
|---|---|---|
| `13 - أكثر من 6300 ملحق للمونتاج مجاني/Overlay/Fire 7 🔥(720P_HD).mp4` | 21.8s 1280x720 30fps alpha=no blend=screen audio | لهب حقيقي أسفل الإطار: لقطة حريق داخل البطاقة |
| `13 - أكثر من 6300 ملحق للمونتاج مجاني/Overlay/PART_MINI.mp4` | 10.0s 1920x1080 60fps alpha=no blend=screen | جمر صغير خافت متفرق (1080p، 60fps): جو حرب دون صخب |
| `13 - أكثر من 6300 ملحق للمونتاج مجاني/Overlay/y2mate.com - مواد مونتاجخلفياتانتقالاتالجرافيكEditingBackgroundsTransitionGraphic MaterialsDuvar kağıdı_1080pبع.mp4` | 19.0s 1920x1012 24fps alpha=no blend=screen audio | قطع لهب تطفو متفرقة؛ نسخته المكررة تحذف |
| `13 - أكثر من 6300 ملحق للمونتاج مجاني/Overlay/Bright Flying Golden Fire Sparks Background video _ Footage _ Screensaver.mp4` | 3601.0s 1280x720 30fps alpha=no blend=screen audio | شرر كثيف (ساعة كاملة، 536MB): قصّ 5–10 ثوانٍ فقط وبشفافية منخفضة |
| `13 - أكثر من 6300 ملحق للمونتاج مجاني/Overlay/FIRE PARTICLES OVERLAY _ 4K FREE PARTICLE OVERLAY ANIMATION.mp4` | 9.0s 640x360 24fps alpha=no blend=screen audio | جمر يتصاعد من الأسفل؛ الدقة منخفضة (640x360) |

### `shapes-flares-hud`

| الملف | meta | لماذا |
|---|---|---|
| `13 - أكثر من 6300 ملحق للمونتاج مجاني/Overlay/Geometric FX 03.mp4` | 9.6s 1920x1080 25fps alpha=no blend=screen | خطوط سداسية رفيعة تُرسم: خلفية تقنية خافتة |
| `13 - أكثر من 6300 ملحق للمونتاج مجاني/Overlay/Particles09.mov` | 7.9s 1920x1080 25fps alpha=no blend=screen | مدارات منقطة ومعيّن ذهبي متحرك: موضوع تقنية أو فضاء |
| `13 - أكثر من 6300 ملحق للمونتاج مجاني/Overlay/Particles02.mov` | 6.2s 1920x1080 25fps alpha=no blend=screen | من نفس السلسلة (Particles02–15): متقاربة، يكفي واحد |
| `13 - أكثر من 6300 ملحق للمونتاج مجاني/Overlay/Glass Smash - Free Overlay Stock Footage(720P_HD).mp4` | 3.5s 1280x720 24fps alpha=no blend=screen audio | زجاج يتحطم (3.5 ثانية): للحظة كسر حقيقية في القصة فقط |

### `glitch-vhs-static`

لا تُستخدم كانتقالات. إطار REC/VHS يُبنى في HTML ضمن `templates/`.

| الملف | meta | لماذا |
|---|---|---|
| `13 - أكثر من 6300 ملحق للمونتاج مجاني/Overlay/Bars_Glitch_Signal_Lost_4K_FREE_high_quality_effect720P_HD.mp4` | 10.1s 1280x720 25fps alpha=no blend=normal audio | أشرطة ألوان ثم "انقطاع الإشارة": عنصر قصة (بث، أو اختراق، أو كاميرا تنطفئ) |
| `13 - أكثر من 6300 ملحق للمونتاج مجاني/Overlay/y2mate.com - TV Distortion Television Static Effect Overlay Grain 4K  Snowman Digital_1080p.mp4` | 30.1s 1920x1080 25fps alpha=no blend=multiply audio | شاشة CRT مدوّرة بتشويش: إطار "تلفاز قديم" لخبر أرشيفي |
| `13 - أكثر من 6300 ملحق للمونتاج مجاني/Overlay/vhs effect overlay_(720P_HD)(360P).mp4` | 32.0s 640x360 30fps alpha=no blend=overlay audio | ملمس VHS رمادي داخل إطار الكاميرا (الدقة منخفضة) |

### `film-burn-leak`

الفئة ممنوعة كأسلوب عام، وهذه أهدأ خمسة إن احتاج مشهد واحد ضوءاً دافئاً.

| الملف | meta | لماذا |
|---|---|---|
| `13 - أكثر من 6300 ملحق للمونتاج مجاني/Overlay/super-8mm-film-burn-2022-01-15-13-39-05-utc.mp4` | 17.1s 3840x2160 24fps alpha=no blend=screen | الأجزاء الداكنة منه حافة Super 8 وغبار بجودة 4K ممتازة؛ تجنّب لحظات الحرق |
| `13 - أكثر من 6300 ملحق للمونتاج مجاني/Overlay/FREE 4K Light Leak!.mp4` | 120.4s 1280x720 30fps alpha=no blend=screen audio | شبه أسود مع تسرّب دافئ نادر: أخفّ ما في الفئة |
| `13 - أكثر من 6300 ملحق للمونتاج مجاني/Overlay/Cinematic Light Leaks _ Shimmer Overlays(720P_HD).mp4` | 41.8s 1280x720 24fps alpha=no blend=screen audio trim≈6.5-38.5s | لمعة ذهبية خافتة لمشهد ذهب أو كنز؛ قصّ البطاقات |
| `13 - أكثر من 6300 ملحق للمونتاج مجاني/Overlay/سبصقصثقصثفث.mp4` | 90.1s 1920x1080 25fps alpha=no blend=screen | شعاع ضوء أصفر دافئ في النصف الثاني: لحظة كشف بشفافية منخفضة |
| `13 - أكثر من 6300 ملحق للمونتاج مجاني/Overlay/Free Light Leaks 4K (3840x2160).mp4` | 300.0s 1280x720 25fps alpha=no blend=screen audio | تسرّبات ناعمة؛ الأجزاء الداكنة فقط (الدقة الفعلية 720p رغم اسمه) |

### `greenscreen-chroma`

| الملف | meta | لماذا |
|---|---|---|
| `13 - أكثر من 6300 ملحق للمونتاج مجاني/Overlay/Fumaça Smoke Fundo Verde Chroma Key 1(720P_HD).mp4` | 49.1s 1280x720 30fps alpha=no blend=chroma audio | دخان أبيض على أخضر؛ يحتاج تفريغاً (والضباب Fog 03 أسهل) |
| `13 - أكثر من 6300 ملحق للمونتاج مجاني/Overlay/VHS Overlay Green Screen _ VHS Tape Overlay(720P_HD).mp4` | 41.8s 1280x720 24fps alpha=no blend=chroma audio trim≈5.5-36.5s | شاشة VHS "PLAY ▶"/"STOP": لحظة تشغيل شريط قديم بعد التفريغ والقص |

### `animated-icon`

كل الأيقونات بأسلوب خطّي تركوازي لا يشبه رسوم النيرد (تعبئة مسطحة وحدّ أبيض سميك)، فالأفضل رسم العنصر بأسلوب القناة. وعلى الخلفية الداكنة يلزم `filter: invert(1)` مع `screen`.

| الملف | meta | لماذا |
|---|---|---|
| `13 - أكثر من 6300 ملحق للمونتاج مجاني/ايقونات/research.gif` | 2.0s 640x640 gif alpha=no(white bg) blend=invert+screen | عدسة مكبرة فوق كرة أرضية: "بحث" أو "تحقيق" |
| `13 - أكثر من 6300 ملحق للمونتاج مجاني/ايقونات/1.mp4` | 2.0s 512x512 60fps alpha=no(white bg) blend=invert+screen | ساعة إيقاف تدور: عدّاد الوقت (والأفضل بناؤه في HTML) |
| `13 - أكثر من 6300 ملحق للمونتاج مجاني/ايقونات/confused.mp4` | 2.0s 512x512 60fps alpha=no(white bg) blend=invert+screen | شخص حائر وعلامات استفهام |
| `13 - أكثر من 6300 ملحق للمونتاج مجاني/ايقونات/overpopulation.mp4` | 2.1s 512x512 60fps alpha=no(white bg) blend=invert+screen | حشد: اكتظاظ أو جمهور |
| `13 - أكثر من 6300 ملحق للمونتاج مجاني/ايقونات/126fb08a3e7b437685c01c8fb05abb56.webm` | 1.6s 360x360 30fps alpha=yes(VP9) blend=normal(+invert) | نسخة بشفافية (webm): الخطوط السوداء تحتاج قلب اللون |

### `film-leader-countdown` و`tutorial-compilation`

لا يوجد ما يُنصح به. العدّ التنازلي والمقدمات تخالف قاعدة "البداية بالخطّاف"، والتجميعات فيها شعارات.

## ما يجب تجنّبه

- `13 - أكثر من 6300 ملحق للمونتاج مجاني/Overlay/GRUNGE Film Overlay Effect(720P_HD).mp4`: رذاذ أحمر يشبه الدم (هوية القناة تمنع الدم)
- `13 - أكثر من 6300 ملحق للمونتاج مجاني/Overlay/Old Projector Frame Overlay with Film Burns(720P_HD).mp4`: درس يوتيوب: مقدّم يتكلم وواجهة Premiere، وليس طبقة
- `13 - أكثر من 6300 ملحق للمونتاج مجاني/Overlay/Super 8 Film CINEMARKS Overlay with SOUND EFFECTS_(720P_HD).mp4`: مقدّم قناة يتكلم في السيارة أول 10 ثوانٍ
- `13 - أكثر من 6300 ملحق للمونتاج مجاني/Overlay/videoplayback.mp4`: 640x360 وشعار AVFX في النهاية
- `13 - أكثر من 6300 ملحق للمونتاج مجاني/Overlay/y2mate.com - Best Overlays For Editing  Top 5 Overlay Pack  _1080p.mp4`: تجميعة RUSH.FX بعناوين وشعار
- `13 - أكثر من 6300 ملحق للمونتاج مجاني/Overlay/Vintage Film Overlay for Premiere Pro(720P_HD).mp4`: زر اشتراك محروق طوال المقطع
- `13 - أكثر من 6300 ملحق للمونتاج مجاني/Overlay/16mm film overlay(720P_HD).mp4`: "DOWNLOAD" وزر اشتراك طوال المقطع
- `13 - أكثر من 6300 ملحق للمونتاج مجاني/Overlay/y2mate.com - مواد مونتاجخلفياتانتقالاتالجرافيكEditingBackgroundsTransitionGraphic MaterialsDuvar kağاıdı_1080p.mp4`: نسخة مطابقة (نفس md5) لملف `y2mate.com - مواد مونتاج...1080pبع.mp4`
- `13 - أكثر من 6300 ملحق للمونتاج مجاني/Overlay/snow and old film overlay(720P_HD).mp4`: شبه فارغ: لا يظهر الثلج المذكور في الاسم
- `13 - أكثر من 6300 ملحق للمونتاج مجاني/Overlay/y2mate.com - light wipe after effects   Real light streak wipes   4K  2024  انتقالات بريمير برو جديدة للمونتاج_1080p.mp4`: اسمه "light wipe" ومحتواه تجميعة تلف فيلم غير متناسقة
- **أزرار اشتراك داخل المحتوى** (لا يحلّها القص): `FREE HD FILM BURNS...`، و`SUPER 8 Letterbox...`، و`film_overlay_SPROCKET_HOLE...`، و`film_scratches_vintage...`، و`old film overlay effect`، و`old film overlays for video content creators`، و`video editing film overlay transition`.
- **دقة منخفضة (640x360 أو أقل):** `4K FREE Dirt...` و`4K Old VHS...` (اسمهما 4K وهما 360p)، و`Aesthetic Overlay Green Screen...`، و`FIRE PARTICLES OVERLAY...`، و`Old Film Grain Overlay Color...` (و10fps أيضاً)، و`Old Film Overlay ~ (FREE FOR USE)`، و`VHS _Play_ Button...` (568x320)، و`old film grain overlay _Video-Audio...`، و`vhs effect overlay...`، و`videoplayback.mp4`.
- **أسماء مضللة:** `Free Light Leaks 4K (3840x2160).mp4` دقته الفعلية 1280x720. و`y2mate.com - Old Film Projector Green Screen Effect` ليس شاشة خضراء بل نافذة عارض على أسود.
- **مكررات الأيقونات:** `confused.gif` = `confused.mp4`، و`يي.gif` = `overpopulation.mp4`، وملفات webm الأربعة نسخ بشفافية من `investment` و`multitasking` و`employee` و`financial-advisor`. وفي `68d94cd1...webm` (الموظف) بقعة بيضاء خاطئة على القميص.
- **ملفات ضخمة:** `Bright Flying Golden Fire Sparks...` (ساعة، 536MB)، و`8mm-film-reel-frame...mov` (ProRes 4K، 384MB)، و`vintage-film-split-screens...mov` (273MB)، و`super-8mm-film-burn...mp4` (180MB)، و`Particle_01.mp4` (117MB). حمّلها فقط عند الحاجة.
- **الحقوق:** الملفات التي فيها `y2mate` أو `(720P_HD)` منزّلة من يوتيوب. الطبقات المجانية عادةً مسموحة، لكن مصدرها غير موثّق، فالأسلم تفضيل الملفات النظيفة بلا علامات: `Noise new`، و`Film Noise`، و`Dust.mov`، و`Grunge Elements`، و`Particle_01`، و`snow.mp4`، و`PART_MINI`، و`Geometric FX 03`. ملفات Envato (`*-utc.mov/mp4`) مرخّصة لصاحب الاشتراك فقط.
