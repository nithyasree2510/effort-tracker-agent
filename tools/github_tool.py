# tools/github_tool.py
# Fetches PR and issue comments from all repos in the org.
# Hours are logged in comments, not commit messages.

from github import Github, Auth
from datetime import datetime, timezone
import os
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_ORG   = os.getenv("GITHUB_ORG")

# Always fetch from the 1st of the current month to now
now   = datetime.now(timezone.utc)
since = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def fetch_comments() -> list[dict]:
    """
    Fetches all PR and issue comments from the start of
    the current month to now.

    Returns list of dicts:
    [
        {
            "author": "hariprasath-rlabs",
            "repo":   "backend-service",
            "body":   "Efforts: 10h\n• Mocked the STM OTP..."
        },
        ...
    ]
    """
    g   = Github(auth=Auth.Token(GITHUB_TOKEN))
    org = g.get_organization(GITHUB_ORG)

    all_comments = []
    repos = list(org.get_repos())
    print(f"  Found {len(repos)} repos in {GITHUB_ORG}")
    print(f"  Fetching comments since: {since.strftime('%Y-%m-%d')}")

    for repo in repos:
        print(f"  Reading comments from: {repo.name}")

        # 1. Issue comments (includes PR comments — PRs are issues in GitHub)
        try:
            for comment in repo.get_issues_comments(since=since):
                if not comment.user or not comment.body:
                    continue
                all_comments.append({
                    "author": comment.user.login,
                    "repo":   repo.name,
                    "body":   comment.body.strip()
                })
        except Exception as e:
            print(f"  ⚠ Could not read issue comments from {repo.name}: {e}")

        # 2. PR review comments (line-by-line code review comments)
        try:
            for comment in repo.get_pulls_comments():
                if not comment.user or not comment.body:
                    continue
                if comment.created_at < since:
                    continue
                all_comments.append({
                    "author": comment.user.login,
                    "repo":   repo.name,
                    "body":   comment.body.strip()
                })
        except Exception as e:
            print(f"  ⚠ Could not read PR comments from {repo.name}: {e}")

    print(f"  Total comments fetched: {len(all_comments)}")
    return all_comments