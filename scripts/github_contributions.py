import os
import json
import urllib.request
from pathlib import Path
from datetime import date, timedelta


USERNAME = "RIxiV1"
OUTPUT = Path("../contributions.json")

GRAPHQL_URL = "https://api.github.com/graphql"


QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        colors
        weeks {
          firstDay
          contributionDays {
            date
            contributionCount
            contributionLevel
            weekday
            color
          }
        }
      }

      totalCommitContributions
      totalIssueContributions
      totalPullRequestContributions
      totalPullRequestReviewContributions
      totalRepositoryContributions
      totalRepositoriesWithContributedCommits
      totalRepositoriesWithContributedIssues
      totalRepositoriesWithContributedPullRequests
      totalRepositoriesWithContributedPullRequestReviews
    }
  }
}
"""


def graphql_request():

    token = os.environ.get("GITHUB_TOKEN")

    if not token:
        raise RuntimeError(
            "GITHUB_TOKEN is not set."
        )

    payload = json.dumps({
        "query": QUERY,
        "variables": {
            "login": USERNAME
        }
    }).encode("utf-8")

    request = urllib.request.Request(
        GRAPHQL_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "RIxiV1-profile-generator",
        },
        method="POST"
    )

    with urllib.request.urlopen(request) as response:
        return json.loads(
            response.read().decode("utf-8")
        )


print(f"Fetching contribution data for {USERNAME}...")

result = graphql_request()


if "errors" in result:
    print(json.dumps(result["errors"], indent=2))
    raise RuntimeError(
        "GitHub GraphQL request failed."
    )


user = result["data"]["user"]

if not user:
    raise RuntimeError(
        f"GitHub user {USERNAME} was not found."
    )


collection = user["contributionsCollection"]

calendar = collection["contributionCalendar"]


# ---------------------------------------------------------
# FLATTEN CONTRIBUTION DAYS
# ---------------------------------------------------------

days = []

for week in calendar["weeks"]:

    for day in week["contributionDays"]:

        days.append({
            "date": day["date"],
            "count": day["contributionCount"],
            "level": day["contributionLevel"],
            "weekday": day["weekday"],
            "color": day["color"],
        })


# ---------------------------------------------------------
# SORT
# ---------------------------------------------------------

days.sort(
    key=lambda x: x["date"]
)


# ---------------------------------------------------------
# STREAK CALCULATION
# ---------------------------------------------------------

contribution_dates = {
    d["date"]
    for d in days
    if d["count"] > 0
}


def calculate_longest_streak():

    longest = 0
    current = 0

    for day in days:

        if day["count"] > 0:
            current += 1
            longest = max(
                longest,
                current
            )
        else:
            current = 0

    return longest


def calculate_current_streak():

    today = date.today()

    available = {
        date.fromisoformat(d["date"])
        for d in days
        if d["count"] > 0
    }

    # If there was no contribution today,
    # start checking from yesterday.
    current_day = today

    if current_day not in available:
        current_day -= timedelta(days=1)

    streak = 0

    while current_day in available:

        streak += 1

        current_day -= timedelta(days=1)

    return streak


# ---------------------------------------------------------
# ACTIVE DAYS
# ---------------------------------------------------------

active_days = sum(
    1
    for day in days
    if day["count"] > 0
)


# ---------------------------------------------------------
# TOTALS
# ---------------------------------------------------------

stats = {
    "total_contributions":
        calendar["totalContributions"],

    "active_days":
        active_days,

    "current_streak":
        calculate_current_streak(),

    "longest_streak":
        calculate_longest_streak(),

    "total_commits":
        collection["totalCommitContributions"],

    "total_issues":
        collection["totalIssueContributions"],

    "total_pull_requests":
        collection["totalPullRequestContributions"],

    "total_reviews":
        collection["totalPullRequestReviewContributions"],

    "repositories_created":
        collection["totalRepositoryContributions"],

    "repositories_with_commits":
        collection[
            "totalRepositoriesWithContributedCommits"
        ],

    "repositories_with_issues":
        collection[
            "totalRepositoriesWithContributedIssues"
        ],

    "repositories_with_pull_requests":
        collection[
            "totalRepositoriesWithContributedPullRequests"
        ],
}


# ---------------------------------------------------------
# OUTPUT
# ---------------------------------------------------------

output = {
    "username": USERNAME,
    "stats": stats,
    "colors": calendar["colors"],
    "days": days,
}


OUTPUT.write_text(
    json.dumps(
        output,
        indent=2
    ),
    encoding="utf-8"
)


print()
print("DONE!")
print(
    f"Total contributions: "
    f"{stats['total_contributions']}"
)

print(
    f"Active days: "
    f"{stats['active_days']}"
)

print(
    f"Current streak: "
    f"{stats['current_streak']}"
)

print(
    f"Longest streak: "
    f"{stats['longest_streak']}"
)

print(
    f"Commits: "
    f"{stats['total_commits']}"
)

print(
    f"Pull requests: "
    f"{stats['total_pull_requests']}"
)

print(
    f"Issues: "
    f"{stats['total_issues']}"
)

print()
print(f"Created: {OUTPUT}")