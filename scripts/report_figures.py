"""Black and white figures for the final report, drawn with ReportLab shapes.

Open markers are the direct workflow and filled markers are the staged workflow in every
figure, so the figures also read in a grayscale print.
"""

from reportlab.graphics.shapes import Circle, Drawing, Line, Polygon, PolyLine, Rect, String
from reportlab.lib.colors import HexColor, black, white

TEXT_WIDTH = 468
MODEL_GRAY = HexColor("#D9D9D9")
GRID = HexColor("#BFBFBF")
SMALL = 8


class Canvas:
    """A drawing with the two fonts and a few helpers shared by the figures."""

    def __init__(self, height: float, normal: str, bold: str):
        self.drawing = Drawing(TEXT_WIDTH, height)
        self.normal, self.bold = normal, bold

    def text(self, x, y, value, size=SMALL, anchor="middle", bold=False):
        font = self.bold if bold else self.normal
        self.drawing.add(
            String(x, y, value, fontName=font, fontSize=size, fillColor=black, textAnchor=anchor)
        )

    def line(self, x0, y0, x1, y1, width=0.6, color=black, dash=None):
        self.drawing.add(
            Line(x0, y0, x1, y1, strokeColor=color, strokeWidth=width, strokeDashArray=dash)
        )

    def marker(self, x, y, filled: bool, radius=2.6):
        fill = black if filled else white
        self.drawing.add(Circle(x, y, radius, fillColor=fill, strokeColor=black, strokeWidth=0.8))

    def legend(self, x, y, entries=(("Direct", False), ("Staged", True))):
        for label, filled in entries:
            self.marker(x, y + 2.6, filled)
            self.text(x + 7, y, label, anchor="start")
            x += 52


def workflow_figure(normal, bold):
    """The two workflows. Gray boxes are model calls and white boxes are Python code."""
    canvas = Canvas(84, normal, bold)
    drawing = canvas.drawing
    box_height, lanes = 30, {"Direct": 50, "Staged": 4}
    left, gap, writer_x = 94, 14, 410
    right = writer_x - gap

    def label(x, y, lines, bold=False, size=SMALL, anchor="middle"):
        top = y + (len(lines) - 1) * 4.6 - 2.7
        for index, line in enumerate(lines):
            canvas.text(x, top - index * 9.2, line, size, anchor, bold)

    def box(x, y, w, h, lines, model):
        fill = MODEL_GRAY if model else white
        drawing.add(
            Rect(x, y, w, h, rx=2.5, ry=2.5, fillColor=fill, strokeColor=black, strokeWidth=0.6)
        )
        label(x + w / 2, y + h / 2, lines)

    def arrow(start, end, y):
        canvas.line(start, y, end - 4, y, 0.8)
        drawing.add(
            Polygon(
                [end, y, end - 4.5, y + 2, end - 4.5, y - 2],
                fillColor=black,
                strokeColor=black,
                strokeWidth=0,
            )
        )

    for name, y in lanes.items():
        label(0, y + box_height / 2, [name], True, 8.5, "start")

    y = lanes["Direct"]
    label(62, y + box_height / 2, ["Sources", "and CRM"])
    one_call = ["One model call returns the fact, the matched record, and the decision"]
    box(left, y, right - left, box_height, one_call, True)
    arrow(80, left - 1, y + box_height / 2)
    arrow(right + 1, writer_x - 1, y + box_height / 2)

    y = lanes["Staged"]
    label(62, y + box_height / 2, ["Sources"])
    steps = (
        (["Model", "extraction"], True),
        (["Python matching", "against the CRM"], False),
        (["Model evidence", "check"], True),
        (["Python decision", "rules"], False),
    )
    width = (right - left - gap * 3) / 4
    arrow(80, left - 1, y + box_height / 2)
    for index, (lines, model) in enumerate(steps):
        x = left + index * (width + gap)
        box(x, y, width, box_height, lines, model)
        arrow(x + width + 1, x + width + gap - 1, y + box_height / 2)

    bottom, top = lanes["Staged"], lanes["Direct"] + box_height
    box(writer_x, bottom, TEXT_WIDTH - writer_x, top - bottom, ["CRM", "writer"], False)
    return drawing


def results_figure(panels, normal, bold):
    """Direct and staged on the main measures for each set of cases, with 95% intervals.

    `panels` maps a panel title to {measure: (direct, staged)}, where each value has the
    keys count, total, low, and high. The last measure is the one where lower is better.
    """
    measures = list(next(iter(panels.values())))
    row_height, top_pad = 25, 30
    height = top_pad + row_height * len(measures) + 26
    canvas = Canvas(height, normal, bold)
    label_width, gap = 132, 12
    width = (TEXT_WIDTH - label_width - gap * (len(panels) - 1)) / len(panels)
    bottom = 24
    top = bottom + row_height * len(measures)

    for row, measure in enumerate(measures):
        y = top - row_height * (row + 0.5)
        lines = measure.split("\n")
        for index, line in enumerate(lines):
            canvas.text(0, y + (len(lines) - 1) * 4.5 - 2.8 - index * 9, line, anchor="start")
    for column, (title, values) in enumerate(panels.items()):
        left = label_width + column * (width + gap)
        canvas.text(left + width / 2, top + 9, title, 8.5, bold=True)
        for tick in (0, 25, 50, 75, 100):
            x = left + width * tick / 100
            canvas.line(x, bottom, x, top, 0.4, GRID)
            if tick % 50 == 0:
                anchor = {0: "start", 50: "middle", 100: "end"}[tick]
                canvas.text(x, bottom - 9, f"{tick}%", anchor=anchor)
        canvas.line(left, bottom, left + width, bottom, 0.6)
        # A rule above the measure where lower is better.
        canvas.line(
            left, bottom + row_height, left + width, bottom + row_height, 0.4, black, [1.5, 1.5]
        )
        for row, measure in enumerate(measures):
            center = top - row_height * (row + 0.5)
            for value, filled, offset in zip(values[measure], (False, True), (4.6, -4.6)):
                y = center + offset
                low, high = left + width * value["low"], left + width * value["high"]
                canvas.line(low, y, high, y, 0.8)
                for x in (low, high):
                    canvas.line(x, y - 2, x, y + 2, 0.8)
                canvas.marker(left + width * value["count"] / value["total"], y, filled)
    canvas.legend(0, 2)
    return canvas.drawing


def models_figure(models, panels, normal, bold):
    """Direct and staged for each model size, one small panel per measure.

    `models` maps a model label to {"direct": row, "staged": row}. `panels` lists
    (title, note, function from a row to its value, axis maximum, ticks).
    """
    height = 148
    canvas = Canvas(height, normal, bold)
    gap, left_pad = 30, 20
    width = (TEXT_WIDTH - left_pad - gap * (len(panels) - 1)) / len(panels) - 4
    bottom, top = 34, height - 30
    names = list(models)
    for column, (title, note, value, maximum, ticks) in enumerate(panels):
        left = left_pad + column * (width + gap)
        canvas.text(left + width / 2, height - 9, title, 8.5, bold=True)
        canvas.text(left + width / 2, height - 19, note)
        for tick in ticks:
            y = bottom + (top - bottom) * tick / maximum
            canvas.line(left, y, left + width, y, 0.4, GRID)
            canvas.text(left - 4, y - 2.8, str(tick), anchor="end")
        canvas.line(left, bottom, left + width, bottom, 0.6)
        canvas.line(left, bottom, left, top, 0.6)
        step = width / len(names)
        for method, filled, dash in (("direct", False, [2.5, 2]), ("staged", True, None)):
            points = []
            for index, name in enumerate(names):
                x = left + step * (index + 0.5)
                y = bottom + (top - bottom) * value(models[name][method]) / maximum
                points += [x, y]
            canvas.drawing.add(
                PolyLine(points, strokeColor=black, strokeWidth=0.8, strokeDashArray=dash)
            )
            for x, y in zip(points[::2], points[1::2]):
                canvas.marker(x, y, filled)
        for index, name in enumerate(names):
            canvas.text(left + step * (index + 0.5), bottom - 10, name)
    canvas.text(left_pad + (TEXT_WIDTH - left_pad) / 2, 10, "Qwen3 model size")
    canvas.legend(left_pad, 8)
    return canvas.drawing
