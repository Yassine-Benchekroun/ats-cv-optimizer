import os
import instructor
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import List, Optional

class ContactInfo(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None

class Education(BaseModel):
    institution: str
    degree: str
    graduation_date: Optional[str] = None
    details: Optional[List[str]] = Field(default_factory=list, description="Any honors, GPA, or extra details")

class WorkExperience(BaseModel):
    company: str
    role: str
    duration: str
    optimized_bullet_points: List[str] = Field(
        ..., 
        description="Rewrite the candidate's bullet points to match the job description keywords while maintaining truthfulness. DO NOT invent experiences."
    )

class TailoredResume(BaseModel):
    contact_info: ContactInfo
    summary: str = Field(..., description="A professional summary tailored to highlight the most relevant skills for the target job description.")
    skills: List[str] = Field(..., description="A list of relevant skills possessed by the candidate that match the job description.")
    experience: List[WorkExperience]
    education: List[Education]

def optimize_resume(master_cv_text: str, job_description: str) -> TailoredResume:
    """
    Core optimization brain that aligns a raw resume with a job description.
    Uses Instructor to guarantee the LLM returns a strongly typed Pydantic model.
    """
    # Initialize the instructor-patched OpenAI client to use a LOCAL AI (like Ollama)
    # This bypasses the OpenAI API entirely and runs on your machine.
    client = instructor.from_openai(
        OpenAI(
            base_url="http://localhost:11434/v1",
            api_key="ollama",  # required, but unused
        ),
        mode=instructor.Mode.JSON,
    )
    
    system_prompt = """
    You are an expert technical recruiter and ATS (Applicant Tracking System) optimization specialist. 
    Your job is to tailor a candidate's master CV to perfectly align with a target job description.
    
    CRITICAL RULES:
    1. Highlight matching keywords from the job description and incorporate them naturally into the resume.
    2. Rewrite and optimize bullet points for maximum impact, focusing on relevant achievements.
    3. DO NOT create fake job experiences, fake dates, fake credentials, or list skills the candidate clearly does not have.
    4. Maintain strict truthfulness based ONLY on the provided master CV.
    5. Return the exact structured JSON mapping to the requested schema. DO NOT wrap the JSON in an outer key like "TailoredResume". The root of the JSON must contain the keys "contact_info", "summary", "skills", "experience", and "education".
    """
    
    user_prompt = f"""
    TARGET JOB DESCRIPTION:
    {job_description}
    
    MASTER CV TEXT:
    {master_cv_text}
    """
    
    response = client.chat.completions.create(
        model="llama3.2",  # Changed to a local Ollama model
        response_model=TailoredResume,
        max_retries=3,  # Auto-retry up to 3 times if AI outputs invalid JSON
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.2, # Lower temperature to enforce deterministic, factual rewriting
    )
    
    return response
