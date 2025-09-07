# from fastapi import APIRouter, HTTPException
# from typing import List, Optional
# from pydantic import BaseModel
# from datetime import datetime
# from ..services.vector_db import EmployeeVectorDB

# router = APIRouter()

# # Initialize vector database
# vector_db = EmployeeVectorDB()

# # Employee models
# class EmployeeBase(BaseModel):
#     name: str
#     role: str
#     skills: List[str]
#     availability_percent: float
#     hourly_cost: float
#     location: str
#     timezone: str
#     experience_years: int
#     certifications: List[str]

# class Employee(EmployeeBase):
#     id: int
#     created_at: datetime
#     updated_at: datetime

#     class Config:
#         from_attributes = True

# # Sample employees data (matching the vector database structure)
# EMPLOYEES_DATA = [
#     {
#         "id": 1,
#         "name": "Alex Chen",
#         "role": "Full-Stack Developer",
#         "skills": ["React", "Node.js", "Python", "JavaScript", "TypeScript", "MongoDB"],
#         "availability_percent": 85.0,
#         "hourly_cost": 75.0,
#         "location": "San Francisco, CA",
#         "timezone": "PST",
#         "experience_years": 5,
#         "certifications": ["AWS Certified Developer", "React Professional"],
#         "created_at": "2024-01-01T00:00:00Z",
#         "updated_at": "2024-01-01T00:00:00Z"
#     },
#     {
#         "id": 2,
#         "name": "Sarah Johnson",
#         "role": "AI/ML Engineer",
#         "skills": ["Python", "TensorFlow", "PyTorch", "Machine Learning", "Deep Learning", "Data Science"],
#         "availability_percent": 70.0,
#         "hourly_cost": 90.0,
#         "location": "New York, NY",
#         "timezone": "EST",
#         "experience_years": 4,
#         "certifications": ["Google AI Certificate", "AWS ML Specialty"],
#         "created_at": "2024-01-01T00:00:00Z",
#         "updated_at": "2024-01-01T00:00:00Z"
#     },
#     {
#         "id": 3,
#         "name": "Marcus Rodriguez",
#         "role": "DevOps Engineer",
#         "skills": ["Docker", "Kubernetes", "AWS", "CI/CD", "Terraform", "Linux"],
#         "availability_percent": 90.0,
#         "hourly_cost": 80.0,
#         "location": "Austin, TX",
#         "timezone": "CST",
#         "experience_years": 6,
#         "certifications": ["AWS Solutions Architect", "Kubernetes Administrator"],
#         "created_at": "2024-01-01T00:00:00Z",
#         "updated_at": "2024-01-01T00:00:00Z"
#     },
#     {
#         "id": 4,
#         "name": "Emily Watson",
#         "role": "Blockchain Developer",
#         "skills": ["Solidity", "Web3.js", "JavaScript", "Ethereum", "Smart Contracts", "DeFi"],
#         "availability_percent": 75.0,
#         "hourly_cost": 95.0,
#         "location": "Seattle, WA",
#         "timezone": "PST",
#         "experience_years": 3,
#         "certifications": ["Ethereum Developer", "Blockchain Professional"],
#         "created_at": "2024-01-01T00:00:00Z",
#         "updated_at": "2024-01-01T00:00:00Z"
#     },
#     {
#         "id": 5,
#         "name": "David Kim",
#         "role": "Frontend Specialist",
#         "skills": ["React", "Vue.js", "Angular", "CSS", "HTML", "JavaScript", "TypeScript"],
#         "availability_percent": 80.0,
#         "hourly_cost": 70.0,
#         "location": "Los Angeles, CA",
#         "timezone": "PST",
#         "experience_years": 4,
#         "certifications": ["React Professional", "Vue.js Certified"],
#         "created_at": "2024-01-01T00:00:00Z",
#         "updated_at": "2024-01-01T00:00:00Z"
#     },
#     {
#         "id": 6,
#         "name": "Lisa Wang",
#         "role": "Backend Specialist",
#         "skills": ["Python", "Django", "FastAPI", "PostgreSQL", "Redis", "Microservices"],
#         "availability_percent": 88.0,
#         "hourly_cost": 85.0,
#         "location": "Boston, MA",
#         "timezone": "EST",
#         "experience_years": 5,
#         "certifications": ["Python Professional", "AWS Developer"],
#         "created_at": "2024-01-01T00:00:00Z",
#         "updated_at": "2024-01-01T00:00:00Z"
#     },
#     {
#         "id": 7,
#         "name": "James Wilson",
#         "role": "Data Engineer",
#         "skills": ["Python", "SQL", "Apache Spark", "Kafka", "Airflow", "Big Data"],
#         "availability_percent": 82.0,
#         "hourly_cost": 78.0,
#         "location": "Chicago, IL",
#         "timezone": "CST",
#         "experience_years": 4,
#         "certifications": ["Apache Spark Certified", "Data Engineering Professional"],
#         "created_at": "2024-01-01T00:00:00Z",
#         "updated_at": "2024-01-01T00:00:00Z"
#     },
#     {
#         "id": 8,
#         "name": "Maria Garcia",
#         "role": "Mobile Developer",
#         "skills": ["React Native", "Flutter", "iOS", "Android", "Swift", "Kotlin"],
#         "availability_percent": 76.0,
#         "hourly_cost": 72.0,
#         "location": "Miami, FL",
#         "timezone": "EST",
#         "experience_years": 3,
#         "certifications": ["React Native Professional", "iOS Developer"],
#         "created_at": "2024-01-01T00:00:00Z",
#         "updated_at": "2024-01-01T00:00:00Z"
#     }
# ]

# @router.get("/", response_model=List[Employee])
# async def get_employees():
#     """Get all employees"""
#     return EMPLOYEES_DATA

# @router.get("/{employee_id}", response_model=Employee)
# async def get_employee(employee_id: int):
#     """Get a specific employee by ID"""
#     # Try to get from vector database first
#     employee_data = vector_db.get_employee_by_id(employee_id)
#     if employee_data:
#         metadata = employee_data['metadata']
#         return Employee(
#             id=employee_id,
#             name=metadata.get('name', 'Unknown'),
#             role=metadata.get('role', 'Developer'),
#             skills=metadata.get('skills', '').split(',') if metadata.get('skills') else [],
#             availability_percent=float(metadata.get('availability_percent', 0)),
#             experience_years=int(metadata.get('experience_years', 0)),
#             certifications=metadata.get('certifications', '').split(',') if metadata.get('certifications') else [],
#             created_at=datetime.fromisoformat(metadata.get('created_at', '2024-01-01T00:00:00Z').replace('Z', '+00:00')),
#             updated_at=datetime.fromisoformat(metadata.get('updated_at', '2024-01-01T00:00:00Z').replace('Z', '+00:00'))
#         )
    
#     # Fallback to static data for backward compatibility
#     employee = next((e for e in EMPLOYEES_DATA if e["id"] == employee_id), None)
#     if not employee:
#         raise HTTPException(status_code=404, detail="Employee not found")
#     return employee

# @router.get("/search/", response_model=List[Employee])
# async def search_employees(
#     skills: Optional[str] = None,
#     role: Optional[str] = None,
#     min_availability: Optional[float] = None,
#     max_hourly_cost: Optional[float] = None
# ):
#     """Search employees by criteria"""
#     filtered_employees = EMPLOYEES_DATA.copy()
    
#     if skills:
#         skill_list = [skill.strip().lower() for skill in skills.split(",")]
#         filtered_employees = [
#             emp for emp in filtered_employees
#             if any(skill in [s.lower() for s in emp["skills"]] for skill in skill_list)
#         ]
    
#     if role:
#         filtered_employees = [
#             emp for emp in filtered_employees
#             if role.lower() in emp["role"].lower()
#         ]
    
#     if min_availability is not None:
#         filtered_employees = [
#             emp for emp in filtered_employees
#             if emp["availability_percent"] >= min_availability
#         ]
    
    
import json
import os
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from pathlib import Path

router = APIRouter()

# Path to employees.json
EMPLOYEE_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "employees.json"

# Employee models
class EmployeeBase(BaseModel):
    name: str
    role: str
    skills: List[str]
    availability_percent: float
    experience_years: int
    certifications: List[str]

class Employee(BaseModel):
    id: int
    name: str
    role: Optional[str] = None
    skills: List[str]

    class Config:
        from_attributes = True

# ------------------------------
# Helpers
# ------------------------------
def load_employees():
    with open("data/employees.json") as f:
        data = json.load(f)
    transformed = []
    for emp in data:
        transformed.append({
            "id": emp.get("employee_id"),
            "name": emp.get("name"),
            "role": emp.get("role"),  # might be None
            "skills": emp.get("skills", [])
        })
    return [Employee(**emp) for emp in transformed]

# ------------------------------
# Routes
# ------------------------------

@router.get("/", response_model=List[Employee])
async def get_employees():
    """Get all employees from JSON file"""
    return load_employees()

@router.get("/{employee_id}", response_model=Employee)
async def get_employee(employee_id: int):
    """Get a specific employee by ID"""
    employees = load_employees()
    for emp in employees:
        if emp.id == employee_id:
            return emp
    raise HTTPException(status_code=404, detail="Employee not found")

@router.get("/search/", response_model=List[Employee])
async def search_employees(
    skills: Optional[str] = None,
    role: Optional[str] = None,
    min_availability: Optional[float] = None
):
    """Search employees by criteria"""
    employees = load_employees()

    if skills:
        skill_list = [skill.strip().lower() for skill in skills.split(",")]
        employees = [
            emp for emp in employees
            if any(skill in [s.lower() for s in emp.skills] for skill in skill_list)
        ]

    if role:
        employees = [
            emp for emp in employees
            if role.lower() in emp.role.lower()
        ]

    if min_availability is not None:
        employees = [
            emp for emp in employees
            if emp.availability_percent >= min_availability
        ]

    return employees
