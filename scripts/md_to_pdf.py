"""Convert NEOS.md to a presentation-quality PDF via markdown → HTML → Chrome headless."""

import markdown
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MD_PATH = ROOT / "NEOS.md"
PDF_PATH = ROOT / "NEOS.pdf"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

# Read markdown source
md_text = MD_PATH.read_text(encoding="utf-8")

# Convert markdown to HTML
html_body = markdown.markdown(
    md_text,
    extensions=["tables", "fenced_code", "toc", "smarty"],
)

# Wrap in a full HTML document with presentation-quality CSS
html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>NEOS — New Earth Operating System</title>
<style>
  @page {{
    size: A4;
    margin: 2.2cm 2cm 2.5cm 2cm;
  }}

  body {{
    font-family: "Segoe UI", Helvetica, Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.65;
    color: #1a1a1a;
    max-width: 100%;
    margin: 0;
    padding: 0;
  }}

  h1 {{
    font-size: 26pt;
    font-weight: 700;
    color: #0d3b2e;
    border-bottom: 3px solid #0d3b2e;
    padding-bottom: 12px;
    margin-top: 0;
    margin-bottom: 24px;
  }}

  h2 {{
    font-size: 17pt;
    font-weight: 600;
    color: #14614d;
    border-bottom: 1.5px solid #c8ddd7;
    padding-bottom: 6px;
    margin-top: 36px;
    margin-bottom: 16px;
    page-break-after: avoid;
  }}

  h3 {{
    font-size: 12.5pt;
    font-weight: 600;
    color: #1a7a5e;
    margin-top: 22px;
    margin-bottom: 8px;
    page-break-after: avoid;
  }}

  p {{
    margin-bottom: 10px;
    text-align: justify;
    orphans: 3;
    widows: 3;
  }}

  strong {{
    color: #0d3b2e;
  }}

  code {{
    font-family: "Cascadia Code", "Consolas", "Courier New", monospace;
    font-size: 9.5pt;
    background: #f0f5f3;
    padding: 1px 5px;
    border-radius: 3px;
    color: #14614d;
  }}

  pre {{
    background: #f5f8f7;
    border: 1px solid #d4e0dc;
    border-radius: 6px;
    padding: 14px 18px;
    font-size: 9pt;
    line-height: 1.5;
    overflow-x: auto;
    page-break-inside: avoid;
  }}

  pre code {{
    background: none;
    padding: 0;
    font-size: 9pt;
  }}

  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 16px 0;
    font-size: 10pt;
    page-break-inside: avoid;
  }}

  th {{
    background: #0d3b2e;
    color: white;
    font-weight: 600;
    text-align: left;
    padding: 10px 12px;
    border: 1px solid #0d3b2e;
  }}

  td {{
    padding: 8px 12px;
    border: 1px solid #d4e0dc;
    vertical-align: top;
  }}

  tr:nth-child(even) td {{
    background: #f5f8f7;
  }}

  ul, ol {{
    margin-bottom: 10px;
    padding-left: 24px;
  }}

  li {{
    margin-bottom: 5px;
  }}

  hr {{
    border: none;
    border-top: 2px solid #c8ddd7;
    margin: 32px 0;
  }}

  em {{
    color: #555;
  }}

  /* First paragraph after h1 — subtitle style */
  h1 + p {{
    font-size: 12pt;
    color: #444;
    line-height: 1.7;
  }}
</style>
</head>
<body>
{html_body}
</body>
</html>
"""

# Write HTML to a temp file, then use Chrome headless to produce PDF
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_doc)
    html_path = f.name

try:
    result = subprocess.run(
        [
            CHROME,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            "--disable-extensions",
            f"--print-to-pdf={PDF_PATH}",
            "--print-to-pdf-no-header",
            html_path,
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode == 0:
        print(f"PDF written to: {PDF_PATH}")
    else:
        print(f"Chrome stderr: {result.stderr}")
        print(f"Chrome stdout: {result.stdout}")
        raise RuntimeError("Chrome PDF generation failed")
finally:
    Path(html_path).unlink(missing_ok=True)
