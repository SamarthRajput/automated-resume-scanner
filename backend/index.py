import os
import re
import fitz  
import spacy
import docx
import time
from pathlib import Path
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
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Load SpaCy NLP model
nlp = spacy.load("en_core_web_sm")

# Skills database
SKILLS = {
    "Python", "Java", "JavaScript", "React", "Node.js", "SQL", "AWS",
    "Docker", "Machine Learning", "Data Science", "Flask", "Django",
    "MongoDB", "PostgreSQL", "Git", "HTML", "CSS", "TypeScript",
    "Kubernetes", "C++", "C#", "Ruby", "Go", "Swift", "Kotlin",
    "TensorFlow", "PyTorch", "NLP", "Tableau", "Power BI", "Excel",
    "Angular", "Vue.js", "Spring Boot", "Hibernate", "REST APIs",
    "GraphQL", "Azure", "GCP", "Spark", "Hadoop", "Kafka", "Jenkins",
    "Ansible", "Terraform", "Linux", "Shell Scripting", "Unity", "Unreal Engine"
}

# Resume text extractors
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

# Info extractors
def extract_contact_info(text):
    email = re.search(r'[\w\.-]+@[\w\.-]+', text)
    phone = re.search(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
    return {
        'email': email.group(0) if email else None,
        'phone': phone.group(0) if phone else None
    }

def extract_skills(text):
    text_lower = text.lower()
    return [skill for skill in SKILLS if skill.lower() in text_lower]

# Web scraping
def scrape_indian_jobs(skills, page=1):
    if not skills:
        app.logger.info("No skills provided for job scraping.")
        return []

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    driver = None
    try:
        # FIX: Ensure correct chromedriver is used on Windows
        driver_path = ChromeDriverManager().install()
        driver_exe = str(Path(driver_path).parent / "chromedriver.exe")

        driver = webdriver.Chrome(
            service=Service(driver_exe),
            options=options
        )

        job_listings = []
        for skill in skills[:3]:  # Limit to top 3 skills
            url = f"https://www.linkedin.com/jobs/search/?keywords={skill}&location=India&start={(page-1)*25}"
            app.logger.info(f"Scraping URL: {url}")
            driver.get(url)
            time.sleep(3)

            soup = BeautifulSoup(driver.page_source, 'html.parser')
            jobs = soup.find_all("div", class_="base-card")
            app.logger.info(f"Jobs found for '{skill}': {len(jobs)}")

            for job in jobs:
                location = job.find("span", class_="job-search-card__location")
                if location and "India" in location.text:
                    title = job.find("h3", class_="base-search-card__title")
                    company = job.find("h4", class_="base-search-card__subtitle")
                    link = job.find("a", class_="base-card__full-link")

                    if all([title, company, link]):
                        job_listings.append({
                            "title": title.text.strip(),
                            "company": company.text.strip(),
                            "url": link['href'].split('?')[0],
                            "location": location.text.strip()
                        })

        return job_listings[:20]
    except Exception as e:
        app.logger.error(f"Scraping error: {str(e)}")
        return []
    finally:
        if driver:
            driver.quit()

# Upload endpoint
@app.route('/upload', methods=['POST'])
def upload_resume():
    if 'resume' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['resume']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        if filename.endswith('.pdf'):
            text = extract_text_from_pdf(filepath)
        else:
            text = extract_text_from_docx(filepath)

        contact_info = extract_contact_info(text)
        skills = extract_skills(text)
        jobs = scrape_indian_jobs(skills)

        return jsonify({
            "success": True,
            "contact": contact_info,
            "skills": skills,
            "jobs": jobs,
            "next_page": 2
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)

# Jobs pagination endpoint
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

# Run server
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
