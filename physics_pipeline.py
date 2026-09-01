#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
PHYSICS PIPELINE ENGINE - PHY-LAB.COM
================================================================================
Developer: AI-Enabled Technology Solutions Developer & Physics Lab Technician
Core Function: Automated Academic Research, Structural Blueprinting, 
               LaTeX Sanitization, and WordPress REST API Integration.
Primary Model: gemini-3.6-flash
================================================================================
"""

import json
import os
import re
import sys
import socket
import requests
import urllib3.util.connection as urllib_util
import google.generativeai as genai

# ==============================================================================
# FORCE IPV4 RESOLUTION (Eliminates GitHub Actions [Errno 101] Network is unreachable)
# ==============================================================================
def allowed_gai_family():
    """Forces socket resolution to use IPv4 only."""
    return socket.AF_INET

urllib_util.allowed_gai_family = allowed_gai_family

# ==============================================================================
# CONFIGURATION & ENVIRONMENT SETUP
# ==============================================================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WP_URL = os.getenv("WP_URL") or "https://phy-lab.com/wp-json/wp/v2"
WP_USER = os.getenv("WP_USER")
WP_PASSWORD = os.getenv("WP_PASSWORD")

# Primary model default set to gemini-3.6-flash with fallback hierarchy
ENV_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash").strip()

MODEL_CANDIDATES = list(dict.fromkeys([
    ENV_MODEL,
    "gemini-3.6-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash"
]))

BATCH_SIZE = int(os.getenv("BATCH_SIZE", "1"))

if not GEMINI_API_KEY:
    print("[CRITICAL ERROR] GEMINI_API_KEY environment variable is missing.")
    sys.exit(1)

genai.configure(api_key=GEMINI_API_KEY)

WP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

# ==============================================================================
# HELPER: ROBUST MODEL GENERATION WITH FALLBACK
# ==============================================================================
def generate_with_fallback(prompt: str) -> str:
    """Tries generating content sequentially across target candidate models."""
    last_exception = None
    for model_name in MODEL_CANDIDATES:
        try:
            print(f"[Gemini API] Attempting generation with model: '{model_name}'...")
            candidate_model = genai.GenerativeModel(model_name)
            response = candidate_model.generate_content(prompt)
            return response.text
        except Exception as e:
            err_msg = str(e)
            print(f"[Model Exception] Engine '{model_name}' returned error: {err_msg}")
            last_exception = e
            continue
    raise last_exception if last_exception else RuntimeError("All configured model candidates failed.")

# ==============================================================================
# PROMPT DEFINITIONS WITH STRICT ESCAPING & STRUCTURE
# ==============================================================================

STAGE_1_PROMPT = """You are a senior academic research assistant in physics and history of science.

Input Physicist Entity:
Name: {physicists_name}
Arabic Name: {physicists_name_ar}

Your task is to conduct deep, rigorous research and structure a factual blueprint for an exhaustive academic profile.

Perform systematic validation across these structural dimensions:
1. Exact transliterated Arabic primary name.
2. Concise biographical timeline (Birth/Death/Institutional affiliations).
3. Academic network, peer collaborations, mentors, and scientific disputes/debates.
4. Core scientific contributions (Laws, equations, empirical apparatus, physical constants).
5. Historical legacy, epistemological impact, paradigm shifts, and influence on subsequent physics.
6. Primary and peer-reviewed sources (MANDATORY).

STRICT MATHEMATICAL & ESCAPING RULES FOR STAGE 1:
- All LaTeX equations MUST use double backslashes inside JSON strings (e.g., "\\\\tau", "\\\\theta", "\\\\frac", "\\\\text", "\\\\Rightarrow").
- Use $...$ for inline math and $$...$$ for block formulas.

You MUST respond strictly with a valid JSON object matching this schema:
{{
  "canonical_name_ar": "string",
  "canonical_name_en": "string",
  "lifespan": "string",
  "nationality": "string",
  "primary_fields": ["string"],
  "academic_network": {{
    "mentors_and_influences": ["string"],
    "collaborators_and_peers": ["string"],
    "scientific_disputes_and_debates": ["string"]
  }},
  "major_discoveries": [
    {{
      "concept_ar": "string",
      "concept_en": "string",
      "mathematical_formulation": "string (LaTeX formatted)",
      "physical_significance": "string",
      "experimental_apparatus": "string"
    }}
  ],
  "historical_legacy": {{
    "paradigm_shifts": "string",
    "influence_on_subsequent_physics": "string"
  }},
  "verified_sources": [
    {{
      "title": "string",
      "author_or_institution": "string",
      "authority_level": "string",
      "url": "string"
    }}
  ]
}}
"""

STAGE_2_PROMPT = """You are an expert scientific communicator, senior physics editor, and technical educator writing for "phy-lab.com" (مبادرة معامل الفيزياء).

RESEARCH BLUEPRINT (STAGE 1 OUTPUT):
{stage_1_json}

Your goal is to write a comprehensive, publication-ready academic article in clean HTML, adhering strictly to the highest standards of scientific accuracy, historical precision, and technical formatting.

--------------------------------------------------
MANDATORY CONTENT WEIGHT & STRUCTURE (80% PHYSICS / 20% HISTORY)
--------------------------------------------------
1. H1 Main Title: Exact Arabic Name ONLY (e.g., "شارل أوغسطين دي كولوم"). No extra subtitles, numbers, or descriptors.
2. Academic Context, Scientific Network & Historical Legacy (~20% of content):
   - Concise historical background.
   - Academic network: Mentors, peer collaborations, and scientific debates/disputes.
   - Historical legacy: Paradigm shifts and long-term impact on physics.
3. Theoretical & Mathematical Foundations (~30% of content):
   - Detailed physical principles and FULL mathematical derivations.
   - MANDATORY LATEX ESCAPING RULES: 
     * ALL physical variables, constants, and equations MUST use MathJax formatting: $...$ for inline and $$...$$ for block formulas.
     * ALL LaTeX control sequences MUST be double-escaped inside JSON strings: use "\\\\tau", "\\\\theta", "\\\\kappa", "\\\\frac", "\\\\text", "\\\\cdot", "\\\\approx", "\\\\propto", "\\\\Rightarrow".
     * NEVER write unescaped single backslashes in JSON output.
4. Experimental Apparatus & Laboratory Metrology (~25% of content):
   - Physical characterization of experimental setups, measurement procedures, calibration, and error analysis.
5. Modern Laboratory & Technological Applications (~25% of content):
   - Practical modern applications and implementation in university laboratory physics experiments.
6. References & Scientific Sources Section (MANDATORY):
   - Dedicated HTML table or structured list of all verified references from Stage 1 before the AI disclosure box.
7. AI Transparency Box (MANDATORY EXACT TEXT):
   - You MUST include a clean HTML callout box at the very end with this EXACT Arabic text:
   "<div style='background-color: #f8f9fa; border-right: 4px solid #0056b3; padding: 15px; margin-top: 30px; border-radius: 4px;'><strong>تنويه:</strong> أُعدّ هذا المقال آليًا بواسطة وكيل ذكاء اصطناعي وفق معايير محددة للبحث والتحقق والصياغة العلمية، مع الاستناد إلى مصادر موثوقة. ويُنصح بالرجوع إلى المراجع المرفقة للتحقق من التفاصيل والمعلومات الواردة في المقال.</div>"

--------------------------------------------------
QUALITY CONTROL EVALUATION (QA)
--------------------------------------------------
Evaluate your generated content internally and fill the `qa_evaluation` object:
- quality_score: Integer (0 to 100).
- has_mandatory_references: Boolean (MUST be true if references table/list is explicitly generated in html_content).
- has_strict_latex: Boolean (MUST be true if all equations and physical variables use valid LaTeX without spaces or non-standard macros).
- critical_errors: List of string errors found.
- publish_recommendation: "PUBLISH" if score >= 90, has_mandatory_references is true, and has_strict_latex is true, else "REVIEW".

You MUST respond strictly with a valid JSON object matching this schema:
{{
  "post_title": "string (Exact Arabic Name Only)",
  "html_content": "string (Full HTML article with inline LaTeX and HTML references table)",
  "seo": {{
    "meta_description": "string",
    "slug": "string",
    "keywords": ["string"]
  }},
  "qa_evaluation": {{
    "quality_score": 0,
    "has_mandatory_references": true,
    "has_strict_latex": true,
    "critical_errors": [],
    "publish_recommendation": "PUBLISH"
  }}
}}
"""

# ==============================================================================
# HELPER FUNCTIONS & SANITIZATION ENGINE
# ==============================================================================

def clean_json_response(text: str) -> str:
    """Extracts JSON content from markdown code blocks and purges illegal control characters."""
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        text = match.group(1).strip()
    # Strip raw C0 control characters (U+0000-U+001F) that break json.loads with
    # "Invalid control character" errors, while preserving tab/newline/carriage return
    # so multi-line string values inside the JSON remain intact.
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
    return text

def sanitize_latex_execution(html_content: str) -> str:
    """Restores broken LaTeX commands stripped by Python string escapes or JSON parsing."""
    if not html_content:
        return ""

    html_content = html_content.replace('\t', r'\t')
    html_content = re.sub(r'\\\$', '$', html_content)

    html_content = html_content.replace(r"\implies", r"\Rightarrow")
    html_content = html_content.replace("implies", r"\Rightarrow")

    keywords = [
        'tau', 'theta', 'kappa', 'sigma', 'phi', 'pi', 'varepsilon', 'epsilon',
        'alpha', 'beta', 'gamma', 'delta', 'lambda', 'mu', 'nu', 'rho', 'omega',
        'frac', 'text', 'cdot', 'approx', 'propto', 'Rightarrow', 'left', 'right',
        'sin', 'cos', 'tan', 'sqrt', 'int', 'sum', 'ln', 'log'
    ]

    # --------------------------------------------------------------------
    # Stash every $$...$$ display block behind a placeholder BEFORE touching
    # inline math. Doing the two passes as two independent regexes on the
    # same text is unsafe: the inline pattern's first '$' cannot land on the
    # first '$' of a "$$" pair, so it starts one character in and leaves a
    # stray '$' dangling on each side of every display block. Those stray
    # '$' characters then pair up with the *next* unrelated inline "$...$"
    # further down the article and swallow whole sentences into bogus math
    # spans. Placeholders make that impossible: the whole "$$...$$" span
    # (all four delimiter characters) is consumed in one match, so nothing
    # is left over for the inline pass to misinterpret.
    # --------------------------------------------------------------------
    display_blocks = []

    def stash_display_math(match):
        math_str = match.group(1)
        for kw in keywords:
            pattern = r'(?<!\\)\b' + kw + r'\b'
            math_str = re.sub(pattern, r'\\' + kw, math_str)
        display_blocks.append(math_str.strip())
        return f"\x00DISPLAYMATH{len(display_blocks) - 1}\x00"

    html_content = re.sub(r'\$\$\s*([\s\S]+?)\s*\$\$', stash_display_math, html_content)

    def repair_math_block(match):
        math_str = match.group(1)
        for kw in keywords:
            pattern = r'(?<!\\)\b' + kw + r'\b'
            math_str = re.sub(pattern, r'\\' + kw, math_str)
        math_str = re.sub(r'\\\.\s*', '.', math_str)
        # The site's MathJax-LaTeX plugin (phy-lab.com) does not enable single-$
        # as an inline math delimiter by default (only $$...$$ and \(...\) are
        # recognized natively) — see plugin docs. Convert inline math to \( ... \)
        # here at publish time so it actually renders, while the generation-stage
        # prompts keep using the project's mandated $ ... $ authoring syntax.
        return f"\\({math_str.strip()}\\)"

    # By now every literal "$$" has been removed (replaced by placeholders),
    # so this can only ever match genuine single-$ inline pairs.
    html_content = re.sub(r'\$([^$\n]+?)\$', repair_math_block, html_content)

    for i, content in enumerate(display_blocks):
        html_content = html_content.replace(f"\x00DISPLAYMATH{i}\x00", f"$${content}$$")

    return html_content.strip()

def get_wordpress_category_id(slug: str = "physicists") -> list:
    if not (WP_USER and WP_PASSWORD):
        return []
    try:
        endpoint = f"{WP_URL.rstrip('/')}/categories?slug={slug}"
        res = requests.get(endpoint, auth=(WP_USER, WP_PASSWORD), headers=WP_HEADERS, timeout=15)
        if res.status_code == 200 and len(res.json()) > 0:
            return [res.json()[0]["id"]]
    except Exception as e:
        print(f"[WordPress Warning] Category lookup error: {e}")
    return []

def post_or_update_wordpress(article_data: dict) -> bool:
    if not (WP_USER and WP_PASSWORD):
        print("[Error] Missing WordPress authentication credentials.")
        return False

    categories = get_wordpress_category_id("physicists")
    sanitized_content = sanitize_latex_execution(article_data["html_content"])
    
    target_slug = article_data.get("seo", {}).get("slug")
    if not target_slug:
        raw_title = article_data.get("post_title", "physicist")
        target_slug = re.sub(r'\s+', '-', raw_title).lower()

    search_endpoint = f"{WP_URL.rstrip('/')}/posts?slug={target_slug}&status=any"
    existing_post_id = None

    try:
        search_res = requests.get(search_endpoint, auth=(WP_USER, WP_PASSWORD), headers=WP_HEADERS, timeout=15)
        if search_res.status_code == 200 and len(search_res.json()) > 0:
            existing_post_id = search_res.json()[0]["id"]
            print(f"[WordPress API] Found existing post ID: {existing_post_id} for slug '{target_slug}'. Executing UPDATE.")
    except Exception as e:
        print(f"[WordPress API Warning] Post lookup failed: {e}")

    payload = {
        "title": article_data["post_title"],
        "content": sanitized_content,
        "status": "draft",
        "slug": target_slug,
        "excerpt": article_data.get("seo", {}).get("meta_description", ""),
        "categories": categories
    }

    if existing_post_id:
        endpoint = f"{WP_URL.rstrip('/')}/posts/{existing_post_id}"
    else:
        endpoint = f"{WP_URL.rstrip('/')}/posts"

    post_headers = WP_HEADERS.copy()
    post_headers["Content-Type"] = "application/json"

    try:
        response = requests.post(
            endpoint,
            auth=(WP_USER, WP_PASSWORD),
            json=payload,
            headers=post_headers,
            timeout=30
        )
        if response.status_code in [200, 201]:
            action = "Updated" if existing_post_id else "Created"
            print(f"[WordPress API] Post {action} successfully. Post ID: {response.json().get('id')}")
            return True
        else:
            print(f"[WordPress API Error] Status {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"[WordPress API Exception] {e}")
        return False

# ==============================================================================
# PIPELINE EXECUTION ENGINE
# ==============================================================================

def process_physicist(entity: dict) -> bool:
    p_name_en = entity.get("name", "Unknown")
    p_name_ar = entity.get("arabic_name") or entity.get("name_ar") or p_name_en

    print(f"\n==================================================")
    print(f"Processing Entity ID {entity.get('id')}: {p_name_ar} ({p_name_en})")
    print(f"==================================================")

    # Stage 1 Execution
    print("[Stage 1] Executing Deep Research & Blueprint Structuring...")
    prompt_1 = STAGE_1_PROMPT.format(physicists_name=p_name_en, physicists_name_ar=p_name_ar)
    
    try:
        raw_text_1 = generate_with_fallback(prompt_1)
        stage_1_json_str = clean_json_response(raw_text_1)
        stage_1_data = json.loads(stage_1_json_str)
        print("[Stage 1] Blueprint generated successfully.")
    except Exception as e:
        print(f"[CRITICAL ERROR] Stage 1 Generation Failed: {e}")
        return False

    # Stage 2 Execution
    print("[Stage 2] Executing HTML Synthesis & Academic QA Evaluation...")
    prompt_2 = STAGE_2_PROMPT.format(stage_1_json=json.dumps(stage_1_data, ensure_ascii=False))

    try:
        raw_text_2 = generate_with_fallback(prompt_2)
        stage_2_json_str = clean_json_response(raw_text_2)
        stage_2_data = json.loads(stage_2_json_str)
    except Exception as e:
        print(f"[CRITICAL ERROR] Stage 2 Generation Failed: {e}")
        return False

    # QA Gateway Verification
    qa = stage_2_data.get("qa_evaluation", {})
    quality_score = qa.get("quality_score", 0)
    has_references = str(qa.get("has_mandatory_references", False)).lower() == "true"
    has_latex = str(qa.get("has_strict_latex", False)).lower() == "true"
    recommendation = qa.get("publish_recommendation", "REJECT")

    print(f"[QA Gate] Score: {quality_score}/100 | References: {has_references} | Strict LaTeX: {has_latex} | Rec: {recommendation}")

    if (
        quality_score >= 90
        and has_references
        and has_latex
        and recommendation == "PUBLISH"
    ):
        print("[QA Gate PASSED] Publishing draft to WordPress...")
        return post_or_update_wordpress(stage_2_data)
    else:
        print(f"[QA Gate FAILED] Critical Errors: {qa.get('critical_errors', [])}. Post withheld.")
        return False

# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================

def main():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    candidates = ["physicists.json", "scientists.json"]
    json_file_path = None

    for candidate in candidates:
        target_path = os.path.join(BASE_DIR, candidate)
        if os.path.exists(target_path):
            json_file_path = target_path
            break

    if not json_file_path:
        print(f"[CRITICAL ERROR] No dataset found. Checked paths: {candidates}")
        sys.exit(1)

    dataset_name = os.path.basename(json_file_path)
    print(f"[Pipeline Engine] Loaded dataset file: '{dataset_name}'")

    with open(json_file_path, "r", encoding="utf-8") as f:
        physicists = json.load(f)

    pending_entities = [
        p for p in physicists 
        if str(p.get("status", "")).strip().lower() == "pending"
    ]

    print(f"[Debug] Total pending entities detected: {len(pending_entities)}")

    if not pending_entities:
        print("[Pipeline Engine] No pending entities found to process. Exiting cleanly.")
        return

    batch = pending_entities[:BATCH_SIZE]
    print(f"[Pipeline Engine] Processing batch of {len(batch)} item(s)...")

    for entity in batch:
        success = process_physicist(entity)
        if success:
            entity["status"] = "completed"
            entity_name = entity.get("arabic_name") or entity.get("name")
            print(f"[Success] Entity '{entity_name}' processed and marked as 'completed'.")
        else:
            entity_name = entity.get("arabic_name") or entity.get("name")
            print(f"[Failure] Entity '{entity_name}' failed processing. Retaining status 'pending'.")

    with open(json_file_path, "w", encoding="utf-8") as f:
        json.dump(physicists, f, ensure_ascii=False, indent=2)
    print(f"[Pipeline Engine] State saved successfully to {dataset_name}.")

if __name__ == "__main__":
    main()
