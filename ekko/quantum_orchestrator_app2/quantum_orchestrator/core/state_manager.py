"""
StateManager: Manages persistent state for the Quantum Orchestrator.

Provides methods to load, save, get, update, and rollback state.
"""

import json
import os
import time
import copy
import threading
import logging
from typing import Any, Dict, Optional, List, Union

from quantum_orchestrator.utils.logging_utils import get_logger

class StateManager:
    """
    StateManager: Handles persistent state management for the Quantum Orchestrator.
    
    Ensures atomic operations and maintains a history for rollback capability.
    """
    
    def __init__(self, state_file: str = "orchestrator_state.json"):
        """
        Initialize the StateManager.
        
        Args:
            state_file: Path to the state file
        """
        self.logger = get_logger(__name__)
        self.state_file = state_file
        self.state: Dict[str, Any] = {}
        self.history: List[Dict[str, Any]] = []
        self.max_history = 10
        self.lock = threading.RLock()  # Reentrant lock for thread safety
        
        # Load initial state
        self.load()
        self.logger.info("StateManager initialized")

    def load(self) -> bool:
        """
        Load state from the state file.
        
        Returns:
            bool: True if state was loaded successfully, False otherwise
        """
        with self.lock:
            try:
                if os.path.exists(self.state_file):
                    with open(self.state_file, 'r') as f:
                        self.state = json.load(f)
                    self.logger.info(f"State loaded from {self.state_file}")
                    return True
                else:
                    self.state = {
                        "created_at": time.time(),
                        "updated_at": time.time(),
                        "version": 1
                    }
                    self.save()
                    self.logger.info(f"No state file found, initialized new state in {self.state_file}")
                    return True
            except Exception as e:
                self.logger.error(f"Failed to load state: {str(e)}")
                return False

    def save(self) -> bool:
        """
        Save state to the state file.
        
        Returns:
            bool: True if state was saved successfully, False otherwise
        """
        with self.lock:
            try:
                # Create a copy for history before updating timestamp
                history_entry = copy.deepcopy(self.state)
                self.history.append(history_entry)
                
                # Limit history size
                while len(self.history) > self.max_history:
                    self.history.pop(0)
                
                # Update timestamp
                self.state["updated_at"] = time.time()
                
                # Save to file with atomic write operation
                temp_file = f"{self.state_file}.tmp"
                with open(temp_file, 'w') as f:
                    json.dump(self.state, f, indent=2)
                
                # Atomic rename
                os.replace(temp_file, self.state_file)
                
                self.logger.debug(f"State saved to {self.state_file}")
                return True
            except Exception as e:
                self.logger.error(f"Failed to save state: {str(e)}")
                return False

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the state.
        
        Args:
            key: Key to retrieve
            default: Default value if key doesn't exist
            
        Returns:
            The value or default if key doesn't exist
        """
        with self.lock:
            # Support for nested keys using dot notation
            if '.' in key:
                parts = key.split('.')
                current = self.state
                
                for part in parts[:-1]:
                    if part not in current or not isinstance(current[part], dict):
                        return default
                    current = current[part]
                
                return current.get(parts[-1], default)
            
            return self.state.get(key, default)

    def update(self, key: str, value: Any, save_state: bool = True) -> bool:
        """
        Update a value in the state.
        
        Args:
            key: Key to update
            value: New value
            save_state: Whether to save state after update
            
        Returns:
            bool: True if update was successful
        """
        with self.lock:
            try:
                # Support for nested keys using dot notation
                if '.' in key:
                    parts = key.split('.')
                    current = self.state
                    
                    # Navigate to the nested dict
                    for part in parts[:-1]:
                        if part not in current:
                            current[part] = {}
                        elif not isinstance(current[part], dict):
                            current[part] = {}
                        current = current[part]
                    
                    # Set the value
                    current[parts[-1]] = value
                else:
                    self.state[key] = value
                
                # Save if requested
                if save_state:
                    return self.save()
                return True
            except Exception as e:
                self.logger.error(f"Failed to update state for key {key}: {str(e)}")
                return False

    def delete(self, key: str, save_state: bool = True) -> bool:
        """
        Delete a key from the state.
        
        Args:
            key: Key to delete
            save_state: Whether to save state after deletion
            
        Returns:
            bool: True if deletion was successful
        """
        with self.lock:
            try:
                # Support for nested keys using dot notation
                if '.' in key:
                    parts = key.split('.')
                    current = self.state
                    
                    # Navigate to the nested dict
                    for part in parts[:-1]:
                        if part not in current or not isinstance(current[part], dict):
                            return False
                        current = current[part]
                    
                    # Delete the key
                    if parts[-1] in current:
                        del current[parts[-1]]
                else:
                    if key in self.state:
                        del self.state[key]
                
                # Save if requested
                if save_state:
                    return self.save()
                return True
            except Exception as e:
                self.logger.error(f"Failed to delete state for key {key}: {str(e)}")
                return False

    def rollback(self, steps: int = 1) -> bool:
        """
        Rollback state to a previous version.
        
        Args:
            steps: Number of steps to rollback
            
        Returns:
            bool: True if rollback was successful
        """
        with self.lock:
            if not self.history or steps <= 0 or steps > len(self.history):
                self.logger.error(f"Cannot rollback {steps} steps, history has {len(self.history)} entries")
                return False
            
            try:
                # Get the state from history
                rollback_index = len(self.history) - steps
                rollback_state = self.history[rollback_index]
                
                # Restore the state
                self.state = copy.deepcopy(rollback_state)
                
                # Truncate history
                self.history = self.history[:rollback_index]
                
                # Save the rolled back state
                return self.save()
            except Exception as e:
                self.logger.error(f"Failed to rollback state: {str(e)}")
                return False

    def get_all(self) -> Dict[str, Any]:
        """
        Get the entire state.
        
        Returns:
            Dict: The complete state
        """
        with self.lock:
            return copy.deepcopy(self.state)

    def update_multiple(self, updates: Dict[str, Any], save_state: bool = True) -> bool:
        """
        Update multiple keys in the state atomically.
        
        Args:
            updates: Dict of key-value pairs to update
            save_state: Whether to save state after updates
            
        Returns:
            bool: True if all updates were successful
        """
        with self.lock:
            try:
                for key, value in updates.items():
                    # Use the existing update method without saving
                    self.update(key, value, save_state=False)
                
                # Save once if requested
                if save_state:
                    return self.save()
                return True
            except Exception as e:
                self.logger.error(f"Failed to update multiple state keys: {str(e)}")
                return False

    def clear(self, save_state: bool = True) -> bool:
        """
        Clear the entire state.
        
        Args:
            save_state: Whether to save state after clearing
            
        Returns:
            bool: True if clear was successful
        """
        with self.lock:
            try:
                # Keep only minimal required fields
                self.state = {
                    "created_at": time.time(),
                    "updated_at": time.time(),
                    "version": self.state.get("version", 1) + 1
                }
                
                # Save if requested
                if save_state:
                    return self.save()
                return True
            except Exception as e:
                self.logger.error(f"Failed to clear state: {str(e)}")
                return False
                
    def get_recent_workflows(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent workflows from the state.
        
        Args:
            limit: Maximum number of workflows to return
            
        Returns:
            List of recent workflow executions
        """
        with self.lock:
            try:
                # Get the workflows from state
                workflows = self.get("workflows", [])
                
                # If workflows is not a list, return an empty list
                if not isinstance(workflows, list):
                    return []
                    
                # Sort by timestamp (newest first) and limit
                sorted_workflows = sorted(
                    workflows, 
                    key=lambda w: w.get("timestamp", 0), 
                    reverse=True
                )
                
                return sorted_workflows[:limit]
            except Exception as e:
                self.logger.error(f"Failed to get recent workflows: {str(e)}")
                return []
