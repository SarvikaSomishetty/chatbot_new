#!/usr/bin/env python3
"""
Setup script for the Customer Support Chatbot
This script helps configure the environment and dependencies
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")

def check_dependencies():
    """Check if required system dependencies are installed"""
    dependencies = {
        'redis-server': 'Redis server',
        'mongod': 'MongoDB server',
        'psql': 'PostgreSQL client'
    }
    
    missing = []
    for cmd, name in dependencies.items():
        if not shutil.which(cmd):
            missing.append(name)
    
    if missing:
        print("❌ Missing system dependencies:")
        for dep in missing:
            print(f"   - {dep}")
        print("\nPlease install the missing dependencies and try again.")
        return False
    
    print("✅ All system dependencies found")
    return True

def setup_environment():
    """Set up environment variables"""
    env_file = Path("backend/.env")
    env_example = Path("backend/.env.example")
    
    if not env_file.exists() and env_example.exists():
        shutil.copy(env_example, env_file)
        print("✅ Created .env file from template")
        print("⚠️  Please edit backend/.env and add your Gemini API key")
    elif env_file.exists():
        print("✅ .env file already exists")
    else:
        print("❌ No .env template found")

def install_python_dependencies():
    """Install Python dependencies"""
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "backend/requirements.txt"], 
                      check=True, cwd=".")
        print("✅ Python dependencies installed")
    except subprocess.CalledProcessError:
        print("❌ Failed to install Python dependencies")
        return False
    return True

def install_node_dependencies():
    """Install Node.js dependencies"""
    try:
        subprocess.run(["npm", "install"], check=True, cwd=".")
        print("✅ Node.js dependencies installed")
    except subprocess.CalledProcessError:
        print("❌ Failed to install Node.js dependencies")
        return False
    return True

def main():
    """Main setup function"""
    print("🚀 Setting up Customer Support Chatbot...")
    print("=" * 50)
    
    # Check Python version
    check_python_version()
    
    # Check system dependencies
    if not check_dependencies():
        print("\n❌ Setup failed due to missing dependencies")
        sys.exit(1)
    
    # Set up environment
    setup_environment()
    
    # Install dependencies
    print("\n📦 Installing dependencies...")
    python_ok = install_python_dependencies()
    node_ok = install_node_dependencies()
    
    if not python_ok or not node_ok:
        print("\n❌ Setup failed during dependency installation")
        sys.exit(1)
    
    print("\n✅ Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Edit backend/.env and add your Gemini API key")
    print("2. Start Redis: redis-server")
    print("3. Start MongoDB: mongod")
    print("4. Start PostgreSQL (if not running)")
    print("5. Run the backend: cd backend && python main.py")
    print("6. Run the frontend: npm run dev")
    print("\n🔗 Get your Gemini API key from: https://makersuite.google.com/app/apikey")

if __name__ == "__main__":
    main()
