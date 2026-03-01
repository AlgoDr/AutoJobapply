import logging
from io import BytesIO
from fpdf import FPDF
from typing import Optional

from storage_helper import upload_bytes_to_gcs
from firestore_helper import get_resume_url, save_resume_url, get_user_profile, set_user_profile

logger = logging.getLogger(__name__)

BUCKET = None  # storage_helper uses env var internally; no need here

def render_simple_pdf(name: str, role: str, profile: dict) -> bytes:
    """
    Create a simple PDF bytes with name/role and basic profile info.
    Replace with your templating engine later.
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=16)
    pdf.cell(0, 10, txt=f"{name}", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 8, txt=f"Target role: {role}", ln=True)
    pdf.ln(6)
    pdf.set_font("Arial", size=11)
    # include profile sections if present
    summary = profile.get("summary") if profile else None
    if summary:
        pdf.multi_cell(0, 6, txt=f"Summary: {summary}")
    skills = profile.get("skills") if profile else None
    if skills:
        pdf.ln(3)
        pdf.cell(0, 6, txt="Skills:", ln=True)
        pdf.multi_cell(0, 6, txt=", ".join(skills) if isinstance(skills, (list, tuple)) else str(skills))
    # return bytes
    buf = BytesIO()
    pdf.output(buf)
    return buf.getvalue()

def get_resume_url_for_user(user_id: str) -> Optional[str]:
    """Return existing resume URL from Firestore if any"""
    return get_resume_url(user_id)

def ensure_resume_for_user(user_id: str) -> str:
    """
    If the user has a resume URL saved in Firestore, return it.
    Otherwise generate a simple PDF and upload to GCS, save URL, and return signed URL.
    """
    url = get_resume_url_for_user(user_id)
    if url:
        logger.info("Found existing resume for %s: %s", user_id, url)
        return url

    profile = get_user_profile(user_id) or {}
    name = profile.get("name", "Unknown")
    role = profile.get("role", "Software Engineer")

    pdf_bytes = render_simple_pdf(name, role, profile)
    destination = f"resumes/{user_id}-{int(__import__('time').time())}-resume.pdf"
    # upload_bytes_to_gcs returns a signed URL or gs:// path
    public_url = upload_bytes_to_gcs(os.getenv("GCS_BUCKET"), destination, pdf_bytes, content_type="application/pdf")
    save_resume_url(user_id, public_url)
    # optionally also save name/role if missing
    if not profile.get("name") or not profile.get("role"):
        set_user_profile(user_id, {"name": name, "role": role})
    return public_url
