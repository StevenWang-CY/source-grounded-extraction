"""Build the progress update PDF from results/analysis/development.json."""

import json
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "results/analysis/development.json"
OUTPUT = ROOT / "reports/EAS_0099_Progress_Update.pdf"
REPOSITORY = "github.com/StevenWang-CY/source-grounded-extraction"
TITLE = "Source-Grounded CRM Extraction: Progress Update"
METHODS = ("direct", "staged")
MODEL_GRAY = HexColor("#D9D9D9")
TEXT_WIDTH = 468

# Numbered in order of first citation. Each number links to the publisher's record.
REFERENCES = [
    (
        "C. K. Chow. On optimum recognition error and reject tradeoff. <i>IEEE Transactions on Information Theory</i>, 16(1):41–46, 1970.",
        "https://doi.org/10.1109/TIT.1970.1054406",
    ),
    (
        "Y. Geifman and R. El-Yaniv. Selective classification for deep neural networks. In <i>NeurIPS</i>, 2017.",
        "https://arxiv.org/abs/1705.08500",
    ),
    (
        "T. Wu, M. Terry, and C. J. Cai. AI Chains: Transparent and controllable human-AI interaction by chaining large language model prompts. In <i>CHI</i>, pp. 1–22, 2022.",
        "https://doi.org/10.1145/3491102.3517582",
    ),
    (
        "T. Khot et al. Decomposed prompting: A modular approach for solving complex tasks. In <i>ICLR</i>, 2023.",
        "https://arxiv.org/abs/2210.02406",
    ),
    (
        "J. Thorne et al. FEVER: A large-scale dataset for fact extraction and verification. In <i>NAACL</i>, pp. 809–819, 2018.",
        "https://aclanthology.org/N18-1074/",
    ),
    (
        "S. Dhuliawala et al. Chain-of-verification reduces hallucination in large language models. In <i>Findings of ACL</i>, pp. 3563–3578, 2024.",
        "https://aclanthology.org/2024.findings-acl.212/",
    ),
    (
        "H. Rashkin et al. Measuring attribution in natural language generation models. <i>Computational Linguistics</i>, 49(4):777–840, 2023.",
        "https://aclanthology.org/2023.cl-4.2/",
    ),
    (
        "T. Gao, H. Yen, J. Yu, and D. Chen. Enabling large language models to generate text with citations. In <i>EMNLP</i>, pp. 6465–6488, 2023.",
        "https://aclanthology.org/2023.emnlp-main.398/",
    ),
    (
        "V. Christophides et al. An overview of end-to-end entity resolution for big data. <i>ACM Computing Surveys</i>, 53(6):1–42, 2020.",
        "https://doi.org/10.1145/3418896",
    ),
    (
        "I. P. Fellegi and A. B. Sunter. A theory for record linkage. <i>J. Amer. Statist. Assoc.</i>, 64(328):1183–1210, 1969.",
        "https://doi.org/10.1080/01621459.1969.10501049",
    ),
    (
        "X. Han et al. FewRel: A large-scale supervised few-shot relation classification dataset with state-of-the-art evaluation. In <i>EMNLP</i>, pp. 4803–4809, 2018.",
        "https://aclanthology.org/D18-1514/",
    ),
    (
        "D. Vrandečić and M. Krötzsch. Wikidata: A free collaborative knowledgebase. <i>Communications of the ACM</i>, 57(10):78–85, 2014.",
        "https://doi.org/10.1145/2629489",
    ),
    (
        "M. Mintz et al. Distant supervision for relation extraction without labeled data. In <i>ACL-IJCNLP</i>, pp. 1003–1011, 2009.",
        "https://aclanthology.org/P09-1113/",
    ),
    (
        "Y. Yao et al. DocRED: A large-scale document-level relation extraction dataset. In <i>ACL</i>, pp. 764–777, 2019.",
        "https://aclanthology.org/P19-1074/",
    ),
    (
        "E. Bassignana and B. Plank. CrossRE: A cross-domain dataset for relation extraction. In <i>Findings of EMNLP</i>, pp. 3592–3604, 2022.",
        "https://aclanthology.org/2022.findings-emnlp.263/",
    ),
    (
        "B. Dhingra et al. Time-aware language models as temporal knowledge bases. <i>Transactions of the ACL</i>, 10:257–273, 2022.",
        "https://aclanthology.org/2022.tacl-1.15/",
    ),
    (
        "H.-T. Chen, M. Zhang, and E. Choi. Rich knowledge sources bring complex knowledge conflicts: Recalibrating models to reflect conflicting evidence. In <i>EMNLP</i>, pp. 2292–2307, 2022.",
        "https://aclanthology.org/2022.emnlp-main.146/",
    ),
    (
        "A. Yang et al. Qwen3 technical report. arXiv:2505.09388, 2025.",
        "https://arxiv.org/abs/2505.09388",
    ),
    (
        "A. Hannun et al. MLX: Efficient and flexible machine learning on Apple silicon. Software, 2023.",
        "https://github.com/ml-explore/mlx",
    ),
    (
        "E. B. Wilson. Probable inference, the law of succession, and statistical inference. <i>J. Amer. Statist. Assoc.</i>, 22(158):209–212, 1927.",
        "https://doi.org/10.1080/01621459.1927.10502953",
    ),
    (
        "Q. McNemar. Note on the sampling error of the difference between correlated proportions or percentages. <i>Psychometrika</i>, 12(2):153–157, 1947.",
        "https://doi.org/10.1007/BF02295996",
    ),
    (
        "S. Kapoor, B. Stroebl, Z. S. Siegel, N. Nadgir, and A. Narayanan. AI agents that matter. arXiv:2407.01502, 2024.",
        "https://arxiv.org/abs/2407.01502",
    ),
]


def fonts():
    folder = Path("/System/Library/Fonts/Supplemental")
    if not (folder / "Times New Roman.ttf").exists():
        return "Times-Roman", "Times-Bold"
    faces = {
        "Report": "Times New Roman.ttf",
        "ReportBold": "Times New Roman Bold.ttf",
        "ReportItalic": "Times New Roman Italic.ttf",
        "ReportBoldItalic": "Times New Roman Bold Italic.ttf",
    }
    for name, filename in faces.items():
        pdfmetrics.registerFont(TTFont(name, str(folder / filename)))
    pdfmetrics.registerFontFamily(
        "Report",
        normal="Report",
        bold="ReportBold",
        italic="ReportItalic",
        boldItalic="ReportBoldItalic",
    )
    return "Report", "ReportBold"


def styles(normal, bold):
    def style(name, font=normal, **settings):
        return ParagraphStyle(name, fontName=font, textColor=black, **settings)

    return {
        "title": style("Title", bold, fontSize=15, leading=18.5, spaceAfter=3),
        "byline": style("Byline", fontSize=10, leading=12.6),
        "section": style(
            "Section",
            bold,
            fontSize=11.5,
            leading=14,
            spaceBefore=9,
            spaceAfter=3,
            keepWithNext=1,
        ),
        "body": style("Body", fontSize=10, leading=12.4, spaceAfter=5),
        "caption": style("Caption", fontSize=9, leading=11, spaceBefore=4, spaceAfter=3),
        "figure_caption": style(
            "FigureCaption", fontSize=9, leading=11, spaceBefore=4, spaceAfter=8
        ),
        "cell": style("Cell", fontSize=9, leading=11),
        "number": style("Number", fontSize=9, leading=11, alignment=TA_CENTER),
        "head": style("Head", bold, fontSize=9, leading=11),
        "head_number": style("HeadNumber", bold, fontSize=9, leading=11, alignment=TA_CENTER),
        "reference": style(
            "Reference", fontSize=8.4, leading=10, spaceAfter=1, leftIndent=19, firstLineIndent=-19
        ),
    }


def workflow_figure(normal, bold):
    """Draw the two workflows. Gray boxes are model calls and white boxes are Python code."""
    drawing = Drawing(TEXT_WIDTH, 84)
    box_height, lanes = 30, {"Direct": 50, "Staged": 4}
    left, width, gap, writer_x = 94, 64.5, 14, 410
    right = writer_x - gap

    def label(x, y, lines, font=normal, size=8, anchor="middle"):
        top = y + (len(lines) - 1) * 4.6 - 2.7
        for index, line in enumerate(lines):
            drawing.add(
                String(
                    x,
                    top - index * 9.2,
                    line,
                    fontName=font,
                    fontSize=size,
                    fillColor=black,
                    textAnchor=anchor,
                )
            )

    def box(x, y, w, h, lines, model):
        fill = MODEL_GRAY if model else white
        drawing.add(
            Rect(x, y, w, h, rx=2.5, ry=2.5, fillColor=fill, strokeColor=black, strokeWidth=0.6)
        )
        label(x + w / 2, y + h / 2, lines)

    def arrow(start, end, y):
        drawing.add(Line(start, y, end - 4, y, strokeColor=black, strokeWidth=0.8))
        drawing.add(
            Polygon(
                [end, y, end - 4.5, y + 2, end - 4.5, y - 2],
                fillColor=black,
                strokeColor=black,
                strokeWidth=0,
            )
        )

    for name, y in lanes.items():
        label(0, y + box_height / 2, [name], bold, 8.5, "start")

    y = lanes["Direct"]
    label(62, y + box_height / 2, ["Sources", "and CRM"])
    box(
        left,
        y,
        right - left,
        box_height,
        ["One model call returns the fact, the matched record, and the decision"],
        True,
    )
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


def main():
    a = json.loads(ANALYSIS.read_text())
    normal, bold = fonts()
    style = styles(normal, bold)
    main_table, stages, fields = a["main"], a["stages"], a["fields"]
    paired, chain, verifier = a["paired"], a["variants"], a["verifier_check"]
    consistency, second = a["consistency"], a["second_run"]
    direct, rules_on_direct, rules_on_staged, full = chain
    conditions = a["review_reject"]
    intended = sum(r["intended"] for r in conditions.values())
    stops = a["other_stops"]

    # Sentences written by hand rest on these facts about the saved runs.
    assert intended + sum(stops.values()) == 28
    assert rules_on_staged["correct"] == full["correct"]
    assert conditions["explicit_denial"]["intended"] == 0
    always = "ambiguous_identity conflicting_sources duplicate_records future_update"
    for name in (*always.split(), "same_date_conflict", "stale_update"):
        assert conditions[name]["direct_accepted"] == conditions[name]["cases"]
    assert conditions["disallowed_source"]["direct_accepted"] == 4
    assert verifier["model_calls"] == 64
    assert stops["missing_organization"] == 7
    from_direct = a["from_direct_candidates"]
    assert a["direct_choices"] == {"valid accept": 57, "invalid accept": 5, "invalid reject": 4}
    assert a["invalid_kinds"]["direct"] == {"match": 8, "candidate": 1}
    assert a["invalid_kinds"]["staged"] == {"match": 0, "candidate": 4}
    assert a["extra_stops_with_staged_extraction"]["missing_organization"] == 4
    assert sum(a["extra_stops_with_staged_extraction"].values()) == 5
    assert a["wrong_writes_verifier_called_supported"] == 5
    assert a["original_answer_key"] == {"direct": 27, "staged": 23}
    low, high = paired["useful"]["difference_interval"]
    assert [r["unsafe_accepted"] for r in a["variants_second_run"]] == [23, 7, 2, 0]

    def p(text, kind="body"):
        return Paragraph(text, style[kind])

    def table(rows, widths, header_rows=1, spans=(), rules=(), text_columns=(0,)):
        cells = []
        for i, row in enumerate(rows):
            line = []
            for j, cell in enumerate(row):
                if isinstance(cell, Paragraph):
                    line.append(cell)
                    continue
                if i < header_rows:
                    kind = "head" if j in text_columns else "head_number"
                else:
                    kind = "cell" if j in text_columns else "number"
                line.append(p(escape(str(cell)), kind))
            cells.append(line)
        result = Table(cells, colWidths=widths, hAlign="CENTER", repeatRows=header_rows)
        result.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LINEABOVE", (0, 0), (-1, 0), 0.9, black),
                    ("LINEBELOW", (0, header_rows - 1), (-1, header_rows - 1), 0.5, black),
                    ("LINEBELOW", (0, -1), (-1, -1), 0.9, black),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 1.8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2.4),
                    *(("SPAN", start, end) for start, end in spans),
                    *(("LINEBELOW", start, end, 0.4, black) for start, end in rules),
                ]
            )
        )
        return result

    def captioned(caption, *flowables):
        return KeepTogether([p(caption, "caption"), *flowables, Spacer(1, 6)])

    def link(url, text):
        return f'<a href="{url}">{text}</a>'

    def interval(row):
        rate = row["count"] / row["total"]
        return f"{row['count']}/{row['total']}, {rate:.1%} ({row['low']:.0%}–{row['high']:.0%})"

    def field_row(name):
        cells = [name]
        for method in METHODS:
            f = fields[method][name]
            cells += [f"{f['correct']}/{f['extracted']}", f"{f['correct']}/{f['expected']}"]
        return cells

    def variant(row):
        return [
            row["name"],
            f"{row['correct']}/{row['accepted']}",
            f"{row['correct']}/38",
            f"{row['unsafe_accepted']}/28",
            f"{row['decisions']}/66",
        ]

    def p_value(value):
        return "p < 0.001" if value < 0.001 else f"p = {value:.2f}"

    resources = [
        ["Resource", "Used for", "License", "Source"],
        [
            "FewRel 1.0 [11]",
            "60 public passages",
            "MIT",
            p(link("https://github.com/thunlp/FewRel", "github.com/thunlp/FewRel"), "cell"),
        ],
        [
            "Qwen3-4B, 4-bit [18]",
            "The model in both workflows",
            "Apache 2.0",
            p(
                link(
                    "https://huggingface.co/mlx-community/Qwen3-4B-4bit",
                    "huggingface.co/mlx-community/Qwen3-4B-4bit",
                ),
                "cell",
            ),
        ],
        [
            "MLX [19]",
            "Running the model on Apple silicon",
            "MIT",
            p(link("https://github.com/ml-explore/mlx", "github.com/ml-explore/mlx"), "cell"),
        ],
    ]
    results = [
        ["Measure", "Direct", "Staged"],
        [
            "Correct writes / accept decisions",
            *(interval(main_table[m]["accepted_accuracy"]) for m in METHODS),
        ],
        ["Useful updates written", *(interval(main_table[m]["useful_coverage"]) for m in METHODS)],
        [
            "Review/reject cases accepted",
            *(interval(main_table[m]["unsafe_accepted"]) for m in METHODS),
        ],
        ["Correct decisions", *(interval(main_table[m]["decisions"]) for m in METHODS)],
        ["Invalid responses", *(main_table[m]["invalid"] for m in METHODS)],
    ]
    field_table = [
        ["Field", "Direct", "", "Staged", ""],
        ["", "Precision", "Recall", "Precision", "Recall"],
        *(field_row(name) for name in fields["direct"]),
    ]
    contribution = [
        [
            "Workflow",
            "Correct writes / accept decisions",
            "Useful updates written",
            "Review/reject cases accepted",
            "Correct decisions",
        ],
        *map(variant, chain),
        variant(verifier),
    ]
    failures = [
        ["Staged failure", "Wrong writes", "Missed updates", "Example"],
        *(
            [name, len(g["wrong"]), len(g["missed"]), g["example"]]
            for name, g in a["staged_failures"].items()
        ),
    ]
    wrong = sum(len(g["wrong"]) for g in a["staged_failures"].values())
    missed = sum(len(g["missed"]) for g in a["staged_failures"].values())
    fewrel = {m: a["origins"][m]["fewrel_adapted"] for m in METHODS}
    synthetic = {m: a["origins"][m]["synthetic"] for m in METHODS}
    input_extra = stages["staged"]["input_tokens"] / stages["direct"]["input_tokens"] - 1
    output_extra = stages["staged"]["output_tokens"] / stages["direct"]["output_tokens"] - 1
    organizations = {m: fields[m]["Organizations"] for m in METHODS}
    assert organizations["direct"]["expected"] == organizations["direct"]["correct"]

    story = [
        p(TITLE, "title"),
        p("Chuyue Wang, November 2026", "byline"),
        p("EAS 0099, Fall 2026. Faculty supervisor: Professor Benjamin C. Pierce.", "byline"),
        HRFlowable(width="100%", thickness=0.6, color=black, spaceBefore=6, spaceAfter=4),
        p("Question", "section"),
        p(
            "A document may say that someone has a new role, or that one company now owns another. Before a "
            "customer relationship management (CRM) system can use a fact like this, something has to extract "
            "it, find the right record, check the evidence and dates, and decide whether to accept the update, "
            "send it for review, or reject it. I want to find out whether splitting these steps apart leads to "
            "fewer incorrect writes, and how many useful updates that costs."
        ),
        p(
            "This question connects to earlier work. Sending a doubtful case to review is a reject option in "
            "the sense of Chow [1], and balancing accuracy on accepted cases against coverage of useful ones is "
            "similar to the tradeoff in selective classification [2]. This update covers the design, the "
            "dataset, and my results on the 66 development cases."
        ),
        p("Workflows", "section"),
        p(
            "I compare the two workflows in Figure 1, which I call direct and staged below. They use the same "
            "small local model and get the same sources, CRM, extraction instructions, and update policy, and "
            "both send accepted updates to the same writer. Direct asks the model to do everything and follow "
            "the policy in one response. Staged applies the policy in Python, so the model only extracts a "
            "candidate and then checks the evidence, date, and source agreement."
        ),
        KeepTogether(
            [
                Spacer(1, 2),
                workflow_figure(normal, bold),
                p(
                    "<b>Figure 1.</b> The two workflows. Gray boxes are model calls and white boxes are Python "
                    "code. Both share one CRM writer.",
                    "figure_caption",
                ),
            ]
        ),
        p(
            "I based the staged design on earlier work. Wu et al. [3] split a task into chained steps with "
            "visible results, and Khot et al. [4] show that a step can be ordinary code instead of a model. The "
            "evidence check labels a claim as supported, uncertain, or contradicted, which is close to the "
            "labels in the FEVER dataset [5], and it runs as a separate call, like the verification step in "
            "Chain-of-Verification [6]. Requiring an exact quotation from an allowed source is a simple, "
            "rule-based version of the attribution that Rashkin et al. [7] and Gao et al. [8] measure in "
            "generated text. Matching against the CRM is a small entity-resolution problem [9]. Its three "
            "outcomes (matched, ambiguous, and new) are like the link, possible link, and non-link of Fellegi "
            "and Sunter [10], and ambiguous cases go to a reviewer."
        ),
        p("Data and setup", "section"),
        p(
            "<b>Dataset.</b> I use 132 cases, half for development and half for test. Each half has 38 cases that "
            "should be accepted, 17 that should go to review, and 11 that should be rejected. Sixty cases adapt "
            "passages from FewRel [11] (Table 1), a public dataset whose Wikipedia sentences were aligned with Wikidata [12] "
            "facts by distant supervision [13] and then filtered by crowdworkers. These passages cover position "
            "held, ownership, and headquarters, and their CRM records, duplicates, and permission labels were "
            "built for this project. I chose FewRel because its short passages fit a task with one fact per case. "
            "DocRED's multi-sentence documents [14] and CrossRE's generic relation types [15] would need more "
            "adaptation. The other 72 cases are synthetic documents written for this project. They add things the "
            "public passages do not have, such as facts that have gone stale [16], sources that disagree [17], "
            "tentative claims, and denials. No target identity or passage appears in both halves, and the "
            "synthetic document forms differ."
        ),
        captioned(
            "<b>Table 1.</b> Open resources used in this project.",
            table(resources, [88, 144, 50, 186], text_columns=(0, 1, 2, 3)),
        ),
        p(
            "<b>Model and runs.</b> Both workflows use Qwen3-4B [18] in 4-bit form on MLX [19], with "
            "greedy decoding, thinking turned off, and a 512-token limit. I ran each workflow once on each "
            "development case in a shuffled order, which gives 132 executions. I also ran six cases a second time "
            "under both workflows, which adds 12 more. Each execution starts from a fresh copy of the CRM, and "
            "the model never sees the answer keys."
        ),
        p(
            "<b>Measures.</b> <i>Correct writes / accept decisions</i> is the share of "
            "accept decisions that save the correct value in the CRM. <i>Useful updates written</i> counts correct "
            "writes among the 38 cases with a valid update. <i>Review/reject cases accepted</i> counts accept "
            "decisions among the 28 cases that should go to review or be rejected. <i>Correct decisions</i> counts "
            "right accept, review, or reject decisions, and an invalid response counts as wrong. <i>Invalid "
            "responses</i> fail validation and write nothing. I give 95% Wilson intervals [20] for rates and use an exact McNemar test [21] for paired comparisons."
        ),
        p("Development results", "section"),
        p(
            f"Table 2 shows the main results. Staged made more correct decisions and accepted none of the "
            f"review/reject cases, but it wrote {direct['correct'] - full['correct']} fewer useful updates. When I "
            f"compare the workflows case by case, staged alone made the correct decision on "
            f"{paired['decision']['staged_only']} cases and direct alone on {paired['decision']['direct_only']} "
            f"({p_value(paired['decision']['p'])}). Direct alone accepted {paired['unsafe']['direct_only']} "
            f"review/reject cases and staged alone accepted none ({p_value(paired['unsafe']['p'])}). Direct alone "
            f"wrote {paired['useful']['direct_only']} useful updates and staged alone wrote "
            f"{paired['useful']['staged_only']} ({p_value(paired['useful']['p'])}), so this last difference could "
            f"be chance. With only 38 useful cases, the 95% interval for direct's advantage runs from "
            f"{abs(low):.0f} fewer to {high:.0f} more updates, so I cannot say from these cases how large the cost "
            "is."
        ),
        captioned(
            "<b>Table 2.</b> Main results on the 66 development cases, with 95% Wilson intervals. Staged accepts "
            "fewer cases, and more of the updates it accepts are correct.",
            table(results, [188, 140, 140]),
        ),
        p(
            "Two things matter here. The development cases guided the design, so the numbers do not predict how the "
            "workflows do on new documents. That is what the test cases are for. The answer key also gained three "
            "valid value forms after a review of the development outputs, raising correct writes from "
            f"{a['original_answer_key']['direct']} to {direct['correct']} for direct and "
            f"{a['original_answer_key']['staged']} to {full['correct']} for staged."
        ),
        p(
            "One result stands out. Every valid direct response was an acceptance. The prompt gives the same "
            "decision policy that staged applies in code, but direct never chose review, and its only 4 rejections "
            "came in invalid responses. It accepted every ambiguous identity, source conflict, duplicate record, "
            "future appointment, same-date conflict, and stale update, and 4 of 5 disallowed sources. For example, "
            "it overwrites Stefan Mensah's newer CRM role with a 2025 appointment, while staged rejects the update. "
            "Eight of direct's 9 invalid responses fail only on the match, which staged never asks the model for. "
            f"Staged wrote {fewrel['staged']['correct']} of {fewrel['staged']['useful']} useful updates on FewRel "
            f"passages and {synthetic['staged']['correct']} of {synthetic['staged']['useful']} on synthetic "
            f"documents, and direct wrote {fewrel['direct']['correct']} and {synthetic['direct']['correct']}."
        ),
        p(
            "I also scored the steps inside each workflow. Entity resolution was correct in "
            f"{stages['staged']['resolution']['count']} of 66 cases for staged and "
            f"{stages['direct']['resolution']['count']} of 66 for direct. All {stages['staged']['quote']['count']} "
            "staged quotations were found in their cited sources, compared with "
            f"{stages['direct']['quote']['count']} of {stages['direct']['quote']['total']} for direct. All "
            f"{stages['staged']['allowed']['count']} staged accepts came from allowed sources, compared with "
            f"{stages['direct']['allowed']['count']} of {stages['direct']['allowed']['total']} for direct. The "
            f"verifier's flags were right on {stages['staged']['verification']['count']} of "
            f"{stages['staged']['verification']['total']} correctly extracted candidates. In Table 3, the biggest "
            "difference is in organizations. Direct returned "
            f"{organizations['direct']['extracted'] - organizations['direct']['correct']} that do not match the "
            f"answer key, and staged missed "
            f"{organizations['staged']['expected'] - organizations['staged']['correct']} of the "
            f"{organizations['staged']['expected']} expected."
        ),
        captioned(
            "<b>Table 3.</b> Extracted fields on the development cases. Precision is correct over returned, and "
            "recall is correct over expected.",
            table(
                field_table,
                [148, 80, 80, 80, 80],
                header_rows=2,
                spans=[((1, 0), (2, 0)), ((3, 0), (4, 0))],
                rules=[((1, 0), (2, 0)), ((3, 0), (4, 0))],
            ),
        ),
        p("What each stage contributes", "section"),
        p(
            "An overall accuracy number can hide where a gain comes from [22], so I rescored parts of the workflow "
            "separately (Table 4). “Python steps” means matching and the decision rules. The first four rows "
            "use only the saved responses. The last row uses the answer key's candidate, so I can see "
            "how the later steps do without extraction errors."
        ),
        captioned(
            "<b>Table 4.</b> Results as parts of the workflow change. Rows 1 to 4 go from direct to full staged. Row 5 "
            "uses the answer key.",
            table(contribution, [196, 76, 70, 72, 54]),
        ),
        p(
            "When I moved the match and the decision into Python, using direct's own candidates and no verifier, "
            f"accepted review/reject cases dropped from {direct['unsafe_accepted']} to "
            f"{rules_on_direct['unsafe_accepted']}. Dropping the model's match also makes "
            f"{from_direct['became_valid']} of direct's 9 invalid responses usable, and "
            f"{from_direct['unsafe_accepted_from_them']} of the {rules_on_direct['unsafe_accepted']} come from those. "
            f"Useful updates fell from {direct['correct']} to {rules_on_direct['correct']}, with "
            f"{from_direct['lost_useful']} lost and {from_direct['gained_useful']} gained. All "
            f"{from_direct['lost_useful']} losses are historical roles where direct filled in an organization that "
            "the CRM record lacks, and matching sends those to review."
        ),
        p(
            f"Using a separate extraction prompt then brought accepted cases down to "
            f"{rules_on_staged['unsafe_accepted']}, although 4 of those 5 stops came from the missing organization "
            f"problem I describe next. Adding the verifier brought them to {full['unsafe_accepted']} without losing "
            "any useful updates. So the Python matching and rules do most of the work, which makes sense because "
            "direct does not apply the policy it is given."
        ),
        p(
            f"The zero does not mean that every check worked as I intended. Only {intended} of the 28 review/reject "
            f"cases stopped at the rule written for them. Another {stops['missing_organization']}, including both "
            "denials, stopped because the extractor left out the organization, which sends a current role to review "
            "before the verifier's answer is used."
        ),
        p(
            "To test the later steps without extraction errors, I ran the verifier on the answer key's candidates, "
            f"which took {verifier['model_calls']} new model calls. The workflow then made {verifier['decisions']} of "
            "66 correct decisions, and its one error accepts a draft staff record as settled. The full workflow made "
            f"{full['decisions']}, so most of the staged errors come from extraction. The verifier does not catch "
            f"these errors, since it reported no problem with any of the {wrong} wrong candidates that staged wrote. "
            "I should also note that the decision measure favors any workflow that follows the policy exactly."
        ),
        p("Where the staged workflow fails", "section"),
        p(
            f"On the useful cases, staged made {wrong} incorrect writes and missed {missed} other updates (Table 5). "
            "The wrong writes come from extraction details that the verifier accepts as supported. The missed "
            "updates come from extraction responses that were invalid, empty, or incomplete."
        ),
        captioned(
            f"<b>Table 5.</b> All {wrong + missed} staged failures on the 38 useful cases, grouped by cause.",
            table(failures, [150, 40, 46, 232], text_columns=(0, 3)),
        ),
        p("Consistency", "section"),
        p(
            f"Every repeated execution returned the same responses as its first run "
            f"({consistency['repeats_same_first_run']} of {consistency['repeated_executions']}). I also reran the "
            "development cases on a second Mac, an M5 Max, and the results do differ between the two machines, whose "
            f"package versions also differ slightly. On the M5 Max, {consistency['same_responses']} of "
            f"{consistency['executions']} executions returned identical responses, and "
            f"{consistency['same_outcomes']} gave the same candidate, match, and decision. Correct writes / accept "
            f"decisions were {second['direct']['correct']}/{second['direct']['accepted']} for direct and "
            f"{second['staged']['correct']}/{second['staged']['accepted']} for staged, and no main count moved by "
            "more than 2 cases. On the M5 Max, the first four rows of Table 4 gave 23, 7, 2, and 0 accepted review/reject cases. "
            "This tells me the results are stable across machines, but it says nothing about new cases."
        ),
        p("Cost", "section"),
        p(
            f"Staged used {input_extra:.0%} more input tokens and {output_extra:.0%} more output tokens."
        ),
        p("Status and next steps", "section"),
        p(
            "The dataset, both workflows, the evaluation code, the development analysis, and a demonstration on saved "
            f"cases are ready. My repository at {link('https://' + REPOSITORY, REPOSITORY)} has the code, data, saved "
            "runs, and more detailed tables."
        ),
        p(
            "I will continue to implement and experiment, and I will present the 66-case test comparison, its error "
            "analysis, and the regression tests in my final report on December 10."
        ),
        p("References", "section"),
        *(
            p(f"{link(url, f'[{number}]')}&nbsp;{text}", "reference")
            for number, (text, url) in enumerate(REFERENCES, 1)
        ),
    ]

    def page_number(canvas, document):
        canvas.setFont(normal, 9)
        canvas.setFillColor(black)
        canvas.drawCentredString(letter[0] / 2, 34, str(document.page))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    SimpleDocTemplate(
        str(OUTPUT),
        pagesize=letter,
        leftMargin=66,
        rightMargin=66,
        topMargin=52,
        bottomMargin=50,
        title=TITLE,
        author="Chuyue Wang",
        invariant=True,
    ).build(story, onFirstPage=page_number, onLaterPages=page_number)
    print(f"Wrote {OUTPUT.relative_to(ROOT)}.")


if __name__ == "__main__":
    main()
