import os
import re
import fitz
import spacy
import docx
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# Configuration
app.config['UPLOAD_FOLDER'] = './uploads'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Load NLP model
nlp = spacy.load("en_core_web_sm")

# Skills database
SKILLS = {
    "Python", "Java", "JavaScript", "React", "Node.js", "SQL", "AWS",
    "Docker", "Machine Learning", "Data Science", "Flask", "Django",
    "MongoDB", "PostgreSQL", "Git", "HTML", "CSS", "TypeScript"
}

def extract_text_from_pdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        return " ".join(page.get_text() for page in doc)
    except Exception as e:
        raise Exception(f"PDF extraction failed: {str(e)}")

def extract_text_from_docx(docx_path):
    try:
        doc = docx.Document(docx_path)
        return " ".join(para.text for para in doc.paragraphs)
    except Exception as e:
        raise Exception(f"DOCX extraction failed: {str(e)}")

def extract_contact_info(text):
    email = re.search(r'[\w\.-]+@[\w\.-]+', text)
    phone = re.search(r'(\+?\d{1,3}[-\.\s]?)?\(?\d{3}\)?[-\.\s]?\d{3}[-\.\s]?\d{4}', text)
    return {
        'email': email.group(0) if email else None,
        'phone': phone.group(0) if phone else None
    }

def extract_skills(text):
    text_lower = text.lower()
    return [skill for skill in SKILLS if skill.lower() in text_lower]

def scrape_indian_jobs(skills, page=1):
    if not skills:
        return []
    
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    
    driver = None
    try:
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        
        job_listings = []
        for skill in skills[:3]:  # Limit to top 3 skills
            url = (f"https://www.linkedin.com/jobs/search/"
                  f"?keywords={skill}&location=India&start={(page-1)*25}")
            driver.get(url)
            time.sleep(3)
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            jobs = soup.find_all("div", class_="base-card")
            
            for job in jobs:
                # Ensure it's an India-based job
                location = job.find("span", class_="job-search-card__location")
                if location and "India" in location.text:
                    title = job.find("h3", class_="base-search-card__title")
                    company = job.find("h4", class_="base-search-card__subtitle")
                    link = job.find("a", class_="base-card__full-link")
                    
                    if all([title, company, link]):
                        job_listings.append({
                            "title": title.text.strip(),
                            "company": company.text.strip(),
                            "url": link['href'].split('?')[0],  # Clean URL
                            "location": location.text.strip()
                        })
        
        return job_listings[:20]  # Limit to 20 jobs per request
    except Exception as e:
        app.logger.error(f"Scraping error: {str(e)}")
        return []
    finally:
        if driver:
            driver.quit()

@app.route('/upload', methods=['POST'])
def upload_resume():
    if 'resume' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['resume']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    try:
        # Save file temporarily
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Extract text
        if filename.endswith('.pdf'):
            text = extract_text_from_pdf(filepath)
        else:
            text = extract_text_from_docx(filepath)
        
        # Process resume
        contact_info = extract_contact_info(text)
        skills = extract_skills(text)
        jobs = scrape_indian_jobs(skills)
        
        return jsonify({
            "success": True,
            "contact": contact_info,
            "skills": skills,
            "jobs": jobs,
            "next_page": 2  # Initial pagination
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'filepath' in locals() and os.path.exists(filepath):
            os.remove(filepath)

@app.route('/jobs', methods=['GET'])
def get_more_jobs():
    skills = request.args.get('skills', '').split(',')
    page = int(request.args.get('page', 2))
    
    try:
        jobs = scrape_indian_jobs(skills, page)
        return jsonify({
            "success": True,
            "jobs": jobs,
            "next_page": page + 1
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)


