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
    "gemini-3.1-pro-preview",
    "gemini-3-flash-preview"
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
# IMPORTANT / LESSON LEARNED (2026-09-10): an earlier version of this function
# forced generation_config={"response_mime_type": "application/json", ...} on
# every call, intending to fix the Run #85/#86 "Expecting ',' delimiter"
# failure at the transport level. It did fix that specific parse error, but
# introduced a worse regression: enabling Gemini's native JSON mode made the
# model produce dramatically SHORTER html_content than plain generation does
# -- confirmed empirically on two separate live regenerations of entity 017
# (Max Planck): 731 words and then 814 words, versus 1,600-1,991 words for
# every other successfully-published article (entities 013-016) that used
# plain (non-JSON-mode) generation. Raising max_output_tokens did NOT fix
# this; JSON mode itself biases the model toward closing long string fields
# early to guarantee structural validity.
#
# Conclusion: generation must stay IDENTICAL to what produced entities
# 001-016 (a plain generate_content(prompt) call, no generation_config at
# all). All JSON-validity robustness now lives entirely downstream in
# parse_json_with_repairs() / clean_json_response(), which only ever run
# AFTER generation, as a repair pass on the raw text -- so they cannot
# influence how much the model chooses to write.
def generate_with_fallback(prompt: str) -> str:
    """Tries generating content sequentially across target candidate models.

    Deliberately identical to the original, pre-2026-09-10 implementation:
    a single plain generate_content(prompt) call per candidate model, no
    generation_config. This preserves the exact generation behavior that
    produced full-length (13,600-15,800 character) articles for entities
    001-016; JSON-validity is handled entirely as a post-hoc repair step by
    the caller (see parse_json_with_repairs), never by changing how the
    model generates.
    """
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
    # NOTE: backslash/quote repair used to run unconditionally right here,
    # on every response, whether or not it actually needed repairing. That
    # is what caused the 2026-09-10 regression: repair_invalid_backslash_escapes
    # doubling \n even in already-perfectly-valid JSON (corrupting a genuine,
    # intended newline into literal visible "\n" text) for entities that
    # never needed any repair in the first place. Both repair passes now
    # live exclusively in parse_json_with_repairs() below and only ever run
    # AFTER a first json.loads() attempt on this cleaned-but-unrepaired text
    # has already failed -- so JSON that was already valid (the normal case
    # for entities 001-016) is guaranteed to pass through byte-for-byte
    # unmodified beyond markdown-fence/control-character stripping.
    return text

# Every backslash in JSON must start one of: \" \\ \/ \b \f \n \r \t \uXXXX.
# Gemini is explicitly instructed (STAGE_1_PROMPT / STAGE_2_PROMPT) to
# double-escape LaTeX backslashes so they survive as literal backslashes
# after json.loads(), but it does not always comply — it frequently emits
# a single backslash in front of a LaTeX macro name instead (e.g. the
# 4-character sequence \, t, a, u instead of the correct \, \, t, a, u).
_JSON_ESCAPE_REPAIR_RE = re.compile(r'\\(?:(["\\/])|(u[0-9A-Fa-f]{4})|(.))', re.S)

def repair_invalid_backslash_escapes(text: str) -> str:
    """
    Repairs single backslashes the model left in front of LaTeX macros so
    json.loads() can parse the response, instead of either of its two
    failure modes:

    1. A macro whose first letter is not a legal JSON escape character
       (\\a, \\c, \\d, \\g, \\k, \\l, \\m, \\o, \\p, \\s, \\v, or any
       uppercase letter as in \\Rightarrow) makes json.loads() raise
       "Invalid \\escape" and the whole entity is dropped. This is
       exactly what happened to entity 011 (سادي كارنو / Sadi Carnot) in
       workflow run #76: Stage 2 returned "\\Rightarrow"-style macros
       with a single backslash, and the run logged "[CRITICAL ERROR]
       Stage 2 Generation Failed: Invalid \\escape: line 3 column 3933"
       and left the entity's status as "pending" forever (the job still
       exits 0, so GitHub shows a green check while nothing is ever
       published for that entity).
    2. A macro whose first letter DOES happen to be a legal JSON escape
       (\\t -> tau/text/tan, \\b -> beta, \\f -> frac, \\r -> rho/right,
       \\u -> upsilon vs. a \\uXXXX unicode escape, \\n -> nu/nabla/neg)
       is silently decoded into a stray control character followed by the
       remaining letters instead of raising anything, corrupting the
       macro without any error at all.

    2026-09-10 FIX: an earlier version of this function kept \\n
    (backslash-n) on the "already valid, leave alone" side on the theory
    that it is more often an intended real line break in html_content than
    the start of "\\nu". Live production data (entity 017 / Max Planck,
    WordPress post 3312) proved that assumption wrong: \\nu is the
    frequency symbol and appears constantly in this exact article (Planck's
    law), and every occurrence was corrupted into a literal newline
    character followed by a stray "u" -- which then also broke the
    $...$ -> \\(...\\) inline-math conversion in sanitize_latex_execution()
    downstream, since that regex excludes real newlines from its match.
    html_content is HTML, built entirely from block tags (<p>, <li>, ...),
    so an actual newline character inside a string value has no rendering
    value here; \\n is now ALWAYS doubled like any other unrecognized
    macro-start, at the cost of an extremely rare genuinely-intended
    newline surviving as the visible two characters "\\n" instead of a
    real line break -- a purely cosmetic, non-breaking regression, versus
    silently corrupting every \\nu/\\nabla/\\neg in the article.

    Every backslash that is not already part of a genuinely valid JSON
    escape (\\", \\\\, \\/, or a real \\uXXXX unicode escape) is doubled,
    so json.loads() sees a literal backslash followed by the macro name
    rather than an illegal or misleading escape sequence.
    """
    def _fix(match: "re.Match[str]") -> str:
        if match.group(1) is not None or match.group(2) is not None:
            return match.group(0)
        return "\\\\" + match.group(3)
    return _JSON_ESCAPE_REPAIR_RE.sub(_fix, text)

def escape_raw_control_chars_in_strings(text: str) -> str:
    """
    Repairs literal, raw control characters (most commonly an actual newline
    character, 0x0A) that appear directly inside a JSON string value instead
    of the proper 2-character escape sequence. Per the JSON spec, every
    control character (U+0000-U+001F) inside a string MUST be escaped; a raw
    one makes json.loads() raise "Invalid control character at: ...".

    This is exactly the failure seen on the 2026-09-10 re-run of entity 017
    (Max Planck) once the article-length fix restored full-length generation:
    "[CRITICAL ERROR] Stage 2 Generation Failed: Invalid control character
    at: line 3 column 13942" -- deep into a long, otherwise well-formed
    html_content string, where the model included a literal newline instead
    of writing "\\n".

    LAST-RESORT repair only, exactly like repair_unescaped_string_quotes: it
    never runs on JSON that already parses (see parse_json_with_repairs), so
    it cannot alter or regress any previously-working generation.

    Strategy: walk the text tracking whether the scanner is inside a JSON
    string (same in_string bookkeeping as repair_unescaped_string_quotes).
    Any already-escaped sequence (a backslash followed by any character) is
    copied through untouched. Any RAW character with a code point below
    0x20 encountered while inside a string is replaced with its proper JSON
    escape (\\n, \\r, \\t, or \\u00XX for anything else); the same character
    outside a string (ordinary JSON whitespace between tokens) is left
    completely untouched, since that is always legal.
    """
    _SIMPLE_ESCAPES = {'\n': '\\n', '\r': '\\r', '\t': '\\t'}
    out = []
    in_string = False
    i, n = 0, len(text)
    while i < n:
        ch = text[i]

        if not in_string:
            out.append(ch)
            if ch == '"':
                in_string = True
            i += 1
            continue

        if ch == '\\' and i + 1 < n:
            out.append(ch)
            out.append(text[i + 1])
            i += 2
            continue

        if ch == '"':
            out.append(ch)
            in_string = False
            i += 1
            continue

        if ord(ch) < 0x20:
            out.append(_SIMPLE_ESCAPES.get(ch, f'\\u{ord(ch):04x}'))
            i += 1
            continue

        out.append(ch)
        i += 1

    return ''.join(out)

def repair_unescaped_string_quotes(text: str) -> str:
    """
    Best-effort structural repair for literal, unescaped double-quote (\")
    characters embedded inside JSON string values -- e.g. a quoted phrase
    inside an academic article's html_content that Gemini forgot to encode
    as \\\". This is the exact signature behind the 2026-09-10 failure on
    entity 017 (Max Planck), workflow runs #85 and #86:
    "[CRITICAL ERROR] Stage 2 Generation Failed: Expecting ',' delimiter:
    line 3 column ... " -- a raw '"' terminates a JSON string early, so the
    parser expects a ',' or '}' right after it and finds ordinary article
    text instead.

    This is a LAST-RESORT repair only. It is never applied to JSON that
    already parses successfully (see parse_json_with_repairs below), so it
    cannot regress or alter any previously-working generation, entity, or
    already-published article.

    Strategy: walk the text tracking whether the scanner is currently
    inside a JSON string. When an unescaped '"' appears while inside a
    string, look ahead past whitespace: if the next significant character
    is a valid JSON structural token (, : } ] or end-of-text, the quote is
    treated as a genuine string terminator. Otherwise it is a stray literal
    quote belonging to the article text and is escaped in place as \\",
    with scanning continuing inside the same string.
    """
    out = []
    in_string = False
    i, n = 0, len(text)
    while i < n:
        ch = text[i]

        if not in_string:
            out.append(ch)
            if ch == '"':
                in_string = True
            i += 1
            continue

        if ch == '\\' and i + 1 < n:
            # Preserve any escape sequence exactly as-is; it is already valid.
            out.append(ch)
            out.append(text[i + 1])
            i += 2
            continue

        if ch == '"':
            j = i + 1
            while j < n and text[j] in ' \t\r\n':
                j += 1
            next_significant = text[j] if j < n else ''
            if next_significant in ',:}]' or next_significant == '':
                out.append(ch)
                in_string = False
                i += 1
                continue
            out.append('\\"')  # stray literal quote -> escape and stay in-string
            i += 1
            continue

        out.append(ch)
        i += 1

    return ''.join(out)

def parse_json_with_repairs(raw_text: str, stage_label: str) -> dict:
    """
    Single choke point used by both Stage 1 and Stage 2 to turn a raw model
    response into a Python dict, without ever touching STAGE_1_PROMPT /
    STAGE_2_PROMPT, the required schema, or any QA threshold.

    Escalating attempts, each ONLY run if the previous one failed, so JSON
    that is already valid is always returned via step 1 completely
    untouched by any repair pass:
      1. clean_json_response() (markdown-fence/control-character-outside-
         strings stripping only) + json.loads().
      2. If that raises JSONDecodeError: additionally apply
         repair_invalid_backslash_escapes() (fixes Run #76-style single-
         backslash LaTeX macros, e.g. \\Rightarrow / \\nu) and retry.
      3. If that also fails: additionally apply
         escape_raw_control_chars_in_strings() on top (fixes the
         2026-09-10 "Invalid control character" failure -- a literal raw
         newline left inside a long html_content string) and retry.
      4. If that also fails: additionally apply
         repair_unescaped_string_quotes() on top (fixes the 2026-09-10
         Run #85/#86-style stray-quote failure) and retry once more.
    If step 4 also fails, the ORIGINAL exception from step 1 is re-raised
    unchanged so error messages/log signatures stay identical to before for
    any failure mode none of these repairs fix.
    """
    cleaned = clean_json_response(raw_text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as first_error:
        print(f"[{stage_label}] Initial parse failed ({first_error}); attempting backslash-repair pass...")
        step = repair_invalid_backslash_escapes(cleaned)
        try:
            data = json.loads(step)
            print(f"[{stage_label}] Backslash-repair pass succeeded.")
            return data
        except json.JSONDecodeError:
            pass

        print(f"[{stage_label}] Backslash-repair insufficient; attempting control-character-repair pass...")
        step = escape_raw_control_chars_in_strings(step)
        try:
            data = json.loads(step)
            print(f"[{stage_label}] Control-character-repair pass succeeded.")
            return data
        except json.JSONDecodeError:
            pass

        print(f"[{stage_label}] Control-character-repair insufficient; attempting quote-repair pass...")
        step = repair_unescaped_string_quotes(step)
        try:
            data = json.loads(step)
            print(f"[{stage_label}] Quote-repair pass succeeded.")
            return data
        except json.JSONDecodeError:
            raise first_error

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
        stage_1_data = parse_json_with_repairs(raw_text_1, "Stage 1")
        print("[Stage 1] Blueprint generated successfully.")
    except Exception as e:
        print(f"[CRITICAL ERROR] Stage 1 Generation Failed: {e}")
        return False

    # Stage 2 Execution
    print("[Stage 2] Executing HTML Synthesis & Academic QA Evaluation...")
    prompt_2 = STAGE_2_PROMPT.format(stage_1_json=json.dumps(stage_1_data, ensure_ascii=False))

    try:
        raw_text_2 = generate_with_fallback(prompt_2)
        stage_2_data = parse_json_with_repairs(raw_text_2, "Stage 2")
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

    failed_entities = []
    for entity in batch:
        success = process_physicist(entity)
        if success:
            entity["status"] = "completed"
            entity_name = entity.get("arabic_name") or entity.get("name")
            print(f"[Success] Entity '{entity_name}' processed and marked as 'completed'.")
        else:
            entity_name = entity.get("arabic_name") or entity.get("name")
            print(f"[Failure] Entity '{entity_name}' failed processing. Retaining status 'pending'.")
            failed_entities.append(entity_name)

    with open(json_file_path, "w", encoding="utf-8") as f:
        json.dump(physicists, f, ensure_ascii=False, indent=2)
    print(f"[Pipeline Engine] State saved successfully to {dataset_name}.")

    # --------------------------------------------------------------------
    # VISIBILITY FIX: previously this function always returned normally, so
    # main() always exited 0 -- the GitHub Actions run showed a green check
    # even when every entity in the batch failed (this is exactly what
    # happened silently in Run #76 and again in Runs #85/#86). Nothing about
    # WHICH entities count as success/failure changes here -- that logic is
    # still decided entirely by process_physicist()/the QA gate above. This
    # only makes the job's exit code (and therefore the GitHub badge/status)
    # truthfully reflect that outcome. No previously-completed entity's
    # status is touched by this block.
    # --------------------------------------------------------------------
    if failed_entities:
        print(f"::error::Pipeline run had {len(failed_entities)} failed entit(y/ies): {', '.join(failed_entities)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
