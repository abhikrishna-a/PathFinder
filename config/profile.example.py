PROFILE = {
    "name": "Your Name",
    "email": "you@example.com",
    "phone": "+91 XXXXXXXXXX",
    "role": "Python Developer",
    "experience_years": 1,
    "experience_min": 0,
    "experience_max": 3,
    "location": "Your City, State",
    "github": "https://github.com/yourusername",
    "linkedin": "https://www.linkedin.com/in/yourusername",
    "portfolio": "https://yourportfolio.dev",
    "skills": {
        "backend": [
            "Python", "Django", "DRF", "Django REST Framework", "PostgreSQL",
            "Celery", "Redis", "REST API", "FastAPI",
        ],
        "frontend": [
            "React", "React.js", "TypeScript", "JavaScript",
            "Tailwind CSS", "Bootstrap",
        ],
        "ai_llm": [
            "LLM", "AI",
        ],
        "cloud": [
            "AWS", "EC2", "RDS", "S3", "CloudFront",
        ],
        "devops": [
            "Docker", "Docker Compose", "GitHub Actions", "CI/CD", "Git",
        ],
        "tools": [
            "pytest", "Swagger", "OpenAPI", "JWT", "RBAC",
        ],
    },
    "projects": [
        {
            "name": "ProjectOne",
            "description": "Short description of what it does",
            "tech": ["Django", "DRF", "PostgreSQL", "React", "Docker"],
        },
        {
            "name": "ProjectTwo",
            "description": "Another project description",
            "tech": ["Django", "PostgreSQL", "Bootstrap"],
        },
    ],
    "education": "Your Degree - Your College, University (20XX-20XX)",
    "languages": ["English"],
    "looking_for": [
        "Python Developer", "Django Developer", "Full Stack Developer",
        "Backend Developer", "Python Backend Developer",
    ],
}

SKILL_WEIGHTS = {
    "python": 20, "django": 20, "drf": 15, "django rest framework": 15,
    "postgresql": 15, "rest api": 10, "fastapi": 10, "celery": 8,
    "redis": 8, "react": 8, "docker": 8, "aws": 8, "typescript": 5,
    "cicd": 5, "ci/cd": 5, "git": 3, "github actions": 5,
    "javascript": 3, "sql": 3, "jwt": 5, "rbac": 3,
    "tailwind": 3, "bootstrap": 2, "ec2": 5, "rds": 5, "s3": 5,
    "gunicorn": 3, "pytest": 2, "swagger": 2, "openapi": 2,
    "llm": 5, "ai": 5, "vercel": 2,
}

SKILL_CATEGORIES = {
    "must_have": ["python", "django"],
    "nice_to_have": ["drf", "postgresql", "celery", "redis", "rest api", "fastapi"],
    "bonus": ["react", "docker", "aws", "typescript", "cicd"],
}
