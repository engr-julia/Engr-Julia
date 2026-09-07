"""
Pulls your real GitHub contribution calendar and regenerates heartbeat.svg.

Usage (locally):
    GITHUB_TOKEN=ghp_xxx GITHUB_USERNAME=yourname python generate_pulse.py

In GitHub Actions, GITHUB_TOKEN is provided automatically (or use a PAT
with 'read:user' scope) and GITHUB_USERNAME is your repo owner.
"""

import os
import sys
import json
import urllib.request

from heartbeat_svg import build_svg, N_DAYS

GRAPHQL_URL = "https://api.github.com/graphql"

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""


def fetch_contributions(username, token):
    req = urllib.request.Request(
        GRAPHQL_URL,
        data=json.dumps({"query": QUERY, "variables": {"login": username}}).encode(),
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "coding-pulse-svg",
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())

    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    days = []
    for w in weeks:
        for d in w["contributionDays"]:
            days.append(d["contributionCount"])
    return days[-N_DAYS:]  # most recent N_DAYS


def main():
    username = os.environ.get("GITHUB_USERNAME")
    token = os.environ.get("GITHUB_TOKEN")
    if not username or not token:
        print("Set GITHUB_USERNAME and GITHUB_TOKEN environment variables.", file=sys.stderr)
        sys.exit(1)

    counts = fetch_contributions(username, token)
    svg = build_svg(counts, username=username)

    out_path = os.environ.get("OUTPUT_PATH", "heartbeat.svg")
    with open(out_path, "w") as f:
        f.write(svg)
    print(f"wrote {out_path} from {len(counts)} days of real contribution data")


if __name__ == "__main__":
    main()
