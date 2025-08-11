"""
Resource management system for FoodPal
Handles database connections, async operations, and component lifecycle
"""

from contextlib import asynccontextmanager, contextmanager
from sqlalchemy.orm import Session
from typing import Optional, Callable, Any, Dict, AsyncGenerator
import asyncio
import weakref
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@dataclass
class AsyncTask:
    """Represents an async task with cleanup"""
    task: asyncio.Task
    created_at: datetime = field(default_factory=datetime.now)
    description: str = ""
    
    def cancel(self):
        """Cancel the task safely"""
        if not self.task.done():
            self.task.cancel()

class ResourceManager:
    """Manages resources and cleanup for UI components"""
    
    def __init__(self):
        self._active_tasks: Dict[str, AsyncTask] = {}
        self._database_sessions: weakref.WeakSet = weakref.WeakSet()
        self._cleanup_handlers: Dict[str, Callable] = {}
        
    def register_async_task(self, task: asyncio.Task, task_id: str = None, description: str = "") -> str:
        """Register an async task for cleanup"""
        if task_id is None:
            task_id = f"task_{id(task)}"
        
        async_task = AsyncTask(task=task, description=description)
        self._active_tasks[task_id] = async_task
        
        # Auto-cleanup when task completes
        def cleanup_on_completion(fut):
            if task_id in self._active_tasks:
                del self._active_tasks[task_id]
        
        task.add_done_callback(cleanup_on_completion)
        
        logger.debug(f"Registered async task: {task_id} - {description}")
        return task_id
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a specific async task"""
        if task_id in self._active_tasks:
            self._active_tasks[task_id].cancel()
            del self._active_tasks[task_id]
            logger.debug(f"Cancelled task: {task_id}")
            return True
        return False
    
    def cancel_all_tasks(self):
        """Cancel all active async tasks"""
        for task_id, async_task in list(self._active_tasks.items()):
            async_task.cancel()
            logger.debug(f"Cancelled task: {task_id}")
        self._active_tasks.clear()
    
    def cleanup_old_tasks(self, max_age_minutes: int = 30):
        """Cleanup tasks older than specified age"""
        cutoff_time = datetime.now() - timedelta(minutes=max_age_minutes)
        old_tasks = []
        
        for task_id, async_task in self._active_tasks.items():
            if async_task.created_at < cutoff_time:
                old_tasks.append(task_id)
        
        for task_id in old_tasks:
            self.cancel_task(task_id)
        
        if old_tasks:
            logger.info(f"Cleaned up {len(old_tasks)} old tasks")
    
    def register_cleanup_handler(self, handler_id: str, cleanup_func: Callable):
        """Register a cleanup handler"""
        self._cleanup_handlers[handler_id] = cleanup_func
    
    def cleanup_all(self):
        """Cleanup all resources"""
        # Cancel async tasks
        self.cancel_all_tasks()
        
        # Run cleanup handlers
        for handler_id, cleanup_func in self._cleanup_handlers.items():
            try:
                cleanup_func()
                logger.debug(f"Executed cleanup handler: {handler_id}")
            except Exception as e:
                logger.error(f"Error in cleanup handler {handler_id}: {e}")
        
        self._cleanup_handlers.clear()
    
    def get_active_tasks_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about active tasks"""
        return {
            task_id: {
                'description': async_task.description,
                'created_at': async_task.created_at.isoformat(),
                'is_done': async_task.task.done(),
                'is_cancelled': async_task.task.cancelled()
            }
            for task_id, async_task in self._active_tasks.items()
        }

# Global resource manager instance
resource_manager = ResourceManager()

@contextmanager
def managed_database_session():
    """Context manager for database sessions with proper cleanup"""
    from ..database.connection import get_db
    
    db_session = None
    try:
        db_session = next(get_db())
        resource_manager._database_sessions.add(db_session)
        yield db_session
    except Exception as e:
        if db_session:
            try:
                db_session.rollback()
            except:
                pass
        raise e
    finally:
        if db_session:
            try:
                db_session.close()
            except Exception as e:
                logger.error(f"Error closing database session: {e}")

def managed_async_task(
    coro,
    task_id: str = None,
    description: str = "",
    timeout: Optional[float] = None
) -> asyncio.Task:
    """Create a managed async task with automatic cleanup"""
    
    async def wrapper():
        try:
            if timeout:
                return await asyncio.wait_for(coro, timeout=timeout)
            else:
                return await coro
        except asyncio.CancelledError:
            logger.debug(f"Task cancelled: {description}")
            raise
        except asyncio.TimeoutError:
            logger.warning(f"Task timed out: {description}")
            raise
        except Exception as e:
            logger.error(f"Task failed: {description} - {e}")
            raise
    
    task = asyncio.create_task(wrapper())
    resource_manager.register_async_task(task, task_id, description)
    
    return task

def safe_create_task(coro, description: str = ""):
    """Safely create an async task with error handling"""
    
    async def error_wrapped_coro():
        try:
            return await coro
        except Exception as e:
            logger.error(f"Async task error ({description}): {e}", exc_info=True)
            return None
    
    return managed_async_task(error_wrapped_coro(), description=description)

class ComponentLifecycleManager:
    """Manages lifecycle of UI components"""
    
    def __init__(self):
        self._components: Dict[str, Dict[str, Any]] = {}
    
    def register_component(
        self,
        component_id: str,
        cleanup_func: Optional[Callable] = None,
        data: Optional[Dict[str, Any]] = None
    ):
        """Register a component for lifecycle management"""
        self._components[component_id] = {
            'created_at': datetime.now(),
            'cleanup_func': cleanup_func,
            'data': data or {}
        }
        
        logger.debug(f"Registered component: {component_id}")
    
    def unregister_component(self, component_id: str):
        """Unregister and cleanup a component"""
        if component_id in self._components:
            component = self._components[component_id]
            
            # Run cleanup function if provided
            cleanup_func = component.get('cleanup_func')
            if cleanup_func:
                try:
                    cleanup_func()
                    logger.debug(f"Cleaned up component: {component_id}")
                except Exception as e:
                    logger.error(f"Error cleaning up component {component_id}: {e}")
            
            del self._components[component_id]
            return True
        return False
    
    def cleanup_all_components(self):
        """Cleanup all registered components"""
        for component_id in list(self._components.keys()):
            self.unregister_component(component_id)
    
    def get_component_info(self, component_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a component"""
        return self._components.get(component_id)

# Global component lifecycle manager
component_manager = ComponentLifecycleManager()

@contextmanager
def managed_ui_component(component_id: str, cleanup_func: Optional[Callable] = None):
    """Context manager for UI components with automatic cleanup"""
    component_manager.register_component(component_id, cleanup_func)
    try:
        yield component_id
    finally:
        component_manager.unregister_component(component_id)

class DatabaseConnectionPool:
    """Simple database connection pool for better resource management"""
    
    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self._connection_count = 0
        self._active_sessions: weakref.WeakSet = weakref.WeakSet()
    
    @contextmanager
    def get_session(self):
        """Get a database session from the pool"""
        if self._connection_count >= self.max_connections:
            from ..utils.error_handler import DatabaseException
            raise DatabaseException("Connection pool exhausted", "POOL_EXHAUSTED")
        
        from ..database.connection import get_db
        
        self._connection_count += 1
        db_session = None
        
        try:
            db_session = next(get_db())
            self._active_sessions.add(db_session)
            yield db_session
            db_session.commit()
        except Exception as e:
            if db_session:
                try:
                    db_session.rollback()
                except:
                    pass
            raise e
        finally:
            if db_session:
                try:
                    db_session.close()
                except:
                    pass
            self._connection_count = max(0, self._connection_count - 1)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        return {
            'active_connections': self._connection_count,
            'max_connections': self.max_connections,
            'active_sessions': len(self._active_sessions)
        }

# Global connection pool
db_pool = DatabaseConnectionPool()

def cleanup_all_resources():
    """Cleanup all application resources"""
    logger.info("Starting resource cleanup...")
    
    # Cleanup async tasks
    resource_manager.cleanup_all()
    
    # Cleanup components
    component_manager.cleanup_all_components()
    
    logger.info("Resource cleanup completed")

# Register cleanup on application shutdown
import atexit
atexit.register(cleanup_all_resources)