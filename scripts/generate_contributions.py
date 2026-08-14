from pathlib import Path
import json
import html
from datetime import date, timedelta


DATA = Path("../contributions.json")
OUTPUT = Path("../contributions.svg")

data = json.loads(DATA.read_text(encoding="utf-8"))

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
    anchor="start"
):
    return (
        f'<text x="{x}" y="{y}" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace" '
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

for d in days:
    daily.append({
        "date": date.fromisoformat(d["date"]),
        "count": int(d["count"])
    })

daily.sort(key=lambda x: x["date"])


# ---------------------------------------------------------
# BEST WEEK
# ---------------------------------------------------------

best_week = 0

for i in range(len(daily)):

    window_start = daily[i]["date"]
    window_end = window_start + timedelta(days=6)

    total = sum(
        d["count"]
        for d in daily
        if window_start <= d["date"] <= window_end
    )

    best_week = max(best_week, total)


# ---------------------------------------------------------
# WEEKLY GRAPH DATA
# ---------------------------------------------------------

# Group contributions into 7-day windows.
# This gives us the broad, elegant graph seen in the reference.

weekly = []

i = 0

while i < len(daily):

    start = daily[i]["date"]
    end = start + timedelta(days=6)

    total = sum(
        d["count"]
        for d in daily
        if start <= d["date"] <= end
    )

    weekly.append(total)

    i += 7


# Keep approximately the last year.
weekly = weekly[-53:]


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

# Avoid a completely flat graph if everything is tiny.
max_value = max(max_value, 1)


points = []

for i, value in enumerate(weekly):

    if len(weekly) == 1:
        x = GRAPH_LEFT
    else:
        x = (
            GRAPH_LEFT
            + (i / (len(weekly) - 1)) * graph_width
        )

    # Slightly compress extreme spikes.
    normalized = value / max_value

    y = (
        GRAPH_BOTTOM
        - normalized * graph_height
    )

    points.append((x, y))svg += text


# ---------------------------------------------------------
# BUILD SMOOTH SVG PATH
# ---------------------------------------------------------

def smooth_path(points):

    if not points:
        return ""

    if len(points) == 1:
        x, y = points[0]
        return f"M {x} {y}"

    path = f"M {points[0][0]} {points[0][1]}"

    for i in range(1, len(points)):

        x0, y0 = points[i - 1]
        x1, y1 = points[i]

        # Control points create a smooth curve.
        midpoint = (x0 + x1) / 2

        path += (
            f" C {midpoint} {y0}, "
            f"{midpoint} {y1}, "
            f"{x1} {y1}"
        )

    return path


line_path = smooth_path(points)


# Filled version of the same graph.

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
# BIG CONTRIBUTION COUNT
# ---------------------------------------------------------

svg += text(
    55,
    385,
    "generated from GitHub contribution data",
    11,
    400,
    MUTED
)

svg += text(
    RIGHT_X,
    355,
    "2026",
    12,
    400,
    MUTED,
    "end"
)

svg += text(
    RIGHT_X,
    385,
    USERNAME,
    12,
    500,
    MUTED,
    "end"
)


# ---------------------------------------------------------
# RIGHT STATS
# ---------------------------------------------------------

RIGHT_X = WIDTH - 55

svg += text(
    RIGHT_X,
    48,
    f"{stats['active_days']:,}",
    22,
    700,
    TEXT,
    "end"
)

svg += text(
    RIGHT_X,
    72,
    "active days",
    12,
    400,
    MUTED,
    "end"
)

svg += text(
    RIGHT_X,
    105,
    f"{best_week:,}",
    22,
    700,
    TEXT,
    "end"
)

svg += text(
    RIGHT_X,
    129,
    "best week",
    12,
    400,
    MUTED,
    "end"
)


# ---------------------------------------------------------
# GRAPH
# ---------------------------------------------------------

if line_path:

    # Area beneath graph
    svg += f'''
<path
    d="{fill_path}"
    fill="{FILL}"
    opacity="0.9"
/>
'''

    # Graph line
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

    # Endpoint dot
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

svg += text(
    55,
    345,
    "generated from GitHub contribution data",
    11,
    400,
    MUTED
)

svg += text(
    RIGHT_X,
    315,
    "2026",
    12,
    400,
    MUTED,
    "end"
)

svg += text(
    RIGHT_X,
    345,
    USERNAME,
    12,
    500,
    MUTED,
    "end"
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
print("DONE!")
print(f"Created: {OUTPUT}")
print(f"Size: {WIDTH} x {HEIGHT}")
print(f"Best week: {best_week}")