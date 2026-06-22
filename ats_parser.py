import os
import re
import pandas as pd
import pdfplumber
from docx import Document
from datetime import datetime


# ----------------------------
# TEXT EXTRACTION
# ----------------------------
def extract_text(file_path):
    if file_path.lower().endswith(".pdf"):
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        return text

    elif file_path.lower().endswith(".docx"):
        doc = Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])

    return ""


# ----------------------------
# FIELD EXTRACTION HELPERS
# ----------------------------
def extract_email(text):
    match = re.findall(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", text)
    return match[0] if match else ""


def extract_phone(text):
    match = re.findall(r"\+?\d[\d\s\-]{8,15}", text)
    return match[0] if match else ""


def extract_name(filename, text):
    # priority: filename (sender name format)
    base = os.path.basename(filename)
    name = base.split("_")[0]
    return name.replace(".", " ").strip()


def extract_experience(text):
    match = re.findall(r"(\d+)\+?\s*(years|yrs|year)", text.lower())
    if match:
        return max([int(m[0]) for m in match])
    return ""


def extract_education(text):
    keywords = ["b.tech", "m.tech", "b.e", "m.e", "bsc", "msc", "mba", "phd", "diploma"]
    found = [k for k in keywords if k in text.lower()]
    return ", ".join(found)


def extract_skills(text):
    skill_bank = [
        "python", "java", "c++", "sql", "machine learning",
        "deep learning", "opencv", "tensorflow", "pytorch",
        "embedded", "linux", "aws", "docker"
    ]
    found = [s for s in skill_bank if s in text.lower()]
    return ", ".join(found)


def extract_companies(text):
    # very heuristic: looks for "at Company" or bullet-like org mentions
    matches = re.findall(r"(?:at|@)\s([A-Z][A-Za-z0-9& ]{2,})", text)
    unique = list(dict.fromkeys(matches))
    return unique[:2] if len(unique) >= 2 else unique + ["", ""]


def extract_location(text):
    match = re.search(r"(Bangalore|Bengaluru|Hyderabad|Chennai|Pune|Delhi|Mumbai)", text, re.IGNORECASE)
    return match.group(0) if match else ""


def extract_designation(text):
    match = re.findall(r"(software engineer|developer|data scientist|analyst|manager|consultant)", text.lower())
    return match[0] if match else ""

date_str = datetime.now().strftime("%Y-%m-%d")
#output = os.path.join(folder_path, f"Resume_categorization_{date_str}.xlsx")
# ----------------------------
# MAIN ATS PIPELINE
# ----------------------------
def process_resumes(folder_path, output_excel=f"Resume_categorization_{date_str}.xlsx"):
    data = []
    sl_no = 1

    for file in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file)

        if not file.lower().endswith((".pdf", ".docx")):
            continue

        text = extract_text(file_path)

        email = extract_email(text)
        phone = extract_phone(text)
        name = extract_name(file, text)
        experience = extract_experience(text)
        education = extract_education(text)
        skills = extract_skills(text)
        location = extract_location(text)
        designation = extract_designation(text)

        companies = extract_companies(text)
        company_1 = companies[0] if len(companies) > 0 else ""
        company_2 = companies[1] if len(companies) > 1 else ""

        # date from filename (from your Outlook naming convention)
        date_match = re.search(r"(\d{8}_\d{6})", file)
        email_date = datetime.strptime(date_match.group(), "%Y%m%d_%H%M%S") if date_match else ""

        data.append([
            sl_no,
            designation,
            name,
            phone,
            email,
            email_date,
            location,
            education,
            experience,
            company_1,
            company_2,
            designation,
            skills
        ])

        sl_no += 1

    df = pd.DataFrame(data, columns=[
        "Sl.No",
        "Position",
        "Name",
        "Contact Number",
        "Email ID",
        "Date of Email",
        "Location",
        "Education",
        "Total Experience",
        "Company 1",
        "Company 2",
        "Designation",
        "Skills"
    ])

    df.to_excel(output_excel, index=False)

    return output_excel