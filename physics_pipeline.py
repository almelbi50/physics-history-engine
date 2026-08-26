import os
import json
import re
import sys
import requests
from google import genai
from google.genai import types

# 1. Configuration & Setup
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WP_URL = os.getenv("WP_URL", "https://phy-lab.com/wp-json/wp/v2")
WP_USER = os.getenv("WP_USER", "physics_generator")
WP_PASSWORD = os.getenv("WP_PASSWORD")

client = genai.Client(api_key=GEMINI_API_KEY)

def clean_and_parse_json(text):
    cleaned = re.sub(r'^```json\s*', '', text.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r'^```\s*', '', cleaned, flags=re.MULTILINE)
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned, strict=False)
    except json.JSONDecodeError:
        # Fix raw unescaped backslashes safely without destroying LaTeX commands
        fixed_text = re.sub(r'\\(?![/"bfnrtu]|u[0-9a-fA-F]{4})', r'\\\\', cleaned)
        return json.loads(fixed_text, strict=False)

# 2. Stage 1 Prompt Schema Definition
STAGE_1_PROMPT = """
You are a specialized Physics Historian and Fact-Extraction Engine for phy-lab.com.
Target Scientist: {scientist_name}

Perform deep identity verification, timeline analysis, and physics modeling check using authoritative sources.
Return ONLY a valid JSON matching this schema:

{{
  "entity_resolution": {{
    "canonical_name": "",
    "arabic_name": "",
    "english_name": "",
    "alternative_names": [],
    "birth_date": "YYYY-MM-DD",
    "death_date": "YYYY-MM-DD",
    "birth_place": "",
    "nationality_context": ""
  }},
  "importance_evaluation": {{
    "score": 0,
    "eligible_for_pipeline": true
  }},
  "timelines": {{
    "timeline_a_biological": [{{"year": 0, "event": ""}}],
    "timeline_b_scientific": [{{"year": 0, "event_type": "", "description": ""}}]
  }},
  "physics_analysis": [
    {{
      "contribution_name": "",
      "scientific_problem": "",
      "hypothesis": "",
      "model_or_framework": "",
      "experiment_details": "",
      "equations": [
        {{
          "latex_raw": "",
          "variables_definition": {{}},
          "validity_domain": "",
          "assumptions": ""
        }}
      ],
      "result_and_impact": "",
      "limitations_and_boundary_conditions": ""
    }}
  ],
  "knowledge_graph_relations": {{
    "teachers": [],
    "students": [],
    "collaborators": [],
    "precursors_built_upon": [],
    "influenced_scientists": []
  }},
  "verified_sources": [
    {{
      "title": "",
      "institution_or_author": "",
      "authority_level": "A",
      "supported_claim": ""
    }}
  ]
}}
"""

# 3. Stage 2 Prompt Schema Definition (Optimized LaTeX & HTML Formatting)
STAGE_2_PROMPT = """
You are an Academic Physics Editor writing for phy-lab.com.
Based ONLY on the verified JSON structured data provided below for {scientist_name}, synthesize a publication-ready HTML article for WordPress.

JSON Data:
{stage1_json}

Strict Formatting & LaTeX Rules:
1. ALL LaTeX block equations MUST use standard double dollar signs: $$ ... $$ (e.g. $$\\sin(\\theta_i) = k \\sin(\\theta_r)$$). Never use bracket notation like \\[ \\].
2. ALL inline LaTeX variables MUST use single dollar signs: $ ... $ (e.g. $\\theta_i$). Never use parentheses notation like \\( \\).
3. Do NOT use <blockquote> tags for references! Format references and verified sources as a clean, styled HTML list (<ol> or <ul>) or a structured <table>.
4. Use clear headings (<h2>, <h3>) and semantic HTML tags (<p>, <ul>, <li>, <table>, <strong>).
5. Tone must be strictly academic, objective, without hyperbolic fluff.
6. Write in professional academic Arabic suitable for university physics laboratories.

Return JSON containing the rendered HTML article and SEO Metadata in this exact structure:

{{
  "post_title": "",
  "html_content": "",
  "seo": {{
    "meta_description": "",
    "primary_keyword": "",
    "slug": ""
  }},
  "qa_evaluation": {{
    "quality_score": 95,
    "critical_errors": [],
    "publish_recommendation": "PUBLISH"
  }}
}}
"""

def run_stage_1(scientist_name):
    print(f"[Stage 1] Extracting structured facts for: {scientist_name}...")
    prompt = STAGE_1_PROMPT.format(scientist_name=scientist_name)
    response = client.models.generate_content(
        model='gemini-3.6-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )
    return response.text

def run_stage_2(scientist_name, stage1_json):
    print(f"[Stage 2] Generating WordPress HTML & QA for: {scientist_name}...")
    prompt = STAGE_2_PROMPT.format(scientist_name=scientist_name, stage1_json=stage1_json)
    response = client.models.generate_content(
        model='gemini-3.6-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )
    return clean_and_parse_json(response.text)

def post_to_wordpress(article_data):
    print("[WordPress API] Uploading draft to phy-lab.com...")
    endpoint = f"{WP_URL.rstrip('/')}/posts"
    
    payload = {
        "title": article_data["post_title"],
        "content": article_data["html_content"],
        "status": "draft",
        "slug": article_data["seo"]["slug"],
        "excerpt": article_data["seo"]["meta_description"]
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    response = requests.post(
        endpoint,
        auth=(WP_USER, WP_PASSWORD),
        headers=headers,
        json=payload,
        timeout=30
    )
    
    if response.status_code in [200, 201]:
        res_json = response.json()
        print("--------------------------------------------------")
        print(f" SUCCESS! Draft Created with ID: {res_json.get('id')}")
        print(f" Direct Edit URL: https://phy-lab.com/wp-admin/post.php?post={res_json.get('id')}&action=edit")
        print("--------------------------------------------------")
        return True
    else:
        print(f" Failed to post to WordPress: {response.status_code} - {response.text}")
        return False

def process_next_scientist():
    with open("scientists.json", "r", encoding="utf-8") as f:
        scientists = json.load(f)
        
    target = None
    for s in scientists:
        if s["status"] == "pending":
            target = s
            break
            
    if not target:
        print("No pending scientists found.")
        return

    scientist_name = target["name"]
    print(f"Processing Scientist: {scientist_name}")

    # Stage 1 execution
    stage1_json_str = run_stage_1(scientist_name)
    
    os.makedirs("knowledge_base", exist_ok=True)
    with open(f"knowledge_base/{target['id']}_{scientist_name.replace(' ', '_')}.json", "w", encoding="utf-8") as f:
        f.write(stage1_json_str)

    # Stage 2 execution
    article_data = run_stage_2(scientist_name, stage1_json_str)

    qa = article_data.get("qa_evaluation", {})
    quality_score = qa.get("quality_score", 0)
    critical_errors = qa.get("critical_errors", [])

    print(f"[QA Evaluation] Score: {quality_score} | Errors: {critical_errors}")

    if quality_score >= 90 and len(critical_errors) == 0:
        success = post_to_wordpress(article_data)
        if success:
            target["status"] = "completed"
            with open("scientists.json", "w", encoding="utf-8") as f:
                json.dump(scientists, f, ensure_ascii=False, indent=2)
            print("Process completed successfully!")
        else:
            print("Process failed at WordPress posting stage.")
            sys.exit(1)
    else:
        print(f"QA Failed (Score: {quality_score}). Errors: {critical_errors}.")
        sys.exit(1)

if __name__ == "__main__":
    process_next_scientist()
