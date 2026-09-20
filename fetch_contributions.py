from pathlib import Path
from datetime import datetime, timedelta, timezone
import json
import os
import sys

import requests


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "contributions.json"

USERNAME = "RIxiV1"
API_URL = "https://api.github.com/graphql"

TOKEN = os.environ.get("GITHUB_TOKEN")

if not TOKEN:
    print("ERROR: GITHUB_TOKEN is not set.")
    sys.exit(1)


today = datetime.now(timezone.utc).date()
start_date = today - timedelta(days=365)

FROM = f"{start_date}T00:00:00Z"
TO = f"{today}T23:59:59Z"


QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    login

    contributionsCollection(from: $from, to: $to) {
      totalContributions
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      totalPullRequestReviewContributions

      contributionCalendar {
        totalContributions

        weeks {
          firstDay

          contributionDays {
            date
            contributionCount
            contributionLevel
            weekday
          }
        }
      }
    }
  }
}
"""


response = requests.post(
    API_URL,
    json={
        "query": QUERY,
        "variables": {
            "login": USERNAME,
            "from": FROM,
            "to": TO,
        },
    },
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
    },
    timeout=30,
)


if response.status_code != 200:
    print("GitHub API request failed.")
    print(response.text)
    sys.exit(1)


payload = response.json()


if "errors" in payload:
    print("GitHub GraphQL returned errors:")
    print(json.dumps(payload["errors"], indent=2))
    sys.exit(1)


user = payload["data"]["user"]


if user is None:
    print(f"ERROR: GitHub user '{USERNAME}' was not found.")
    sys.exit(1)


collection = user["contributionsCollection"]
calendar = collection["contributionCalendar"]


days = []

for week in calendar["weeks"]:
    for day in week["contributionDays"]:

        current_date = day["date"]

        if current_date < str(start_date):
            continue

        if current_date > str(today):
            continue

        days.append(
            {
                "date": current_date,
                "weekday": day["weekday"],
                "count": day["contributionCount"],
                "level": day["contributionLevel"],
            }
        )


days.sort(key=lambda x: x["date"])


active_days = sum(
    1 for day in days
    if day["count"] > 0
)


# Current streak
current_streak = 0

for day in reversed(days):

    if day["count"] > 0:
        current_streak += 1
    else:
        break


# Longest streak
longest_streak = 0
streak = 0

for day in days:

    if day["count"] > 0:
        streak += 1
        longest_streak = max(longest_streak, streak)

    else:
        streak = 0


# Best week
best_week = 0
current_week_total = 0
previous_weekday = None

for day in days:

    weekday = day["weekday"]

    if previous_weekday is not None and weekday == 0:
        best_week = max(
            best_week,
            current_week_total
        )

        current_week_total = 0

    current_week_total += day["count"]

    previous_weekday = weekday


best_week = max(
    best_week,
    current_week_total
)


stats = {
    "total_contributions":
        collection["totalContributions"],

    "active_days":
        active_days,

    "current_streak":
        current_streak,

    "longest_streak":
        longest_streak,

    "best_week":
        best_week,

    "total_commits":
        collection["totalCommitContributions"],

    "total_pull_requests":
        collection["totalPullRequestContributions"],

    "total_issues":
        collection["totalIssueContributions"],

    "total_reviews":
        collection["totalPullRequestReviewContributions"],
}


data = {
    "username": user["login"],

    "range": {
        "from": str(start_date),
        "to": str(today),
    },

    "stats": stats,

    "days": days,
}


OUTPUT.write_text(
    json.dumps(data, indent=2) + "\n",
    encoding="utf-8",
)


print()
print("DONE!")
print(f"Created: {OUTPUT}")
print()
print(f"Contributions: {stats['total_contributions']}")
print(f"Active days:   {stats['active_days']}")
print(f"Current streak: {stats['current_streak']}")
print(f"Longest streak: {stats['longest_streak']}")
print(f"Best week:     {stats['best_week']}")
print(f"Commits:       {stats['total_commits']}")
print(f"Pull requests: {stats['total_pull_requests']}")
print(f"Issues:        {stats['total_issues']}")
print(f"Reviews:       {stats['total_reviews']}")
