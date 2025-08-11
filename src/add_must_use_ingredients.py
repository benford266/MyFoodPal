#!/usr/bin/env python3
"""
Database migration script to add must_use_ingredients column to users table
and must_use_ingredients_snapshot column to meal_plans table.
"""

import sqlite3
import os

def migrate_database():
    """Add the must_use_ingredients columns to existing database"""
    db_path = "foodpal.db"
    
    if not os.path.exists(db_path):
        print("Database file not found. New tables will be created with the correct schema.")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if must_use_ingredients column exists in users table
        cursor.execute("PRAGMA table_info(users)")
        users_columns = [column[1] for column in cursor.fetchall()]
        
        if 'must_use_ingredients' not in users_columns:
            print("Adding must_use_ingredients column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN must_use_ingredients TEXT DEFAULT ''")
            print("✅ Added must_use_ingredients to users table")
        else:
            print("✅ must_use_ingredients column already exists in users table")
        
        # Check if must_use_ingredients_snapshot column exists in meal_plans table
        cursor.execute("PRAGMA table_info(meal_plans)")
        meal_plans_columns = [column[1] for column in cursor.fetchall()]
        
        if 'must_use_ingredients_snapshot' not in meal_plans_columns:
            print("Adding must_use_ingredients_snapshot column to meal_plans table...")
            cursor.execute("ALTER TABLE meal_plans ADD COLUMN must_use_ingredients_snapshot TEXT DEFAULT ''")
            print("✅ Added must_use_ingredients_snapshot to meal_plans table")
        else:
            print("✅ must_use_ingredients_snapshot column already exists in meal_plans table")
        
        conn.commit()
        conn.close()
        
        print("\n🎉 Database migration completed successfully!")
        print("You can now use the 'Must Use (Expiring Soon)' feature in FoodPal.")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("🔄 Starting database migration for must-use ingredients feature...")
    migrate_database()