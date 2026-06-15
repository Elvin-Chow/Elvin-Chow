#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


USERNAME = "Elvin-Chow"
README = Path("README.md")
START = "<!-- PROFILE-METRICS:START -->"
END = "<!-- PROFILE-METRICS:END -->"
TRACKED_REPOS = [
    "DeepFirm-Quant",
    "FundX",
    "DeepFirm-Quant_Paper-Artifact-Repository",
]


def fetch_json(url: str) -> dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "elvin-chow-profile-updater",
    }
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def format_date(value: str | None) -> str:
    if not value:
        return "n/a"

    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return value[:10]

    return parsed.astimezone(timezone.utc).strftime("%Y-%m-%d")


def markdown_escape(value: object) -> str:
    text = str(value or "n/a")
    return text.replace("|", "\\|").replace("\n", " ").strip()


def build_metrics_block() -> str:
    lines = [
        START,
        "| Project | Language | Stars | Forks | Open items | Last push |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]

    for repo_name in TRACKED_REPOS:
        repo = fetch_json(f"https://api.github.com/repos/{USERNAME}/{repo_name}")
        project = f"[{markdown_escape(repo['name'])}]({repo['html_url']})"
        language = markdown_escape(repo.get("language"))
        stars = repo.get("stargazers_count", 0)
        forks = repo.get("forks_count", 0)
        issues = repo.get("open_issues_count", 0)
        pushed = format_date(repo.get("pushed_at"))
        lines.append(f"| {project} | {language} | {stars} | {forks} | {issues} | {pushed} |")

    lines.append(END)
    return "\n".join(lines)


def replace_block(readme: str, block: str) -> str:
    start_index = readme.find(START)
    end_index = readme.find(END)

    if start_index == -1 or end_index == -1 or end_index < start_index:
        raise RuntimeError(f"Could not find {START} / {END} markers in {README}.")

    end_index += len(END)
    return readme[:start_index] + block + readme[end_index:]


def main() -> int:
    parser = argparse.ArgumentParser(description="Refresh the dynamic profile metrics block.")
    parser.add_argument("--check", action="store_true", help="Fail if README.md is not up to date.")
    args = parser.parse_args()

    try:
        current = README.read_text(encoding="utf-8")
        updated = replace_block(current, build_metrics_block())
    except (OSError, RuntimeError, urllib.error.URLError, KeyError) as exc:
        print(f"profile update failed: {exc}", file=sys.stderr)
        return 1

    if args.check:
        if current != updated:
            print("README.md profile metrics are stale.", file=sys.stderr)
            return 1
        print("README.md profile metrics are current.")
        return 0

    README.write_text(updated, encoding="utf-8")
    print("README.md profile metrics refreshed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
