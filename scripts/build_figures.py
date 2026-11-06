"""Draw the README figures from results/analysis/development.json.

Each figure is an SVG with its text kept as text and a small subset of STIX Two
Text embedded, so it looks the same on every machine. Wide figures use a canvas
1120 units across, and the narrow versions for phones use 420.
"""

import base64
import io
import json
from html import escape
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "results/analysis/development.json"
ASSETS = ROOT / "assets"
FONT_FILE = ASSETS / "fonts/STIXTwoText-Regular.ttf"
WIDE, NARROW = 1120, 420
TITLE, LABEL, NAME, NOTE = 23, 21, 20, 18

STYLE = """
svg{font-family:'STIX Two Text',serif;font-size:21px}
text{fill:#1f2328}
.soft{fill:#3d444d}
.mute{fill:#656d76}
.page{fill:#ffffff}
.grid{stroke:#e3e7ee;stroke-width:1}
.axis{stroke:#2b3138;stroke-width:1.2}
.bar{stroke:#2b3138;stroke-width:1.1}
.whisker{stroke:#1f2328;stroke-width:1.5}
.direct{fill:#b7bdc8}
.partial{fill:#c5d9f4}
.staged{fill:#3a7bd5}
.answer-key{fill:url(#hatch)}
.hatch-page{fill:#ffffff}
.hatch-line{stroke:#656d76;stroke-width:1.6}
@media (prefers-color-scheme:dark){
text{fill:#e6edf3}
.soft{fill:#c9d1d9}
.mute{fill:#9198a1}
.page{fill:#0d1117}
.grid{stroke:#2a3038}
.axis{stroke:#d0d7de}
.bar{stroke:#d0d7de}
.whisker{stroke:#e6edf3}
.direct{fill:#68717d}
.partial{fill:#24405f}
.staged{fill:#5b9bf0}
.hatch-page{fill:#0d1117}
.hatch-line{stroke:#9198a1}
}
"""

HATCH = (
    '<defs><pattern id="hatch" width="7" height="7" patternUnits="userSpaceOnUse" '
    'patternTransform="rotate(45)"><rect class="hatch-page" width="7" height="7"/>'
    '<line class="hatch-line" x1="0" y1="0" x2="0" y2="7"/></pattern></defs>'
)


class Figure:
    """An SVG canvas that refuses overlapping or clipped text when saved."""

    font = TTFont(FONT_FILE, recalcTimestamp=False)
    glyphs = font.getBestCmap()
    advances = font["hmtx"]
    units = font["head"].unitsPerEm

    def __init__(self, width, height, description):
        self.width, self.height, self.description = width, height, description
        self.parts, self.boxes, self.characters = [], [], set()

    def measure(self, value, size):
        return sum(self.advances[self.glyphs[ord(c)]][0] for c in value) * size / self.units

    def text(self, x, y, value, size=LABEL, anchor="middle", kind=""):
        width = self.measure(value, size)
        left = x - {"start": 0, "middle": width / 2, "end": width}[anchor]
        self.boxes.append((left, y - size * 0.72, left + width, y + size * 0.22, value))
        self.characters.update(value)
        kind = f' class="{kind}"' if kind else ""
        self.parts.append(
            f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" text-anchor="{anchor}"{kind}>{escape(value)}</text>'
        )

    def line(self, x0, y0, x1, y1, kind):
        self.parts.append(
            f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" class="{kind}"/>'
        )

    def column(self, x, width, top, bottom, kind):
        """A flat vertical bar with slightly rounded top corners."""
        if bottom - top < 0.5:
            return
        r = min(3, (bottom - top))
        self.parts.append(
            f'<path class="bar {kind}" d="M{x:.1f} {bottom:.1f}V{top + r:.1f}Q{x:.1f} {top:.1f} {x + r:.1f} {top:.1f}'
            f'H{x + width - r:.1f}Q{x + width:.1f} {top:.1f} {x + width:.1f} {top + r:.1f}V{bottom:.1f}Z"/>'
        )

    def row(self, x, width, y, height, kind):
        """A flat horizontal bar with slightly rounded right corners."""
        if width < 0.5:
            return
        r = min(3, width)
        self.parts.append(
            f'<path class="bar {kind}" d="M{x:.1f} {y:.1f}H{x + width - r:.1f}Q{x + width:.1f} {y:.1f} '
            f"{x + width:.1f} {y + r:.1f}V{y + height - r:.1f}Q{x + width:.1f} {y + height:.1f} "
            f'{x + width - r:.1f} {y + height:.1f}H{x:.1f}Z"/>'
        )

    def swatch(self, x, y, kind):
        self.parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="17" height="17" rx="2" class="bar {kind}"/>'
        )

    def font_face(self):
        options = subset.Options()
        options.flavor = "woff"
        options.layout_features = ["kern", "liga"]
        options.hinting = False
        options.recalc_timestamp = False
        font = TTFont(FONT_FILE, recalcTimestamp=False)
        subsetter = subset.Subsetter(options)
        subsetter.populate(unicodes={ord(c) for c in self.characters})
        subsetter.subset(font)
        font.flavor = "woff"
        buffer = io.BytesIO()
        font.save(buffer)
        data = base64.b64encode(buffer.getvalue()).decode()
        return f"@font-face{{font-family:'STIX Two Text';src:url(data:font/woff;base64,{data}) format('woff')}}"

    def check(self):
        for i, (left, top, right, bottom, value) in enumerate(self.boxes):
            if left < 0 or top < 0 or right > self.width or bottom > self.height:
                raise ValueError(f"Text outside the canvas: {value!r}")
            for other_left, other_top, other_right, other_bottom, other in self.boxes[i + 1 :]:
                if (
                    left < other_right
                    and other_left < right
                    and top < other_bottom
                    and other_top < bottom
                ):
                    raise ValueError(f"Overlapping text: {value!r} and {other!r}")

    def save(self, name):
        self.check()
        body = "\n".join(self.parts)
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.width} {self.height}" '
            f'width="{self.width}" height="{self.height}" role="img">\n'
            f"<desc>{escape(self.description)}</desc>\n"
            f"<style>{self.font_face()}{STYLE}</style>\n{HATCH}\n"
            f'<rect class="page" width="{self.width}" height="{self.height}"/>\n{body}\n</svg>\n'
        )
        ASSETS.mkdir(exist_ok=True)
        (ASSETS / name).write_text(svg)
        print(f"Wrote assets/{name}.")


def percent(row):
    return f"{row['count'] / row['total']:.1%}"


def count(row):
    return f"{row['count']}/{row['total']}"


def results_figure(measures):
    """Direct and staged on the four main measures, on one 0 to 100 percent scale."""
    description = "Direct and staged on the 66 development cases: " + "; ".join(
        f"{name}, direct {count(direct)}, staged {count(staged)}"
        for _, name, direct, staged in measures
    )
    figure = Figure(WIDE, 576, description)
    figure.text(WIDE / 2, 34, "Direct and staged workflows on the 66 development cases", TITLE)
    figure.text(
        WIDE / 2,
        62,
        "Percent of each measure's total • Whiskers show 95% Wilson intervals",
        NOTE,
        kind="soft",
    )
    figure.swatch(WIDE / 2 - 96, 80, "direct")
    figure.text(WIDE / 2 - 72, 94, "Direct", NOTE, "start", "soft")
    figure.swatch(WIDE / 2 + 18, 80, "staged")
    figure.text(WIDE / 2 + 42, 94, "Staged", NOTE, "start", "soft")

    top, bottom = 196, 486
    left, right = 76, 1092
    slot, panel_gap = 236, 72
    for tick in range(0, 101, 20):
        y = bottom - (bottom - top) * tick / 100
        figure.line(left, y, right, y, "axis" if tick == 0 else "grid")
        figure.text(left - 10, y + 6, f"{tick}%", NOTE, "end", "mute")
    figure.line(left, top, left, bottom, "axis")
    figure.text(left + slot * 1.5, 132, "Higher is better", LABEL)
    figure.text(left + slot * 3 + panel_gap + slot / 2, 132, "Lower is better", LABEL)

    width = 86
    for index, (panel, name, direct, staged) in enumerate(measures):
        center = left + slot * index + slot / 2 + (panel_gap if panel == "lower" else 0)
        for row, kind, x in (
            (direct, "direct", center - width - 3),
            (staged, "staged", center + 3),
        ):
            rate = row["count"] / row["total"]
            figure.column(x, width, bottom - (bottom - top) * rate, bottom, kind)
            middle = x + width / 2
            high, low = (bottom - (bottom - top) * row[end] for end in ("high", "low"))
            figure.line(middle, high, middle, low, "whisker")
            for y in (high, low):
                figure.line(middle - 7, y, middle + 7, y, "whisker")
            figure.text(middle, high - 9, count(row), NOTE, kind="soft")
            figure.text(middle, high - 31, percent(row), NOTE)
        for line_number, line in enumerate(name):
            figure.text(center, bottom + 30 + line_number * 25, line, NAME)
    figure.save("fig-results.svg")


def results_narrow(measures):
    description = "Direct and staged on the 66 development cases, one group of rows per measure."
    figure = Figure(NARROW, 0, description)
    figure.text(NARROW / 2, 30, "Direct and staged workflows", TITLE)
    figure.text(NARROW / 2, 57, "on the 66 development cases", TITLE)
    figure.text(NARROW / 2, 84, "Whiskers show 95% Wilson intervals", NOTE, kind="soft")
    y = 124
    left, length, height = 70, 216, 18
    for panel, name, direct, staged in measures:
        title = " ".join(name)
        direction = "Lower is better" if panel == "lower" else "Higher is better"
        figure.text(14, y, title, NAME, "start")
        figure.text(14, y + 23, direction, NOTE, "start", "soft")
        y += 34
        for row, label, kind in ((direct, "Direct", "direct"), (staged, "Staged", "staged")):
            figure.text(left - 8, y + 14, label, NOTE, "end", "soft")
            figure.row(left, length * row["count"] / row["total"], y, height, kind)
            low, high = left + length * row["low"], left + length * row["high"]
            middle = y + height / 2
            figure.line(low, middle, high, middle, "whisker")
            for x in (low, high):
                figure.line(x, middle - 5, x, middle + 5, "whisker")
            figure.text(NARROW - 14, y + 14, f"{percent(row)}  {count(row)}", NOTE, "end")
            y += 25
        figure.line(left, y - 57, left, y - 7, "axis")
        y += 34
    figure.height = y - 28
    figure.save("fig-results-narrow.svg")


def stages_figure(rows):
    """Review/reject cases accepted and correct decisions as the workflow changes."""
    description = "Workflow variants on the 66 development cases: " + "; ".join(
        f"{' '.join(row['label'])}, {row['unsafe_accepted']} of 28 review/reject cases accepted, "
        f"{row['decisions']} of 66 correct decisions"
        for row in rows
    )
    figure = Figure(WIDE, 500, description)
    figure.text(WIDE / 2, 34, "What each stage contributes on the 66 development cases", TITLE)
    figure.text(
        WIDE / 2,
        62,
        "From direct to full staged, then with the answer key's candidate",
        NOTE,
        kind="soft",
    )

    top, bottom = 164, 396
    panels = (
        (
            54,
            "Review/reject cases accepted",
            "Of 28 cases • Lower is better",
            "unsafe_accepted",
            28,
            (0, 7, 14, 21, 28),
        ),
        (
            590,
            "Correct decisions",
            "Of 66 cases • Higher is better",
            "decisions",
            66,
            (0, 22, 44, 66),
        ),
    )
    slot, width = 98, 84
    for left, title, subtitle, key, total, ticks in panels:
        right = left + slot * len(rows)
        middle = (left + right) / 2
        figure.text(middle, 102, title, LABEL)
        figure.text(middle, 126, subtitle, NOTE, kind="soft")
        for tick in ticks:
            y = bottom - (bottom - top) * tick / total
            figure.line(left, y, right, y, "axis" if tick == 0 else "grid")
            figure.text(left - 9, y + 6, str(tick), NOTE, "end", "mute")
        figure.line(left, top, left, bottom, "axis")
        for index, row in enumerate(rows):
            x = left + slot * index + (slot - width) / 2
            bar_top = bottom - (bottom - top) * row[key] / total
            figure.column(x, width, bar_top, bottom, row["kind"])
            figure.text(x + width / 2, bar_top - 9, str(row[key]), NOTE)
            for line_number, line in enumerate(row["label"]):
                figure.text(x + width / 2, bottom + 26 + line_number * 23, line, NOTE)
    figure.save("fig-stages.svg")


def stages_narrow(rows):
    description = "Workflow variants on the 66 development cases, one group of rows per measure."
    figure = Figure(NARROW, 0, description)
    figure.text(NARROW / 2, 30, "What each stage contributes", TITLE)
    figure.text(NARROW / 2, 57, "on the 66 development cases", TITLE)
    y = 96
    left, length, height = 14, 340, 16
    panels = (
        ("Review/reject cases accepted", "Of 28 cases • Lower is better", "unsafe_accepted", 28),
        ("Correct decisions", "Of 66 cases • Higher is better", "decisions", 66),
    )
    for title, subtitle, key, total in panels:
        figure.text(14, y, title, LABEL, "start")
        figure.text(14, y + 23, subtitle, NOTE, "start", "soft")
        y += 40
        for row in rows:
            figure.text(left, y + 12, " ".join(row["label"]), NOTE, "start")
            figure.row(left, length * row[key] / total, y + 19, height, row["kind"])
            figure.line(left, y + 17, left, y + 37, "axis")
            figure.text(left + length * row[key] / total + 8, y + 33, str(row[key]), NOTE, "start")
            y += 45
        y += 20
    figure.height = y - 22
    figure.save("fig-stages-narrow.svg")


def main():
    a = json.loads(ANALYSIS.read_text())
    table = a["main"]
    measures = [
        (
            "higher",
            ("Correct writes /", "accept decisions"),
            table["direct"]["accepted_accuracy"],
            table["staged"]["accepted_accuracy"],
        ),
        (
            "higher",
            ("Useful updates", "written"),
            table["direct"]["useful_coverage"],
            table["staged"]["useful_coverage"],
        ),
        (
            "higher",
            ("Correct", "decisions"),
            table["direct"]["decisions"],
            table["staged"]["decisions"],
        ),
        (
            "lower",
            ("Review/reject", "cases accepted"),
            table["direct"]["unsafe_accepted"],
            table["staged"]["unsafe_accepted"],
        ),
    ]
    results_figure(measures)
    results_narrow(measures)

    direct, on_direct, on_staged, full = a["variants"]
    rows = [
        {**direct, "label": ("Direct",), "kind": "direct"},
        {**on_direct, "label": ("Direct's", "candidate", "+ Python"), "kind": "partial"},
        {**on_staged, "label": ("Staged", "extraction", "+ Python"), "kind": "partial"},
        {**full, "label": ("Full staged", "workflow"), "kind": "staged"},
        {**a["verifier_check"], "label": ("Answer-key", "candidate"), "kind": "answer-key"},
    ]
    stages_figure(rows)
    stages_narrow(rows)


if __name__ == "__main__":
    main()
