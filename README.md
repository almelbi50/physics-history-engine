# خط المعالجة الأوتوماتيكي لنشر سير علماء الفيزياء (Automated Physics Editorial Pipeline)

نظام وكيل ذكاء اصطناعي ثنائي المرحلة (Two-Stage Pipeline Agent)، مُصمم ومطور لصالح منصة **معامل الفيزياء (phy-lab.com)**. يقوم النظام باستخلاص الحقائق العلمية والتاريخية الموثقة، وصياغة المعادلات الفيزيائية المتقدمة، ونشر المقالات الأكاديمية بتنسيق HTML مباشرة عبر وردبريس REST API.

---

## 🏗 بنية النظام (System Architecture)

يعالج النظام قائمة العلماء المجدولين تسلسلياً باستخدام بنية ثنائية المرحلة معتمدة على نموذج `gemini-3.6-flash`:
[scientists.json] ──► [المرحلة الأولى: محرك استخلاص الحقائق]
│
▼
[knowledge_base/*.json]
│
▼
[المرحلة الثانية: محرك التنسيق الأكاديمي]
│
▼
[النشر عبر WordPress REST API]
---

## ⚙️ المزايا التقنية الرئيسية

* **خط معالجة ثنائي المرحلة (Two-Stage Decoupled Workflow):**
  * **المرحلة الأولى (Fact-Extraction Engine):** تحليل السير الزمنية، والشروط الحدية (Boundary Conditions)، والمعادلات بترميز LaTeX، ونطاقات الصحة العلمية في هيكل `JSON` صريح.
  * **المرحلة الثانية (Academic HTML Engine):** تحويل البيانات الهيكلية إلى مقال أكاديمي باللغة العربية الفصحى مع دعم وسوم وردبريس القياسية (`[mathjax]` و `[latex]`).
* **معالجة معادلات MathJax / LaTeX:** تلافي مشاكل العرض البرمجي عبر حظر وسوم `<blockquote>` وتغليف المعادلات ضمن وسوم قصيرة محددة.
* **إدارة أخطاء الاتصال (Resilience & Fault Tolerance):** إدراج آلية الانتظار التصاعدي (`generate_content_with_retry`) لمواجهة أخطاء الضغط `503 Unavailable` و `429 Rate Limit`.
* **الأتمتة والتصنيف التلقائي:** جلب معرف تصنيف `علماء الفيزياء` (`physicists`) تلقائياً عبر API وتعيينه للمقال، مع إدراج تذييل التنويه الآلي الموحد.

---

## 🚀 التشغيل والإعداد

### متغيرات البيئة (Environment Variables)
قم بتحديد المتغيرات التالية في بيئة GitHub Secrets أو المتغيرات المحلية:

```bash
export GEMINI_API_KEY="your-gemini-api-key"
export WP_URL="[https://phy-lab.com/wp-json/wp/v2](https://phy-lab.com/wp-json/wp/v2)"
export WP_USER="your-wp-username"
export WP_PASSWORD="your-application-password"

إدارة قائمة الانتظار (scientists.json)
[
  {
    "id": "001",
    "name": "ابن الهيثم",
    "status": "pending"
  }
]
التشغيل يدويًا
python physics_pipeline.py
🛡 نظام ضبط الجودة (QA System)
قبل إرسال حمولة البيانات إلى وردبريس، تقوّم المرحلة الثانية المقال وتستخرج quality_score. إذا كانت النتيجة أقل من 90 أو احتوت على أخطاء حرجة critical_errors، يتم إيقاف خط المعالجة تلقائياً لمنع نشر المحتوى غير المكتمل
---

---

### **المكون الثاني: مقال WordPress التعريفي باللغة العربية**

* **العنوان:** مشروع توثيق علماء الفيزياء: نظام ذكي ممتد لمعالجة ونشر التاريخ العلمي
* **التصنيف:** أخبار المنصة / مشروعات تقنية

**كود المقال (HTML جاهز للنشر):**

```html
<p><img class="aligncenter size-full" src="https://phy-lab.com/wp-content/uploads/2026/08/مشروع-علماء-الفيزياء.png" alt="مشروع علماء الفيزياء - phy-lab.com" width="1200" height="630" /></p>

<p>تعلن منصة <strong>معامل الفيزياء (phy-lab.com)</strong> عن إطلاق نظامها الذكي المستقل لإعادة توثيق السير العلمية والإسهامات الفيزيائية عبر التاريخ، اعتماداً على بنية معالجة خطوط البيانات الأوتوماتيكية (Automated Physics Editorial Pipeline).</p>

<h3>أهداف المشروع الأساسية</h3>
<ul>
	<li><strong>التوثيق الأكاديمي الدقيق:</strong> استخلاص الحقائق التاريخية والنظريات الفيزيائية من المصادر الموثوقة دون إدراج صيغ إنشائية أو انحيازات غير موثقة.</li>
	<li><strong>معالجة الصيغ الرياضية:</strong> إدراج المعادلات والمحدودية الفيزيائية (Boundary Conditions) باستخدام محركات التنسيق القياسية MathJax/LaTeX لضمان الوضوح على جميع الأجهزة.</li>
	<li><strong>أتمتة النشر والتصنيف:</strong> ربط خط التوليد بمجلة المنصة آلياً لإثراء المحتوى العربي الأكاديمي الخاص بالمختبرات والفيزياء النظرية.</li>
</ul>

<h3>البنية التقنية للوكيل الرقمي</h3>
<p>يعتمد المشروع على محرك معالجة ثنائي المرحلة (Two-Stage Knowledge Extraction Pipeline):</p>

<table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
<thead>
<tr style="background-color: #f2f2f2;">
<th style="border: 1px solid #dddddd; padding: 8px; text-align: right;">المرحلة</th>
<th style="border: 1px solid #dddddd; padding: 8px; text-align: right;">الوظيفة البرمجية</th>
<th style="border: 1px solid #dddddd; padding: 8px; text-align: right;">المخرجات</th>
</tr>
</thead>
<tbody>
<tr>
<td style="border: 1px solid #dddddd; padding: 8px;"><strong>المرحلة الأولى</strong></td>
<td style="border: 1px solid #dddddd; padding: 8px;">Fact-Extraction Engine (استخلاص البيانات والتحقق من النماذج)</td>
<td style="border: 1px solid #dddddd; padding: 8px;">ملف JSON بنيوي موحد في قاعدة المعرفة.</td>
</tr>
<tr>
<td style="border: 1px solid #dddddd; padding: 8px;"><strong>المرحلة الثانية</strong></td>
<td style="border: 1px solid #dddddd; padding: 8px;">Academic HTML Engine (إخراج المقال، التقييم الأكاديمي، والنشر)</td>
<td style="border: 1px solid #dddddd; padding: 8px;">مسودة HTML أكاديمية موجهة لـ REST API.</td>
</tr>
</tbody>
</table>

<hr />
<div style="background-color: #f8f9fa; border-right: 4px solid #0073aa; padding: 12px 16px; margin-top: 25px; font-size: 0.9em; color: #555; line-height: 1.6;">
  <strong>تنويه:</strong> أُعدّ هذا المقال آليًا بواسطة وكيل ذكاء اصطناعي وفق معايير محددة للبحث والتحقق والصياغة العلمية، مع الاستناد إلى مصادر موثوقة. ويُنصح بالرجوع إلى المراجع المرفقة للتحقق من التفاصيل والمعلومات الواردة في المقال.
</d
