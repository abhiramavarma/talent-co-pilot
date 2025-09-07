#!/usr/bin/env python3
"""
Complete setup script for Talent Co-Pilot dataset
This script will:
1. Update data models to remove unnecessary fields
2. Update services to work with simplified models
3. Generate synthetic dataset based on real CSV data
4. Load the dataset into the vector database
"""

import os
import sys
import subprocess
import asyncio
from pathlib import Path

def run_script(script_path: str, description: str) -> bool:
    """Run a Python script and return success status"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run([
            sys.executable, script_path
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print(f"❌ {description} failed")
            if result.stderr:
                print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error running {script_path}: {e}")
        return False

def install_requirements():
    """Install additional requirements for dataset generation"""
    print("\n🔄 Installing additional requirements...")
    try:
        requirements_file = "backend/scripts/requirements.txt"
        if os.path.exists(requirements_file):
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", requirements_file
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Additional requirements installed successfully")
                return True
            else:
                print(f"❌ Failed to install requirements: {result.stderr}")
                return False
        else:
            print("⚠️  Requirements file not found, skipping installation")
            return True
    except Exception as e:
        print(f"❌ Error installing requirements: {e}")
        return False

def check_csv_file():
    """Check if the real CSV data file exists"""
    csv_file = "backend/data/Employee.csv"
    if os.path.exists(csv_file):
        print(f"✅ Found real employee data: {csv_file}")
        return True
    else:
        print(f"❌ Real employee data not found: {csv_file}")
        print("   Please ensure the Employee.csv file is in the backend/data/ directory")
        return False

def main():
    """Main setup function"""
    print("🚀 Starting complete dataset setup for Talent Co-Pilot...")
    
    # Check if we're in the right directory
    if not os.path.exists("backend"):
        print("❌ Please run this script from the project root directory")
        return False
    
    # Check for real CSV data
    if not check_csv_file():
        return False
    
    # Install additional requirements
    if not install_requirements():
        print("⚠️  Continuing without additional requirements...")
    
    # Step 1: Update data models
    if not run_script("backend/scripts/update_models.py", "Updating data models"):
        return False
    
    # Step 2: Update services
    if not run_script("backend/scripts/update_services.py", "Updating services"):
        return False
    
    # Step 3: Generate dataset
    if not run_script("backend/scripts/generate_dataset.py", "Generating synthetic dataset"):
        return False
    
    # Step 4: Load dataset into vector database
    print("\n🔄 Loading dataset into vector database...")
    try:
        # Import and run the loader
        sys.path.append("backend")
        from scripts.load_dataset import DatasetLoader
        
        async def load_data():
            loader = DatasetLoader()
            return await loader.load_complete_dataset()
        
        result = asyncio.run(load_data())
        
        if result:
            print("✅ Dataset loaded into vector database successfully")
        else:
            print("❌ Failed to load dataset into vector database")
            return False
            
    except Exception as e:
        print(f"❌ Error loading dataset: {e}")
        return False
    
    print("\n🎉 Complete dataset setup finished successfully!")
    print("\n📊 What was accomplished:")
    print("   ✅ Updated data models (removed location, timezone, hourly_cost, proficiency, synergy)")
    print("   ✅ Updated services to work with simplified models")
    print("   ✅ Generated synthetic dataset based on real CSV data")
    print("   ✅ Loaded employees into ChromaDB vector database")
    print("   ✅ Generated project embeddings")
    print("\n🚀 Your Talent Co-Pilot system is ready to use!")
    print("\nNext steps:")
    print("   1. Start the backend: cd backend && python -m uvicorn app.main:app --reload")
    print("   2. Start the frontend: cd frontend && npm start")
    print("   3. Access the API docs at: http://localhost:8000/docs")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
