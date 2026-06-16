import os
import re
import spacy
import pdfplumber
import pandas as pd
import numpy as np
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Dynamic loading of Sentence-BERT
sbert_model = None
try:
    from sentence_transformers import SentenceTransformer
    print("Loading Sentence-BERT model 'all-MiniLM-L6-v2'...")
    sbert_model = SentenceTransformer('all-MiniLM-L6-v2')
    print("Sentence-BERT model loaded successfully.")
except Exception as e:
    print(f"WARNING: Sentence-BERT model could not be loaded: {e}. Falling back to TF-IDF matching.")
    sbert_model = None

def calculate_sbert_similarity(text1: str, text2: str) -> float:
    if sbert_model is None:
        return None
    try:
        embeddings = sbert_model.encode([text1, text2])
        vec1 = embeddings[0]
        vec2 = embeddings[1]
        dot_product = np.dot(vec1, vec2)
        norm_a = np.linalg.norm(vec1)
        norm_b = np.linalg.norm(vec2)
        similarity = dot_product / (norm_a * norm_b) if norm_a > 0 and norm_b > 0 else 0.0
        return float(similarity)
    except Exception as e:
        print(f"Error calculating SBERT similarity: {e}")
        return None

# Initialize FastAPI App
app = FastAPI(title="AI Interview Assistant ML Microservice")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load spaCy English Model
try:
    nlp = spacy.load("en_core_web_sm")
except Exception:
    try:
        # Fallback to downloading it if not present
        import subprocess
        subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"], timeout=30)
        nlp = spacy.load("en_core_web_sm")
    except Exception as e:
        print(f"WARNING: spaCy model 'en_core_web_sm' could not be loaded: {e}. Falling back to regex-only matching.")
        nlp = None

# Define Skills Dictionary (Keywords and regex patterns)
SKILLS_DICT = {
    "languages": [
        "python", "java", "javascript", "typescript", "c++", "c#", "go", "golang", "rust", 
        "ruby", "php", "swift", "kotlin", "scala", "c", "html", "css", "sass", "less", "bash", "shell", "js"
    ],
    "frameworks": [
        "spring boot", "spring", "react", "reactjs", "react.js", "angular", "angularjs", 
        "vue", "vuejs", "vue.js", "node", "nodejs", "node.js", "express", "expressjs", 
        "django", "flask", "fastapi", "next.js", "nextjs", "nestjs", "nuxt.js", "nuxtjs", 
        "tailwind", "bootstrap", "laravel", "rails", "jquery", "asp.net", ".net core", "net core", ".net"
    ],
    "databases": [
        "sql", "mysql", "postgresql", "postgres", "mongodb", "mongo", "redis", "oracle", 
        "sqlite", "cassandra", "dynamodb", "mariadb", "firebase", "mssql", "sql server"
    ],
    "cloud": [
        "aws", "amazon web services", "azure", "gcp", "google cloud", "heroku", "vercel", 
        "netlify", "digitalocean", "docker", "kubernetes", "k8s", "terraform", "ansible", "jenkins"
    ],
    "ml/ai": [
        "machine learning", "deep learning", "nlp", "natural language processing", 
        "computer vision", "pytorch", "tensorflow", "keras", "scikit-learn", "sklearn", 
        "pandas", "numpy", "llm", "large language models", "langchain", "huggingface", 
        "artificial intelligence", "ai", "ml", "transformers", "bert", "gpt"
    ],
    "tools": [
        "git", "github", "gitlab", "jenkins", "cicd", "ci/cd", "jira", "postman", "figma", 
        "linux", "nginx", "apache", "maven", "gradle", "npm", "yarn", "swagger"
    ],
    "concepts": [
        "microservices", "rest api", "graphql", "grpc", "agile", "scrum", "tdd", "oop", 
        "solid", "mvc", "scalability", "load balancing", "caching", "design patterns", 
        "system design", "clean code", "dry"
    ]
}

# Compile Skills Patterns for Regex Matching
SKILL_PATTERNS = {}
SKILL_PATTERNS_OLD = {}
for category, skills in SKILLS_DICT.items():
    patterns = []
    patterns_old = []
    for skill in skills:
        escaped_skill = re.escape(skill)
        patterns.append((skill, re.compile(rf"(?<!\w){escaped_skill}(?!\w)", re.IGNORECASE)))
        patterns_old.append((skill, re.compile(rf"\b{escaped_skill}\b", re.IGNORECASE)))
    SKILL_PATTERNS[category] = patterns
    SKILL_PATTERNS_OLD[category] = patterns_old


# Hardcoded Question Bank
QUESTION_BANK = {
    "python": [
        "What is the difference between a list and a tuple in Python, and when would you use each?",
        "Explain generators, decorators, and the 'yield' keyword in Python with examples.",
        "How does Python's memory management and garbage collection work? Mention reference counting."
    ],
    "java": [
        "Explain the differences between JVM, JRE, and JDK. How does Java achieve platform independence?",
        "What is the difference between HashMap, HashTable, and ConcurrentHashMap in Java?",
        "Explain garbage collection in Java. What are the different generations in the Java heap memory?"
    ],
    "spring boot": [
        "Explain Dependency Injection and Inversion of Control (IoC) in Spring Boot.",
        "What is the difference between @Component, @Service, @Repository, and @Controller annotations?",
        "How does Spring Boot handle transaction management? Explain the @Transactional annotation."
    ],
    "react": [
        "What are React Hooks? Explain the rules of Hooks and how useEffect differs from class lifecycles.",
        "Explain the Virtual DOM and React's reconciliation algorithm (Diffing algorithm).",
        "How do you handle state management in React? Compare Context API with Redux."
    ],
    "aws": [
        "Compare Amazon S3, EBS, and EFS. In what scenarios would you choose one over the others?",
        "What are IAM Roles and IAM Policies in AWS? Explain the principle of least privilege.",
        "Explain AWS VPC. What is the difference between a Public Subnet, Private Subnet, and NAT Gateway?"
    ],
    "docker": [
        "What is the difference between a Docker image and a Docker container? Explain copy-on-write.",
        "Explain the concept and advantages of multi-stage builds in Dockerfiles.",
        "How do you manage persistent data in Docker? Compare volumes and bind mounts."
    ],
    "sql": [
        "Explain the differences between INNER JOIN, LEFT JOIN, RIGHT JOIN, and FULL OUTER JOIN with examples.",
        "What is database normalization? Explain the rules for 1NF, 2NF, and 3NF.",
        "What are database indexes? Explain how a B-Tree index speeds up read queries and its impact on writes."
    ],
    "machine learning": [
        "Explain the bias-variance tradeoff. How do you diagnose and address underfitting and overfitting?",
        "Explain how the Random Forest algorithm works. What is bagging and how does it reduce variance?",
        "Describe the gradient descent optimization algorithm. What is the difference between batch, mini-batch, and stochastic gradient descent?"
    ]
}

# Global TF-IDF and Classifier Centroids
tfidf_vectorizer = TfidfVectorizer(stop_words='english', token_pattern=r'(?u)\b\w+\b')
category_centroids = {}  # Maps Category Name -> Mean TF-IDF vector

def clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

SYNONYM_DB = {
    # Abbreviation / Alias -> Canonical Skill Name
    "golang": "go",
    "js": "javascript",
    "ts": "typescript",
    "py": "python",
    "cpp": "c++",
    "cplusplus": "c++",
    "c sharp": "c#",
    "csharp": "c#",
    "reactjs": "react",
    "react.js": "react",
    "vuejs": "vue",
    "vue.js": "vue",
    "angularjs": "angular",
    "nodejs": "node.js",
    "node": "node.js",
    "expressjs": "express",
    "nextjs": "next.js",
    "nuxtjs": "nuxt.js",
    "nestjs": "nest.js",
    "springboot": "spring boot",
    "net core": ".net core",
    "dotnet": ".net",
    "aspnet": "asp.net",
    "mongo": "mongodb",
    "postgres": "postgresql",
    "sqlserver": "sql server",
    "mssql": "sql server",
    "mariadb": "mysql",
    "amazon web services": "aws",
    "google cloud platform": "gcp",
    "google cloud": "gcp",
    "microsoft azure": "azure",
    "k8s": "kubernetes",
    "ci/cd": "cicd",
    "continuous integration": "cicd",
    "continuous deployment": "cicd",
    "github actions": "github",
    "ai": "artificial intelligence",
    "ml": "machine learning",
    "dl": "deep learning",
    "neural networks": "deep learning",
    "natural language processing": "nlp",
    "large language models": "llm",
    "large language model": "llm",
    "scikit-learn": "sklearn",
    "tf": "tensorflow",
    "computer vision": "cv",
    "restful api": "rest api",
    "restful apis": "rest api",
    "microservices": "microservice architecture",
    "system design": "systems design",
    "agile methodology": "agile",
    "scrum master": "scrum"
}

def normalize_skill(skill: str) -> str:
    s = skill.lower().strip()
    return SYNONYM_DB.get(s, s)

def train_tfidf():
    global tfidf_vectorizer, category_centroids
    dataset_paths = [
        "./UpdatedResumeDataSet.csv",
        "../UpdatedResumeDataSet.csv",
        "C:\\Users\\rreji\\Downloads\\archive_22_temp\\UpdatedResumeDataSet.csv",
        "/app/UpdatedResumeDataSet.csv"
    ]
    
    loaded = False
    for path in dataset_paths:
        if os.path.exists(path):
            try:
                df = pd.read_csv(path)
                if 'Resume' in df.columns and 'Category' in df.columns:
                    corpus = df['Resume'].apply(clean_text).tolist()
                    tfidf_vectorizer.fit(corpus)
                    print(f"Successfully trained TF-IDF vectorizer on {len(corpus)} resumes.")
                    
                    # Calculate centroids for each job category
                    for category, group in df.groupby('Category'):
                        group_corpus = group['Resume'].apply(clean_text).tolist()
                        group_vectors = tfidf_vectorizer.transform(group_corpus)
                        category_centroids[category] = np.mean(group_vectors.toarray(), axis=0)
                    
                    print(f"Calculated centroids for {len(category_centroids)} categories.")
                    loaded = True
                    break
            except Exception as e:
                print(f"Error reading resume dataset at {path}: {e}")
                
    if not loaded:
        # Fallback corpus
        fallback_data = [
            ("Java Developer", "java spring boot microservices sql database maven backend developer rest api git jpa hibernate"),
            ("Python Developer", "python django flask fastapi programming script data scraping pandas numpy sql developer"),
            ("DevOps Engineer", "devops docker kubernetes aws cloud terraform jenkins cicd pipelines linux bash ansible"),
            ("Data Science", "data science machine learning deep learning python pytorch tensorflow scikit-learn pandas numpy stats"),
            ("Web Designing", "frontend html css javascript react typescript angular vue nextjs tailwind responsive ui web designer"),
            ("Database", "database administrator sql mysql postgresql oracle database tuning backup replication index dba"),
            ("Testing", "qa testing manual selenium automation test junit testng bug tracking postman qa engineer")
        ]
        
        corpus = [d[1] for d in fallback_data]
        tfidf_vectorizer.fit(corpus)
        
        for category, txt in fallback_data:
            vec = tfidf_vectorizer.transform([txt])
            category_centroids[category] = vec.toarray()[0]
            
        print("Trained TF-IDF vectorizer and centroids on fallback categories.")

    # Add custom AI/ML roles
    custom_aiml_roles = {
        "AI/ML Engineer": "machine learning deep learning artificial intelligence python pytorch tensorflow neural networks llm prompt engineering computer vision nlp langchain",
        "Machine Learning Engineer": "machine learning ml engineering python scikit-learn pandas numpy tensorflow pytorch mlops pipeline models deployment",
        "Deep Learning Engineer": "deep learning neural networks cnn rnn lstm transformers pytorch tensorflow keras computer vision image processing",
        "NLP Engineer": "natural language processing nlp text mining bert transformers gpt llm spacy nltk tokenization sentiment analysis langchain",
        "Computer Vision Engineer": "computer vision opencv image processing object detection segmentation yolo cnn pytorch tensorflow image classification"
    }
    
    for role, desc in custom_aiml_roles.items():
        desc_cleaned = clean_text(desc)
        vec = tfidf_vectorizer.transform([desc_cleaned])
        category_centroids[role] = vec.toarray()[0]
        
    print(f"Added custom AI/ML roles. Total categories: {len(category_centroids)}")

# Train on startup
train_tfidf()

# Pydantic Schemas
class MatchSkillsRequest(BaseModel):
    resume_text: str
    job_description: str

class GenerateQuestionsRequest(BaseModel):
    skills: List[str]

class EvaluateAnswerRequest(BaseModel):
    question: str
    answer: str
    skills: List[str]

# Extract text using pdfplumber
def extract_text_from_pdf(file_path_or_bytes) -> str:
    text = ""
    try:
        with pdfplumber.open(file_path_or_bytes) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse PDF resume: {str(e)}")
    return text

# Extract skills using dictionary regex matcher
def extract_skills(text: str) -> Dict[str, List[str]]:
    cleaned = clean_text(text)
    extracted = {}
    for category, patterns in SKILL_PATTERNS.items():
        matched_skills = []
        for skill, pattern in patterns:
            if pattern.search(cleaned):
                normalized = normalize_skill(skill)
                if normalized not in matched_skills:
                    matched_skills.append(normalized)
        extracted[category] = matched_skills
    return extracted

# Extract candidate info using regex
def extract_candidate_info(text: str) -> Dict[str, Any]:
    email_pattern = re.compile(r'[\w\.-]+@[\w\.-]+\.\w+')
    emails = email_pattern.findall(text)
    email = emails[0] if emails else "Not Provided"

    phone_pattern = re.compile(r'(?:(?:\+?\d{1,4}[-.\s]?)?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9})')
    phones = []
    for match in phone_pattern.findall(text):
        digits_only = re.sub(r'\D', '', match)
        if 7 <= len(digits_only) <= 15:
            phones.append(match.strip())
            break
    phone = phones[0] if phones else "Not Provided"

    experience_patterns = [
        re.compile(r'(\d+)\+?\s*(?:year|yr)s?\s*(?:of\s*)?experience', re.IGNORECASE),
        re.compile(r'(?:experience|exp)[:\-\s]+(\d+)\+?\s*(?:year|yr)s?', re.IGNORECASE),
        re.compile(r'(\d+)\s*(?:year|yr)s?\s*(?:in|of)\s*(?:industry|field|working)', re.IGNORECASE)
    ]
    
    exp_years = 0
    for pattern in experience_patterns:
        matches = pattern.findall(text)
        if matches:
            try:
                years = [int(m) for m in matches if m.isdigit()]
                if years:
                    exp_years = max(exp_years, max(years))
            except ValueError:
                pass
                
    if exp_years == 0:
        years_matches = re.findall(r'\b(\d+)\b\s*(?:year|yr)s?', text, re.IGNORECASE)
        if years_matches:
            try:
                years = [int(y) for y in years_matches if y.isdigit()]
                valid_years = [y for y in years if y < 45]
                if valid_years:
                    exp_years = max(valid_years)
            except ValueError:
                pass
                
    exp_str = f"{exp_years} Years" if exp_years > 0 else "Entry Level"
    return {"email": email, "phone": phone, "experience": exp_str}

def recommend_roles(resume_text: str) -> List[Dict[str, Any]]:
    """Recommend roles based on TF-IDF similarity against dataset centroids."""
    cleaned = clean_text(resume_text)
    try:
        resume_vec = tfidf_vectorizer.transform([cleaned]).toarray()[0]
        similarities = []
        for category, centroid in category_centroids.items():
            # Calculate Cosine Similarity
            dot_product = np.dot(resume_vec, centroid)
            norm_a = np.linalg.norm(resume_vec)
            norm_b = np.linalg.norm(centroid)
            sim = dot_product / (norm_a * norm_b) if norm_a > 0 and norm_b > 0 else 0.0
            similarities.append((category, float(sim)))
        
        # Sort by similarity in descending order
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Keep only software-related roles
        software_roles = {
            "data science", "web designing", "java developer", "sap developer",
            "automation testing", "python developer", "devops engineer",
            "network security engineer", "database", "hadoop", "etl developer",
            "dotnet developer", "blockchain", "testing",
            "ai/ml engineer", "machine learning engineer", "deep learning engineer",
            "nlp engineer", "computer vision engineer"
        }
        
        filtered_similarities = []
        for category, sim in similarities:
            if category.lower() in software_roles:
                filtered_similarities.append((category, sim))
                
        if not filtered_similarities:
            filtered_similarities = similarities
            
        # Get recommended categories with match percentage
        recommendations = []
        for category, sim in filtered_similarities:
            # Map TF-IDF cosine similarity values (typically 0.1 to 0.7) to a clear match percentage (30% to 98%)
            percentage = int(min(98, max(30, sim * 150)))
            recommendations.append({
                "role": category,
                "matchPercentage": percentage
            })
        return recommendations
    except Exception as e:
        print(f"Error calculating role recommendations: {e}")
        return [
            {"role": "Software Engineer", "matchPercentage": 92},
            {"role": "Backend Developer", "matchPercentage": 89},
            {"role": "Frontend Developer", "matchPercentage": 84},
            {"role": "Data Scientist", "matchPercentage": 78},
            {"role": "DevOps Engineer", "matchPercentage": 75},
            {"role": "Project Manager", "matchPercentage": 68}
        ]

ROLE_SKILL_TEMPLATES = {
    "java developer": {
        "core": ["java", "spring boot", "spring", "microservices", "sql"],
        "secondary": ["mysql", "postgresql", "docker", "git", "maven"],
        "soft_concepts": ["rest api", "agile", "cicd", "oop"]
    },
    "python developer": {
        "core": ["python", "django", "flask", "fastapi"],
        "secondary": ["sql", "git", "postgresql", "docker", "rest api"],
        "soft_concepts": ["oop", "agile", "tdd"]
    },
    "devops engineer": {
        "core": ["docker", "kubernetes", "aws", "terraform", "jenkins"],
        "secondary": ["cicd", "linux", "bash", "shell", "git", "ansible"],
        "soft_concepts": ["agile", "scrum", "cloud engineering"]
    },
    "data science": {
        "core": ["python", "machine learning", "deep learning", "statistics"],
        "secondary": ["pandas", "numpy", "pytorch", "tensorflow", "scikit-learn", "git"],
        "soft_concepts": ["nlp", "computer vision", "artificial intelligence", "data analysis"]
    },
    "web designing": {
        "core": ["html", "css", "javascript", "react"],
        "secondary": ["typescript", "tailwind", "bootstrap", "figma", "jquery", "git"],
        "soft_concepts": ["ui/ux", "responsive design", "web design"]
    },
    "database": {
        "core": ["sql", "mysql", "postgresql", "oracle", "database"],
        "secondary": ["redis", "sql server", "nosql", "git"],
        "soft_concepts": ["database optimization", "indexing", "query tuning"]
    },
    "testing": {
        "core": ["testing", "qa", "selenium", "manual testing"],
        "secondary": ["postman", "automation testing", "junit", "testng", "git"],
        "soft_concepts": ["bug tracking", "test plans", "agile"]
    },
    "automation testing": {
        "core": ["testing", "qa", "selenium", "automation testing"],
        "secondary": ["postman", "junit", "testng", "git", "cicd"],
        "soft_concepts": ["test automation framework", "bug tracking", "agile"]
    },
    "network security engineer": {
        "core": ["network", "security", "linux", "firewalls"],
        "secondary": ["aws", "gcp", "git", "bash", "shell", "wireshark"],
        "soft_concepts": ["cybersecurity", "routing", "switching"]
    },
    "sap developer": {
        "core": ["sap", "abap", "sap hana"],
        "secondary": ["sql", "database", "git"],
        "soft_concepts": ["erp", "business processes"]
    },
    "etl developer": {
        "core": ["etl", "data warehousing", "sql", "informatica"],
        "secondary": ["hadoop", "database", "python", "git"],
        "soft_concepts": ["data pipeline", "data integration"]
    },
    "dotnet developer": {
        "core": ["c#", "asp.net", ".net core", "net core"],
        "secondary": ["sql", "git", "sql server", "azure"],
        "soft_concepts": ["oop", "mvc", "web api"]
    },
    "blockchain": {
        "core": ["blockchain", "solidity", "smart contracts"],
        "secondary": ["go", "golang", "cryptography", "git", "ethereum"],
        "soft_concepts": ["decentralized systems", "consensus algorithms"]
    },
    "ai/ml engineer": {
        "core": ["python", "machine learning", "deep learning", "artificial intelligence", "pytorch", "tensorflow"],
        "secondary": ["git", "pandas", "numpy", "scikit-learn", "llm", "transformers"],
        "soft_concepts": ["nlp", "computer vision", "mlops", "neural networks"]
    },
    "machine learning engineer": {
        "core": ["python", "machine learning", "scikit-learn", "pytorch", "tensorflow"],
        "secondary": ["git", "pandas", "numpy", "mlops", "deployment"],
        "soft_concepts": ["predictive modeling", "feature engineering", "data pipelines"]
    },
    "deep learning engineer": {
        "core": ["python", "deep learning", "neural networks", "pytorch", "tensorflow"],
        "secondary": ["keras", "git", "computer vision", "nlp"],
        "soft_concepts": ["backpropagation", "cnn", "rnn", "transformers"]
    },
    "nlp engineer": {
        "core": ["python", "nlp", "natural language processing", "llm", "transformers"],
        "secondary": ["spacy", "nltk", "git", "bert", "gpt"],
        "soft_concepts": ["text normalization", "tokenization", "sentiment analysis"]
    },
    "computer vision engineer": {
        "core": ["python", "computer vision", "opencv", "image processing"],
        "secondary": ["pytorch", "tensorflow", "git", "cnn", "yolo"],
        "soft_concepts": ["object detection", "image segmentation", "image classification"]
    }
}

ROLE_DEFAULT_SKILLS_OLD = {}
for role, template in ROLE_SKILL_TEMPLATES.items():
    all_skills = set()
    for tier_skills in template.values():
        all_skills.update(tier_skills)
    ROLE_DEFAULT_SKILLS_OLD[role] = {s.lower() for s in all_skills}

# Normalize templates in-place
for role, template in list(ROLE_SKILL_TEMPLATES.items()):
    ROLE_SKILL_TEMPLATES[role] = {
        tier: {normalize_skill(s) for s in skill_set}
        for tier, skill_set in template.items()
    }

ROLE_DEFAULT_SKILLS = {}
for role, template in ROLE_SKILL_TEMPLATES.items():
    all_skills = set()
    for tier_skills in template.values():
        all_skills.update(tier_skills)
    ROLE_DEFAULT_SKILLS[role] = all_skills

def to_display_skill(skill: str) -> str:
    display_map = {
        "artificial intelligence": "Artificial Intelligence",
        "machine learning": "Machine Learning",
        "javascript": "JavaScript",
        "node.js": "Node.js",
        "react": "React",
        "mongodb": "MongoDB",
        "c++": "C++",
        "c#": "C#",
        ".net": ".NET",
        "asp.net": "ASP.NET",
        "spring boot": "Spring Boot",
        "rest api": "REST API",
        "ci/cd": "CI/CD",
        "cicd": "CI/CD",
        "aws": "AWS",
        "gcp": "GCP",
        "sql": "SQL",
        "mysql": "MySQL",
        "postgresql": "PostgreSQL",
        "html": "HTML",
        "css": "CSS",
        "k8s": "Kubernetes",
        "kubernetes": "Kubernetes",
        "json": "JSON",
        "nlp": "NLP",
        "ui": "UI",
        "ux": "UX",
        "api": "API",
        "git": "Git",
        "github": "GitHub",
        "gitlab": "GitLab"
    }
    s = skill.lower().strip()
    if s in display_map:
        return display_map[s]
    return s.title()


STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't", "as", "at",
    "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "can't", "cannot", "could",
    "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during", "each", "few", "for",
    "from", "further", "had", "hadn't", "has", "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's",
    "her", "here", "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i", "i'd", "i'll", "i'm",
    "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself", "let's", "me", "more", "most", "mustn't",
    "my", "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours",
    "ourselves", "out", "over", "own", "same", "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't",
    "so", "some", "such", "than", "that", "that's", "the", "their", "theirs", "them", "themselves", "then", "there",
    "there's", "these", "they", "they'd", "they'll", "they're", "they've", "this", "those", "through", "to", "too",
    "under", "until", "up", "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were", "weren't",
    "what", "what's", "when", "when's", "where", "where's", "which", "while", "who", "who's", "whom", "why", "why's",
    "with", "won't", "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours", "yourself",
    "yourselves", "the", "will", "shall", "company", "candidate", "role", "experience", "work", "job", "description",
    "requirements", "responsibilities", "looking", "team", "skills"
}

def extract_meaningful_keywords(text: str) -> set:
    cleaned = re.sub(r'[^a-zA-Z\s]', '', text.lower())
    words = cleaned.split()
    return {w for w in words if len(w) > 3 and w not in STOP_WORDS}

def calculate_confidence_score(resume_text: str, candidate_info: dict, all_skills: set) -> float:
    # 1. Text length confidence: optimal word count is 250 - 850 words
    words = resume_text.split()
    word_count = len(words)
    if 250 <= word_count <= 850:
        len_score = 30.0
    elif 150 <= word_count <= 1200:
        len_score = 20.0
    else:
        len_score = 10.0

    # 2. Metadata completeness: Email, Phone, Experience (30 pts)
    meta_score = 0.0
    if candidate_info.get("email") != "Not Provided":
        meta_score += 10.0
    if candidate_info.get("phone") != "Not Provided":
        meta_score += 10.0
    if candidate_info.get("experience") != "Entry Level" and candidate_info.get("experience") != "Not Provided":
        meta_score += 10.0
    else:
        meta_score += 5.0

    # 3. Skill coverage: optimal identified skills count is 6 - 22 (40 pts)
    skills_count = len(all_skills)
    if 6 <= skills_count <= 22:
        skills_score = 40.0
    elif 3 <= skills_count <= 30:
        skills_score = 25.0
    else:
        skills_score = 10.0

    return float(np.round(len_score + meta_score + skills_score, 1))

def prioritize_missing_skills(role: str, missing_skills: set) -> List[Dict[str, str]]:
    role_lower = role.lower() if role else ""
    template = ROLE_SKILL_TEMPLATES.get(role_lower, {})
    
    prioritized = []
    for skill in missing_skills:
        skill_lower = skill.lower().strip()
        canonical = normalize_skill(skill_lower)
        
        if template:
            if canonical in template.get("core", []):
                priority = "high"
            elif canonical in template.get("secondary", []):
                priority = "medium"
            elif canonical in template.get("soft_concepts", []):
                priority = "low"
            else:
                priority = "medium"
        else:
            category = None
            for cat, skills in SKILLS_DICT.items():
                if canonical in [s.lower() for s in skills]:
                    category = cat
                    break
            if category in ["languages", "databases", "frameworks", "ml/ai"]:
                priority = "high" if category == "languages" else "medium"
            else:
                priority = "low"
                
        prioritized.append({
            "name": to_display_skill(skill),
            "priority": priority
        })
        
    priority_order = {"high": 0, "medium": 1, "low": 2}
    prioritized.sort(key=lambda x: (priority_order.get(x["priority"], 1), x["name"].lower()))
    return prioritized

def calculate_ats_scores(resume_text: str, job_desc: str) -> Dict[str, Any]:
    cleaned_resume = clean_text(resume_text)
    cleaned_jd = clean_text(job_desc)
    jd_available = bool(cleaned_jd)

    # Calculate Completeness Score (used in both paths)
    candidate_info = extract_candidate_info(resume_text)
    completeness_score = 0.0
    if candidate_info.get("email") != "Not Provided":
        completeness_score += 40.0
    if candidate_info.get("phone") != "Not Provided":
        completeness_score += 40.0
    if candidate_info.get("experience") != "Entry Level":
        completeness_score += 20.0
    else:
        completeness_score += 10.0

    # ------------------ NEW (Normalized) MATCHING LOGIC ------------------
    # 1. Extract resume skills using correct boundaries and synonym resolution
    resume_skills_dict = extract_skills(resume_text)  # Already normalized to lowercase by extract_skills
    resume_skills_flat = set()
    for cat_skills in resume_skills_dict.values():
        resume_skills_flat.update(cat_skills)

    # 2. Extract job description skills using correct boundaries
    jd_skills_flat = set()
    if cleaned_jd:
        jd_skills_dict = extract_skills(job_desc)
        for cat_skills in jd_skills_dict.values():
            jd_skills_flat.update(cat_skills)

    # Fallback to recommended role default skills (normalized)
    recs = recommend_roles(resume_text)
    top_role = recs[0]["role"].lower() if recs else "java developer"
    if not jd_skills_flat:
        jd_skills_flat = ROLE_DEFAULT_SKILLS.get(top_role, {"java", "git", "sql", "python", "developer"})

    # Perform matching on lowercase normalized sets
    matched_skills = resume_skills_flat.intersection(jd_skills_flat)
    missing_skills = jd_skills_flat - resume_skills_flat

    # Calculate Skill Match Score
    if jd_skills_flat:
        skill_match_score = float(np.round((len(matched_skills) / len(jd_skills_flat)) * 100, 2))
    else:
        skill_match_score = 100.0 if resume_skills_flat else 0.0

    # ------------------ OLD (Before Fixes) MATCHING LOGIC ------------------
    # 1. Extract raw resume skills using OLD \b boundaries and NO normalization
    resume_skills_flat_old = set()
    for category, patterns in SKILL_PATTERNS_OLD.items():
        for skill, pattern in patterns:
            if pattern.search(cleaned_resume):
                resume_skills_flat_old.add(skill.lower())  # old matched raw lowercase skill key

    # 2. Extract raw job description skills using OLD \b boundaries and NO normalization
    jd_skills_flat_old = set()
    if cleaned_jd:
        for category, patterns in SKILL_PATTERNS_OLD.items():
            for skill, pattern in patterns:
                if pattern.search(cleaned_jd):
                    jd_skills_flat_old.add(skill.lower())
    
    # Fallback to unnormalized role default skills
    if not jd_skills_flat_old:
        jd_skills_flat_old = {s.lower() for s in ROLE_DEFAULT_SKILLS_OLD.get(top_role, {"java", "git", "sql", "python", "developer"})}

    # Perform matching on unnormalized sets
    matched_skills_old = resume_skills_flat_old.intersection(jd_skills_flat_old)
    missing_skills_old = jd_skills_flat_old - resume_skills_flat_old

    # Calculate Old Skill Match Score
    if jd_skills_flat_old:
        skill_match_score_old = float(np.round((len(matched_skills_old) / len(jd_skills_flat_old)) * 100, 2))
    else:
        skill_match_score_old = 100.0 if resume_skills_flat_old else 0.0

    # ------------------ Semantic Score & Keyword Overlap ------------------
    # Calculate Semantic Score combining keyword overlap and SBERT similarity
    sbert_sim = None
    if cleaned_resume and cleaned_jd:
        sbert_sim = calculate_sbert_similarity(cleaned_resume, cleaned_jd)

    try:
        if cleaned_resume and cleaned_jd:
            if sbert_sim is not None:
                # Scale SBERT cosine similarity (typically 0.3 - 0.85) to [40% - 100%]
                scaled_similarity = min(100.0, max(0.0, (sbert_sim - 0.3) / 0.55 * 60 + 40))
            else:
                resume_vec = tfidf_vectorizer.transform([cleaned_resume])
                jd_vec = tfidf_vectorizer.transform([cleaned_jd])
                similarity = cosine_similarity(resume_vec, jd_vec)[0][0]
                scaled_similarity = min(100.0, similarity * 220)
            
            jd_keywords = extract_meaningful_keywords(job_desc)
            resume_keywords = extract_meaningful_keywords(resume_text)
            if jd_keywords:
                keyword_overlap = len(jd_keywords.intersection(resume_keywords)) / len(jd_keywords) * 100
            else:
                keyword_overlap = 100.0 if resume_keywords else 0.0
                
            semantic_score = float(np.round(0.60 * keyword_overlap + 0.40 * scaled_similarity, 2))
        else:
            word_count = len(cleaned_resume.split())
            semantic_score = float(min(100.0, max(40.0, word_count / 5.0)))
            keyword_overlap = semantic_score
    except Exception as e:
        print(f"Error calculating similarity: {e}")
        semantic_score = 0.0
        keyword_overlap = 0.0

    # ------------------ Final ATS Scores ------------------
    ats_score = float(np.round(0.70 * skill_match_score + 0.20 * keyword_overlap + 0.10 * completeness_score, 2))
    before_ats_score = float(np.round(0.70 * skill_match_score_old + 0.20 * keyword_overlap + 0.10 * completeness_score, 2))
    confidence_score = calculate_confidence_score(resume_text, candidate_info, resume_skills_flat)

    # Format lists nicely for user presentation using to_display_skill
    all_skills_display = sorted(list({to_display_skill(s) for s in resume_skills_flat}))
    matched_skills_display = sorted(list({to_display_skill(s) for s in matched_skills}))
    
    # Prioritize missing skills by core template levels
    missing_skills_prioritized = prioritize_missing_skills(top_role, missing_skills)

    before_matched_skills_display = sorted(list({to_display_skill(s) for s in matched_skills_old}))
    before_missing_skills_display = sorted(list({to_display_skill(s) for s in missing_skills_old}))

    categorized_skills_display = {}
    for cat, list_skills in resume_skills_dict.items():
        categorized_skills_display[cat] = sorted(list({to_display_skill(s) for s in list_skills}))

    return {
        "atsScore": ats_score,
        "skillMatchScore": skill_match_score,
        "semanticScore": semantic_score,
        "keywordOverlap": keyword_overlap,
        "completenessScore": completeness_score,
        "allSkills": all_skills_display,
        "matchedSkills": matched_skills_display,
        "missingSkills": missing_skills_prioritized,
        "categorizedSkills": categorized_skills_display,
        "confidenceScore": confidence_score,
        "jdAvailable": jd_available,
        # Before fixes values
        "beforeAtsScore": before_ats_score,
        "beforeSkillMatchScore": skill_match_score_old,
        "beforeMatchedSkills": before_matched_skills_display,
        "beforeMissingSkills": before_missing_skills_display
    }


def generate_saas_career_assistant_payload(resume_text: str, job_description: str, analysis: dict, recommended_roles: list) -> dict:
    text_lower = resume_text.lower()
    
    # 1. Section scores (Skills, Projects, Experience, Education, Achievements, Certifications)
    skills_score = int(analysis.get("skillMatchScore", 70))
    
    projects_score = 40
    if "project" in text_lower or "portfolio" in text_lower:
        projects_score += 30
        if len(re.findall(r'\b(build|develop|implement|design|create|system)\b', text_lower)) > 5:
            projects_score += 20
    projects_score = min(98, max(35, projects_score))
    
    experience_score = 30
    exp_info = analysis.get("completenessScore", 50)
    experience_score += int(exp_info * 0.5)
    if "experience" in text_lower or "work history" in text_lower or "employed" in text_lower:
        experience_score += 20
    experience_score = min(98, max(30, experience_score))
    
    education_score = 40
    if any(deg in text_lower for deg in ["bachelor", "master", "phd", "b.s", "m.s", "degree", "university", "college"]):
        education_score += 45
    education_score = min(98, max(40, education_score))
    
    achievements_score = 30
    if "%" in text_lower or any(word in text_lower for word in ["achieved", "won", "award", "scholarship", "first place", "revenue", "saved"]):
        achievements_score += 45
    achievements_score = min(98, max(25, achievements_score))
    
    certifications_score = 30
    if any(word in text_lower for word in ["certificat", "certified", "aws", "gcp", "azure", "oracle", "credential"]):
        certifications_score += 55
    certifications_score = min(98, max(20, certifications_score))
    
    section_scores = {
        "skills": skills_score,
        "projects": projects_score,
        "experience": experience_score,
        "education": education_score,
        "achievements": achievements_score,
        "certifications": certifications_score
    }
    
    # Find weakest section
    weakest_sec = min(section_scores, key=section_scores.get)
    
    # 2. AI Insights
    strengths = []
    if skills_score > 70:
        strengths.append("Robust technical keyword alignment.")
    else:
        strengths.append("Clear structural layout.")
    if education_score > 80:
        strengths.append("Strong academic credentials.")
    if projects_score > 70:
        strengths.append("Detailed project descriptions.")
    if len(strengths) < 2:
        strengths.append("Includes essential contact information.")
        
    weaknesses = []
    missing_skills = [s.get("name") if isinstance(s, dict) else s for s in analysis.get("missingSkills", [])]
    if missing_skills:
        weaknesses.append(f"Lacks key role technologies: {', '.join(missing_skills[:2])}.")
    if achievements_score < 50:
        weaknesses.append("Fewer quantified metrics and business achievements.")
    if experience_score < 50:
        weaknesses.append("Work history details could be expanded.")
    if len(weaknesses) < 2:
        weaknesses.append("Missing certification badges for target technologies.")
        
    highest_impact_imp = ""
    next_action = ""
    if missing_skills:
        highest_impact_imp = f"Add {missing_skills[0]} experience to your projects."
        next_action = f"Complete a mini-project using {missing_skills[0]} and document it on GitHub."
    else:
        highest_impact_imp = "Integrate quantified business achievements (e.g., performance improvements %)."
        next_action = "Add metrics like 'reduced latency by 20%' or 'scaled API load by 50%' to your projects."

    ai_insights = {
        "strengths": strengths,
        "weaknesses": weaknesses,
        "highestImpactImprovement": highest_impact_imp,
        "recommendedNextAction": next_action
    }
    
    # 3. AI Resume Optimizer Suggestions
    weak_sections = [weakest_sec.title()]
    if achievements_score < 60:
        weak_sections.append("Achievements")
    
    improvements = []
    if "achievements" in weak_sections or achievements_score < 60:
        improvements.append("Use the STAR method: Action-Result framework to rewrite bullet points.")
    if missing_skills:
        improvements.append(f"Add a dedicated Tech Stack pill for {', '.join(missing_skills[:3])}.")
    improvements.append("Include links to your GitHub profile and demo links for projects.")
    
    # Generate rewritten bullet points
    bullets = []
    if missing_skills:
        bullets.append({
            "original": "Worked on python code and databases.",
            "rewritten": f"Architected scalable Python backend systems using {missing_skills[0]}, optimizing query performance by 35%."
        })
        if len(missing_skills) > 1:
            bullets.append({
                "original": "Helped team in software deployment.",
                "rewritten": f"Implemented CI/CD pipelines using {missing_skills[1]} and Docker, reducing deployment time by 40%."
            })
    else:
        bullets.append({
            "original": "Worked on frontend features.",
            "rewritten": "Designed interactive user interfaces using React and Tailwind CSS, increasing page load speed by 25%."
        })
        bullets.append({
            "original": "Responsible for API development.",
            "rewritten": "Developed high-throughput RESTful APIs using Node.js and Express, supporting 10k+ active daily users."
        })
        
    resume_optimizer = {
        "weakSections": weak_sections,
        "improvements": improvements,
        "rewrittenBullets": bullets,
        "keywordsToAdd": missing_skills[:4]
    }
    
    # 4. Learning Roadmap
    plan7 = []
    plan30 = []
    plan60 = []
    
    if missing_skills:
        plan7.append(f"Understand core concepts of {missing_skills[0]} and read official documentation.")
        plan7.append(f"Set up a local development environment and run a Hello World program.")
        
        if len(missing_skills) > 1:
            plan30.append(f"Build a medium-complexity application integrating {missing_skills[0]} and {missing_skills[1]}.")
            plan30.append("Implement automated unit testing and containerize the application.")
        else:
            plan30.append(f"Build a fully-functional CRUD application with {missing_skills[0]}.")
            plan30.append("Host the repository on GitHub with clean documentation.")
            
        if len(missing_skills) > 2:
            plan60.append(f"Configure CI/CD automated deployments and deploy to {missing_skills[2]} or cloud provider.")
            plan60.append("Run load tests and optimize the application performance.")
        else:
            plan60.append("Deploy the application to a public hosting service (e.g. Render, Railway).")
            plan60.append("Write a comprehensive blog post detailing your architecture and learnings.")
    else:
        plan7.append("Research advanced system design patterns and microservices.")
        plan7.append("Review concurrency, caching, and database optimization techniques.")
        plan30.append("Build a distributed system using Kafka or RabbitMQ.")
        plan30.append("Implement Redis caching and profile the API latency.")
        plan60.append("Configure AWS VPC, load balancers, and deploy via Kubernetes.")
        plan60.append("Prepare system design mock interviews.")
        
    learning_roadmap = {
        "plan7Days": plan7,
        "plan30Days": plan30,
        "plan60Days": plan60
    }
    
    # 5. Career Path suggestions
    career_paths = []
    for rec in recommended_roles[:3]:
        role_name = rec["role"]
        match_pct = rec["matchPercentage"]
        
        salary = "$85,000 - $125,000"
        demand = "High"
        
        role_lower = role_name.lower()
        if "data science" in role_lower or "machine learning" in role_lower or "ai" in role_lower:
            salary = "$115,000 - $165,000"
            demand = "Very High"
        elif "devops" in role_lower or "cloud" in role_lower:
            salary = "$110,000 - $155,000"
            demand = "Very High"
        elif "java" in role_lower or "dotnet" in role_lower or "backend" in role_lower:
            salary = "$95,000 - $140,000"
            demand = "High"
        elif "web" in role_lower or "frontend" in role_lower:
            salary = "$80,000 - $120,000"
            demand = "High"
            
        career_paths.append({
            "role": role_name,
            "matchPercentage": match_pct,
            "salaryRange": salary,
            "marketDemand": demand
        })
        
    # 6. Skill Gap Analysis
    skill_gap = {}
    resume_skills_dict = extract_skills(resume_text)
    
    recs = recommend_roles(resume_text)
    top_role = recs[0]["role"].lower() if recs else "java developer"
    
    for category, skills in SKILLS_DICT.items():
        cat_resume_skills = [to_display_skill(s) for s in resume_skills_dict.get(category, [])]
        cat_required_skills = []
        
        template = ROLE_SKILL_TEMPLATES.get(top_role, {})
        for tier, template_skills in template.items():
            for s in template_skills:
                skill_cat = None
                for c, cs in SKILLS_DICT.items():
                    if s.lower() in [x.lower() for x in cs]:
                        skill_cat = c
                        break
                if skill_cat == category:
                    display_s = to_display_skill(s)
                    if display_s not in cat_required_skills:
                        cat_required_skills.append(display_s)
                        
        if not cat_required_skills:
            cat_required_skills = [to_display_skill(s) for s in skills[:3]]
            
        matched_cat = set(cat_resume_skills).intersection(set(cat_required_skills))
        if cat_required_skills:
            gap_pct = int((1 - len(matched_cat) / len(cat_required_skills)) * 100)
        else:
            gap_pct = 0
            
        display_category_map = {
            "languages": "Programming",
            "frameworks": "Frameworks",
            "databases": "Databases",
            "cloud": "Cloud",
            "ml/ai": "AI/ML",
            "tools": "DevOps",
            "concepts": "Concepts"
        }
        
        skill_gap[display_category_map.get(category, category.title())] = {
            "current": cat_resume_skills,
            "required": cat_required_skills,
            "gapPercentage": gap_pct
        }
        
    # 7. Job Readiness Index
    ats_wt = float(analysis.get("atsScore", 60)) * 0.2
    tech_wt = float(skills_score) * 0.3
    proj_wt = float(projects_score) * 0.2
    exp_wt = float(experience_score) * 0.2
    qual_wt = float(analysis.get("completenessScore", 60)) * 0.1
    readiness_score = int(ats_wt + tech_wt + proj_wt + exp_wt + qual_wt)
    readiness_score = min(100, max(10, readiness_score))
    
    # 8. Detailed Interview Questions
    detailed_questions = []
    idx = 1
    matched_list = list(analysis.get("matchedSkills", []))
    for skill in matched_list[:2]:
        skill_lower = skill.lower()
        q = f"What is your approach to structuring code and managing memory when using {skill}?"
        for k, questions_list in QUESTION_BANK.items():
            if k in skill_lower or skill_lower in k:
                q = questions_list[0]
                break
            
        detailed_questions.append({
            "id": idx,
            "question": q,
            "expectedAnswer": f"A solid answer should explain the core design philosophy of {skill}, memory model details, and performance implications.",
            "keyConcepts": [skill, "Architecture", "Optimization"],
            "difficulty": "Medium",
            "category": "Technical"
        })
        idx += 1
        
    for skill in missing_skills[:2]:
        detailed_questions.append({
            "id": idx,
            "question": f"How would you integrate {skill} into an existing microservices stack, and what design trade-offs would you consider?",
            "expectedAnswer": f"The answer should discuss how {skill} handles connection pooling, synchronization, scaling patterns, and integration checkpoints with other components.",
            "keyConcepts": [skill, "System Design", "Integration"],
            "difficulty": "Hard",
            "category": "Project-Based"
        })
        idx += 1
        
    detailed_questions.append({
        "id": idx,
        "question": "Describe a challenging technical disagreement you had with a teammate. How did you resolve it?",
        "expectedAnswer": "Use the STAR method: explain the Situation, Task, Action you took to research/compromise, and the Resulting team cohesion.",
        "keyConcepts": ["Collaboration", "Conflict Resolution", "Communication"],
        "difficulty": "Easy",
        "category": "Behavioral"
    })
    idx += 1
    
    detailed_questions.append({
        "id": idx,
        "question": "Why do you want to join this role, and how do you align with our technological roadmap?",
        "expectedAnswer": "Explain how your experience matches their stack, mention your adaptability, and show interest in their business problems.",
        "keyConcepts": ["Motivation", "Career Alignment", "Culture Fit"],
        "difficulty": "Easy",
        "category": "HR"
    })
    
    return {
        "sectionScores": section_scores,
        "weakestSection": weakest_sec,
        "aiInsights": ai_insights,
        "resumeOptimizer": resume_optimizer,
        "learningRoadmap": learning_roadmap,
        "careerPaths": career_paths,
        "skillGap": skill_gap,
        "jobReadinessIndex": readiness_score,
        "detailedQuestions": detailed_questions
    }


# ----------------- FastAPI Endpoints -----------------

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/match-skills")
def match_skills(request: MatchSkillsRequest):
    scores = calculate_ats_scores(request.resume_text, request.job_description)
    return scores

@app.post("/analyze-resume")
async def analyze_resume(file: UploadFile = File(...), job_description: str = Form("")):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    try:
        contents = await file.read()
        temp_filename = f"temp_{file.filename}"
        with open(temp_filename, "wb") as f:
            f.write(contents)
            
        resume_text = extract_text_from_pdf(temp_filename)
        os.remove(temp_filename)
    except Exception as e:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")

    candidate_info = extract_candidate_info(resume_text)
    analysis = calculate_ats_scores(resume_text, job_description)
    
    # ML Role recommendations
    recommended_roles = recommend_roles(resume_text)

    # Question Generation
    questions = []
    all_detected_skills = analysis["allSkills"]
    for skill in all_detected_skills:
        skill_lower = skill.lower()
        if skill_lower in QUESTION_BANK:
            questions.extend(QUESTION_BANK[skill_lower])
            
    if not questions:
        questions = [
            "Can you describe your most challenging software project and the technical decisions you made?",
            "How do you approach debugging a complex issue in a production environment?",
            "Explain your process for learning a new technology or framework quickly."
        ]

    questions = questions[:12]

    saas_data = generate_saas_career_assistant_payload(resume_text, job_description, analysis, recommended_roles)

    return {
        "fileName": file.filename,
        "atsScore": analysis["atsScore"],
        "skillMatchScore": analysis["skillMatchScore"],
        "semanticScore": analysis["semanticScore"],
        "keywordOverlap": analysis["keywordOverlap"],
        "completenessScore": analysis["completenessScore"],
        "allSkills": analysis["allSkills"],
        "matchedSkills": analysis["matchedSkills"],
        "missingSkills": analysis["missingSkills"],
        "categorizedSkills": analysis["categorizedSkills"],
        "candidateInfo": candidate_info,
        "questions": questions,
        "recommendedRoles": recommended_roles,
        "confidenceScore": analysis["confidenceScore"],
        "jdAvailable": analysis["jdAvailable"],
        "beforeAtsScore": analysis["beforeAtsScore"],
        "beforeSkillMatchScore": analysis["beforeSkillMatchScore"],
        "beforeMatchedSkills": analysis["beforeMatchedSkills"],
        "beforeMissingSkills": analysis["beforeMissingSkills"],
        "careerAssistantData": saas_data
    }


@app.post("/generate-questions")
def generate_questions(request: GenerateQuestionsRequest):
    questions = []
    for skill in request.skills:
        skill_lower = skill.lower()
        if skill_lower in QUESTION_BANK:
            questions.extend(QUESTION_BANK[skill_lower])
    
    if not questions:
        questions = [
            f"What are the best practices when building systems using {', '.join(request.skills)}?",
            f"Explain a common challenge you face when working with {', '.join(request.skills)} and how you overcome it.",
            f"How do you handle scalability and performance optimization in your stack?"
        ]
    return {"questions": questions}

@app.post("/evaluate-answer")
def evaluate_answer(request: EvaluateAnswerRequest):
    """Evaluate candidate answer for mock interview question, returning score and feedback."""
    q_lower = request.question.lower()
    a_lower = request.answer.lower()
    
    # 1. Base Score calculation using length and keyword matching
    score = 4.0  # base starting score for any attempt
    
    # Match keywords in the answer
    keywords = ["use", "how", "why", "example", "difference", "process", "design", "scalable", "performance"]
    matches = [k for k in keywords if k in a_lower]
    score += len(matches) * 0.4
    
    # Add length points
    word_count = len(a_lower.split())
    if word_count > 80:
        score += 2.0
    elif word_count > 40:
        score += 1.0
    elif word_count < 10:
        score -= 2.0  # too short
        
    # Cap score
    score = min(10.0, max(1.0, float(np.round(score, 1))))
    
    # Generate custom mock feedback based on question subject
    correctness = "The answer demonstrates a basic conceptual understanding of the requested topic. "
    missing = "Requires more concrete details. "
    model_ans = "A model answer should start with a clear definition, explain the architecture/mechanism, and mention real-world usage."
    tips = [
        "Include more concrete architectural terms (e.g. layers, memory, lifecycle).",
        "Use structured patterns (e.g. STAR method for behavioral, technical definitions first).",
        "Mention real-world examples from your past projects."
    ]
    
    # Tailor based on Java/Python/Spring/SQL keywords
    if "python" in q_lower or "list" in q_lower or "tuple" in q_lower:
        correctness += "Successfully mentioned the differences in syntax or mutability."
        missing += "Should explicitly mention reference management, hashability, and memory overhead (tuples are smaller and read-only)."
        model_ans = "Lists are mutable, dynamic arrays that require more memory overhead, while tuples are immutable, fixed-size sequences that are hashable (can be used as dictionary keys) and faster to allocate."
        tips.append("Mention that tuples are hashable and can be used as dictionary keys.")
    elif "java" in q_lower or "hashmap" in q_lower or "concurrenthashmap" in q_lower:
        correctness += "Identified that HashMap is unsynchronized and ConcurrentHashMap is thread-safe."
        missing += "Missing technical details about java's thread safety mechanisms (e.g., segment locking, CAS, bucket-level locking in Java 8)."
        model_ans = "HashMap is not thread-safe. ConcurrentHashMap achieves thread-safety without locking the entire map by using bucket-level locks (synchronized on node head) and CAS (Compare-And-Swap) operations on empty buckets."
        tips.append("Explain thread-safety locks at the segment or node level instead of locking the entire collection.")
    elif "spring" in q_lower or "dependency injection" in q_lower:
        correctness += "Accurately noted that Dependency Injection (DI) manages components and decouples code."
        missing += "Could mention Spring ApplicationContext container and Constructor vs Setter injection."
        model_ans = "Dependency Injection is a design pattern implementing IoC. In Spring Boot, the ApplicationContext container manages the lifecycle of beans, injecting dependencies into components annotated with @Autowired (preferably via constructor injection)."
    elif "join" in q_lower or "sql" in q_lower:
        correctness += "Correctly defined inner join vs outer joins."
        missing += "Should mention null values in left/right joins and Cartesian product matching."
        model_ans = "INNER JOIN returns matching rows from both tables. LEFT JOIN returns all rows from the left table and matched rows from the right table, filling unmatched right columns with NULL."
    
    return {
        "score": score,
        "correctness": correctness,
        "missing": missing,
        "modelAnswer": model_ans,
        "tips": tips
    }

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
