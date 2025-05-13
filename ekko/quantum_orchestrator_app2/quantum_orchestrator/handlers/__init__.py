"""
Handlers for the Quantum Orchestrator system.

This package contains task-specific handler functions that are registered with
the Orchestrator and can be invoked by instructions.
"""

from functools import wraps
from typing import Any, Callable, Dict, Optional

def handler(name: Optional[str] = None, description: str = "", parameters: Optional[Dict[str, Any]] = None, 
           returns: Optional[Dict[str, Any]] = None):
    """
    Decorator to mark a function as a handler for the orchestrator.
    
    Args:
        name: The name of the handler (defaults to function name)
        description: Description of what the handler does
        parameters: Dictionary describing the expected parameters
        returns: Dictionary describing the return values
    
    Returns:
        Decorated function
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        # Set attributes for handler registration
        wrapper.is_handler = True
        wrapper.handler_name = name or func.__name__
        wrapper.description = description
        wrapper.parameters = parameters or {}
        wrapper.returns = returns or {}
        
        return wrapper
    
    return decorator
