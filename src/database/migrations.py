"""
Database migration utilities for FoodPal
Handles schema changes and data migrations safely
"""

from sqlalchemy import text, inspect
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from datetime import datetime, timezone
from typing import List, Dict, Any, Callable
import json

class DatabaseMigration:
    """Base class for database migrations"""
    
    def __init__(self, version: str, description: str):
        self.version = version
        self.description = description
        self.timestamp = datetime.now(timezone.utc)
    
    def up(self, db: Session) -> None:
        """Apply the migration"""
        raise NotImplementedError
    
    def down(self, db: Session) -> None:
        """Rollback the migration"""
        raise NotImplementedError

class MigrationManager:
    """Manages database migrations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.migrations: List[DatabaseMigration] = []
        self._ensure_migration_table()
    
    def _ensure_migration_table(self):
        """Create migrations table if it doesn't exist"""
        try:
            self.db.execute(text("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version TEXT UNIQUE NOT NULL,
                    description TEXT NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    rollback_sql TEXT
                )
            """))
            self.db.commit()
        except Exception as e:
            print(f"Error creating migration table: {e}")
            self.db.rollback()
    
    def register_migration(self, migration: DatabaseMigration):
        """Register a migration"""
        self.migrations.append(migration)
    
    def get_applied_migrations(self) -> List[str]:
        """Get list of applied migration versions"""
        try:
            result = self.db.execute(text("SELECT version FROM schema_migrations ORDER BY applied_at"))
            return [row[0] for row in result]
        except:
            return []
    
    def apply_migration(self, migration: DatabaseMigration) -> bool:
        """Apply a single migration"""
        try:
            print(f"Applying migration {migration.version}: {migration.description}")
            
            # Apply the migration
            migration.up(self.db)
            
            # Record the migration
            self.db.execute(text("""
                INSERT INTO schema_migrations (version, description) 
                VALUES (:version, :description)
            """), {
                'version': migration.version,
                'description': migration.description
            })
            
            self.db.commit()
            print(f"Successfully applied migration {migration.version}")
            return True
            
        except Exception as e:
            print(f"Failed to apply migration {migration.version}: {e}")
            self.db.rollback()
            return False
    
    def rollback_migration(self, version: str) -> bool:
        """Rollback a specific migration"""
        try:
            migration = next((m for m in self.migrations if m.version == version), None)
            if not migration:
                print(f"Migration {version} not found")
                return False
            
            print(f"Rolling back migration {version}")
            
            # Apply rollback
            migration.down(self.db)
            
            # Remove from migrations table
            self.db.execute(text("DELETE FROM schema_migrations WHERE version = :version"), {'version': version})
            
            self.db.commit()
            print(f"Successfully rolled back migration {version}")
            return True
            
        except Exception as e:
            print(f"Failed to rollback migration {version}: {e}")
            self.db.rollback()
            return False
    
    def migrate(self) -> None:
        """Apply all pending migrations"""
        applied_migrations = set(self.get_applied_migrations())
        pending_migrations = [m for m in self.migrations if m.version not in applied_migrations]
        
        if not pending_migrations:
            print("No pending migrations")
            return
        
        # Sort migrations by version
        pending_migrations.sort(key=lambda x: x.version)
        
        print(f"Found {len(pending_migrations)} pending migrations")
        
        for migration in pending_migrations:
            success = self.apply_migration(migration)
            if not success:
                print("Migration failed, stopping")
                break

# Specific migrations for FoodPal

class AddMustUseIngredientsColumn(DatabaseMigration):
    """Add must_use_ingredients column to users table"""
    
    def __init__(self):
        super().__init__("001_add_must_use_ingredients", "Add must_use_ingredients column to users table")
    
    def up(self, db: Session):
        # Check if column already exists
        inspector = inspect(db.bind)
        columns = [col['name'] for col in inspector.get_columns('users')]
        
        if 'must_use_ingredients' not in columns:
            db.execute(text("ALTER TABLE users ADD COLUMN must_use_ingredients TEXT DEFAULT ''"))
    
    def down(self, db: Session):
        # SQLite doesn't support DROP COLUMN, so we'd need to recreate table
        # For now, just mark as rolled back
        pass

class AddMustUseIngredientsToMealPlans(DatabaseMigration):
    """Add must_use_ingredients_snapshot to meal_plans table"""
    
    def __init__(self):
        super().__init__("002_add_must_use_to_meal_plans", "Add must_use_ingredients_snapshot to meal_plans")
    
    def up(self, db: Session):
        inspector = inspect(db.bind)
        columns = [col['name'] for col in inspector.get_columns('meal_plans')]
        
        if 'must_use_ingredients_snapshot' not in columns:
            db.execute(text("ALTER TABLE meal_plans ADD COLUMN must_use_ingredients_snapshot TEXT DEFAULT ''"))
    
    def down(self, db: Session):
        pass

class AddPerformanceIndexes(DatabaseMigration):
    """Add performance indexes to tables"""
    
    def __init__(self):
        super().__init__("003_add_performance_indexes", "Add performance indexes for better query speed")
    
    def up(self, db: Session):
        from .indexes import create_performance_indexes
        create_performance_indexes(db)
    
    def down(self, db: Session):
        # Drop indexes
        indexes_to_drop = [
            'idx_user_email', 'idx_user_created_at',
            'idx_meal_plan_user_id', 'idx_meal_plan_created_at', 'idx_meal_plan_user_created',
            'idx_recipe_rating_user_id', 'idx_recipe_rating_meal_plan_id', 'idx_recipe_rating_composite'
        ]
        
        for index_name in indexes_to_drop:
            try:
                db.execute(text(f"DROP INDEX IF EXISTS {index_name}"))
            except:
                pass

class AddFullTextSearch(DatabaseMigration):
    """Add full-text search capabilities"""
    
    def __init__(self):
        super().__init__("004_add_fulltext_search", "Add FTS5 virtual tables for search functionality")
    
    def up(self, db: Session):
        from .indexes import create_search_indexes
        create_search_indexes(db)
    
    def down(self, db: Session):
        try:
            db.execute(text("DROP TABLE IF EXISTS meal_plan_fts"))
            db.execute(text("DROP TRIGGER IF EXISTS meal_plan_fts_insert"))
            db.execute(text("DROP TRIGGER IF EXISTS meal_plan_fts_delete"))
            db.execute(text("DROP TRIGGER IF EXISTS meal_plan_fts_update"))
        except:
            pass

class CreateMaterializedViews(DatabaseMigration):
    """Create materialized views for analytics"""
    
    def __init__(self):
        super().__init__("005_create_materialized_views", "Create views for user stats and recipe popularity")
    
    def up(self, db: Session):
        from .indexes import create_materialized_views
        create_materialized_views(db)
    
    def down(self, db: Session):
        views_to_drop = ['user_stats', 'recipe_popularity', 'monthly_generation_stats']
        
        for view_name in views_to_drop:
            try:
                db.execute(text(f"DROP VIEW IF EXISTS {view_name}"))
            except:
                pass

class OptimizeDatabaseSettings(DatabaseMigration):
    """Optimize database settings for performance"""
    
    def __init__(self):
        super().__init__("006_optimize_database_settings", "Apply performance optimizations to database")
    
    def up(self, db: Session):
        from .indexes import optimize_database
        optimize_database(db)
    
    def down(self, db: Session):
        # Reset to default settings
        try:
            db.execute(text("PRAGMA cache_size = 2000"))
            db.execute(text("PRAGMA temp_store = DEFAULT"))
            db.execute(text("PRAGMA mmap_size = 0"))
            db.execute(text("PRAGMA journal_mode = DELETE"))
            db.execute(text("PRAGMA synchronous = FULL"))
        except:
            pass

def run_migrations(db: Session) -> None:
    """Run all available migrations"""
    print("Starting database migrations...")
    
    manager = MigrationManager(db)
    
    # Register all migrations
    migrations = [
        AddMustUseIngredientsColumn(),
        AddMustUseIngredientsToMealPlans(),
        AddPerformanceIndexes(),
        AddFullTextSearch(),
        CreateMaterializedViews(),
        OptimizeDatabaseSettings()
    ]
    
    for migration in migrations:
        manager.register_migration(migration)
    
    # Apply migrations
    manager.migrate()
    
    print("Database migrations completed!")

def create_backup(db: Session, backup_path: str) -> bool:
    """Create a backup of the database before migrations"""
    try:
        # For SQLite, we can use the backup API or simple file copy
        db.execute(text(f"VACUUM INTO '{backup_path}'"))
        db.commit()
        print(f"Database backup created: {backup_path}")
        return True
    except Exception as e:
        print(f"Failed to create backup: {e}")
        return False

def verify_database_integrity(db: Session) -> bool:
    """Verify database integrity after migrations"""
    try:
        # Run SQLite integrity check
        result = db.execute(text("PRAGMA integrity_check")).fetchone()
        
        if result and result[0] == "ok":
            print("Database integrity check passed")
            return True
        else:
            print(f"Database integrity check failed: {result}")
            return False
            
    except Exception as e:
        print(f"Error during integrity check: {e}")
        return False