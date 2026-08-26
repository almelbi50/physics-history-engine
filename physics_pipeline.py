def clean_and_parse_json(text):
    # 1. إزالة وسم markdown إن وجد
    cleaned = re.sub(r'^```json\s*', '', text.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r'^```\s*', '', cleaned, flags=re.MULTILINE)
    cleaned = cleaned.strip()

    # 2. حماية رموز LaTeX واستبدال الـ backslashes المنفردة داخل السلاسل النصية
    # يمنع هذا التغيير حدوث خطأ Invalid \escape مع معادلات LaTeX
    try:
        return json.loads(cleaned, strict=False)
    except json.JSONDecodeError:
        # إذا فشل التحليل المباشر، يتم ترميز الـ backslashes الخاصة بـ LaTeX تلقائياً
        fixed_text = re.sub(r'\\(?![/"bfnrtu]|u[0-9a-fA-F]{4})', r'\\\\', cleaned)
        return json.loads(fixed_text, strict=False)
