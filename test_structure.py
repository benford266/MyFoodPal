#!/usr/bin/env python3
"""
Test script to verify the refactored FoodPal structure works correctly.
"""

import sys
import importlib

def test_imports():
    """Test that all refactored modules can be imported successfully."""
    modules_to_test = [
        'src.database.models',
        'src.database.connection', 
        'src.database.operations',
        'src.models.schemas',
        'src.services.recipe_generator',
        'src.utils.theme',
        'src.utils.session',
        'src.utils.shopping_list',
        'src.utils.pdf_export',
        'src.utils.recipe_parser',
        'src.api.endpoints',
        'src.ui.pages',
        'src.config'
    ]
    
    print("Testing module imports...")
    failed_imports = []
    
    for module in modules_to_test:
        try:
            importlib.import_module(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {e}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"\n❌ Failed to import {len(failed_imports)} modules")
        return False
    else:
        print(f"\n✅ Successfully imported all {len(modules_to_test)} modules!")
        return True

def test_key_classes():
    """Test that key classes can be instantiated."""
    print("\nTesting key classes...")
    
    try:
        from src.database.models import User, MealPlan, RecipeRating
        from src.services.recipe_generator import RecipeGenerator
        from src.utils.theme import get_theme_classes
        
        # Test theme classes
        theme = get_theme_classes()
        assert isinstance(theme, dict)
        assert 'bg_primary' in theme
        print("✅ Theme classes working")
        
        # Test recipe generator instantiation
        generator = RecipeGenerator("http://localhost:11434", "test-model")
        assert generator.ollama_url == "http://localhost:11434"
        assert generator.model == "test-model"
        print("✅ RecipeGenerator class working")
        
        print("✅ All key classes working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing classes: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing FoodPal refactored structure...\n")
    
    import_success = test_imports()
    class_success = test_key_classes()
    
    if import_success and class_success:
        print("\n🎉 All tests passed! The refactored structure is working correctly.")
        print("\n📁 New structure summary:")
        print("├── src/api/          # FastAPI endpoints")
        print("├── src/database/     # Models, connections, operations") 
        print("├── src/models/       # Pydantic schemas")
        print("├── src/services/     # Business logic")
        print("├── src/ui/           # UI pages and components")
        print("├── src/utils/        # Reusable utilities")
        print("└── src/config.py     # Configuration")
        print("\n🚀 Ready to run: python main.py")
        return True
    else:
        print("\n💥 Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)