import streamlit as st
import requests
import base64

API_URL = "http://localhost:8000/api/v1/tailor"

def main():
    st.set_page_config(page_title="AI-Powered Resume & CV Tailor", page_icon="📄", layout="wide")

    # Initialize session state variables
    if "is_processing" not in st.session_state:
        st.session_state.is_processing = False
    if "saved_file" not in st.session_state:
        st.session_state.saved_file = None
    if "saved_job_description" not in st.session_state:
        st.session_state.saved_job_description = ""

    st.title("AI-Powered Resume & CV Tailor")
    st.write("Upload your master CV and a job description to automatically tailor your resume.")

    # ------- INPUTS (disabled while AI is processing) -------
    st.header("1. Upload Master CV")
    uploaded_file = st.file_uploader(
        "Upload your CV (PDF or DOCX)",
        type=["pdf", "docx"],
        disabled=st.session_state.is_processing
    )

    st.header("2. Job Description")
    job_description = st.text_area(
        "Paste the specific Job Description here:",
        height=200,
        disabled=st.session_state.is_processing
    )

    # Show a locked status banner while processing
    if st.session_state.is_processing:
        st.info("⏳ AI is tailoring your resume... Inputs are locked. Please wait.")

    # ------- SUBMIT BUTTON -------
    if st.button(
        "Tailor My Resume",
        type="primary",
        disabled=st.session_state.is_processing
    ):
        if uploaded_file is None:
            st.error("Please upload a master CV.")
        elif not job_description.strip():
            st.error("Please provide a job description.")
        else:
            # Save inputs to session state BEFORE rerunning
            # so they survive the rerun even when the widgets are disabled
            st.session_state.saved_file = {
                "name": uploaded_file.name,
                "bytes": uploaded_file.getvalue(),
                "type": uploaded_file.type
            }
            st.session_state.saved_job_description = job_description
            st.session_state.is_processing = True
            st.rerun()

    # ------- API CALL (runs after rerun, reads from session_state) -------
    if st.session_state.is_processing and st.session_state.saved_file is not None:
        with st.spinner("🤖 AI is analyzing your CV and rewriting it for the job description..."):
            try:
                saved_file = st.session_state.saved_file
                files = {"file": (saved_file["name"], saved_file["bytes"], saved_file["type"])}
                data = {"job_description": st.session_state.saved_job_description}

                response = requests.post(API_URL, files=files, data=data, timeout=300)

                if response.status_code == 200:
                    result_json = response.json()
                    if result_json.get("success"):
                        st.success("✅ Resume tailored successfully!")
                        st.divider()

                        st.header("Results")
                        col1, col2 = st.columns(2)

                        structured_data = result_json.get("data", {})
                        pdf_base64 = result_json.get("pdf_base64", "")
                        filename = result_json.get("filename", "tailored_resume.pdf")

                        with col1:
                            st.subheader("Original Inputs")
                            st.write(f"**File Name:** {saved_file['name']}")
                            st.write("**Job Description Snippet:**")
                            snippet = st.session_state.saved_job_description[:200] + "..." if len(st.session_state.saved_job_description) > 200 else st.session_state.saved_job_description
                            st.info(snippet)

                        with col2:
                            st.subheader("Tailored Resume Structure")
                            st.json(structured_data)

                            if pdf_base64:
                                pdf_bytes = base64.b64decode(pdf_base64)
                                st.download_button(
                                    label="⬇️ Download Tailored PDF",
                                    data=pdf_bytes,
                                    file_name=filename,
                                    mime="application/pdf",
                                    type="secondary"
                                )
                    else:
                        st.error(f"Error from backend: {result_json.get('error')}")
                elif response.status_code == 400:
                    error_detail = response.json().get('detail', 'Invalid file.')
                    st.error(f"⚠️ File Error: {error_detail}")
                elif response.status_code == 422:
                    error_detail = response.json().get('detail', 'AI processing failed.')
                    st.warning(f"🤖 AI Error: {error_detail}")
                else:
                    st.error(f"Server Error (Status Code {response.status_code}): {response.text}")

            except requests.exceptions.Timeout:
                st.warning("⏱️ The request timed out. Your local AI is taking too long. Try using a shorter CV or job description, then click 'Tailor My Resume' again.")
            except requests.exceptions.ConnectionError:
                st.error("🔌 Failed to connect to the backend server. Please make sure `main.py` is running on port 8000.")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
            finally:
                # Always unlock the inputs when done (success or failure)
                st.session_state.is_processing = False

if __name__ == "__main__":
    main()
