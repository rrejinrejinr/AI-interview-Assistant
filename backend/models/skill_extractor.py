import re

SKILL_DICTIONARY = {
    "Programming": [
        "python", "java", "javascript", "typescript", "c", "c++", "c#", "sql",
        "go", "golang", "rust", "ruby", "php", "swift", "kotlin", "r", "matlab",
        "bash", "shell", "scala", "perl", "lua", "julia", "dart",
        "html", "html5", "css", "css3", "xml", "json", "yaml"
    ],
    "Frontend": [
        "react", "angular", "vue", "next.js", "nextjs", "nuxt", "svelte",
        "tailwind", "tailwindcss", "bootstrap", "material ui", "mui",
        "redux", "zustand", "webpack", "vite", "babel", "sass", "scss",
        "jquery", "three.js", "threejs", "webgl"
    ],
    "Backend": [
        "fastapi", "flask", "django", "node.js", "nodejs", "express", "express.js",
        "spring boot", "spring framework", "spring", "asp.net", "laravel", "rails",
        "gin", "fiber", "nestjs", "nest.js", "grpc", "graphql",
        "rest api", "rest apis", "restful api", "restful", "restapi",
        "microservices", "web scraping", "selenium"
    ],
    "AI/ML": [
        "machine learning", "deep learning", "nlp", "natural language processing",
        "computer vision", "generative ai", "genai", "llm", "large language models",
        "rag", "retrieval augmented generation", "reinforcement learning",
        "neural networks", "transformers", "bert", "gpt", "svm",
        "random forest", "decision trees", "gradient boosting",
        "object detection", "image segmentation", "time series",
        "feature engineering", "model deployment", "mlops"
    ],
    "ML Libraries": [
        "scikit-learn", "sklearn", "tensorflow", "pytorch", "keras",
        "huggingface", "spacy", "nltk", "opencv", "gensim",
        "xgboost", "lightgbm", "catboost", "statsmodels",
        "langchain", "llamaindex"
    ],
    "Data": [
        "pandas", "numpy", "matplotlib", "seaborn", "plotly",
        "power bi", "tableau", "excel", "scipy",
        "apache spark", "pyspark", "spark", "hadoop", "kafka", "apache kafka",
        "airflow", "apache airflow", "dbt", "dask", "polars",
        "etl", "data pipeline", "data warehousing", "snowflake", "databricks",
        "looker", "metabase"
    ],
    "Cloud/DevOps": [
        "aws", "amazon web services", "azure", "gcp", "google cloud",
        "docker", "kubernetes", "k8s", "jenkins", "terraform", "ansible",
        "ci/cd", "cicd", "linux", "git", "github", "gitlab", "bitbucket",
        "helm", "prometheus", "grafana", "nginx",
        "cloudformation", "github actions", "circleci"
    ],
    "Databases": [
        "postgresql", "postgres", "mysql", "mongodb", "redis", "sqlite",
        "oracle", "cassandra", "elasticsearch", "firebase", "dynamodb",
        "sql server", "supabase", "neo4j", "couchdb", "mariadb",
        "prisma", "sequelize", "sqlalchemy"
    ],
    "Tools": [
        "jira", "confluence", "postman", "swagger", "figma",
        "jupyter", "jupyter notebook", "google colab", "colab",
        "intellij", "eclipse"
    ]
}

# Canonical display name mapping
FMT_MAP = {
    "sql": "SQL", "nlp": "NLP", "llm": "LLM", "rag": "RAG",
    "aws": "AWS", "gcp": "GCP", "ci/cd": "CI/CD", "cicd": "CI/CD",
    "html": "HTML", "html5": "HTML", "css": "CSS", "css3": "CSS",
    "xml": "XML", "json": "JSON", "yaml": "YAML",
    "scikit-learn": "scikit-learn", "sklearn": "scikit-learn",
    "node.js": "Node.js", "nodejs": "Node.js",
    "next.js": "Next.js", "nextjs": "Next.js",
    "asp.net": "ASP.NET", "fastapi": "FastAPI",
    "pytorch": "PyTorch", "numpy": "NumPy",
    "opencv": "OpenCV", "mongodb": "MongoDB", "mysql": "MySQL",
    "power bi": "Power BI", "javascript": "JavaScript",
    "typescript": "TypeScript", "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL", "k8s": "Kubernetes",
    "kubernetes": "Kubernetes", "amazon web services": "AWS",
    "google cloud": "GCP", "rest api": "REST APIs",
    "rest apis": "REST APIs", "restful api": "REST APIs",
    "restful": "REST APIs", "restapi": "REST APIs",
    "tailwind": "Tailwind CSS", "tailwindcss": "Tailwind CSS",
    "pyspark": "Apache Spark", "spark": "Apache Spark",
    "apache spark": "Apache Spark", "huggingface": "HuggingFace",
    "langchain": "LangChain", "llamaindex": "LlamaIndex",
    "material ui": "Material UI", "mui": "Material UI",
    "three.js": "Three.js", "threejs": "Three.js",
    "github actions": "GitHub Actions", "circleci": "CircleCI",
    "cloudformation": "CloudFormation", "snowflake": "Snowflake",
    "databricks": "Databricks", "dbt": "dbt",
    "sqlalchemy": "SQLAlchemy", "prisma": "Prisma",
    "sequelize": "Sequelize", "supabase": "Supabase",
    "firebase": "Firebase", "dynamodb": "DynamoDB",
    "elasticsearch": "Elasticsearch", "cassandra": "Cassandra",
    "graphql": "GraphQL", "redis": "Redis",
    "nginx": "Nginx", "jupyter notebook": "Jupyter Notebook",
    "jupyter": "Jupyter Notebook", "google colab": "Google Colab",
    "colab": "Google Colab", "genai": "Generative AI",
    "generative ai": "Generative AI", "mlops": "MLOps", "svm": "SVM",
    "xgboost": "XGBoost", "lightgbm": "LightGBM",
    "catboost": "CatBoost", "statsmodels": "Statsmodels",
    "gensim": "Gensim", "spacy": "spaCy", "nltk": "NLTK",
    "keras": "Keras", "tensorflow": "TensorFlow",
    "bert": "BERT", "gpt": "GPT",
    "transformers": "Transformers", "transformer": "Transformers",
    "tableau": "Tableau", "hadoop": "Hadoop", "excel": "Excel",
    "dask": "Dask", "polars": "Polars",
    "selenium": "Selenium", "web scraping": "Web Scraping",
    "data pipeline": "Data Pipelines",
    "data warehousing": "Data Warehousing",
    "etl": "ETL", "looker": "Looker", "metabase": "Metabase",
    "postman": "Postman", "swagger": "Swagger",
    "figma": "Figma", "jira": "Jira",
    "confluence": "Confluence", "nuxt": "Nuxt.js",
    "svelte": "Svelte", "zustand": "Zustand",
    "webpack": "Webpack", "vite": "Vite",
    "babel": "Babel", "sass": "Sass", "scss": "SCSS",
    "jquery": "jQuery", "webgl": "WebGL",
    "bootstrap": "Bootstrap", "redux": "Redux",
    "helm": "Helm", "prometheus": "Prometheus",
    "grafana": "Grafana", "ansible": "Ansible",
    "terraform": "Terraform", "jenkins": "Jenkins",
    "bitbucket": "Bitbucket", "pandas": "Pandas",
    "matplotlib": "Matplotlib", "seaborn": "Seaborn",
    "plotly": "Plotly", "scipy": "SciPy",
    "flask": "Flask", "django": "Django", "laravel": "Laravel",
    "rails": "Rails", "gin": "Gin", "fiber": "Fiber",
    "angular": "Angular", "vue": "Vue.js", "react": "React",
    "dart": "Dart", "lua": "Lua", "julia": "Julia",
    "perl": "Perl", "swift": "Swift", "kotlin": "Kotlin",
    "ruby": "Ruby", "php": "PHP", "golang": "Go", "rust": "Rust",
    "scala": "Scala", "java": "Java", "python": "Python",
    "shell": "Shell", "bash": "Bash", "matlab": "MATLAB",
    "neo4j": "Neo4j", "couchdb": "CouchDB",
    "mariadb": "MariaDB", "oracle": "Oracle",
    "sqlite": "SQLite", "sql server": "SQL Server",
    "intellij": "IntelliJ", "eclipse": "Eclipse",
    "object detection": "Object Detection",
    "image segmentation": "Image Segmentation",
    "time series": "Time Series",
    "feature engineering": "Feature Engineering",
    "model deployment": "Model Deployment",
    "computer vision": "Computer Vision",
    "reinforcement learning": "Reinforcement Learning",
    "natural language processing": "NLP",
    "neural networks": "Neural Networks",
    "gradient boosting": "Gradient Boosting",
    "decision trees": "Decision Trees",
    "random forest": "Random Forest",
    "large language models": "LLM",
    "retrieval augmented generation": "RAG",
    "machine learning": "Machine Learning",
    "deep learning": "Deep Learning",
    "microservices": "Microservices",
    "grpc": "gRPC", "nestjs": "NestJS", "nest.js": "NestJS",
    "airflow": "Apache Airflow", "apache airflow": "Apache Airflow",
    "kafka": "Kafka", "apache kafka": "Kafka",
    "express": "Express", "express.js": "Express",
    "spring": "Spring Boot", "spring boot": "Spring Boot",
    "spring framework": "Spring Boot",
    "github": "GitHub", "gitlab": "GitLab", "git": "Git",
    "linux": "Linux", "powershell": "PowerShell",
    "go": "Go", "c++": "C++", "c#": "C#", "r": "R", "c": "C",
}


def strip_projects_from_text(text: str) -> str:
    if not text:
        return ""
    section_pattern = (
        r'(?is)(?:PROJECTS|PERSONAL\s+PROJECTS|ACADEMIC\s+PROJECTS|KEY\s+PROJECTS'
        r'|TECHNICAL\s+PROJECTS|PROJECT\s+WORK|PROJECT\s+DETAILS|MAJOR\s+PROJECTS'
        r'|MINI\s+PROJECTS|PROJECTS\s*&\s*EXPERIENCE|PROJECTS\s*/\s*ASSIGNMENTS'
        r'|PROJECTS\s*&\s*IMPLEMENTATIONS)[\s:#\-_=]*\n[\s\S]*?'
        r'(?=\n\s*(?:EXPERIENCE|WORK\s+EXPERIENCE|EMPLOYMENT\s+HISTORY'
        r'|PROFESSIONAL\s+EXPERIENCE|EDUCATION|ACADEMIC\s+BACKGROUND|ACADEMICS'
        r'|SKILLS|TECHNICAL\s+SKILLS|CORE\s+COMPETENCIES|CERTIFICATIONS|LICENSES'
        r'|PUBLICATIONS|AWARDS|DECLARATION|INTERESTS|ACTIVITIES|HOBBIES'
        r'|EXTRA\s+CURRICULAR|$))'
    )
    cleaned = re.sub(section_pattern, '\n', text)

    cleaned_lines = []
    for line in cleaned.splitlines():
        line_s = line.strip()
        if re.match(
            r'(?i)^(?:Project\s*\d*|Project\s+Title|Project\s+Name|Technologies'
            r'|Tech\s+Stack|Tools\s+Used|Tools\s*&\s*Technologies|Environment'
            r'|Frameworks\s+used)\s*:',
            line_s
        ):
            continue
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines)


def _add(found_list, seen_global, key, formatted):
    """Add formatted skill to found_list if not already globally seen."""
    k = key.lower()
    if k not in seen_global:
        found_list.append(formatted)
        seen_global.add(k)


def extract_skills(text: str, exclude_projects: bool = False) -> dict:
    """Extract categorized skills from resume or JD text.

    Args:
        text: Input text.
        exclude_projects: If True, strips the Projects section before matching.
                          Defaults to False so skills inside projects are captured.
    Returns:
        Dict mapping category -> sorted list of canonical skill names.
    """
    if not text:
        return {}

    target_text = strip_projects_from_text(text) if exclude_projects else text
    text_lower = target_text.lower()
    extracted_by_category = {}
    seen_global: set = set()  # canonical-key dedup across all categories

    for category, skill_list in SKILL_DICTIONARY.items():
        found_in_cat = []

        for skill in skill_list:

            # ---- Context-aware / special-cased skills ----

            if skill == "r":
                r_pattern = (
                    r'(?i)(?:'
                    r'(?:languages?|programming|skills?|technologies?|tech\s+stack|tools?'
                    r'|proficien\w+|experience\s+(?:in|with)|knowledge\s+of|working\s+with'
                    r'|using)[:\s][^\n]*\b[rR]\b'
                    r'|\b[rR]\s*,\s*(?:python|java|c\+\+|c#|sql|matlab|julia|sas|scala|pandas|numpy)'
                    r'|\b(?:python|java|c\+\+|c#|sql|matlab|julia|sas|scala|pandas|numpy)\s*,\s*[rR]\b'
                    r'|\b[rR]\s+(?:programming|language|scripting|studio|package)\b'
                    r'|(?:^|[\n,;•|/(\[])\\s*[rR]\s*(?:[,;•|/)\].]|\n|$))'
                )
                if re.search(r_pattern, target_text):
                    _add(found_in_cat, seen_global, "r", "R")

            elif skill == "c":
                c_pattern = (
                    r'(?i)(?:'
                    r'(?:languages?|programming|skills?|technologies?|tech\s+stack|tools?'
                    r'|proficien\w+|experience\s+(?:in|with)|knowledge\s+of|working\s+with'
                    r'|using)[:\s][^\n]*\b[cC]\b'
                    r'|\b[cC]\s*,\s*(?:c\+\+|c#|java|python|sql|assembly|rust|go|matlab|bash)'
                    r'|\b(?:c\+\+|c#|java|python|sql|assembly|rust|go|matlab|bash)\s*,\s*[cC]\b'
                    r'|\b[cC]\s+(?:programming|language)\b'
                    r'|(?:^|[\n,;•|/(\[])\\s*[cC]\s*(?:[,;•|/)\].]|\n|$))'
                )
                if re.search(c_pattern, target_text):
                    _add(found_in_cat, seen_global, "c", "C")

            elif skill == "c++":
                if re.search(r'(?i)(?:^|[\s,;•|/])c\+\+(?:$|[\s,;•|/.,;:])', text_lower):
                    _add(found_in_cat, seen_global, "c++", "C++")

            elif skill == "c#":
                if re.search(r'(?i)(?:^|[\s,;•|/])c#(?:$|[\s,;•|/.,;:])', text_lower):
                    _add(found_in_cat, seen_global, "c#", "C#")

            elif skill in ("go", "golang"):
                go_pattern = (
                    r'(?:(?i:\bgolang\b|\bgo\s+(?:lang|programming|language|developer|backend)\b'
                    r'|(?:languages?|skills?|technologies?|tech\s+stack|requirements?'
                    r'|proficien\w+|experience\s+(?:in|with)|using)[:\s][^\n]*\bgo\b))'
                    r'|(?:^|[\n,;•|/(\[-])\s*(?:[Gg]o|GO)\s*(?:[,;•|/)\].-]|\n|$)'
                )
                if re.search(go_pattern, target_text):
                    _add(found_in_cat, seen_global, "go", "Go")

            elif skill in ("spring", "spring boot", "spring framework"):
                spring_pattern = (
                    r'(?i)(?:\bspring\s+(?:boot|framework|data|security|mvc|cloud|batch|jpa)\b'
                    r'|(?:languages?|frameworks?|technologies?|tech\s+stack|skills?|proficien\w+)'
                    r'[:\s][^\n]*\bspring\b'
                    r'|\b(?:java|hibernate|kotlin)\s*,\s*spring\b'
                    r'|\bspring\s*,\s*(?:java|hibernate|kotlin)\b)'
                )
                if re.search(spring_pattern, target_text):
                    _add(found_in_cat, seen_global, "spring boot", "Spring Boot")

            elif skill in ("spark", "apache spark", "pyspark"):
                spark_pattern = (
                    r'(?i)(?:\bapache\s+spark\b|\bpyspark\b'
                    r'|\bspark\s+(?:sql|streaming|core|rdd|mllib)\b'
                    r'|(?:technologies?|tech\s+stack|skills?|tools?)[:\s][^\n]*\bspark\b'
                    r'|\b(?:hadoop|kafka|flink)\s*,\s*spark\b'
                    r'|\bspark\s*,\s*(?:hadoop|kafka|flink)\b)'
                )
                if re.search(spark_pattern, target_text):
                    _add(found_in_cat, seen_global, "apache spark", "Apache Spark")

            elif skill in ("express", "express.js"):
                express_pattern = (
                    r'(?i)(?:\bexpress\.?js\b|\bnode(?:\.js)?[\w\s/]*express\b'
                    r'|(?:frameworks?|technologies?|skills?)[:\s][^\n]*\bexpress\b'
                    r'|\b(?:node|react|mongodb)\s*,\s*express\b'
                    r'|\bexpress\s*,\s*(?:node|react|mongodb)\b)'
                )
                if re.search(express_pattern, target_text):
                    _add(found_in_cat, seen_global, "express", "Express")

            elif skill in ("kafka", "apache kafka"):
                if re.search(r'(?i)\bkafka\b', target_text):
                    _add(found_in_cat, seen_global, "kafka", "Kafka")

            elif skill in ("airflow", "apache airflow"):
                if re.search(r'(?i)\b(?:apache\s+)?airflow\b', target_text):
                    _add(found_in_cat, seen_global, "apache airflow", "Apache Airflow")

            elif skill in ("nestjs", "nest.js"):
                if re.search(r'(?i)\bnest\.?js\b', target_text):
                    _add(found_in_cat, seen_global, "nestjs", "NestJS")

            elif skill in ("next.js", "nextjs"):
                if re.search(r'(?i)\bnext\.?js\b', target_text):
                    _add(found_in_cat, seen_global, "next.js", "Next.js")

            elif skill in ("node.js", "nodejs"):
                if re.search(r'(?i)\bnode\.?js\b', target_text):
                    _add(found_in_cat, seen_global, "node.js", "Node.js")

            elif skill in ("three.js", "threejs"):
                if re.search(r'(?i)\bthree\.?js\b', target_text):
                    _add(found_in_cat, seen_global, "three.js", "Three.js")

            elif skill in ("git", "github", "gitlab", "bitbucket"):
                if re.search(r'(?i)\b' + re.escape(skill) + r'\b', target_text):
                    _add(found_in_cat, seen_global, skill, FMT_MAP.get(skill, skill.title()))

            elif skill in ("linux", "bash", "shell", "powershell"):
                if re.search(r'(?i)\b' + re.escape(skill) + r'\b', target_text):
                    _add(found_in_cat, seen_global, skill, FMT_MAP.get(skill, skill.title()))

            elif skill == "microservices":
                if re.search(r'(?i)\bmicroservices?\b', target_text):
                    _add(found_in_cat, seen_global, "microservices", "Microservices")

            elif skill == "grpc":
                if re.search(r'(?i)\bgrpc\b', target_text):
                    _add(found_in_cat, seen_global, "grpc", "gRPC")

            elif skill == "etl":
                if re.search(r'(?i)\betl\b', target_text):
                    _add(found_in_cat, seen_global, "etl", "ETL")

            elif skill == "github actions":
                if re.search(r'(?i)\bgithub\s+actions\b', target_text):
                    _add(found_in_cat, seen_global, "github actions", "GitHub Actions")

            elif skill == "data pipeline":
                if re.search(r'(?i)\bdata\s+pipelines?\b', target_text):
                    _add(found_in_cat, seen_global, "data pipeline", "Data Pipelines")

            elif skill == "data warehousing":
                if re.search(r'(?i)\bdata\s+warehous\w*\b', target_text):
                    _add(found_in_cat, seen_global, "data warehousing", "Data Warehousing")

            elif skill == "web scraping":
                if re.search(r'(?i)\bweb\s+scrap\w*\b', target_text):
                    _add(found_in_cat, seen_global, "web scraping", "Web Scraping")

            elif skill in ("material ui", "mui"):
                if re.search(r'(?i)(?:\bmaterial[\s-]ui\b|\bmui\b)', target_text):
                    _add(found_in_cat, seen_global, "material ui", "Material UI")

            elif skill == "power bi":
                if re.search(r'(?i)\bpower\s+bi\b', target_text):
                    _add(found_in_cat, seen_global, "power bi", "Power BI")

            elif skill == "sql server":
                if re.search(r'(?i)\bsql\s+server\b', target_text):
                    _add(found_in_cat, seen_global, "sql server", "SQL Server")

            elif skill == "amazon web services":
                if re.search(r'(?i)\bamazon\s+web\s+services\b', target_text):
                    _add(found_in_cat, seen_global, "aws", "AWS")

            elif skill == "google cloud":
                if re.search(r'(?i)\bgoogle\s+cloud\b', target_text):
                    _add(found_in_cat, seen_global, "gcp", "GCP")

            elif skill in ("rest api", "rest apis", "restful api", "restful", "restapi"):
                if re.search(r'(?i)(?:\brest\s+api\b|\brestful\b|\brest\b\s+(?:api|service))', target_text):
                    _add(found_in_cat, seen_global, "rest apis", "REST APIs")

            elif skill in ("tailwind", "tailwindcss"):
                if re.search(r'(?i)\btailwind(?:\s+css)?\b', target_text):
                    _add(found_in_cat, seen_global, "tailwind", "Tailwind CSS")

            elif skill == "sklearn":
                if re.search(r'(?i)\bsklearn\b', target_text):
                    _add(found_in_cat, seen_global, "scikit-learn", "scikit-learn")

            elif skill == "cicd":
                if re.search(r'(?i)\bci/?cd\b', target_text):
                    _add(found_in_cat, seen_global, "ci/cd", "CI/CD")

            elif skill == "html5":
                if re.search(r'(?i)\bhtml5?\b', target_text):
                    _add(found_in_cat, seen_global, "html", "HTML")

            elif skill == "css3":
                if re.search(r'(?i)\bcss3?\b', target_text):
                    _add(found_in_cat, seen_global, "css", "CSS")

            elif skill == "k8s":
                if re.search(r'(?i)\bk8s\b', target_text):
                    _add(found_in_cat, seen_global, "kubernetes", "Kubernetes")

            elif skill in ("jupyter notebook", "colab", "google colab"):
                # handled after the loop to avoid double-adding
                pass

            else:
                # Generic word-boundary match
                esc = re.escape(skill)
                pattern = r'(?i)(?:^|(?<=\W))' + esc + r'(?:$|(?=\W))'
                if re.search(pattern, text_lower):
                    formatted = FMT_MAP.get(skill, skill.title())
                    canonical_key = formatted.lower()
                    if canonical_key not in seen_global:
                        found_in_cat.append(formatted)
                        seen_global.add(canonical_key)

        if found_in_cat:
            extracted_by_category[category] = sorted(list(set(found_in_cat)))

    # Handle Jupyter / Colab aliases
    _handle_jupyter_colab(target_text, extracted_by_category, seen_global)

    return {k: v for k, v in extracted_by_category.items() if v}


def _handle_jupyter_colab(text: str, result: dict, seen_global: set):
    """Detect Jupyter Notebook and Google Colab separately to avoid alias conflicts."""
    if re.search(r'(?i)\bjupyter(?:\s+notebook)?\b', text) and "jupyter notebook" not in seen_global:
        result.setdefault("Tools", [])
        result["Tools"] = sorted(list(set(result["Tools"] + ["Jupyter Notebook"])))
        seen_global.add("jupyter notebook")
    if re.search(r'(?i)\bgoogle\s+colab\b|\bcolab\b', text) and "google colab" not in seen_global:
        result.setdefault("Tools", [])
        result["Tools"] = sorted(list(set(result["Tools"] + ["Google Colab"])))
        seen_global.add("google colab")
