#!/usr/bin/env python3
"""
physics_pipeline.py
===================
Automated Two-Stage Physics Editorial & Fact-Extraction Pipeline for phy-lab.com.
Engineered for strict academic accuracy, historical rigor, and MathJax/LaTeX integration.
"""

import os
import sys
import json
import time
import requests
import google.generativeai as genai

# ==============================================================================
# CONFIGURATION & ENVIRONMENT SETUP
# ==============================================================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WP_URL = os.getenv("WP_URL", "https://phy-lab.com/wp-json/wp/v2")
WP_USER = os.getenv("WP_USER")
WP_PASSWORD = os.getenv("WP_PASSWORD")

if not GEMINI_API_KEY:
    print("[CRITICAL] GEMINI_API_KEY environment variable is missing.")
    sys.exit(1)

genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-3.6-flash")

# ==============================================================================
# STAGE 1 PROMPT: FACT EXTRACTION ENGINE
# ==============================================================================
STAGE_1_PROMPT = """
You are a specialized Physics Historian, Scientific Fact-Checker, and Fact-Extraction Engine for phy-lab.com.

Target Scientist: {scientist_name}

Your task is to build a scientifically rigorous structured knowledge base about the scientist.

IMPORTANT:
This is NOT a creative biography generation task.
Accuracy has priority over completeness, rhetorical impact, or impressive claims.

You MUST distinguish between:

1. Historically established facts.
2. Strong scholarly interpretations.
3. Historically disputed claims.
4. Modern interpretations of historical scientific work.

Do NOT invent dates, discoveries, equations, experiments, titles, relationships, or attributions.

If an exact date is uncertain, DO NOT fabricate an exact YYYY-MM-DD date.
Use null for uncertain exact dates and explain the uncertainty in the relevant evidence field.

Do NOT automatically describe a scientist as:
- founder
- inventor
- first
- father of
- creator of the scientific method
- discoverer of a law
- pioneer

unless the attribution is sufficiently supported.

For every major scientific contribution, distinguish:
- what the scientist actually proposed, observed, demonstrated, or wrote;
- later historical interpretation;
- modern scientific interpretation.

For equations and mathematical models:
- verify mathematical consistency;
- define variables;
- identify assumptions;
- identify validity domain;
- do not attribute modern reformulations to historical scientists unless justified.

Return ONLY valid JSON matching this schema:

{{
  "entity_resolution": {{
    "canonical_name": "",
    "arabic_name": "",
    "english_name": "",
    "alternative_names": [],
    "birth_date": null,
    "death_date": null,
    "birth_date_precision": "exact|approximate|unknown",
    "death_date_precision": "exact|approximate|unknown",
    "birth_place": "",
    "nationality_context": "",
    "identity_confidence": 0
  }},

  "importance_evaluation": {{
    "score": 0,
    "eligible_for_pipeline": true,
    "scientific_significance": "",
    "historical_significance": ""
  }},

  "timelines": {{
    "timeline_a_biological": [
      {{
        "year": null,
        "date_precision": "exact|approximate|unknown",
        "event": "",
        "confidence": "high|medium|low",
        "evidence_note": ""
      }}
    ],
    "timeline_b_scientific": [
      {{
        "year": null,
        "date_precision": "exact|approximate|unknown",
        "event_type": "",
        "description": "",
        "confidence": "high|medium|low",
        "evidence_note": ""
      }}
    ]
  }},

  "physics_analysis": [
    {{
      "contribution_name": "",
      "historical_claim": "",
      "scientific_problem": "",
      "historical_hypothesis": "",
      "historical_model_or_framework": "",
      "modern_interpretation": "",
      "experiment_details": "",
      "historical_experiment_status": "documented|probable|disputed|unknown",

      "equations": [
        {{
          "latex_raw": "",
          "historical_or_modern": "historical|modern_reformulation",
          "variables_definition": {{}},
          "validity_domain": "",
          "assumptions": "",
          "dimensional_consistency": "verified|not_applicable|uncertain",
          "attribution_confidence": "high|medium|low"
        }}
      ],

      "result_and_impact": "",
      "limitations_and_boundary_conditions": "",

      "claim_confidence": "high|medium|low",
      "anachronism_risk": "low|medium|high",
      "verification_note": ""
    }}
  ],

  "knowledge_graph_relations": {{
    "teachers": [],
    "students": [],
    "collaborators": [],
    "precursors_built_upon": [],
    "influenced_scientists": []
  }},

  "major_claims_audit": [
    {{
      "claim": "",
      "claim_type": "historical|scientific|mathematical|attributional|chronological",
      "confidence": "high|medium|low",
      "status": "established|qualified|disputed|insufficient_evidence",
      "recommended_wording": "",
      "risk": "low|medium|high"
    }}
  ],

  "verified_sources": [
    {{
      "title": "",
      "institution_or_author": "",
      "authority_level": "A|B|C",
      "source_type": "primary|peer_reviewed|scholarly_book|university|encyclopedia|reference",
      "url": "",
      "supported_claim": "",
      "source_confidence": "high|medium|low"
    }}
  ],

  "verification_summary": {{
    "historical_accuracy": 0,
    "scientific_accuracy": 0,
    "mathematical_accuracy": 0,
    "source_quality": 0,
    "major_uncertainties": [],
    "high_risk_claims": [],
    "ready_for_article_generation": true
  }}
}}

SOURCE QUALITY:

Prefer:
1. Primary historical works and critical editions.
2. Peer-reviewed academic publications.
3. Scholarly books by recognized historians of science.
4. University and research institutions.
5. Established academic encyclopedias.
6. General references only when necessary.

Do NOT treat a general website, blog, AI-generated summary, or Wikipedia as sufficient evidence for an important claim.

CRITICAL RULE:

If evidence is uncertain, preserve the uncertainty in the JSON.

Never convert uncertainty into false precision.
"""

# ==============================================================================
# STAGE 2 PROMPT: ACADEMIC HTML ARTICLE GENERATOR
# ==============================================================================
STAGE_2_PROMPT = """
You are an Academic Physics Editor and Scientific Fact-Checking Editor writing for phy-lab.com.

Target Scientist: {scientist_name}

Generate a publication-ready WordPress HTML article using ONLY the structured knowledge base provided below.

JSON Data:
{stage1_json}

The JSON is the authoritative working dataset for this article.

IMPORTANT:
Do NOT introduce new factual claims that are not supported by the JSON.

The article must preserve uncertainty where the structured data identifies uncertainty.

Do NOT transform:
- approximate dates into exact dates;
- disputed claims into established facts;
- modern interpretations into historical claims;
- modern mathematical reformulations into historical equations;
- weak evidence into confident statements.

--------------------------------------------------
SCIENTIFIC AND HISTORICAL WRITING RULES
--------------------------------------------------

1. LANGUAGE

The entire article:
- post_title
- html_content
- meta_description

MUST be written in professional, formal academic Arabic.

Use established Arabic scientific terminology.

Include the English scientific term at first occurrence when it improves precision.

--------------------------------------------------

2. TITLE

post_title MUST contain only the scientist's Arabic name.

Examples:
"ابن الهيثم"
"إسحاق نيوتن"
"ألبرت أينشتاين"

Do NOT add a subtitle to post_title.

--------------------------------------------------

3. HISTORICAL PRECISION

Do not present uncertain historical information as certain.

If the JSON marks information as approximate, disputed, or uncertain, preserve that qualification.

Prefer:

"نحو..."
"خلال هذه الفترة..."
"يُرجح..."
"تشير المصادر..."
"يُعد من أبرز..."
"أسهم في..."

Avoid unsupported absolute statements such as:

"كان أول من..."
"أسس المنهج العلمي..."
"اخترع..."
"اكتشف..."
"وضع الأساس الكامل لـ..."

unless explicitly supported by the verified dataset.

--------------------------------------------------

4. HISTORICAL SCIENCE VS MODERN SCIENCE

When describing historical scientific ideas:

FIRST explain the historical concept.

THEN explain the modern scientific interpretation.

Use explicit distinctions such as:

"وفق التصور العلمي لدى العالم..."
"في سياقه التاريخي..."
"أما في الفيزياء الحديثة..."

Never silently replace historical terminology with modern terminology.

--------------------------------------------------

5. PHYSICS ACCURACY

All physics explanations must respect:

- assumptions;
- validity domains;
- approximations;
- boundary conditions;
- dimensional consistency;
- mathematical consistency.

Avoid unrestricted statements when a physical law applies only under specific conditions.

--------------------------------------------------

6. EQUATIONS

Start html_content with:

[mathjax]

All block equations MUST use:

[latex]equation[/latex]

All inline variables MUST use:

[latex]var[/latex]

or $var$.

For every equation:
- define variables;
- explain physical meaning;
- state assumptions where necessary;
- state validity domain where relevant.

If an equation is a modern reformulation, explicitly identify it as such.

--------------------------------------------------

7. HISTORICAL ATTRIBUTION

Do not attribute a modern formulation, terminology, equation, or theory directly to the historical scientist unless the JSON explicitly supports the attribution.

Use formulations such as:

"يمكن إعادة صياغة هذه الفكرة في الإطار الرياضي الحديث..."

instead of implying:

"صاغ العالم هذه المعادلة..."

when the equation is a modern reconstruction.

--------------------------------------------------

8. NO BLOCKQUOTES

Do NOT use <blockquote> under any circumstances.

Use:
- headings;
- paragraphs;
- tables;
- ordered lists;
- unordered lists.

--------------------------------------------------

9. ARTICLE STRUCTURE

Build a coherent academic article containing, when applicable:

- introduction;
- historical context;
- scientific problem;
- contribution of the scientist;
- experimental or mathematical approach;
- physical interpretation;
- limitations;
- modern interpretation;
- scientific legacy;
- connection to physics education where relevant;
- references.

Do not force sections that are unsupported by the knowledge base.

--------------------------------------------------

10. REFERENCES

References must correspond to the sources contained in the JSON.

Do not fabricate bibliographic details.

Do not add references merely to make the article appear academic.

--------------------------------------------------

11. SEO

Create:

meta_description:
- professional Arabic;
- approximately 140–160 characters where practical;
- accurately describing the article;
- no keyword stuffing.

primary_keyword:
- the most relevant search phrase.

slug:
- concise English transliteration/keyword slug;
- lowercase;
- hyphen-separated;
- no unnecessary words.

--------------------------------------------------

12. MANDATORY FINAL AI DISCLOSURE

At the very end of html_content append EXACTLY:

<hr />
<div style="background-color: #f8f9fa; border-right: 4px solid #0073aa; padding: 12px 16px; margin-top: 25px; font-size: 0.9em; color: #555; line-height: 1.6;">
<strong>تنويه:</strong> أُعدّ هذا المقال آليًا بواسطة وكيل ذكاء اصطناعي وفق معايير محددة للبحث والتحقق والصياغة العلمية، مع الاستناد إلى مصادر موثوقة. ويُنصح بالرجوع إلى المراجع المرفقة للتحقق من التفاصيل والمعلومات الواردة في المقال.
</div>

--------------------------------------------------
FINAL QA
--------------------------------------------------

Before returning the JSON, independently audit the generated article against the supplied knowledge base.

Check:

1. Historical accuracy.
2. Scientific accuracy.
3. Mathematical accuracy.
4. Terminological accuracy.
5. Historical attribution.
6. Anachronism.
7. Unsupported claims.
8. Dates and chronology.
9. Citation/source consistency.
10. SEO quality.
11. Arabic academic quality.

CRITICAL ERRORS include:

- fabricated historical facts;
- fabricated dates;
- unsupported attribution;
- incorrect equations;
- incorrect physical laws;
- historical concepts presented as modern theories;
- modern theories attributed to historical scientists;
- references that are not present in the JSON;
- contradiction with high-confidence information in the JSON.

QUALITY SCORE:

0–59 = FAIL
60–74 = MAJOR REVISION
75–89 = REVISION REQUIRED
90–100 = PUBLICATION READY (Note: standard scales 0.0 to 1.0 are acceptable, where 0.90+ = 90+)

A score of 90 (or 0.90) or above is allowed ONLY when there are no critical errors.

Return ONLY valid JSON:

{{
  "post_title": "",
  "html_content": "",
  "seo": {{
    "meta_description": "",
    "primary_keyword": "",
    "slug": ""
  }},
  "qa_evaluation": {{
    "quality_score": 0,
    "critical_errors": [],
    "warnings": [],
    "historical_accuracy": 0,
    "scientific_accuracy": 0,
    "mathematical_accuracy": 0,
    "source_quality": 0,
    "anachronism_check": "PASS|WARNING|FAIL",
    "publish_recommendation": "PUBLISH|REVIEW|REJECT"
  }}
}}
"""

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================
def generate_content_with_retry(prompt_text, max_retries=3, delay=5):
    """Executes Gemini API requests with exponential backoff strategy."""
    for attempt in range(max_retries):
        try:
            response = model.generate_content(
                prompt_text,
                generation_config={"response_mime_type": "application/json"}
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"[Warning] API call attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(delay * (2 ** attempt))
            else:
                raise e

def get_wordpress_category_id(category_slug="physicists"):
    """Fetches category ID for taxonomy assignment via REST API."""
    if not (WP_USER and WP_PASSWORD):
        return []
    endpoint = f"{WP_URL.rstrip('/')}/categories?slug={category_slug}"
    try:
        res = requests.get(endpoint, auth=(WP_USER, WP_PASSWORD), timeout=15)
        if res.status_code == 200 and len(res.json()) > 0:
            return [res.json()[0]["id"]]
    except Exception as e:
        print(f"[Warning] Category lookup failed: {e}")
    return []

def post_to_wordpress(article_data):
    """Posts generated HTML article draft to WordPress via REST API."""
    if not (WP_USER and WP_PASSWORD):
        print("[Error] Missing WordPress authentication credentials.")
        return False

    endpoint = f"{WP_URL.rstrip('/')}/posts"
    categories = get_wordpress_category_id("physicists")

    payload = {
        "title": article_data["post_title"],
        "content": article_data["html_content"],
        "status": "draft",
        "slug": article_data["seo"]["slug"],
        "excerpt": article_data["seo"]["meta_description"],
        "categories": categories
    }

    try:
        response = requests.post(
            endpoint,
            auth=(WP_USER, WP_PASSWORD),
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        if response.status_code in [200, 201]:
            print(f"[WordPress API] Draft created successfully. ID: {response.json().get('id')}")
            return True
        else:
            print(f"[WordPress API Error] Status {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"[WordPress API Exception] {e}")
        return False

# ==============================================================================
# MAIN EXECUTION FLOW
# ==============================================================================
def main():
    if not os.path.exists("scientists.json"):
        print("[CRITICAL] 'scientists.json' queue file not found.")
        sys.exit(1)

    with open("scientists.json", "r", encoding="utf-8") as f:
        scientists = json.load(f)

    target_index = None
    target = None
    for idx, item in enumerate(scientists):
        if item.get("status") == "pending":
            target_index = idx
            target = item
            break

    if not target:
        print("[Pipeline] No pending scientists found in queue.")
        sys.exit(0)

    scientist_name = target["name"]
    print(f"\n==================================================")
    print(f"[Pipeline Start] Processing scientist: {scientist_name}")
    print(f"==================================================")

    # --------------------------------------------------------------------------
    # STAGE 1: FACT EXTRACTION ENGINE
    # --------------------------------------------------------------------------
    print("\n[Stage 1] Executing Fact-Extraction & Physics Modeling Check...")
    prompt_stage1 = STAGE_1_PROMPT.format(scientist_name=scientist_name)
    stage1_json = generate_content_with_retry(prompt_stage1)

    os.makedirs("knowledge_base", exist_ok=True)
    kb_path = f"knowledge_base/{target['id']}_{scientist_name}.json"
    with open(kb_path, "w", encoding="utf-8") as f:
        json.dump(stage1_json, f, ensure_ascii=False, indent=2)
    print(f"[Stage 1] Structured Knowledge Base saved to '{kb_path}'.")

    # --------------------------------------------------------------------------
    # STAGE 2: ACADEMIC ARTICLE GENERATION
    # --------------------------------------------------------------------------
    print("\n[Stage 2] Synthesizing Academic HTML Article & Quality Audit...")
    prompt_stage2 = STAGE_2_PROMPT.format(
        scientist_name=scientist_name,
        stage1_json=json.dumps(stage1_json, ensure_ascii=False)
    )
    article_data = generate_content_with_retry(prompt_stage2)

    # --------------------------------------------------------------------------
    # MULTI-DIMENSIONAL QUALITY GATE AUDIT
    # --------------------------------------------------------------------------
    qa = article_data.get("qa_evaluation", {})

    def normalize_score(val):
        try:
            val = float(val)
            return val * 100 if val <= 1.0 else val
        except (ValueError, TypeError):
            return 0.0

    quality_score = normalize_score(qa.get("quality_score", 0))
    historical_accuracy = normalize_score(qa.get("historical_accuracy", 0))
    scientific_accuracy = normalize_score(qa.get("scientific_accuracy", 0))
    mathematical_accuracy = normalize_score(qa.get("mathematical_accuracy", 0))
    source_quality = normalize_score(qa.get("source_quality", 0))

    critical_errors = qa.get("critical_errors", [])
    publish_recommendation = qa.get("publish_recommendation", "REJECT")
    anachronism_check = qa.get("anachronism_check", "FAIL")

    print("\n--------------------------------------------------")
    print(
        f"[QA Evaluation] "
        f"Overall={quality_score:.1f} | "
        f"Historical={historical_accuracy:.1f} | "
        f"Scientific={scientific_accuracy:.1f} | "
        f"Math={mathematical_accuracy:.1f} | "
        f"Sources={source_quality:.1f} | "
        f"Anachronism={anachronism_check}"
    )
    print("--------------------------------------------------")

    if (
        quality_score >= 90
        and historical_accuracy >= 90
        and scientific_accuracy >= 90
        and mathematical_accuracy >= 90
        and source_quality >= 85
        and anachronism_check == "PASS"
        and len(critical_errors) == 0
        and publish_recommendation == "PUBLISH"
    ):
        print("\n[QA PASSED] Payload meets all academic thresholds. Posting to WordPress...")
        success = post_to_wordpress(article_data)

        if success:
            scientists[target_index]["status"] = "completed"
            with open("scientists.json", "w", encoding="utf-8") as f:
                json.dump(scientists, f, ensure_ascii=False, indent=2)
            print("[Pipeline Complete] Process completed and queue updated successfully!")
        else:
            print("[CRITICAL] Process failed at WordPress REST API posting stage.")
            sys.exit(1)
    else:
        print(
            "\n[QA FAILED] Target article rejected due to threshold failure:\n"
            f"Overall={quality_score:.1f}, "
            f"Historical={historical_accuracy:.1f}, "
            f"Scientific={scientific_accuracy:.1f}, "
            f"Math={mathematical_accuracy:.1f}, "
            f"Sources={source_quality:.1f}, "
            f"Anachronism={anachronism_check}, "
            f"Critical Errors={critical_errors}"
        )
        sys.exit(1)

if __name__ == "__main__":
    main()
