"""Optional short descriptions to improve skill-name embeddings."""

from __future__ import annotations

# Kept small and editable. Skills without an entry fall back to the name.
SKILL_DESCRIPTIONS: dict[str, str] = {
    "Python": "Python programming language for software and data",
    "Java": "Java JVM backend programming language",
    "JavaScript": "JavaScript ECMAScript language for web frontends",
    "TypeScript": "TypeScript typed JavaScript language",
    "SQL": "SQL database query language",
    "R": "R programming language for statistics",
    "C++": "C++ systems programming language",
    "C#": "C# programming language on .NET",
    "Go": "Go golang programming language",
    "Rust": "Rust systems programming language",
    "Deep Learning": "deep learning neural networks",
    "Machine Learning": "machine learning model training and prediction",
    "Natural Language Processing": (
        "natural language processing text NLP linguistics"
    ),
    "Computer Vision": "computer vision image recognition",
    "Data Analysis": "data analysis analytics",
    "Data Science": "data science applied statistics modeling",
    "Data Engineering": "data engineering pipelines ETL",
    "PyTorch": "PyTorch deep learning framework",
    "TensorFlow": "TensorFlow deep learning framework",
    "scikit-learn": "scikit-learn classical machine learning library for model training",
    "Hugging Face": "Hugging Face transformers NLP models",
    "spaCy": "spaCy NLP natural language processing library",
    "NLTK": "NLTK natural language toolkit",
    "Pandas": "pandas dataframes data analysis library",
    "NumPy": "NumPy numerical arrays library",
    "Apache Spark": "Apache Spark distributed data processing",
    "Airflow": "Apache Airflow workflow orchestration",
    "Kafka": "Apache Kafka event streaming platform",
    "ETL": "ETL extract transform load data pipelines",
    "PostgreSQL": "PostgreSQL relational SQL database",
    "MySQL": "MySQL relational SQL database",
    "MongoDB": "MongoDB NoSQL document database",
    "Redis": "Redis in-memory cache database",
    "FastAPI": "FastAPI Python web API framework",
    "Flask": "Flask Python web API framework",
    "Django": "Django Python web framework",
    "REST APIs": "REST HTTP web API interface design and endpoints",
    "GraphQL": "GraphQL web API query interface alternative to REST",
    "Node.js": "Node.js JavaScript runtime backend",
    "React": "React JavaScript frontend UI library",
    "Next.js": "Next.js React web framework",
    "AWS": "Amazon Web Services cloud platform",
    "GCP": "Google Cloud Platform",
    "Azure": "Microsoft Azure cloud platform",
    "Docker": "Docker containerization",
    "Kubernetes": "Kubernetes container orchestration",
    "CI/CD": "CI/CD continuous integration and continuous deployment automation pipelines",
    "GitHub Actions": "GitHub Actions CI/CD continuous integration deployment workflows",
    "Terraform": "Terraform infrastructure as code",
    "Git": "Git version control",
    "MLOps": "MLOps machine learning operations",
    "LLM": "large language models LLM generative AI",
    "RAG": "retrieval augmented generation RAG",
    "Vector Databases": "vector database embeddings search",
}


def describe_skill(skill: str) -> str:
    return SKILL_DESCRIPTIONS.get(skill, skill)
