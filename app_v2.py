import streamlit as st
from datetime import datetime
import os

from outlook_engine import download_resumes
from ats_parser import process_resumes

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="ATS Resume Categorization System",
    page_icon="📄",
    layout="wide"
)

st.title("📄 ATS Resume Categorization System")

st.markdown("---")

# --------------------------------------------------
# FOLDER SELECTION
# --------------------------------------------------
folder_path = st.text_input(
    "Resume Download Folder",
    value=os.path.join(os.getcwd(), "Downloads")
)

col1, col2 = st.columns(2)

with col1:
    from_date = st.date_input(
        "From Date",
        value=datetime.today()
    )

with col2:
    to_date = st.date_input(
        "To Date",
        value=datetime.today()
    )

st.markdown("---")

# --------------------------------------------------
# PROCESS BUTTON
# --------------------------------------------------
if st.button("Run ATS Pipeline"):

    try:

        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        start_date = datetime.combine(
            from_date,
            datetime.min.time()
        )

        end_date = datetime.combine(
            to_date,
            datetime.max.time()
        )

        # --------------------------------------
        # DOWNLOAD RESUMES
        # --------------------------------------
        with st.spinner("Downloading resumes from Outlook..."):

            processed, downloaded = download_resumes(
                folder_path,
                start_date,
                end_date,
                lambda x: None
            )

        st.success(
            f"Processed Emails: {processed} | Downloaded Resumes: {downloaded}"
        )

        # --------------------------------------
        # ATS PARSING
        # --------------------------------------
        with st.spinner("Categorizing resumes..."):

            output_excel = process_resumes(folder_path)

        st.success("Resume categorization completed")

        st.write("Generated Excel:")

        st.code(output_excel)

        # --------------------------------------
        # DOWNLOAD BUTTON
        # --------------------------------------
        with open(output_excel, "rb") as file:

            st.download_button(
                label="⬇ Download Excel Report",
                data=file,
                file_name=os.path.basename(output_excel),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:

        st.error(str(e))