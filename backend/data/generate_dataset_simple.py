#!/usr/bin/env python3
"""
Dataset Generation Script for Talent Co-Pilot
Generates synthetic employee and project datasets based on real-world data patterns.
"""

import pandas as pd
import numpy as np
import random
from datetime import datetime, date, timedelta
from typing import List, Dict, Any
import json
import os
from faker import Faker
from faker.providers import internet, company, lorem
import uuid

# Initialize Faker for generating synthetic data
fake = Faker()
fake.add_provider(internet)
fake.add_provider(company)
fake.add_provider(lorem)

# Set random seed for reproducibility
random.seed(42)
np.random.seed(42)

class DatasetGenerator:
    def __init__(self, csv_file_path: str = "Employee.csv", project_csv_path: str = "project_description_for_er.csv"):
        """Initialize the dataset generator with real employee data"""
        self.csv_file_path = csv_file_path
        self.project_csv_path = project_csv_path
        self.real_employees_df = None
        self.real_projects_df = None
        self.load_real_data()
        
        # Define skill categories and technologies
        self.skill_categories = {
            "frontend": [
                "React", "Vue.js", "Angular", "JavaScript", "TypeScript", 
                "HTML", "CSS", "SASS", "Bootstrap", "Tailwind CSS",
                "Webpack", "Vite", "Next.js", "Nuxt.js", "Svelte", "Ember.js"
            ],
            "backend": [
                "Python", "Java", "Node.js", "C#", "Go", "Rust", "PHP",
                "Django", "Flask", "Express.js", "Spring Boot", "ASP.NET",
                "FastAPI", "Laravel", "Ruby on Rails", "Koa.js", "Nest.js"
            ],
            "database": [
                "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch",
                "SQLite", "Oracle", "SQL Server", "Cassandra", "DynamoDB",
                "Neo4j", "CouchDB", "InfluxDB", "TimescaleDB"
            ],
            "devops": [
                "Docker", "Kubernetes", "AWS", "Azure", "GCP", "Jenkins",
                "GitLab CI", "GitHub Actions", "Terraform", "Ansible",
                "Prometheus", "Grafana", "ELK Stack", "Helm", "Istio"
            ],
            "mobile": [
                "React Native", "Flutter", "iOS", "Android", "Swift",
                "Kotlin", "Xamarin", "Ionic", "Cordova", "Unity"
            ],
            "data_science": [
                "Python", "R", "SQL", "Pandas", "NumPy", "Scikit-learn",
                "TensorFlow", "PyTorch", "Jupyter", "Apache Spark",
                "Tableau", "Power BI", "Matplotlib", "Seaborn", "Keras"
            ],
            "testing": [
                "Jest", "Cypress", "Selenium", "JUnit", "Pytest",
                "Mocha", "Chai", "TestNG", "Cucumber", "Postman",
                "Playwright", "WebDriver", "Karma", "Jasmine"
            ],
            "design": [
                "Figma", "Sketch", "Adobe XD", "Photoshop", "Illustrator",
                "InVision", "Principle", "Framer", "Canva", "Zeplin"
            ],
            "blockchain": [
                "Solidity", "Web3.js", "Ethereum", "Bitcoin", "Hyperledger",
                "Truffle", "Hardhat", "IPFS", "MetaMask"
            ],
            "ai_ml": [
                "TensorFlow", "PyTorch", "Keras", "OpenCV", "NLTK",
                "spaCy", "Hugging Face", "MLflow", "Kubeflow"
            ],
            "security": [
                "OWASP", "Penetration Testing", "Cryptography", "SSL/TLS",
                "OAuth", "JWT", "Firewall", "VPN", "SIEM"
            ],
            "game_dev": [
                "Unity", "Unreal Engine", "C#", "C++", "OpenGL",
                "DirectX", "Blender", "Maya", "3ds Max"
            ]
        }
        
        
        # Role mappings based on education and experience
        self.role_mappings = {
            "junior": ["Junior Developer", "Associate Developer", "Trainee Developer"],
            "mid": ["Software Developer", "Full Stack Developer", "Backend Developer", "Frontend Developer"],
            "senior": ["Senior Developer", "Lead Developer", "Technical Lead", "Software Architect"],
            "expert": ["Principal Developer", "Staff Engineer", "Distinguished Engineer", "CTO"]
        }

    def load_real_data(self):
        """Load real employee and project data from CSV"""
        try:
            self.real_employees_df = pd.read_csv(self.csv_file_path)
            print(f"Loaded {len(self.real_employees_df)} real employee records")
        except FileNotFoundError:
            print(f"Warning: Could not find {self.csv_file_path}")
            self.real_employees_df = None
            
        try:
            print(f"Attempting to load CSV from: {self.project_csv_path}")
            print(f"File exists: {os.path.exists(self.project_csv_path)}")
            
            # Read CSV with proper handling of multi-line content
            self.real_projects_df = pd.read_csv(
                self.project_csv_path, 
                quotechar='"', 
                skipinitialspace=True,
                keep_default_na=False,  # Don't convert to NaN
                na_values=[]  # Don't treat any values as NaN
            )
            print(f"✅ Successfully loaded {len(self.real_projects_df)} real project descriptions")
            print(f"Columns: {list(self.real_projects_df.columns)}")
            print(f"DataFrame shape: {self.real_projects_df.shape}")
            print(f"First few rows preview:")
            print(self.real_projects_df.head(2))
            print(f"DataFrame is None: {self.real_projects_df is None}")
            print(f"DataFrame length: {len(self.real_projects_df) if self.real_projects_df is not None else 'N/A'}")
        except FileNotFoundError as e:
            print(f"❌ FileNotFoundError: Could not find {self.project_csv_path}")
            print(f"Error: {e}")
            self.real_projects_df = None
        except Exception as e:
            print(f"❌ Error loading CSV: {e}")
            self.real_projects_df = None

    def determine_role_level(self, education: str, experience: int, payment_tier: int) -> str:
        """Determine role level based on education, experience, and payment tier"""
        if experience <= 1:
            return "junior"
        elif experience <= 4:
            return "mid"
        elif experience <= 8:
            return "senior"
        else:
            return "expert"

    def generate_skills_for_employee(self, role_level: str, experience: int, education: str) -> List[str]:
        """Generate realistic skills based on role level and experience with enhanced diversity"""
        skills = []
        
        # Define employee archetypes for better diversity
        archetypes = [
            "frontend_specialist", "backend_specialist", "fullstack_developer", 
            "devops_engineer", "data_engineer", "mobile_developer", 
            "qa_engineer", "ui_ux_designer", "tech_lead", "data_scientist",
            "blockchain_developer", "ai_ml_engineer", "security_engineer", "game_developer"
        ]
        
        # Choose archetype based on role level and experience
        if role_level == "junior":
            archetype = random.choice(["frontend_specialist", "backend_specialist", "qa_engineer", "game_developer"])
            num_skills = random.randint(2, 4)
        elif role_level == "mid":
            archetype = random.choice(archetypes[:8])  # Exclude senior roles
            num_skills = random.randint(3, 6)
        elif role_level == "senior":
            archetype = random.choice(archetypes)
            num_skills = random.randint(4, 8)
        else:  # expert
            archetype = random.choice(["tech_lead", "fullstack_developer", "devops_engineer", "data_scientist", 
                                     "ai_ml_engineer", "security_engineer", "blockchain_developer"])
            num_skills = random.randint(5, 10)
        
        # Generate skills based on archetype
        skills = self._generate_skills_by_archetype(archetype, num_skills, experience)
        
        return skills
    
    def _generate_skills_by_archetype(self, archetype: str, num_skills: int, experience: int) -> List[str]:
        """Generate skills based on employee archetype for better diversity"""
        skills = []
        
        if archetype == "frontend_specialist":
            # Frontend specialist with some backend knowledge
            skills.extend(random.sample(self.skill_categories["frontend"], min(3, len(self.skill_categories["frontend"]))))
            if experience > 2:
                skills.extend(random.sample(self.skill_categories["backend"], min(2, len(self.skill_categories["backend"]))))
            skills.extend(random.sample(self.skill_categories["testing"], min(1, len(self.skill_categories["testing"]))))
            
        elif archetype == "backend_specialist":
            # Backend specialist with database and some frontend
            skills.extend(random.sample(self.skill_categories["backend"], min(3, len(self.skill_categories["backend"]))))
            skills.extend(random.sample(self.skill_categories["database"], min(2, len(self.skill_categories["database"]))))
            if experience > 3:
                skills.extend(random.sample(self.skill_categories["frontend"], min(1, len(self.skill_categories["frontend"]))))
            skills.extend(random.sample(self.skill_categories["testing"], min(1, len(self.skill_categories["testing"]))))
            
        elif archetype == "fullstack_developer":
            # Full-stack with balanced frontend/backend + devops
            skills.extend(random.sample(self.skill_categories["frontend"], min(2, len(self.skill_categories["frontend"]))))
            skills.extend(random.sample(self.skill_categories["backend"], min(2, len(self.skill_categories["backend"]))))
            skills.extend(random.sample(self.skill_categories["database"], min(1, len(self.skill_categories["database"]))))
            if experience > 4:
                skills.extend(random.sample(self.skill_categories["devops"], min(2, len(self.skill_categories["devops"]))))
            skills.extend(random.sample(self.skill_categories["testing"], min(1, len(self.skill_categories["testing"]))))
            
        elif archetype == "devops_engineer":
            # DevOps with infrastructure and some development
            skills.extend(random.sample(self.skill_categories["devops"], min(4, len(self.skill_categories["devops"]))))
            skills.extend(random.sample(self.skill_categories["backend"], min(2, len(self.skill_categories["backend"]))))
            skills.extend(random.sample(self.skill_categories["database"], min(1, len(self.skill_categories["database"]))))
            skills.extend(random.sample(self.skill_categories["testing"], min(1, len(self.skill_categories["testing"]))))
            
        elif archetype == "data_engineer":
            # Data engineering with backend and data science
            skills.extend(random.sample(self.skill_categories["data_science"], min(3, len(self.skill_categories["data_science"]))))
            skills.extend(random.sample(self.skill_categories["backend"], min(2, len(self.skill_categories["backend"]))))
            skills.extend(random.sample(self.skill_categories["database"], min(2, len(self.skill_categories["database"]))))
            if experience > 3:
                skills.extend(random.sample(self.skill_categories["devops"], min(1, len(self.skill_categories["devops"]))))
            
        elif archetype == "mobile_developer":
            # Mobile development with some backend
            skills.extend(random.sample(self.skill_categories["mobile"], min(3, len(self.skill_categories["mobile"]))))
            skills.extend(random.sample(self.skill_categories["backend"], min(1, len(self.skill_categories["backend"]))))
            skills.extend(random.sample(self.skill_categories["database"], min(1, len(self.skill_categories["database"]))))
            skills.extend(random.sample(self.skill_categories["testing"], min(1, len(self.skill_categories["testing"]))))
            
        elif archetype == "qa_engineer":
            # QA with testing and some development
            skills.extend(random.sample(self.skill_categories["testing"], min(3, len(self.skill_categories["testing"]))))
            skills.extend(random.sample(self.skill_categories["backend"], min(1, len(self.skill_categories["backend"]))))
            skills.extend(random.sample(self.skill_categories["frontend"], min(1, len(self.skill_categories["frontend"]))))
            if experience > 2:
                skills.extend(random.sample(self.skill_categories["devops"], min(1, len(self.skill_categories["devops"]))))
            
        elif archetype == "ui_ux_designer":
            # Design with some frontend development
            skills.extend(random.sample(self.skill_categories["design"], min(3, len(self.skill_categories["design"]))))
            skills.extend(random.sample(self.skill_categories["frontend"], min(2, len(self.skill_categories["frontend"]))))
            skills.extend(random.sample(self.skill_categories["testing"], min(1, len(self.skill_categories["testing"]))))
            
        elif archetype == "tech_lead":
            # Tech lead with broad knowledge
            skills.extend(random.sample(self.skill_categories["backend"], min(2, len(self.skill_categories["backend"]))))
            skills.extend(random.sample(self.skill_categories["frontend"], min(2, len(self.skill_categories["frontend"]))))
            skills.extend(random.sample(self.skill_categories["devops"], min(2, len(self.skill_categories["devops"]))))
            skills.extend(random.sample(self.skill_categories["database"], min(1, len(self.skill_categories["database"]))))
            skills.extend(random.sample(self.skill_categories["testing"], min(1, len(self.skill_categories["testing"]))))
            
        elif archetype == "data_scientist":
            # Data science with backend and database
            skills.extend(random.sample(self.skill_categories["data_science"], min(4, len(self.skill_categories["data_science"]))))
            skills.extend(random.sample(self.skill_categories["backend"], min(1, len(self.skill_categories["backend"]))))
            skills.extend(random.sample(self.skill_categories["database"], min(2, len(self.skill_categories["database"]))))
            if experience > 4:
                skills.extend(random.sample(self.skill_categories["devops"], min(1, len(self.skill_categories["devops"]))))
                
        elif archetype == "blockchain_developer":
            # Blockchain with web development
            skills.extend(random.sample(self.skill_categories["blockchain"], min(3, len(self.skill_categories["blockchain"]))))
            skills.extend(random.sample(self.skill_categories["backend"], min(2, len(self.skill_categories["backend"]))))
            skills.extend(random.sample(self.skill_categories["frontend"], min(1, len(self.skill_categories["frontend"]))))
            skills.extend(random.sample(self.skill_categories["devops"], min(1, len(self.skill_categories["devops"]))))
            
        elif archetype == "ai_ml_engineer":
            # AI/ML with infrastructure
            skills.extend(random.sample(self.skill_categories["ai_ml"], min(3, len(self.skill_categories["ai_ml"]))))
            skills.extend(random.sample(self.skill_categories["data_science"], min(2, len(self.skill_categories["data_science"]))))
            skills.extend(random.sample(self.skill_categories["backend"], min(1, len(self.skill_categories["backend"]))))
            skills.extend(random.sample(self.skill_categories["devops"], min(2, len(self.skill_categories["devops"]))))
            
        elif archetype == "security_engineer":
            # Security with development and infrastructure
            skills.extend(random.sample(self.skill_categories["security"], min(3, len(self.skill_categories["security"]))))
            skills.extend(random.sample(self.skill_categories["backend"], min(2, len(self.skill_categories["backend"]))))
            skills.extend(random.sample(self.skill_categories["devops"], min(2, len(self.skill_categories["devops"]))))
            skills.extend(random.sample(self.skill_categories["testing"], min(1, len(self.skill_categories["testing"]))))
            
        elif archetype == "game_developer":
            # Game development with some backend
            skills.extend(random.sample(self.skill_categories["game_dev"], min(3, len(self.skill_categories["game_dev"]))))
            skills.extend(random.sample(self.skill_categories["backend"], min(1, len(self.skill_categories["backend"]))))
            skills.extend(random.sample(self.skill_categories["database"], min(1, len(self.skill_categories["database"]))))
            skills.extend(random.sample(self.skill_categories["testing"], min(1, len(self.skill_categories["testing"]))))
        
        # Remove duplicates and limit to num_skills
        skills = list(set(skills))
        
        # If we have more skills than needed, randomly select
        if len(skills) > num_skills:
            skills = random.sample(skills, num_skills)
        
        return skills

    def generate_certifications(self, skills: List[str], experience: int) -> List[str]:
        """Generate relevant certifications based on skills and experience"""
        certifications = []
        
        # Common certifications
        common_certs = [
            "AWS Certified Developer", "AWS Solutions Architect", "Google Cloud Professional",
            "Microsoft Azure Fundamentals", "Docker Certified Associate", "Kubernetes Administrator",
            "Certified Scrum Master", "PMP Certification", "ITIL Foundation"
        ]
        
        # Technology-specific certifications
        tech_certs = {
            "AWS": ["AWS Certified Developer", "AWS Solutions Architect", "AWS DevOps Engineer"],
            "Docker": ["Docker Certified Associate", "Docker Certified Professional"],
            "Kubernetes": ["Certified Kubernetes Administrator", "Certified Kubernetes Application Developer"],
            "Python": ["Python Institute PCAP", "Python Institute PCPP"],
            "Java": ["Oracle Certified Professional", "Oracle Certified Master"],
            "React": ["React Professional Certificate", "Meta React Developer Certificate"]
        }
        
        # Add certifications based on skills
        for skill in skills:
            for tech, certs in tech_certs.items():
                if tech.lower() in skill.lower():
                    if random.random() < 0.3:  # 30% chance of having certification
                        certifications.extend(random.sample(certs, 1))
        
        # Add common certifications based on experience
        if experience >= 3 and random.random() < 0.4:
            certifications.extend(random.sample(common_certs, random.randint(1, 2)))
        
        return list(set(certifications))  # Remove duplicates

    def generate_past_projects(self, skills: List[str], experience: int) -> List[Dict[str, Any]]:
        """Generate past project history"""
        projects = []
        
        if experience == 0:
            return projects
        
        # Generate 1-3 past projects based on experience
        num_projects = min(experience // 2 + 1, 3)
        
        # Simple project templates for past projects
        project_templates = [
            "Web Application Development",
            "Mobile App Development", 
            "Data Analytics Platform",
            "API Development",
            "Database Design",
            "Cloud Migration",
            "System Integration",
            "Performance Optimization"
        ]
        
        for i in range(num_projects):
            # Select a random project template
            project_template = random.choice(project_templates)
            
            # Generate project dates
            start_date = fake.date_between(
                start_date=date.today() - timedelta(days=experience * 365),
                end_date=date.today() - timedelta(days=30)
            )
            duration_days = random.randint(30, 180)
            end_date = start_date + timedelta(days=duration_days)
            
            # Determine role in project
            if experience <= 2:
                role = "Developer"
            elif experience <= 5:
                role = random.choice(["Developer", "Senior Developer", "Tech Lead"])
            else:
                role = random.choice(["Senior Developer", "Tech Lead", "Architect"])
            
            projects.append({
                "project_id": random.randint(1000, 9999),
                "project_name": f"{project_template} - {fake.company()}",
                "role": role,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "success_rating": random.uniform(0.7, 1.0)
            })
        
        return projects

    def generate_employee_from_real_data(self, row: pd.Series) -> Dict[str, Any]:
        """Generate an employee record based on real data"""
        # Calculate experience in years
        current_year = datetime.now().year
        experience_years = current_year - row['JoiningYear']
        
        # Determine role level
        role_level = self.determine_role_level(
            row['Education'], 
            row['ExperienceInCurrentDomain'], 
            row['PaymentTier']
        )
        
        # Generate role
        role = random.choice(self.role_mappings[role_level])
        
        # Generate skills
        skills = self.generate_skills_for_employee(
            role_level, 
            row['ExperienceInCurrentDomain'], 
            row['Education']
        )
        
        # Generate certifications
        certifications = self.generate_certifications(skills, row['ExperienceInCurrentDomain'])
        
        # Generate past projects
        past_projects = self.generate_past_projects(skills, row['ExperienceInCurrentDomain'])
        
        # Calculate availability (based on whether they're likely to leave)
        # If LeaveOrNot is 1, they might have lower availability
        base_availability = 100 if row['LeaveOrNot'] == 0 else random.randint(60, 90)
        availability_percent = min(100, base_availability - random.randint(0, 20))
        
        # Generate employee name
        
        name = fake.name()
        
        # Generate additional fields for frontend compatibility
        hourly_cost = random.randint(50, 150)  # Random hourly cost between $50-150
        location = fake.city() + ", " + fake.state_abbr()
        timezone = random.choice(["PST", "EST", "CST", "MST", "UTC"])
        
        employee = {
            "employee_id": random.randint(1000, 9999),
            "name": name,
            "role": role,
            "skills": skills,
            "experience_years": experience_years,
            "certifications": certifications,
            "past_projects": past_projects,
            "availability_percent": availability_percent,
            "hourly_cost": hourly_cost,
            "location": location,
            "timezone": timezone,
            "education": row['Education'],
            "age": random.randint(22, 65),
            "gender": random.choice(["Male", "Female", "Other"]),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "last_updated": datetime.utcnow().isoformat()
        }
        
        return employee

    def generate_synthetic_employees(self, num_employees: int = 300) -> List[Dict[str, Any]]:
        """Generate synthetic employees based on real data patterns with enhanced diversity"""
        employees = []
        
        if self.real_employees_df is not None:
            # Sample from real data for faster generation
            sampled_df = self.real_employees_df.sample(n=min(num_employees, len(self.real_employees_df)), random_state=42)
            for _, row in sampled_df.iterrows():
                employee = self.generate_employee_from_real_data(row)
                employees.append(employee)
        else:
            # Generate completely synthetic data with diverse archetypes
            employees = self._generate_diverse_employee_set(num_employees)
        
        return employees
    
    def _generate_diverse_employee_set(self, num_employees: int) -> List[Dict[str, Any]]:
        """Generate a diverse set of employees with different archetypes"""
        employees = []
        
        # Define target distribution for different archetypes
        archetype_distribution = {
            "frontend_specialist": 0.12,      # 12%
            "backend_specialist": 0.12,       # 12%
            "fullstack_developer": 0.18,      # 18%
            "devops_engineer": 0.08,          # 8%
            "data_engineer": 0.06,            # 6%
            "mobile_developer": 0.06,         # 6%
            "qa_engineer": 0.06,              # 6%
            "ui_ux_designer": 0.05,           # 5%
            "tech_lead": 0.04,                # 4%
            "data_scientist": 0.04,           # 4%
            "blockchain_developer": 0.03,     # 3%
            "ai_ml_engineer": 0.03,           # 3%
            "security_engineer": 0.03,        # 3%
            "game_developer": 0.02            # 2%
        }
        
        # Calculate number of employees for each archetype
        archetype_counts = {}
        for archetype, percentage in archetype_distribution.items():
            archetype_counts[archetype] = int(num_employees * percentage)
        
        # Adjust for rounding errors
        total_allocated = sum(archetype_counts.values())
        if total_allocated < num_employees:
            # Add remaining to fullstack developers
            archetype_counts["fullstack_developer"] += (num_employees - total_allocated)
        
        # Generate employees for each archetype
        for archetype, count in archetype_counts.items():
            for i in range(count):
                employee = self._generate_employee_by_archetype(archetype)
                employees.append(employee)
        
        # Shuffle the list to randomize order
        random.shuffle(employees)
        
        # Add some specialized employees with unique skill combinations
        specialized_employees = self._generate_specialized_employees(10)  # Add 10 specialized employees
        employees.extend(specialized_employees)
        
        return employees
    
    def _generate_specialized_employees(self, count: int) -> List[Dict[str, Any]]:
        """Generate specialized employees with unique skill combinations"""
        specialized_employees = []
        
        # Define unique skill combinations that might be missing
        unique_combinations = [
            {
                "name": "Blockchain Developer",
                "skills": ["JavaScript", "Python", "Solidity", "Web3.js", "Node.js", "Docker", "AWS"],
                "experience_range": (3, 8)
            },
            {
                "name": "AI/ML Engineer", 
                "skills": ["Python", "TensorFlow", "PyTorch", "Docker", "Kubernetes", "AWS", "PostgreSQL"],
                "experience_range": (4, 10)
            },
            {
                "name": "Security Engineer",
                "skills": ["Python", "JavaScript", "Docker", "Kubernetes", "AWS", "PostgreSQL", "Jest"],
                "experience_range": (5, 12)
            },
            {
                "name": "Cloud Architect",
                "skills": ["AWS", "Azure", "Docker", "Kubernetes", "Terraform", "Python", "PostgreSQL"],
                "experience_range": (6, 15)
            },
            {
                "name": "Game Developer",
                "skills": ["C#", "Unity", "JavaScript", "Python", "Docker", "PostgreSQL"],
                "experience_range": (2, 8)
            },
            {
                "name": "IoT Developer",
                "skills": ["Python", "C++", "Docker", "AWS", "PostgreSQL", "JavaScript"],
                "experience_range": (3, 9)
            },
            {
                "name": "AR/VR Developer",
                "skills": ["C#", "Unity", "JavaScript", "Python", "Docker", "AWS"],
                "experience_range": (2, 7)
            },
            {
                "name": "Fintech Developer",
                "skills": ["Java", "Python", "PostgreSQL", "Docker", "AWS", "Jest"],
                "experience_range": (4, 11)
            },
            {
                "name": "E-commerce Specialist",
                "skills": ["React", "Node.js", "PostgreSQL", "Docker", "AWS", "Jest"],
                "experience_range": (3, 9)
            },
            {
                "name": "Microservices Architect",
                "skills": ["Java", "Spring Boot", "Docker", "Kubernetes", "AWS", "PostgreSQL", "Jest"],
                "experience_range": (6, 14)
            }
        ]
        
        for i in range(min(count, len(unique_combinations))):
            combo = unique_combinations[i]
            experience_years = random.randint(*combo["experience_range"])
            
            employee = {
                "employee_id": random.randint(1000, 9999),
                "name": fake.name(),
                "skills": combo["skills"],
                "experience_years": experience_years,
                "certifications": self.generate_certifications(combo["skills"], experience_years),
                "past_projects": self.generate_past_projects(combo["skills"], experience_years),
                "availability_percent": random.randint(60, 100),
                "last_updated": datetime.utcnow().isoformat(),
                "archetype": f"specialized_{combo['name'].lower().replace(' ', '_')}"
            }
            specialized_employees.append(employee)
        
        return specialized_employees
    
    def _generate_employee_by_archetype(self, archetype: str) -> Dict[str, Any]:
        """Generate an employee with a specific archetype"""
        # Determine experience and role level based on archetype
        if archetype in ["tech_lead", "data_scientist", "ai_ml_engineer", "security_engineer"]:
            experience_years = random.randint(8, 15)
            role_level = "expert"
        elif archetype in ["fullstack_developer", "devops_engineer", "data_engineer", "blockchain_developer"]:
            experience_years = random.randint(5, 12)
            role_level = random.choice(["senior", "expert"])
        elif archetype in ["game_developer"]:
            experience_years = random.randint(1, 8)
            role_level = random.choice(["junior", "mid"])
        else:
            experience_years = random.randint(1, 10)
            role_level = random.choice(["junior", "mid", "senior"])
        
        education = random.choice(['Bachelors', 'Masters', 'PHD'])
        
        # Generate skills based on archetype
        skills = self._generate_skills_by_archetype(archetype, random.randint(3, 8), experience_years)
        certifications = self.generate_certifications(skills, experience_years)
        past_projects = self.generate_past_projects(skills, experience_years)
        
        return {
            "employee_id": random.randint(1000, 9999),
            "name": fake.name(),
            "skills": skills,
            "experience_years": experience_years,
            "certifications": certifications,
            "past_projects": past_projects,
            "availability_percent": random.randint(60, 100),
            "last_updated": datetime.utcnow().isoformat(),
            "archetype": archetype  # Add archetype for tracking
        }

    def generate_synthetic_employee(self) -> Dict[str, Any]:
        """Generate a completely synthetic employee"""
        experience_years = random.randint(0, 15)
        education = random.choice(['Bachelors', 'Masters', 'PHD'])
        role_level = self.determine_role_level(education, experience_years, random.randint(1, 3))
        
        skills = self.generate_skills_for_employee(role_level, experience_years, education)
        certifications = self.generate_certifications(skills, experience_years)
        past_projects = self.generate_past_projects(skills, experience_years)
        
        return {
            "employee_id": random.randint(1000, 9999),
            "name": fake.name(),
            "skills": skills,
            "experience_years": experience_years,
            "certifications": certifications,
            "past_projects": past_projects,
            "availability_percent": random.randint(60, 100),
            "last_updated": datetime.utcnow().isoformat()
        }

    def generate_projects(self, num_projects: int = 50) -> List[Dict[str, Any]]:
        """Generate projects using real project descriptions"""
        projects = []
        
        print(f"\n🔍 DEBUG: generate_projects called with num_projects={num_projects}")
        print(f"🔍 DEBUG: self.real_projects_df is None: {self.real_projects_df is None}")
        if self.real_projects_df is not None:
            print(f"🔍 DEBUG: self.real_projects_df length: {len(self.real_projects_df)}")
            print(f"🔍 DEBUG: self.real_projects_df shape: {self.real_projects_df.shape}")
        else:
            print("🔍 DEBUG: self.real_projects_df is None, will use fallback")
        
        if self.real_projects_df is not None and len(self.real_projects_df) > 0:
            # Get the first column name (Project Description)
            first_column = self.real_projects_df.columns[0]
            print(f"Using column: {first_column}")
            
            # Filter out rows with empty or very short descriptions
            valid_projects = self.real_projects_df[
                (self.real_projects_df[first_column].astype(str).str.len() > 50) &
                (self.real_projects_df[first_column].astype(str) != '')
            ]
            
            print(f"Found {len(valid_projects)} valid projects with descriptions > 50 chars")
            
            # Ensure we have enough valid projects
            if len(valid_projects) < num_projects:
                print(f"Warning: Only {len(valid_projects)} valid projects available, generating {len(valid_projects)} projects")
                num_projects = len(valid_projects)
            
            # Use diversified sampling for better variety
            # Try to get projects from different parts of the dataset for diversity
            if len(valid_projects) > num_projects:
                # Sample from different sections of the dataset
                step = len(valid_projects) // num_projects
                indices = [i * step for i in range(num_projects)]
                available_projects = valid_projects.iloc[indices]
            else:
                available_projects = valid_projects
            
            print(f"Processing {len(available_projects)} projects...")
            
            for idx, row in available_projects.iterrows():
                # Get the full description from the first column
                raw_description = str(row[first_column])
                
                print(f"\n=== Processing Project {len(projects)+1} ===")
                print(f"Raw description length: {len(raw_description)}")
                print(f"Raw description preview: {repr(raw_description[:300])}")
                
                # Preserve the original multi-line structure
                # Only clean up excessive whitespace but keep the line breaks
                lines = raw_description.split('\n')
                print(f"Number of lines after split: {len(lines)}")
                
                cleaned_lines = []
                for i, line in enumerate(lines):
                    cleaned_line = line.strip()
                    if cleaned_line:  # Only add non-empty lines
                        cleaned_lines.append(cleaned_line)
                        if i < 5:  # Show first 5 lines
                            print(f"  Line {i+1}: {cleaned_line[:100]}...")
                
                # Join with proper line breaks to preserve structure
                description = '\n'.join(cleaned_lines)
                
                print(f"Final description length: {len(description)}")
                print(f"Final description preview: {repr(description[:300])}")
                
                # Skip if description is too short or empty
                if len(description.strip()) < 50:
                    print("SKIPPING: Description too short")
                    continue
                
                print("ACCEPTED: Description is valid")
                    
                # Generate project timeline
                start_date = fake.date_between(start_date='-1y', end_date='today')
                duration_weeks = random.randint(4, 52)
                end_date = start_date + timedelta(weeks=duration_weeks)
                
                # Generate a project name from the description
                project_name = self._extract_project_name(description)
                
                project = {
                    "project_id": random.randint(10000, 99999),
                    "project_name": project_name,
                    "description": description,
                    "project_phase": random.choice(['DESIGN', 'DEVELOPMENT', 'TESTING', 'DEPLOYMENT']),
                    "priority_level": random.randint(1, 10),
                    "team_size_required": random.randint(2, 8),
                    "created_at": datetime.utcnow().isoformat(),
                    "timeline": [start_date.isoformat(), end_date.isoformat()]
                }
                
                projects.append(project)
        else:
            # Fallback to simple synthetic projects if no real data available
            for i in range(num_projects):
                # Generate project timeline
                start_date = fake.date_between(start_date='-1y', end_date='today')
                duration_weeks = random.randint(4, 52)
                end_date = start_date + timedelta(weeks=duration_weeks)
                
                project = {
                    "project_id": random.randint(10000, 99999),
                    "project_name": f"Project {i+1} - {fake.company()}",
                    "description": f"Software development project for {fake.company()}",
                    "project_phase": random.choice(['DESIGN', 'DEVELOPMENT', 'TESTING', 'DEPLOYMENT']),
                    "priority_level": random.randint(1, 10),
                    "team_size_required": random.randint(2, 8),
                    "created_at": datetime.utcnow().isoformat(),
                    "timeline": [start_date.isoformat(), end_date.isoformat()]
                }
                
                projects.append(project)
        
        return projects
    
    def _extract_project_name(self, description: str) -> str:
        """Extract a meaningful project name from the description"""
        if not description or not isinstance(description, str):
            return "Project"
            
        # Take the first sentence or first 80 characters as project name
        first_sentence = description.split('.')[0]
        if len(first_sentence) > 80:
            first_sentence = first_sentence[:80] + "..."
        
        # Clean up the name - remove extra whitespace and newlines
        name = first_sentence.strip()
        if not name:
            return "Project"
            
        return name

    def save_datasets(self, employees: List[Dict], projects: List[Dict], output_dir: str = "."):
        """Save generated datasets to JSON files"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Save employees
        employees_file = os.path.join(output_dir, "employees.json")
        with open(employees_file, 'w') as f:
            json.dump(employees, f, indent=2)
        print(f"Saved {len(employees)} employees to {employees_file}")
        
        # Save projects
        projects_file = os.path.join(output_dir, "projects.json")
        with open(projects_file, 'w') as f:
            json.dump(projects, f, indent=2)
        print(f"Saved {len(projects)} projects to {projects_file}")
        
        # Save summary statistics
        stats = {
            "generation_date": datetime.utcnow().isoformat(),
            "total_employees": len(employees),
            "total_projects": len(projects),
            "employee_stats": {
                "by_education": {},
                "by_experience_range": {},
                "by_role_level": {},
                "total_skills": len(set(skill for emp in employees for skill in emp["skills"]))
            },
            "project_stats": {
                "by_phase": {},
                "by_priority": {}
            }
        }
        
        # Calculate employee statistics
        for emp in employees:
            # Education distribution
            edu = emp.get("education", "Unknown")
            stats["employee_stats"]["by_education"][edu] = stats["employee_stats"]["by_education"].get(edu, 0) + 1
            
            # Experience ranges
            exp = emp["experience_years"]
            if exp <= 2:
                range_key = "0-2 years"
            elif exp <= 5:
                range_key = "3-5 years"
            elif exp <= 8:
                range_key = "6-8 years"
            else:
                range_key = "9+ years"
            stats["employee_stats"]["by_experience_range"][range_key] = stats["employee_stats"]["by_experience_range"].get(range_key, 0) + 1
        
        # Calculate project statistics
        for proj in projects:
            # Phase distribution
            phase = proj["project_phase"]
            stats["project_stats"]["by_phase"][phase] = stats["project_stats"]["by_phase"].get(phase, 0) + 1
            
            # Priority distribution
            priority = proj["priority_level"]
            priority_range = f"{priority}-{priority}"
            stats["project_stats"]["by_priority"][priority_range] = stats["project_stats"]["by_priority"].get(priority_range, 0) + 1
        
        stats_file = os.path.join(output_dir, "dataset_stats.json")
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2)
        print(f"Saved dataset statistics to {stats_file}")

    def generate_complete_dataset(self, num_employees: int = 200, num_projects: int = 50):
        """Generate complete dataset with employees and projects"""
        print("Starting dataset generation...")
        
        # Limit to 300 employees for hackathon
        if self.real_employees_df is not None:
            num_employees = min(num_employees, len(self.real_employees_df))
        
        print(f"Generating {num_employees} employees and {num_projects} projects...")
        
        # Generate employees
        employees = self.generate_synthetic_employees(num_employees)
        print(f"Generated {len(employees)} employees")
        
        # Generate projects
        projects = self.generate_projects(num_projects)
        print(f"Generated {len(projects)} projects")
        
        # Save datasets
        self.save_datasets(employees, projects)
        
        print("Dataset generation completed successfully!")
        
        return employees, projects


def main():
    """Main function to run dataset generation"""
    generator = DatasetGenerator()
    
    # Generate dataset
    employees, projects = generator.generate_complete_dataset(
        num_employees=100,  # Limit to 200 employees for hackathon
        num_projects=20
    )
    
    print(f"\nDataset Summary:")
    print(f"   - Employees: {len(employees)}")
    print(f"   - Projects: {len(projects)}")
    print(f"   - Unique Skills: {len(set(skill for emp in employees for skill in emp['skills']))}")
    print(f"   - Real Project Descriptions Used: {len(projects)}")


if __name__ == "__main__":
    main()
