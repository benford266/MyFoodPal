"""
Database indexes for improved query performance
Run this to add indexes to existing database tables
"""

from sqlalchemy import Index, text
from sqlalchemy.orm import Session
from .models import User, MealPlan, RecipeRating, RecipeHistory, GenerationTask

def create_performance_indexes(db: Session):
    """Create database indexes for better performance"""
    
    # Index definitions
    indexes = [
        # User table indexes
        Index('idx_user_email', User.email),  # For login queries
        Index('idx_user_created_at', User.created_at),  # For user analytics
        
        # MealPlan table indexes
        Index('idx_meal_plan_user_id', MealPlan.user_id),  # Most important - for user's meal plans
        Index('idx_meal_plan_created_at', MealPlan.created_at),  # For ordering by date
        Index('idx_meal_plan_user_created', MealPlan.user_id, MealPlan.created_at),  # Composite for common query
        Index('idx_meal_plan_name', MealPlan.name),  # For searching by name
        
        # RecipeRating table indexes  
        Index('idx_recipe_rating_user_id', RecipeRating.user_id),  # For user's ratings
        Index('idx_recipe_rating_meal_plan_id', RecipeRating.meal_plan_id),  # For meal plan ratings
        Index('idx_recipe_rating_composite', RecipeRating.user_id, RecipeRating.meal_plan_id, RecipeRating.recipe_index),  # For specific rating lookups
        Index('idx_recipe_rating_title', RecipeRating.recipe_title),  # For recipe analytics
        Index('idx_recipe_rating_rating', RecipeRating.rating),  # For filtering by rating
        
        # RecipeHistory table indexes
        Index('idx_recipe_history_user_id', RecipeHistory.user_id),  # For user's history
        Index('idx_recipe_history_created_at', RecipeHistory.created_at),  # For cleanup operations
        
        # GenerationTask table indexes
        Index('idx_generation_task_user_id', GenerationTask.user_id),  # For user's tasks
        Index('idx_generation_task_status', GenerationTask.status),  # For finding active tasks
        Index('idx_generation_task_created_at', GenerationTask.created_at),  # For cleanup
        Index('idx_generation_task_user_status', GenerationTask.user_id, GenerationTask.status),  # Composite for common queries
    ]
    
    # Create indexes
    for index in indexes:
        try:
            # Check if index already exists
            index_name = index.name
            result = db.execute(
                text(f"""
                SELECT COUNT(*) 
                FROM sqlite_master 
                WHERE type='index' AND name='{index_name}'
                """)
            ).scalar()
            
            if result == 0:
                index.create(db.bind)
                print(f"Created index: {index_name}")
            else:
                print(f"Index already exists: {index_name}")
                
        except Exception as e:
            print(f"Error creating index {index.name}: {e}")
            continue
    
    db.commit()
    print("Database indexes created successfully!")

def create_search_indexes(db: Session):
    """Create full-text search indexes for better search performance"""
    
    try:
        # Create FTS virtual table for meal plan search
        db.execute(text("""
            CREATE VIRTUAL TABLE IF NOT EXISTS meal_plan_fts USING fts5(
                meal_plan_id, 
                name, 
                liked_foods_snapshot, 
                disliked_foods_snapshot, 
                must_use_ingredients_snapshot,
                content='meal_plans',
                content_rowid='id'
            )
        """))
        
        # Populate FTS table with existing data
        db.execute(text("""
            INSERT OR REPLACE INTO meal_plan_fts(meal_plan_id, name, liked_foods_snapshot, disliked_foods_snapshot, must_use_ingredients_snapshot)
            SELECT id, name, liked_foods_snapshot, disliked_foods_snapshot, must_use_ingredients_snapshot 
            FROM meal_plans
        """))
        
        # Create triggers to keep FTS in sync
        db.execute(text("""
            CREATE TRIGGER IF NOT EXISTS meal_plan_fts_insert AFTER INSERT ON meal_plans 
            BEGIN
                INSERT INTO meal_plan_fts(meal_plan_id, name, liked_foods_snapshot, disliked_foods_snapshot, must_use_ingredients_snapshot)
                VALUES (NEW.id, NEW.name, NEW.liked_foods_snapshot, NEW.disliked_foods_snapshot, NEW.must_use_ingredients_snapshot);
            END
        """))
        
        db.execute(text("""
            CREATE TRIGGER IF NOT EXISTS meal_plan_fts_delete AFTER DELETE ON meal_plans 
            BEGIN
                DELETE FROM meal_plan_fts WHERE meal_plan_id = OLD.id;
            END
        """))
        
        db.execute(text("""
            CREATE TRIGGER IF NOT EXISTS meal_plan_fts_update AFTER UPDATE ON meal_plans 
            BEGIN
                UPDATE meal_plan_fts 
                SET name = NEW.name, 
                    liked_foods_snapshot = NEW.liked_foods_snapshot,
                    disliked_foods_snapshot = NEW.disliked_foods_snapshot,
                    must_use_ingredients_snapshot = NEW.must_use_ingredients_snapshot
                WHERE meal_plan_id = NEW.id;
            END
        """))
        
        db.commit()
        print("Full-text search indexes created successfully!")
        
    except Exception as e:
        print(f"Error creating search indexes: {e}")
        db.rollback()

def optimize_database(db: Session):
    """Run database optimization commands"""
    
    try:
        # Analyze database to update statistics
        db.execute(text("ANALYZE"))
        
        # Vacuum to reclaim space and defragment
        db.execute(text("VACUUM"))
        
        # Enable query optimization
        db.execute(text("PRAGMA optimize"))
        
        # Set performance pragmas
        db.execute(text("PRAGMA cache_size = 10000"))  # Increase cache size
        db.execute(text("PRAGMA temp_store = MEMORY"))  # Store temp tables in memory
        db.execute(text("PRAGMA mmap_size = 268435456"))  # Enable memory mapping (256MB)
        db.execute(text("PRAGMA journal_mode = WAL"))  # Enable WAL mode for better concurrency
        db.execute(text("PRAGMA synchronous = NORMAL"))  # Balance between safety and performance
        
        db.commit()
        print("Database optimization completed!")
        
    except Exception as e:
        print(f"Error during database optimization: {e}")

def create_materialized_views(db: Session):
    """Create materialized views for common aggregations"""
    
    try:
        # User statistics view
        db.execute(text("""
            CREATE VIEW IF NOT EXISTS user_stats AS
            SELECT 
                u.id as user_id,
                u.name,
                u.email,
                u.created_at as user_created_at,
                COUNT(DISTINCT mp.id) as total_meal_plans,
                SUM(mp.recipe_count) as total_recipes_generated,
                AVG(mp.recipe_count) as avg_recipes_per_plan,
                AVG(mp.serving_size) as avg_serving_size,
                COUNT(DISTINCT rr.id) as total_ratings,
                AVG(rr.rating) as avg_rating_given,
                MAX(mp.created_at) as last_meal_plan_date
            FROM users u
            LEFT JOIN meal_plans mp ON u.id = mp.user_id
            LEFT JOIN recipe_ratings rr ON u.id = rr.user_id
            GROUP BY u.id, u.name, u.email, u.created_at
        """))
        
        # Recipe popularity view
        db.execute(text("""
            CREATE VIEW IF NOT EXISTS recipe_popularity AS
            SELECT 
                rr.recipe_title,
                COUNT(*) as times_rated,
                AVG(rr.rating) as avg_rating,
                MIN(rr.rating) as min_rating,
                MAX(rr.rating) as max_rating,
                COUNT(CASE WHEN rr.rating >= 4 THEN 1 END) as highly_rated_count,
                MAX(rr.created_at) as last_rated_date
            FROM recipe_ratings rr
            GROUP BY rr.recipe_title
            HAVING COUNT(*) >= 2  -- Only include recipes rated by multiple users
            ORDER BY avg_rating DESC, times_rated DESC
        """))
        
        # Monthly generation stats view
        db.execute(text("""
            CREATE VIEW IF NOT EXISTS monthly_generation_stats AS
            SELECT 
                strftime('%Y-%m', mp.created_at) as year_month,
                COUNT(*) as meal_plans_created,
                SUM(mp.recipe_count) as total_recipes,
                COUNT(DISTINCT mp.user_id) as active_users,
                AVG(mp.recipe_count) as avg_recipes_per_plan,
                AVG(mp.serving_size) as avg_serving_size
            FROM meal_plans mp
            GROUP BY strftime('%Y-%m', mp.created_at)
            ORDER BY year_month DESC
        """))
        
        db.commit()
        print("Materialized views created successfully!")
        
    except Exception as e:
        print(f"Error creating materialized views: {e}")
        db.rollback()

def setup_database_performance(db: Session):
    """Setup all performance optimizations"""
    print("Setting up database performance optimizations...")
    
    # Create indexes
    create_performance_indexes(db)
    
    # Create search indexes
    create_search_indexes(db)
    
    # Create materialized views
    create_materialized_views(db)
    
    # Optimize database
    optimize_database(db)
    
    print("Database performance optimization complete!")