from pathlib import Path
import json
import html


DATA = Path("../github-data.json")
OUTPUT = Path("../stats.svg")


data = json.loads(DATA.read_text(encoding="utf-8"))

username = data["username"]
name = data.get("name") or username
repos = data["repositories"]
languages = data["languages"]


# ---------------------------------------------------------
# CALCULATE TOTALS
# ---------------------------------------------------------

total_stars = sum(repo["stars"] for repo in repos)
total_forks = sum(repo["forks"] for repo in repos)

language_total = sum(languages.values())


# ---------------------------------------------------------
# LANGUAGE BARS
# ---------------------------------------------------------

language_lines = []

for language, count in list(languages.items())[:6]:

    percentage = (
        count / language_total * 100
        if language_total
        else 0
    )

    bar_length = round(percentage / 5)

    bar = "█" * bar_length

    language_lines.append(
        f"{language:<15} {bar:<20} {percentage:>5.1f}%"
    )


language_text = "\n".join(language_lines)


# ---------------------------------------------------------
# SVG SETTINGS
# ---------------------------------------------------------

WIDTH = 900
HEIGHT = 520

BG = "#ffffff"
FG = "#111111"
MUTED = "#666666"
LINE = "#d8d8d8"


# ---------------------------------------------------------
# SVG
# ---------------------------------------------------------

svg = f'''<svg
xmlns="http://www.w3.org/2000/svg"
width="{WIDTH}"
height="{HEIGHT}"
viewBox="0 0 {WIDTH} {HEIGHT}">

<rect
    width="100%"
    height="100%"
    fill="{BG}"
/>

<style>

.title {{
    font-family: "JetBrains Mono", monospace;
    font-size: 30px;
    font-weight: 700;
    fill: {FG};
}}

.label {{
    font-family: "JetBrains Mono", monospace;
    font-size: 14px;
    fill: {MUTED};
}}

.value {{
    font-family: "JetBrains Mono", monospace;
    font-size: 34px;
    font-weight: 700;
    fill: {FG};
}}

.mono {{
    font-family: "JetBrains Mono", monospace;
    font-size: 15px;
    fill: {FG};
}}

.small {{
    font-family: "JetBrains Mono", monospace;
    font-size: 13px;
    fill: {MUTED};
}}

</style>


<text
    x="50"
    y="65"
    class="title">
    GITHUB / {html.escape(username)}
</text>


<line
    x1="50"
    y1="90"
    x2="850"
    y2="90"
    stroke="{LINE}"
/>


<!-- REPOSITORIES -->

<text
    x="50"
    y="135"
    class="label">
    PUBLIC REPOSITORIES
</text>

<text
    x="50"
    y="175"
    class="value">
    {data["public_repos"]}
</text>


<!-- STARS -->

<text
    x="300"
    y="135"
    class="label">
    STARS
</text>

<text
    x="300"
    y="175"
    class="value">
    {total_stars}
</text>


<!-- FOLLOWERS -->

<text
    x="500"
    y="135"
    class="label">
    FOLLOWERS
</text>

<text
    x="500"
    y="175"
    class="value">
    {data["followers"]}
</text>


<!-- FOLLOWING -->

<text
    x="700"
    y="135"
    class="label">
    FOLLOWING
</text>

<text
    x="700"
    y="175"
    class="value">
    {data["following"]}
</text>


<line
    x1="50"
    y1="220"
    x2="850"
    y2="220"
    stroke="{LINE}"
/>


<!-- LANGUAGES -->

<text
    x="50"
    y="260"
    class="label">
    LANGUAGES
</text>
'''


y = 300

for line in language_lines:

    safe = html.escape(line)

    svg += f'''
<text
    x="50"
    y="{y}"
    class="mono">{safe}</text>
'''

    y += 30


# ---------------------------------------------------------
# TOP PROJECTS
# ---------------------------------------------------------

svg += '''
<text
    x="500"
    y="260"
    class="label">
    PROJECTS
</text>
'''

y = 300

for repo in repos[:5]:

    repo_name = html.escape(repo["name"])

    description = (
        repo.get("description")
        or "No description"
    )

    description = html.escape(
        description[:45]
    )

    svg += f'''
<text
    x="500"
    y="{y}"
    class="mono">{repo_name}</text>

<text
    x="500"
    y="{y + 18}"
    class="small">{description}</text>
'''

    y += 55


svg += '''
</svg>
'''


OUTPUT.write_text(
    svg,
    encoding="utf-8"
)


print("DONE!")
print(f"Created: {OUTPUT}")