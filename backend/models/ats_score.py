import os
import re
from typing import List, Dict, Tuple, Optional

from models.skill_extractor import extract_skills

# Configurable weights via environment variables (Default 50/50)
ATS_SEMANTIC_WEIGHT = float(os.getenv("ATS_SEMANTIC_WEIGHT", "0.50"))
ATS_SKILL_WEIGHT = float(os.getenv("ATS_SKILL_WEIGHT", "0.50"))

CANONICAL_SKILL_MAP = {
    "sklearn": "scikit-learn",
    "scikit learn": "scikit-learn",
    "scikit-learn": "scikit-learn",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "node": "Node.js",
    "nextjs": "Next.js",
    "next.js": "Next.js",
    "fastapi": "FastAPI",
    "pytorch": "PyTorch",
    "python": "Python",
    "java": "Java",
    "javascript": "JavaScript",
    "js": "JavaScript",
    "typescript": "TypeScript",
    "ts": "TypeScript",
    "sql": "SQL",
    "aws": "AWS",
    "amazon web services": "AWS",
    "azure": "Azure",
    "microsoft azure": "Azure",
    "gcp": "GCP",
    "google cloud": "GCP",
    "google cloud platform": "GCP",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "react": "React",
    "reactjs": "React",
    "react.js": "React",
    "vue": "Vue",
    "vuejs": "Vue",
    "vue.js": "Vue",
    "express": "Express",
    "expressjs": "Express",
    "express.js": "Express",
    "spring boot": "Spring Boot",
    "spring": "Spring",
    "numpy": "NumPy",
    "opencv": "OpenCV",
    "power bi": "Power BI",
    "mongodb": "MongoDB",
    "mysql": "MySQL",
    "redis": "Redis",
    "tensorflow": "TensorFlow",
    "keras": "Keras",
    "flask": "Flask",
    "tailwind": "Tailwind CSS",
    "tailwindcss": "Tailwind CSS",
    "tailwind css": "Tailwind CSS",
    "graphql": "GraphQL",
    "rest": "REST APIs",
    "rest api": "REST APIs",
    "rest apis": "REST APIs",
    "restful": "REST APIs",
    "restful api": "REST APIs",
    "restapi": "REST APIs",
    "git": "Git",
    "github": "Git",
    "gitlab": "Git",
    "linux": "Linux",
    "bash": "Bash",
    "terraform": "Terraform",
    "cicd": "CI/CD",
    "ci/cd": "CI/CD",
    "golang": "Go",
    "go": "Go",
    "html": "HTML",
    "html5": "HTML",
    "css": "CSS",
    "css3": "CSS",
    "kafka": "Kafka",
    "apache kafka": "Kafka",
    "spark": "Apache Spark",
    "apache spark": "Apache Spark",
    "nlp": "NLP",
    "natural language processing": "NLP",
    "llm": "LLM",
    "large language models": "LLM",
    "rag": "RAG",
    "retrieval augmented generation": "RAG",
    "genai": "Generative AI",
    "generative ai": "Generative AI",
    "pandas": "Pandas",
    "c++": "C++",
    "c#": "C#",
}

# Standard benchmarks for target roles
ROLE_BENCHMARK_SKILLS = {
    "frontend": ["JavaScript", "TypeScript", "React", "HTML", "CSS", "Next.js", "Redux", "Tailwind CSS", "Git"],
    "frontend developer": ["JavaScript", "TypeScript", "React", "HTML", "CSS", "Next.js", "Redux", "Tailwind CSS", "Git"],
    "web developer": ["JavaScript", "HTML", "CSS", "React", "Node.js", "Git", "REST APIs"],
    "backend": ["Python", "Java", "Node.js", "FastAPI", "Spring Boot", "SQL", "PostgreSQL", "Docker", "REST APIs", "Redis"],
    "backend developer": ["Python", "Java", "Node.js", "FastAPI", "Spring Boot", "SQL", "PostgreSQL", "Docker", "REST APIs", "Redis"],
    "full stack": ["JavaScript", "TypeScript", "React", "Python", "Node.js", "SQL", "PostgreSQL", "HTML", "CSS", "Git", "Docker", "REST APIs"],
    "full stack developer": ["JavaScript", "TypeScript", "React", "Python", "Node.js", "SQL", "PostgreSQL", "HTML", "CSS", "Git", "Docker", "REST APIs"],
    "machine learning": ["Python", "PyTorch", "TensorFlow", "NumPy", "Pandas", "scikit-learn", "SQL"],
    "machine learning engineer": ["Python", "PyTorch", "TensorFlow", "NumPy", "Pandas", "scikit-learn", "SQL"],
    "data science": ["Python", "SQL", "Pandas", "NumPy", "scikit-learn", "Power BI", "Statistics"],
    "data scientist": ["Python", "SQL", "Pandas", "NumPy", "scikit-learn", "Power BI", "Statistics"],
    "data analyst": ["SQL", "Python", "Excel", "Power BI", "Pandas", "Statistics", "Data Visualization"],
    "devops": ["Docker", "Kubernetes", "AWS", "CI/CD", "Linux", "Terraform", "Git", "Bash", "Python"],
    "devops engineer": ["Docker", "Kubernetes", "AWS", "CI/CD", "Linux", "Terraform", "Git", "Bash", "Python"],
    "cloud": ["AWS", "Azure", "GCP", "Docker", "Kubernetes", "Linux", "Terraform", "CI/CD"],
    "cloud engineer": ["AWS", "Azure", "GCP", "Docker", "Kubernetes", "Linux", "Terraform", "CI/CD"],
    "mobile": ["React Native", "Flutter", "Kotlin", "Swift", "Android", "iOS", "JavaScript"],
    "mobile developer": ["React Native", "Flutter", "Kotlin", "Swift", "Android", "iOS", "JavaScript"],
    "android developer": ["Kotlin", "Java", "Android", "Jetpack Compose", "REST APIs", "Git"],
    "ios developer": ["Swift", "iOS", "Xcode", "UIKit", "REST APIs", "Git"],
    "software engineer": ["Python", "Java", "C++", "JavaScript", "SQL", "Git", "Data Structures", "Algorithms", "OOP", "REST APIs"],
    "software developer": ["Python", "Java", "JavaScript", "SQL", "Git", "OOP", "REST APIs"],
}


def normalize_skill(skill_name: str) -> str:
    s_lower = skill_name.strip().lower()
    return CANONICAL_SKILL_MAP.get(s_lower, skill_name.strip())


def calculate_semantic_similarity(resume_text: str, comparison_text: str) -> float:
    if not resume_text or not comparison_text or not comparison_text.strip():
        return 0.0

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
        tfidf_matrix = vectorizer.fit_transform([resume_text, comparison_text])
        cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        # Scale to 0-100 percentage
        semantic_score = round(float(cosine_sim * 100), 2)
        return min(max(semantic_score, 0.0), 100.0)
    except Exception:
        return 0.0


def calculate_skill_overlap(
    resume_text: str,
    target_skills_or_text
) -> Tuple[float, List[str], List[str]]:
    resume_skills_dict = extract_skills(resume_text, exclude_projects=False)

    if isinstance(target_skills_or_text, (list, set)):
        target_skills = {normalize_skill(s) for s in target_skills_or_text}
    else:
        target_skills_dict = extract_skills(target_skills_or_text, exclude_projects=False)
        target_skills = set()
        for cat, skills in target_skills_dict.items():
            for s in skills:
                target_skills.add(normalize_skill(s))

    # Flatten and normalize resume skills
    resume_skills = set()
    for cat, skills in resume_skills_dict.items():
        for s in skills:
            resume_skills.add(normalize_skill(s))

    if not target_skills:
        return 100.0, sorted(list(resume_skills)), []

    # Case-insensitive matching to avoid double-penalizing synonyms
    resume_skills_lower = {s.lower(): s for s in resume_skills}
    target_skills_lower = {s.lower(): s for s in target_skills}

    matched = set()
    missing = set()
    for tl, t in target_skills_lower.items():
        if tl in resume_skills_lower:
            matched.add(t)
        else:
            missing.add(t)

    match_percentage = round((len(matched) / len(target_skills)) * 100.0, 2)
    return min(max(match_percentage, 0.0), 100.0), sorted(list(matched)), sorted(list(missing))


def _evaluate_structure_completeness(resume_text: str) -> Tuple[float, Dict[str, bool]]:
    """
    Evaluates resume structure completeness based on standard professional sections.
    Core sections (up to 100 max):
      - Contact Info (email, phone, links): up to 25 pts
      - Education (degree, university, college, graduation year): up to 25 pts
      - Technical Skills (skills list, technologies): up to 20 pts
      - Practical Work (Projects OR Work History): up to 30 pts
        (Freshers with projects are not penalized for lack of corporate experience)
    Supplemental sections (can top-up shortfalls, capped at 100):
      - Summary / Objective: up to 5 pts
      - Certifications / Honors: up to 5 pts
    Total possible = 100%. Normalized strictly between 0.0 and 100.0.
    """
    text_lower = resume_text.lower()

    has_email = bool(re.search(r'[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}', resume_text))
    has_phone = bool(re.search(r'(\+?\d[\d\s\-\(\)]{7,}\d)', resume_text))
    has_links = any(k in text_lower for k in ["linkedin.com", "github.com", "portfolio"])
    has_contact = has_email or has_phone or has_links

    has_degree = any(k in text_lower for k in [
        "bachelor", "master", "b.tech", "b.e.", "b.s.", "m.s.", "b.sc", "m.sc", "phd", "degree", "associate"
    ])
    has_institution = any(k in text_lower for k in [
        "university", "college", "institute", "school", "academy", "polytechnic", "iit", "nit", "bits"
    ])
    has_education = has_degree or has_institution or ("education" in text_lower or "academic" in text_lower)

    has_skills_heading = any(k in text_lower for k in [
        "skills", "technical skills", "technologies", "tech stack", "competencies", "proficiencies", "programming"
    ])

    has_projects_heading = any(k in text_lower for k in [
        "project", "projects", "key projects", "personal projects", "academic projects", "portfolio"
    ])
    has_experience_heading = any(k in text_lower for k in [
        "experience", "work history", "employment", "internship", "worked as", "engineer at", "developer at"
    ])

    has_summary = any(k in text_lower for k in [
        "summary", "objective", "profile", "about me", "professional summary"
    ])
    has_certifications = any(k in text_lower for k in [
        "certification", "certifications", "certificate", "awards", "achievements", "honors", "licenses"
    ])

    score = 0.0
    # 1. Contact (up to 20 pts)
    if has_email and (has_phone or has_links):
        score += 20.0
    elif has_contact:
        score += 12.0

    # 2. Education (up to 20 pts)
    if has_degree and (has_institution or "gpa" in text_lower or "cgpa" in text_lower):
        score += 20.0
    elif has_education:
        score += 12.0

    # 3. Skills (up to 20 pts)
    if has_skills_heading:
        score += 20.0
    elif any(k in text_lower for k in ["python", "java", "sql", "javascript", "c++", "docker"]):
        score += 10.0

    # 4. Practical Experience / Projects (up to 25 pts)
    # Freshers with projects receive practical experience credit
    if has_projects_heading and has_experience_heading:
        score += 25.0
    elif has_projects_heading or has_experience_heading:
        score += 20.0

    # 5. Professional Summary / Objective (up to 10 pts)
    if has_summary:
        score += 10.0

    # 6. Certifications / Honors (up to 5 pts)
    if has_certifications:
        score += 5.0

    sections_status = {
        "contact": has_contact,
        "education": has_education,
        "skills": has_skills_heading,
        "projects": has_projects_heading,
        "experience": has_experience_heading,
        "summary": has_summary,
        "certifications": has_certifications
    }

    return min(100.0, max(0.0, round(score, 1))), sections_status


def _evaluate_skill_evidence(resume_text: str, all_skills: List[str]) -> Tuple[float, List[str], List[str]]:
    """
    Evaluates skill breadth, contextual application, and depth:
    - Breadth (up to 40 pts): graduated scale based on distinct verified canonical skills.
    - Contextual Application (up to 40 pts): checks whether extracted skills are demonstrated
      in actionable bullet points with active verbs rather than simply dumped into a list.
    - Depth & Repetition (up to 20 pts): checks whether skills appear across multiple distinct
      bullet points or project contexts.
    Total: 0 to 100 points.
    Returns: (skill_density_score, supported_skills, unevidenced_skills)
    """
    if not all_skills:
        return 0.0, [], []

    lines = [l.strip() for l in resume_text.splitlines() if l.strip()]
    action_verbs = {
        'developed', 'built', 'implemented', 'designed', 'architected', 'integrated',
        'deployed', 'trained', 'configured', 'tested', 'created', 'engineered',
        'optimized', 'automated', 'managed', 'authored', 'maintained', 'analyzed',
        'conducted', 'spearheaded', 'established', 'formulated', 'delivered', 'collaborated'
    }

    skill_heading_pattern = r'^(?:technical\s+|key\s+|core\s+)?(?:skills|technologies|languages|frameworks|databases|tools)[\s:]'

    bullet_lines = []
    for line in lines:
        if re.search(skill_heading_pattern, line, re.IGNORECASE):
            continue
        low = line.lower()
        has_verb = any(v in low for v in action_verbs)
        is_bullet = line.startswith('•') or line.startswith('-') or line.startswith('*')
        if has_verb or is_bullet:
            if not has_verb and line.count(',') >= 3:
                continue
            bullet_lines.append(line)

    # 1. Breadth score (up to 35 pts)
    n_skills = len(all_skills)
    if n_skills >= 10:
        breadth_score = 35.0
    elif n_skills >= 7:
        breadth_score = 28.0
    elif n_skills >= 4:
        breadth_score = 20.0
    elif n_skills >= 2:
        breadth_score = 12.0
    else:
        breadth_score = 6.0

    # 2. Contextual Application (up to 45 pts)
    supported = []
    unevidenced = []
    skill_mention_counts = {s: 0 for s in all_skills}

    for skill in all_skills:
        pattern = r'(?:\b|(?<=\W))' + re.escape(skill.lower()) + r'(?:\b|(?=\W))'
        matched_bullets = 0
        for bline in bullet_lines:
            if re.search(pattern, bline.lower()):
                matched_bullets += 1
        skill_mention_counts[skill] = matched_bullets
        if matched_bullets > 0:
            supported.append(skill)
        else:
            unevidenced.append(skill)

    evidence_ratio = (len(supported) / max(1, n_skills)) if n_skills else 0.0
    distinct_contexts = sum(1 for bline in bullet_lines if any(re.search(r'(?:\b|(?<=\W))' + re.escape(s.lower()) + r'(?:\b|(?=\W))', bline.lower()) for s in all_skills))
    context_score = round(evidence_ratio * 35.0 + min(10.0, distinct_contexts * 2.0), 1)

    # 3. Depth & Repetition (up to 20 pts)
    multi_context_skills = sum(1 for s, count in skill_mention_counts.items() if count >= 2)
    if multi_context_skills >= 5:
        depth_score = 20.0
    elif multi_context_skills >= 3:
        depth_score = 14.0
    elif multi_context_skills >= 1:
        depth_score = 7.0
    else:
        depth_score = 0.0

    skill_score = round(breadth_score + context_score + depth_score, 1)
    return min(100.0, max(0.0, skill_score)), supported, unevidenced


def _evaluate_content_impact(resume_text: str) -> float:
    """
    Evaluates bullet point quality, action-oriented descriptions, and quantified metrics:
    - Action Verbs (up to 35 pts): active verbs demonstrating leadership and implementation.
    - Quantified Achievements & Metrics (up to 35 pts): numbers, percentages, scales, performance data.
    - Detail & Substance (up to 30 pts): substantive descriptions vs superficial one-liners.
    Total: 0 to 100 points.
    """
    lines = [l.strip() for l in resume_text.splitlines() if l.strip()]
    action_verbs = {
        'developed', 'built', 'implemented', 'designed', 'architected', 'integrated',
        'deployed', 'trained', 'configured', 'tested', 'created', 'engineered',
        'optimized', 'automated', 'managed', 'authored', 'maintained', 'analyzed',
        'conducted', 'spearheaded', 'established', 'formulated', 'delivered', 'collaborated'
    }

    bullet_lines = []
    for line in lines:
        low = line.lower()
        has_verb = any(v in low for v in action_verbs)
        is_bullet = line.startswith('•') or line.startswith('-') or line.startswith('*')
        if (has_verb or is_bullet) and len(line.split()) >= 4:
            bullet_lines.append(line)

    if not bullet_lines:
        return 0.0

    # 1. Action verbs count (up to 35 pts)
    action_bullets = sum(1 for line in bullet_lines if any(v in line.lower() for v in action_verbs))
    if action_bullets >= 5:
        verb_score = 35.0
    elif action_bullets >= 3:
        verb_score = 25.0
    elif action_bullets >= 1:
        verb_score = 15.0
    else:
        verb_score = 0.0

    # 2. Measurable Metrics (up to 35 pts)
    metric_patterns = [
        r'\b\d+(?:\.\d+)?%',                                   # Percentages: 45%, 99.99%
        r'\b\d+k\b|\b\d+m\b|\b\d+ms\b',                         # Scales: 25k, 10ms
        r'\b\d+(?:\+)?\s*(?:users|clients|nodes|requests|qps|queries|endpoints|modules|records|problems|services|stars|downloads|tables)\b',
        r'\$\d+(?:,\d+)?',                                      # Financial: $120,000
        r'(?:cgpa|gpa|rating)[\s:]*\d+(?:\.\d+)?',              # Academic: CGPA: 9.09
        r'\b(?:latency|throughput|uptime|accuracy)\b',          # Engineering metrics
    ]
    total_metrics_found = 0
    full_text_lower = resume_text.lower()
    for pat in metric_patterns:
        total_metrics_found += len(re.findall(pat, full_text_lower))

    if total_metrics_found >= 5:
        metric_score = 35.0
    elif total_metrics_found >= 3:
        metric_score = 25.0
    elif total_metrics_found >= 1:
        metric_score = 15.0
    else:
        metric_score = 5.0

    # 3. Detail & Substance (up to 30 pts)
    avg_words = sum(len(b.split()) for b in bullet_lines) / max(1, len(bullet_lines))
    if avg_words >= 18:
        substance_score = 30.0
    elif avg_words >= 12:
        substance_score = 20.0
    elif avg_words >= 6:
        substance_score = 10.0
    else:
        substance_score = 0.0

    total_impact = round(verb_score + metric_score + substance_score, 1)
    return min(100.0, max(0.0, total_impact))


def _evaluate_document_length(word_count: int) -> float:
    """
    Evaluates document length transparently:
    - 250 to 900 words: Optimal 1-2 page standard (100.0%)
    - 200 to 249 or 901 to 1200 words: Acceptable range (85.0%)
    - 120 to 199 words: Brief resume (60.0%)
    - 50 to 119 words: Sparse resume (35.0%)
    - 25 to 49 words: Minimal/Stub (15.0%)
    - < 25 words: Unreadable (0.0%)
    - > 1200 words: Verbose penalty (70.0%)
    """
    if word_count < 25:
        return 0.0
    elif word_count < 50:
        return 15.0
    elif word_count < 120:
        return 35.0
    elif word_count < 200:
        return 60.0
    elif (200 <= word_count < 250) or (900 < word_count <= 1200):
        return 85.0
    elif 250 <= word_count <= 900:
        return 100.0
    else:
        return 70.0


def _generate_report_sections(
    resume_text: str,
    matched_skills: List[str],
    missing_skills: List[str],
    ats_score: float,
    analysis_mode: str,
    job_title: Optional[str] = None
) -> Dict:
    """
    Generate evidence-based strengths, areas to improve, and recommendations.
    Only includes claims that are grounded in the resume text or the skill lists.
    """
    text_lower = resume_text.lower()
    strengths = []
    improvements = []
    next_steps = []

    # Skill breadth strength - do not claim role relevance unless a job_title / role was provided
    if len(matched_skills) >= 5:
        if job_title:
            strengths.append(f"Strong technical skill set: your resume includes {len(matched_skills)} relevant skills for the {job_title} role.")
        else:
            strengths.append(f"Strong technical skill set: your resume includes {len(matched_skills)} verified technical skills.")
    elif len(matched_skills) >= 2:
        if job_title:
            strengths.append(f"Your resume covers {len(matched_skills)} relevant technical skill{'s' if len(matched_skills) > 1 else ''} for the {job_title} role.")
        else:
            strengths.append(f"Your resume includes {len(matched_skills)} verified technical skill{'s' if len(matched_skills) > 1 else ''}.")

    # Section completeness strengths
    has_projects = any(k in text_lower for k in ["project", "built", "developed", "implemented"])
    has_education = any(k in text_lower for k in ["education", "university", "college", "b.tech", "b.e.", "bachelor", "degree"])
    has_experience = any(k in text_lower for k in ["experience", "internship", "worked", "engineer at", "developer at"])
    has_summary = any(k in text_lower for k in ["summary", "objective", "profile", "about"])
    has_contact = bool(re.search(r'[\w\.-]+@[\w\.-]+', resume_text) or any(k in text_lower for k in ["contact", "email", "phone", "linkedin.com", "github.com"]))

    if has_projects:
        strengths.append("Projects section is present, demonstrating applied technical work.")
    if has_education:
        strengths.append("Educational background is clearly documented.")
    if has_experience:
        strengths.append("Professional experience or internship details are included.")
    if has_contact:
        strengths.append("Contact information is clearly provided.")

    # Missing skills are direct improvements (only when a comparison exists)
    if missing_skills:
        top_missing = missing_skills[:5]
        improvements.append(
            f"Add or demonstrate skills that are expected for this role but not detected in your resume: "
            f"{', '.join(top_missing)}"
            + (f" (and {len(missing_skills) - 5} more)" if len(missing_skills) > 5 else "") + "."
        )

    if not has_summary:
        improvements.append("Add a concise professional summary or objective at the top of your resume.")

    if not has_projects and not has_experience:
        improvements.append("Include at least one project or work experience entry with specific technologies used.")

    word_count = len(resume_text.split())
    if word_count < 200:
        improvements.append("The resume appears very short. Add more detail about your experience, projects, and skills.")
    elif word_count > 1200:
        improvements.append("The resume is quite long. Consider condensing to 1-2 pages by removing low-impact content.")

    # Next steps
    if ats_score < 50:
        next_steps.append("Expand your skills section to include more technologies relevant to the target role.")
    if missing_skills:
        next_steps.append(f"Work on or add: {', '.join(missing_skills[:3])}.")
    if not has_summary:
        next_steps.append("Write a 2-3 sentence professional summary tailored to your target role.")
    if not has_projects:
        next_steps.append("Add 1-2 technical projects with a brief description of your contribution and technologies used.")
    if not next_steps:
        next_steps.append("Tailor the resume language to match the exact keywords used in the job description.")

    return {
        "strengths": strengths if strengths else ["Resume contains detectable technical content and skills."],
        "areas_to_improve": improvements if improvements else ["Review the resume for clarity and completeness."],
        "recommended_next_steps": next_steps if next_steps else ["Run another analysis with a specific job description for more targeted recommendations."]
    }


def calculate_ats_score(
    resume_text: str,
    job_description: Optional[str] = None,
    job_title: Optional[str] = None
) -> dict:
    if not resume_text or not resume_text.strip():
        raise ValueError("Resume text cannot be empty.")

    clean_text = resume_text.strip()
    words = clean_text.split()

    clean_jd = (job_description or "").strip()
    clean_title = (job_title or "").strip()

    # ----------------------------------------------------------------
    # CASE A: Resume Only (Baseline Quality & Readiness Score)
    # Does NOT pretend a role-specific match score exists.
    # ----------------------------------------------------------------
    if not clean_jd and not clean_title:
        resume_skills_dict = extract_skills(resume_text, exclude_projects=False)
        all_skills = sorted(list({normalize_skill(s) for skills in resume_skills_dict.values() for s in skills}))

        # 1. Structure completeness (30% weight)
        structure_score, _ = _evaluate_structure_completeness(resume_text)

        # 2. Skill breadth & contextual evidence (30% weight)
        skill_density_score, supported_skills, unevidenced_skills = _evaluate_skill_evidence(resume_text, all_skills)

        # 3. Content impact & measurable metrics (25% weight)
        content_impact_score = _evaluate_content_impact(resume_text)

        # 4. Document length & formatting (15% weight): optimal 250-900 words
        word_count = len(words)
        length_score = _evaluate_document_length(word_count)

        # Composite: 30% structure, 30% skill evidence, 25% content impact, 15% length (sum = 100%)
        final_score = round(
            (structure_score * 0.30)
            + (skill_density_score * 0.30)
            + (content_impact_score * 0.25)
            + (length_score * 0.15),
            1
        )
        final_score = min(max(final_score, 0.0), 100.0)

        report = _generate_report_sections(
            resume_text=resume_text,
            matched_skills=all_skills,
            missing_skills=[],
            ats_score=final_score,
            analysis_mode="Resume-only analysis",
            job_title=None
        )

        return {
            "ats_score": final_score,
            # Explicit tier scores
            "resume_quality_score": final_score,
            "role_match_score": None,      # No role provided — not computed
            "jd_match_score": None,        # No JD provided — not computed
            "structure_score": round(structure_score, 1),
            "skill_density_score": round(skill_density_score, 1),
            "content_impact_score": round(content_impact_score, 1),
            "length_score": round(length_score, 1),
            "structure_weight": 30,
            "skill_density_weight": 30,
            "content_impact_weight": 25,
            "length_weight": 15,
            "word_count": word_count,
            # For backward-compat with DB columns:
            "semantic_score": round(structure_score, 1),
            "skill_match_score": round(skill_density_score, 1),
            "matched_skills": all_skills,
            "missing_skills": [],
            "analysis_mode": "Resume-only analysis",
            "scoring_note": (
                "Score is based on resume structure completeness (30%), "
                "technical skill breadth and project evidence (30%), "
                "content impact and measurable outcomes (25%), and document length (15%). "
                "No job description was provided, so no role-specific comparison is computed."
            ),
            "strengths": report["strengths"],
            "areas_to_improve": report["areas_to_improve"],
            "recommended_next_steps": report["recommended_next_steps"],
        }

    # ----------------------------------------------------------------
    # CASE B: Resume + Target Role Only
    # Evaluates normalized Role Skill Coverage against benchmark skills.
    # Keeps document quality separate from role compatibility.
    # Does NOT compare against a short synthetic string using TF-IDF.
    # ----------------------------------------------------------------
    if not clean_jd and clean_title:
        title_lower = clean_title.lower()
        matched_bench = None
        benchmark_is_exact = False

        # Exact match first, then substring match
        if title_lower in ROLE_BENCHMARK_SKILLS:
            matched_bench = ROLE_BENCHMARK_SKILLS[title_lower]
            benchmark_is_exact = True
        else:
            for role_key, bench_skills in ROLE_BENCHMARK_SKILLS.items():
                if role_key in title_lower or title_lower in role_key:
                    matched_bench = bench_skills
                    benchmark_is_exact = True
                    break

        if not matched_bench:
            # Fallback: general software engineering baseline
            matched_bench = ROLE_BENCHMARK_SKILLS["software engineer"]
            benchmark_is_exact = False

        # Role skill coverage: percentage of required benchmark skills present in resume
        skill_match_score, matched_skills, missing_skills = calculate_skill_overlap(resume_text, matched_bench)
        final_score = round(skill_match_score, 1)

        # Document quality (structure completeness + skill evidence) evaluated separately
        structure_score, _ = _evaluate_structure_completeness(resume_text)

        if benchmark_is_exact:
            note = (
                f"Role Compatibility Score: {final_score}% ({len(matched_skills)} of {len(matched_bench)} benchmark skills matched for '{clean_title}'). "
                f"General document structure quality is {structure_score}%. "
                "No job description was provided, so no text-similarity match is computed."
            )
        else:
            note = (
                f"'{clean_title}' is not in our standardized role benchmark library; evaluated against a general software engineering baseline "
                f"({len(matched_skills)} of {len(matched_bench)} skills matched: {final_score}%). "
                f"General document structure quality is {structure_score}%. "
                "For role-specific precision, provide a job description."
            )

        report = _generate_report_sections(
            resume_text=resume_text,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            ats_score=final_score,
            analysis_mode="Resume + Target Role",
            job_title=clean_title
        )

        # Compute resume quality separately from role match
        resume_skills_dict = extract_skills(resume_text, exclude_projects=False)
        all_resume_skills = sorted(list({normalize_skill(s) for skills in resume_skills_dict.values() for s in skills}))
        skill_density_score, supported_skills, _ = _evaluate_skill_evidence(resume_text, all_resume_skills)
        content_impact_score = _evaluate_content_impact(resume_text)
        word_count = len(resume_text.split())
        length_score = _evaluate_document_length(word_count)
        resume_quality_score = round(
            (structure_score * 0.30) + (skill_density_score * 0.30) + (content_impact_score * 0.25) + (length_score * 0.15), 1
        )
        resume_quality_score = min(max(resume_quality_score, 0.0), 100.0)

        return {
            "ats_score": final_score,
            # Explicit tier scores
            "resume_quality_score": round(resume_quality_score, 1),
            "role_match_score": final_score,
            "jd_match_score": None,        # No JD provided
            "role_skill_coverage": final_score,
            "skill_match_score": final_score,
            "structure_score": structure_score,
            "skill_density_score": skill_density_score,
            "content_impact_score": round(content_impact_score, 1),
            "length_score": length_score,
            "structure_weight": 30,
            "skill_density_weight": 30,
            "content_impact_weight": 25,
            "length_weight": 15,
            "word_count": word_count,
            "semantic_score": 0.0,  # Semantic TF-IDF is not applicable without a real job description
            "benchmark_is_exact": benchmark_is_exact,
            "total_benchmark_skills": len(matched_bench),
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "analysis_mode": "Resume + Target Role",
            "scoring_note": note,
            "strengths": report["strengths"],
            "areas_to_improve": report["areas_to_improve"],
            "recommended_next_steps": report["recommended_next_steps"],
        }

    # ----------------------------------------------------------------
    # CASE C: Resume + Job Description Only
    # Compares directly against the actual job description text.
    # ----------------------------------------------------------------
    if clean_jd and not clean_title:
        if len(clean_jd.split()) < 5:
            raise ValueError(
                "Job description is too short to be meaningful. "
                "Please provide at least a few sentences describing the role."
            )
        semantic_score = calculate_semantic_similarity(resume_text, clean_jd)
        skill_match_score, matched_skills, missing_skills = calculate_skill_overlap(resume_text, clean_jd)

        final_score = round((semantic_score * ATS_SEMANTIC_WEIGHT) + (skill_match_score * ATS_SKILL_WEIGHT), 1)
        final_score = min(max(final_score, 0.0), 100.0)

        report = _generate_report_sections(
            resume_text=resume_text,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            ats_score=final_score,
            analysis_mode="Resume + Job Description",
            job_title=None
        )

        # Compute general resume quality as tier score
        structure_score, _ = _evaluate_structure_completeness(resume_text)
        resume_skills_dict = extract_skills(resume_text, exclude_projects=False)
        all_resume_skills = sorted(list({normalize_skill(s) for skills in resume_skills_dict.values() for s in skills}))
        skill_density_score, _, _ = _evaluate_skill_evidence(resume_text, all_resume_skills)
        content_impact_score = _evaluate_content_impact(resume_text)
        word_count = len(resume_text.split())
        length_score = _evaluate_document_length(word_count)
        resume_quality_score = round(
            (structure_score * 0.30) + (skill_density_score * 0.30) + (content_impact_score * 0.25) + (length_score * 0.15), 1
        )
        resume_quality_score = min(max(resume_quality_score, 0.0), 100.0)

        return {
            "ats_score": final_score,
            "resume_quality_score": round(resume_quality_score, 1),
            "role_match_score": None,
            "jd_match_score": final_score,
            "semantic_score": semantic_score,
            "skill_match_score": skill_match_score,
            "structure_score": structure_score,
            "skill_density_score": skill_density_score,
            "content_impact_score": round(content_impact_score, 1),
            "length_score": length_score,
            "structure_weight": 30,
            "skill_density_weight": 30,
            "content_impact_weight": 25,
            "length_weight": 15,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "analysis_mode": "Resume + Job Description",
            "scoring_note": (
                "Score is 50% TF-IDF cosine similarity between your resume and the job description, "
                "and 50% overlap between skills detected in your resume and skills detected in the job description. "
                "Missing skills are extracted from the actual job description text you provided."
            ),
            "strengths": report["strengths"],
            "areas_to_improve": report["areas_to_improve"],
            "recommended_next_steps": report["recommended_next_steps"],
        }

    # ----------------------------------------------------------------
    # CASE D: Resume + Target Role + Job Description
    # Most comprehensive: compares against combined role + JD.
    # ----------------------------------------------------------------
    if len(clean_jd.split()) < 5:
        raise ValueError(
            "Job description is too short to be meaningful. "
            "Please provide at least a few sentences describing the role."
        )

    combined_jd = f"Target Position: {clean_title}\n\nJob Description:\n{clean_jd}"
    semantic_score = calculate_semantic_similarity(resume_text, combined_jd)
    skill_match_score, matched_skills, missing_skills = calculate_skill_overlap(resume_text, combined_jd)

    final_score = round((semantic_score * ATS_SEMANTIC_WEIGHT) + (skill_match_score * ATS_SKILL_WEIGHT), 1)
    final_score = min(max(final_score, 0.0), 100.0)

    report = _generate_report_sections(
        resume_text=resume_text,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        ats_score=final_score,
        analysis_mode="Resume + Target Role + Job Description",
        job_title=clean_title
    )

    # Compute resume quality and role benchmark match as tier scores
    structure_score, _ = _evaluate_structure_completeness(resume_text)
    resume_skills_dict = extract_skills(resume_text, exclude_projects=False)
    all_resume_skills = sorted(list({normalize_skill(s) for skills in resume_skills_dict.values() for s in skills}))
    skill_density_score, _, _ = _evaluate_skill_evidence(resume_text, all_resume_skills)
    content_impact_score = _evaluate_content_impact(resume_text)
    word_count = len(resume_text.split())
    length_score = _evaluate_document_length(word_count)
    resume_quality_score = round(
        (structure_score * 0.30) + (skill_density_score * 0.30) + (content_impact_score * 0.25) + (length_score * 0.15), 1
    )
    resume_quality_score = min(max(resume_quality_score, 0.0), 100.0)

    role_bench_score = None
    if clean_title:
        title_lower = clean_title.lower()
        matched_bench = None
        for role_key, bench_skills in ROLE_BENCHMARK_SKILLS.items():
            if role_key in title_lower or title_lower in role_key:
                matched_bench = bench_skills
                break
        if not matched_bench:
            matched_bench = ROLE_BENCHMARK_SKILLS.get("software engineer")
        if matched_bench:
            bench_match, _, _ = calculate_skill_overlap(resume_text, matched_bench)
            role_bench_score = round(bench_match, 1)

    return {
        "ats_score": final_score,
        "resume_quality_score": round(resume_quality_score, 1),
        "role_match_score": role_bench_score,
        "jd_match_score": final_score,
        "semantic_score": semantic_score,
        "skill_match_score": skill_match_score,
        "structure_score": structure_score,
        "skill_density_score": skill_density_score,
        "content_impact_score": round(content_impact_score, 1),
        "length_score": length_score,
        "structure_weight": 30,
        "skill_density_weight": 30,
        "content_impact_weight": 25,
        "length_weight": 15,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "analysis_mode": "Resume + Target Role + Job Description",
        "scoring_note": (
            f"Score is 50% TF-IDF cosine similarity between your resume and the combined '{clean_title}' job description, "
            "and 50% overlap between skills detected in your resume and skills extracted from the job description. "
            "Missing skills are derived from the actual job description you provided."
        ),
        "strengths": report["strengths"],
        "areas_to_improve": report["areas_to_improve"],
        "recommended_next_steps": report["recommended_next_steps"],
    }

