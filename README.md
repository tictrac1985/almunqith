# المنقذ — AlMunqith

برنامج استعادة الملفات المحذوفة والمفقودة لويندوز، بواجهة عربية/إنجليزية سهلة وبدون أي طرفية.

A professional Windows data-recovery app with an Arabic/English GUI — no terminal required.

## للمستخدم (Release)

مجلد `Release/` يحوي:
- **`AlMunqith.exe`** — النسخة المحمولة (انقر نقرًا مزدوجًا، بلا تثبيت).
- **`AlMunqith-Setup.exe`** — نسخة التثبيت (تثبيت لكل مستخدم بدون صلاحيات مدير، تُنشئ اختصارات).
- **`كيفية_الاستخدام.txt`** — دليل الاستخدام بالعربية.

## القدرات

- **معالج من 5 خطوات**: اختيار القرص ← نوع الملفات ← مكان الحفظ ← الفحص ← النتائج.
- **سلّم الاستعادة**:
  - المستوى 1 — استرجاع من نظام الملفات (FAT / exFAT / NTFS) مع الأسماء والتواريخ الأصلية.
  - المستوى 2 — فحص عميق بالبصمات لأكثر من 22 نوع ملف في أي موضع.
  - المستوى 4 — إعادة بناء فيديوهات الكاميرات المجزأة (MJPEG → AVI)، وإنقاذ الصور الجزئية (مصغّرة EXIF + بيانات التصوير).
  - وضع النسخ الإنقاذي للأقراص المتعثرة (watchdog + إعادة تشغيل الجهاز + تخطي المناطق التالفة).
- **قراءة فقط**: لا يُكتب على القرص المصدر أبدًا.
- **بلا إنترنت**: كل المعالجة محلية على الجهاز.

## الأنواع المدعومة (22)

صور: JPEG, PNG, GIF, BMP, TIFF, PSD, HEIC, CR2 · فيديو: AVI, MP4/MOV, MKV/WebM, WMV/ASF · صوت: MP3, WAV, FLAC, OGG · مستندات: PDF, DOCX/XLSX/PPTX, DOC/XLS/PPT · أرشيف: ZIP, RAR, 7z.

## للمطوّر

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e . PySide6 pytest pytest-qt
.\.venv\Scripts\python.exe -m almunqith          # تشغيل الواجهة
$env:QT_QPA_PLATFORM="offscreen"; .\.venv\Scripts\python.exe -m pytest   # الاختبارات
```

بناء الحزم:
```powershell
.\.venv\Scripts\python.exe packaging\make_icon.py
.\.venv\Scripts\python.exe -m PyInstaller packaging\portable.spec   --distpath dist       --noconfirm
.\.venv\Scripts\python.exe -m PyInstaller packaging\app_onedir.spec --distpath dist       --noconfirm
.\.venv\Scripts\python.exe -m PyInstaller packaging\installer.spec  --distpath dist_setup --noconfirm
```

### البنية
```
almunqith/
  __main__.py          نقطة الدخول + الرفع لصلاحية المدير وقت التشغيل
  core/
    source.py          DiskImage / RawDevice (قراءة فقط)
    reader.py          ResilientReader (watchdog + إعادة فتح + فجوات)
    imager.py          النسخ الإنقاذي القابل للاستئناف
    devices.py         تعداد أقراص ويندوز
    carve/             scanner + signatures + validators/*
    fs/                fat.py exfat/ntfs.py + scan.py (المستوى 1)
    rebuild/           mjpeg_avi.py + jpeg_salvage.py (المستوى 4)
    pipeline.py        سلّم الاستعادة + بروتوكول الأحداث
    extract.py         الحفظ المصنّف + التقرير
  ui/                  wizard.py + pages/* + worker.py + i18n + theme
packaging/             specs + installer + icon
```

اختبارات: 73 ناجحة. اختبار قبول ذهبي على نسخة كارت حقيقية (‏13,606 إطارًا / 9 فيديوهات).

صُنع بحبّ لاستعادة الذكريات 🛟
