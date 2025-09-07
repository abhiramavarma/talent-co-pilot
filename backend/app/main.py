from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
import asyncio

from .models import (
    EmployeeProfile, ProjectRequirement, ResourceAllocation,
    AdvancedMatchingRequest, MatchingResponse, WhatIfRequest, WhatIfResponse,
    AllocationFeedback, ResourceUtilizationResponse, DemandForecastResponse
)
from .services.vector_db import EmployeeVectorDB
from .services.llm_service import ProjectRequirementExtractor
from .services.matching_engine import IntelligentMatchingEngine
from .websocket_manager import ConnectionManager

# Import new API routes
from .api import projects, employees, matching

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Talent Co-Pilot API",
    description="AI-Powered Project-Resource Matching Engine",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(projects.router, prefix="/projects", tags=["projects"])
app.include_router(employees.router, prefix="/employees", tags=["employees"])
app.include_router(matching.router, prefix="/matching", tags=["matching"])

# Initialize services
vector_db = EmployeeVectorDB()
requirement_extractor = ProjectRequirementExtractor()
matching_engine = IntelligentMatchingEngine()
websocket_manager = ConnectionManager()

# In-memory storage for demo (in production, use a database)
projects_db: Dict[int, ProjectRequirement] = {}
employees_db: Dict[int, EmployeeProfile] = {}
allocations_db: Dict[str, ResourceAllocation] = {}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Talent Co-Pilot API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check vector database
        vector_stats = vector_db.get_collection_stats()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "vector_database": "healthy" if vector_stats else "unhealthy",
                "llm_service": "healthy",
                "matching_engine": "healthy"
            },
            "vector_db_stats": vector_stats
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


# Employee Management Endpoints
@app.post("/api/v1/employees", response_model=Dict[str, Any])
async def create_employee(employee: EmployeeProfile):
    """Create a new employee profile"""
    try:
        # Add to vector database
        success = vector_db.add_employee(employee)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to add employee to vector database")
        
        # Store in memory database
        employees_db[employee.employee_id] = employee
        
        # Broadcast update via WebSocket
        await websocket_manager.broadcast_employee_update({
            "type": "employee_created",
            "employee_id": employee.employee_id,
            "name": employee.name
        })
        
        return {
            "status": "success",
            "employee_id": employee.employee_id,
            "message": f"Employee {employee.name} created successfully"
        }
    except Exception as e:
        logger.error(f"Failed to create employee: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/employees", response_model=List[EmployeeProfile])
async def get_employees():
    """Get all employees"""
    return list(employees_db.values())


@app.get("/api/v1/employees/{employee_id}", response_model=EmployeeProfile)
async def get_employee(employee_id: int):
    """Get employee by ID"""
    if employee_id not in employees_db:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employees_db[employee_id]


@app.put("/api/v1/employees/{employee_id}", response_model=Dict[str, Any])
async def update_employee(employee_id: int, employee: EmployeeProfile):
    """Update employee profile"""
    try:
        if employee_id not in employees_db:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        # Update in memory database
        employees_db[employee_id] = employee
        
        # Update in vector database
        success = vector_db.add_employee(employee)  # This will update existing
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update employee in vector database")
        
        # Broadcast update
        await websocket_manager.broadcast_employee_update({
            "type": "employee_updated",
            "employee_id": employee_id,
            "name": employee.name
        })
        
        return {
            "status": "success",
            "message": f"Employee {employee.name} updated successfully"
        }
    except Exception as e:
        logger.error(f"Failed to update employee: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Project Management Endpoints
@app.post("/api/v1/projects", response_model=Dict[str, Any])
async def create_project(project: ProjectRequirement):
    """Create a new project"""
    try:
        # Generate project ID
        project_id = max(projects_db.keys(), default=0) + 1
        project.project_id = project_id
        
        # Store project
        projects_db[project_id] = project
        
        # Broadcast update
        await websocket_manager.broadcast_project_update({
            "type": "project_created",
            "project_id": project_id,
            "name": project.project_name
        })
        
        return {
            "status": "success",
            "project_id": project_id,
            "message": f"Project {project.project_name} created successfully"
        }
    except Exception as e:
        logger.error(f"Failed to create project: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/projects", response_model=List[ProjectRequirement])
async def get_projects():
    """Get all projects"""
    return list(projects_db.values())


@app.get("/api/v1/projects/{project_id}", response_model=ProjectRequirement)
async def get_project(project_id: int):
    """Get project by ID"""
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
    return projects_db[project_id]


# Matching Engine Endpoints
@app.post("/api/v1/projects/{project_id}/match", response_model=MatchingResponse)
async def find_project_matches(
    project_id: int,
    matching_request: AdvancedMatchingRequest,
    background_tasks: BackgroundTasks,
    include_predictions: bool = True,
    simulate_conflicts: bool = True
):
    """Enhanced project matching with conflict resolution and predictions"""
    try:
        # Extract project requirements
        project_req = await requirement_extractor.extract_requirements(
            matching_request.project_description,
            matching_request.additional_documents
        )
        project_req.project_id = project_id
        project_req.priority_level = matching_request.priority
        
        # Store project
        projects_db[project_id] = project_req
        
        # Find optimal allocations
        allocations = await matching_engine.find_optimal_allocation(
            project_req,
            consider_conflicts=simulate_conflicts
        )
        
        # Resolve conflicts if any
        conflicts = []
        if simulate_conflicts:
            conflict_resolutions = await conflict_resolver.resolve_resource_conflicts(
                project_req, allocations
            )
            conflicts = [r.conflict for r in conflict_resolutions]
        
        # Store allocations
        for allocation in allocations:
            allocations_db[allocation.allocation_id] = allocation
        
        # Generate success predictions (simplified)
        predictions = None
        if include_predictions and allocations:
            avg_confidence = sum(a.confidence_score for a in allocations) / len(allocations)
            predictions = {
                "success_probability": avg_confidence,
                "confidence_interval": (avg_confidence - 0.1, avg_confidence + 0.1),
                "primary_risk_factors": ["Resource availability", "Skill gaps"] if conflicts else [],
                "recommendations": ["Monitor resource utilization", "Plan for skill development"]
            }
        
        # Background task: Update metrics
        background_tasks.add_task(
            update_matching_metrics, 
            project_req, 
            allocations,
            len(conflicts)
        )
        
        # Broadcast matching results
        await websocket_manager.broadcast_matching_update({
            "type": "matching_completed",
            "project_id": project_id,
            "allocations_count": len(allocations),
            "conflicts_count": len(conflicts)
        })
        
        return MatchingResponse(
            project_id=project_id,
            recommendations=allocations,
            conflicts=conflicts,
            success_prediction=predictions,
            alternative_options=[],  # Simplified for now
            confidence_score=sum(a.confidence_score for a in allocations) / len(allocations) if allocations else 0.0,
            explanation=f"Found {len(allocations)} suitable allocations with {len(conflicts)} conflicts to resolve"
        )
        
    except Exception as e:
        logger.error(f"Matching failed for project {project_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/simulate/what-if")
async def simulate_what_if_scenario(what_if_request: WhatIfRequest):
    """Run what-if simulation analysis"""
    try:
        # Simplified what-if simulation
        # In a full implementation, this would parse the natural language query
        # and run comprehensive simulations
        
        simulation_result = {
            "scenario": {
                "description": what_if_request.query,
                "changes": []
            },
            "projected_impacts": {
                "timeline_impact": "Minimal",
                "cost_impact": "No change",
                "resource_impact": "Balanced"
            },
            "affected_projects": [],
            "resource_utilization": {"overall": 0.75},
            "timeline_changes": {},
            "cost_implications": {},
            "risk_assessment": {"overall_risk": "Low"},
            "recommendations": ["Proceed with caution", "Monitor resource utilization"]
        }
        
        return WhatIfResponse(
            original_query=what_if_request.query,
            parsed_scenario=simulation_result["scenario"],
            impact_analysis=simulation_result,
            recommendations=simulation_result["recommendations"],
            visualization_data={},
            natural_language_summary=f"Analysis of '{what_if_request.query}' shows minimal impact with low risk."
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Simulation failed: {str(e)}")


@app.post("/api/v1/allocations/{allocation_id}/feedback")
async def submit_allocation_feedback(
    allocation_id: str,
    feedback: AllocationFeedback,
    background_tasks: BackgroundTasks
):
    """Submit feedback on allocation quality for continuous learning"""
    try:
        if allocation_id not in allocations_db:
            raise HTTPException(status_code=404, detail="Allocation not found")
        
        # Store feedback (in production, this would be in a database)
        logger.info(f"Received feedback for allocation {allocation_id}: {feedback.quality_rating}")
        
        # Background task: Update learning models
        background_tasks.add_task(
            process_allocation_feedback,
            allocation_id,
            feedback
        )
        
        return {"status": "success", "message": "Feedback recorded successfully"}
        
    except Exception as e:
        logger.error(f"Failed to submit feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/analytics/resource-utilization")
async def get_resource_utilization(
    time_range: str = "30d",
    group_by: str = "department"
):
    """Get resource utilization analytics"""
    try:
        # Simplified analytics (in production, this would query a time-series database)
        utilization_data = {
            "utilization_by_group": {
                "Engineering": 0.85,
                "Design": 0.72,
                "QA": 0.68
            },
            "trends": {
                "overall": [0.7, 0.72, 0.75, 0.78, 0.8],
                "engineering": [0.8, 0.82, 0.84, 0.85, 0.85]
            },
            "capacity_gaps": {
                "frontend": 0.15,
                "devops": 0.25
            },
            "efficiency_metrics": {
                "average_utilization": 0.75,
                "utilization_variance": 0.12
            },
            "optimization_recommendations": [
                "Increase DevOps capacity",
                "Cross-train frontend developers"
            ]
        }
        
        return ResourceUtilizationResponse(**utilization_data)
        
    except Exception as e:
        logger.error(f"Failed to get resource utilization: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/forecasting/demand")
async def get_demand_forecast(horizon_weeks: int = 12):
    """Get resource demand forecasting"""
    try:
        # Simplified forecasting (in production, this would use ML models)
        forecast_data = {
            "forecast_horizon_weeks": horizon_weeks,
            "skill_demand_forecast": {
                "react": [0.8, 0.82, 0.85, 0.88, 0.9],
                "nodejs": [0.7, 0.72, 0.75, 0.78, 0.8],
                "python": [0.9, 0.92, 0.95, 0.98, 1.0]
            },
            "capacity_gaps": {
                "react": 0.1,
                "devops": 0.2
            },
            "hiring_recommendations": [
                {"role": "DevOps Engineer", "priority": "High", "timeline": "2-4 weeks"},
                {"role": "React Developer", "priority": "Medium", "timeline": "4-6 weeks"}
            ],
            "confidence_intervals": {
                "react": [0.75, 0.85],
                "nodejs": [0.65, 0.75]
            }
        }
        
        return DemandForecastResponse(**forecast_data)
        
    except Exception as e:
        logger.error(f"Failed to get demand forecast: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket Endpoints
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    """WebSocket endpoint for real-time updates"""
    await websocket_manager.connect(websocket, user_id)
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "subscribe_project":
                await handle_project_subscription(user_id, message.get("project_id"))
            elif message.get("type") == "request_update":
                await send_current_state(user_id)
                
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, user_id)


# Background Tasks
async def update_matching_metrics(project_req: ProjectRequirement, allocations: List[ResourceAllocation], conflict_count: int):
    """Update matching metrics in background"""
    try:
        logger.info(f"Updated metrics: Project {project_req.project_id}, {len(allocations)} allocations, {conflict_count} conflicts")
        # In production, this would update metrics in a time-series database
    except Exception as e:
        logger.error(f"Failed to update metrics: {str(e)}")


async def process_allocation_feedback(allocation_id: str, feedback: AllocationFeedback):
    """Process allocation feedback for learning"""
    try:
        logger.info(f"Processing feedback for allocation {allocation_id}: {feedback.quality_rating}")
        # In production, this would update ML models
    except Exception as e:
        logger.error(f"Failed to process feedback: {str(e)}")


# WebSocket Helper Functions
async def handle_project_subscription(user_id: int, project_id: int):
    """Handle project subscription"""
    # In production, this would manage subscriptions in a database
    logger.info(f"User {user_id} subscribed to project {project_id}")


async def send_current_state(user_id: int):
    """Send current state to user"""
    try:
        state = {
            "type": "current_state",
            "projects": len(projects_db),
            "employees": len(employees_db),
            "allocations": len(allocations_db)
        }
        await websocket_manager.send_to_user(user_id, state)
    except Exception as e:
        logger.error(f"Failed to send current state: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
