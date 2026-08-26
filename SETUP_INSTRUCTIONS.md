# 🚀 خطوات الإعداد النهائية | Setup Instructions

## تم إنشاء الملفات التالية لك:

```
✅ .gitignore              - حماية الملفات الحساسة من الـ Git
✅ LICENSE                 - رخصة MIT المفتوحة المصدر
✅ SECURITY.md             - سياسة الأمان والإبلاغ عن الثغرات
✅ CONTRIBUTING.md         - إرشادات المساهمة
✅ requirements.txt        - المتطلبات (pip)
✅ README.md               - التوثيق الشامل
✅ publish.yml             - GitHub Actions Workflow
```

---

## 📋 الخطوات التطبيق

### 1️⃣ انسخ الملفات إلى مستودعك

```bash
# انسخ كل الملفات إلى مجلد المشروع
# يمكنك تحميلها من هنا:

# Windows (PowerShell)
Copy-Item ".gitignore", "LICENSE", "SECURITY.md", "CONTRIBUTING.md", "requirements.txt", "README.md" -Destination "C:\path\to\your\repo"

# macOS/Linux
cp .gitignore LICENSE SECURITY.md CONTRIBUTING.md requirements.txt README.md /path/to/your/repo/
```

أو **انسخ ولصق يدوياً** من هنا!

---

### 2️⃣ أنشئ مجلد .github/workflows

```bash
# أنشئ مجلدات GitHub Actions
mkdir -p .github/workflows

# انسخ workflow file
cp publish.yml .github/workflows/publish.yml
```

---

### 3️⃣ تحديث المستودع على GitHub

```bash
cd /path/to/physics-history-engine

# أضف جميع الملفات الجديدة
git add .gitignore LICENSE SECURITY.md CONTRIBUTING.md requirements.txt README.md .github/workflows/publish.yml

# قم بـ commit
git commit -m "chore: Add security, documentation, and automation files for public release"

# رفع للـ GitHub
git push origin main
```

---

### 4️⃣ أضف Secrets إلى GitHub

1. اذهب إلى مستودعك على GitHub
2. انقر **Settings** ← **Secrets and variables** ← **Actions**
3. أنقر **New repository secret** وأضف:

| الاسم | القيمة |
|------|--------|
| `GEMINI_API_KEY` | مفتاح Gemini API الخاص بك |
| `WP_URL` | `https://phy-lab.com/wp-json/wp/v2` |
| `WP_USER` | اسم مستخدم WordPress |
| `WP_PASSWORD` | كلمة مرور التطبيق (App Password) |

**⚠️ نصيحة:** استخدم WordPress App Password، ليس كلمة المرور الرئيسية!

---

### 5️⃣ فعّل GitHub Actions

1. اذهب إلى **Settings** ← **Actions** ← **General**
2. تأكد من تفعيل "Actions permissions"
3. حدد "Allow all actions"

---

### 6️⃣ اجعل المستودع عام (Public)

1. اذهب إلى **Settings** ← **Visibility**
2. انقر **Change visibility**
3. اختر **Public**
4. أكّد الاختيار

---

### 7️⃣ أضف Topics (اختياري لكن مفيد)

1. اذهب إلى الصفحة الرئيسية للمستودع
2. انقر **Add topics**
3. أضف:
   - `physics`
   - `education`
   - `automation`
   - `ai`
   - `gemini`
   - `wordpress`
   - `arabic`
   - `open-source`

---

## ✅ Checklist النشر النهائي

قبل النشر، تأكد من:

- [ ] تم نسخ `.gitignore` (منع تسريب البيانات الحساسة)
- [ ] تم نسخ `LICENSE` (رخصة MIT واضحة)
- [ ] تم نسخ `SECURITY.md` (سياسة الأمان)
- [ ] تم نسخ `CONTRIBUTING.md` (إرشادات المساهمة)
- [ ] تم نسخ `requirements.txt` (المتطلبات)
- [ ] تم تحديث `README.md` (التوثيق الشامل)
- [ ] تم إنشاء `.github/workflows/publish.yml`
- [ ] تم رفع كل الملفات إلى GitHub
- [ ] تم إضافة Secrets في GitHub Settings
- [ ] تم تفعيل GitHub Actions
- [ ] تم جعل المستودع Public

---

## 🎯 الخطوات الاختيارية

### إضافة Branch Protection (موصى به)

1. **Settings** → **Branches** → **Add rule**
2. اسم الـ branch: `main`
3. فعّل:
   - ✅ Require pull request reviews
   - ✅ Dismiss stale pull request approvals
   - ✅ Require branches to be up to date
   - ✅ Require status checks to pass

### إنشاء Discussions (للمجتمع)

1. **Settings** → **Features** → فعّل **Discussions**
2. أنشئ categories:
   - Questions & Answers
   - Ideas & Suggestions
   - Show & Tell

### إنشاء Issues Templates

```bash
# أنشئ مجلد templates
mkdir -p .github/ISSUE_TEMPLATE

# أنشئ ملف bug report
cat > .github/ISSUE_TEMPLATE/bug_report.md << 'EOF'
---
name: Bug Report
about: Report a bug
---

## الوصف
<!-- وصف المشكلة -->

## خطوات التكرار
1. 
2.
3.

## الملفات ذات الصلة
<!-- المسارات ذات الصلة -->

## البيئة
- Python version: 
- OS:
EOF
```

---

## 🔐 نصائح الأمان الإضافية

### 1. فعّل 2FA على GitHub
- Settings → Password and authentication → Two-factor authentication

### 2. استخدم Deploy Keys (للـ CI/CD)
- Settings → Deploy keys → Add deploy key

### 3. راجع Security Advisories
- Settings → Security → Security advisories

### 4. Audit Logs
- Settings → Audit log → راجع الوصول والتغييرات

---

## 📞 دعم وتواصل

- **لديك أسئلة؟** اقرأ README.md و CONTRIBUTING.md
- **وجدت ثغرة؟** أرسل بريد لـ security@phy-lab.com
- **تريد المساهمة؟** اتبع CONTRIBUTING.md

---

## 🎉 تم! نشرت مشروعك بنجاح!

الآن يمكن للجميع:
- ✅ استخدام الكود
- ✅ فهم كيفية المساهمة
- ✅ الإبلاغ عن المشاكل بشكل آمن
- ✅ ترقية ودعم المشروع

---

**شكراً لجعل هذا المشروع مفتوح المصدر للفائدة العامة!** 🚀

---

## 📝 ملاحظات إضافية

### إذا أردت تشغيل Pipeline تلقائياً يومياً:

ستجد هذا السطر في `publish.yml`:
```yaml
schedule:
  - cron: '0 9 * * *'  # كل يوم الساعة 9 صباحاً
```

لتفعيله، أزل علامات التعليق!

### إذا أردت تشغيل يدوي فقط:

اذهب إلى **Actions** → **Physics History Pipeline** → **Run workflow**

---

**Happy coding! 🧬✨**
