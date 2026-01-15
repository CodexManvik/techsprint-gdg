DIFFICULTY_PROMPTS = {
    "Junior": {
        "name": "Junior (0-2 years)",
        "prompt": "Ask foundational questions about basic concepts, syntax, and simple problem-solving. Be encouraging and educational. Focus on learning potential."
    },
    "Mid-Level": {
        "name": "Mid-Level (2-5 years)",
        "prompt": "Ask applied questions requiring practical experience. Expect candidates to explain trade-offs, debug issues, and design small systems. Probe for depth."
    },
    "Senior": {
        "name": "Senior (5-8 years)",
        "prompt": "Ask complex system design questions. Expect architectural thinking, scalability considerations, and leadership examples. Challenge assumptions and look for edge cases."
    },
    "Staff+": {
        "name": "Staff/Principal (8+ years)",
        "prompt": "Ask open-ended, ambiguous problems requiring strategic thinking. Expect candidates to drive the conversation, identify constraints, and propose multiple solutions. Be highly critical of technical depth and business impact."
    }
}

TOPICS = {
    "System Design": "Distributed systems, scalability, databases, caching, load balancing, microservices",
    "Algorithms": "Data structures, time/space complexity, dynamic programming, graphs, trees, sorting",
    "Frontend": "React, JavaScript, CSS, performance optimization, accessibility, state management",
    "Backend": "APIs, databases, authentication, caching, message queues, server architecture",
    "DevOps": "CI/CD, Docker, Kubernetes, monitoring, infrastructure as code, cloud platforms",
    "Machine Learning": "ML algorithms, model training, feature engineering, deployment, ethics",
    "Data Structures": "Arrays, linked lists, trees, graphs, hash tables, heaps, tries",
    "Behavioral": "Leadership, conflict resolution, project management, communication, teamwork",
    "Mobile": "iOS, Android, React Native, mobile architecture, offline-first, performance",
    "Security": "Authentication, authorization, encryption, OWASP, secure coding, compliance"
}

def get_difficulty_prompt(level: str):
    return DIFFICULTY_PROMPTS.get(level, DIFFICULTY_PROMPTS["Mid-Level"])["prompt"]

def get_difficulty_list():
    return {key: val["name"] for key, val in DIFFICULTY_PROMPTS.items()}

def get_topics_list():
    return TOPICS
