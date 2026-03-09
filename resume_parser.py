import re
import os

# Import skill taxonomy from skill_extractor
from skill_extractor import SKILLS, extract_skills


def parse_resume_text(text):
    """
    Given plain text from a resume,
    extract skills, experience level, and name.
    """
    if not text or len(text.strip()) < 10:
        return {
            "name":             "Unknown",
            "experience_level": "fresher",
            "skills_found":     [],
            "raw_text":         ""
        }

    # Extract skills
    skills_found = extract_skills(text)

    # Detect experience level
    experience_level = detect_experience_level(text)

    # Detect name (first line heuristic)
    name = extract_name(text)

    return {
        "name":             name,
        "experience_level": experience_level,
        "skills_found":     skills_found,
        "raw_text":         text[:500]
    }


def detect_experience_level(text):
    """
    Detect if candidate is fresher, junior, mid, or senior
    based on years of experience mentioned.
    """
    text_lower = text.lower()

    # Look for year patterns like "3 years", "5+ years"
    patterns = [
        r'(\d+)\+?\s*years?\s*of\s*experience',
        r'(\d+)\+?\s*years?\s*experience',
        r'experience\s*of\s*(\d+)\+?\s*years?',
    ]

    years = 0
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            years = int(match.group(1))
            break

    # Keywords that suggest seniority
    if any(x in text_lower for x in ["fresher", "fresh graduate", "no experience", "0 years"]):
        return "fresher"
    elif years == 0 or years <= 1:
        return "fresher"
    elif years <= 3:
        return "junior"
    elif years <= 6:
        return "mid-level"
    else:
        return "senior"


def extract_name(text):
    """
    Simple heuristic — first non-empty line is usually the name.
    """
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if not lines:
        return "Unknown"
    first_line = lines[0]
    # If it looks like a name (2-4 words, no special chars)
    if len(first_line.split()) <= 4 and re.match(r'^[A-Za-z\s]+$', first_line):
        return first_line
    return "Unknown"


def parse_pdf_resume(uploaded_file):
    """
    Extract text from uploaded PDF resume using PyMuPDF.
    Falls back to raw text if PDF parsing fails.
    """
    try:
        import fitz  # PyMuPDF
        import tempfile

        # Save uploaded file to temp location
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

        # Extract text
        doc  = fitz.open(tmp_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        os.unlink(tmp_path)

        return text.strip()

    except ImportError:
        return None
    except Exception as e:
        print(f"PDF parsing error: {e}")
        return None


def parse_txt_resume(uploaded_file):
    """Extract text from plain .txt resume."""
    try:
        return uploaded_file.read().decode("utf-8")
    except Exception:
        return None


if __name__ == "__main__":
    # Test with sample resume text
    sample_resume = """
    Salaar Khan
    Fresh Graduate — Computer Science

    Skills:
    Python, SQL, Machine Learning, Pandas, NumPy, Statistics

    Education:
    B.Tech Computer Science — 2025

    Projects:
    - Built a sentiment analysis model using HuggingFace transformers
    - Created a data pipeline using Airflow and AWS
    """

    result = parse_resume_text(sample_resume)
    print(f"Name:             {result['name']}")
    print(f"Experience Level: {result['experience_level']}")
    print(f"Skills Found:     {result['skills_found']}")