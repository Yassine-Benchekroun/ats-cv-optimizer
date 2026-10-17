from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from xhtml2pdf import pisa

def generate_pdf_from_dict(resume_data: dict, output_path: str = "tailored_resume.pdf", template_name: str = "resume_template.html"):
    """
    Renders structured JSON/dict into a simple text-based PDF using xhtml2pdf.
    """
    # Resume text is untrusted input, even after rewriting by a local model.
    env = Environment(
        loader=FileSystemLoader(searchpath=str(Path(__file__).resolve().parent)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template(template_name)
    
    # Render HTML with data
    rendered_html = template.render(**resume_data)
    
    # Convert HTML to PDF using xhtml2pdf
    with open(output_path, "wb") as result_file:
        pisa_status = pisa.CreatePDF(
            rendered_html, dest=result_file
        )
    
    if pisa_status.err:
        raise Exception("Error generating PDF using xhtml2pdf")
        
    return output_path
