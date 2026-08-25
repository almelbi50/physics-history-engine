import sys

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
    quality_score = qa.get("quality_score", 0)
    critical_errors = qa.get("critical_errors", [])

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
