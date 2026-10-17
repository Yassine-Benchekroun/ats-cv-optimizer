import os
import re
import tempfile
import base64
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from fastapi.concurrency import run_in_threadpool

# Import real modules
from document_parser import extract_text_from_file
from ai_optimizer import optimize_resume
from pdf_generator import generate_pdf_from_dict

app = FastAPI(title="AI-Powered Resume & CV Tailor API", version="1.0.0")

# This application handles personal CV data. Keep the development API on loopback.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=False,
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_JOB_DESCRIPTION_CHARS = 20_000
MAX_CV_CHARS = 15_000
COPY_CHUNK_BYTES = 1024 * 1024


def safe_download_filename(uploaded_name: str) -> str:
    """Build a PDF name without retaining path separators or the input extension."""
    leaf = uploaded_name.replace("\\", "/").split("/")[-1]
    stem = leaf.rsplit(".", 1)[0] if "." in leaf else leaf
    safe_stem = re.sub(r"[^A-Za-z0-9._-]+", "_", stem).strip("._-")[:64]
    return f"tailored_{safe_stem or 'resume'}.pdf"


def copy_upload_limited(source, destination_path: str) -> None:
    """Copy an already parsed multipart file while enforcing the file cap."""
    size = 0
    with open(destination_path, "wb") as destination:
        while chunk := source.read(COPY_CHUNK_BYTES):
            size += len(chunk)
            if size > MAX_UPLOAD_BYTES:
                raise HTTPException(status_code=413, detail="CV file exceeds the 10 MiB limit.")
            destination.write(chunk)

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
            "error": "Internal server error. Check the local server logs."
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
    # The name comes from the multipart request. Use it only for validation and
    # a sanitized download label, never as a path on the server.
    uploaded_name = (file.filename or "").replace("\\", "/").split("/")[-1]
    _, ext = os.path.splitext(uploaded_name)
    if ext.lower() not in (".pdf", ".docx"):
        raise HTTPException(status_code=400, detail="Only .pdf and .docx files are supported.")
    if not job_description.strip():
        raise HTTPException(status_code=400, detail="A job description is required.")
    if len(job_description) > MAX_JOB_DESCRIPTION_CHARS:
        raise HTTPException(status_code=413, detail="Job description exceeds the 20,000 character limit.")

    # A private directory per request prevents collisions between CVs with the
    # same uploaded name. It is removed on both success and error.
    with tempfile.TemporaryDirectory(prefix="ats_cv_") as temp_dir:
        temp_file_path = os.path.join(temp_dir, f"master{ext.lower()}")
        output_pdf_path = os.path.join(temp_dir, "tailored_resume.pdf")
        await run_in_threadpool(copy_upload_limited, file.file, temp_file_path)

        # Step 2: Extract text (Module 2)
        # Using run_in_threadpool since it's a blocking IO operation
        parser_result = await run_in_threadpool(extract_text_from_file, temp_file_path)
        
        if not parser_result.get("success"):
            raise HTTPException(status_code=400, detail="Could not parse the uploaded document.")
            
        raw_cv_text = parser_result.get("extracted_text")
        if not raw_cv_text or len(raw_cv_text.strip()) < 50:
            raise HTTPException(
                status_code=400,
                detail="Could not extract readable text from the uploaded file. This usually means the PDF is image-based (a scanned document). Please upload a text-selectable PDF or a DOCX file instead."
            )
        
        # Truncate text to 15,000 characters to prevent context window overflow on local AI models
        if len(raw_cv_text) > MAX_CV_CHARS:
            raw_cv_text = raw_cv_text[:MAX_CV_CHARS]
            
        # Step 3: Optimize using AI (Module 3)
        # LLM calls are blocking, so we run them in a threadpool
        try:
            tailored_resume_obj = await run_in_threadpool(optimize_resume, raw_cv_text, job_description)
        except Exception:
            raise HTTPException(
                status_code=422,
                detail="The local AI could not format the resume. Check Ollama and try again."
            )
        
        # Convert Pydantic object to dictionary
        structured_resume_data = tailored_resume_obj.model_dump()
        
        # Step 4: Generate physical PDF (Module 4)
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
                "filename": safe_download_filename(uploaded_name)
            }
        )

if __name__ == "__main__":
    print("Starting API Orchestration Server...")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
