#!/usr/bin/env python3
"""
Simple test script to verify the application setup
"""
import sys
import os
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test if all modules can be imported successfully"""
    print("🧪 Testing imports...")
    
    try:
        from app.core.config import settings
        print("✅ Config module imported successfully")
        
        from app.core.database import init_db
        print("✅ Database module imported successfully")
        
        from app.services.data.stock_data_service import stock_data_service
        print("✅ Stock data service imported successfully")
        
        from app.services.news.news_service import news_service
        print("✅ News service imported successfully")
        
        from app.services.ai.ai_service import ai_advisor
        print("✅ AI service imported successfully")
        
        from app.api.websockets.chat_websocket import connection_manager
        print("✅ WebSocket module imported successfully")
        
        from app.utils.logger import setup_logging
        print("✅ Logger module imported successfully")
        
        from app.utils.rate_limiter import rate_limiter
        print("✅ Rate limiter module imported successfully")
        
        print("\n🎉 All imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_config():
    """Test configuration loading"""
    print("\n🔧 Testing configuration...")
    
    try:
        from app.core.config import settings
        
        print(f"✅ App name: {settings.app_name}")
        print(f"✅ Host: {settings.host}")
        print(f"✅ Port: {settings.port}")
        print(f"✅ Debug mode: {settings.debug}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def test_database():
    """Test database initialization"""
    print("\n🗄️ Testing database...")
    
    try:
        from app.core.database import init_db
        init_db()
        print("✅ Database initialized successfully")
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Stock Market Chat - Setup Test")
    print("=" * 50)
    
    # Test imports
    imports_ok = test_imports()
    
    # Test configuration
    config_ok = test_config()
    
    # Test database
    db_ok = test_database()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"   Imports: {'✅ PASS' if imports_ok else '❌ FAIL'}")
    print(f"   Config:  {'✅ PASS' if config_ok else '❌ FAIL'}")
    print(f"   Database: {'✅ PASS' if db_ok else '❌ FAIL'}")
    
    if all([imports_ok, config_ok, db_ok]):
        print("\n🎉 All tests passed! The application is ready to run.")
        print("💡 Run 'python run.py' to start the application.")
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 