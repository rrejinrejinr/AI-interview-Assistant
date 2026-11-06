import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.ats_score import calculate_ats_score

STRONG_RESUME = """
John Doe
john@example.com | +1 555-0199 | San Francisco, CA | linkedin.com/in/johndoe | github.com/johndoe

Summary:
Senior Software Engineer with 6+ years of experience architecting distributed backend systems and high-throughput microservices.

Education:
B.S. in Computer Science, UC Berkeley, 2018. GPA: 3.85

Experience:
Senior Backend Engineer, CloudCorp (2021 - Present)
• Architected a real-time event streaming pipeline processing 25,000 requests per second using Go, Kafka, and PostgreSQL, reducing message latency by 45%.
• Deployed 14 containerized microservices to Kubernetes clusters across AWS multi-region infrastructure using Terraform and CI/CD pipelines.
• Optimized PostgreSQL query performance by introducing Redis caching and partitioned indexes, saving $120,000 annually in database compute costs.
• Spearheaded migration from monolithic Ruby service to Go gRPC microservices with 99.99% uptime SLA.

Software Engineer, DataSystems (2018 - 2021)
• Built RESTful APIs using Python, FastAPI, and Docker supporting 500,000 active web users.
• Designed automated integration testing suite with 88% code coverage, cutting production deployment incidents by 35%.

Skills:
Languages: Go, Python, SQL, Bash
Frameworks & Tools: FastAPI, Docker, Kubernetes, AWS, Kafka, Redis, PostgreSQL, Terraform, Git, CI/CD
Certifications: AWS Certified Solutions Architect
"""

AVERAGE_RESUME = """
Jane Smith
jane@example.com | 555-0144

Education:
Bachelor of Engineering in Information Technology, State University, 2023

Projects:
Online Book Store
• Created an online bookstore website using Python, Flask, and SQLite.
• Implemented user login and registration with basic session management.
• Added a shopping cart feature and order history page.

Weather App
• Developed a weather application using JavaScript, HTML, and CSS.
• Connected to OpenWeather API to display current temperature.

Skills:
Python, JavaScript, Flask, HTML, CSS, SQLite, Git
"""

WEAK_RESUME = """
Candidate Resume
Email: user@example.com

Looking for an entry level software role.

Skills:
Java, C, Python

Hobbies:
Reading books, gaming.
"""

KEYWORD_STUFFED_RESUME = """
Candidate Resume
contact@example.com | 555-9999

Skills:
Python, Java, C++, Go, Rust, React, Node.js, Next.js, Express, Spring Boot,
Docker, Kubernetes, AWS, GCP, Azure, Terraform, Ansible, Kafka, RabbitMQ,
PostgreSQL, MySQL, MongoDB, Redis, Cassandra, GraphQL, REST APIs, Linux, Git

Education:
B.Tech Computer Science, 2022
"""

EMPTY_STUB_RESUME = """
Resume
Phone: 123456
"""

def test_current_5_tier_scores():
    r_strong = calculate_ats_score(STRONG_RESUME)
    r_avg = calculate_ats_score(AVERAGE_RESUME)
    r_weak = calculate_ats_score(WEAK_RESUME)
    r_stuffed = calculate_ats_score(KEYWORD_STUFFED_RESUME)

    print("\n--- 5-Tier Resume Score Benchmark ---")
    print(f"Strong: ats={r_strong['ats_score']}, structure={r_strong['structure_score']}, skill={r_strong['skill_density_score']}, length={r_strong['length_score']}")
    print(f"Average: ats={r_avg['ats_score']}, structure={r_avg['structure_score']}, skill={r_avg['skill_density_score']}, length={r_avg['length_score']}")
    print(f"Weak: ats={r_weak['ats_score']}, structure={r_weak['structure_score']}, skill={r_weak['skill_density_score']}, length={r_weak['length_score']}")
    print(f"Keyword Stuffed: ats={r_stuffed['ats_score']}, structure={r_stuffed['structure_score']}, skill={r_stuffed['skill_density_score']}, length={r_stuffed['length_score']}")
    
    with pytest.raises(Exception):
        calculate_ats_score("")
