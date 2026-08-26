# 🧬 Physics History Engine | خط معالجة تاريخ الفيزياء

<div align="center">

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=flat-square&logo=python)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Security](https://img.shields.io/badge/Security-GitHub%20Secrets-brightgreen?style=flat-square)
![Status](https://img.shields.io/badge/Status-Active-success?style=flat-square)
![Contributions](https://img.shields.io/badge/Contributions-Welcome-blueviolet?style=flat-square)

**Automated two-stage AI pipeline to construct historical knowledge base and scientific profiles of physicists**

[العربية](#-العربية) | [English](#-english)

</div>

---

## 🇸🇦 العربية

### 📋 نظرة عامة

نظام ذكي ثنائي المرحلة لاستخلاص السير الذاتية والإسهامات العلمية لعلماء الفيزياء من المصادر الموثقة، وتحويلها إلى مقالات أكاديمية احترافية باللغة العربية الفصحى، مع النشر التلقائي على منصة phy-lab.com عبر WordPress REST API.

يستخدم النظام نموذج **Gemini 3.6 Flash** لتحليل السير العلمية وصياغة المحتوى الأكاديمي بمعايير عالية من الدقة والموثوقية.

### ✨ المميزات الرئيسية

| الميزة | الوصف |
|--------|-------|
| 🤖 **استخلاص ذكي** | استخدام Google Gemini AI لتحليل عميق للسير الذاتية والإسهامات العلمية |
| 📄 **توليد أكاديمي** | صياغة مقالات HTML احترافية باللغة العربية الفصحى مع معادلات LaTeX |
| 🔗 **نشر تلقائي** | تكامل مباشر مع WordPress REST API لنشر المقالات كمسودات |
| 🛡️ **أمان عالي** | جميع البيانات الحساسة في GitHub Secrets، بدون تعريض credentials |
| 📊 **جودة مضمونة** | نظام QA يقيّم كل مقال قبل النشر |
| 🌍 **مفتوح المصدر** | رخصة MIT - للفائدة العامة للمجتمع الأكاديمي |

### 🏗️ البنية المعمارية

```
scientists.json ──────────────────────┐
(قائمة العلماء)                        │
                                      ├─→ [المرحلة الأولى: Fact-Extraction]
                                      │   - تحليل السيرة الذاتية
                                      │   - استخلاص المعادلات والإسهامات
                                      │   - التحقق من المصادر
                                      │
knowledge_base/*.json ─────────────────┤
(البيانات المهيكلة)                    │
                                      ├─→ [المرحلة الثانية: Academic HTML Engine]
                                      │   - صياغة المقال باللغة العربية
                                      │   - تنسيق المعادلات (MathJax/LaTeX)
                                      │   - تقييم الجودة (QA)
                                      │
WordPress Draft ────────────────────────┤
(مسودة جاهزة للنشر)                    │
                                      └─→ [النشر التلقائي]
                                          - رفع للـ phy-lab.com
                                          - تعيين التصنيف
                                          - إضافة التنويه الآلي
```

### 🚀 التثبيت والتشغيل

#### المتطلبات الأساسية
- **Python 3.9+**
- **حساب Google Cloud** مع تفعيل Gemini API
- **حساب WordPress** مع صلاحيات REST API
- **حساب GitHub** (اختياري - للـ Automation)

#### الخطوة 1: نسخ المستودع
```bash
git clone https://github.com/almelbi50/physics-history-engine.git
cd physics-history-engine
```

#### الخطوة 2: تثبيت المتطلبات
```bash
pip install -r requirements.txt
```

#### الخطوة 3: إعداد البيانات الحساسة

**للتطوير المحلي:**
```bash
# أنشئ ملف .env (لا تشاركه مع أحد!)
cat > .env << 'EOF'
GEMINI_API_KEY="your-gemini-api-key-here"
WP_URL="https://phy-lab.com/wp-json/wp/v2"
WP_USER="your-wordpress-username"
WP_PASSWORD="your-wordpress-app-password"
EOF

# تحميل البيانات من .env
export $(cat .env | xargs)
```

**للـ GitHub Automation:**
اذهب إلى: **Settings → Secrets and variables → Actions**

أضف:
- `GEMINI_API_KEY` - من Google Cloud Console
- `WP_URL` - رابط WordPress JSON API
- `WP_USER` - اسم المستخدم WordPress
- `WP_PASSWORD` - App Password (ليس كلمة المرور الرئيسية)

#### الخطوة 4: تحضير قائمة العلماء
```json
// scientists.json
[
  {
    "id": "001",
    "name": "إسحاق نيوتن",
    "status": "pending"
  },
  {
    "id": "002", 
    "name": "ألبيرت أينشتاين",
    "status": "pending"
  }
]
```

#### الخطوة 5: تشغيل الخط
```bash
# تشغيل مباشر
python physics_pipeline.py

# أو عبر GitHub Actions (تلقائي عند كل push)
git push origin main
```

### 📂 هيكل المشروع

```
physics-history-engine/
│
├── physics_pipeline.py          # محرك المعالجة الرئيسي (273 سطر)
├── scientists.json              # قائمة العلماء (JSON)
├── knowledge_base/              # قاعدة المعرفة المستخلصة
│   ├── 001_إسحاق_نيوتن.json
│   └── 002_ألبيرت_أينشتاين.json
│
├── .github/workflows/           # GitHub Actions automation
│   └── publish.yml              # Workflow تلقائي للنشر
│
├── README.md                    # هذا الملف
├── SECURITY.md                  # سياسة الأمان
├── CONTRIBUTING.md              # إرشادات المساهمة
├── LICENSE                      # رخصة MIT
├── .gitignore                   # ملفات مستثناة من Git
└── requirements.txt             # المتطلبات (pip)
```

### 🔐 الأمان

#### معايير الأمان المطبقة ✅

- **بدون Credentials معروضة**: جميع API keys و passwords في GitHub Secrets
- **Validation شامل**: فحص جميع المدخلات قبل المعالجة
- **معالجة آمنة للأخطاء**: لا تطبع البيانات الحساسة في الرسائل
- **HTTPS بـ SSL Verification**: اتصالات آمنة مع WordPress
- **JSON Parsing آمن**: تحقق من الحجم والصيغة

#### الإبلاغ عن ثغرات أمنية 🚨

إذا اكتشفت ثغرة أمنية:
1. **لا تفتح issue علني** ❌
2. **أرسل بريد إلى**: `security@phy-lab.com`
3. سيتم الرد خلال 7 أيام عمل ✅

اقرأ [SECURITY.md](./SECURITY.md) لمزيد من التفاصيل

### 📊 استخدام الموارد

| المورد | الاستخدام |
|--------|----------|
| **Gemini API Calls** | 1 call per scientist (2 stages) |
| **WordPress API Calls** | 1-2 calls per scientist |
| **Storage** | ~50KB per knowledge base JSON |
| **Execution Time** | ~30-60 ثانية per scientist |

### 🛠️ أمثلة الاستخدام

#### إضافة عالم جديد
```json
{
  "id": "003",
  "name": "ماري كوري",
  "status": "pending"
}
```

#### فحص الحالة
```bash
cat scientists.json | grep -i status
```

#### عرض قاعدة المعرفة
```bash
ls -la knowledge_base/
cat knowledge_base/001_*.json | python -m json.tool
```

### 📚 المراجع والموارد

- [Google Gemini API Documentation](https://ai.google.dev)
- [WordPress REST API](https://developer.wordpress.org/rest-api/)
- [LaTeX Math Reference](https://en.wikibooks.org/wiki/LaTeX/Mathematics)
- [MathJax Documentation](https://docs.mathjax.org/)

### 🤝 المساهمة

نرحب بـ Pull Requests! 🎉

اقرأ [CONTRIBUTING.md](./CONTRIBUTING.md) لمعرفة كيفية المساهمة

### 📝 الترخيص

هذا المشروع تحت رخصة **MIT License**
اقرأ [LICENSE](./LICENSE) للتفاصيل

### 📧 التواصل

- **البريد الرئيسي**: contact@phy-lab.com
- **الأمان**: security@phy-lab.com
- **الموقع**: https://phy-lab.com

### 🙏 شكر خاص

شكر لكل من ساهم أو ساعد في هذا المشروع!

---

## 🇬🇧 English

### 📋 Overview

An intelligent two-stage system for extracting biographies and scientific contributions of physicists from reliable sources, transforming them into professional academic articles in formal Arabic, with automatic publishing on phy-lab.com via WordPress REST API.

The system uses **Gemini 3.6 Flash** model for deep analysis and academic-grade content generation.

### ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🤖 **Smart Extraction** | Uses Google Gemini AI for deep biography and contribution analysis |
| 📄 **Academic Generation** | Produces professional HTML articles in formal Arabic with LaTeX equations |
| 🔗 **Automatic Publishing** | Direct WordPress REST API integration for draft publication |
| 🛡️ **High Security** | All sensitive data in GitHub Secrets, no credential exposure |
| 📊 **Quality Assurance** | QA system evaluates each article before publishing |
| 🌍 **Open Source** | MIT License - for the academic community's benefit |

### 🚀 Installation & Setup

#### Prerequisites
- Python 3.9+
- Google Cloud account with Gemini API enabled
- WordPress account with REST API permissions
- GitHub account (optional - for automation)

#### Quick Start
```bash
# Clone repository
git clone https://github.com/almelbi50/physics-history-engine.git
cd physics-history-engine

# Install dependencies
pip install -r requirements.txt

# Set up secrets (GitHub Secrets for CI/CD)
# or create .env file for local development (not tracked by git)
```

#### Local Development
```bash
export GEMINI_API_KEY="your-key"
export WP_URL="https://phy-lab.com/wp-json/wp/v2"
export WP_USER="username"
export WP_PASSWORD="app-password"

python physics_pipeline.py
```

### 🔐 Security

#### Applied Security Standards ✅

- **No Exposed Credentials**: All secrets in GitHub Secrets
- **Input Validation**: All inputs checked before processing
- **Safe Error Handling**: Sensitive data never logged
- **HTTPS with SSL**: Verified connections to WordPress
- **Safe JSON Parsing**: Size and format validation

#### Reporting Vulnerabilities 🚨

Found a security issue? Please don't open a public issue.
Email: `security@phy-lab.com`

See [SECURITY.md](./SECURITY.md) for details

### 🤝 Contributing

We welcome Pull Requests! 

Read [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines

### 📝 License

MIT License - See [LICENSE](./LICENSE)

### 📧 Contact

- **Email**: contact@phy-lab.com
- **Security**: security@phy-lab.com
- **Website**: https://phy-lab.com

---

<div align="center">

**Made with ❤️ for Physics Educators & Researchers Worldwide**

*Advancing scientific knowledge through open-source tools*

[⬆️ Back to Top](#-physics-history-engine)

</div>
