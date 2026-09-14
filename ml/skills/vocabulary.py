"""Curated skill vocabulary with aliases for V1 extraction/matching."""

from __future__ import annotations

# Canonical skill -> aliases (lowercase). Canonical names are display forms.
SKILL_VOCAB: dict[str, list[str]] = {
    # Languages
    "Python": ["python", "python3", "py"],
    "Java": ["java"],
    "JavaScript": ["javascript", "js", "ecmascript"],
    "TypeScript": ["typescript", "ts"],
    "SQL": ["sql", "structured query language"],
    "R": ["r programming", "r language"],
    "C++": ["c++", "cpp", "cplusplus"],
    "C#": ["c#", "csharp", "c sharp"],
    "Go": ["golang", "go lang"],
    "Rust": ["rust"],
    "Scala": ["scala"],
    "Kotlin": ["kotlin"],
    "Swift": ["swift"],
    "Ruby": ["ruby"],
    "PHP": ["php"],
    "Bash": ["bash", "shell scripting", "shell script"],
    # Data / ML
    "Machine Learning": ["machine learning", "ml"],
    "Deep Learning": ["deep learning", "dl"],
    "Natural Language Processing": [
        "natural language processing",
        "nlp",
        "computational linguistics",
    ],
    "Computer Vision": ["computer vision", "cv"],
    "Data Analysis": ["data analysis", "data analytics"],
    "Data Science": ["data science"],
    "Data Engineering": ["data engineering"],
    "Statistics": ["statistics", "statistical analysis"],
    "Feature Engineering": ["feature engineering"],
    "Model Evaluation": ["model evaluation", "model validation"],
    "A/B Testing": ["a/b testing", "ab testing", "split testing"],
    "Recommendation Systems": [
        "recommendation systems",
        "recommender systems",
        "recommendations",
    ],
    # ML libraries / frameworks
    "PyTorch": ["pytorch", "torch"],
    "TensorFlow": ["tensorflow", "tf"],
    "scikit-learn": ["scikit-learn", "sklearn", "scikit learn"],
    "Hugging Face": ["hugging face", "huggingface", "transformers library"],
    "spaCy": ["spacy"],
    "NLTK": ["nltk"],
    "OpenCV": ["opencv", "cv2"],
    "XGBoost": ["xgboost"],
    "LightGBM": ["lightgbm"],
    "Keras": ["keras"],
    "LangChain": ["langchain"],
    # Data stack
    "Pandas": ["pandas"],
    "NumPy": ["numpy"],
    "Apache Spark": ["apache spark", "spark", "pyspark"],
    "Hadoop": ["hadoop"],
    "Airflow": ["airflow", "apache airflow"],
    "dbt": ["dbt", "data build tool"],
    "Kafka": ["kafka", "apache kafka"],
    "ETL": ["etl", "extract transform load"],
    # Databases
    "PostgreSQL": ["postgresql", "postgres"],
    "MySQL": ["mysql"],
    "MongoDB": ["mongodb", "mongo"],
    "Redis": ["redis"],
    "Elasticsearch": ["elasticsearch", "elastic search"],
    "Snowflake": ["snowflake"],
    "BigQuery": ["bigquery", "google bigquery"],
    "DynamoDB": ["dynamodb"],
    # Backend / web
    "FastAPI": ["fastapi"],
    "Flask": ["flask"],
    "Django": ["django"],
    "REST APIs": ["rest apis", "rest api", "restful", "rest"],
    "GraphQL": ["graphql"],
    "Node.js": ["node.js", "nodejs", "node"],
    "Express": ["express", "express.js", "expressjs"],
    "Spring Boot": ["spring boot", "springboot"],
    # Frontend
    "React": ["react", "react.js", "reactjs"],
    "Next.js": ["next.js", "nextjs"],
    "Vue.js": ["vue.js", "vuejs", "vue"],
    "HTML": ["html", "html5"],
    "CSS": ["css", "css3"],
    "Tailwind CSS": ["tailwind css", "tailwind"],
    # Cloud / DevOps
    "AWS": ["aws", "amazon web services"],
    "GCP": ["gcp", "google cloud", "google cloud platform"],
    "Azure": ["azure", "microsoft azure"],
    "Docker": ["docker", "containerization"],
    "Kubernetes": ["kubernetes", "k8s"],
    "CI/CD": ["ci/cd", "cicd", "continuous integration", "continuous deployment"],
    "Terraform": ["terraform"],
    "Linux": ["linux"],
    "Git": ["git", "version control"],
    "GitHub Actions": ["github actions"],
    # Practices / soft-adjacent technical
    "Agile": ["agile", "scrum"],
    "System Design": ["system design", "distributed systems"],
    "Microservices": ["microservices", "micro services"],
    "Unit Testing": ["unit testing", "unit tests", "pytest", "junit"],
    "MLOps": ["mlops", "ml ops"],
    "LLM": ["llm", "large language models", "large language model"],
    "Prompt Engineering": ["prompt engineering"],
    "RAG": ["rag", "retrieval augmented generation", "retrieval-augmented generation"],
    "Vector Databases": ["vector databases", "vector database", "vectordb", "pinecone", "faiss"],
    "Power BI": ["power bi", "powerbi"],
    "Tableau": ["tableau"],
    "Excel": ["excel", "microsoft excel"],
}


def build_alias_lookup() -> dict[str, str]:
    """Map normalized alias text -> canonical skill name."""
    lookup: dict[str, str] = {}
    for canonical, aliases in SKILL_VOCAB.items():
        lookup[_normalize_key(canonical)] = canonical
        for alias in aliases:
            lookup[_normalize_key(alias)] = canonical
    return lookup


def _normalize_key(text: str) -> str:
    return " ".join(text.lower().strip().split())


ALIAS_TO_CANONICAL = build_alias_lookup()

# Longest aliases first so "machine learning" wins over "ml" inside phrase scans
ALIASES_BY_LENGTH = sorted(ALIAS_TO_CANONICAL.keys(), key=len, reverse=True)
