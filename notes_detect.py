import streamlit as st
import difflib
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import cv2
import numpy as np
from io import BytesIO

# ----------------- Set Tesseract path -----------------
pytesseract.pytesseract.tesseract_cmd = r"C:\TESSERACT\tesseract.exe"

# ----------------- Extract Text from PDF -----------------
def extract_text_from_pdf(file_bytes):
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text("text") + "\n"
    return text.strip()

# ----------------- Extract Text from Image -----------------
def extract_text_from_image(file_bytes):
    img = Image.open(BytesIO(file_bytes)).convert("RGB")
    img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 3)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    text = pytesseract.image_to_string(thresh, lang="eng")
    return text.strip()

# ----------------- Extract text from any file -----------------
def extract_text_from_file(uploaded_file):
    file_bytes = uploaded_file.read()
    ext = uploaded_file.name.lower().split(".")[-1]
    
    if ext == "pdf":
        return extract_text_from_pdf(file_bytes)
    elif ext in ["jpg", "jpeg", "png"]:
        return extract_text_from_image(file_bytes)
    elif ext == "txt":
        return file_bytes.decode("utf-8")
    else:
        st.warning(f"Unsupported file type: {uploaded_file.name}")
        return ""

# ----------------- Compare Notes -----------------
def compare_notes(original_text, student_text):
    original_lines = original_text.splitlines()
    student_lines = student_text.splitlines()
    diff = difflib.ndiff(original_lines, student_lines)

    results = ["\n--- Comparison Result ---\n"]
    for line in diff:
        if line.startswith("- "):
            results.append(f"❌ Missing in student notes: {line[2:]}")
        elif line.startswith("+ "):
            results.append(f"⚠️ Extra/Incorrect in student notes: {line[2:]}")
        elif line.startswith("? "):
            results.append(f"🔍 Possible spelling issue indicator: {line[2:]}")
    
    return "\n".join(results)

# ----------------- Streamlit App -----------------
st.title("📝 Notes Comparison Tool")

# Upload teacher files
teacher_files = st.file_uploader(
    "Upload Teacher Notes (PDF, Image, or TXT)",
    accept_multiple_files=True,
    type=["pdf", "jpg", "jpeg", "png", "txt"]
)

# Upload student files
student_files = st.file_uploader(
    "Upload Student Notes (PDF, Image, or TXT)",
    accept_multiple_files=True,
    type=["pdf", "jpg", "jpeg", "png", "txt"]
)

# Compare button
if st.button("Compare Notes"):
    if not teacher_files or not student_files:
        st.error("Please upload both teacher and student files.")
    else:
        with st.spinner("Processing files, please wait..."):
            # Combine teacher text
            original_text = ""
            for file in teacher_files:
                original_text += extract_text_from_file(file) + "\n"
            
            # Combine student text
            student_text = ""
            for file in student_files:
                student_text += extract_text_from_file(file) + "\n"
            
            # Compare
            report = compare_notes(original_text, student_text)
        
        st.success("✅ Comparison complete!")
        st.text_area("📄 Comparison Report", report, height=400)

        # Allow download
        st.download_button(
            "Download Report",
            data=report,
            file_name="comparison_report.txt",
            mime="text/plain"
        )
