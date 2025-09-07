import logging
from typing import List, Dict, Optional, Tuple
from datetime import date, datetime, timedelta
import math
from ..models import (
    ProjectRequirement, ResourceAllocation, EmployeeProfile,
    AlternativeOption, ProjectPhase
)
from .vector_db import EmployeeVectorDB
from .llm_service import ProjectRequirementExtractor

logger = logging.getLogger(__name__)


class IntelligentMatchingEngine:
    def __init__(self):
        """Initialize the intelligent matching engine"""
        self.vector_db = EmployeeVectorDB()
        self.requirement_extractor = ProjectRequirementExtractor()
        logger.info("IntelligentMatchingEngine initialized")
    
    async def find_optimal_allocation(
        self, 
        project_req: ProjectRequirement,
        consider_conflicts: bool = True,
        min_availability_threshold: float = 30.0
    ) -> List[ResourceAllocation]:
        """Find optimal employee allocation for project"""
        try:
            # 1. Get candidate employees from vector search
            candidates = self.vector_db.search_matching_employees(
                project_req, 
                top_k=20,
                availability_threshold=min_availability_threshold
            )
            
            if not candidates:
                logger.warning(f"No candidates found for project {project_req.project_id}")
                return []
            
            # 2. Score candidates based on multiple factors
            scored_candidates = []
            for candidate in candidates:
                score = await self._calculate_composite_score(candidate, project_req)
                scored_candidates.append((candidate, score))
            
            # 3. Sort by composite score
            scored_candidates.sort(key=lambda x: x[1]['total_score'], reverse=True)
            
            # 4. Generate allocation recommendations
            allocations = await self._generate_allocations(
                scored_candidates[:10], 
                project_req,
                consider_conflicts
            )
            
            logger.info(f"Generated {len(allocations)} allocations for project {project_req.project_id}")
            return allocations
            
        except Exception as e:
            logger.error(f"Failed to find optimal allocation: {str(e)}")
            return []
    
    async def _calculate_composite_score(self, candidate: Dict, project_req: ProjectRequirement) -> Dict:
        """Calculate multi-factor matching score"""
        try:
            # Skill fit score (from vector similarity)
            skill_fit = candidate['similarity_score']
            
            # Availability score
            availability_score = min(1.0, candidate['availability_percent'] / 80.0)
            
            # Cost efficiency score (simplified - no hourly_cost in simplified model)
            budget_fit = 0.5  # Default neutral score
            
            # Phase relevance score (simplified - no skill_proficiencies in simplified model)
            phase_relevance = 0.5  # Default neutral score
            
            # Experience relevance
            experience_score = self._calculate_experience_score(
                candidate['experience_years'],
                project_req
            )
            
            # Composite scoring with weights
            weights = {
                'skill_fit': 0.40,
                'availability': 0.30,
                'budget_fit': 0.10,
                'phase_relevance': 0.10,
                'experience': 0.10
            }
            
            total_score = (
                skill_fit * weights['skill_fit'] +
                availability_score * weights['availability'] +
                budget_fit * weights['budget_fit'] +
                phase_relevance * weights['phase_relevance'] +
                experience_score * weights['experience']
            )
            
            return {
                'total_score': min(1.0, total_score),
                'breakdown': {
                    'skill_fit': skill_fit,
                    'availability': availability_score,
                    'budget_fit': budget_fit,
                    'phase_relevance': phase_relevance,
                    'experience': experience_score
                },
                'confidence': self._calculate_confidence(total_score, candidate)
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate composite score: {str(e)}")
            return {'total_score': 0.0, 'breakdown': {}, 'confidence': 0.0}
    
    
    def _calculate_phase_relevance(self, employee_skills: Dict[str, float], project_req: ProjectRequirement) -> float:
        """Calculate how relevant employee skills are to project phase - simplified"""
        # Simplified phase relevance - just return neutral score since we don't have detailed skill proficiencies
        return 0.5
    
    
    def _calculate_experience_score(self, experience_years: int, project_req: ProjectRequirement) -> float:
        """Calculate experience relevance score"""
        # Optimal experience range based on project complexity
        if project_req.priority_level >= 8:  # High priority projects
            optimal_min, optimal_max = 5, 15
        elif project_req.priority_level >= 6:  # Medium priority
            optimal_min, optimal_max = 3, 10
        else:  # Low priority
            optimal_min, optimal_max = 1, 8
        
        if optimal_min <= experience_years <= optimal_max:
            return 1.0
        elif experience_years < optimal_min:
            # Under-experienced - linear penalty
            return experience_years / optimal_min
        else:
            # Over-experienced - slight penalty for potential over-qualification
            overage_ratio = experience_years / optimal_max
            return max(0.7, 1.0 - (overage_ratio - 1) * 0.1)
    
    def _calculate_confidence(self, total_score: float, candidate: Dict) -> float:
        """Calculate confidence in the matching score"""
        # Base confidence on score and data completeness
        base_confidence = total_score
        
        # Adjust based on data completeness
        completeness_factors = [
            len(candidate.get('skills', [])) > 0,
            candidate.get('experience_years', 0) > 0,
            candidate.get('availability_percent', 0) > 0
        ]
        
        completeness_bonus = sum(completeness_factors) / len(completeness_factors) * 0.1
        
        return min(1.0, base_confidence + completeness_bonus)
    
    async def _generate_allocations(
        self, 
        scored_candidates: List[Tuple[Dict, Dict]], 
        project_req: ProjectRequirement,
        consider_conflicts: bool
    ) -> List[ResourceAllocation]:
        """Generate resource allocations from scored candidates using skill distribution"""
        allocations = []
        
        # Get skill distribution from project requirements
        skill_distribution = self._get_skill_distribution(project_req)
        
        # If we have skill distribution, use skill-based team formation
        if skill_distribution:
            return await self._generate_skill_based_allocations(
                scored_candidates, project_req, skill_distribution, consider_conflicts
            )
        
        # Fallback to simple capacity-based allocation
        return await self._generate_capacity_based_allocations(
            scored_candidates, project_req, consider_conflicts
        )
    
    def _get_skill_distribution(self, project_req: ProjectRequirement) -> Dict[str, float]:
        """Extract skill distribution from project requirements"""
        if not project_req.phase_skill_adjustments:
            return {}
        
        # Get skills for the current project phase
        phase_skills = project_req.phase_skill_adjustments.get(project_req.project_phase, {})
        return phase_skills
    
    async def _generate_skill_based_allocations(
        self,
        scored_candidates: List[Tuple[Dict, Dict]], 
        project_req: ProjectRequirement,
        skill_distribution: Dict[str, float],
        consider_conflicts: bool
    ) -> List[ResourceAllocation]:
        """Generate allocations based on skill distribution"""
        allocations = []
        allocated_skills = set()
        
        # Sort skills by importance (weight)
        sorted_skills = sorted(skill_distribution.items(), key=lambda x: x[1], reverse=True)
        
        # Estimate project duration
        if project_req.timeline:
            start_date, end_date = project_req.timeline
            duration_days = (end_date - start_date).days
        else:
            start_date = date.today()
            duration_days = 84  # 12 weeks default
            end_date = start_date + timedelta(days=duration_days)
        
        # For each skill, find the best candidate (avoiding already allocated employees)
        for skill, weight in sorted_skills:
            if skill in allocated_skills:
                continue
                
            best_candidate = None
            best_score = 0
            
            # Find candidate with best match for this skill (excluding already allocated employees)
            allocated_employee_ids = [a.employee_id for a in allocations]
            for candidate, score_data in scored_candidates:
                # Skip if this employee is already allocated
                if candidate['employee_id'] in allocated_employee_ids:
                    continue
                    
                candidate_skills = candidate.get('skills', [])
                if skill in candidate_skills:
                    # Calculate skill-specific score
                    skill_score = score_data['total_score'] * weight
                    if skill_score > best_score:
                        best_score = skill_score
                        best_candidate = candidate
            
            if best_candidate:
                # Calculate allocation based on skill importance
                allocation_percent = min(
                    weight * 100,  # Convert weight to percentage
                    best_candidate['availability_percent'],
                    60.0  # Max 60% per person
                )
                
                if allocation_percent >= 20.0:  # Only allocate if significant
                    allocation = ResourceAllocation(
                        employee_id=int(best_candidate['employee_id']),
                        project_id=project_req.project_id,
                        allocation_percent=allocation_percent,
                        start_date=start_date,
                        end_date=end_date,
                        skill_fit_score=best_score,
                        confidence_score=best_score
                    )
                    
                    if consider_conflicts:
                        allocation.alternatives = await self._generate_alternatives(
                            best_candidate, project_req, allocation_percent
                        )
                    
                    allocations.append(allocation)
                    allocated_skills.add(skill)
        
        # If we still need more team members, add generalists
        if len(allocations) < project_req.team_size_required:
            remaining_candidates = [
                (candidate, score_data) for candidate, score_data in scored_candidates
                if candidate['employee_id'] not in [a.employee_id for a in allocations]
            ]
            
            for candidate, score_data in remaining_candidates[:3]:  # Add up to 3 more
                allocation_percent = min(
                    candidate['availability_percent'],
                    40.0  # Lower allocation for generalists
                )
                
                if allocation_percent >= 20.0:
                    allocation = ResourceAllocation(
                        employee_id=candidate['employee_id'],
                        project_id=project_req.project_id,
                        allocation_percent=allocation_percent,
                        start_date=start_date,
                        end_date=end_date,
                        skill_fit_score=score_data['total_score'],
                        confidence_score=score_data['confidence']
                    )
                    
                    if consider_conflicts:
                        allocation.alternatives = await self._generate_alternatives(
                            candidate, project_req, allocation_percent
                        )
                    
                    allocations.append(allocation)
        
        return allocations
    
    async def _generate_capacity_based_allocations(
        self,
        scored_candidates: List[Tuple[Dict, Dict]], 
        project_req: ProjectRequirement,
        consider_conflicts: bool
    ) -> List[ResourceAllocation]:
        """Generate allocations based on capacity (fallback method)"""
        allocations = []
        
        # Calculate total capacity needed
        total_capacity_needed = 100.0  # 100% of project capacity
        remaining_capacity = total_capacity_needed
        
        # Estimate project duration (default 12 weeks if not specified)
        if project_req.timeline:
            start_date, end_date = project_req.timeline
            duration_days = (end_date - start_date).days
        else:
            start_date = date.today()
            duration_days = 84  # 12 weeks default
            end_date = start_date + timedelta(days=duration_days)
        
        for candidate, score_data in scored_candidates:
            if remaining_capacity <= 0:
                break
            
            # Calculate allocation percentage for this candidate
            # Consider their availability and project needs
            max_allocation = min(
                candidate['availability_percent'],
                remaining_capacity,
                50.0  # Max 50% per person for better distribution
            )
            
            if max_allocation < 20.0:  # Skip if less than 20% available
                continue
            
            # Create allocation
            allocation = ResourceAllocation(
                employee_id=int(candidate['employee_id']),
                project_id=project_req.project_id,
                allocation_percent=max_allocation,
                start_date=start_date,
                end_date=end_date,
                skill_fit_score=score_data['breakdown']['skill_fit'],
                confidence_score=score_data['confidence']
            )
            
            # Generate alternatives if requested
            if consider_conflicts:
                allocation.alternatives = await self._generate_alternatives(
                    candidate, project_req, max_allocation
                )
            
            allocations.append(allocation)
            remaining_capacity -= max_allocation
        
        return allocations
    
    async def _generate_alternatives(
        self, 
        candidate: Dict, 
        project_req: ProjectRequirement,
        current_allocation: float
    ) -> List[AlternativeOption]:
        """Generate alternative options for a candidate"""
        alternatives = []
        
        # Find similar employees with different availability/cost
        similar_candidates = self.vector_db.search_matching_employees(
            project_req,
            top_k=5,
            availability_threshold=20.0
        )
        
        for alt_candidate in similar_candidates:
            if alt_candidate['employee_id'] == candidate['employee_id']:
                continue
            
            # Calculate trade-offs
            trade_offs = []
            
            if alt_candidate['availability_percent'] < candidate['availability_percent']:
                trade_offs.append("Lower availability")
            
            if alt_candidate['similarity_score'] < candidate['similarity_score']:
                trade_offs.append("Lower skill match")
            
            alternative = AlternativeOption(
                employee_id=int(alt_candidate['employee_id']),
                name=alt_candidate['name'],
                skill_fit_score=alt_candidate['similarity_score'],
                availability_percent=alt_candidate['availability_percent'],
                trade_offs=trade_offs
            )
            
            alternatives.append(alternative)
        
        return alternatives[:3]  # Return top 3 alternatives
    
    
    async def optimize_team_composition(
        self, 
        project_req: ProjectRequirement,
        current_allocations: List[ResourceAllocation]
    ) -> List[ResourceAllocation]:
        """Optimize existing team composition"""
        try:
            # Analyze current team
            current_team_skills = set()
            total_allocation = sum(alloc.allocation_percent for alloc in current_allocations)
            
            # Get current team member details
            for allocation in current_allocations:
                employee = self.vector_db.get_employee_by_id(allocation.employee_id)
                if employee:
                    current_team_skills.update(employee['metadata'].get('skills', '').split(','))
            
            # Find optimization opportunities
            skill_gaps = await self.find_skill_gaps(project_req)
            
            # If we have significant gaps or over-allocation, suggest changes
            if skill_gaps['skill_coverage_percentage'] < 80 or total_allocation > 120:
                # Generate new optimized allocations
                return await self.find_optimal_allocation(project_req)
            
            return current_allocations
            
        except Exception as e:
            logger.error(f"Failed to optimize team composition: {str(e)}")
            return current_allocations
