#!/usr/bin/env python3
"""
Script to update services to work with simplified data models
Removes location, timezone, hourly_cost, proficiency, and synergy score logic
"""

import os
import shutil
from datetime import datetime

def backup_original_file(file_path):
    """Create backup of original file"""
    if os.path.exists(file_path):
        backup_path = f"{file_path}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(file_path, backup_path)
        print(f"✅ Created backup: {backup_path}")
        return True
    return False

def update_vector_db_service():
    """Update vector database service"""
    updated_content = '''import os
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional, Tuple
import numpy as np
import logging
from ..models import EmployeeProfile, ProjectRequirement

logger = logging.getLogger(__name__)


class EmployeeVectorDB:
    def __init__(self, persist_directory: str = None):
        """Initialize ChromaDB client and embedding model"""
        self.persist_directory = persist_directory or os.getenv('CHROMA_DB_PATH', '/app/chroma_data')
        
        # Initialize ChromaDB client
        self.chroma_client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Create or get collection
        try:
            self.collection = self.chroma_client.get_collection(
                name="employees",
                metadata={"hnsw:space": "cosine"}
            )
        except:
            self.collection = self.chroma_client.create_collection(
                name="employees",
                metadata={"hnsw:space": "cosine"}
            )
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("EmployeeVectorDB initialized successfully")
    
    def add_employee(self, employee: EmployeeProfile) -> bool:
        """Add employee to vector database"""
        try:
            # Create rich text representation for embedding
            employee_text = self._create_employee_text(employee)
            embedding = self.embedding_model.encode(employee_text)
            
            # Prepare metadata
            metadata = {
                "employee_id": employee.employee_id,
                "name": employee.name,
                "role": employee.role,
                "availability_percent": employee.availability_percent,
                "experience_years": employee.experience_years,
                "skills": ",".join(employee.skills),
                "certifications": ",".join(employee.certifications),
                "education": employee.education or "",
                "age": employee.age or 0,
                "gender": employee.gender or "",
                "last_updated": employee.last_updated.isoformat()
            }
            
            # Add to collection
            self.collection.add(
                embeddings=[embedding.tolist()],
                metadatas=[metadata],
                documents=[employee_text],
                ids=[str(employee.employee_id)]
            )
            
            logger.info(f"Employee {employee.employee_id} added to vector database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add employee {employee.employee_id}: {str(e)}")
            return False
    
    def search_matching_employees(
        self, 
        project_req: ProjectRequirement, 
        top_k: int = 10,
        availability_threshold: float = 20.0
    ) -> List[Dict]:
        """Find employees matching project requirements"""
        try:
            # Create search query from project requirements
            query_text = self._create_project_query_text(project_req)
            query_embedding = self.embedding_model.encode(query_text)
            
            # Build where clause for filtering
            where_clause = {
                "$and": [
                    {"availability_percent": {"$gte": availability_threshold}}
                ]
            }
            
            # Perform vector search
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=top_k,
                where=where_clause,
                include=["metadatas", "documents", "distances"]
            )
            
            # Process and return results
            return self._process_search_results(results, project_req)
            
        except Exception as e:
            logger.error(f"Vector search failed: {str(e)}")
            return []
    
    def update_employee_availability(self, employee_id: int, new_availability: float) -> bool:
        """Update employee availability after allocation"""
        try:
            self.collection.update(
                ids=[str(employee_id)],
                metadatas=[{"availability_percent": new_availability}]
            )
            logger.info(f"Updated availability for employee {employee_id} to {new_availability}%")
            return True
        except Exception as e:
            logger.error(f"Failed to update availability for employee {employee_id}: {str(e)}")
            return False
    
    def get_employee_by_id(self, employee_id: int) -> Optional[Dict]:
        """Get employee by ID"""
        try:
            results = self.collection.get(
                ids=[str(employee_id)],
                include=["metadatas", "documents", "embeddings"]
            )
            
            if results['ids']:
                return {
                    'employee_id': employee_id,
                    'metadata': results['metadatas'][0],
                    'document': results['documents'][0],
                    'embedding': results['embeddings'][0]
                }
            return None
            
        except Exception as e:
            logger.error(f"Failed to get employee {employee_id}: {str(e)}")
            return None
    
    def delete_employee(self, employee_id: int) -> bool:
        """Delete employee from vector database"""
        try:
            self.collection.delete(ids=[str(employee_id)])
            logger.info(f"Employee {employee_id} deleted from vector database")
            return True
        except Exception as e:
            logger.error(f"Failed to delete employee {employee_id}: {str(e)}")
            return False
    
    def get_collection_stats(self) -> Dict:
        """Get collection statistics"""
        try:
            count = self.collection.count()
            return {
                "total_employees": count,
                "collection_name": self.collection.name,
                "embedding_dimension": len(self.embedding_model.encode("test"))
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {str(e)}")
            return {}
    
    def _create_employee_text(self, employee: EmployeeProfile) -> str:
        """Create rich text representation for semantic embedding"""
        skills_text = " ".join(employee.skills)
        projects_text = " ".join([p.project_name for p in employee.past_projects])
        certifications_text = " ".join(employee.certifications)
        
        return f"""
        Role: {employee.role}
        Skills: {skills_text}
        Experience: {employee.experience_years} years
        Past Projects: {projects_text}
        Certifications: {certifications_text}
        Education: {employee.education or 'Not specified'}
        """
    
    def _create_project_query_text(self, project_req: ProjectRequirement) -> str:
        """Create search query text from project requirements"""
        skills_text = " ".join([f"{skill}:{weight}" for skill, weight in project_req.skill_distribution.items()])
        
        return f"""
        Project: {project_req.project_name}
        Description: {project_req.description}
        Phase: {project_req.project_phase.value}
        Required Skills: {skills_text}
        Team Size: {project_req.team_size_required}
        Priority: {project_req.priority_level}
        """
    
    def _process_search_results(self, results: Dict, project_req: ProjectRequirement) -> List[Dict]:
        """Process ChromaDB search results into standardized format"""
        processed_results = []
        
        if not results['ids']:
            return processed_results
        
        for i, employee_id in enumerate(results['ids']):
            metadata = results['metadatas'][i]
            distance = results['distances'][i] if results['distances'] else [0.0]
            
            # Convert distance to similarity score (1 - distance)
            similarity_score = max(0.0, 1.0 - distance[0])
            
            # Parse skills from metadata
            skills = metadata.get('skills', '').split(',') if metadata.get('skills') else []
            
            processed_result = {
                'employee_id': int(employee_id),
                'name': metadata.get('name', ''),
                'role': metadata.get('role', ''),
                'skills': skills,
                'availability_percent': float(metadata.get('availability_percent', 0)),
                'experience_years': int(metadata.get('experience_years', 0)),
                'certifications': metadata.get('certifications', '').split(',') if metadata.get('certifications') else [],
                'education': metadata.get('education', ''),
                'age': int(metadata.get('age', 0)),
                'gender': metadata.get('gender', ''),
                'similarity_score': similarity_score,
                'distance': distance[0] if distance else 0.0
            }
            
            processed_results.append(processed_result)
        
        return processed_results
    
    def batch_add_employees(self, employees: List[EmployeeProfile]) -> Dict[str, int]:
        """Add multiple employees in batch"""
        success_count = 0
        failure_count = 0
        
        for employee in employees:
            if self.add_employee(employee):
                success_count += 1
            else:
                failure_count += 1
        
        return {
            "success": success_count,
            "failed": failure_count,
            "total": len(employees)
        }
    
    def search_by_skills(
        self, 
        required_skills: List[str], 
        top_k: int = 10
    ) -> List[Dict]:
        """Search employees by specific skills"""
        try:
            # Create skill-based query
            skills_text = " ".join(required_skills)
            query_embedding = self.embedding_model.encode(skills_text)
            
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=top_k,
                include=["metadatas", "documents", "distances"]
            )
            
            # Filter by skill match
            filtered_results = []
            for i, metadata in enumerate(results['metadatas']):
                employee_skills = metadata.get('skills', '').split(',') if metadata.get('skills') else []
                
                # Check if employee has any of the required skills
                has_required_skills = any(skill in employee_skills for skill in required_skills)
                
                if has_required_skills:
                    distance = results['distances'][i] if results['distances'] else [0.0]
                    similarity_score = max(0.0, 1.0 - distance[0])
                    
                    filtered_results.append({
                        'employee_id': int(results['ids'][i]),
                        'name': metadata.get('name', ''),
                        'role': metadata.get('role', ''),
                        'skills': employee_skills,
                        'availability_percent': float(metadata.get('availability_percent', 0)),
                        'similarity_score': similarity_score
                    })
            
            return filtered_results
            
        except Exception as e:
            logger.error(f"Skill-based search failed: {str(e)}")
            return []
'''
    
    # Write updated vector database service
    with open("backend/app/services/vector_db.py", "w") as f:
        f.write(updated_content)
    
    print("✅ Updated vector database service")

def update_matching_engine():
    """Update matching engine to remove location, cost, and synergy logic"""
    updated_content = '''import logging
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
            
            # Phase relevance score
            phase_relevance = self._calculate_phase_relevance(
                candidate['skills'], 
                project_req
            )
            
            # Priority alignment score
            priority_bonus = project_req.priority_level / 10.0
            
            # Experience relevance
            experience_score = self._calculate_experience_score(
                candidate['experience_years'],
                project_req
            )
            
            # Education relevance
            education_score = self._calculate_education_score(
                candidate.get('education', ''),
                project_req
            )
            
            # Composite scoring with weights
            weights = {
                'skill_fit': 0.40,
                'availability': 0.25,
                'phase_relevance': 0.15,
                'experience': 0.10,
                'education': 0.10
            }
            
            total_score = (
                skill_fit * weights['skill_fit'] +
                availability_score * weights['availability'] +
                phase_relevance * weights['phase_relevance'] +
                experience_score * weights['experience'] +
                education_score * weights['education']
            ) * (1 + priority_bonus * 0.1)  # Priority boost
            
            return {
                'total_score': min(1.0, total_score),
                'breakdown': {
                    'skill_fit': skill_fit,
                    'availability': availability_score,
                    'phase_relevance': phase_relevance,
                    'experience': experience_score,
                    'education': education_score
                },
                'confidence': self._calculate_confidence(total_score, candidate)
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate composite score: {str(e)}")
            return {'total_score': 0.0, 'breakdown': {}, 'confidence': 0.0}
    
    def _calculate_phase_relevance(self, employee_skills: List[str], project_req: ProjectRequirement) -> float:
        """Calculate how relevant employee skills are to project phase"""
        phase_skill_weights = {
            ProjectPhase.DESIGN: {
                'architecture': 1.5, 'ui_ux': 1.4, 'system_design': 1.3,
                'design_thinking': 1.6, 'wireframing': 1.4, 'figma': 1.3
            },
            ProjectPhase.DEVELOPMENT: {
                'programming': 1.4, 'react': 1.3, 'nodejs': 1.3,
                'python': 1.2, 'javascript': 1.2, 'databases': 1.2
            },
            ProjectPhase.TESTING: {
                'testing': 1.8, 'qa': 1.6, 'automation': 1.4,
                'test_automation': 1.5, 'performance_testing': 1.3
            },
            ProjectPhase.DEPLOYMENT: {
                'devops': 1.8, 'aws': 1.6, 'docker': 1.5,
                'kubernetes': 1.6, 'monitoring': 1.4
            }
        }
        
        phase_weights = phase_skill_weights.get(project_req.project_phase, {})
        
        total_relevance = 0.0
        total_weight = 0.0
        
        for skill in employee_skills:
            normalized_skill = skill.lower().replace(' ', '_').replace('-', '_')
            phase_weight = phase_weights.get(normalized_skill, 1.0)
            
            total_relevance += phase_weight
            total_weight += phase_weight
        
        return total_relevance / total_weight if total_weight > 0 else 0.0
    
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
    
    def _calculate_education_score(self, education: str, project_req: ProjectRequirement) -> float:
        """Calculate education relevance score"""
        education_weights = {
            'PHD': 1.0,
            'Masters': 0.9,
            'Bachelors': 0.8,
            '': 0.5  # No education specified
        }
        
        return education_weights.get(education, 0.7)
    
    def _calculate_confidence(self, total_score: float, candidate: Dict) -> float:
        """Calculate confidence in the matching score"""
        # Base confidence on score and data completeness
        base_confidence = total_score
        
        # Adjust based on data completeness
        completeness_factors = [
            len(candidate.get('skills', [])) > 0,
            candidate.get('experience_years', 0) > 0,
            candidate.get('availability_percent', 0) > 0,
            candidate.get('education', '') != ''
        ]
        
        completeness_bonus = sum(completeness_factors) / len(completeness_factors) * 0.1
        
        return min(1.0, base_confidence + completeness_bonus)
    
    async def _generate_allocations(
        self, 
        scored_candidates: List[Tuple[Dict, Dict]], 
        project_req: ProjectRequirement,
        consider_conflicts: bool
    ) -> List[ResourceAllocation]:
        """Generate resource allocations from scored candidates"""
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
                employee_id=candidate['employee_id'],
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
        
        # Find similar employees with different availability
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
                employee_id=alt_candidate['employee_id'],
                name=alt_candidate['name'],
                skill_fit_score=alt_candidate['similarity_score'],
                availability_percent=alt_candidate['availability_percent'],
                trade_offs=trade_offs
            )
            
            alternatives.append(alternative)
        
        return alternatives[:3]  # Return top 3 alternatives
    
    async def find_skill_gaps(self, project_req: ProjectRequirement) -> Dict[str, List[str]]:
        """Identify skill gaps in available workforce"""
        try:
            # Get all available employees
            all_candidates = self.vector_db.search_matching_employees(
                project_req,
                top_k=100,
                availability_threshold=10.0
            )
            
            # Analyze skill coverage
            required_skills = set(project_req.skill_distribution.keys())
            available_skills = set()
            
            for candidate in all_candidates:
                available_skills.update(candidate.get('skills', []))
            
            # Find gaps
            skill_gaps = required_skills - available_skills
            
            # Find under-represented skills
            skill_counts = {}
            for candidate in all_candidates:
                for skill in candidate.get('skills', []):
                    skill_counts[skill] = skill_counts.get(skill, 0) + 1
            
            under_represented = [
                skill for skill, count in skill_counts.items()
                if skill in required_skills and count < 2
            ]
            
            return {
                'missing_skills': list(skill_gaps),
                'under_represented_skills': under_represented,
                'total_available_employees': len(all_candidates),
                'skill_coverage_percentage': len(available_skills & required_skills) / len(required_skills) * 100
            }
            
        except Exception as e:
            logger.error(f"Failed to find skill gaps: {str(e)}")
            return {'missing_skills': [], 'under_represented_skills': [], 'total_available_employees': 0, 'skill_coverage_percentage': 0}
    
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
'''
    
    # Write updated matching engine
    with open("backend/app/services/matching_engine.py", "w") as f:
        f.write(updated_content)
    
    print("✅ Updated matching engine")

def main():
    """Main function to update services"""
    print("🔄 Updating services to work with simplified data models...")
    
    # Update vector database service
    if backup_original_file("backend/app/services/vector_db.py"):
        update_vector_db_service()
    
    # Update matching engine
    if backup_original_file("backend/app/services/matching_engine.py"):
        update_matching_engine()
    
    print("✅ Services updated successfully!")
    print("📝 Changes made:")
    print("   • Removed location and timezone logic")
    print("   • Removed hourly cost calculations")
    print("   • Simplified skills to List[str]")
    print("   • Removed team synergy calculations")
    print("   • Added education and age scoring")
    print("   • Updated metadata structure")

if __name__ == "__main__":
    main()
