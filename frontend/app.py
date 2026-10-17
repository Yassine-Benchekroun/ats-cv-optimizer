import streamlit as st
import requests
import base64

API_URL = "http://localhost:8000/api/v1/tailor"


def clear_previous_result():
    """Do not show an earlier draft after either required input changes."""
    st.session_state.latest_result = None
    st.session_state.latest_notice = None


def main():
    st.set_page_config(page_title="AI-Powered Resume & CV Tailor", page_icon="📄", layout="wide")

    # Initialize session state variables
    if "is_processing" not in st.session_state:
        st.session_state.is_processing = False
    if "saved_file" not in st.session_state:
        st.session_state.saved_file = None
    if "saved_job_description" not in st.session_state:
        st.session_state.saved_job_description = ""
    if "latest_result" not in st.session_state:
        st.session_state.latest_result = None
    if "latest_notice" not in st.session_state:
        st.session_state.latest_notice = None

    st.title("AI-Powered Resume & CV Tailor")
    st.write("Upload your master CV and a job description to automatically tailor your resume.")

    # ------- INPUTS (disabled while AI is processing) -------
    st.header("1. Upload Master CV (required)")
    uploaded_file = st.file_uploader(
        "Upload your CV (PDF or DOCX)",
        type=["pdf", "docx"],
        disabled=st.session_state.is_processing,
        on_change=clear_previous_result,
    )

    st.header("2. Job Description (required)")
    job_description = st.text_area(
        "Paste the specific Job Description here:",
        height=200,
        disabled=st.session_state.is_processing,
        on_change=clear_previous_result,
    )

    # Show a locked status banner while processing
    if st.session_state.is_processing:
        st.info("⏳ AI is tailoring your resume... Inputs are locked. Please wait.")

    # Streamlit reruns after either input changes, so the button becomes
    # available only when both required inputs are present.
    has_required_inputs = uploaded_file is not None and bool(job_description.strip())
    if not has_required_inputs and not st.session_state.is_processing:
        st.caption("Upload a CV and enter a job description to enable generation.")

    # ------- SUBMIT BUTTON -------
    if st.button(
        "Tailor My Resume",
        type="primary",
        disabled=st.session_state.is_processing or not has_required_inputs
    ):
        if uploaded_file is None:
            st.error("Please upload a master CV.")
        elif not job_description.strip():
            st.error("Please provide a job description.")
        else:
            # Save inputs to session state BEFORE rerunning
            # so they survive the rerun even when the widgets are disabled
            st.session_state.latest_result = None
            st.session_state.latest_notice = None
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
                        st.session_state.latest_result = {
                            "response": result_json,
                            "source_name": saved_file["name"],
                            "job_description": st.session_state.saved_job_description,
                        }
                    else:
                        st.session_state.latest_notice = ("error", f"Error from backend: {result_json.get('error')}")
                elif response.status_code == 400:
                    error_detail = response.json().get('detail', 'Invalid file.')
                    st.session_state.latest_notice = ("error", f"⚠️ File Error: {error_detail}")
                elif response.status_code == 422:
                    error_detail = response.json().get('detail', 'AI processing failed.')
                    st.session_state.latest_notice = ("warning", f"🤖 AI Error: {error_detail}")
                else:
                    st.session_state.latest_notice = ("error", f"Local server error (status {response.status_code}). Check the backend console.")

            except requests.exceptions.Timeout:
                st.session_state.latest_notice = ("warning", "⏱️ The request timed out. Your local AI is taking too long. Try using a shorter CV or job description, then click 'Tailor My Resume' again.")
            except requests.exceptions.ConnectionError:
                st.session_state.latest_notice = ("error", "🔌 Failed to connect to the backend server. Please make sure `main.py` is running on port 8000.")
            except Exception:
                st.session_state.latest_notice = ("error", "An unexpected local error occurred. Check the backend console and try again.")
            finally:
                # Release the uploaded CV and job text from session state after use.
                st.session_state.saved_file = None
                st.session_state.saved_job_description = ""
                st.session_state.is_processing = False

        # Redraw the controls with the processing lock released, keeping the
        # result (or error) visible in session state.
        st.rerun()

    if st.session_state.latest_notice is not None:
        level, message = st.session_state.latest_notice
        if level == "warning":
            st.warning(message)
        else:
            st.error(message)

    if st.session_state.latest_result is not None:
        latest = st.session_state.latest_result
        result_json = latest["response"]
        st.success("✅ Resume draft generated. Review it before use.")
        st.divider()
        st.header("Results")
        st.warning(
            "AI-generated draft: verify every name, date, skill, "
            "accomplishment, and experience bullet against your "
            "original CV before downloading or submitting."
        )
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Original Inputs")
            st.write(f"**File Name:** {latest['source_name']}")
            st.write("**Job Description Snippet:**")
            description = latest["job_description"]
            snippet = description[:200] + "..." if len(description) > 200 else description
            st.info(snippet)

        with col2:
            st.subheader("Tailored Resume Structure")
            st.json(result_json.get("data", {}))

            pdf_base64 = result_json.get("pdf_base64", "")
            if pdf_base64:
                st.download_button(
                    label="⬇️ Download Draft PDF",
                    data=base64.b64decode(pdf_base64),
                    file_name=result_json.get("filename", "tailored_resume.pdf"),
                    mime="application/pdf",
                    type="secondary",
                )

if __name__ == "__main__":
    main()
