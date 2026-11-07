"""
resume_pdf_generator.py — ATS-Friendly A4 PDF Resume Generator

Supports 5 Structurally Different Resume Templates:
  1. Simple    — Traditional single-column academic/corporate structure with dividing rules
  2. Modern    — Header banner styling, structured project cards, and clean skill tags
  3. Minimal   — Typography-focused layout with generous spacing and understated elegance
  4. Fresher   — Education & academic/capstone projects prioritized for new graduates
  5. Technical — Categorized technical stack at top, GitHub project links, and architecture notes

Uses ReportLab for selectable, ATS-compliant A4 PDF compilation.
"""

import io
import os
import re
from typing import Dict, Any, List
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)

# Standard font mapping to ReportLab standard 14 PostScript fonts
FONT_FAMILY_MAP = {
    "helvetica": ("Helvetica", "Helvetica-Bold", "Helvetica-Oblique"),
    "arial": ("Helvetica", "Helvetica-Bold", "Helvetica-Oblique"),
    "calibri": ("Helvetica", "Helvetica-Bold", "Helvetica-Oblique"),
    "times new roman": ("Times-Roman", "Times-Bold", "Times-Italic"),
    "times": ("Times-Roman", "Times-Bold", "Times-Italic"),
    "georgia": ("Times-Roman", "Times-Bold", "Times-Italic"),
    "courier": ("Courier", "Courier-Bold", "Courier-Oblique"),
}

SUPPORTED_TEMPLATES = ["Simple", "Modern", "Minimal", "Fresher", "Technical"]
SUPPORTED_FONTS = ["Helvetica", "Arial", "Calibri", "Times New Roman", "Georgia"]

def clean_text(val: Any) -> str:
    """Escape XML special characters for ReportLab Paragraphs."""
    if val is None:
        return ""
    text = str(val).strip()
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return text


def build_resume_pdf(
    data: Dict[str, Any] = None,
    template_name: str = "Simple",
    font_family: str = "Helvetica",
    template_id: str = None,
    resume_data: Dict[str, Any] = None,
    primary_color: str = None,
    **kwargs
) -> bytes:
    """
    Compiles candidate data into a professional ATS-friendly A4 PDF.
    Returns the PDF bytes.
    """
    if data is None:
        data = resume_data or {}
    if template_id and (template_name == "Simple" or not template_name):
        template_name = template_id

    buffer = io.BytesIO()
    
    # 20mm margins (~0.78 in)
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm
    )

    norm_font_key = (font_family or "Helvetica").strip().lower()
    regular_font, bold_font, italic_font = FONT_FAMILY_MAP.get(
        norm_font_key, ("Helvetica", "Helvetica-Bold", "Helvetica-Oblique")
    )

    styles = getSampleStyleSheet()

    # Base Colors
    if primary_color and re.match(r"^#[0-9a-fA-F]{6}$", primary_color):
        primary_col = colors.HexColor(primary_color)
    else:
        primary_col = colors.HexColor("#1e3a8a") if template_name in ["Modern", "Technical"] else colors.HexColor("#0f172a")

    secondary_color = colors.HexColor("#475569")
    text_color = colors.HexColor("#1e293b")
    line_color = colors.HexColor("#cbd5e1")
    accent_bg = colors.HexColor("#f1f5f9")

    # Custom Paragraph Styles
    title_style = ParagraphStyle(
        "ResumeTitle",
        fontName=bold_font,
        fontSize=20 if template_name == "Modern" else 18,
        leading=24,
        textColor=primary_col,
        alignment=0 if template_name != "Simple" else 1 # Center for Simple
    )

    subtitle_style = ParagraphStyle(
        "ResumeSubtitle",
        fontName=regular_font,
        fontSize=10,
        leading=14,
        textColor=secondary_color,
        alignment=0 if template_name != "Simple" else 1
    )

    contact_style = ParagraphStyle(
        "ResumeContact",
        fontName=regular_font,
        fontSize=9,
        leading=13,
        textColor=secondary_color,
        alignment=0 if template_name != "Simple" else 1
    )

    section_heading_style = ParagraphStyle(
        "ResumeSectionHeading",
        fontName=bold_font,
        fontSize=11.5,
        leading=16,
        textColor=primary_col,
        spaceBefore=8,
        spaceAfter=3,
        keepWithNext=True
    )

    item_title_style = ParagraphStyle(
        "ResumeItemTitle",
        fontName=bold_font,
        fontSize=10,
        leading=14,
        textColor=text_color
    )

    item_meta_style = ParagraphStyle(
        "ResumeItemMeta",
        fontName=italic_font,
        fontSize=9,
        leading=13,
        textColor=secondary_color
    )

    body_style = ParagraphStyle(
        "ResumeBody",
        fontName=regular_font,
        fontSize=9,
        leading=13.5,
        textColor=text_color,
        spaceAfter=2
    )

    bullet_style = ParagraphStyle(
        "ResumeBullet",
        fontName=regular_font,
        fontSize=8.8,
        leading=13,
        textColor=text_color,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=2
    )

    story = []

    # Extract Data Fields (handle nested personal_info or flat dict)
    personal = data.get("personal_info", {})
    name = clean_text(
        personal.get("name") or personal.get("full_name") or 
        data.get("full_name") or data.get("name") or "Candidate Name"
    )
    email = clean_text(personal.get("email") or data.get("email", ""))
    phone = clean_text(personal.get("phone") or data.get("phone", ""))
    location = clean_text(personal.get("location") or data.get("location", ""))
    linkedin = clean_text(personal.get("linkedin") or data.get("linkedin", ""))
    github = clean_text(personal.get("github") or data.get("github", ""))
    summary = clean_text(data.get("summary") or data.get("career_objective", ""))

    education_list = data.get("education", [])
    skills_list = data.get("skills", [])
    projects_list = data.get("projects", [])
    experience_list = data.get("experience") or data.get("internships", [])
    certifications_list = data.get("certifications", [])
    achievements_list = data.get("achievements", [])
    languages_list = data.get("languages", [])

    # Format Contact Line
    contact_parts = [p for p in [email, phone, location, linkedin, github] if p]
    contact_str = " | ".join(contact_parts)

    # 
    # HEADER SECTION
    # 
    story.append(Paragraph(name, title_style))
    story.append(Spacer(1, 2))

    if contact_str:
        story.append(Paragraph(contact_str, contact_style))
        story.append(Spacer(1, 4))

    if template_name in ["Simple", "Modern", "Technical", "Fresher"]:
        story.append(HRFlowable(width="100%", thickness=1, color=primary_col, spaceBefore=4, spaceAfter=8))
    else:
        story.append(Spacer(1, 6))

    # 
    # PROFESSIONAL SUMMARY / CAREER OBJECTIVE
    # 
    if summary:
        story.append(Paragraph("PROFESSIONAL SUMMARY", section_heading_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=line_color, spaceBefore=1, spaceAfter=4))
        story.append(Paragraph(summary, body_style))
        story.append(Spacer(1, 6))

    # Helper function for rendering sections
    def render_education():
        if not education_list:
            return
        story.append(Paragraph("EDUCATION", section_heading_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=line_color, spaceBefore=1, spaceAfter=4))
        for edu in education_list:
            degree = clean_text(edu.get("degree") or edu.get("qualification", ""))
            institution = clean_text(edu.get("institution") or edu.get("college") or edu.get("school", ""))
            year = clean_text(edu.get("year") or edu.get("graduation_year", ""))
            score = clean_text(edu.get("score") or edu.get("cgpa") or edu.get("percentage", ""))

            title_row = f"<b>{degree}</b>" if degree else ""
            meta_parts = [p for p in [institution, year, f"Score/CGPA: {score}" if score else ""] if p]
            meta_row = " — ".join(meta_parts)

            story.append(Paragraph(title_row, item_title_style))
            if meta_row:
                story.append(Paragraph(meta_row, item_meta_style))
            story.append(Spacer(1, 3))
        story.append(Spacer(1, 4))

    def render_skills():
        if not skills_list:
            return
        story.append(Paragraph("SKILLS &amp; EXPERTISE" if template_name == "Fresher" else "TECHNICAL &amp; CORE SKILLS", section_heading_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=line_color, spaceBefore=1, spaceAfter=4))

        generic_cat_names = {"category", "category 1", "category 2", "category 3", "technical skills", "skills", "general", "general category", "technical category", "skill category", "core skills"}

        if isinstance(skills_list, str):
            clean_items = [clean_text(s.strip()) for s in re.split(r'[,•\n]+', skills_list) if s.strip()]
            if clean_items:
                story.append(Paragraph(" • ".join(clean_items), body_style))
        elif isinstance(skills_list, list):
            clean_items = []
            for item in skills_list:
                if isinstance(item, str):
                    for sub in re.split(r'[,•\n]+', item):
                        if sub.strip():
                            clean_items.append(clean_text(sub.strip()))
            if clean_items:
                story.append(Paragraph(" • ".join(clean_items), body_style))
        elif isinstance(skills_list, dict):
            # Check if all keys are generic
            keys_lower = [str(k).strip().lower() for k in skills_list.keys()]
            is_all_generic = all(k in generic_cat_names or not k for k in keys_lower)

            if is_all_generic:
                # Flatten everything into a clean natural skill list
                clean_items = []
                for val in skills_list.values():
                    if isinstance(val, str):
                        for sub in re.split(r'[,•\n]+', val):
                            if sub.strip():
                                clean_items.append(clean_text(sub.strip()))
                    elif isinstance(val, list):
                        for sub in val:
                            if isinstance(sub, str) and sub.strip():
                                clean_items.append(clean_text(sub.strip()))
                if clean_items:
                    story.append(Paragraph(" • ".join(clean_items), body_style))
            else:
                for category_name, cat_skills in skills_list.items():
                    c_name = str(category_name).strip()
                    if not c_name:
                        continue
                    if isinstance(cat_skills, str):
                        sub_items = [clean_text(s.strip()) for s in re.split(r'[,•\n]+', cat_skills) if s.strip()]
                        s_str = " • ".join(sub_items) if template_name != "Technical" else ", ".join(sub_items)
                    elif isinstance(cat_skills, list):
                        sub_items = [clean_text(str(s).strip()) for s in cat_skills if str(s).strip()]
                        s_str = " • ".join(sub_items) if template_name != "Technical" else ", ".join(sub_items)
                    else:
                        s_str = clean_text(str(cat_skills))

                    if s_str:
                        if c_name.lower() in generic_cat_names:
                            story.append(Paragraph(s_str, body_style))
                        else:
                            story.append(Paragraph(f"<b>{clean_text(c_name)}:</b> {s_str}", body_style))
        story.append(Spacer(1, 6))

    def render_projects():
        if not projects_list:
            return
        heading_title = "ACADEMIC &amp; CAPSTONE PROJECTS" if template_name == "Fresher" else "TECHNICAL PROJECTS"
        story.append(Paragraph(heading_title, section_heading_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=line_color, spaceBefore=1, spaceAfter=4))
        for proj in projects_list:
            p_title = clean_text(proj.get("title") or proj.get("name", "Project"))
            p_tech = clean_text(proj.get("technologies") or proj.get("tech_stack", ""))
            p_desc = clean_text(proj.get("description", ""))
            p_link = clean_text(proj.get("link") or proj.get("url", ""))

            header_text = f"<b>{p_title}</b>"
            if p_tech:
                header_text += f" <font color='#475569'>({p_tech})</font>"
            if p_link:
                header_text += f" — <i><font color='#2563eb'>{p_link}</font></i>"

            story.append(Paragraph(header_text, item_title_style))
            if p_desc:
                # Split description into bullet points if multi-line or long
                lines = [l.strip().lstrip('•-* ') for l in p_desc.splitlines() if l.strip()]
                if len(lines) > 1:
                    for l in lines:
                        story.append(Paragraph(f"• {clean_text(l)}", bullet_style))
                else:
                    story.append(Paragraph(p_desc, body_style))
            story.append(Spacer(1, 4))
        story.append(Spacer(1, 4))

    def render_experience():
        if not experience_list:
            return
        story.append(Paragraph("WORK EXPERIENCE &amp; INTERNSHIPS", section_heading_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=line_color, spaceBefore=1, spaceAfter=4))
        for exp in experience_list:
            role = clean_text(exp.get("role") or exp.get("position") or exp.get("title", ""))
            company = clean_text(exp.get("company") or exp.get("organization", ""))
            duration = clean_text(exp.get("duration") or exp.get("period", ""))
            desc = clean_text(exp.get("description", ""))

            title_row = f"<b>{role}</b>"
            if company:
                title_row += f" — <i>{company}</i>"
            if duration:
                title_row += f" <font color='#64748b'>({duration})</font>"

            story.append(Paragraph(title_row, item_title_style))
            if desc:
                lines = [l.strip().lstrip('•-* ') for l in desc.splitlines() if l.strip()]
                if len(lines) > 1:
                    for l in lines:
                        story.append(Paragraph(f"• {clean_text(l)}", bullet_style))
                else:
                    story.append(Paragraph(desc, body_style))
            story.append(Spacer(1, 4))
        story.append(Spacer(1, 4))

    def render_certifications():
        if not certifications_list:
            return
        story.append(Paragraph("CERTIFICATIONS &amp; LICENSES", section_heading_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=line_color, spaceBefore=1, spaceAfter=4))
        for cert in certifications_list:
            c_name = clean_text(cert if isinstance(cert, str) else cert.get("name") or cert.get("title", ""))
            c_issuer = clean_text(cert.get("issuer", "") if isinstance(cert, dict) else "")
            c_year = clean_text(cert.get("year", "") if isinstance(cert, dict) else "")
            
            line = f"• <b>{c_name}</b>"
            if c_issuer:
                line += f" — {c_issuer}"
            if c_year:
                line += f" ({c_year})"
            story.append(Paragraph(line, bullet_style))
        story.append(Spacer(1, 4))

    def render_achievements_and_languages():
        if achievements_list:
            story.append(Paragraph("ACHIEVEMENTS &amp; HONORS", section_heading_style))
            story.append(HRFlowable(width="100%", thickness=0.5, color=line_color, spaceBefore=1, spaceAfter=4))
            for ach in achievements_list:
                ach_text = clean_text(ach if isinstance(ach, str) else ach.get("title", ""))
                story.append(Paragraph(f"• {ach_text}", bullet_style))
            story.append(Spacer(1, 4))

        if languages_list:
            story.append(Paragraph("LANGUAGES", section_heading_style))
            story.append(HRFlowable(width="100%", thickness=0.5, color=line_color, spaceBefore=1, spaceAfter=4))
            lang_str = ", ".join([clean_text(l if isinstance(l, str) else l.get("name", "")) for l in languages_list if l])
            story.append(Paragraph(lang_str, body_style))
            story.append(Spacer(1, 4))

    # 
    # TEMPLATE-SPECIFIC STRUCTURAL ORDERING
    # 
    if template_name == "Fresher":
        # Fresher order: Summary -> Education -> Projects -> Skills -> Certifications -> Experience -> Achievements
        render_education()
        render_projects()
        render_skills()
        render_certifications()
        render_experience()
        render_achievements_and_languages()

    elif template_name == "Technical":
        # Technical order: Summary -> Skills (top) -> Projects -> Experience -> Education -> Certifications
        render_skills()
        render_projects()
        render_experience()
        render_education()
        render_certifications()
        render_achievements_and_languages()

    elif template_name == "Minimal":
        # Minimal order: Summary -> Experience -> Projects -> Skills -> Education
        render_experience()
        render_projects()
        render_skills()
        render_education()
        render_certifications()
        render_achievements_and_languages()

    else:
        # Simple / Modern order: Summary -> Skills -> Experience -> Projects -> Education -> Certifications
        render_skills()
        render_experience()
        render_projects()
        render_education()
        render_certifications()
        render_achievements_and_languages()

    # Build Document
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

generate_resume_pdf_bytes = build_resume_pdf

