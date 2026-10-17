# مونتاج القناة الآلي

هذا المستودع يحوّل **تسجيل صوت + سكربت** إلى فيديو وثائقي جاهز للنشر، ملتزم بهوية القناة في `brand/BRAND.md` و `brand/FONTS.md`، وبتعليمات `CLAUDE.md`.

## ما يحتاجه المالك لكل حلقة
1. **السكربت** بنفس قالب الحلقة الأولى (`episodes/ep-001-chile-33/script.md`).
2. **تسجيل الصوت**، إما ملفاً واحداً أو ملفاً لكل مشهد.
3. **لقطات وصور** إن وُجدت. الناقص يُجلب من مصادر مرخّصة: ويكيميديا، وناسا، وPexels.
4. **الموسيقى والمؤثرات المرخّصة**، مع ذكر مصدرها.

## الحلقة 001 — «69 يومًا تحت الأرض» (Shorts عمودي 1080×1920)
| المرحلة | الأداة |
|---|---|
| تفريغ الصوت بتوقيت الكلمات | `faster-whisper large-v3` ← `tools/transcribe_fw.py` |
| تقصير الوقفات بلا قصّ كلمات | `tools/cut_voice.py` |
| محاذاة دقيقة لكل كلمة | `tools/align_ctc.py` (wav2vec2 عربي) |
| ترميم الصوت | Sidon v0.1 (يعيد بناء صوت نقي 48kHz من تسجيل الهاتف) ← `tools/enh_sidon.py` |
| معالجة الراوي | مطابقة النغمة لمنحنى الكلام القياسي ANSI S3.5 + de-esser + ضغط 2:1 + loudnorm (−16 LUFS) ← `tools/narrator.py` |
| فحص الجودة الصوتية | DNSMOS + SQUIM ← `tools/speech_quality.py`، سلامة الكلمات ← `tools/asr_cer.py`، الطيف ← `tools/ltass.py` |
| اختيار الصور | ويكيميديا (صور الحكومة التشيلية CC BY 2.0) ← `tools/commons.py`, `tools/fetch_selected.py` |
| الطيران من الفضاء | صور ناسا GIBS + EO-1 ← `tools/map_zoom.py` |
| تصنيف المؤثرات | AudioSet AST ← `tools/tag_sounds.py` |
| بناء التايم‑لاين | `episodes/ep-001-chile-33/build/build_timeline.py` |
| الرسوم والإطارات | محرّك Chromium خاص ← `tools/render/` (كل حركة دالة نقية للزمن) |
| المكساج | `tools/mix.py` (ducking، attack 150ms، release 400ms) — مستوى الموسيقى يُقاس بـ `tools/mix_report.py` |
| التصدير والفحص | `tools/export.sh`, `tools/qc.py` |

## إعادة البناء
```bash
cd episodes/ep-001-chile-33
python3 build/build_timeline.py                     # timeline.js + audio_plan.json + timeline.json
python3 ../../tools/mix.py . build/mix.wav           # الصوت النهائي
node ../../tools/render/render.js build/timeline.js build/video_final.mp4 --workers 3
bash ../../tools/export.sh build/video_final.mp4 build/mix.wav renders/final-1080x1920.mp4 renders/share-preview.mp4
python3 build/make_credits.py && python3 ../../tools/qc.py . renders/final-1080x1920.mp4
```
الوسائط الثقيلة (الصور والفيديو والصوت) لا تُرفع إلى git. انظر `.gitignore`.
