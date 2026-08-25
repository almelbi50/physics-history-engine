import os
import json
import requests
from google import genai
from google.genai import types

# 1. Configuration & Setup
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WP_URL = os.getenv("WP_URL", "https://phy-lab.com/wp-json/wp/v2")
WP_USER = os.getenv("WP_USER", "physics_generator")
WP_PASSWORD = os.getenv("WP_PASSWORD")

client = genai.Client(api_key=GEMINI_API_KEY)

# 2. Stage 1 Prompt Schema Definition
STAGE_1_PROMPT = """
You are a specialized Physics Historian and Fact-Extraction Engine for phy-lab.com.
Target Scientist: {scientist_name}

Perform deep identity verification, timeline analysis, and physics modeling check using authoritative sources (AIP History Network, APS, Nobel Prize archives).
Return ONLY a valid JSON matching this schema without markdown code blocks or additional text:

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

# 3. Stage 2 Prompt Schema Definition
STAGE_2_PROMPT = """
You are an Academic Physics Editor writing for phy-lab.com.
Based ONLY on the verified JSON structured data provided below for {scientist_name}, synthesize a publication-ready HTML article for WordPress.

JSON Data:
{stage1_json}

Strict Formatting Constraints:
1. All LaTeX inline equations must use \\( ... \\) format.
2. All LaTeX block equations must use \\[ ... \\] format.
3. Use standard HTML tags (<h2>, <h3>, <p>, <ul>, <li>, <table>, <blockquote>). NO markdown headings (##).
4. Tone must be strictly objective, academic, without hyperbolic fluff ("genius", "greatest").
5. Return JSON containing the rendered HTML article and SEO Metadata in this exact structure:

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
    return json.loads(response.text)

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
    
    response = requests.post(
        endpoint,
        auth=(WP_USER, WP_PASSWORD),
        json=payload
    )
    
    if response.status_code in [200, 201]:
        res_json = response.json()
        print(f" Successfully created WP Draft ID: {res_json.get('id')} - {res_json.get('link')}")
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
    
    # Save stage 1 output locally for auditability
    os.makedirs("knowledge_base", exist_ok=True)
    with open(f"knowledge_base/{target['id']}_{scientist_name.replace(' ', '_')}.json", "w", encoding="utf-8") as f:
        f.write(stage1_json_str)

    # Stage 2 execution
    article_data = run_stage_2(scientist_name, stage1_json_str)

    # Quality Gate check
    qa = article_data.get("qa_evaluation", {})
    if qa.get("quality_score", 0) >= 90 and len(qa.get("critical_errors", [])) == 0:
        success = post_to_wordpress(article_data)
        if success:
            target["status"] = "completed"
            with open("scientists.json", "w", encoding="utf-8") as f:
                json.dump(scientists, f, ensure_ascii=False, indent=2)
    else:
        print(f" QA Failed (Score: {qa.get('quality_score')}). Errors: {qa.get('critical_errors')}. Sent to manual review.")

if __name__ == "__main__":
    process_next_scientist()
