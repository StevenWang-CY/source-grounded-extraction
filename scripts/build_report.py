"""Build the final report PDF from the analysis files in results/analysis."""

import json
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from xml.sax.saxutils import escape

from report_figures import models_figure, results_figure, workflow_figure
from reportlab.lib.colors import black
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
ANALYSIS = ROOT / "results/analysis"
OUTPUT = ROOT / "reports/EAS_0099_Final_Report.pdf"
REPOSITORY = "github.com/StevenWang-CY/source-grounded-extraction"
TITLE = "Source-Grounded CRM Extraction: Final Report"
METHODS = ("direct", "staged")

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


def main():
    sets = {
        name: json.loads((ANALYSIS / f"{name}.json").read_text())
        for name in ("development", "test", "second-test")
    }
    comparisons = json.loads((ANALYSIS / "comparisons.json").read_text())
    dev, test, second = sets.values()
    fixes, models, one_call = (comparisons[k] for k in ("fixes", "models", "one_call"))
    normal, bold = fonts()
    style = styles(normal, bold)

    def p(text, kind="body"):
        assert "{" not in text, text  # a value that was not filled in
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

    def figure(drawing, caption):
        return KeepTogether([Spacer(1, 2), drawing, p(caption, "figure_caption")])

    def link(url, text):
        return f'<a href="{url}">{text}</a>'

    def interval(row):
        rate = row["count"] / row["total"]
        return f"{row['count']}/{row['total']}, {rate:.1%} ({row['low']:.0%}–{row['high']:.0%})"

    def count(row):
        return f"{row['count']}/{row['total']}"

    def count_of(row):
        return f"{row['correct']} of {row['useful']}"

    def of(row):
        return f"{row['count']} of {row['total']}"

    def percent(row):
        return f"{row['count'] / row['total']:.1%}"

    def number_word(value):
        return ("No", "One", "Two", "Three", "Four", "Five", "Six")[value]

    def p_value(value):
        """A p-value with spaces that do not break, rounded half up (0.125 prints as 0.13)."""
        if value < 0.001:
            return "p\u00a0<\u00a00.001"
        places = Decimal("0.001") if value < 0.01 else Decimal("0.01")
        return f"p\u00a0=\u00a0{Decimal(str(value)).quantize(places, ROUND_HALF_UP)}"

    def more(new, old):
        return f"{new / old - 1:.0%}"

    # ------------------------------------------------------------------ facts used in the text
    main_test, paired = test["main"], test["paired"]
    direct, staged = main_test["direct"], main_test["staged"]
    chain = test["variants"]
    second_chain = second["variants"]
    low, high = paired["useful"]["difference_interval"]
    test_wrong = sum(len(g["wrong"]) for g in test["staged_failures"].values())
    test_missed = sum(len(g["missed"]) for g in test["staged_failures"].values())
    second_failures = second["staged_failures"]
    second_wrong = sum(len(g["wrong"]) for g in second_failures.values())
    second_missed = sum(len(g["missed"]) for g in second_failures.values())
    second_direct, second_staged = second["main"]["direct"], second["main"]["staged"]
    fix_second = fixes["second-test"]
    stopped_as_intended = sum(r["intended"] for r in test["review_reject"].values())

    # Sentences written by hand rest on these facts about the saved runs.
    for a in sets.values():
        choices = a["direct_choices"]
        assert not any(k.startswith("valid") and k != "valid accept" for k in choices), choices
    assert direct["unsafe_accepted"]["count"] + direct["invalid"] == 28
    assert test["invalid_kinds"]["direct"]["candidate"] == 0
    assert test["direct_choices"].get("invalid reject") == 2
    assert [dev["variants"][i]["unsafe_accepted"] for i in range(4)] == [21, 7, 2, 0]
    assert paired["unsafe"]["staged_only"] == 0
    assert test["wrong_writes_verifier_called_supported"] == test_wrong
    assert direct["unsafe_accepted"]["count"] + direct["invalid"] == 28
    assert test["direct_choices"] == {
        "valid accept": direct["accepted_accuracy"]["total"],
        "invalid accept": direct["invalid"] - 2,
        "invalid reject": 2,
    }
    assert (
        test["stages"]["staged"]["allowed"]["count"] == test["stages"]["staged"]["allowed"]["total"]
    )
    assert test["repeats"] == second["repeats"] == dev["repeats"] == {"repeated": 12, "same": 12}
    assert fix_second["before"]["unsafe_accepted"] == fix_second["after"]["unsafe_accepted"] == 1
    assert len(second_failures["Entity type does not fit the attribute"]["missed"]) == 5
    assert all(f["same_extraction_responses"] == 66 for f in fixes.values())

    # ------------------------------------------------------------------ tables and figures
    resources = [
        ["Resource", "Used for", "License", "Source"],
        [
            "FewRel 1.0 [11]",
            "90 public passages",
            "MIT",
            p(link("https://github.com/thunlp/FewRel", "github.com/thunlp/FewRel"), "cell"),
        ],
        [
            "Qwen3, 4-bit [18]",
            "The model (4B, and 1.7B, 8B, 14B)",
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
            "Running the models on Apple silicon",
            "MIT",
            p(link("https://github.com/ml-explore/mlx", "github.com/ml-explore/mlx"), "cell"),
        ],
    ]
    measure_names = {
        "Correct writes /\naccept decisions": "accepted_accuracy",
        "Useful updates\nwritten": "useful_coverage",
        "Correct decisions": "decisions",
        "Review/reject cases\naccepted (lower is better)": "unsafe_accepted",
    }
    panels = {
        title: {
            label: (a["main"]["direct"][key], a["main"]["staged"][key])
            for label, key in measure_names.items()
        }
        for title, a in zip(("Development", "Test", "Second test"), sets.values())
    }
    results = [
        ["Measure", "Direct", "Staged"],
        [
            "Correct writes / accept decisions",
            *(interval(main_test[m]["accepted_accuracy"]) for m in METHODS),
        ],
        ["Useful updates written", *(interval(main_test[m]["useful_coverage"]) for m in METHODS)],
        [
            "Review/reject cases accepted",
            *(interval(main_test[m]["unsafe_accepted"]) for m in METHODS),
        ],
        ["Correct decisions", *(interval(main_test[m]["decisions"]) for m in METHODS)],
        ["Invalid responses", *(main_test[m]["invalid"] for m in METHODS)],
    ]

    def field_row(name):
        cells = [name]
        for method in METHODS:
            f = test["fields"][method][name]
            cells += [f"{f['correct']}/{f['extracted']}", f"{f['correct']}/{f['expected']}"]
        return cells

    field_table = [
        ["Field", "Direct", "", "Staged", ""],
        ["", "Precision", "Recall", "Precision", "Recall"],
        *(field_row(name) for name in test["fields"]["direct"]),
    ]

    def chain_cells(row):
        return [
            f"{row['unsafe_accepted']}/{row['unsafe']}",
            f"{row['correct']}/{row['useful']}",
            f"{row['decisions']}/{row['cases']}",
        ]

    def chain_row(name, first, other):
        return [name, *chain_cells(first), *chain_cells(other)]

    contribution = [
        ["Workflow", "Test", "", "", "Second test", "", ""],
        ["", *["Review/reject accepted", "Useful written", "Correct decisions"] * 2],
        *(chain_row(a["name"], a, b) for a, b in zip(chain, second_chain)),
        chain_row(test["verifier_check"]["name"], test["verifier_check"], second["verifier_check"]),
    ]
    fixed_by = {
        "Value includes extra words": "Open",
        "Effective date not stated in the source": "Fix 1 (3 of 5)",
        "Identity matching": "Fixes 2, 3, 4",
        "Conflicting sources not detected": "Open",
        "Quotation altered": "Open",
    }
    failures = [
        ["Staged failure", "Wrong writes", "Missed updates", "Example", "Status"],
        *(
            [name, len(g["wrong"]), len(g["missed"]), g["example"], fixed_by[name]]
            for name, g in test["staged_failures"].items()
        ),
    ]

    def fix_row(label, row):
        return [
            label,
            f"{row['correct']}/{row['accepted']}",
            f"{row['correct']}/{row['useful']}",
            f"{row['unsafe_accepted']}/{row['unsafe']}",
            f"{row['decisions']}/{row['cases']}",
            row["invalid"],
        ]

    fix_table = [
        [
            "Staged workflow",
            "Correct writes / accept decisions",
            "Useful updates written",
            "Review/reject cases accepted",
            "Correct decisions",
            "Invalid responses",
        ],
        *(
            fix_row(f"{title}, {label}", fixes[name][key])
            for name, title in (
                ("development", "Development"),
                ("test", "Test"),
                ("second-test", "Second test"),
            )
            for key, label in (("before", "before the fixes"), ("after", "after the fixes"))
        ),
    ]
    one = one_call["second-test"]
    one_call_table = [
        [
            "Workflow",
            "Correct writes / accept decisions",
            "Useful updates written",
            "Review/reject cases accepted",
            "Correct decisions",
            "Invalid responses",
            "Tokens in / out",
            "Seconds per case",
        ],
        *(
            [
                name,
                count(r["accepted_accuracy"]),
                count(r["useful_coverage"]),
                count(r["unsafe_accepted"]),
                count(r["decisions"]),
                r["invalid"],
                f"{r['input_tokens'] / 1000:.0f}k / {r['output_tokens'] / 1000:.0f}k",
                f"{r['seconds']:.2f}",
            ]
            for name, r in one.items()
        ),
    ]
    model_rows = {name.removeprefix("Qwen3-"): m["main"] for name, m in models.items()}
    model_panels = [
        (
            "Review/reject cases accepted",
            "of 28, lower is better",
            lambda r: r["unsafe_accepted"]["count"],
            28,
            (0, 7, 14, 21, 28),
        ),
        (
            "Useful updates written",
            "of 38, higher is better",
            lambda r: r["useful_coverage"]["count"],
            38,
            (0, 19, 38),
        ),
        (
            "Invalid responses",
            "of 66, lower is better",
            lambda r: r["invalid"],
            66,
            (0, 22, 44, 66),
        ),
    ]

    small, base, large = (models[f"Qwen3-{size}"] for size in ("1.7B", "4B", "14B"))
    lenient = large["direct_lenient_match"]
    decisions_by_size = [m["main"]["direct"]["decisions"]["count"] for m in models.values()]
    invalid_by_size = [m["main"]["direct"]["invalid"] for m in models.values()]
    useful_by_size = [m["main"]["direct"]["useful_coverage"]["count"] for m in models.values()]
    assert lenient["invalid"] == 0 and useful_by_size[0] > useful_by_size[-1]
    assert (
        invalid_by_size == sorted(invalid_by_size) and decisions_by_size[0] > decisions_by_size[-1]
    )
    assert large["main"]["staged"]["unsafe_accepted"]["count"] == 0
    model_sentences = (
        "Staged got better as the model got larger. With Qwen3-14B it wrote "
        f"{large['main']['staged']['useful_coverage']['count']} of the 38 useful updates and accepted none of "
        f"the 28 review/reject cases, compared with {base['main']['staged']['useful_coverage']['count']} and "
        f"{base['main']['staged']['unsafe_accepted']['count']} for Qwen3-4B. Direct changed in a different "
        "way. The larger models did start to choose review or reject, but they also returned more invalid "
        "matches, such as a status of new together with a record ID. Direct's invalid responses rose from "
        f"{invalid_by_size[0]} with the smallest model to {invalid_by_size[-1]} with the largest. An invalid "
        "response writes nothing, so direct accepted fewer review/reject cases with the larger models mostly "
        f"for that reason, and its useful updates fell from {useful_by_size[0]} to {useful_by_size[-1]}. To "
        "give direct the benefit of the doubt, I also rescored its responses treating every match that names "
        "a record ID as a match to that record. Direct with Qwen3-14B then returned no invalid responses, "
        f"wrote {lenient['useful_coverage']['count']} useful updates, and still accepted "
        f"{lenient['unsafe_accepted']['count']} of the 28 review/reject cases. The smallest model shows the "
        f"limit of staging. With Qwen3-1.7B, staged accepted {small['main']['staged']['unsafe_accepted']['count']} "
        "review/reject cases, because the extraction and the evidence check still depend on the model."
    )
    plain, thinking, guided, staged_one = (
        one[k] for k in ("Direct", "Direct with thinking", "Guided direct", "Staged")
    )
    assert guided["decisions"]["count"] > max(
        plain["decisions"]["count"], thinking["decisions"]["count"]
    )
    assert thinking["invalid"] > plain["invalid"] > guided["invalid"]
    one_call_sentences = (
        "I also tried two stronger one-call workflows with Qwen3-4B (Table 7). Direct with thinking turns on "
        "the model's reasoning mode and raises the token limit to 4,096 so the reasoning fits. Guided direct adds the checks that staged runs in Python to the prompt, "
        "asks the model to record each check before it decides, and gives three worked examples. I tuned the "
        "guided prompt on the development set only. Guided direct was the best one-call workflow. On the "
        f"second test set it made {guided['decisions']['count']} correct decisions, wrote "
        f"{guided['useful_coverage']['count']} useful updates, and returned only {guided['invalid']} invalid "
        f"response. But it still accepted {guided['unsafe_accepted']['count']} of the 28 review/reject cases, "
        f"where staged accepted {staged_one['unsafe_accepted']['count']}. Thinking made direct reject a few "
        f"cases, but it also returned {thinking['invalid']} invalid responses, and it used about "
        f"{thinking['output_tokens'] / plain['output_tokens']:.0f} times the output tokens of direct. So a "
        "better prompt narrows the gap in correct decisions, but it does not stop unsafe updates from being "
        "written the way the Python rules do."
    )

    story = [
        p(TITLE, "title"),
        p("Chuyue Wang, December 2026", "byline"),
        p("EAS 0099, Fall 2026. Faculty supervisor: Professor Benjamin C. Pierce.", "byline"),
        HRFlowable(width="100%", thickness=0.6, color=black, spaceBefore=6, spaceAfter=4),
        p("Question", "section"),
        p(
            "A document may say that someone has a new role, or that one company now owns another. Before a "
            "customer relationship management (CRM) system can use a fact like this, something has to extract "
            "it, find the right record, check the evidence and dates, and decide whether to accept the update, "
            "send it for review, or reject it. I wanted to find out whether splitting these steps apart leads "
            "to fewer incorrect writes, and how many useful updates that costs. Sending a doubtful case to "
            "review is a reject option in the sense of Chow [1], and balancing accuracy on accepted cases "
            "against coverage of useful ones is similar to the tradeoff in selective classification [2]."
        ),
        p(
            f"On the 66 held-out test cases, the staged workflow accepted {staged['unsafe_accepted']['count']} "
            f"of the 28 cases that needed review or rejection, and the direct workflow accepted "
            f"{direct['unsafe_accepted']['count']}. Of staged's {staged['accepted_accuracy']['total']} accept "
            f"decisions, {staged['accepted_accuracy']['count']} produced a correct write "
            f"({percent(staged['accepted_accuracy'])}), compared with {direct['accepted_accuracy']['count']} of "
            f"{direct['accepted_accuracy']['total']} ({percent(direct['accepted_accuracy'])}) for direct. Staged "
            f"wrote {staged['useful_coverage']['count']} of the 38 useful updates and direct wrote "
            f"{direct['useful_coverage']['count']}. So staged made far fewer incorrect writes and gave up "
            f"{direct['useful_coverage']['count'] - staged['useful_coverage']['count']} useful updates."
        ),
        p(
            "This report covers the design, the test results, the failures I found and the fixes I made, and "
            "three follow-up experiments. I built a second test set to check the fixes on new cases, ran the "
            "comparison on smaller and larger models, and tried two stronger versions of the direct workflow."
        ),
        p("Workflows", "section"),
        p(
            "Figure 1 shows the two workflows, which I call direct and staged. They use the same small local "
            "model and get the same sources, CRM, extraction instructions, and update policy, and both send "
            "accepted updates to the same writer. Direct asks the model to do everything and follow the policy "
            "in one response. Staged applies the policy in Python, so the model only extracts a candidate and "
            "then checks the evidence, date, and source agreement."
        ),
        figure(
            workflow_figure(normal, bold),
            "<b>Figure 1.</b> The two workflows. Gray boxes are model calls and white boxes are Python code. "
            "Both share one CRM writer.",
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
            "<b>Dataset.</b> I use 198 cases in three sets of 66. Each set has 38 cases that should be accepted, "
            "17 that should go to review, and 11 that should be rejected. I used the development set while "
            "building the workflows and kept the test set for the comparison planned in my proposal. I built "
            "the second test set in November, after the fixes described below, to check them on cases the "
            "workflow had never seen."
        ),
        p(
            "Ninety cases adapt passages from FewRel [11] (Table 1), a public dataset whose Wikipedia sentences "
            "were aligned with Wikidata [12] facts by distant supervision [13] and then filtered by "
            "crowdworkers. These passages cover position held, ownership, and headquarters, and their CRM "
            "records, duplicates, and permission labels were built for this project. I chose FewRel because its "
            "short passages fit a task with one fact per case. DocRED's multi-sentence documents [14] and "
            "CrossRE's generic relation types [15] would need more adaptation. The other 108 cases are "
            "synthetic documents written for this project. They add things the public passages do not have, "
            "such as facts that have gone stale [16], sources that disagree [17], tentative claims, and denials. "
            "Each set has its own passages, names, and document forms. For the second test set I took the next "
            "ten acceptable passages per relation in file order and fixed the answer key before running any "
            "model on it."
        ),
        captioned(
            "<b>Table 1.</b> Open resources used in this project.",
            table(resources, [84, 150, 50, 184], text_columns=(0, 1, 2, 3)),
        ),
        p(
            "<b>Model and runs.</b> Both workflows use Qwen3-4B [18] in 4-bit form on MLX [19], with greedy "
            "decoding, thinking turned off, and a 512-token limit. I ran each workflow once on each case in a "
            "shuffled order, and ran six cases per set a second time to check consistency. Each execution "
            "starts from a fresh copy of the CRM, and the model never sees the answer keys."
        ),
        p(
            "<b>Measures.</b> <i>Correct writes / accept decisions</i> is the share of accept decisions that save "
            "the correct value in the CRM. <i>Useful updates written</i> counts correct writes among the 38 cases "
            "with a valid update. <i>Review/reject cases accepted</i> counts accept decisions among the 28 cases "
            "that should go to review or be rejected. <i>Correct decisions</i> counts right accept, review, or "
            "reject decisions, and an invalid response counts as wrong. <i>Invalid responses</i> fail validation "
            "and write nothing. I give 95% Wilson intervals [20] for rates. For paired comparisons I use an "
            "exact McNemar test [21] and a normal-approximation interval for the difference."
        ),
        p("Results on the held-out test set", "section"),
        p(
            "Figure 2 shows the main measures on all three sets, and Table 2 gives the numbers for the test set. "
            "The pattern from development held up on the test cases. When I compare the workflows case by case, "
            f"staged alone made the correct decision on {paired['decision']['staged_only']} cases and direct alone "
            f"on {paired['decision']['direct_only']} ({p_value(paired['decision']['p'])}). Direct alone accepted "
            f"{paired['unsafe']['direct_only']} review/reject cases and staged alone accepted none "
            f"({p_value(paired['unsafe']['p'])}). Direct alone wrote {paired['useful']['direct_only']} useful "
            f"updates and staged alone wrote {paired['useful']['staged_only']} ({p_value(paired['useful']['p'])}), "
            "so the difference in useful updates could be chance. With only 38 useful cases, the 95% interval for "
            f"direct's advantage runs from {abs(low):.0f} fewer to {high:.0f} more updates."
        ),
        figure(
            results_figure(panels, normal, bold),
            "<b>Figure 2.</b> Direct and staged on the three sets of 66 cases, with 95% Wilson intervals. "
            "Development and test use the workflow as tested, and the second test set uses the fixed workflow.",
        ),
        captioned(
            "<b>Table 2.</b> Main results on the 66 held-out test cases, with 95% Wilson intervals.",
            table(results, [188, 140, 140]),
        ),
        p(
            "Every valid direct response was an acceptance. The prompt gives direct the same decision policy "
            "that staged applies in code, but with this model direct never returned a valid review or reject "
            f"decision on any of the three sets. On the test set it accepted {direct['accepted_accuracy']['total']} "
            f"cases, including {direct['unsafe_accepted']['count']} of the 28 review/reject cases. Its other "
            f"{direct['invalid']} responses were invalid because the match was impossible, such as a record ID "
            f"for a new person, and all {direct['invalid']} were on review/reject cases. Two of them did choose "
            "reject, on the two denial cases, but they wrote reject as the match status as well."
        ),
        p(
            "Staged lost its useful updates on the public passages. It wrote "
            f"{count_of(test['origins']['staged']['fewrel_adapted'])} useful updates on FewRel passages and "
            f"{count_of(test['origins']['staged']['synthetic'])} on synthetic documents, and direct wrote "
            f"{count_of(test['origins']['direct']['fewrel_adapted'])} and "
            f"{count_of(test['origins']['direct']['synthetic'])}."
        ),
        p(
            "I also scored the steps inside each workflow. Entity resolution was correct in "
            f"{test['stages']['staged']['resolution']['count']} of 66 cases for staged and "
            f"{test['stages']['direct']['resolution']['count']} of 66 for direct. The cited source contained "
            f"the quotation in {of(test['stages']['staged']['quote'])} staged candidates, "
            f"compared with {of(test['stages']['direct']['quote'])} for direct. All "
            f"{test['stages']['staged']['allowed']['count']} staged accepts came from allowed sources, compared "
            f"with {of(test['stages']['direct']['allowed'])} for direct. The verifier's flags were right on "
            f"{of(test['stages']['staged']['verification'])} correctly extracted candidates. Staged stopped "
            f"{28 - staged['unsafe_accepted']['count']} of the 28 review/reject cases, and {stopped_as_intended} "
            "of them stopped at the rule written for that kind of case. The others stopped for another reason, "
            "such as a missing organization. Table 3 gives the extracted fields."
        ),
        captioned(
            "<b>Table 3.</b> Extracted fields on the test cases. Precision is correct over returned, and recall "
            "is correct over expected.",
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
            "An overall accuracy number can hide where a gain comes from [22], so I rescored parts of the "
            "workflow separately (Table 4). “Python steps” means matching and the decision rules. The first four "
            "rows use only the saved responses. The last row uses the answer key's candidate, so I can see how the later steps do without extraction errors."
        ),
        captioned(
            "<b>Table 4.</b> Results as parts of the workflow change. Rows 1 to 4 go from direct to full staged. Row 5 uses the answer key.",
            table(
                contribution,
                [136, 66, 42, 50, 66, 42, 50],
                header_rows=2,
                spans=[((1, 0), (3, 0)), ((4, 0), (6, 0))],
                rules=[((1, 0), (3, 0)), ((4, 0), (6, 0))],
            ),
        ),
        p(
            "On the test set, moving the match and the decision into Python, using direct's own candidates and no "
            f"verifier, cut accepted review/reject cases from {chain[0]['unsafe_accepted']} to "
            f"{chain[1]['unsafe_accepted']}. A separate extraction prompt brought them to "
            f"{chain[2]['unsafe_accepted']}, and adding the verifier brought them to {chain[3]['unsafe_accepted']}. "
            "Development gave 21, 7, 2, and 0 for the same four steps, and the second test set gave "
            f"{', '.join(str(r['unsafe_accepted']) for r in second_chain[:3])}, and {second_chain[3]['unsafe_accepted']}. "
            "So the Python matching and rules do most of the work in all three sets, which makes sense because "
            "direct does not apply the policy it is given."
        ),
        p(
            "When the later steps get the answer key's candidate, they make "
            f"{test['verifier_check']['decisions']} of 66 correct decisions on the test set and "
            f"{second['verifier_check']['decisions']} of 66 on the second test set, compared with "
            f"{chain[3]['decisions']} and {second_chain[3]['decisions']} for the full workflow. So most of the "
            "remaining staged errors come from extraction. The verifier does not catch these errors. On the "
            f"test set it called the candidate supported in all {test_wrong} accept decisions that went wrong."
        ),
        p("Failures on the test set and four fixes", "section"),
        p(
            f"On the test set, staged made {test_wrong} accept decisions that did not produce a correct write "
            f"and missed {test_missed} other useful updates. The saved traces sort into five groups (Table 5)."
        ),
        captioned(
            f"<b>Table 5.</b> All {test_wrong + test_missed} staged failures on the test set, grouped by cause. "
            "Wrong writes are accept decisions without a correct write.",
            table(failures, [128, 36, 42, 196, 66], text_columns=(0, 3, 4)),
        ),
        p(
            "I then made four fixes to the Python stages. (1) An effective date is kept only when the cited "
            "source writes it in full, and otherwise it is stored as unknown. (2) An organization written as the "
            "string “null” counts as missing. (3) A CRM record without an organization does not conflict with a "
            "stated organization. (4) A name that lengthens or shortens an existing record's name is ambiguous, "
            "not a new record. The prompts, the model, and the direct workflow stayed the same. I call the "
            "tested version workflow 3 and the fixed version workflow 4."
        ),
        p(
            "Twelve confirmed failures from development and test became regression tests. Each test replays the "
            "saved model responses through both versions. With the fixes, eight of them write the expected "
            "fact, two longer names now go to review, and two are still open. In one open case the owner is "
            "written with extra words, and in the other the quotation is shortened with an ellipsis."
        ),
        captioned(
            "<b>Table 6.</b> The staged workflow before and after the four fixes, on the same machine. "
            "Development before the fixes is the rerun on that machine, so it differs slightly from Figure 2.",
            table(fix_table, [150, 78, 62, 70, 58, 50]),
        ),
        p(
            "Table 6 shows staged before and after the fixes. The fixes were written from the development and "
            "test cases, so those rows only show that the fixes do what they were meant to do. The second test "
            f"set is the fair check. There the fixes raised correct writes from {fix_second['before']['correct']} "
            f"to {fix_second['after']['correct']} of 38 and cut accept decisions without a correct write from "
            f"{fix_second['before']['accepted'] - fix_second['before']['correct']} to "
            f"{fix_second['after']['accepted'] - fix_second['after']['correct']}. "
            f"{number_word(fix_second['correct_writes_gained'])} cases gained a correct write and none lost "
            f"one, which is still too few to rule out chance ({p_value(fix_second['p'])})."
        ),
        p("Results on the second test set", "section"),
        p(
            "The second test set gave the same picture as the test set (Figure 2). Staged with the fixes made "
            f"{second_staged['accepted_accuracy']['count']} correct writes out of "
            f"{second_staged['accepted_accuracy']['total']} accept decisions and accepted "
            f"{second_staged['unsafe_accepted']['count']} of the 28 review/reject cases. Direct made "
            f"{second_direct['accepted_accuracy']['count']} correct writes out of "
            f"{second_direct['accepted_accuracy']['total']} accept decisions and accepted "
            f"{second_direct['unsafe_accepted']['count']} review/reject cases. Staged made "
            f"{second_staged['decisions']['count']} correct decisions and direct made "
            f"{second_direct['decisions']['count']} ({p_value(second['paired']['decision']['p'])})."
        ),
        p(
            f"Staged still failed on {second_wrong + second_missed} cases, with {second_wrong} accept decisions "
            f"that did not produce a correct write and {second_missed} missed updates. The largest group had "
            "already appeared in development and was not one of the four fixes. In 5 cases the extractor gave "
            "an organization that is not a company, such as a society or a university channel, the entity "
            "type “organization”. The schema has no such type, so the response was "
            "invalid and nothing was written. One group is new. In 3 cases the extractor picked the wrong "
            "person as the subject. The other groups were known. They are values with extra words (2 cases), "
            "no candidate returned (2), a source conflict the verifier missed (1), and an organization left "
            "out (1). I left these unfixed, so the second test set stays an unseen check. Accepting "
            "“organization” as a company would be my next fix."
        ),
        p("Model size and stronger direct workflows", "section"),
        p(
            "The results above use one model and one direct prompt, so I checked both. First I ran the two "
            "workflows on the second test set with Qwen3-1.7B, 8B, and 14B (Figure 3). "
            + model_sentences
        ),
        figure(
            models_figure(model_rows, model_panels, normal, bold),
            "<b>Figure 3.</b> Direct and staged on the second test set for four sizes of Qwen3. An invalid "
            "response writes nothing, so it lowers both accepted review/reject cases and useful updates.",
        ),
        p(one_call_sentences),
        captioned(
            "<b>Table 7.</b> One-call workflows and staged on the second test set with Qwen3-4B. Tokens are "
            "totals for the 66 cases.",
            table(one_call_table, [86, 76, 46, 62, 46, 50, 54, 48]),
        ),
        p("Consistency and cost", "section"),
        p(
            "Every repeated execution returned the same responses as its first run, 12 of 12 on each of the "
            "three sets. Results do differ between machines. I ran the development set on an earlier Mac and "
            f"again on the M5 Max, and {dev['across_machines']['same_responses']} of "
            f"{dev['across_machines']['executions']} executions returned identical responses while "
            f"{dev['across_machines']['same_outcomes']} gave the same candidate, match, and decision. No main "
            "count moved by more than 2 cases. All test and second-test runs used the M5 Max."
        ),
        p(
            f"On the second test set, staged used {more(one['Staged']['input_tokens'], one['Direct']['input_tokens'])} "
            f"more input tokens and {more(one['Staged']['output_tokens'], one['Direct']['output_tokens'])} more "
            f"output tokens than direct, and took {one['Staged']['seconds']:.2f} seconds per case instead of "
            f"{one['Direct']['seconds']:.2f} (Table 7). Everything ran locally, so there was no API cost."
        ),
        p("Limits", "section"),
        p(
            "Each set has only 66 cases, so the intervals are wide, and a difference of three useful updates "
            "cannot be told apart from chance. The synthetic documents, CRM records, and answer keys were "
            "written for this project and were not checked by an independent annotator. The synthetic cases "
            "come from templates and are simpler than real documents. The answer keys were written to agree "
            "with the decision rules, and a test keeps them in agreement, so the correct-decisions measure "
            "favors a workflow that follows those rules exactly. The keys also accept only the listed value "
            "forms, so a value such as “The Milton Hershey School Trust” counts as wrong. Counting values that "
            "differ only in form would add two correct writes to each workflow on the test set and two to "
            "direct on the second test set. All models are 4-bit Qwen3 models, and the prompts were written "
            "for them. I tried one model from each of three other families on six cases, and more than half "
            "of their responses were invalid, so I left them out."
        ),
        p("Conclusion", "section"),
        p(
            "Splitting the work into steps led to fewer incorrect writes in every comparison I ran. The model "
            "extracted most facts correctly but did not apply the written policy, so the biggest gain came from "
            "moving the match and the decision into code. A second model call that checks the evidence stopped "
            "a few more unsafe cases, but it missed three of the four source conflicts in the two test sets "
            "and never questioned a wrong extraction. Most of the errors that remain start in extraction, and "
            "that is where I would work next."
        ),
        p(
            "The code, data, saved runs, regression tests, and detailed tables are in my repository at "
            f"{link('https://' + REPOSITORY, REPOSITORY)}. It also has a short demonstration that shows one "
            "saved case going through both workflows."
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
