from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from ..services.matching_engine import IntelligentMatchingEngine
from ..services.vector_db import EmployeeVectorDB
from ..services.llm_service import ProjectRequirementExtractor
from ..models import ProjectRequirement, ProjectPhase
from ..api.employees import get_employee

router = APIRouter()

# Matching models
class TalentMatch(BaseModel):
    employee_id: int
    skill_fit_score: float
    confidence_score: float
    allocation_percent: float
    start_date: str
    end_date: str
    alternatives: List[Dict[str, Any]] = []

class MatchingResult(BaseModel):
    project_id: int
    project_name: str
    matches: List[TalentMatch]
    total_matches: int
    generated_at: datetime

# Initialize services
matching_engine = IntelligentMatchingEngine()
vector_db = EmployeeVectorDB()
llm_service = ProjectRequirementExtractor()
from ..api.projects import load_projects

@router.get("/match/{project_id}", response_model=MatchingResult)
async def get_talent_match(project_id: int):
    """Get AI-powered talent recommendations for a project"""
    try:
        # Load projects
        project = next((p for p in load_projects() if p.id == project_id), None)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Access fields with dot notation
        project_req = ProjectRequirement(
            project_id=project.id,
            project_name=project.name,
            description=project.description,
            project_phase=ProjectPhase.DEVELOPMENT,
            phase_skill_adjustments={},
            priority_level=5,
            team_size_required=project.team_size_required,
            embedding_vector=[],
            created_at=datetime.utcnow()
        )
        
        # Extract requirements using LLM
        project_req.project_id = project_id
        project_req = await llm_service.extract_requirements(project.description)
        project_req.project_name = project.name

        
        # Get talent matches using the matching engine with the same vector_db instance
        matching_engine.vector_db = vector_db
        allocations = await matching_engine.find_optimal_allocation(project_req, consider_conflicts=True)
        
        # Convert allocations to talent matches with employee details
        matches = []
        for allocation in allocations:
            # Get employee details from vector database
            employee_details = vector_db.get_employee_by_id(allocation.employee_id)
            
            if not employee_details:
                print(f"Warning: Employee {allocation.employee_id} not found in vector database")
                continue  # Skip if employee not found
            
            print(f"Found employee {allocation.employee_id}: {employee_details['metadata'].get('name', 'Unknown')}")
            
            # Convert AlternativeOption objects to dictionaries
            alternatives_dict = []
            if allocation.alternatives:
                for alt in allocation.alternatives:
                    alternatives_dict.append({
                        "employee_id": alt.employee_id,
                        "name": alt.name,
                        "skill_fit_score": alt.skill_fit_score,
                        "availability_percent": alt.availability_percent,
                        "trade_offs": alt.trade_offs
                    })
            
            # Create enhanced match with employee details
            match = {
                "employee_id": allocation.employee_id,
                "skill_fit_score": allocation.skill_fit_score,
                "confidence_score": allocation.confidence_score,
                "allocation_percent": allocation.allocation_percent,
                "start_date": allocation.start_date.isoformat(),
                "end_date": allocation.end_date.isoformat(),
                "alternatives": alternatives_dict,
                # Add employee details directly
                "employee_details": {
                    "id": allocation.employee_id,
                    "name": employee_details['metadata'].get('name', 'Unknown'),
                    "skills": employee_details['metadata'].get('skills', '').split(',') if employee_details['metadata'].get('skills') else [],
                    "availability_percent": float(employee_details['metadata'].get('availability_percent', 0)),
                    "experience_years": int(employee_details['metadata'].get('experience_years', 0)),
                    "certifications": employee_details['metadata'].get('certifications', '').split(',') if employee_details['metadata'].get('certifications') else [],
                    "education": employee_details['metadata'].get('education', ''),
                    "age": int(employee_details['metadata'].get('age', 0)),
                    "gender": employee_details['metadata'].get('gender', '')
                }
            }
            matches.append(match)
        
        return MatchingResult(
            project_id=project_id,
            project_name=project.name,
            matches=matches,
            total_matches=len(matches),
            generated_at=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating talent matches: {str(e)}")

@router.get("/match/{project_id}/detailed", response_model=Dict[str, Any])
async def get_detailed_talent_match(project_id: int):
    """Get detailed talent matches with complete employee information"""
    try:
        # Get basic talent matches
        matching_result = await get_talent_match(project_id)
        
        # Get detailed employee information for each match
        detailed_matches = []
        for match in matching_result.matches:
            try:
                # Get employee details
                from ..api.employees import get_employee
                employee = await get_employee(match.employee_id)
                
                # Combine match data with employee details
                detailed_match = {
                    "match_info": match.dict(),
                    "employee_details": employee.dict()
                }
                detailed_matches.append(detailed_match)
                
            except Exception as e:
                # If employee not found, skip this match
                continue
        
        return {
            "project_id": project_id,
            "project_name": matching_result.project_name,
            "matches": detailed_matches,
            "total_matches": len(detailed_matches),
            "generated_at": matching_result.generated_at
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating detailed talent matches: {str(e)}")

@router.post("/analyze", response_model=Dict[str, Any])
async def analyze_project_requirements(project_description: str):
    """Analyze project requirements and suggest optimal team composition"""
    try:
        # Extract requirements using LLM
        project_req = await llm_service.extract_requirements(project_description)
        
        # Get skill distribution
        skill_distribution = project_req.phase_skill_adjustments.get(project_req.project_phase, {})
        
        # Analyze team requirements
        analysis = {
            "project_name": project_req.project_name,
            "recommended_team_size": project_req.team_size_required,
            "skill_distribution": skill_distribution,
            "priority_skills": sorted(skill_distribution.items(), key=lambda x: x[1], reverse=True)[:5],
            "project_phase": project_req.project_phase.value,
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
        
        return analysis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing project requirements: {str(e)}")

@router.get("/stats", response_model=Dict[str, Any])
async def get_matching_stats():
    """Get matching engine statistics"""
    try:
        # Get employee count from vector database
        all_employees = vector_db.collection.get(include=["metadatas"])
        total_employees = len(all_employees['ids'])
        
        # Get available employees
        available_employees = [
            emp for emp in all_employees['metadatas']
            if emp.get('availability_percent', 0) >= 20.0
        ]
        
        stats = {
            "total_employees": total_employees,
            "available_employees": len(available_employees),
            "availability_rate": len(available_employees) / total_employees if total_employees > 0 else 0,
            "matching_engine_status": "operational",
            "last_updated": datetime.utcnow().isoformat()
        }
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting matching stats: {str(e)}")
