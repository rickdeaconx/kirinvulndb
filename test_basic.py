#!/usr/bin/env python3
"""
Basic test script to verify the system works
"""

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")
    
    try:
        import fastapi
        print("✅ FastAPI imported successfully")
    except ImportError as e:
        print(f"❌ FastAPI import failed: {e}")
        return False
    
    try:
        import uvicorn
        print("✅ Uvicorn imported successfully")
    except ImportError as e:
        print(f"❌ Uvicorn import failed: {e}")
        return False
    
    try:
        import sqlalchemy
        print("✅ SQLAlchemy imported successfully")
    except ImportError as e:
        print(f"❌ SQLAlchemy import failed: {e}")
        return False
    
    try:
        import redis
        print("✅ Redis imported successfully")
    except ImportError as e:
        print(f"❌ Redis import failed: {e}")
        return False
    
    return True

def test_app_structure():
    """Test that the app structure is correct"""
    print("\nTesting app structure...")
    
    import os
    required_files = [
        'app/main.py',
        'app/core/config.py',
        'app/models/__init__.py',
        'app/api/health.py'
    ]
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")
            return False
    
    return True

def test_config():
    """Test configuration loading"""
    print("\nTesting configuration...")
    
    try:
        import sys
        sys.path.insert(0, '.')
        from app.core.config import settings
        print(f"✅ Settings loaded: {settings.PROJECT_NAME}")
        return True
    except Exception as e:
        print(f"❌ Config loading failed: {e}")
        return False

def test_basic_app():
    """Test basic app creation"""
    print("\nTesting basic app creation...")
    
    try:
        import sys
        sys.path.insert(0, '.')
        
        # Try to import the main app
        from app.main import app
        print("✅ App created successfully")
        
        # Check if app has routes
        routes = [route.path for route in app.routes]
        print(f"✅ Found {len(routes)} routes")
        
        return True
    except Exception as e:
        print(f"❌ App creation failed: {e}")
        return False

def main():
    print("🧪 Running basic system tests...\n")
    
    tests = [
        test_imports,
        test_app_structure, 
        test_config,
        test_basic_app
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print("")
    
    print(f"📊 Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! System should work.")
        print("\nTo start the API server:")
        print("python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8080")
    else:
        print("❌ Some tests failed. Please check the setup.")
        return False
    
    return True

if __name__ == "__main__":
    main()