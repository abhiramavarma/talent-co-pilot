#!/usr/bin/env python3
"""
Script to load generated dataset into the Talent Co-Pilot system
"""

import json
import os
import sys
import asyncio
from typing import List, Dict, Any
from datetime import datetime

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.models import EmployeeProfile, ProjectRequirement, ProjectPhase, ProjectHistory
from app.services.vector_db import EmployeeVectorDB
from app.services.llm_service import ProjectRequirementExtractor

class DatasetLoader:
    def __init__(self, data_dir: str = "backend/data"):
        """Initialize the dataset loader"""
        self.data_dir = data_dir
        self.vector_db = EmployeeVectorDB()
        self.requirement_extractor = ProjectRequirementExtractor()
        
    def load_employees_from_json(self, file_path: str) -> List[Dict[str, Any]]:
        """Load employees from JSON file"""
        try:
            with open(file_path, 'r') as f:
                employees_data = json.load(f)
            print(f"✅ Loaded {len(employees_data)} employees from {file_path}")
            return employees_data
        except FileNotFoundError:
            print(f"❌ Could not find {file_path}")
            return []
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing JSON: {e}")
            return []
    
    def load_projects_from_json(self, file_path: str) -> List[Dict[str, Any]]:
        """Load projects from JSON file"""
        try:
            with open(file_path, 'r') as f:
                projects_data = json.load(f)
            print(f"✅ Loaded {len(projects_data)} projects from {file_path}")
            return projects_data
        except FileNotFoundError:
            print(f"❌ Could not find {file_path}")
            return []
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing JSON: {e}")
            return []
    
    def convert_to_employee_profile(self, emp_data: Dict[str, Any]) -> EmployeeProfile:
        """Convert JSON data to EmployeeProfile model"""
        # Convert past projects
        past_projects = []
        for proj in emp_data.get('past_projects', []):
            past_projects.append(ProjectHistory(
                project_id=proj['project_id'],
                project_name=proj['project_name'],
                role=proj['role'],
                start_date=datetime.fromisoformat(proj['start_date']).date(),
                end_date=datetime.fromisoformat(proj['end_date']).date(),
                success_rating=proj['success_rating']
            ))
        
        return EmployeeProfile(
            employee_id=emp_data['employee_id'],
            name=emp_data['name'],
            role=emp_data['role'],
            skills=emp_data['skills'],
            experience_years=emp_data['experience_years'],
            certifications=emp_data.get('certifications', []),
            past_projects=past_projects,
            availability_percent=emp_data['availability_percent'],
            last_updated=datetime.fromisoformat(emp_data['last_updated']),
            # Real data fields
            education=emp_data.get('education'),
            joining_year=emp_data.get('joining_year'),
            age=emp_data.get('age'),
            gender=emp_data.get('gender'),
            ever_benched=emp_data.get('ever_benched'),
            experience_in_current_domain=emp_data.get('experience_in_current_domain'),
            payment_tier=emp_data.get('payment_tier'),
            leave_or_not=emp_data.get('leave_or_not')
        )
    
    def convert_to_project_requirement(self, proj_data: Dict[str, Any]) -> ProjectRequirement:
        """Convert JSON data to ProjectRequirement model"""
        # Parse timeline if available
        timeline = None
        if 'timeline' in proj_data and proj_data['timeline']:
            start_date = datetime.fromisoformat(proj_data['timeline'][0]).date()
            end_date = datetime.fromisoformat(proj_data['timeline'][1]).date()
            timeline = (start_date, end_date)
        
        return ProjectRequirement(
            project_id=proj_data['project_id'],
            project_name=proj_data['project_name'],
            description=proj_data['description'],
            skill_distribution=proj_data['skill_distribution'],
            project_phase=ProjectPhase(proj_data['project_phase']),
            priority_level=proj_data['priority_level'],
            team_size_required=proj_data['team_size_required'],
            created_at=datetime.fromisoformat(proj_data['created_at']),
            timeline=timeline
        )
    
    async def load_employees_to_vector_db(self, employees_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """Load employees into vector database"""
        print("🔄 Loading employees into vector database...")
        
        success_count = 0
        failure_count = 0
        
        for i, emp_data in enumerate(employees_data):
            try:
                # Convert to EmployeeProfile
                employee = self.convert_to_employee_profile(emp_data)
                
                # Add to vector database
                if self.vector_db.add_employee(employee):
                    success_count += 1
                else:
                    failure_count += 1
                
                # Progress indicator
                if (i + 1) % 100 == 0:
                    print(f"   Processed {i + 1}/{len(employees_data)} employees...")
                    
            except Exception as e:
                print(f"❌ Error processing employee {emp_data.get('employee_id', 'unknown')}: {e}")
                failure_count += 1
        
        result = {
            "success": success_count,
            "failed": failure_count,
            "total": len(employees_data)
        }
        
        print(f"✅ Employee loading completed: {success_count} success, {failure_count} failed")
        return result
    
    def save_projects_to_file(self, projects_data: List[Dict[str, Any]], output_file: str = "backend/data/projects_loaded.json"):
        """Save projects to a file for the API to use"""
        try:
            with open(output_file, 'w') as f:
                json.dump(projects_data, f, indent=2)
            print(f"✅ Saved {len(projects_data)} projects to {output_file}")
            return True
        except Exception as e:
            print(f"❌ Error saving projects: {e}")
            return False
    
    def generate_embeddings_for_projects(self, projects_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate embeddings for projects"""
        print("🔄 Generating embeddings for projects...")
        
        for i, proj_data in enumerate(projects_data):
            try:
                # Create project text for embedding
                project_text = f"{proj_data['description']} {' '.join(proj_data['skill_distribution'].keys())}"
                
                # Generate embedding
                embedding = self.requirement_extractor.embedding_model.encode(project_text)
                proj_data['embedding_vector'] = embedding.tolist()
                
                # Progress indicator
                if (i + 1) % 10 == 0:
                    print(f"   Generated embeddings for {i + 1}/{len(projects_data)} projects...")
                    
            except Exception as e:
                print(f"❌ Error generating embedding for project {proj_data.get('project_id', 'unknown')}: {e}")
                proj_data['embedding_vector'] = []
        
        print("✅ Project embeddings generated")
        return projects_data
    
    async def load_complete_dataset(self):
        """Load complete dataset into the system"""
        print("🚀 Starting dataset loading process...")
        
        # Load employees
        employees_file = os.path.join(self.data_dir, "employees.json")
        employees_data = self.load_employees_from_json(employees_file)
        
        if not employees_data:
            print("❌ No employee data to load")
            return
        
        # Load employees into vector database
        employee_result = await self.load_employees_to_vector_db(employees_data)
        
        # Load projects
        projects_file = os.path.join(self.data_dir, "projects.json")
        projects_data = self.load_projects_from_json(projects_file)
        
        if projects_data:
            # Generate embeddings for projects
            projects_data = self.generate_embeddings_for_projects(projects_data)
            
            # Save projects with embeddings
            self.save_projects_to_file(projects_data)
        
        # Get final statistics
        stats = self.vector_db.get_collection_stats()
        
        print("\n🎉 Dataset loading completed successfully!")
        print(f"📊 Final Statistics:")
        print(f"   • Employees in vector DB: {stats.get('total_employees', 0)}")
        print(f"   • Projects loaded: {len(projects_data) if projects_data else 0}")
        print(f"   • Employee loading: {employee_result['success']} success, {employee_result['failed']} failed")
        
        return {
            "employees_loaded": employee_result['success'],
            "projects_loaded": len(projects_data) if projects_data else 0,
            "vector_db_stats": stats
        }

async def main():
    """Main function to run dataset loading"""
    loader = DatasetLoader()
    
    try:
        result = await loader.load_complete_dataset()
        
        if result:
            print(f"\n✅ Dataset loading completed successfully!")
            print(f"   • {result['employees_loaded']} employees loaded")
            print(f"   • {result['projects_loaded']} projects loaded")
        else:
            print("❌ Dataset loading failed")
            
    except Exception as e:
        print(f"❌ Error during dataset loading: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
