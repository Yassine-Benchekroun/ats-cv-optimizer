"""Check that model text cannot become HTML markup in the generated PDF."""

from types import SimpleNamespace

import pdfplumber
import pdf_generator


def test_pdf_template_escapes_resume_markup(monkeypatch, tmp_path):
    rendered = []

    def fake_create_pdf(html, dest):
        rendered.append(html)
        dest.write(b"%PDF-1.4 test")
        return SimpleNamespace(err=0)

    monkeypatch.setattr(pdf_generator.pisa, "CreatePDF", fake_create_pdf)
    monkeypatch.chdir(tmp_path)
    data = {
        "contact_info": {"name": "Test User", "email": "test@example.com"},
        "summary": "<script>untrusted</script>",
        "skills": ["Python"],
        "experience": [],
        "education": [],
    }
    pdf_generator.generate_pdf_from_dict(data, str(tmp_path / "output.pdf"))
    assert "&lt;script&gt;untrusted&lt;/script&gt;" in rendered[0]
    assert "<script>untrusted</script>" not in rendered[0]


def test_generated_pdf_has_extractable_text(tmp_path):
    output_path = tmp_path / "resume.pdf"
    data = {
        "contact_info": {"name": "Test User", "email": "test@example.com"},
        "summary": "Builds reliable Python services.",
        "skills": ["Python", "FastAPI"],
        "experience": [],
        "education": [],
    }
    pdf_generator.generate_pdf_from_dict(data, str(output_path))
    with pdfplumber.open(output_path) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    assert "Test User" in text
    assert "Builds reliable Python services." in text
