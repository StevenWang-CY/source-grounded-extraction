"""Black and white figures for the final report, drawn with ReportLab shapes.

Open circles are the direct workflow, open squares are guided direct, and filled circles are
the staged workflow in every chart, so the figures also read in a grayscale print.
"""

from reportlab.graphics.shapes import Circle, Drawing, Line, Polygon, PolyLine, Rect, String
from reportlab.lib.colors import HexColor, black, white
from reportlab.pdfbase.pdfmetrics import stringWidth

TEXT_WIDTH = 468
MODEL_GRAY = HexColor("#D9D9D9")
GRID = HexColor("#BFBFBF")
DIVIDER = HexColor("#7F7F7F")
SMALL = 8
STEPS = ("Extract the fact", "Match the record", "Check the evidence", "Make the decision")
# Each workflow's key, name, marker (filled, square), and line dash in the charts.
SERIES = (
    ("direct", "Direct", (False, False), [2.5, 2]),
    ("guided", "Guided direct", (False, True), [0.8, 1.8]),
    ("staged", "Staged", (True, False), None),
)
# What happened to a review/reject case, with its fill and its name in the key.
OUTCOMES = (
    ("accepted", black, "Accepted"),
    ("invalid", MODEL_GRAY, "Invalid response, nothing written"),
    ("held", white, "Sent to review or rejected"),
)


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

    def marker(self, x, y, filled: bool, square=False, radius=2.6):
        look = {"fillColor": black if filled else white, "strokeColor": black, "strokeWidth": 0.8}
        if square:
            side = radius * 1.8
            self.drawing.add(Rect(x - side / 2, y - side / 2, side, side, **look))
        else:
            self.drawing.add(Circle(x, y, radius, **look))

    def legend(self, x, y, keys=("direct", "staged")):
        for key, label, look, _ in SERIES:
            if key in keys:
                self.marker(x, y + 2.6, *look)
                self.text(x + 7, y, label, anchor="start")
                x += 7 + stringWidth(label, self.normal, SMALL) + 16


def workflow_figure(normal, bold):
    """The two workflows as the same four steps, between the case and the shared CRM writer.

    Direct is one gray box that holds all four steps. Staged has one box per step, gray for a
    model call and white for Python code.
    """
    box_height, gap, side, head = 26, 16, 44, 4.5
    staged_y = 20
    direct_y = staged_y + box_height + 24
    canvas = Canvas(direct_y + box_height + 13, normal, bold)
    drawing = canvas.drawing
    left, right = side + 18, TEXT_WIDTH - side - 32
    width = (right - left - gap * 3) / 4
    centers = [left + index * (width + gap) + width / 2 for index in range(len(STEPS))]

    def box(x, y, w, h, fill, dash=None):
        drawing.add(
            Rect(
                x,
                y,
                w,
                h,
                rx=3,
                ry=3,
                fillColor=fill,
                strokeColor=black,
                strokeWidth=0.6,
                strokeDashArray=dash,
            )
        )

    def label(x, y, lines):
        top = y + (len(lines) - 1) * 4.6 - 2.7
        for index, line in enumerate(lines):
            canvas.text(x, top - index * 9.2, line)

    def arrow(start, end, y):
        canvas.line(start, y, end - head + 0.5, y, 0.8)
        drawing.add(
            Polygon(
                [end, y, end - head, y + 2, end - head, y - 2],
                fillColor=black,
                strokeColor=black,
                strokeWidth=0,
            )
        )

    def title(y, name, note):
        canvas.text(left, y, name, 8.5, "start", True)
        canvas.text(left + stringWidth(name, bold, 8.5) + 6, y, note, anchor="start")

    # The case on the left and the writer on the right are shared by both workflows.
    bottom, top = staged_y, direct_y + box_height
    box(0, bottom, side, top - bottom, white, [2.5, 2])
    label(side / 2, (bottom + top) / 2, ["Sources", "and CRM"])
    box(TEXT_WIDTH - side, bottom, side, top - bottom, white)
    label(TEXT_WIDTH - side / 2, (bottom + top) / 2, ["CRM", "writer"])
    for y in (direct_y + box_height / 2, staged_y + box_height / 2):
        arrow(side + 1, left - 1, y)
        arrow(right + 1, TEXT_WIDTH - side - 1, y)
        canvas.text((right + TEXT_WIDTH - side) / 2 - 1, y + 3.5, "accept", 7.5)

    title(direct_y + box_height + 5, "Direct", "one model call does all four steps")
    box(left, direct_y, right - left, box_height, MODEL_GRAY)
    for x in centers[:-1]:
        divider = x + (width + gap) / 2
        canvas.line(divider, direct_y + 6, divider, direct_y + box_height - 6, 0.5, DIVIDER)
    for x, step in zip(centers, STEPS):
        label(x, direct_y + box_height / 2, [step])

    title(
        staged_y + box_height + 5,
        "Staged",
        "the model does two steps and Python code does the other two",
    )
    for index, (x, step) in enumerate(zip(centers, STEPS)):
        box(x - width / 2, staged_y, width, box_height, white if index % 2 else MODEL_GRAY)
        label(x, staged_y + box_height / 2, [step])
        if x != centers[-1]:
            arrow(x + width / 2 + 1, x + width / 2 + gap - 1, staged_y + box_height / 2)

    x = left
    for name, fill in (("Model call", MODEL_GRAY), ("Python code", white)):
        drawing.add(
            Rect(x, 1.5, 14, 8, rx=1.5, ry=1.5, fillColor=fill, strokeColor=black, strokeWidth=0.6)
        )
        canvas.text(x + 19, 3, name, anchor="start")
        x += 19 + stringWidth(name, normal, SMALL) + 18
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
    """The workflows for each model size, one small panel per measure.

    `models` maps a model label to {"direct": row, "guided": row, "staged": row}. `panels`
    lists (title, note, function from a row to its value, axis maximum, ticks).
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
        for method, _, look, dash in SERIES:
            points = []
            for index, name in enumerate(names):
                x = left + step * (index + 0.5)
                y = bottom + (top - bottom) * value(models[name][method]) / maximum
                points += [x, y]
            canvas.drawing.add(
                PolyLine(points, strokeColor=black, strokeWidth=0.8, strokeDashArray=dash)
            )
            for x, y in zip(points[::2], points[1::2]):
                canvas.marker(x, y, *look)
        for index, name in enumerate(names):
            canvas.text(left + step * (index + 0.5), bottom - 10, name)
    canvas.text(left_pad + (TEXT_WIDTH - left_pad) / 2, 10, "Qwen3 model size")
    canvas.legend(left_pad, 8, [key for key, *_ in SERIES])
    return canvas.drawing


def kinds_figure(kinds, workflows, normal, bold):
    """Every review/reject case as one square, by kind of case and workflow.

    `kinds` maps a kind's name to {"expected": "review" or "reject", "cases": n, and for each
    workflow {"accepted": a, "invalid": i, "held": h}}.
    """
    row, size, pitch, label_width = 10.2, 6.2, 7.8, 176
    groups = (
        ("review", "Cases that should go to review"),
        ("reject", "Cases that should be rejected"),
    )
    lines = sum(1 + sum(k["expected"] == group for k in kinds.values()) for group, _ in groups)
    total_y = 19
    bottom = total_y + 12
    top = bottom + lines * row + 3 * (len(groups) - 1)
    canvas = Canvas(top + 14, normal, bold)
    drawing = canvas.drawing
    column = (TEXT_WIDTH - label_width) / len(workflows)
    starts = [label_width + index * column for index in range(len(workflows))]

    def square(x, y, fill):
        drawing.add(Rect(x, y, size, size, fillColor=fill, strokeColor=black, strokeWidth=0.5))

    for x, name in zip(starts, workflows):
        canvas.text(x, top + 5, name, 8.5, "start", True)
    canvas.line(0, top + 1, TEXT_WIDTH, top + 1, 0.5)
    y = top
    for group, title in groups:
        y -= row if group == groups[0][0] else row + 3
        canvas.text(0, y + 2, title, anchor="start", bold=True)
        for name, kind in kinds.items():
            if kind["expected"] != group:
                continue
            y -= row
            canvas.text(8, y + 2, name, anchor="start")
            for start, workflow in zip(starts, workflows):
                x = start
                for outcome, fill, _ in OUTCOMES:
                    for _ in range(kind[workflow].get(outcome, 0)):
                        square(x, y + 1.2, fill)
                        x += pitch
    canvas.line(0, bottom - 2, TEXT_WIDTH, bottom - 2, 0.5)
    cases = sum(kind["cases"] for kind in kinds.values())
    canvas.text(0, total_y, f"Accepted, of all {cases} cases", anchor="start")
    for start, workflow in zip(starts, workflows):
        accepted = sum(kind[workflow].get("accepted", 0) for kind in kinds.values())
        canvas.text(start, total_y, f"{accepted} of {cases}", anchor="start")
    x = label_width
    for _, fill, name in OUTCOMES:
        square(x, 2, fill)
        canvas.text(x + size + 4, 2.6, name, anchor="start")
        x += size + 4 + stringWidth(name, normal, SMALL) + 14
    return drawing
