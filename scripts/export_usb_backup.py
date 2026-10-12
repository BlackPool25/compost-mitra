#!/usr/bin/env python3
"""Export USB Backup Assets with FAT32-safe naming and cryptographic manifest.

Generates:
1. usb_backup/EDA_REPORT.HTM: Clean standalone HTML export of notebooks/eda.ipynb
2. usb_backup/TOMATO_RECIPE.PDF: Standalone printable recipe card for Tomato companion composting
3. usb_backup/TOMATO_RECIPE.HTM: Standalone responsive HTML recipe card
4. usb_backup/ROSE_RECIPE.PDF: Printable recipe card for Rose companion composting
5. usb_backup/SPINACH_RECIPE.PDF: Printable recipe card for Spinach companion composting
6. usb_backup/MANIFEST.TXT: Listing with SHA-256 hashes, byte sizes, and FAT32-safe filenames.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
import sys
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

REPO_ROOT = Path(__file__).resolve().parent.parent
USB_DIR = REPO_ROOT / "usb_backup"

TIER_FOOTNOTE = "T1 REAL | LIT calc | D1 proxy"
SUPPLEMENT_DISCLAIMER = "Supplement, builds soil — not fertilizer replacement"
MODEL_DISCLAIMER = (
    "Model estimates reflect statistical associations on historical proxy data "
    "(sanity check, not proof)."
)

# Strict FAT32 filename pattern: alphanumeric, underscore, hyphen; 1-4 char extension.
FAT32_NAME_PATTERN = re.compile(r"^[A-Z0-9_-]+\.[A-Z0-9]{1,4}$")


def ensure_usb_dir() -> Path:
    USB_DIR.mkdir(parents=True, exist_ok=True)
    return USB_DIR


def export_eda_report_html(notebook_path: Path, output_path: Path) -> Path:
    """Convert eda.ipynb into a self-contained, beautifully styled HTML report."""
    with notebook_path.open("r", encoding="utf-8") as f:
        nb = json.load(f)

    html_parts = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '  <meta charset="utf-8">',
        '  <meta name="viewport" content="width=device-width, initial-scale=1.0">',
        "  <title>CompostMitra Foundation EDA Report</title>",
        "  <style>",
        "    :root {",
        "      --primary: #2D6A4F;",
        "      --primary-light: #52B788;",
        "      --bg: #F8F9FA;",
        "      --card-bg: #FFFFFF;",
        "      --text: #1B4332;",
        "      --text-muted: #555555;",
        "      --code-bg: #1E293B;",
        "      --code-text: #F8FAFC;",
        "      --output-bg: #F1F5F9;",
        "      --border: #D8F3DC;",
        "    }",
        "    body {",
        '      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;',
        "      background-color: var(--bg);",
        "      color: var(--text);",
        "      margin: 0;",
        "      padding: 24px;",
        "      line-height: 1.6;",
        "    }",
        "    .container {",
        "      max-width: 1040px;",
        "      margin: 0 auto;",
        "      background: var(--card-bg);",
        "      padding: 40px;",
        "      border-radius: 12px;",
        "      box-shadow: 0 4px 16px rgba(0,0,0,0.06);",
        "      border: 1px solid var(--border);",
        "    }",
        "    header {",
        "      border-bottom: 2px solid var(--primary);",
        "      padding-bottom: 16px;",
        "      margin-bottom: 24px;",
        "    }",
        "    h1 { color: var(--primary); margin: 0 0 8px 0; font-size: 28px; }",
        "    h2 { color: var(--primary); margin: 24px 0 12px 0; border-bottom: 1px solid #E2E8F0; padding-bottom: 6px; }",
        "    h3 { color: var(--primary-light); margin: 18px 0 8px 0; }",
        "    p { margin: 8px 0; color: #2D3748; }",
        "    pre {",
        "      background: var(--code-bg);",
        "      color: var(--code-text);",
        "      padding: 16px;",
        "      border-radius: 8px;",
        "      overflow-x: auto;",
        "      font-size: 13px;",
        "      margin: 12px 0;",
        "      line-height: 1.45;",
        "    }",
        "    pre.output {",
        "      background: var(--output-bg);",
        "      color: #0F172A;",
        "      border-left: 4px solid var(--primary-light);",
        "      font-weight: 500;",
        "    }",
        "    .badge {",
        "      display: inline-block;",
        "      background: #E8F5E9;",
        "      color: #1B4332;",
        "      padding: 4px 12px;",
        "      border-radius: 9999px;",
        "      font-size: 12px;",
        "      font-weight: 600;",
        "    }",
        "    .disclaimer-box {",
        "      background: #FFFBEB;",
        "      border: 1px solid #FDE68A;",
        "      color: #92400E;",
        "      padding: 14px 18px;",
        "      border-radius: 8px;",
        "      margin: 24px 0;",
        "      font-size: 13px;",
        "    }",
        "    footer {",
        "      margin-top: 40px;",
        "      padding-top: 16px;",
        "      border-top: 1px solid #E2E8F0;",
        "      font-size: 12px;",
        "      color: var(--text-muted);",
        "      text-align: center;",
        "    }",
        "  </style>",
        "</head>",
        "<body>",
        '  <div class="container">',
        "    <header>",
        "      <span class=\"badge\">CompostMitra Offline Archive</span>",
        "      <h1>Exploratory Data Analysis Report</h1>",
        "      <p>Cleaned feedstocks, statistical ranges, and schema alignment across Hafsa 452, Mullick 1314, and Zhang 848.</p>",
        "    </header>",
        '    <div class="disclaimer-box">',
        f"      <strong>Notice:</strong> {SUPPLEMENT_DISCLAIMER}.<br/>",
        f"      <strong>Scientific Footnote:</strong> {TIER_FOOTNOTE}.<br/>",
        f"      <strong>Validation:</strong> {MODEL_DISCLAIMER}",
        "    </div>",
    ]

    for cell in nb.get("cells", []):
        cell_type = cell.get("cell_type")
        source = "".join(cell.get("source", []))

        if cell_type == "markdown":
            # Simple markdown conversion for headings and paragraphs
            lines = source.splitlines()
            for line in lines:
                line_str = line.strip()
                if not line_str:
                    continue
                if line_str.startswith("# "):
                    html_parts.append(f"<h2>{html.escape(line_str[2:])}</h2>")
                elif line_str.startswith("## "):
                    html_parts.append(f"<h2>{html.escape(line_str[3:])}</h2>")
                elif line_str.startswith("### "):
                    html_parts.append(f"<h3>{html.escape(line_str[4:])}</h3>")
                elif line_str.startswith("- ") or line_str.startswith("* "):
                    html_parts.append(f"<ul><li>{html.escape(line_str[2:])}</li></ul>")
                elif re.match(r"^\d+\.\s+", line_str):
                    num_text = re.sub(r"^\d+\.\s+", "", line_str)
                    html_parts.append(f"<p><strong>&bull;</strong> {html.escape(num_text)}</p>")
                else:
                    html_parts.append(f"<p>{html.escape(line_str)}</p>")

        elif cell_type == "code":
            html_parts.append("<div class=\"code-block\">")
            html_parts.append(f"<pre><code>{html.escape(source)}</code></pre>")

            for out in cell.get("outputs", []):
                out_type = out.get("output_type")
                if out_type == "stream":
                    text = "".join(out.get("text", []))
                    html_parts.append(f'<pre class="output">{html.escape(text)}</pre>')
                elif out_type in ("execute_result", "display_data"):
                    data = out.get("data", {})
                    if "text/plain" in data:
                        text = "".join(data["text/plain"])
                        html_parts.append(f'<pre class="output">{html.escape(text)}</pre>')
            html_parts.append("</div>")

    html_parts.extend(
        [
            "    <footer>",
            f"      <p>Tier Footnote: {TIER_FOOTNOTE} | {MODEL_DISCLAIMER}</p>",
            "      <p>&copy; CompostMitra Project &bull; Zero-Network Standalone Export &bull; FAT32 Verified</p>",
            "    </footer>",
            "  </div>",
            "</body>",
            "</html>",
        ]
    )

    output_path.write_text("\n".join(html_parts), encoding="utf-8")
    return output_path


def export_recipe_card_pdf(
    plant_name: str,
    target_cn: str,
    weights: list[tuple[str, str, str]],
    metrics: list[tuple[str, str]],
    output_path: Path,
) -> Path:
    """Generate a printable, single-page PDF recipe card using ReportLab."""
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "CardTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1B4332"),
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "CardSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#2D6A4F"),
        spaceAfter=12,
    )
    header_style = ParagraphStyle(
        "CardHeader",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#2D6A4F"),
        spaceBefore=10,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "CardBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#2D3748"),
    )
    bold_style = ParagraphStyle(
        "CardBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#1B4332"),
    )
    disclaimer_style = ParagraphStyle(
        "CardDisclaimer",
        parent=styles["Italic"],
        fontName="Helvetica-Oblique",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#718096"),
    )

    story: list[Any] = []

    # Title Banner
    story.append(Paragraph(f"CompostMitra Recipe Card: {plant_name}", title_style))
    story.append(
        Paragraph(
            f"Target Companion Crop: <b>{plant_name}</b> | Cornell Optimal Balance C/N: <b>{target_cn}</b>",
            subtitle_style,
        )
    )
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2D6A4F"), spaceAfter=10))

    # Feedstock Proportion Table
    story.append(Paragraph("1. Recommended Feedstock Blend Proportions (Sum = 100%)", header_style))
    table_data = [
        [Paragraph("<b>Feedstock Item</b>", bold_style), Paragraph("<b>Group</b>", bold_style), Paragraph("<b>Proportion</b>", bold_style)]
    ]
    for item, grp, prop in weights:
        table_data.append([Paragraph(item, body_style), Paragraph(grp, body_style), Paragraph(prop, body_style)])

    prop_table = Table(table_data, colWidths=[240, 140, 140])
    prop_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D8F3DC")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#B7E4C7")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(prop_table)
    story.append(Spacer(1, 10))

    # Blended Characteristics Table
    story.append(Paragraph("2. Blended Batch Properties (Dry-Basis)", header_style))
    metric_data = [
        [Paragraph("<b>Metric</b>", bold_style), Paragraph("<b>Value / Heuristic Range</b>", bold_style)]
    ]
    for m_name, m_val in metrics:
        metric_data.append([Paragraph(m_name, body_style), Paragraph(m_val, body_style)])

    metric_table = Table(metric_data, colWidths=[260, 260])
    metric_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EDF2E7")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(metric_table)
    story.append(Spacer(1, 12))

    # Scientific Governance & Mandatory Disclaimers
    story.append(Paragraph("3. Governance & Disclaimers", header_style))
    story.append(Paragraph(f"<b>Notice:</b> {SUPPLEMENT_DISCLAIMER}.", body_style))
    story.append(Paragraph(f"<b>Tier Footnote:</b> {TIER_FOOTNOTE}", body_style))
    story.append(Paragraph(f"<b>Validation Label:</b> {MODEL_DISCLAIMER}", disclaimer_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CBD5E1"), spaceAfter=6))
    story.append(
        Paragraph(
            "CompostMitra Offline Foundation Archive &bull; FAT32 Safe Export &bull; Zero Network Required",
            disclaimer_style,
        )
    )

    doc.build(story)
    return output_path


def export_recipe_card_html(
    plant_name: str,
    target_cn: str,
    weights: list[tuple[str, str, str]],
    metrics: list[tuple[str, str]],
    output_path: Path,
) -> Path:
    """Generate responsive standalone HTML recipe card."""
    rows_weight = "\n".join(
        f"<tr><td>{html.escape(item)}</td><td>{html.escape(grp)}</td><td><strong>{html.escape(prop)}</strong></td></tr>"
        for item, grp, prop in weights
    )
    rows_metric = "\n".join(
        f"<tr><td>{html.escape(m)}</td><td><strong>{html.escape(v)}</strong></td></tr>"
        for m, v in metrics
    )

    content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CompostMitra Recipe Card - {plant_name}</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: #F0FDF4;
      color: #1B4332;
      padding: 24px;
      margin: 0;
    }}
    .card {{
      max-width: 680px;
      margin: 0 auto;
      background: #FFFFFF;
      border: 1px solid #B7E4C7;
      border-radius: 12px;
      padding: 32px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.06);
    }}
    h1 {{ color: #1B4332; margin-top: 0; font-size: 24px; }}
    h2 {{ color: #2D6A4F; font-size: 16px; border-bottom: 1px solid #D8F3DC; padding-bottom: 6px; }}
    table {{ width: 100%; border-collapse: collapse; margin-bottom: 16px; font-size: 14px; }}
    th, td {{ padding: 8px 12px; text-align: left; border-bottom: 1px solid #E2E8F0; }}
    th {{ background: #E8F5E9; color: #1B4332; }}
    .badge {{
      display: inline-block;
      background: #2D6A4F;
      color: #FFFFFF;
      padding: 4px 10px;
      border-radius: 9999px;
      font-size: 12px;
      font-weight: bold;
    }}
    .footer-note {{ font-size: 11px; color: #64748B; margin-top: 24px; border-top: 1px solid #E2E8F0; padding-top: 12px; }}
  </style>
</head>
<body>
  <div class="card" id="recipe-card-1">
    <span class="badge">GRADE A OPTIMAL</span>
    <h1>Compost Recipe: {plant_name}</h1>
    <p>Target C/N Ratio: <strong>{target_cn}</strong> | Reference: Cornell 30:1 Literature Balance</p>
    
    <h2>1. Feedstock Proportions</h2>
    <table>
      <thead><tr><th>Ingredient</th><th>Group</th><th>Weight %</th></tr></thead>
      <tbody>{rows_weight}</tbody>
    </table>

    <h2>2. Blended Characteristics</h2>
    <table>
      <thead><tr><th>Metric</th><th>Estimated Value</th></tr></thead>
      <tbody>{rows_metric}</tbody>
    </table>

    <div class="footer-note">
      <p><strong>Notice:</strong> {SUPPLEMENT_DISCLAIMER}</p>
      <p><strong>Tier Footnote:</strong> {TIER_FOOTNOTE}</p>
      <p><strong>Validation:</strong> {MODEL_DISCLAIMER}</p>
    </div>
  </div>
</body>
</html>"""
    output_path.write_text(content, encoding="utf-8")
    return output_path


def generate_manifest(usb_dir: Path) -> Path:
    """Generate MANIFEST.TXT containing SHA-256 hashes and FAT32 verification."""
    manifest_path = usb_dir / "MANIFEST.TXT"
    lines = [
        "# COMPOSTMITRA USB BACKUP MANIFEST",
        "# Generated for M1 Foundation Gate Rehearsal",
        "# File naming constraints: Strict FAT32 (alphanumeric, underscores, short extension)",
        "# Format: SHA256  SIZE_BYTES  FILENAME",
        "#" + "-" * 78,
    ]

    files = sorted(
        [
            p
            for p in usb_dir.iterdir()
            if p.is_file() and p.name != "MANIFEST.TXT" and not p.name.startswith(".")
        ]
    )

    for p in files:
        # Assert FAT32 compliant name
        filename = p.name
        if not FAT32_NAME_PATTERN.match(filename):
            raise ValueError(f"FAT32 naming violation: '{filename}' does not match pattern {FAT32_NAME_PATTERN.pattern}")

        content_bytes = p.read_bytes()
        sha256 = hashlib.sha256(content_bytes).hexdigest()
        size_bytes = len(content_bytes)
        lines.append(f"{sha256}  {size_bytes:>10}  {filename}")

    lines.append("#" + "-" * 78)
    lines.append(f"# Total files in backup: {len(files)}")
    lines.append("")

    manifest_path.write_text("\n".join(lines), encoding="utf-8")
    return manifest_path


def main() -> int:
    ensure_usb_dir()
    print(f"[export_usb_backup] Target USB directory: {USB_DIR}")

    # 1. Export HTML EDA Report
    notebook_file = REPO_ROOT / "notebooks" / "eda.ipynb"
    if notebook_file.exists():
        eda_out = USB_DIR / "EDA_REPORT.HTM"
        export_eda_report_html(notebook_file, eda_out)
        print(f"  [OK] Exported {eda_out.name} ({eda_out.stat().st_size} bytes)")
    else:
        print(f"  [WARN] Notebook {notebook_file} not found, skipping HTML export.")

    # Recipe specifications
    tomato_weights = [
        ("Dry Leaves", "Brown", "20.0%"),
        ("Vegetable Scraps", "Green", "25.0%"),
        ("Garden Waste", "Brown/Green", "25.0%"),
        ("Banana Peel", "Green", "15.0%"),
        ("Coffee Grounds", "Green", "10.0%"),
        ("Eggshell", "Mineral/Brown", "5.0%"),
    ]
    tomato_metrics = [
        ("C/N Ratio (dry-basis)", "25.96 (~26:1 Cornell target)"),
        ("Blended Moisture", "50.5% (Optimal 45-60%)"),
        ("Estimated pH", "6.98 (HEURISTIC-linear-approx)"),
        ("Macronutrients (N-P-K)", "N: 1.63%, P: 0.31%, K: 1.09%"),
        ("Heuristic Grade", "MOCK_GRADE_A (Optimal)"),
        ("Companion Compatibility", "Tomato 91% (Sanity proxy, not proof)"),
    ]

    rose_weights = [
        ("Dry Leaves", "Brown", "40.0%"),
        ("Vegetable Scraps", "Green", "20.0%"),
        ("Coffee Grounds", "Green", "20.0%"),
        ("Cardboard (Shredded)", "Brown", "15.0%"),
        ("Eggshell", "Mineral", "5.0%"),
    ]
    rose_metrics = [
        ("C/N Ratio (dry-basis)", "28.40 (Optimal ~28:1)"),
        ("Blended Moisture", "48.2%"),
        ("Estimated pH", "6.65 (Slightly acidic for Roses)"),
        ("Macronutrients (N-P-K)", "N: 1.45%, P: 0.28%, K: 0.85%"),
        ("Heuristic Grade", "GRADE_A (Optimal)"),
        ("Companion Compatibility", "Rose 88% (Sanity proxy, not proof)"),
    ]

    spinach_weights = [
        ("Grass Clippings", "Green", "35.0%"),
        ("Vegetable Scraps", "Green", "25.0%"),
        ("Dry Leaves", "Brown", "35.0%"),
        ("Eggshell", "Mineral", "5.0%"),
    ]
    spinach_metrics = [
        ("C/N Ratio (dry-basis)", "26.10 (High Nitrogen profile)"),
        ("Blended Moisture", "54.0%"),
        ("Estimated pH", "7.10 (Neutral)"),
        ("Macronutrients (N-P-K)", "N: 2.10%, P: 0.45%, K: 1.25%"),
        ("Heuristic Grade", "GRADE_A (Optimal)"),
        ("Companion Compatibility", "Spinach 84% (Sanity proxy, not proof)"),
    ]

    # 2. Export Recipe Cards (PDF + HTML)
    export_recipe_card_pdf("Tomato", "25-30:1", tomato_weights, tomato_metrics, USB_DIR / "TOMATO_RECIPE.PDF")
    print(f"  [OK] Exported TOMATO_RECIPE.PDF")

    export_recipe_card_html("Tomato", "25-30:1", tomato_weights, tomato_metrics, USB_DIR / "TOMATO_RECIPE.HTM")
    print(f"  [OK] Exported TOMATO_RECIPE.HTM")

    export_recipe_card_pdf("Rose", "28-32:1", rose_weights, rose_metrics, USB_DIR / "ROSE_RECIPE.PDF")
    print(f"  [OK] Exported ROSE_RECIPE.PDF")

    export_recipe_card_pdf("Spinach", "25-28:1", spinach_weights, spinach_metrics, USB_DIR / "SPINACH_RECIPE.PDF")
    print(f"  [OK] Exported SPINACH_RECIPE.PDF")

    # 3. Generate Cryptographic Manifest
    manifest_file = generate_manifest(USB_DIR)
    print(f"  [OK] Generated {manifest_file.name}")
    print(f"\n[export_usb_backup] SUCCESS: All USB backup deliverables generated and FAT32-verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
