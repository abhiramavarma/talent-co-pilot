
#!/usr/bin/env python3
"""
Simple script to load generated dataset into the vector database
"""

import json
import os
import sys
import asyncio
from typing import List, Dict, Any
from datetime import datetime

# Add the current directory to the Python path
sys.path.append(os.path.dirname(__file__))

from app.models import EmployeeProfile, ProjectRequirement, ProjectPhase, ProjectHistory
from app.services.vector_db import EmployeeVectorDB

class DatasetLoader:
    def __init__(self, data_dir: str = "data"):
        """Initialize the dataset loader"""
        self.data_dir = data_dir
        # Use the correct ChromaDB path relative to the backend directory
        self.vector_db = EmployeeVectorDB(persist_directory="./chroma_db")
        
    def load_employees_from_json(self, file_path: str) -> List[Dict[str, Any]]:
        """Load employees from JSON file"""
        try:
            with open(file_path, 'r') as f:
                employees_data = json.load(f)
            print(f"Loaded {len(employees_data)} employees from {file_path}")
            return employees_data
        except FileNotFoundError:
            print(f"Could not find {file_path}")
            return []
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
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
            skills=emp_data['skills'],
            experience_years=emp_data['experience_years'],
            certifications=emp_data.get('certifications', []),
            past_projects=past_projects,
            availability_percent=emp_data['availability_percent'],
            last_updated=datetime.fromisoformat(emp_data['last_updated'])
        )
    
    async def load_employees_to_vector_db(self, employees_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """Load employees into vector database"""
        print("Loading employees into vector database...")
        
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
                if (i + 1) % 500 == 0:
                    print(f"   Processed {i + 1}/{len(employees_data)} employees...")
                    
            except Exception as e:
                print(f"Error processing employee {emp_data.get('employee_id', 'unknown')}: {e}")
                failure_count += 1
        
        result = {
            "success": success_count,
            "failed": failure_count,
            "total": len(employees_data)
        }
        
        print(f"Employee loading completed: {success_count} success, {failure_count} failed")
        return result
    
    async def load_complete_dataset(self):
        """Load complete dataset into the system"""
        print("Starting dataset loading process...")
        
        # Load employees
        employees_file = os.path.join(self.data_dir, "employees.json")
        employees_data = self.load_employees_from_json(employees_file)
        
        if not employees_data:
            print("No employee data to load")
            return
        
        # Load employees into vector database
        employee_result = await self.load_employees_to_vector_db(employees_data)
        
        # Get final statistics
        stats = self.vector_db.get_collection_stats()
        
        print("\nDataset loading completed successfully!")
        print(f"Final Statistics:")
        print(f"   - Employees in vector DB: {stats.get('total_employees', 0)}")
        print(f"   - Employee loading: {employee_result['success']} success, {employee_result['failed']} failed")
        
        return {
            "employees_loaded": employee_result['success'],
            "vector_db_stats": stats
        }

async def main():
    """Main function to run dataset loading"""
    loader = DatasetLoader()
    
    try:
        result = await loader.load_complete_dataset()
        
        if result:
            print(f"\nDataset loading completed successfully!")
            print(f"   - {result['employees_loaded']} employees loaded")
        else:
            print("Dataset loading failed")
            
    except Exception as e:
        print(f"Error during dataset loading: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
