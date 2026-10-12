import os
from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa

def generate_pdf_from_dict(resume_data: dict, output_path: str = "tailored_resume.pdf", template_name: str = "resume_template.html"):
    """
    Renders structured JSON/dict into an ATS-friendly PDF using xhtml2pdf.
    """
    # Setup Jinja2 environment to load templates from the current directory
    env = Environment(loader=FileSystemLoader(searchpath="."))
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

if __name__ == "__main__":
    # Dummy dictionary matching the exact data structure produced by Module 3's schema
    dummy_resume_data = {
        "contact_info": {
            "name": "Alex Mercer",
            "email": "alex.mercer@example.com",
            "phone": "(555) 019-8273",
            "location": "San Francisco, CA",
            "linkedin_url": "linkedin.com/in/alexmercer"
        },
        "summary": "Results-oriented Backend Engineer with over 6 years of experience designing scalable microservices and robust API architectures. Proven ability to optimize database performance, streamline deployment pipelines using AWS, and collaborate effectively across cross-functional teams.",
        "skills": [
            "Python", "FastAPI", "SQL", "PostgreSQL", "Docker", "AWS", "Git", "CI/CD", "Jinja2"
        ],
        "experience": [
            {
                "company": "Tech Innovations Inc.",
                "role": "Senior Backend Developer",
                "duration": "Jan 2021 - Present",
                "optimized_bullet_points": [
                    "Architected and deployed scalable REST APIs using Python and FastAPI, handling 10k+ requests per minute.",
                    "Optimized PostgreSQL database queries, reducing average response time by 40%.",
                    "Automated infrastructure deployment on AWS using Docker and CI/CD pipelines, increasing release velocity."
                ]
            },
            {
                "company": "DataFlow Systems",
                "role": "Software Engineer",
                "duration": "Jun 2017 - Dec 2020",
                "optimized_bullet_points": [
                    "Developed and maintained legacy monolithic systems using Python and Django.",
                    "Collaborated with data science teams to integrate machine learning models into production environments.",
                    "Mentored junior developers and led code reviews to ensure high code quality."
                ]
            }
        ],
        "education": [
            {
                "institution": "University of Technology",
                "degree": "B.S. in Computer Science",
                "graduation_date": "May 2017",
                "details": [
                    "Graduated Magna Cum Laude",
                    "Dean's List: 2015 - 2017"
                ]
            }
        ]
    }
    
    print("Generating PDF from dummy data...")
    output_file = generate_pdf_from_dict(dummy_resume_data)
    print(f"Success! PDF generated at: {output_file}")
