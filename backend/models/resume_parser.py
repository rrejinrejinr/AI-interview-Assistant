import re
import pdfplumber

def extract_resume_text(file_path: str) -> str:
    text = ""
    if file_path.lower().endswith(".pdf"):
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
    elif file_path.lower().endswith(".docx"):
        try:
            import docx
            doc = docx.Document(file_path)
            full_text = []
            for para in doc.paragraphs:
                full_text.append(para.text)
            text = "\n".join(full_text)
        except Exception as e:
            raise ValueError(f"Failed to extract text from DOCX: {e}")
    else:
        raise ValueError("Unsupported file format. Only PDF and DOCX files are supported.")

    return text.strip()

def extract_candidate_info(text: str) -> dict:
    if not text:
        return {
            "name": None,
            "email": None,
            "phone": None,
            "location": None,
            "linkedin": None,
            "github": None,
            "portfolio": None,
            "years_of_experience": None,
            "summary": None,
            "education": [],
            "experience": [],
            "projects": [],
            "certifications": [],
            "degree": None,
            "college": None,
            "graduation_year": None,
            "target_role": None,
        }

    lines = [l.strip() for l in text.splitlines() if l.strip()]

    # 1. Email
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    email_match = re.search(email_pattern, text)
    email = email_match.group(0) if email_match else None

    # 2. Phone — supports +1 555-0199, (123) 456-7890, +91 98765-43210, 555.123.4567, etc.
    phone_pattern = r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|(?:\+?\d{1,3}[-.\s]?)?\d{3}[-.\s]?\d{4}|(?:\+91[-.\s]?)?\d{5}[-.\s]?\d{5}'
    phone_match = re.search(phone_pattern, text)
    phone = phone_match.group(0) if phone_match else None

    # 3. Experience
    exp_pattern = r'(\d+| (one|two|three|four|five|six|seven|eight|nine|ten) )\+?\s*(?:years?|yrs?)\s*(?:of)?\s*(?:experience|exp)?'
    exp_match = re.search(exp_pattern, text, re.IGNORECASE)
    years_of_experience = exp_match.group(0) if exp_match else None

    # 4. Social Links
    linkedin_match = re.search(r'(?:https?://)?(?:www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+', text, re.IGNORECASE)
    linkedin = linkedin_match.group(0) if linkedin_match else None

    github_match = re.search(r'(?:https?://)?(?:www\.)?github\.com/[a-zA-Z0-9_-]+', text, re.IGNORECASE)
    github = github_match.group(0) if github_match else None

    portfolio_match = re.search(r'(?:https?://)?(?:www\.)?[a-zA-Z0-9_-]+\.(?:dev|io|me|com|tech)(?:/[a-zA-Z0-9_-]*)?', text, re.IGNORECASE)
    portfolio = None
    if portfolio_match:
        cand_url = portfolio_match.group(0)
        if "linkedin.com" not in cand_url and "github.com" not in cand_url and "gmail.com" not in cand_url:
            portfolio = cand_url

    # 5. Location heuristic (check top lines for City, State / Country first)
    location = None
    for line in lines[:6]:
        line_clean = line.strip()
        # Matches "City, State", "City, Country", "Chennai, Tamil Nadu", "Seattle, WA", etc.
        if re.search(r'^[A-Za-z\s.\-]+,\s*[A-Za-z\s.\-]+(?:\s+\d{5,6})?$', line_clean):
            if not any(k in line_clean.lower() for k in ["university", "college", "school", "institute", "b.tech", "degree", "experience"]):
                location = line_clean
                break
    if not location:
        loc_match = re.search(r'([A-Z][a-zA-Z\s]+,\s*(?:[A-Z]{2}(?:\s+\d{5})?|USA|India|Canada|UK|United States|Germany|Australia|Tamil Nadu|Karnataka|Maharashtra|Delhi|California|Texas|New York|Washington))', text)
        if loc_match:
            loc_str = loc_match.group(0).strip()
            if len(loc_str) < 45:
                location = loc_str

    # 6. Name heuristic (first clean line that isn't location, email, or URL)
    candidate_name = None
    for line in lines[:5]:
        line_clean = line.strip()
        if location and line_clean == location:
            continue
        # Lines with commas in top header are almost always locations or credential lists
        if ',' in line_clean:
            continue
        if '@' in line_clean or re.search(r'\d{5,}', line_clean) or 'http' in line_clean:
            continue
        candidate_line = line_clean
        # If line has dash or pipe separating title (e.g. John Doe - Senior Backend Engineer), check prefix
        if '-' in line_clean or '|' in line_clean:
            prefix = re.split(r'[-|]', line_clean)[0].strip()
            if 1 <= len(prefix.split()) <= 4:
                candidate_line = prefix
        words = candidate_line.split()
        if 1 <= len(words) <= 4 and len(candidate_line) < 50 and not re.search(r'[@:/\\0-9]', candidate_line):
            if not any(keyword in candidate_line.lower() for keyword in ["resume", "curriculum", "page", "profile", "contact", "email", "phone"]):
                candidate_name = candidate_line
                break

    # 7. Section Segmentations
    sections = {
        "summary": None,
        "education": [],
        "experience": [],
        "projects": [],
        "certifications": []
    }

    # Universal Lookahead for section headers
    SECTION_LOOKAHEAD = r'(?=\n\s*(?:EDUCATION|ACADEMIC\s+BACKGROUND|WORK\s+EXPERIENCE|EXPERIENCE|EMPLOYMENT\s+HISTORY|PROFESSIONAL\s+EXPERIENCE|(?:TECHNICAL\s+|KEY\s+|CORE\s+)?SKILLS|PROJECTS|PERSONAL\s+PROJECTS|KEY\s+PROJECTS|CERTIFICATIONS|LICENSES|CERTIFICATES|PROFESSIONAL\s+SUMMARY|SUMMARY|OBJECTIVE|EXTRACURRICULAR|ACHIEVEMENTS|AWARDS|$))'

    # Extract Summary snippet
    summary_match = re.search(r'(?:PROFESSIONAL\s+SUMMARY|SUMMARY|OBJECTIVE|ABOUT\s+ME)[\s:]*\n([\s\S]+?)' + SECTION_LOOKAHEAD, text, re.IGNORECASE)
    if summary_match:
        summary_text = summary_match.group(1).strip()
        if len(summary_text) >= 20:
            sections["summary"] = summary_text[:500].strip()

    # Extract Education lines
    edu_match = re.search(r'(?:EDUCATION|ACADEMIC\s+BACKGROUND|QUALIFICATIONS)[\s:]*\n([\s\S]+?)' + SECTION_LOOKAHEAD, text, re.IGNORECASE)
    if edu_match:
        edu_lines = [l.strip() for l in edu_match.group(1).splitlines() if l.strip() and len(l.strip()) > 3]
        sections["education"] = edu_lines[:5]

    # Extract Experience lines
    exp_block = re.search(r'(?:WORK\s+EXPERIENCE|EXPERIENCE|EMPLOYMENT\s+HISTORY|PROFESSIONAL\s+EXPERIENCE)[\s:]*\n([\s\S]+?)' + SECTION_LOOKAHEAD, text, re.IGNORECASE)
    if exp_block:
        exp_lines = [l.strip() for l in exp_block.group(1).splitlines() if l.strip() and len(l.strip()) > 3]
        sections["experience"] = exp_lines[:8]

    # Extract Projects lines
    proj_block = re.search(r'(?:PROJECTS|PERSONAL\s+PROJECTS|KEY\s+PROJECTS|ACADEMIC\s+PROJECTS)[\s:]*\n([\s\S]+?)' + SECTION_LOOKAHEAD, text, re.IGNORECASE)
    if proj_block:
        proj_lines = [l.strip() for l in proj_block.group(1).splitlines() if l.strip() and len(l.strip()) > 3]
        sections["projects"] = proj_lines[:6]

    # Extract Certifications lines
    cert_block = re.search(r'(?:CERTIFICATIONS|LICENSES|CERTIFICATES)[\s:]*\n([\s\S]+?)' + SECTION_LOOKAHEAD, text, re.IGNORECASE)
    if cert_block:
        cert_lines = [l.strip() for l in cert_block.group(1).splitlines() if l.strip() and len(l.strip()) > 3]
        sections["certifications"] = cert_lines[:5]

    # 8. Degree, College, Graduation Year (from education block)
    degree = None
    college = None
    graduation_year = None

    INST_KEYWORDS = r'(?:University|College|Institute|School|Academy|Polytechnic|IIT|NIT|BITS|MIT|UCLA|Stanford)'
    DEGREE_PATTERN = r'(?:(?:\bB\.?S\.?|\bM\.?S\.?|\bB\.?Tech|\bM\.?Tech|\bB\.?E\.?|\bM\.?E\.?|\bPh\.?D\.?|\bB\.?Sc\.?|\bM\.?Sc\.?|\bBachelor|\bMaster|\bAssociate|\bDoctorate)\b[^\n,;|\-]*)'

    edu_text = edu_match.group(1) if edu_match else text

    deg_match = re.search(DEGREE_PATTERN, edu_text, re.IGNORECASE)
    if deg_match:
        degree = deg_match.group(0).strip().rstrip(',.').strip()

    # College extraction: check line-by-line within education text first
    for edu_line in edu_text.splitlines():
        edu_line_clean = edu_line.strip()
        if not edu_line_clean:
            continue
        if re.search(INST_KEYWORDS, edu_line_clean, re.IGNORECASE):
            # Strip out degree mentions so degree prefix doesn't pollute college
            c_clean = re.sub(DEGREE_PATTERN, '', edu_line_clean, flags=re.IGNORECASE)
            # Strip out 4-digit years
            c_clean = re.sub(r'\b(20\d{2}|19\d{2})\b', '', c_clean)
            # Strip status keywords like Expected, Pursuing, Completed
            c_clean = re.sub(r'\b(?:Expected|Pursuing|Completed|Graduated)\b', '', c_clean, flags=re.IGNORECASE)
            # Strip leading/trailing delimiters & parens
            c_clean = re.sub(r'^[,\s|\-–()]+|[,\s|\-–()]+$', '', c_clean).strip()
            c_clean = ' '.join(c_clean.split())
            if c_clean and re.search(INST_KEYWORDS, c_clean, re.IGNORECASE) and len(c_clean) > 3:
                college = c_clean
                break

    # Graduation year: when multiple years are found in education (e.g. 2024 - 2028), take the graduation/end year
    all_years = re.findall(r'\b(20\d{2}|19\d{2})\b', edu_text)
    if all_years:
        graduation_year = all_years[-1]

    # 9. Target role — look for a headline like "Name - Software Engineer" or a standalone line below the name
    target_role = None
    if candidate_name:
        # Check if the name line itself contains a dash-separated role
        for line in lines[:6]:
            if candidate_name in line and '-' in line:
                parts = line.split('-', 1)
                if len(parts) == 2 and parts[1].strip():
                    potential = parts[1].strip()
                    if 2 <= len(potential.split()) <= 6 and not re.search(r'[@:/\\|0-9]', potential):
                        target_role = potential
                        break
        # Also check the line immediately after the name for a standalone role headline (must contain role keywords)
        ROLE_KEYWORDS = r'\b(?:engineer|developer|analyst|architect|scientist|designer|manager|specialist|consultant|intern|lead|programmer|administrator)\b'
        if not target_role:
            name_found = False
            for line in lines[:8]:
                line_clean = line.strip()
                if name_found and 2 <= len(line_clean.split()) <= 6 and not re.search(r'[@:/\\|0-9]', line_clean):
                    if location and line_clean == location:
                        continue
                    if ',' in line_clean:
                        continue
                    low = line_clean.lower()
                    if re.search(ROLE_KEYWORDS, low):
                        if not any(kw in low for kw in ['email', 'phone', 'github', 'linkedin', 'portfolio', 'location', 'address', 'city', 'education', 'university', 'college', 'school']):
                            target_role = line_clean
                            break
                if candidate_name and candidate_name.lower() in line_clean.lower():
                    name_found = True

    # Safeguard: assessment-mode labels must never be classified as candidate target roles
    if target_role and target_role.strip().lower() in [
        "resume baseline assessment",
        "general resume quality",
        "resume-only analysis",
        "baseline assessment",
        "target position",
        "ats evaluation",
        "resume quality assessment"
    ]:
        target_role = None

    return {
        "name": candidate_name,
        "email": email,
        "phone": phone,
        "location": location,
        "linkedin": linkedin,
        "github": github,
        "portfolio": portfolio,
        "years_of_experience": years_of_experience,
        "summary": sections["summary"],
        "education": sections["education"],
        "experience": sections["experience"],
        "projects": sections["projects"],
        "certifications": sections["certifications"],
        "degree": degree,
        "college": college,
        "graduation_year": graduation_year,
        "target_role": target_role,
    }
