import os
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from pygments import highlight
from pygments.lexers import get_lexer_for_filename, TextLexer
from pygments.formatters import HtmlFormatter
from pygments.styles import get_style_by_name
from reportlab.lib.styles import StyleSheet1
from reportlab.platypus import Flowable
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import XPreformatted


EXCLUDE_DIRS = {".git", "__pycache__", "venv", ".venv", "node_modules", "build", "dist"}
SUPPORTED_EXTENSIONS = (".py", ".js", ".ts", ".go", ".java", ".cpp", ".c", ".json", ".yaml", ".yml", ".md")


def collect_code_files(directory):
    code_files = []
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

        for file in files:
            if file.endswith(SUPPORTED_EXTENSIONS):
                code_files.append(os.path.join(root, file))

    return sorted(code_files)


def highlight_code(code, filename):
    try:
        lexer = get_lexer_for_filename(filename)
    except:
        lexer = TextLexer()

    formatter = HtmlFormatter(style="monokai", noclasses=True)
    return highlight(code, lexer, formatter)


def strip_html_tags(text):
    import re
    clean = re.compile("<.*?>")
    return re.sub(clean, "", text)


def create_pdf_from_code(files, output_pdf):
    doc = SimpleDocTemplate(
        output_pdf,
        pagesize=A4,
        rightMargin=20,
        leftMargin=20,
        topMargin=20,
        bottomMargin=20,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        name="TitleStyle",
        fontName="Helvetica-Bold",
        fontSize=12,
        spaceAfter=8,
        alignment=TA_CENTER,
    )

    code_style = ParagraphStyle(
        name="CodeStyle",
        fontName="Courier",
        fontSize=7,
        leading=8,
        backColor=None,
    )

    elements = []

    for file in files:
        with open(file, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()

        elements.append(Paragraph(os.path.basename(file), title_style))

        highlighted = highlight_code(code, file)
        clean_code = strip_html_tags(highlighted)

        numbered_lines = "\n".join(
            f"{str(i+1).rjust(4)} | {line}"
            for i, line in enumerate(clean_code.splitlines())
        )

        elements.append(XPreformatted(numbered_lines, code_style))
        elements.append(PageBreak())

    doc.build(elements)


if __name__ == "__main__":
    project_dir = "./"
    output_pdf = "project_code_pro.pdf"

    code_files = collect_code_files(project_dir)

    print(f"Found {len(code_files)} files")
    create_pdf_from_code(code_files, output_pdf)

    print(f"PDF created: {output_pdf}")
