from pathlib import Path
import json
import os
import urllib.request
import urllib.error
from datetime import date, timedelta


# ---------------------------------------------------------
# PATHS
# ---------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "contributions.json"

USERNAME = "RIxiV1"


# ---------------------------------------------------------
# GITHUB API
# ---------------------------------------------------------

TOKEN = os.environ.get("GITHUB_TOKEN")

if not TOKEN:
    raise RuntimeError(
        "GITHUB_TOKEN environment variable is missing."
    )


GRAPHQL_URL = "https://api.github.com/graphql"

QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(
      from: $from
      to: $to
    ) {
      contributionCalendar {
        totalContributions
        colors
        weeks {
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

      restrictedContributionsCount
    }
  }
}
"""


# ---------------------------------------------------------
# DATE RANGE
# ---------------------------------------------------------

today = date.today()

# GitHub's contribution calendar covers roughly one year.
# Start slightly earlier so the complete calendar is included.
start = today - timedelta(days=365)

from_datetime = f"{start.isoformat()}T00:00:00Z"
to_datetime = f"{today.isoformat()}T23:59:59Z"


# ---------------------------------------------------------
# REQUEST
# ---------------------------------------------------------

payload = json.dumps({
    "query": QUERY,
    "variables": {
        "login": USERNAME,
        "from": from_datetime,
        "to": to_datetime,
    },
}).encode("utf-8")


request = urllib.request.Request(
    GRAPHQL_URL,
    data=payload,
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": USERNAME,
    },
    method="POST",
)


try:

    with urllib.request.urlopen(request) as response:
        result = json.loads(
            response.read().decode("utf-8")
        )

except urllib.error.HTTPError as error:

    body = error.read().decode("utf-8", errors="replace")

    raise RuntimeError(
        f"GitHub API request failed: "
        f"{error.code}\n{body}"
    )


# ---------------------------------------------------------
# CHECK GRAPHQL ERRORS
# ---------------------------------------------------------

if "errors" in result:

    raise RuntimeError(
        "GitHub GraphQL returned errors:\n"
        + json.dumps(
            result["errors"],
            indent=2
        )
    )


user = result["data"]["user"]

if user is None:

    raise RuntimeError(
        f"GitHub user '{USERNAME}' was not found."
    )


collection = user["contributionsCollection"]
calendar = collection["contributionCalendar"]


# ---------------------------------------------------------
# EXTRACT DAYS
# ---------------------------------------------------------

days = []

for week in calendar["weeks"]:

    for item in week["contributionDays"]:

        days.append({
            "date": item["date"],
            "count": item["contributionCount"],
            "level": item["contributionLevel"],
            "weekday": item["weekday"],
            "color": item["color"],
        })


days.sort(
    key=lambda item: item["date"]
)


# ---------------------------------------------------------
# STATS
# ---------------------------------------------------------

total_contributions = (
    calendar["totalContributions"]
)

active_days = sum(
    1
    for item in days
    if item["count"] > 0
)


stats = {
    "total_contributions": total_contributions,

    "active_days": active_days,

    "current_streak": 0,
    "longest_streak": 0,

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

    "restricted_contributions":
        collection[
            "restrictedContributionsCount"
        ],
}


# ---------------------------------------------------------
# STREAK CALCULATION
# ---------------------------------------------------------

counts_by_date = {
    item["date"]: item["count"]
    for item in days
}


# Current streak
current_streak = 0
cursor = today

while True:

    value = counts_by_date.get(
        cursor.isoformat(),
        0
    )

    if value <= 0:
        break

    current_streak += 1
    cursor -= timedelta(days=1)


# Longest streak
longest_streak = 0
streak = 0

for item in days:

    if item["count"] > 0:

        streak += 1
        longest_streak = max(
            longest_streak,
            streak
        )

    else:

        streak = 0


stats["current_streak"] = current_streak
stats["longest_streak"] = longest_streak


# ---------------------------------------------------------
# COLORS
# ---------------------------------------------------------

colors = calendar["colors"]


# ---------------------------------------------------------
# OUTPUT
# ---------------------------------------------------------

output = {
    "username": USERNAME,
    "stats": stats,
    "colors": colors,
    "days": days,
}


OUTPUT.write_text(
    json.dumps(
        output,
        indent=2
    ),
    encoding="utf-8"
)


# ---------------------------------------------------------
# REPORT
# ---------------------------------------------------------

print()
print("========================================")
print(" GitHub contribution data fetched")
print("========================================")
print(f"User          : {USERNAME}")
print(f"Total         : {total_contributions}")
print(f"Active days   : {active_days}")
print(f"Commits       : {stats['total_commits']}")
print(f"Pull requests : {stats['total_pull_requests']}")
print(f"Reviews       : {stats['total_reviews']}")
print(
    f"Restricted    : "
    f"{stats['restricted_contributions']}"
)
print(f"Created repos : {stats['repositories_created']}")
print(f"Output        : {OUTPUT}")
print()
