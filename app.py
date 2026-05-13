"""
ATS Resume Screener - No JD + Duplicate Detection
-------------------------------------------------
Run using:
    python -m streamlit run app.py

This version removes the Job Description input and ranks candidates using:
    - Required skill match
    - Experience match
    - Duplicate resume/candidate detection
"""

import os
import tempfile
from datetime import datetime

import pandas as pd
import streamlit as st

from ats_backend import (
    clear_results,
    get_results_dataframe,
    process_resume,
    results,
    set_min_required_experience,
    set_skills,
)

# -------------------------------------------------------------------
# Page configuration
# -------------------------------------------------------------------
st.set_page_config(
    page_title="ATS Resume Screener",
    page_icon="📄",
    layout="wide",
)

st.title("📄 ATS Resume Screener")
st.caption("Skill-based resume screening with duplicate candidate detection. No job description required.")

# -------------------------------------------------------------------
# Sidebar settings
# -------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Screening Settings")

    min_exp = st.number_input(
        "Minimum Required Experience (Years)",
        min_value=0.0,
        max_value=50.0,
        value=0.0,
        step=0.5,
        help="Used to calculate the experience score.",
    )

    top_n = st.slider(
        "Number of Top Candidates to Display",
        min_value=3,
        max_value=30,
        value=5,
        step=1,
    )

    show_duplicates = st.checkbox(
        "Show duplicate candidates in main table",
        value=True,
        help="If unchecked, duplicate candidates are shown only in the duplicate section.",
    )

    st.info("Run using: python -m streamlit run app.py")

# -------------------------------------------------------------------
# Main inputs
# -------------------------------------------------------------------
skills = st.text_area(
    "🛠️ Enter Required Skills",
    height=160,
    placeholder="Example: Python, Django, SQL, Machine Learning, NLP",
)

uploaded_files = st.file_uploader(
    "📂 Upload Resumes (PDF/DOCX)",
    type=["pdf", "docx"],
    accept_multiple_files=True,
)

# -------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------
def validate_inputs(skills_text, files):
    if not skills_text.strip():
        return False, "Please enter at least one required skill."
    if not files:
        return False, "Please upload at least one resume."
    return True, ""


def safe_sort_results(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    if "Score" in df.columns:
        return df.sort_values(by="Score", ascending=False)
    return df


def split_duplicates(df: pd.DataFrame):
    if df.empty or "Duplicate Status" not in df.columns:
        return df, pd.DataFrame()

    duplicate_mask = df["Duplicate Status"].astype(str).str.lower().eq("candidate exists")
    duplicate_df = df[duplicate_mask].copy()
    unique_df = df[~duplicate_mask].copy()
    return unique_df, duplicate_df

# -------------------------------------------------------------------
# Process button
# -------------------------------------------------------------------
if st.button("🚀 Process Resumes", type="primary", use_container_width=True):
    is_valid, message = validate_inputs(skills, uploaded_files)

    if not is_valid:
        st.warning(f"⚠️ {message}")
    else:
        try:
            set_skills(skills)
            set_min_required_experience(min_exp)
            clear_results()

            progress = st.progress(0)
            status_box = st.empty()

            with tempfile.TemporaryDirectory() as temp_dir:
                total_files = len(uploaded_files)

                for i, uploaded_file in enumerate(uploaded_files):
                    file_path = os.path.join(temp_dir, uploaded_file.name)

                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                    status_box.info(f"Processing: {uploaded_file.name}")
                    process_resume(file_path)
                    progress.progress((i + 1) / total_files)

            df = get_results_dataframe()
            df = safe_sort_results(df)

            if df.empty:
                st.error("No results were generated. Please check the uploaded files.")
            else:
                unique_df, duplicate_df = split_duplicates(df)
                display_df = df if show_duplicates else unique_df

                st.success("✅ Processing complete")

                metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

                with metric_col1:
                    st.metric("Uploaded Resumes", len(df))

                with metric_col2:
                    st.metric("Unique Candidates", len(unique_df))

                with metric_col3:
                    st.metric("Duplicates Found", len(duplicate_df))

                with metric_col4:
                    avg_score = round(float(unique_df["Score"].mean()), 2) if not unique_df.empty and "Score" in unique_df.columns else 0
                    st.metric("Average Unique Score", avg_score)

                if not duplicate_df.empty:
                    st.warning("⚠️ Duplicate candidates found. These resumes already exist in the uploaded list.")
                    st.subheader("🔁 Duplicate Candidates")
                    st.dataframe(duplicate_df, use_container_width=True)

                st.subheader("🏆 Top Candidates")
                st.dataframe(unique_df.head(top_n), use_container_width=True)

                st.subheader("📊 All Results")
                st.dataframe(display_df, use_container_width=True)

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

                csv_data = df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "⬇️ Download Full CSV Results",
                    data=csv_data,
                    file_name=f"ATS_results_{timestamp}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

                unique_csv_data = unique_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "⬇️ Download Unique Candidates CSV",
                    data=unique_csv_data,
                    file_name=f"ATS_unique_candidates_{timestamp}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

                excel_path = os.path.join(tempfile.gettempdir(), f"ATS_results_{timestamp}.xlsx")
                with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
                    df.to_excel(writer, sheet_name="All Results", index=False)
                    unique_df.to_excel(writer, sheet_name="Unique Candidates", index=False)
                    duplicate_df.to_excel(writer, sheet_name="Duplicates", index=False)

                with open(excel_path, "rb") as f:
                    st.download_button(
                        "⬇️ Download Excel Report",
                        data=f,
                        file_name=f"ATS_results_{timestamp}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                    )

        except Exception as exc:
            st.error("❌ Processing failed.")
            st.exception(exc)

# -------------------------------------------------------------------
# Usage note
# -------------------------------------------------------------------
with st.expander("ℹ️ How this version works"):
    st.write("This version does not use a job description. It ranks resumes using required skills and experience.")
    st.write("Duplicate detection checks email, phone number, resume content, and candidate name fallback.")
    st.code("python -m streamlit run app.py", language="bash")
