import os
import json
import urllib.request
from pathlib import Path
from datetime import datetime, timedelta, timezone


USERNAME = "RIxiV1"
OUTPUT = Path("../github-data.json")


def github_request(url):
    token = os.environ.get("GITHUB_TOKEN")

    if not token:
        raise RuntimeError(
            "GITHUB_TOKEN is not set. Run the PowerShell token command first."
        )

    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "RIxiV1-profile-generator",
        },
    )

    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode())


print(f"Fetching GitHub data for {USERNAME}...")


# ---------------------------------------------------------
# USER
# ---------------------------------------------------------

user = github_request(
    f"https://api.github.com/users/{USERNAME}"
)


# ---------------------------------------------------------
# PUBLIC REPOSITORIES
# ---------------------------------------------------------

repos = github_request(
    f"https://api.github.com/users/{USERNAME}/repos"
    "?per_page=100&sort=updated"
)


# ---------------------------------------------------------
# BASIC STATS
# ---------------------------------------------------------

data = {
    "username": USERNAME,
    "name": user.get("name"),
    "bio": user.get("bio"),
    "public_repos": user.get("public_repos", 0),
    "followers": user.get("followers", 0),
    "following": user.get("following", 0),
    "hireable": user.get("hireable", False),
    "repositories": [],
}


# ---------------------------------------------------------
# REPOSITORY DATA
# ---------------------------------------------------------

for repo in repos:

    if repo.get("fork"):
        continue

    data["repositories"].append({
        "name": repo.get("name"),
        "description": repo.get("description"),
        "language": repo.get("language"),
        "stars": repo.get("stargazers_count", 0),
        "forks": repo.get("forks_count", 0),
        "updated": repo.get("updated_at"),
        "url": repo.get("html_url"),
    })


# ---------------------------------------------------------
# LANGUAGE COUNTS
# ---------------------------------------------------------

languages = {}

for repo in data["repositories"]:

    language = repo.get("language")

    if language:
        languages[language] = languages.get(language, 0) + 1

data["languages"] = dict(
    sorted(
        languages.items(),
        key=lambda item: item[1],
        reverse=True,
    )
)


# ---------------------------------------------------------
# RECENT ACTIVITY
# ---------------------------------------------------------

events = github_request(
    f"https://api.github.com/users/{USERNAME}/events/public"
    "?per_page=100"
)

data["recent_activity"] = []

for event in events:

    created = event.get("created_at")

    if not created:
        continue

    data["recent_activity"].append({
        "type": event.get("type"),
        "repo": event.get("repo", {}).get("name"),
        "created_at": created,
    })


# ---------------------------------------------------------
# WRITE DATA
# ---------------------------------------------------------

OUTPUT.write_text(
    json.dumps(data, indent=2),
    encoding="utf-8"
)

print()
print("DONE!")
print(f"Repositories: {len(data['repositories'])}")
print(f"Languages: {len(data['languages'])}")
print(f"Recent events: {len(data['recent_activity'])}")
print(f"Created: {OUTPUT}")