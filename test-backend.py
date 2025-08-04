#!/usr/bin/env python3
"""
Simple test script to verify backend configuration
"""
import os
import sys
sys.path.append('./backend')

def test_config():
    """Test configuration loading"""
    print("🔧 Testing configuration...")
    
    try:
        from backend.app.config import settings
        print(f"✅ Database URL: {settings.DATABASE_URL}")
        print(f"✅ LM Studio URL: {settings.LM_STUDIO_BASE_URL}")
        print(f"✅ Model: {settings.LM_STUDIO_MODEL}")
        return True
    except Exception as e:
        print(f"❌ Config error: {e}")
        return False

def test_database():
    """Test database connection"""
    print("🗄️ Testing database...")
    
    try:
        from backend.app.database.connection import create_tables
        create_tables()
        print("✅ Database tables created successfully")
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

if __name__ == "__main__":
    print("🍽️ FoodPal Backend Test")
    print("=" * 30)
    
    config_ok = test_config()
    db_ok = test_database()
    
    if config_ok and db_ok:
        print("\n✅ Backend test passed!")
        sys.exit(0)
    else:
        print("\n❌ Backend test failed!")
        sys.exit(1)