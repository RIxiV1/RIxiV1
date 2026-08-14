from pathlib import Path
import html

import numpy as np
import cv2
from PIL import Image


INPUT = Path("../assets/portrait.jpg")
OUTPUT = Path("../portrait.svg")

# More detail than before
COLS = 120

FONT_SIZE = 10.5
CHAR_W = 6.3
LINE_HEIGHT = 1.15

# Dark -> light
RAMP = "@%#*+=-:. "

ROW_DELAY = 0.055


# ---------------------------------------------------------
# LOAD
# ---------------------------------------------------------

if not INPUT.exists():
    raise FileNotFoundError(f"Could not find {INPUT}")

print(f"Loading {INPUT}...")

image = Image.open(INPUT).convert("RGB")

img = np.array(image)


# ---------------------------------------------------------
# GRAYSCALE
# ---------------------------------------------------------

print("Converting to grayscale...")

gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)


# ---------------------------------------------------------
# LIGHT SMOOTHING
# ---------------------------------------------------------

# Don't use CLAHE here.
# Comic artwork already has strong contrast.

gray = cv2.GaussianBlur(
    gray,
    (3, 3),
    0
)


# ---------------------------------------------------------
# CONTRAST
# ---------------------------------------------------------

gray = cv2.normalize(
    gray,
    None,
    0,
    255,
    cv2.NORM_MINMAX
)


# ---------------------------------------------------------
# GAMMA
# ---------------------------------------------------------

# Keep the red suit from becoming one giant dark blob.

normalized = gray.astype(np.float32) / 255.0

gamma = 0.72

adjusted = np.power(normalized, gamma)

gray = np.clip(
    adjusted * 255,
    0,
    255
).astype(np.uint8)


# ---------------------------------------------------------
# RESIZE
# ---------------------------------------------------------

height, width = gray.shape

rows = max(
    1,
    round(COLS * (height / width) * 0.48)
)

print(
    f"Generating {COLS} x {rows} ASCII portrait..."
)

gray = cv2.resize(
    gray,
    (COLS, rows),
    interpolation=cv2.INTER_AREA
)


# ---------------------------------------------------------
# ASCII
# ---------------------------------------------------------

ascii_rows = []

for row in gray:

    line = ""

    for value in row:

        index = int(
            value / 255 * (len(RAMP) - 1)
        )

        index = max(
            0,
            min(len(RAMP) - 1, index)
        )

        line += RAMP[index]

    ascii_rows.append(line)


# ---------------------------------------------------------
# SVG
# ---------------------------------------------------------

print("Creating animated SVG...")

svg_width = COLS * CHAR_W
svg_height = rows * FONT_SIZE * LINE_HEIGHT

parts = []

parts.append(
    f'''<svg
xmlns="http://www.w3.org/2000/svg"
width="{svg_width:.0f}"
height="{svg_height:.0f}"
viewBox="0 0 {svg_width:.0f} {svg_height:.0f}">
'''
)

# White background
parts.append(
    '<rect width="100%" height="100%" fill="white"/>'
)

for i, line in enumerate(ascii_rows):

    y = FONT_SIZE * (i + 1) * LINE_HEIGHT

    safe_line = html.escape(line)

    delay = i * ROW_DELAY

    clip_id = f"row{i}"

    parts.append(
        f'''
<clipPath id="{clip_id}">
    <rect
        x="0"
        y="{y - FONT_SIZE}"
        width="0"
        height="{FONT_SIZE * 1.4}">
        <animate
            attributeName="width"
            from="0"
            to="{svg_width}"
            dur="0.65s"
            begin="{delay:.3f}s"
            fill="freeze"/>
    </rect>
</clipPath>

<text
    x="0"
    y="{y:.2f}"
    clip-path="url(#{clip_id})"
    font-family="monospace"
    font-size="{FONT_SIZE}px"
    fill="black">{safe_line}</text>
'''
    )

parts.append("</svg>")


OUTPUT.write_text(
    "\n".join(parts),
    encoding="utf-8"
)

print()
print("DONE!")
print(f"Created: {OUTPUT}")
print(f"Size: {COLS} columns x {rows} rows")