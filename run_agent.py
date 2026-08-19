# run_agent.py
# Main entry point — runs the full pipeline.
# Fetch comments → parse hours → aggregate → update sheet

from tools.github_tool import fetch_comments
from tools.parser      import extract_hours_from_comment
from tools.aggregator  import aggregate
from tools.sheets_tool import run as update_sheet


def run_pipeline():
    print("\n" + "="*50)
    print("  Effort Tracker Agent")
    print("="*50)

    # ── Step 1: Fetch comments from GitHub ────────────────────
    print("\n[1/4] Fetching comments from GitHub...")
    comments = fetch_comments()

    if not comments:
        print("  No comments found in the period. Nothing to update.")
        return

    # ── Step 2: Parse hours from each comment ─────────────────
    print(f"\n[2/4] Parsing hours from {len(comments)} comments...")
    parsed = []
    for i, comment in enumerate(comments):
        print(f"  ({i+1}/{len(comments)}) {comment['author']} — {comment['repo']}")
        result = extract_hours_from_comment(comment["body"])

        parsed.append({
            "author":  comment["author"],
            "repo":    comment["repo"],
            "planned": result["planned"],
            "actual":  result["actual"],
        })

        # Show what was found
        if result["planned"] or result["actual"]:
            print(f"    → planned={result['planned']}h  actual={result['actual']}h")
        else:
            print(f"    → no hours found")

    # ── Step 3: Aggregate hours ────────────────────────────────
    print("\n[3/4] Aggregating hours per engineer per repo...")
    aggregated = aggregate(parsed)

    if not aggregated:
        print("  No hours found in any comments. Sheet not updated.")
        return

    # Print summary
    for repo, engineers in aggregated.items():
        print(f"  {repo}:")
        for eng, hours in engineers.items():
            print(f"    {eng} → planned={hours['planned']}h  actual={hours['actual']}h")

    # ── Step 4: Update Google Sheet ───────────────────────────
    print("\n[4/4] Updating Google Sheet...")
    update_sheet(aggregated)

    print("\n" + "="*50)
    print("  Done ✓ Sheet updated successfully")
    print("="*50 + "\n")


if __name__ == "__main__":
    run_pipeline()