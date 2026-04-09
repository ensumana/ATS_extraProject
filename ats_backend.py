import os
import re
import pdfplumber
import docx
import pandas as pd
from sentence_transformers import SentenceTransformer, util

# -------------------------------
# Load Model ONCE (important)
# -------------------------------
model = SentenceTransformer('all-MiniLM-L6-v2')

# -------------------------------
# Global Variables
# -------------------------------
JOB_DESCRIPTION = ""
SKILLS = []
results = []
JD_EMBEDDING = None  # optimization

# -------------------------------
# Set Inputs
# -------------------------------
def load_jd(jd_text):
    global JOB_DESCRIPTION, JD_EMBEDDING
    JOB_DESCRIPTION = jd_text
    JD_EMBEDDING = model.encode(JOB_DESCRIPTION, convert_to_tensor=True)

def set_skills(skills_str):
    global SKILLS
    SKILLS = [s.strip().lower() for s in skills_str.split(",")]

# -------------------------------
# Text Extraction
# -------------------------------
def extract_text(file_path):
    text = ""
    try:
        if file_path.lower().endswith(".pdf"):
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
        elif file_path.lower().endswith(".docx"):
            doc = docx.Document(file_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    return text.lower()

# -------------------------------
# Information Extraction
# -------------------------------
def extract_email(text):
    match = re.search(r'[\w\.-]+@[\w\.-]+', text)
    return match.group(0) if match else ""

def extract_phone(text):
    match = re.search(r'\b\d{10}\b', text)
    return match.group(0) if match else ""

def extract_experience(text):
    matches = re.findall(r'(\d+)[\s\+-]?years', text)
    return max(map(int, matches)) if matches else 0

def extract_education(text):
    patterns = [
        r'(ph\.d\.|doctor of philosophy)',
        r'(m\.tech|m\.e\.|master)',
        r'(b\.tech|b\.e\.|bachelor)'
    ]
    for p in patterns:
        match = re.search(p, text)
        if match:
            return match.group(0)
    return ""

# -------------------------------
# Skill Matching
# -------------------------------
def skill_score(text):
    found = []
    for skill in SKILLS:
        if re.search(rf"\b{re.escape(skill)}\b", text):
            found.append(skill)
    return len(found), ", ".join(found)

# -------------------------------
# Semantic Score (optimized)
# -------------------------------
def semantic_score(text):
    if not JOB_DESCRIPTION.strip():
        return 0.0
    res_emb = model.encode(text, convert_to_tensor=True)
    return float(util.cos_sim(JD_EMBEDDING, res_emb))

# -------------------------------
# Main Processing
# -------------------------------
def process_resume(file_path):
    text = extract_text(file_path)

    skill_count, skills_found = skill_score(text)
    sem_score = semantic_score(text)
    exp = extract_experience(text)
    edu = extract_education(text)

    final_score = (0.5 * skill_count) + (0.3 * sem_score) + (0.2 * exp)

    # Category (important for UI)
    if final_score >= 5:
        category = "Strong Match"
    elif final_score >= 3:
        category = "Moderate Match"
    else:
        category = "Low Match"

    results.append({
        "Candidate Name": os.path.basename(file_path),
        "Email": extract_email(text),
        "Phone": extract_phone(text),
        "Education": edu,
        "Experience": exp,
        "Skills": skills_found,
        "Score": round(final_score, 3),
        "Category": category,
        "Why Selected": f"Skills: {skills_found}, Exp: {exp}, Semantic: {round(sem_score,2)}"
    })