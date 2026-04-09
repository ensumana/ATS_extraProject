import streamlit as st
import os
import tempfile
import pandas as pd

from ats_backend import load_jd, set_skills, process_resume, results

# -------------------------------
# Page Config
# -------------------------------
st.set_page_config(page_title="ATS Resume Screener", layout="wide")

st.title("📄 ATS Resume Screener")

# -------------------------------
# Inputs
# -------------------------------
jd = st.text_area("📌 Enter Job Description", height=200)

skills = st.text_input("🛠️ Enter Skills (comma separated)")

uploaded_files = st.file_uploader(
    "📂 Upload Resumes (PDF/DOCX)",
    type=["pdf", "docx"],
    accept_multiple_files=True
)

# -------------------------------
# Process Button
# -------------------------------
if st.button("🚀 Process Resumes"):

    if not jd or not skills or not uploaded_files:
        st.warning("⚠️ Please fill all fields and upload resumes")
    else:
        load_jd(jd)
        set_skills(skills)

        results.clear()

        progress = st.progress(0)

        with tempfile.TemporaryDirectory() as temp_dir:
            for i, file in enumerate(uploaded_files):

                file_path = os.path.join(temp_dir, file.name)

                with open(file_path, "wb") as f:
                    f.write(file.read())

                process_resume(file_path)

                progress.progress((i + 1) / len(uploaded_files))

        df = pd.DataFrame(results)
        df.sort_values(by="Score", ascending=False, inplace=True)

        st.success("✅ Processing Complete")

        # -------------------------------
        # Top Candidates
        # -------------------------------
        st.subheader("🏆 Top Candidates")
        st.dataframe(df.head(5), use_container_width=True)

        # -------------------------------
        # Full Results
        # -------------------------------
        st.subheader("📊 All Results")
        st.dataframe(df, use_container_width=True)

        # -------------------------------
        # Download Button
        # -------------------------------
        st.download_button(
            "⬇️ Download Results",
            df.to_csv(index=False),
            "ATS_results.csv",
            mime="text/csv"
        )