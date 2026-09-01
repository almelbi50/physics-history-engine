import json
import os
import re
import sys
import requests
import google.generativeai as genai

# ==============================================================================
# CONFIGURATION & ENVIRONMENT SETUP
# ==============================================================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WP_URL = os.getenv("WP_URL") or "https://phy-lab.com/wp-json/wp/v2"
WP_USER = os.getenv("WP_USER")
WP_PASSWORD = os.getenv("WP_PASSWORD")

# Model & Execution Parameters
MODEL_NAME = os.getenv("GEMINI_MODEL") or "gemini-2.5-flash"
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "1"))

if not GEMINI_API_KEY:
    print("[CRITICAL ERROR] GEMINI_API_KEY environment variable is missing.")
    sys.exit(1)

genai.configure(api_key=GEMINI_API_KEY)
print(f"[Pipeline Init] Initializing model: {MODEL_NAME}")
model = genai.GenerativeModel(MODEL_NAME)

# ==============================================================================
# PROMPT DEFINITIONS
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

STRICT MATHEMATICAL RULE FOR STAGE 1:
All mathematical formulations and physical variables MUST strictly use standard LaTeX notation ($...$ for inline or $$...$$ for block formulas).

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
   - Academic network: Mentors, peer collaborations, and notable scientific debates/disputes.
   - Historical legacy: Paradigm shifts and long-term impact on subsequent physical theories.
3. Theoretical & Mathematical Foundations (~30% of content):
   - Detailed physical principles and FULL mathematical derivations.
   - MANDATORY: ALL physical variables, constants, and equations MUST strictly use LaTeX formatting ($...$ for inline and $$...$$ for block formulas). Plain text math is STRICTLY FORBIDDEN.
4. Experimental Apparatus & Laboratory Metrology (~25% of content):
   - Physical characterization of experimental setups, measurement procedures, calibration, and error analysis.
5. Modern Laboratory & Technological Applications (~25% of content):
   - Practical modern applications and implementation in university laboratory physics experiments.
6. References & Scientific Sources Section (MANDATORY):
   - Dedicated HTML table or structured list of all verified references from Stage 1 before the AI disclosure box.
7. AI Transparency Box:
   - Clean HTML callout box stating article synthesis via Physics Pipeline Engine and academic review for phy-lab.com.

--------------------------------------------------
QUALITY CONTROL EVALUATION (QA)
--------------------------------------------------
Evaluate your generated content internally and fill the `qa_evaluation` object:
- quality_score: Integer (0 to 100).
- has_mandatory_references: Boolean (MUST be true if references table/list is explicitly generated in html_content).
- has_strict_latex: Boolean (MUST be true if all equations and physical variables use $...$ or $$...$$).
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
# HELPER FUNCTIONS
# ==============================================================================

def clean_json_response(text: str) -> str:
    """Extracts JSON content from markdown code blocks if present."""
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        return match.group(1).strip()
    return text

def get_wordpress_category_id(slug: str = "physicists") -> list:
    """Retrieves or defaults the WordPress category ID."""
    if not (WP_USER and WP_PASSWORD):
        return []
    try:
        endpoint = f"{WP_URL.rstrip('/')}/categories?slug={slug}"
        res = requests.get(endpoint, auth=(WP_USER, WP_PASSWORD), timeout=10)
        if res.status_code == 200 and len(res.json()) > 0:
            return [res.json()[0]["id"]]
    except Exception as e:
        print(f"[WordPress Warning] Category lookup error: {e}")
    return []

def post_or_update_wordpress(article_data: dict) -> bool:
    """Posts a new article or updates an existing post if the slug already exists."""
    if not (WP_USER and WP_PASSWORD):
        print("[Error] Missing WordPress authentication credentials.")
        return False

    categories = get_wordpress_category_id("physicists")
    
    target_slug = article_data.get("seo", {}).get("slug")
    if not target_slug:
        raw_title = article_data.get("post_title", "physicist")
        target_slug = re.sub(r'\s+', '-', raw_title).lower()

    search_endpoint = f"{WP_URL.rstrip('/')}/posts?slug={target_slug}&status=any"
    existing_post_id = None

    try:
        search_res = requests.get(search_endpoint, auth=(WP_USER, WP_PASSWORD), timeout=15)
        if search_res.status_code == 200 and len(search_res.json()) > 0:
            existing_post_id = search_res.json()[0]["id"]
            print(f"[WordPress API] Found existing post ID: {existing_post_id} for slug '{target_slug}'. Executing UPDATE.")
    except Exception as e:
        print(f"[WordPress API Warning] Post lookup failed: {e}")

    payload = {
        "title": article_data["post_title"],
        "content": article_data["html_content"].strip(),
        "status": "draft",
        "slug": target_slug,
        "excerpt": article_data.get("seo", {}).get("meta_description", ""),
        "categories": categories
    }

    if existing_post_id:
        endpoint = f"{WP_URL.rstrip('/')}/posts/{existing_post_id}"
    else:
        endpoint = f"{WP_URL.rstrip('/')}/posts"

    try:
        response = requests.post(
            endpoint,
            auth=(WP_USER, WP_PASSWORD),
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        if response.status_code in [200, 201]:
            action = "Updated" if existing_post_id else "Created"
            print(f"[WordPress API] Post {action} successfully. ID: {response.json().get('id')}")
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
    """Executes Stage 1, Stage 2, QA Validation, and WP publishing for an entity."""
    p_name_en = entity.get("name", "Unknown")
    p_name_ar = entity.get("arabic_name") or entity.get("name_ar") or p_name_en

    print(f"\n==================================================")
    print(f"Processing Entity ID {entity.get('id')}: {p_name_ar} ({p_name_en})")
    print(f"==================================================")

    # Stage 1 Execution
    print("[Stage 1] Executing Deep Research & Blueprint Structuring...")
    prompt_1 = STAGE_1_PROMPT.format(physicists_name=p_name_en, physicists_name_ar=p_name_ar)
    
    try:
        res_1 = model.generate_content(prompt_1)
        stage_1_json_str = clean_json_response(res_1.text)
        stage_1_data = json.loads(stage_1_json_str)
        print("[Stage 1] Blueprint generated successfully.")
    except Exception as e:
        print(f"[CRITICAL ERROR] Stage 1 Generation Failed: {e}")
        return False

    # Stage 2 Execution
    print("[Stage 2] Executing HTML Synthesis & Academic QA Evaluation...")
    prompt_2 = STAGE_2_PROMPT.format(stage_1_json=json.dumps(stage_1_data, ensure_ascii=False))

    try:
        res_2 = model.generate_content(prompt_2)
        stage_2_json_str = clean_json_response(res_2.text)
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
        print(f"[Debug] Files present in workspace: {os.listdir(BASE_DIR)}")
        sys.exit(1)

    dataset_name = os.path.basename(json_file_path)
    print(f"[Pipeline Engine] Loaded dataset file: '{dataset_name}'")

    with open(json_file_path, "r", encoding="utf-8") as f:
        physicists = json.load(f)

    print(f"[Debug] Total records loaded from {dataset_name}: {len(physicists)}")

    # Strict filtering for pending entities
    pending_entities = [
        p for p in physicists 
        if str(p.get("status", "")).strip().lower() == "pending"
    ]

    print(f"[Debug] Total pending entities detected: {len(pending_entities)}")

    if not pending_entities:
        print("[Pipeline Engine] No pending entities found to process. Exiting cleanly.")
        return

    # Select batch size
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

    # Save state changes
    with open(json_file_path, "w", encoding="utf-8") as f:
        json.dump(physicists, f, ensure_ascii=False, indent=2)
    print(f"[Pipeline Engine] State saved successfully to {dataset_name}.")

if __name__ == "__main__":
    main()
