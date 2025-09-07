#!/usr/bin/env python3
"""
Simple setup script for Talent Co-Pilot dataset generation
"""

import os
import sys
import subprocess
class DatasetGeneration:
    def run_script(script_path: str, description: str) -> bool:
        """Run a Python script and return success status"""
        print(f"\n{description}...")
        try:
            result = subprocess.run([
                sys.executable, script_path
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"SUCCESS: {description} completed")
                if result.stdout:
                    print(result.stdout)
                return True
            else:
                print(f"FAILED: {description}")
                if result.stderr:
                    print(f"Error: {result.stderr}")
                return False
        except Exception as e:
            print(f"Error running {script_path}: {e}")
            return False

    def install_requirements():
        """Install additional requirements for dataset generation"""
        print("\nInstalling additional requirements...")
        try:
            requirements_file = "backend/scripts/requirements.txt"
            if os.path.exists(requirements_file):
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install", "-r", requirements_file
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    print("SUCCESS: Additional requirements installed")
                    return True
                else:
                    print(f"FAILED to install requirements: {result.stderr}")
                    return False
            else:
                print("WARNING: Requirements file not found, skipping installation")
                return True
        except Exception as e:
            print(f"Error installing requirements: {e}")
            return False

    def check_csv_file():
        """Check if the real CSV data file exists"""
        csv_file = "backend/data/Employee.csv"
        if os.path.exists(csv_file):
            print(f"SUCCESS: Found real employee data: {csv_file}")
            return True
        else:
            print(f"ERROR: Real employee data not found: {csv_file}")
            print("   Please ensure the Employee.csv file is in the backend/data/ directory")
            return False

    def main():
        """Main setup function"""
        print("Starting complete dataset setup for Talent Co-Pilot...")
        
        # Check if we're in the right directory
        if not os.path.exists("backend"):
            print("ERROR: Please run this script from the project root directory")
            return False
        
        # Check for real CSV data
        if not check_csv_file():
            return False
        
        # Install additional requirements
        if not install_requirements():
            print("WARNING: Continuing without additional requirements...")
        

        if not run_script("backend/scripts/generate_dataset_simple.py", "Generating synthetic dataset"):
            return False
        
        print("\nDataset setup completed successfully!")
        
        return True

    if __name__ == "__main__":
        success = main()
        sys.exit(0 if success else 1)
