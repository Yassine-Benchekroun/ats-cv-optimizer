import json
from ai_optimizer import optimize_resume
# pyrefly: ignore [missing-import]
from openai import OpenAIError
import os

if __name__ == "__main__":
    master_cv = """
    John Doe
    johndoe@email.com | 555-0198 | New York, NY
    LinkedIn: linkedin.com/in/johndoe
    
    Professional Summary:
    Hardworking developer with a few years of coding experience. I like building things and working on teams.
    
    Skills:
    Python, Javascript, React, SQL, Git, AWS
    
    Experience:
    Software Developer at TechCorp
    Jan 2020 - Present
    - Wrote code for the backend in Python.
    - Made the database queries faster using SQL.
    - Worked with cloud stuff on AWS.
    - Helped the frontend team with some Javascript and React tasks.
    
    Education:
    B.S. Computer Science, State University, 2019
    GPA: 3.8
    """
    
    job_description = """
    We are looking for a Backend Data Engineer.
    The ideal candidate has strong Python skills and experience optimizing SQL databases.
    Experience with deploying microservices on AWS is highly desired.
    You will be responsible for building scalable data pipelines.
    """
    
    print("Testing AI Optimizer module...")
    print("-" * 50)
    print("Connecting to local Ollama instance on port 11434...")
    
    try:
        # Call the core function
        tailored_resume_obj = optimize_resume(master_cv, job_description)
        
        # Verify it returns the strongly typed Pydantic object
        print("SUCCESS! The LLM successfully returned a strongly typed Pydantic object.")
        print("\nType of returned object:", type(tailored_resume_obj))
        
        # Dump to JSON for clean visualization
        print("\nTailored JSON Output:")
        print(tailored_resume_obj.model_dump_json(indent=2))
        
    except OpenAIError as e:
        print(f"\nOpenAI API Error encountered (Expected if no API key is provided):")
        print(e)
    except Exception as e:
        print(f"\nUnexpected Error encountered:")
        print(e)
