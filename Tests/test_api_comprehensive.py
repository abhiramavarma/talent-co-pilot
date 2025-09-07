#!/usr/bin/env python3
"""
Comprehensive Backend API Test Suite
Tests all major components and endpoints
"""

import asyncio
import json
import sys
import os
from typing import Dict, Any

# Add backend directory to path
sys.path.append('backend')

from backend.app.models import EmployeeProfile, ProjectRequirement, AdvancedMatchingRequest
from backend.app.services.vector_db import EmployeeVectorDB
from backend.app.services.llm_service import ProjectRequirementExtractor
from backend.app.services.matching_engine import IntelligentMatchingEngine

class BackendTester:
    def __init__(self):
        self.vector_db = None
        self.requirement_extractor = None
        self.matching_engine = None
        self.conflict_resolver = None
        
    async def test_all_components(self):
        """Test all backend components comprehensively"""
        print("=" * 60)
        
        # Test 1: Vector Database
        await self.test_vector_database()
        
        # Test 2: LLM Service
        await self.test_llm_service()
        
        # Test 3: Matching Engine
        await self.test_matching_engine()
        
        # Test 4: Conflict Resolution
        await self.test_conflict_resolution()
        
        # Test 5: End-to-End Integration
        await self.test_end_to_end_integration()
        
        print("\n" + "=" * 60)
        print("All Backend Tests Completed!")
        
    async def test_vector_database(self):
        """Test vector database functionality"""
        print("\nTesting Vector Database...")
        try:
            self.vector_db = EmployeeVectorDB()
            stats = self.vector_db.get_collection_stats()
            print(f"Vector DB initialized: {stats['total_employees']} employees")
            
            # Test search functionality
            if stats['total_employees'] > 0:
                # Create a simple test project for search
                from backend.app.models import ProjectRequirement, ProjectPhase
                test_project = ProjectRequirement(
                    project_id=999,
                    project_name="Test Python Project",
                    description="Python development project",
                    project_phase=ProjectPhase.DEVELOPMENT,
                    priority_level=5,
                    team_size_required=1
                )
                results = self.vector_db.search_matching_employees(test_project, top_k=5)
                print(f" Search test: Found {len(results)} employees for test project")
                
                if results:
                    print(f"   Top {min(3, len(results))} matches:")
                    for i, result in enumerate(results[:3]):
                        print(f"     {i+1}. {result['name']} (score: {result['similarity_score']:.3f}, availability: {result['availability_percent']}%)")
                else:
                    print("   No matching employees found")
            
            return True
        except Exception as e:
            print(f" Vector DB test failed: {str(e)}")
            return False
    
    async def test_llm_service(self):
        """Test LLM service functionality"""
        print("\n Testing LLM Service...")
        try:
            self.requirement_extractor = ProjectRequirementExtractor()
            
            # Test skill extraction
            sample_text = """
            We need to build a React-based e-commerce platform with the following requirements:
            - Frontend: React with TypeScript, responsive design
            - Backend: Node.js with Express, RESTful APIs
            - Database: PostgreSQL for data storage
            - Authentication: JWT tokens
            - Payment: Stripe integration
            - Deployment: AWS with Docker containers
            """
            
            result = await self.requirement_extractor.extract_requirements(sample_text)
            print(f" LLM Service: Extracted project '{result.project_name[:50]}...'")
            print(f"   Description length: {len(result.description)} characters")
            print(f"   Project phase: {result.project_phase}")
            
            # Show skill distribution if available
            if result.phase_skill_adjustments:
                skills = result.phase_skill_adjustments.get(result.project_phase, {})
                if skills:
                    print(f"   Skill distribution: {len(skills)} skills identified")
                    for skill, weight in list(skills.items())[:5]:  # Show top 5 skills
                        print(f"     - {skill}: {weight:.2f}")
                else:
                    print("   No skill distribution extracted")
            else:
                print("   No skill distribution available")
            
            return True
        except Exception as e:
            print(f" LLM Service test failed: {str(e)}")
            return False
    
    async def test_matching_engine(self):
        """Test matching engine functionality"""
        print("\ Testing Matching Engine...")
        try:
            self.matching_engine = IntelligentMatchingEngine()
            
            # Create a test project
            from backend.app.models import ProjectPhase
            test_project = ProjectRequirement(
                project_id=999,
                project_name="Test E-commerce Platform",
                description="React-based e-commerce platform with Node.js backend",
                project_phase=ProjectPhase.DEVELOPMENT,
                priority_level=8,
                team_size_required=4
            )
            
            # Test matching
            allocations = await self.matching_engine.find_optimal_allocation(test_project)
            print(f" Matching Engine: Found {len(allocations)} potential allocations")
            
            if allocations:
                print(f"   Team composition ({len(allocations)} members):")
                for i, allocation in enumerate(allocations[:5]):  # Show up to 5 team members
                    print(f"     {i+1}. Employee {allocation.employee_id} - {allocation.allocation_percent}% allocation (confidence: {allocation.confidence_score:.3f})")
                
                # Show total allocation
                total_allocation = sum(a.allocation_percent for a in allocations)
                print(f"   Total team allocation: {total_allocation:.1f}%")
            else:
                print("   No suitable team members found")
            
            return True
        except Exception as e:
            print(f" Matching Engine test failed: {str(e)}")
            return False
    
    async def test_conflict_resolution(self):
        """Test conflict resolution functionality"""
        print("\ Testing Conflict Resolution...")
        try:
            self.conflict_resolver = ConflictResolutionEngine()
            
            # Create test allocations with conflicts
            from backend.app.models import ProjectPhase
            test_project = ProjectRequirement(
                project_id=998,
                project_name="Test Project with Conflicts",
                description="Test project for conflict resolution",
                project_phase=ProjectPhase.DEVELOPMENT,
                priority_level=7,
                team_size_required=2
            )
            
            # Test conflict resolution
            resolutions = await self.conflict_resolver.resolve_resource_conflicts(test_project, [])
            print(f" Conflict Resolution: Processed {len(resolutions)} potential conflicts")
            
            return True
        except Exception as e:
            print(f" Conflict Resolution test failed: {str(e)}")
            return False
    
    async def test_end_to_end_integration(self):
        """Test complete end-to-end workflow"""
        print("\n Testing End-to-End Integration...")
        try:
            # Create a realistic project
            project_description = """
            Build a modern web application for a healthcare startup:
            - Frontend: React with TypeScript, Material-UI components
            - Backend: Python FastAPI with PostgreSQL database
            - Authentication: OAuth2 with JWT tokens
            - Real-time features: WebSocket connections
            - Deployment: Docker containers on AWS
            - Testing: Jest for frontend, pytest for backend
            - CI/CD: GitHub Actions pipeline
            """
            
            # Extract requirements
            project_req = await self.requirement_extractor.extract_requirements(project_description)
            project_req.project_id = 997
            project_req.priority_level = 9
            
            print(f" E2E: Extracted project '{project_req.project_name[:40]}...'")
            print(f"   Description: {project_req.description[:100]}...")
            
            # Find matches
            allocations = await self.matching_engine.find_optimal_allocation(project_req)
            print(f" E2E: Found {len(allocations)} suitable team members")
            
            if allocations:
                print("   Top 3 matches:")
                for i, allocation in enumerate(allocations[:3]):
                    print(f"     {i+1}. Employee {allocation.employee_id} - {allocation.confidence_score:.3f} confidence")
                    print(f"        Allocation: {allocation.allocation_percent}%")
            
            # Test conflict resolution
            conflicts = await self.conflict_resolver.resolve_resource_conflicts(project_req, allocations)
            print(f" E2E: Resolved {len(conflicts)} conflicts")
            
            return True
        except Exception as e:
            print(f" End-to-End test failed: {str(e)}")
            return False

async def main():
    """Main test function"""
    tester = BackendTester()
    await tester.test_all_components()

if __name__ == "__main__":
    asyncio.run(main())
