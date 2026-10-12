import os
import shutil
import tempfile
import base64
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
from fastapi.concurrency import run_in_threadpool

# Import real modules
from document_parser import extract_text_from_file
from ai_optimizer import optimize_resume
from pdf_generator import generate_pdf_from_dict

app = FastAPI(title="AI-Powered Resume & CV Tailor API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# GLOBAL EXCEPTION HANDLER
# ---------------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catches any unhandled exceptions during the workflow and returns an elegant JSON error.
    """
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal Server Error",
            "details": str(exc)
        },
    )

# ---------------------------------------------------------
# CENTRAL ORCHESTRATION ENDPOINT
# ---------------------------------------------------------
@app.post("/api/v1/tailor")
async def tailor_resume(
    file: UploadFile = File(..., description="The master CV file (.pdf or .docx)"),
    job_description: str = Form(..., description="The target job description text")
):
    """
    The main orchestration workflow:
    1. Save incoming file temporarily.
    2. Pass to Document Parser (Module 2).
    3. Pass text + job description to AI Optimizer (Module 3).
    4. Compile tailored data into PDF (Module 4).
    5. Return JSON containing the data and a Base64 encoded PDF.
    """
    temp_file_path = None
    output_pdf_path = None
    
    try:
        # Step 1: Save the incoming file temporarily
        _, ext = os.path.splitext(file.filename)
        if ext.lower() not in ['.pdf', '.docx']:
            raise HTTPException(status_code=400, detail="Only .pdf and .docx files are supported.")
            
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_file_path = temp_file.name
            
        # Step 2: Extract text (Module 2)
        # Using run_in_threadpool since it's a blocking IO operation
        parser_result = await run_in_threadpool(extract_text_from_file, temp_file_path)
        
        if not parser_result.get("success"):
            raise HTTPException(status_code=400, detail=f"Parsing Failed: {parser_result.get('error')}")
            
        raw_cv_text = parser_result.get("extracted_text")
        if not raw_cv_text or len(raw_cv_text.strip()) < 50:
            raise HTTPException(
                status_code=400,
                detail="Could not extract readable text from the uploaded file. This usually means the PDF is image-based (a scanned document). Please upload a text-selectable PDF or a DOCX file instead."
            )
        
        # Truncate text to 15,000 characters to prevent context window overflow on local AI models
        MAX_CHARS = 15000
        if len(raw_cv_text) > MAX_CHARS:
            raw_cv_text = raw_cv_text[:MAX_CHARS]
            
        # Step 3: Optimize using AI (Module 3)
        # LLM calls are blocking, so we run them in a threadpool
        try:
            tailored_resume_obj = await run_in_threadpool(optimize_resume, raw_cv_text, job_description)
        except Exception as ai_error:
            raise HTTPException(
                status_code=422,
                detail=f"The AI failed to format the resume correctly after multiple retries. Please click 'Tailor My Resume' to try again. (Details: {str(ai_error)})"
            )
        
        # Convert Pydantic object to dictionary
        structured_resume_data = tailored_resume_obj.model_dump()
        
        # Step 4: Generate physical PDF (Module 4)
        output_pdf_path = os.path.join(tempfile.gettempdir(), f"tailored_{file.filename}.pdf")
        await run_in_threadpool(generate_pdf_from_dict, structured_resume_data, output_pdf_path)
        
        # Step 5: Read PDF and encode to Base64
        with open(output_pdf_path, "rb") as pdf_file:
            pdf_bytes = pdf_file.read()
            pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
        
        # Step 6: Return the structured data AND the encoded PDF file
        return JSONResponse(
            content={
                "success": True,
                "data": structured_resume_data,
                "pdf_base64": pdf_base64,
                "filename": f"tailored_{file.filename}.pdf"
            }
        )
        
    finally:
        # Cleanup: Remove temporary files
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        if output_pdf_path and os.path.exists(output_pdf_path):
            os.remove(output_pdf_path)

if __name__ == "__main__":
    print("Starting API Orchestration Server...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
