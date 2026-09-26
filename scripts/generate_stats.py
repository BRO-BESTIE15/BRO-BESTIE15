#!/usr/bin/env python3
"""
Generate static SVG GitHub profile stats cards.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_USERNAME = "BRO-BESTIE15"

def escape_svg_text(value: object) -> str:
    if value is None:
        return ""
    text = str(value)
    replacements = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

def github_api_request(endpoint: str, token: str | None = None) -> dict:
    url = f"https://api.github.com{endpoint}"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "github-profile-stats-generator",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        request = Request(url, headers=headers)
        with urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        print(f"GitHub API request failed for {url}: HTTP {exc.code}", file=sys.stderr)
        print(body, file=sys.stderr)
        raise SystemExit(1)
    except URLError as exc:
        print(f"GitHub API request failed for {url}: {exc}", file=sys.stderr)
        raise SystemExit(1)
    except json.JSONDecodeError as exc:
        print(f"GitHub API returned invalid JSON for {url}", file=sys.stderr)
        raise SystemExit(1) from exc

def load_user_data(username: str, token: str | None) -> dict:
    data = github_api_request(f"/users/{username}", token)
    if isinstance(data, dict) and "message" in data:
        raise SystemExit(f"API error for '{username}': {data['message']}")
    return data

def load_repos(username: str, token: str | None) -> list[dict]:
    data = github_api_request(f"/users/{username}/repos?type=owner&per_page=100&sort=updated", token)
    if isinstance(data, dict) and "message" in data:
        raise SystemExit(f"API error fetching repos for '{username}': {data['message']}")
    if not isinstance(data, list):
        return []
    return data

def generate_github_stats_svg(user_data: dict, repos_data: list[dict]) -> str:
    username = escape_svg_text(user_data.get("login") or DEFAULT_USERNAME)
    full_name = escape_svg_text(user_data.get("name") or username)
    public_repos = int(user_data.get("public_repos", 0) or 0)
    public_gists = int(user_data.get("public_gists", 0) or 0)
    followers = int(user_data.get("followers", 0) or 0)
    following = int(user_data.get("following", 0) or 0)
    total_stars = sum(int(repo.get("stargazers_count", 0) or 0) for repo in repos_data)
    total_forks = sum(int(repo.get("forks_count", 0) or 0) for repo in repos_data)

    return f'''<svg width="500" height="220" viewBox="0 0 500 220" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect width="500" height="220" rx="12" fill="#0d1117"/>
  <rect x="12" y="12" width="476" height="196" rx="10" fill="#161b22" stroke="#30363d"/>
  <text x="24" y="38" fill="#e6edf3" font-family="Segoe UI, Arial, sans-serif" font-size="18" font-weight="700">{full_name}</text>
  <text x="24" y="58" fill="#8b949e" font-family="Segoe UI, Arial, sans-serif" font-size="11">@{username}</text>
  <rect x="24" y="76" width="100" height="1" fill="#30363d"/>

  <text x="24" y="110" fill="#79c0ff" font-family="Segoe UI, Arial, sans-serif" font-size="24" font-weight="700">{public_repos}</text>
  <text x="24" y="128" fill="#8b949e" font-family="Segoe UI, Arial, sans-serif" font-size="11">Public Repos</text>

  <text x="132" y="110" fill="#79c0ff" font-family="Segoe UI, Arial, sans-serif" font-size="24" font-weight="700">{total_stars}</text>
  <text x="132" y="128" fill="#8b949e" font-family="Segoe UI, Arial, sans-serif" font-size="11">Stars</text>

  <text x="240" y="110" fill="#79c0ff" font-family="Segoe UI, Arial, sans-serif" font-size="24" font-weight="700">{total_forks}</text>
  <text x="240" y="128" fill="#8b949e" font-family="Segoe UI, Arial, sans-serif" font-size="11">Forks</text>

  <text x="348" y="110" fill="#79c0ff" font-family="Segoe UI, Arial, sans-serif" font-size="24" font-weight="700">{followers}</text>
  <text x="348" y="128" fill="#8b949e" font-family="Segoe UI, Arial, sans-serif" font-size="11">Followers</text>

  <text x="24" y="170" fill="#79c0ff" font-family="Segoe UI, Arial, sans-serif" font-size="24" font-weight="700">{public_gists}</text>
  <text x="24" y="188" fill="#8b949e" font-family="Segoe UI, Arial, sans-serif" font-size="11">Public Gists</text>

  <text x="132" y="170" fill="#79c0ff" font-family="Segoe UI, Arial, sans-serif" font-size="24" font-weight="700">{following}</text>
  <text x="132" y="188" fill="#8b949e" font-family="Segoe UI, Arial, sans-serif" font-size="11">Following</text>

  <text x="348" y="170" fill="#7ee787" font-family="Segoe UI, Arial, sans-serif" font-size="22" font-weight="700">{len(repos_data)}</text>
  <text x="348" y="188" fill="#8b949e" font-family="Segoe UI, Arial, sans-serif" font-size="11">Repos Viewed</text>
</svg>
'''

def generate_top_languages_svg(repos_data: list[dict]) -> str:
    language_counts: dict[str, int] = {}
    for repo in repos_data:
        lang = repo.get("language")
        if lang:
            language_counts[lang] = language_counts.get(lang, 0) + 1

    if not language_counts:
        language_counts = {"No language data": 1}

    top_languages = sorted(language_counts.items(), key=lambda item: item[1], reverse=True)[:6]
    total = sum(count for _, count in top_languages)
    palette = ["#79c0ff", "#7ee787", "#ffa657", "#ff7b72", "#d2a8ff", "#c9d1d9"]

    parts = [
        '<svg width="500" height="220" viewBox="0 0 500 220" fill="none" xmlns="http://www.w3.org/2000/svg">',
        '<rect width="500" height="220" rx="12" fill="#0d1117"/>',
        '<rect x="12" y="12" width="476" height="196" rx="10" fill="#161b22" stroke="#30363d"/>',
        '<text x="24" y="38" fill="#e6edf3" font-family="Segoe UI, Arial, sans-serif" font-size="18" font-weight="700">Top Languages</text>',
        '<rect x="24" y="50" width="452" height="1" fill="#30363d"/>',
    ]

    start_y = 78
    for index, (language_name, count) in enumerate(top_languages):
        percent = (count / total) * 100 if total else 0
        y = start_y + index * 24
        bar_width = max(20, (percent / 100) * 300)
        color = palette[index % len(palette)]
        safe_lang = escape_svg_text(language_name)
        parts.append(f'<text x="24" y="{y}" fill="#8b949e" font-family="Segoe UI, Arial, sans-serif" font-size="11">{safe_lang}</text>')
        parts.append(f'<rect x="150" y="{y - 10}" width="300" height="8" rx="4" fill="#21262d"/>')
        parts.append(f'<rect x="150" y="{y - 10}" width="{bar_width:.1f}" height="8" rx="4" fill="{color}" />')
        parts.append(f'<text x="458" y="{y}" fill="#e6edf3" font-family="Segoe UI, Arial, sans-serif" font-size="11" text-anchor="end">{percent:.1f}%</text>')

    parts.append("</svg>")
    return "".join(parts)

def main() -> None:
    username = os.getenv("GITHUB_USERNAME", DEFAULT_USERNAME)
    token = os.getenv("GITHUB_TOKEN")

    print(f"Generating stats for {username}")
    user_data = load_user_data(username, token)
    repos_data = load_repos(username, token)

    stats_dir = Path("stats")
    stats_dir.mkdir(exist_ok=True)

    (stats_dir / "github-stats.svg").write_text(generate_github_stats_svg(user_data, repos_data), encoding="utf-8")
    (stats_dir / "top-languages.svg").write_text(generate_top_languages_svg(repos_data), encoding="utf-8")

    print("Saved stats/github-stats.svg")
    print("Saved stats/top-languages.svg")

if __name__ == "__main__":
    main()
