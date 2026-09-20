from pathlib import Path
import json
import html
from datetime import date


# ---------------------------------------------------------
# PATHS
# ---------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent

DATA = ROOT / "contributions.json"
OUTPUT = ROOT / "contributions.svg"


# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------

if not DATA.exists():
    raise FileNotFoundError(
        f"Could not find {DATA}"
    )


data = json.loads(
    DATA.read_text(encoding="utf-8")
)


stats = data["stats"]
days = data["days"]

USERNAME = data["username"]


# ---------------------------------------------------------
# SETTINGS
# ---------------------------------------------------------

WIDTH = 1200
HEIGHT = 430

BG = "#0d1117"
TEXT = "#f0f6fc"
MUTED = "#8b949e"
LINE = "#c9d1d9"
FILL = "#21262d"

RIGHT_X = WIDTH - 55


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------

def esc(value):
    return html.escape(str(value))


def text(
    x,
    y,
    content,
    size=16,
    weight=400,
    color=TEXT,
    anchor="start",
):
    return (
        f'<text x="{x}" y="{y}" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, '
        f'Monaco, Consolas, monospace" '
        f'font-size="{size}px" '
        f'font-weight="{weight}" '
        f'fill="{color}" '
        f'text-anchor="{anchor}">'
        f'{esc(content)}</text>'
    )


# ---------------------------------------------------------
# NORMALIZE DAYS
# ---------------------------------------------------------

daily = []

for item in days:
    daily.append({
        "date": date.fromisoformat(item["date"]),
        "count": int(item["count"]),
        "weekday": int(item["weekday"]),
    })


daily.sort(key=lambda item: item["date"])


# ---------------------------------------------------------
# WEEKLY DATA
# ---------------------------------------------------------

weekly = []
current_week = 0

for item in daily:

    # GitHub's contribution calendar uses:
    # 0 = Sunday
    # 1 = Monday
    # ...
    # 6 = Saturday

    if item["weekday"] == 0 and current_week:
        weekly.append(current_week)
        current_week = 0

    current_week += item["count"]


if current_week:
    weekly.append(current_week)


# Keep approximately one year.
weekly = weekly[-53:]


# ---------------------------------------------------------
# BEST WEEK
# ---------------------------------------------------------

best_week = max(weekly) if weekly else 0


# ---------------------------------------------------------
# GRAPH GEOMETRY
# ---------------------------------------------------------

GRAPH_LEFT = 55
GRAPH_RIGHT = WIDTH - 55

GRAPH_TOP = 165
GRAPH_BOTTOM = 325

graph_width = GRAPH_RIGHT - GRAPH_LEFT
graph_height = GRAPH_BOTTOM - GRAPH_TOP

max_value = max(weekly) if weekly else 1

max_value = max(max_value, 1)


points = []


for index, value in enumerate(weekly):

    if len(weekly) == 1:
        x = GRAPH_LEFT
    else:
        x = (
            GRAPH_LEFT
            + (
                index
                / (len(weekly) - 1)
            )
            * graph_width
        )

    normalized = value / max_value

    y = (
        GRAPH_BOTTOM
        - normalized * graph_height
    )

    points.append((x, y))


# ---------------------------------------------------------
# SMOOTH PATH
# ---------------------------------------------------------

def smooth_path(points):

    if not points:
        return ""

    if len(points) == 1:
        x, y = points[0]
        return f"M {x} {y}"

    path = (
        f"M {points[0][0]} "
        f"{points[0][1]}"
    )

    for index in range(1, len(points)):

        x0, y0 = points[index - 1]
        x1, y1 = points[index]

        midpoint = (x0 + x1) / 2

        path += (
            f" C {midpoint} {y0}, "
            f"{midpoint} {y1}, "
            f"{x1} {y1}"
        )

    return path


line_path = smooth_path(points)


# ---------------------------------------------------------
# FILLED AREA
# ---------------------------------------------------------

if points:

    fill_path = (
        line_path
        + f" L {points[-1][0]} {GRAPH_BOTTOM}"
        + f" L {points[0][0]} {GRAPH_BOTTOM}"
        + " Z"
    )

else:
    fill_path = ""


# ---------------------------------------------------------
# SVG START
# ---------------------------------------------------------

svg = f'''<svg
xmlns="http://www.w3.org/2000/svg"
width="{WIDTH}"
height="{HEIGHT}"
viewBox="0 0 {WIDTH} {HEIGHT}">

<rect
    width="{WIDTH}"
    height="{HEIGHT}"
    fill="{BG}"
/>
'''


# ---------------------------------------------------------
# TOTAL CONTRIBUTIONS
# ---------------------------------------------------------

svg += text(
    55,
    48,
    f"{stats['total_contributions']:,}",
    30,
    700,
    TEXT,
)

svg += text(
    55,
    72,
    "contributions in the last year",
    12,
    400,
    MUTED,
)


# ---------------------------------------------------------
# RIGHT STATS
# ---------------------------------------------------------

svg += text(
    RIGHT_X,
    48,
    f"{stats['active_days']:,}",
    22,
    700,
    TEXT,
    "end",
)

svg += text(
    RIGHT_X,
    72,
    "active days",
    12,
    400,
    MUTED,
    "end",
)

svg += text(
    RIGHT_X,
    105,
    f"{best_week:,}",
    22,
    700,
    TEXT,
    "end",
)

svg += text(
    RIGHT_X,
    129,
    "best week",
    12,
    400,
    MUTED,
    "end",
)


# ---------------------------------------------------------
# GRAPH
# ---------------------------------------------------------

if line_path:

    # Area
    svg += f'''
<path
    d="{fill_path}"
    fill="{FILL}"
    opacity="0.9"
/>
'''

    # Line
    svg += f'''
<path
    d="{line_path}"
    fill="none"
    stroke="{LINE}"
    stroke-width="3"
    stroke-linecap="round"
    stroke-linejoin="round"
/>
'''

    # Endpoint
    last_x, last_y = points[-1]

    svg += f'''
<circle
    cx="{last_x}"
    cy="{last_y}"
    r="5"
    fill="{LINE}"
/>
'''


# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------

current_year = date.today().year

svg += text(
    55,
    385,
    "generated from GitHub contribution data",
    11,
    400,
    MUTED,
)

svg += text(
    RIGHT_X,
    355,
    str(current_year),
    12,
    400,
    MUTED,
    "end",
)

svg += text(
    RIGHT_X,
    385,
    USERNAME,
    12,
    500,
    MUTED,
    "end",
)


# ---------------------------------------------------------
# CLOSE SVG
# ---------------------------------------------------------

svg += "</svg>"


# ---------------------------------------------------------
# WRITE
# ---------------------------------------------------------

OUTPUT.write_text(
    svg,
    encoding="utf-8"
)


print()
print("========================================")
print(" Contribution SVG generated")
print("========================================")
print(f"Created   : {OUTPUT}")
print(f"Size      : {WIDTH} x {HEIGHT}")
print(f"Total     : {stats['total_contributions']}")
print(f"Active    : {stats['active_days']}")
print(f"Best week : {best_week}")
