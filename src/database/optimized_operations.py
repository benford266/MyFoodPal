"""
Optimized database operations for better performance
"""

from sqlalchemy.orm import Session, selectinload, joinedload
from sqlalchemy import text, func, and_, or_, desc, asc
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging

from .models import User, MealPlan, RecipeRating, RecipeHistory, GenerationTask
from ..utils.logging_config import PerformanceLogger, get_logger

logger = get_logger('database')

class OptimizedQueries:
    """Optimized database query operations"""
    
    @staticmethod
    def get_user_meal_plans_optimized(
        db: Session, 
        user_id: int, 
        limit: int = 10, 
        offset: int = 0,
        include_ratings: bool = False
    ) -> Tuple[List[MealPlan], int]:
        """
        Get user's meal plans with optimized loading and total count
        """
        with PerformanceLogger(f"get_user_meal_plans_optimized(user_id={user_id}, limit={limit})"):
            # Build base query
            query = db.query(MealPlan).filter(MealPlan.user_id == user_id)
            
            # Add eager loading if ratings are needed
            if include_ratings:
                query = query.options(selectinload(MealPlan.recipe_ratings))
            
            # Get total count (using the same filter conditions)
            total_count = query.count()
            
            # Apply ordering, limit, and offset
            meal_plans = (
                query
                .order_by(desc(MealPlan.created_at))
                .limit(limit)
                .offset(offset)
                .all()
            )
            
            logger.info(f"Retrieved {len(meal_plans)} meal plans for user {user_id}")
            return meal_plans, total_count
    
    @staticmethod
    def get_meal_plan_with_ratings_optimized(
        db: Session, 
        meal_plan_id: int, 
        user_id: int
    ) -> Optional[MealPlan]:
        """
        Get single meal plan with all related data optimized
        """
        with PerformanceLogger(f"get_meal_plan_with_ratings_optimized(plan_id={meal_plan_id})"):
            meal_plan = (
                db.query(MealPlan)
                .options(selectinload(MealPlan.recipe_ratings))
                .filter(
                    and_(
                        MealPlan.id == meal_plan_id,
                        MealPlan.user_id == user_id
                    )
                )
                .first()
            )
            
            if meal_plan:
                logger.info(f"Retrieved meal plan {meal_plan_id} with {len(meal_plan.recipe_ratings)} ratings")
            else:
                logger.warning(f"Meal plan {meal_plan_id} not found for user {user_id}")
                
            return meal_plan
    
    @staticmethod
    def get_user_recipe_ratings_paginated(
        db: Session, 
        user_id: int, 
        limit: int = 20, 
        offset: int = 0,
        min_rating: Optional[int] = None
    ) -> Tuple[List[RecipeRating], int]:
        """
        Get user's recipe ratings with pagination and filtering
        """
        with PerformanceLogger(f"get_user_recipe_ratings_paginated(user_id={user_id})"):
            # Build query with optional rating filter
            query = db.query(RecipeRating).filter(RecipeRating.user_id == user_id)
            
            if min_rating is not None:
                query = query.filter(RecipeRating.rating >= min_rating)
            
            # Get total count
            total_count = query.count()
            
            # Apply ordering and pagination
            ratings = (
                query
                .order_by(desc(RecipeRating.updated_at))
                .limit(limit)
                .offset(offset)
                .all()
            )
            
            logger.info(f"Retrieved {len(ratings)} ratings for user {user_id}")
            return ratings, total_count
    
    @staticmethod
    def get_popular_recipes(
        db: Session, 
        limit: int = 10,
        min_ratings: int = 3,
        min_avg_rating: float = 3.5
    ) -> List[Dict[str, Any]]:
        """
        Get popular recipes based on ratings using optimized query
        """
        with PerformanceLogger(f"get_popular_recipes(limit={limit})"):
            # Use the materialized view if available, fallback to direct query
            try:
                results = db.execute(text("""
                    SELECT recipe_title, times_rated, avg_rating, highly_rated_count, last_rated_date
                    FROM recipe_popularity
                    WHERE times_rated >= :min_ratings AND avg_rating >= :min_avg_rating
                    LIMIT :limit
                """), {
                    'min_ratings': min_ratings,
                    'min_avg_rating': min_avg_rating,
                    'limit': limit
                }).fetchall()
                
                popular_recipes = [
                    {
                        'recipe_title': row.recipe_title,
                        'times_rated': row.times_rated,
                        'avg_rating': float(row.avg_rating),
                        'highly_rated_count': row.highly_rated_count,
                        'last_rated_date': row.last_rated_date
                    }
                    for row in results
                ]
                
            except Exception as e:
                logger.warning(f"Error using recipe_popularity view: {e}, falling back to direct query")
                # Fallback to direct query
                popular_recipes = (
                    db.query(
                        RecipeRating.recipe_title,
                        func.count().label('times_rated'),
                        func.avg(RecipeRating.rating).label('avg_rating'),
                        func.sum(func.case([(RecipeRating.rating >= 4, 1)], else_=0)).label('highly_rated_count'),
                        func.max(RecipeRating.created_at).label('last_rated_date')
                    )
                    .group_by(RecipeRating.recipe_title)
                    .having(and_(
                        func.count() >= min_ratings,
                        func.avg(RecipeRating.rating) >= min_avg_rating
                    ))
                    .order_by(desc('avg_rating'), desc('times_rated'))
                    .limit(limit)
                    .all()
                )
                
                popular_recipes = [
                    {
                        'recipe_title': recipe.recipe_title,
                        'times_rated': recipe.times_rated,
                        'avg_rating': float(recipe.avg_rating),
                        'highly_rated_count': recipe.highly_rated_count,
                        'last_rated_date': recipe.last_rated_date
                    }
                    for recipe in popular_recipes
                ]
            
            logger.info(f"Retrieved {len(popular_recipes)} popular recipes")
            return popular_recipes
    
    @staticmethod
    def search_meal_plans(
        db: Session, 
        user_id: int, 
        search_query: str, 
        limit: int = 10
    ) -> List[MealPlan]:
        """
        Search meal plans using full-text search
        """
        with PerformanceLogger(f"search_meal_plans(user_id={user_id}, query='{search_query}')"):
            try:
                # Use FTS if available
                results = db.execute(text("""
                    SELECT mp.* 
                    FROM meal_plans mp
                    JOIN meal_plan_fts fts ON mp.id = fts.meal_plan_id
                    WHERE mp.user_id = :user_id AND meal_plan_fts MATCH :query
                    ORDER BY bm25(meal_plan_fts) 
                    LIMIT :limit
                """), {
                    'user_id': user_id,
                    'query': search_query,
                    'limit': limit
                }).fetchall()
                
                # Convert results to MealPlan objects
                meal_plan_ids = [row.id for row in results]
                meal_plans = (
                    db.query(MealPlan)
                    .filter(MealPlan.id.in_(meal_plan_ids))
                    .all()
                )
                
            except Exception as e:
                logger.warning(f"FTS search failed: {e}, falling back to LIKE search")
                # Fallback to LIKE search
                search_pattern = f"%{search_query}%"
                meal_plans = (
                    db.query(MealPlan)
                    .filter(
                        and_(
                            MealPlan.user_id == user_id,
                            or_(
                                MealPlan.name.like(search_pattern),
                                MealPlan.liked_foods_snapshot.like(search_pattern),
                                MealPlan.disliked_foods_snapshot.like(search_pattern),
                                MealPlan.must_use_ingredients_snapshot.like(search_pattern)
                            )
                        )
                    )
                    .order_by(desc(MealPlan.created_at))
                    .limit(limit)
                    .all()
                )
            
            logger.info(f"Found {len(meal_plans)} meal plans matching '{search_query}'")
            return meal_plans
    
    @staticmethod
    def get_user_statistics(db: Session, user_id: int) -> Dict[str, Any]:
        """
        Get comprehensive user statistics using optimized queries
        """
        with PerformanceLogger(f"get_user_statistics(user_id={user_id})"):
            try:
                # Use materialized view if available
                result = db.execute(text("""
                    SELECT * FROM user_stats WHERE user_id = :user_id
                """), {'user_id': user_id}).fetchone()
                
                if result:
                    stats = dict(result._mapping)
                else:
                    # Fallback to direct queries
                    stats = OptimizedQueries._calculate_user_stats_direct(db, user_id)
                
            except Exception as e:
                logger.warning(f"Error using user_stats view: {e}, calculating directly")
                stats = OptimizedQueries._calculate_user_stats_direct(db, user_id)
            
            logger.info(f"Retrieved statistics for user {user_id}")
            return stats
    
    @staticmethod
    def _calculate_user_stats_direct(db: Session, user_id: int) -> Dict[str, Any]:
        """Calculate user statistics using direct queries"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {}
        
        # Meal plan stats
        meal_plan_stats = (
            db.query(
                func.count(MealPlan.id).label('total_meal_plans'),
                func.sum(MealPlan.recipe_count).label('total_recipes_generated'),
                func.avg(MealPlan.recipe_count).label('avg_recipes_per_plan'),
                func.avg(MealPlan.serving_size).label('avg_serving_size'),
                func.max(MealPlan.created_at).label('last_meal_plan_date')
            )
            .filter(MealPlan.user_id == user_id)
            .first()
        )
        
        # Rating stats
        rating_stats = (
            db.query(
                func.count(RecipeRating.id).label('total_ratings'),
                func.avg(RecipeRating.rating).label('avg_rating_given')
            )
            .filter(RecipeRating.user_id == user_id)
            .first()
        )
        
        return {
            'user_id': user.id,
            'name': user.name,
            'email': user.email,
            'user_created_at': user.created_at,
            'total_meal_plans': meal_plan_stats.total_meal_plans or 0,
            'total_recipes_generated': meal_plan_stats.total_recipes_generated or 0,
            'avg_recipes_per_plan': float(meal_plan_stats.avg_recipes_per_plan or 0),
            'avg_serving_size': float(meal_plan_stats.avg_serving_size or 0),
            'total_ratings': rating_stats.total_ratings or 0,
            'avg_rating_given': float(rating_stats.avg_rating_given or 0),
            'last_meal_plan_date': meal_plan_stats.last_meal_plan_date
        }
    
    @staticmethod
    def cleanup_old_data(db: Session, days_to_keep: int = 90) -> Dict[str, int]:
        """
        Clean up old data to maintain performance
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        cleanup_stats = {}
        
        with PerformanceLogger("cleanup_old_data"):
            # Clean up old generation tasks (completed/failed ones older than cutoff)
            deleted_tasks = (
                db.query(GenerationTask)
                .filter(
                    and_(
                        GenerationTask.completed_at < cutoff_date,
                        GenerationTask.status.in_(['completed', 'failed'])
                    )
                )
                .count()
            )
            
            if deleted_tasks > 0:
                db.query(GenerationTask).filter(
                    and_(
                        GenerationTask.completed_at < cutoff_date,
                        GenerationTask.status.in_(['completed', 'failed'])
                    )
                ).delete()
                cleanup_stats['deleted_tasks'] = deleted_tasks
            
            # Clean up old recipe history (keep only recent entries per user)
            users_with_history = db.query(RecipeHistory.user_id).distinct().all()
            deleted_history = 0
            
            for (user_id,) in users_with_history:
                # Keep only the 30 most recent entries per user
                keep_ids = (
                    db.query(RecipeHistory.id)
                    .filter(RecipeHistory.user_id == user_id)
                    .order_by(desc(RecipeHistory.created_at))
                    .limit(30)
                    .subquery()
                )
                
                deleted = (
                    db.query(RecipeHistory)
                    .filter(
                        and_(
                            RecipeHistory.user_id == user_id,
                            ~RecipeHistory.id.in_(keep_ids)
                        )
                    )
                    .count()
                )
                
                if deleted > 0:
                    db.query(RecipeHistory).filter(
                        and_(
                            RecipeHistory.user_id == user_id,
                            ~RecipeHistory.id.in_(keep_ids)
                        )
                    ).delete()
                    deleted_history += deleted
            
            if deleted_history > 0:
                cleanup_stats['deleted_history'] = deleted_history
            
            # Commit all changes
            db.commit()
            
            # Run optimization after cleanup
            db.execute(text("ANALYZE"))
            db.execute(text("PRAGMA optimize"))
            
            logger.info(f"Cleanup completed: {cleanup_stats}")
            return cleanup_stats
    
    @staticmethod
    def get_database_health(db: Session) -> Dict[str, Any]:
        """
        Get database health and performance metrics
        """
        with PerformanceLogger("get_database_health"):
            health_stats = {}
            
            # Table row counts
            tables = [
                ('users', User),
                ('meal_plans', MealPlan),
                ('recipe_ratings', RecipeRating),
                ('recipe_history', RecipeHistory),
                ('generation_tasks', GenerationTask)
            ]
            
            for table_name, model_class in tables:
                count = db.query(model_class).count()
                health_stats[f"{table_name}_count"] = count
            
            # Database size information
            try:
                size_result = db.execute(text("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")).fetchone()
                health_stats['database_size_bytes'] = size_result[0] if size_result else 0
                
                # WAL file size
                wal_result = db.execute(text("PRAGMA wal_checkpoint(PASSIVE)")).fetchone()
                health_stats['wal_mode_active'] = True if wal_result else False
                
            except Exception as e:
                logger.warning(f"Error getting database size info: {e}")
            
            # Recent activity
            try:
                recent_meal_plans = (
                    db.query(func.count(MealPlan.id))
                    .filter(MealPlan.created_at >= datetime.now() - timedelta(days=7))
                    .scalar()
                )
                health_stats['meal_plans_last_7_days'] = recent_meal_plans
                
                active_users = (
                    db.query(func.count(func.distinct(MealPlan.user_id)))
                    .filter(MealPlan.created_at >= datetime.now() - timedelta(days=30))
                    .scalar()
                )
                health_stats['active_users_last_30_days'] = active_users
                
            except Exception as e:
                logger.warning(f"Error calculating recent activity: {e}")
            
            logger.info("Database health check completed")
            return health_stats