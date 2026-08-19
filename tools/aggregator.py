# tools/aggregator.py
# Takes parsed comment data and sums hours
# per author per repo.
# No API calls — pure Python logic.

def aggregate(parsed_comments: list[dict]) -> dict:
    """
    Takes a list of parsed comments:
    [
        {
            "author":  "emp-alice",
            "repo":    "backend-service",
            "planned": None,
            "actual":  5.0
        },
        ...
    ]

    Returns nested dict:
    {
        "backend-service": {
            "emp-alice": {"planned": 8.0, "actual": 5.0},
            "emp-bob":   {"planned": 0.0, "actual": 8.0},
        },
        "frontend-app": {
            "emp-alice": {"planned": 0.0, "actual": 3.0},
        },
        ...
    }
    """
    result = {}

    for item in parsed_comments:
        author  = item["author"]
        repo    = item["repo"]
        planned = item.get("planned") or 0.0
        actual  = item.get("actual")  or 0.0

        # Skip if no hours at all
        if planned == 0.0 and actual == 0.0:
            continue

        # Initialise repo if not seen before
        if repo not in result:
            result[repo] = {}

        # Initialise author if not seen before
        if author not in result[repo]:
            result[repo][author] = {"planned": 0.0, "actual": 0.0}

        # Add hours
        result[repo][author]["planned"] += planned
        result[repo][author]["actual"]  += actual

    return result


if __name__ == "__main__":
    # Test with fake parsed data — no API needed
    fake_parsed = [
        {"author": "emp-alice",   "repo": "backend-service",  "planned": None, "actual": 5.0},
        {"author": "emp-alice",   "repo": "backend-service",  "planned": None, "actual": 3.0},
        {"author": "emp-bob",     "repo": "backend-service",  "planned": None, "actual": 8.0},
        {"author": "emp-alice",   "repo": "frontend-app",     "planned": None, "actual": 3.0},
        {"author": "emp-charlie", "repo": "security-system",  "planned": None, "actual": 16.0},
        {"author": "emp-bob",     "repo": "security-system",  "planned": None, "actual": 4.0},
        # This one has no hours — should be skipped
        {"author": "emp-alice",   "repo": "backend-service",  "planned": None, "actual": None},
    ]

    print("Testing aggregator.py...\n")
    result = aggregate(fake_parsed)

    for repo, engineers in result.items():
        print(f"  {repo}:")
        for author, hours in engineers.items():
            print(f"    {author} → planned={hours['planned']}h  actual={hours['actual']}h")
        print()