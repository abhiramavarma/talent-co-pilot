from datetime import datetime, date
from typing import List, Dict, Optional, Tuple
from enum import Enum
from pydantic import BaseModel, Field
import uuid


class ProjectPhase(str, Enum):
    DESIGN = "DESIGN"
    DEVELOPMENT = "DEVELOPMENT"
    TESTING = "TESTING"
    DEPLOYMENT = "DEPLOYMENT"


class ProjectHistory(BaseModel):
    project_id: int
    project_name: str
    role: str
    start_date: date
    end_date: date
    success_rating: float = Field(ge=0.0, le=1.0)


class EmployeeProfile(BaseModel):
    employee_id: int
    name: str
    skills: List[str]  # Simplified to just list of skills
    experience_years: int
    certifications: List[str] = []
    past_projects: List[ProjectHistory] = []
    availability_percent: float = Field(ge=0.0, le=100.0)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    # Real data fields from CSV
    education: Optional[str] = None
    joining_year: Optional[int] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    ever_benched: Optional[bool] = None
    experience_in_current_domain: Optional[int] = None
    payment_tier: Optional[int] = None
    leave_or_not: Optional[int] = None


class ProjectRequirement(BaseModel):
    project_id: int
    project_name: str
    description: str
    project_phase: ProjectPhase
    phase_skill_adjustments: Dict[ProjectPhase, Dict[str, float]] = {}
    priority_level: int = Field(ge=1, le=10)  # 1-10 (10 = critical)
    budget_range: Optional[Tuple[float, float]] = None
    timeline: Optional[Tuple[date, date]] = None
    team_size_required: int = Field(ge=1)
    embedding_vector: List[float] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ConflictInfo(BaseModel):
    employee_id: int
    current_allocation: float
    requested_allocation: float
    conflicting_projects: List[int]


class AlternativeOption(BaseModel):
    employee_id: int
    name: str
    skill_fit_score: float
    availability_percent: float
    trade_offs: List[str]


class ResourceAllocation(BaseModel):
    allocation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_id: int
    project_id: int
    allocation_percent: float = Field(ge=0.0, le=100.0)
    start_date: date
    end_date: date
    skill_fit_score: float = Field(ge=0.0, le=1.0)
    confidence_score: float = Field(ge=0.0, le=1.0)
    conflicts: List[ConflictInfo] = []
    alternatives: List[AlternativeOption] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AllocationOption(BaseModel):
    type: str  # FRACTIONAL, REBALANCE, ALTERNATIVE, UPSKILL, HIRE
    employee_percent: Optional[float] = None
    alternative_employees: Optional[List[AlternativeOption]] = None
    employees_to_upskill: Optional[List[int]] = None
    roles_to_hire: Optional[List[str]] = None
    training_timeline: Optional[str] = None
    timeline: Optional[str] = None
    impact_assessment: str
    trade_offs: List[str]


class ResolutionOption(BaseModel):
    conflict: ConflictInfo
    options: List[AllocationOption]
    recommended_option: AllocationOption


class ReallocationScenario(BaseModel):
    scenario_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str
    changes: List[Dict]  # List of allocation changes
    constraints: Dict[str, any] = {}


class SimulationResult(BaseModel):
    scenario: ReallocationScenario
    projected_impacts: Dict[str, any]
    affected_projects: List[int]
    resource_utilization: Dict[str, float]
    timeline_changes: Dict[str, any]
    cost_implications: Dict[str, float]
    risk_assessment: Dict[str, any]
    recommendations: List[str]


class WhatIfResult(BaseModel):
    query: str
    parsed_scenario: ReallocationScenario
    simulation_result: SimulationResult
    natural_language_explanation: str
    visualizations: Dict[str, any]


class ProjectSuccessPredict(BaseModel):
    success_probability: float = Field(ge=0.0, le=1.0)
    confidence_interval: Tuple[float, float]
    primary_risk_factors: List[str]
    recommendations: List[str]


class ResourceDemandForecast(BaseModel):
    timeline: List[date]
    demand_by_skill: Dict[str, List[float]]
    capacity_gaps: Dict[str, float]
    hiring_recommendations: List[Dict[str, any]]
    confidence_data: Dict[str, List[float]]


class ProjectOutcome(BaseModel):
    project_id: int
    success_rating: float = Field(ge=0.0, le=1.0)
    actual_duration: int  # days
    budget_variance: float  # percentage
    quality_metrics: Dict[str, float]
    team_satisfaction: float = Field(ge=0.0, le=1.0)


class TeamFeedback(BaseModel):
    project_id: int
    employee_feedback: Dict[int, Dict[str, any]]  # emp_id -> feedback
    overall_rating: float = Field(ge=0.0, le=1.0)
    improvement_suggestions: List[str]


class LearningUpdate(BaseModel):
    accuracy_improvement: float
    model_updates: Dict[str, any]
    embedding_updates: int


class AllocationFeedback(BaseModel):
    allocation_id: str
    quality_rating: float = Field(ge=0.0, le=1.0)
    accuracy_rating: float = Field(ge=0.0, le=1.0)
    comments: str
    suggestions: List[str]


# API Request/Response Models
class AdvancedMatchingRequest(BaseModel):
    project_description: str
    additional_documents: Optional[List[str]] = []
    priority: int = Field(ge=1, le=10, default=5)
    budget_constraints: Optional[Tuple[float, float]] = None
    timeline_constraints: Optional[Tuple[date, date]] = None
    team_size_preference: Optional[int] = None


class MatchingResponse(BaseModel):
    project_id: int
    recommendations: List[ResourceAllocation]
    conflicts: List[ConflictInfo]
    success_prediction: Optional[ProjectSuccessPredict] = None
    alternative_options: List[AlternativeOption] = []
    confidence_score: float
    explanation: str


class WhatIfRequest(BaseModel):
    query: str


class WhatIfResponse(BaseModel):
    original_query: str
    parsed_scenario: ReallocationScenario
    impact_analysis: SimulationResult
    recommendations: List[str]
    visualization_data: Dict[str, any]
    natural_language_summary: str


class ResourceUtilizationResponse(BaseModel):
    utilization_by_group: Dict[str, float]
    trends: Dict[str, List[float]]
    capacity_gaps: Dict[str, float]
    efficiency_metrics: Dict[str, float]
    optimization_recommendations: List[str]


class DemandForecastResponse(BaseModel):
    forecast_horizon_weeks: int
    skill_demand_forecast: Dict[str, List[float]]
    capacity_gaps: Dict[str, float]
    hiring_recommendations: List[Dict[str, any]]
    confidence_intervals: Dict[str, List[float]]
