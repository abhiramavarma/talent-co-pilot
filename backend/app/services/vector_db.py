import os
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
        self.persist_directory = persist_directory or os.getenv('CHROMA_DB_PATH', './chroma_db')
        
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
            self.collection = self.chroma_client.get_collection(name="employees")
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
                "availability_percent": employee.availability_percent,
                "experience_years": employee.experience_years,
                "skills": ",".join(employee.skills),
                "certifications": ",".join(employee.certifications),
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
            
    
            all_results = self.collection.get(
                include=["metadatas", "documents", "embeddings"]
            )
            
            
            similarities = []
            for i, employee_id in enumerate(all_results['ids']):
                metadata = all_results['metadatas'][i]
                
                
                if metadata.get('availability_percent', 0) < availability_threshold:
                    continue
                
                
                employee_embedding = all_results['embeddings'][i]
                similarity = self._calculate_cosine_similarity(
                    query_embedding, 
                    employee_embedding
                )
                
                similarities.append({
                    'employee_id': employee_id,
                    'metadata': metadata,
                    'similarity': similarity,
                    'distance': 1.0 - similarity
                })
            
            # Sort by similarity and return top_k
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            top_results = similarities[:top_k]
            
            # Convert to expected format
            processed_results = []
            for result in top_results:
                print(f"Vector DB result: employee_id={result['employee_id']}, name={result['metadata'].get('name', 'Unknown')}")
                processed_result = {
                    'employee_id': int(result['employee_id']),
                    'name': result['metadata'].get('name', ''),
                    'skills': result['metadata'].get('skills', '').split(',') if result['metadata'].get('skills') else [],
                    'skill_proficiencies': {},
                    'availability_percent': float(result['metadata'].get('availability_percent', 0)),
                    'experience_years': int(result['metadata'].get('experience_years', 0)),
                    'certifications': result['metadata'].get('certifications', '').split(',') if result['metadata'].get('certifications') else [],
                    'similarity_score': result['similarity'],
                    'distance': result['distance']
                }
                processed_results.append(processed_result)
            
            return processed_results
            
        except Exception as e:
            logger.error(f"Vector search failed: {str(e)}")
            return []
        
    def recommend_by_career_goal(
        self, 
        project_req: ProjectRequirement, 
        top_k: int = 5,
        base_availability_threshold: float = 20.0,
        negotiable_bonus: float = 10.0
    ) -> List[Dict]:
            """
            Recommend employees based on career goals.
            If an employee's career goal matches the project focus, they are recommended
            even if their availability is slightly below the base threshold."""
            try:
                query_text = self._create_project_query_text(project_req)
                query_embedding = self.embedding_model.encode(query_text)

                all_results = self.collection.get(include=["metadatas", "documents", "embeddings"])

                recommendations = []
                for i, employee_id in enumerate(all_results['ids']):
                    metadata = all_results['metadatas'][i]

                    availability = float(metadata.get('availability_percent', 0))
                    career_goal = metadata.get('career_goal', '').lower()
                    project_focus = project_req.focus.lower()  # assuming project_req has a 'focus' field

                    # Check if career goal matches project focus
                    career_match = project_focus in career_goal

                    # Relax threshold if career goal matches
                    effective_threshold = base_availability_threshold - negotiable_bonus if career_match else base_av
            except:pass

    
    def _calculate_cosine_similarity(self, vec1: np.ndarray, vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            vec2_array = np.array(vec2)
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2_array)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2_array)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0
    
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
        Skills: {skills_text}
        Experience: {employee.experience_years} years
        Past Projects: {projects_text}
        Certifications: {certifications_text}
        """
    
    def _create_project_query_text(self, project_req: ProjectRequirement) -> str:
        """Create search query text from project requirements"""
        return f"""
        Project: {project_req.project_name}
        Description: {project_req.description}
        Phase: {project_req.project_phase.value}
        Team Size: {project_req.team_size_required}
        Priority: {project_req.priority_level}
        """
    
    def _process_search_results(self, results: Dict, project_req: ProjectRequirement) -> List[Dict]:
        """Process ChromaDB search results into standardized format"""
        processed_results = []
        
        if not results['ids']:
            return processed_results
        
        # Debug logging (commented out for production)
        # print(f"ChromaDB results structure: {list(results.keys())}")
        # print(f"Number of results: {len(results['ids'])}")
        # if results['metadatas']:
        #     print(f"First metadata type: {type(results['metadatas'][0])}")
        #     print(f"First metadata: {results['metadatas'][0]}")
        
        for i, employee_id in enumerate(results['ids']):
            # Handle different metadata formats from ChromaDB
            if results['metadatas'] and i < len(results['metadatas']):
                metadata = results['metadatas'][i]
                # If metadata is a list, take the first element (which should be a dict)
                if isinstance(metadata, list) and len(metadata) > 0:
                    # Find the metadata that matches the current employee_id
                    matching_metadata = None
                    try:
                        # Handle employee_id as list or single value
                        if isinstance(employee_id, list) and len(employee_id) > 0:
                            target_id = int(employee_id[0])
                        else:
                            target_id = int(employee_id)
                        
                        for meta in metadata:
                            if isinstance(meta, dict) and meta.get('employee_id') == target_id:
                                matching_metadata = meta
                                break
                    except Exception as e:
                        # print(f"Error matching employee_id: {e}")
                        # print(f"employee_id: {employee_id}, type: {type(employee_id)}")
                        matching_metadata = None
                    # If no match found, use the first one
                    metadata = matching_metadata if matching_metadata else (metadata[0] if isinstance(metadata[0], dict) else {})
                elif not isinstance(metadata, dict):
                    metadata = {}
            else:
                metadata = {}
            
            distance = results['distances'][i] if results['distances'] and i < len(results['distances']) else [0.0]
            
            # Convert distance to similarity score (1 - distance)
            try:
                similarity_score = max(0.0, 1.0 - distance[0])
            except Exception as e:
                # print(f"Error calculating similarity score: {e}")
                # print(f"Distance: {distance}, type: {type(distance)}")
                similarity_score = 0.0
            
            # Parse skills from metadata
            skills = metadata.get('skills', '').split(',') if metadata.get('skills') else []
            skill_proficiencies = {}
            if metadata.get('skill_proficiencies'):
                for sp in metadata['skill_proficiencies'].split(','):
                    if ':' in sp:
                        skill, prof = sp.split(':', 1)
                        try:
                            skill_proficiencies[skill] = float(prof)
                        except ValueError:
                            continue
            
            # Handle employee_id as list or single value
            try:
                if isinstance(employee_id, list) and len(employee_id) > 0:
                    emp_id = int(employee_id[0])
                else:
                    emp_id = int(employee_id)
            except:
                emp_id = 0
            
            processed_result = {
                'employee_id': emp_id,
                'name': metadata.get('name', ''),
                'skills': skills,
                'availability_percent': float(metadata.get('availability_percent', 0)) if isinstance(metadata.get('availability_percent'), (int, float, str)) else 0.0,
                'experience_years': int(metadata.get('experience_years', 0)) if isinstance(metadata.get('experience_years'), (int, str)) else 0,
                'certifications': metadata.get('certifications', '').split(',') if metadata.get('certifications') else [],
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
        min_proficiency: float = 0.5,
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
            
            # Filter by minimum proficiency
            filtered_results = []
            for i, metadata in enumerate(results['metadatas']):
                skill_proficiencies = {}
                if metadata.get('skill_proficiencies'):
                    for sp in metadata['skill_proficiencies'].split(','):
                        if ':' in sp:
                            skill, prof = sp.split(':', 1)
                            try:
                                skill_proficiencies[skill] = float(prof)
                            except ValueError:
                                continue
                
                # Check if employee has required skills with minimum proficiency
                has_required_skills = all(
                    skill_proficiencies.get(skill, 0) >= min_proficiency 
                    for skill in required_skills
                )
                
                if has_required_skills:
                    distance = results['distances'][i] if results['distances'] else [0.0]
                    similarity_score = max(0.0, 1.0 - distance[0])
                    
                    filtered_results.append({
                        'employee_id': int(results['ids'][i]),
                        'name': metadata.get('name', ''),
                        'skills': metadata.get('skills', '').split(',') if metadata.get('skills') else [],
                        'skill_proficiencies': skill_proficiencies,
                        'availability_percent': float(metadata.get('availability_percent', 0)),
                        'similarity_score': similarity_score
                    })
            
            return filtered_results
            
        except Exception as e:
            logger.error(f"Skill-based search failed: {str(e)}")
            return []
