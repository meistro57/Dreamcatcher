#!/usr/bin/env python3
"""
Test runner script for Dreamcatcher backend.
"""
import subprocess
import sys
import os

def run_tests():
    """Run the test suite."""
    # Change to backend directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Run pytest with coverage
    cmd = [
        sys.executable, 
        "-m", 
        "pytest",
        "tests/",
        "-v",
        "--tb=short",
        "--color=yes"
    ]
    
    print("Running Dreamcatcher backend tests...")
    print("=" * 50)
    
    try:
        result = subprocess.run(cmd, check=True)
        print("\n" + "=" * 50)
        print("✅ All tests passed!")
        return 0
    except subprocess.CalledProcessError as e:
        print("\n" + "=" * 50)
        print(f"❌ Tests failed with exit code {e.returncode}")
        return e.returncode
    except KeyboardInterrupt:
        print("\n" + "=" * 50)
        print("⏹️  Tests interrupted by user")
        return 1

if __name__ == "__main__":
    sys.exit(run_tests())