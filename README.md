# AI-Powered Resume & CV Tailor

An end-to-end application that automatically tailors a candidate's master CV/resume to match a target job description using a local LLM, then compiles an ATS-friendly PDF ready for immediate download.

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
 │  • Rewrites summary, selects matching skills, reframes       │
 │    bullet points (without inventing experiences)             │
 │  • Outputs: Validated TailoredResume JSON Data               │
 │                            │                                 │
 │                            ▼                                 │
 │  Step 3: PDF Generator Engine (pdf_generator.py)             │
 │  • Injects JSON data into resume_template.html (Jinja2)      │
 │  • Compiles HTML/CSS into standard ATS PDF (xhtml2pdf)       │
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
   - When the user clicks **"Tailor My Resume"**, the frontend sends both as a `multipart/form-data` request to the backend endpoint `/api/v1/tailor`.

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
     - **Fact Verification**: Strictly preserves the candidate's real history, preventing false claims or invented experiences.
   - Outputs a typed, schema-validated `TailoredResume` JSON containing: `contact_info`, `summary`, `skills`, `experience`, and `education`.

4. **ATS-Compliant Document Compilation (`pdf_generator.py`)**:
   - The structured JSON is merged with `resume_template.html` using **Jinja2**.
   - **xhtml2pdf** converts the rendered HTML/CSS into a standardized, single/multi-page, ATS-scannable PDF document.
   - The generated PDF binary is converted into a **Base64 string** and packaged into the JSON response.

5. **Delivery to User**:
   - The backend returns the JSON response containing the structured data and the Base64 PDF string.
   - The frontend decodes the Base64 data into raw PDF bytes and presents an interactive **"⬇️ Download Tailored PDF"** button directly to the user.

---

## 🌟 Key Features

- **Document Parsing**: Extracts clean text from master CVs in `.pdf` and `.docx` formats.
- **Local AI Optimization**: Rewrites summary, skills, and experience bullet points to match target job keywords using **Ollama** (`llama3.2`) with strictly enforced schemas via **Instructor** & **Pydantic**.
- **ATS-Friendly PDF Generation**: Renders structured data into a standardized layout via **Jinja2** and **xhtml2pdf**.
- **100% Local & Private**: Runs completely on your machine—no CV data is sent to external cloud APIs.
- **Streamlit Web Interface**: Fast UI to upload your file, paste job descriptions, preview extracted JSON, and download the tailored PDF.

---

## 🏗️ Architecture & Project Structure

```text
website1/
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
streamlit run app.py
```
- Web UI will open at: `http://localhost:8501`

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
