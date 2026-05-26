"""
generate_readme.py
──────────────────
Fetches live data from GitHub API and rewrites README.md automatically.
Runs inside GitHub Actions — triggered on push or every 6 hours.

Environment variables (set in the workflow):
  GITHUB_TOKEN      → provided automatically by GitHub Actions
  GITHUB_USERNAME   → your GitHub username
  LINKEDIN_URL      → your LinkedIn profile URL
"""

import os
import re
import requests
from collections import defaultdict
from datetime import datetime, timezone

# ── Config ────────────────────────────────────────────────────────────────────

USERNAME     = os.environ.get("GITHUB_USERNAME", "MuhammadMustafa23")
LINKEDIN     = os.environ.get("LINKEDIN_URL", "https://www.linkedin.com/in/muhammad-mustafa-ab5b273a9/")
TOKEN        = os.environ.get("GITHUB_TOKEN", "")
DISPLAY_NAME = "Muhammad Mustafa"
UNI          = "FAST-NUCES, Islamabad"
LOCATION     = "Pakistan"
INTERESTS    = ["AI/ML", "Software Engineering", "Gaming", "Fitness"]
GOAL         = "Build production-level AI systems"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

# ── Language → skillicons.dev key ─────────────────────────────────────────────

LANG_TO_ICON = {
    "c++": "cpp", "python": "python", "java": "java",
    "javascript": "javascript", "typescript": "typescript",
    "c#": "cs", "go": "go", "rust": "rust", "kotlin": "kotlin",
    "swift": "swift", "php": "php", "html": "html", "css": "css",
    "shell": "bash", "ruby": "ruby", "scala": "scala",
}

# ── Language → shields.io badge ───────────────────────────────────────────────

LANG_TO_BADGE = {
    "c++":        ("C++",        "C%2B%2B-00599C",  "c%2B%2B",      "white"),
    "python":     ("Python",     "Python-3776AB",    "python",        "white"),
    "java":       ("Java",       "Java-ED8B00",      "openjdk",       "white"),
    "javascript": ("JavaScript", "JavaScript-F7DF1E","javascript",    "black"),
    "typescript": ("TypeScript", "TypeScript-3178C6","typescript",    "white"),
    "c#":         ("C#",         "C%23-239120",      "csharp",        "white"),
    "go":         ("Go",         "Go-00ADD8",        "go",            "white"),
    "rust":       ("Rust",       "Rust-000000",      "rust",          "white"),
    "kotlin":     ("Kotlin",     "Kotlin-A97BFF",    "kotlin",        "white"),
    "swift":      ("Swift",      "Swift-F05138",     "swift",         "white"),
    "php":        ("PHP",        "PHP-777BB4",        "php",           "white"),
    "html":       ("HTML",       "HTML5-E34F26",     "html5",         "white"),
    "css":        ("CSS",        "CSS3-563D7C",      "css3",          "white"),
    "shell":      ("Shell",      "Shell-89E051",     "gnubash",       "black"),
    "mysql":      ("MySQL",      "MySQL-4479A1",     "mysql",         "white"),
    "git":        ("Git",        "Git-F05032",       "git",           "white"),
}

# Extra skills always added if certain languages are present
ALWAYS_ADD = {
    "mysql": ["c++", "java", "python", "php"],   # if any of these exist, add mysql badge
    "git":   ["c++", "java", "python", "javascript", "typescript",
               "c#", "go", "rust", "kotlin", "swift"],
}

# ── GitHub API helpers ─────────────────────────────────────────────────────────

def get_profile():
    r = requests.get(f"https://api.github.com/users/{USERNAME}", headers=HEADERS)
    r.raise_for_status()
    return r.json()

def get_repos():
    repos, page = [], 1
    while True:
        r = requests.get(
            f"https://api.github.com/users/{USERNAME}/repos",
            headers=HEADERS,
            params={"per_page": 100, "page": page, "sort": "updated"},
        )
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        repos.extend(batch)
        page += 1
    return [r for r in repos if not r["fork"]]   # exclude forks

def get_languages(repos):
    """Aggregate byte counts across all repos (up to 40 to stay within rate limit)."""
    totals = defaultdict(int)
    for repo in repos[:40]:
        try:
            r = requests.get(repo["languages_url"], headers=HEADERS)
            if r.ok:
                for lang, count in r.json().items():
                    totals[lang.lower()] += count
        except Exception:
            pass
    return totals   # { "python": 123456, "c++": 78900, ... }

# ── Skill detection ────────────────────────────────────────────────────────────

def detect_skills(lang_totals):
    """Return ordered list of skill keys based on actual language usage."""
    detected = []
    sorted_langs = sorted(lang_totals.items(), key=lambda x: -x[1])

    for lang, _ in sorted_langs:
        if lang in LANG_TO_BADGE:
            detected.append(lang)

    # Add MySQL if any backend language present
    has_backend = any(l in detected for l in ALWAYS_ADD["mysql"])
    if has_backend and "mysql" not in detected:
        detected.append("mysql")

    # Always add Git if any language found
    has_code = any(l in detected for l in ALWAYS_ADD["git"])
    if has_code and "git" not in detected:
        detected.append("git")

    return detected   # ordered by usage

# ── README section builders ────────────────────────────────────────────────────

def build_skills_section(skills):
    icon_keys = ",".join(
        LANG_TO_ICON[s] for s in skills if s in LANG_TO_ICON
    )
    badges = "\n".join(
        f'![{LANG_TO_BADGE[s][0]}](https://img.shields.io/badge/'
        f'{LANG_TO_BADGE[s][1]}?style=for-the-badge'
        f'&logo={LANG_TO_BADGE[s][2]}&logoColor={LANG_TO_BADGE[s][3]})'
        for s in skills if s in LANG_TO_BADGE
    )
    return f"""## 🛠️ **Technical Skills**

<div align="center">

<img src="https://skillicons.dev/icons?i={icon_keys}&theme=dark&perline=6" />

</div>

<div align="center">

{badges}

</div>"""

def build_stats_section():
    return f"""## 📊 **GitHub Statistics**

<div align="center">
  <img height="180em" src="https://github-readme-stats.vercel.app/api?username={USERNAME}&show_icons=true&theme=tokyonight&include_all_commits=true&count_private=true&hide_border=true&bg_color=0d1117&title_color=00d4ff&icon_color=a855f7&text_color=c9d1d9"/>
  <img height="180em" src="https://streak-stats.demolab.com?user={USERNAME}&theme=tokyonight&hide_border=true&background=0d1117&ring=00d4ff&fire=a855f7&currStreakLabel=00d4ff"/>
</div>

<div align="center">
  <img src="https://github-readme-stats.vercel.app/api/top-langs/?username={USERNAME}&layout=compact&theme=tokyonight&hide_border=true&bg_color=0d1117&title_color=00d4ff&text_color=c9d1d9" />
</div>

<div align="center">
  <img src="https://github-readme-activity-graph.vercel.app/graph?username={USERNAME}&theme=tokyo-night&hide_border=true&bg_color=0d1117&color=00d4ff&line=a855f7&point=00d4ff" width="100%"/>
</div>"""

def build_projects_section(repos):
    top = sorted(repos, key=lambda r: r["stargazers_count"], reverse=True)[:6]
    rows = "\n".join(
        f'| [{r["name"]}]({r["html_url"]}) '
        f'| {(r["description"] or "No description")[:60]} '
        f'| {r["language"] or "-"} '
        f'| ★{r["stargazers_count"]} |'
        for r in top
    )
    return f"""## 🚀 **Projects**

| Project | Description | Language | Stars |
|---------|-------------|----------|-------|
{rows}"""

def build_about_section(lang_totals):
    top_langs = [k for k, _ in sorted(lang_totals.items(), key=lambda x: -x[1])[:4]]
    lang_str  = ", ".join(f'"{l.title()}"' for l in top_langs)
    class_name = DISPLAY_NAME.replace(" ", "")
    return f"""## 💡 **About Me**

```python
class {class_name}:
    name      = "{DISPLAY_NAME}"
    username  = "{USERNAME}"
    uni       = "{UNI}"
    location  = "{LOCATION} 🇵🇰"
    languages = [{lang_str}]
    interests = {INTERESTS}
    goal      = "{GOAL}"

    def say_hi(self):
        print("Thanks for stopping by! Let's build something cool 🚀")

me = {class_name}()
me.say_hi()
```"""

def build_currently_section(lang_totals):
    top3 = [k.title() for k, _ in sorted(lang_totals.items(), key=lambda x: -x[1])[:3]]
    langs_str = ", ".join(f"**{l}**" for l in top3)
    return f"""## 🌱 **Currently Working On**

- 🤖 Exploring **Artificial Intelligence & Machine Learning**
- 💻 Building projects with {langs_str}
- 📚 Deepening knowledge in ** Databases & Data Analysis**


# ── Full README assembler ──────────────────────────────────────────────────────

def build_readme(profile, repos, lang_totals, skills):
    bio       = profile.get("bio") or "Passionately exploring AI, Software Development, and everything in between."
    updated   = datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC")
    name_enc  = DISPLAY_NAME.replace(" ", "%20").replace("'", "%27")

    header = f"""<!-- Header Banner -->
<div align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=0:0d1117,50:1a1a2e,100:7c3aed&height=200&section=header&text=Hi,%20I'm%20{name_enc}%20👋&fontSize=40&fontColor=00d4ff&fontAlignY=38&animation=fadeIn&desc=CS%20Student%20|%20Aspiring%20Developer&descSize=18&descAlignY=58&descColor=a855f7" width="100%"/>
</div>

---

## 👋 Hi, I'm [{DISPLAY_NAME}](https://github.com/{USERNAME})! | Computer Science Student | Aspiring Developer

{bio}

---"""

    connect = f"""## 🔗 **Connect With Me**

<div align="center">

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)]({LINKEDIN})
[![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/{USERNAME})

</div>"""

    footer = f"""<div align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=0:7c3aed,50:1a1a2e,100:0d1117&height=100&section=footer" width="100%"/>

  ![Visitor Count](https://visitor-badge.laobi.icu/badge?page_id={USERNAME}.{USERNAME}&color=00d4ff)

  *"Code is poetry written for machines, but read by humans."*

  <!-- auto-updated: {updated} -->
</div>"""

    sections = [
        header,
        build_skills_section(skills),
        "---",
        build_stats_section(),
        "---",
        build_projects_section(repos),
        "---",
        connect,
        "---",
        build_about_section(lang_totals),
        "---",
        build_currently_section(lang_totals),
        "---",
        footer,
    ]

    return "\n\n".join(sections) + "\n"

# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    print(f"[+] Fetching profile for {USERNAME}...")
    profile = get_profile()

    print("[+] Fetching repos...")
    repos = get_repos()
    print(f"    Found {len(repos)} non-fork repos")

    print("[+] Aggregating language data...")
    lang_totals = get_languages(repos)
    print(f"    Languages detected: {list(lang_totals.keys())}")

    print("[+] Detecting skills...")
    skills = detect_skills(lang_totals)
    print(f"    Skills: {skills}")

    print("[+] Building README...")
    readme = build_readme(profile, repos, lang_totals, skills)

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme)

    print("[✓] README.md written successfully")

if __name__ == "__main__":
    main()
