import os
import re
import pdfplumber
import docx

def clean_text(text: str) -> str:
    """
    Cleans the extracted text by removing redundant whitespaces,
    resolving encoding bugs, and stripping non-printable characters.
    """
    if not text:
        return ""
    
    # Strip out non-printable text elements (excluding standard whitespace like \n, \t)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    
    # Replace multiple spaces/tabs with a single space
    text = re.sub(r'[ \t]+', ' ', text)
    
    # Replace multiple newlines with a single newline to condense layout
    text = re.sub(r'\n\s*\n', '\n', text)
    
    # Strip leading and trailing whitespace
    return text.strip()

def extract_text_from_file(file_path: str) -> dict:
    """
    Extracts and cleans text from PDF and DOCX files.
    
    Returns:
        dict: A dictionary matching the contract:
              {"success": bool, "extracted_text": str or None, "error": str or None}
    """
    result = {
        "success": False,
        "extracted_text": None,
        "error": None
    }
    
    if not os.path.exists(file_path):
        result["error"] = f"File not found: {file_path}"
        return result
        
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    if ext not in ['.pdf', '.docx']:
        result["error"] = f"Unsupported file extension '{ext}'. Only .pdf and .docx are supported."
        return result
        
    try:
        extracted_text = ""
        
        if ext == '.pdf':
            # Handle PDF extraction with layout preservation
            with pdfplumber.open(file_path) as pdf:
                pages_text = []
                for page in pdf.pages:
                    # layout=True maintains visual layout lines where possible
                    text = page.extract_text(layout=True)
                    if text:
                        pages_text.append(text)
                extracted_text = "\n".join(pages_text)
                
        elif ext == '.docx':
            # Handle Word Document extraction paragraph by paragraph
            doc = docx.Document(file_path)
            paragraphs_text = []
            for para in doc.paragraphs:
                if para.text.strip():
                    paragraphs_text.append(para.text)
            extracted_text = "\n".join(paragraphs_text)
            
        # Clean and sanitize the extracted text
        cleaned_text = clean_text(extracted_text)
        
        result["success"] = True
        result["extracted_text"] = cleaned_text
        
    except pdfplumber.pdfminer.pdfdocument.PDFPasswordIncorrect as e:
        result["error"] = "Failed to extract text: PDF is password protected."
    except Exception as e:
        result["error"] = f"Failed to extract text: {str(e)}"
        
    return result
