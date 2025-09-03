#!/usr/bin/env python3
"""
MongoDB Setup Script for MEDIMORPH
This script helps set up MongoDB and test the connection
"""

import subprocess
import sys
import time
import os
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, ConnectionFailure

def check_mongodb_installed():
    """Check if MongoDB is installed"""
    try:
        result = subprocess.run(['mongod', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ MongoDB is installed")
            print(f"   Version info: {result.stdout.split()[2] if len(result.stdout.split()) > 2 else 'Unknown'}")
            return True
        else:
            print("❌ MongoDB is not installed or not in PATH")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        print("❌ MongoDB is not installed or not accessible")
        return False

def check_mongodb_running():
    """Check if MongoDB service is running"""
    try:
        client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=3000)
        client.admin.command('ping')
        client.close()
        print("✅ MongoDB service is running")
        return True
    except (ServerSelectionTimeoutError, ConnectionFailure):
        print("❌ MongoDB service is not running")
        return False
    except Exception as e:
        print(f"❌ Error checking MongoDB service: {e}")
        return False

def start_mongodb_service():
    """Attempt to start MongoDB service"""
    print("🔄 Attempting to start MongoDB service...")
    
    # Try different methods to start MongoDB
    start_commands = [
        ['net', 'start', 'MongoDB'],  # Windows service
        ['sudo', 'systemctl', 'start', 'mongod'],  # Linux systemd
        ['sudo', 'service', 'mongod', 'start'],  # Linux service
        ['brew', 'services', 'start', 'mongodb-community'],  # macOS Homebrew
    ]
    
    for cmd in start_commands:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print(f"✅ Started MongoDB using: {' '.join(cmd)}")
                time.sleep(3)  # Wait for service to start
                return check_mongodb_running()
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            continue
    
    print("⚠️ Could not start MongoDB service automatically")
    print("   Please start MongoDB manually:")
    print("   - Windows: net start MongoDB")
    print("   - Linux: sudo systemctl start mongod")
    print("   - macOS: brew services start mongodb-community")
    return False

def test_mongodb_connection():
    """Test MongoDB connection and basic operations"""
    try:
        print("🔍 Testing MongoDB connection...")
        
        client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
        
        # Test connection
        client.admin.command('ping')
        print("✅ MongoDB connection successful")
        
        # List databases
        db_list = client.list_database_names()
        print(f"📊 Available databases: {db_list}")
        
        # Test database operations
        db = client['medimorph_test']
        collection = db['test_collection']
        
        # Insert test document
        test_doc = {'test': 'data', 'timestamp': time.time()}
        result = collection.insert_one(test_doc)
        print(f"✅ Test document inserted with ID: {result.inserted_id}")
        
        # Read test document
        found_doc = collection.find_one({'_id': result.inserted_id})
        if found_doc:
            print("✅ Test document retrieved successfully")
        
        # Clean up test data
        collection.delete_one({'_id': result.inserted_id})
        client.drop_database('medimorph_test')
        print("✅ Test cleanup completed")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ MongoDB connection test failed: {e}")
        return False

def install_python_dependencies():
    """Install required Python packages for MongoDB"""
    print("📦 Installing Python MongoDB dependencies...")
    
    packages = ['pymongo==4.6.0', 'flask-pymongo==2.3.0', 'mongoengine==0.27.0']
    
    for package in packages:
        try:
            print(f"   Installing {package}...")
            result = subprocess.run([sys.executable, '-m', 'pip', 'install', package], 
                                  capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                print(f"   ✅ {package} installed successfully")
            else:
                print(f"   ❌ Failed to install {package}: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            print(f"   ❌ Timeout installing {package}")
            return False
        except Exception as e:
            print(f"   ❌ Error installing {package}: {e}")
            return False
    
    print("✅ All Python MongoDB dependencies installed")
    return True

def create_mongodb_config():
    """Create MongoDB configuration file"""
    config_content = """# MongoDB Configuration for MEDIMORPH
storage:
  dbPath: ./data/db
  journal:
    enabled: true

systemLog:
  destination: file
  logAppend: true
  path: ./logs/mongod.log

net:
  port: 27017
  bindIp: 127.0.0.1

processManagement:
  fork: false
"""
    
    try:
        os.makedirs('config', exist_ok=True)
        with open('config/mongod.conf', 'w') as f:
            f.write(config_content)
        print("✅ MongoDB configuration file created: config/mongod.conf")
        return True
    except Exception as e:
        print(f"❌ Failed to create MongoDB config: {e}")
        return False

def setup_mongodb_directories():
    """Create necessary directories for MongoDB"""
    directories = ['data/db', 'logs']
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"✅ Created directory: {directory}")
        except Exception as e:
            print(f"❌ Failed to create directory {directory}: {e}")
            return False
    
    return True

def print_installation_instructions():
    """Print MongoDB installation instructions"""
    print("\n📋 MongoDB Installation Instructions:")
    print("=" * 50)
    
    print("\n🪟 Windows:")
    print("1. Download MongoDB Community Server from:")
    print("   https://www.mongodb.com/try/download/community")
    print("2. Run the installer and follow the setup wizard")
    print("3. Choose 'Complete' installation")
    print("4. Install MongoDB as a Windows Service")
    print("5. Start the service: net start MongoDB")
    
    print("\n🐧 Linux (Ubuntu/Debian):")
    print("1. Import MongoDB public key:")
    print("   wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -")
    print("2. Add MongoDB repository:")
    print("   echo 'deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/7.0 multiverse' | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list")
    print("3. Update package list:")
    print("   sudo apt-get update")
    print("4. Install MongoDB:")
    print("   sudo apt-get install -y mongodb-org")
    print("5. Start MongoDB:")
    print("   sudo systemctl start mongod")
    print("   sudo systemctl enable mongod")
    
    print("\n🍎 macOS:")
    print("1. Install Homebrew if not already installed:")
    print("   /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
    print("2. Add MongoDB tap:")
    print("   brew tap mongodb/brew")
    print("3. Install MongoDB:")
    print("   brew install mongodb-community")
    print("4. Start MongoDB:")
    print("   brew services start mongodb-community")

def main():
    """Main setup function"""
    print("🚀 MEDIMORPH MongoDB Setup")
    print("=" * 40)
    
    # Check if MongoDB is installed
    if not check_mongodb_installed():
        print_installation_instructions()
        return False
    
    # Check if MongoDB is running
    if not check_mongodb_running():
        if not start_mongodb_service():
            print("\n⚠️ Please start MongoDB manually and run this script again")
            return False
    
    # Test MongoDB connection
    if not test_mongodb_connection():
        print("❌ MongoDB connection test failed")
        return False
    
    # Install Python dependencies
    if not install_python_dependencies():
        print("❌ Failed to install Python dependencies")
        return False
    
    # Setup directories and config
    setup_mongodb_directories()
    create_mongodb_config()
    
    print("\n🎉 MongoDB Setup Complete!")
    print("=" * 40)
    print("✅ MongoDB is installed and running")
    print("✅ Python dependencies installed")
    print("✅ Configuration files created")
    print("✅ Ready to run MEDIMORPH with MongoDB")
    
    print("\n🚀 Next Steps:")
    print("1. Run the MongoDB version of MEDIMORPH:")
    print("   python app_mongodb.py")
    print("2. Access the application at: http://localhost:5000")
    print("3. All data will be stored in MongoDB!")
    
    print(f"\n📊 MongoDB Connection String: mongodb://localhost:27017/")
    print(f"🗄️ Database Name: medimorph_db")
    
    return True

if __name__ == '__main__':
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️ Setup interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed with error: {e}")
        exit(1)
