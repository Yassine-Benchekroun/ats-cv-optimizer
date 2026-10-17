# AI-Powered Resume & CV Tailor

An end-to-end local application that proposes a tailored CV from a master resume and job description, then generates a simple, text-based PDF for review and download.

---

## 📖 Complete End-to-End Workflow & Data Flow

This section details how the inputs enter the system, where they travel through each internal module, and how the final output is delivered back to the user.

```
 [User Browser (Streamlit)]
   ├── 1. Master CV (.pdf or .docx)
   └── 2. Job Description (Raw Text)
              │
              │  HTTP POST /api/v1/tailor (Multipart Form)
              ▼
 ┌──────────────────────────────────────────────────────────────┐
 │                    FastAPI Backend Orchestrator              │
 │                                                              │
 │  Step 1: Document Parser (document_parser.py)                │
 │  • Reads .pdf (via pdfplumber) or .docx (via python-docx)     │
 │  • Strips non-printable characters & cleans layout           │
 │  • Outputs: Raw Cleaned CV Text                              │
 │                            │                                 │
 │                            ▼                                 │
 │  Step 2: AI Optimizer Brain (ai_optimizer.py)                │
 │  • Inputs: Cleaned CV Text + Job Description                 │
 │  • Model: Local Ollama (llama3.2) via Instructor & Pydantic  │
 │  • Extracts & matches job keywords naturally                 │
 │  • Proposes a rewritten summary, skills, and bullet points   │
 │    for the user to verify against the original CV             │
 │  • Outputs: Validated TailoredResume JSON Data               │
 │                            │                                 │
 │                            ▼                                 │
 │  Step 3: PDF Generator Engine (pdf_generator.py)             │
 │  • Injects JSON data into resume_template.html (Jinja2)      │
 │  • Compiles HTML/CSS into a simple PDF (xhtml2pdf)            │
 │  • Encodes generated PDF bytes to Base64 string              │
 │                            │                                 │
 │                            ▼                                 │
 │  Step 4: API Response Delivery                               │
 │  • Sends JSON response back to Frontend:                     │
 │    { success: true, data: {...}, pdf_base64: "..." }         │
 └────────────────────────────┬─────────────────────────────────┘
                              │
                              │ JSON Response (Data + Base64 PDF)
                              ▼
 [User Browser (Streamlit)]
   • Decodes Base64 string back into binary PDF
   • Displays preview of the structured JSON data
   • Provides "Download Tailored PDF" button to save the file
```

### Detailed Stage Breakdown:

1. **User Input Collection (Frontend)**:
   - The user opens the Streamlit interface and supplies two inputs:
     - **Input A**: A master CV file (`.pdf` or `.docx`).
     - **Input B**: The job description pasted as plain text.
   - Both inputs are required. **"Tailor My Resume"** stays disabled until a CV is uploaded and the job description contains text. The app generates a draft only from the uploaded CV. The frontend then sends both as a `multipart/form-data` request to the backend endpoint `/api/v1/tailor`.

2. **File Ingestion & Parsing (`document_parser.py`)**:
   - The backend saves the uploaded file to a temporary location.
   - Depending on the file format:
     - `.pdf` files are parsed with `pdfplumber` to maintain reading order.
     - `.docx` files are parsed paragraph-by-paragraph using `python-docx`.
   - Text is sanitized by stripping unreadable characters, multiple blank lines, and encoding anomalies.

3. **AI Keyword Alignment & Optimization (`ai_optimizer.py`)**:
   - The cleaned text and job description are passed to **Ollama** running the `llama3.2` model locally via **Instructor**.
   - The LLM performs technical recruitment alignment:
     - **Keyword Alignment**: Detects key qualifications, tools, and technical competencies requested in the job post.
     - **Content Rewriting**: Rewrites experience bullet points and the summary to highlight matching skills and achievements.
     - **Truthfulness instruction**: Prompts the model to use only the candidate's CV. The application does not independently verify the model's claims, so the user must review every change.
   - Outputs a typed, schema-validated `TailoredResume` JSON containing: `contact_info`, `summary`, `skills`, `experience`, and `education`.

4. **PDF Compilation (`pdf_generator.py`)**:
   - The structured JSON is merged with `resume_template.html` using **Jinja2**.
   - **xhtml2pdf** converts the rendered HTML/CSS into a simple PDF. Compatibility with specific applicant tracking systems has not been tested.
   - The generated PDF binary is converted into a **Base64 string** and packaged into the JSON response.

5. **Delivery to User**:
   - The backend returns the JSON response containing the structured data and the Base64 PDF string.
   - The frontend decodes the Base64 data into raw PDF bytes and presents an interactive **"⬇️ Download Tailored PDF"** button directly to the user.

---

## 🌟 Key Features

- **Document Parsing**: Extracts clean text from master CVs in `.pdf` and `.docx` formats.
- **Local AI Optimization**: Proposes changes to the summary, skills, and experience bullet points using **Ollama** (`llama3.2`) with a typed output schema via **Instructor** & **Pydantic**. Review all factual claims before using the result.
- **Simple PDF Generation**: Renders structured data into a text-based layout via **Jinja2** and **xhtml2pdf**. ATS compatibility has not been measured.
- **Local Processing**: This code calls the Ollama server on your computer, not a cloud API. Keep the services bound to your own computer and review the privacy notes below.
- **Streamlit Web Interface**: Fast UI to upload your file, paste job descriptions, preview extracted JSON, and download the tailored PDF.

---

## 🏗️ Architecture & Project Structure

```text
ats-cv-optimizer/
├── backend/
│   ├── main.py                 # FastAPI server (orchestration endpoint /api/v1/tailor)
│   ├── document_parser.py      # PDF & DOCX text extraction and sanitation
│   ├── ai_optimizer.py         # Ollama LLM integration via Instructor & Pydantic
│   ├── pdf_generator.py        # Jinja2 + xhtml2pdf resume generation
│   ├── resume_template.html    # HTML/CSS template for the generated PDF
│   └── requirements.txt        # Backend Python dependencies
├── frontend/
│   ├── app.py                  # Streamlit web application
│   └── requirements.txt        # Frontend Python dependencies
└── README.md
```

---

## ⚙️ Prerequisites

1. **Python 3.10+**
2. **Ollama**: Installed and running locally.
   - Pull the model used by the backend:
     ```bash
     ollama run llama3.2
     ```
   - Ensure the Ollama server is accessible at `http://localhost:11434`.

---

## 🚀 Quickstart

### 1. Start the Backend

Open a terminal:

```bash
cd backend

# Create & activate a virtual environment (if not already done)
python -m venv venv
# Windows:
.\venv\Scripts\Activate.ps1
# macOS/Linux:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the backend API
python main.py
```
- API is live at: `http://localhost:8000`
- Interactive Swagger docs: `http://localhost:8000/docs`

---

### 2. Start the Frontend

Open a **separate** terminal:

```bash
cd frontend

# Create & activate a virtual environment (if not already done)
python -m venv venv
# Windows:
.\venv\Scripts\Activate.ps1
# macOS/Linux:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Launch Streamlit
streamlit run app.py --server.address 127.0.0.1 --server.maxUploadSize 10
```
- Web UI will open at: `http://localhost:8501`

---

## Tests

From `backend/`, install the optional test dependencies and run:

```bash
pip install -r requirements-dev.txt
python -m pytest -q test_api_safety.py test_pdf_template.py
```

The API tests replace Ollama and PDF conversion with local stubs. The PDF tests check HTML escaping and that generated PDF text can be extracted. An end-to-end test with the local Ollama model still requires a manual run.

---

## 📡 API Reference

### `POST /api/v1/tailor`
- **Content-Type**: `multipart/form-data`
- **Parameters**:
  - `file`: Master CV file (`.pdf` or `.docx`)
  - `job_description`: Plain text of target job posting
- **Response**:
  ```json
  {
    "success": true,
    "data": {
      "contact_info": { ... },
      "summary": "...",
      "skills": [ ... ],
      "experience": [ ... ],
      "education": [ ... ]
    },
    "pdf_base64": "<base64-encoded-pdf>",
    "filename": "tailored_master_resume.pdf"
  }
  ```

## Privacy and current limits

- The backend started with `python main.py` listens on `127.0.0.1:8000`; the Streamlit command above also binds to loopback. Do not expose either service to a network without adding authentication and stronger request limits.
- Uploaded CVs are limited to 10 MiB and job descriptions to 20,000 characters. These checks run after FastAPI/Starlette parses the multipart request, so some data may already have been spooled to temporary storage. A network-facing deployment needs an earlier body-size limit in its server or proxy.
- The backend uses a unique temporary directory per request and removes it after responding. The frontend clears its saved CV bytes and job text from session state after processing, though the displayed result and download remain in the active Streamlit session.
- The extracted CV text is truncated to 15,000 characters before model processing. PDF layouts and DOCX tables may not extract completely. Check the generated PDF against the original CV.
- The model is instructed to avoid invented facts, but there is no independent fact checker. A synthetic local smoke test produced an unsupported experience bullet, so treat every output as a draft and compare it with the original CV before use. The PDF layout has not been tested against applicant tracking systems.
