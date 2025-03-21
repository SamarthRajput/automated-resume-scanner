import fitz  # PyMuPDF
import re
import spacy
import docx
import requests
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox, Toplevel, scrolledtext
from sklearn.feature_extraction.text import TfidfVectorizer
from fuzzywuzzy import fuzz
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

# Load NLP model
nlp = spacy.load("en_core_web_sm")

# Predefined list of skills (extended)
skill_keywords = set([
    "Python", "Java", "C++", "Machine Learning", "Deep Learning", "Data Science", "SQL", "React", 
    "Node.js", "Django", "Flask", "TensorFlow", "Keras", "NLP", "Pandas", "NumPy", "Git", "AWS",
    "JavaScript", "TypeScript", "HTML", "CSS", "MongoDB", "NextJs", "PostgreSQL", "Prisma", "CI/CD",
    "VS Code", "Google Cloud Platform", "Cloudflare", "Turbo Repo", "Docker", "Next Auth", "JWT", 
    "Recoil", "Aceternity UI", "Mongoose", "TailwindCSS"
])

def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file."""
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text("text") + "\n"
    return text

def extract_text_from_docx(docx_path):
    """Extracts text from a DOCX file."""
    doc = docx.Document(docx_path)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text

def extract_email(text):
    """Extract email from text using regex."""
    email_pattern = r'[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+'
    matches = re.findall(email_pattern, text)
    return matches[0] if matches else None

def extract_phone(text):
    """Extract phone number from text using regex."""
    phone_pattern = r'\b\d{10}\b|\(\d{3}\)\s?\d{3}-\d{4}'
    matches = re.findall(phone_pattern, text)
    return matches[0] if matches else None

def extract_skills_spacy(text):
    """Extracts relevant skills using NLP with spaCy."""
    doc = nlp(text)
    found_skills = set()
    for token in doc:
        if token.text in skill_keywords:
            found_skills.add(token.text)
    return list(found_skills)

def scrape_jobs(skills):
    """Scrapes job listings based on extracted skills."""
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    job_links = []
    
    for skill in skills:
        search_url = f"https://www.linkedin.com/jobs/search/?keywords={skill}"
        driver.get(search_url)
        time.sleep(5)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        job_elements = soup.find_all("a", class_="base-card__full-link")
        for job in job_elements[:5]:  # Get top 5 jobs per skill
            job_links.append(job['href'])
    
    driver.quit()
    return job_links

def parse_resume(file_path, file_type="pdf"):
    """Main function to parse resume and extract relevant information."""
    text = extract_text_from_pdf(file_path) if file_type == "pdf" else extract_text_from_docx(file_path)
    email = extract_email(text)
    phone = extract_phone(text)
    skills = extract_skills_spacy(text)
    jobs = scrape_jobs(skills) if skills else []
    
    return {
        "Email": email,
        "Phone": phone,
        "Skills": skills,
        "Jobs": jobs
    }

def browse_file():
    """Function to open file dialog and select resume."""
    file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf"), ("Word Documents", "*.docx")])
    if file_path:
        file_label.config(text=f"Selected File: {file_path}")
        file_extension = file_path.split(".")[-1]
        file_type = "pdf" if file_extension == "pdf" else "docx"
        result = parse_resume(file_path, file_type)
        display_results(result)

def display_results(result):
    """Function to display extracted information in a new GUI window."""
    result_window = Toplevel(root)
    result_window.title("Extracted Resume Details")
    result_window.geometry("600x400")
    
    result_text = scrolledtext.ScrolledText(result_window, height=20, width=70)
    result_text.pack(pady=10)
    
    result_text.insert(tk.END, f"Email: {result['Email']}\n")
    result_text.insert(tk.END, f"Phone: {result['Phone']}\n")
    result_text.insert(tk.END, f"Skills: {', '.join(result['Skills']) if result['Skills'] else 'No skills found'}\n")
    
    result_text.insert(tk.END, "\nJob Listings:\n")
    for job in result['Jobs']:
        result_text.insert(tk.END, f"{job}\n")
    
    close_button = tk.Button(result_window, text="Close", command=result_window.destroy, font=("Arial", 12))
    close_button.pack(pady=5)

# GUI Setup
root = tk.Tk()
root.title("Resume Parser")
root.geometry("500x200")

tk.Label(root, text="Resume Parser", font=("Arial", 16)).pack(pady=10)
file_label = tk.Label(root, text="No file selected", font=("Arial", 10))
file_label.pack(pady=5)

browse_button = tk.Button(root, text="Browse Resume", command=browse_file, font=("Arial", 12))
browse_button.pack(pady=10)

root.mainloop()
