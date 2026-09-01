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
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*
