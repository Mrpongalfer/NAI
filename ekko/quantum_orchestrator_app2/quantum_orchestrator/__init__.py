"""
Quantum Orchestrator: A comprehensive system with Neural Flow Pipeline and Cognitive Fusion Core.

This package implements a production-grade orchestration system that coordinates
specialized AI agents through a Neural Flow Pipeline and Cognitive Fusion Core.
It provides robust automation, integration, and meta-generation capabilities.
"""

import sys
import os
import logging

__version__ = "1.0.0"

# Initialize package-level logger
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import main components for easy access
from quantum_orchestrator.core.agent import Orchestrator
from quantum_orchestrator.core.config import Config
from quantum_orchestrator.core.self_verification import SelfVerification

# Global orchestrator instance
_orchestrator_instance = None

def get_orchestrator():
    """Get the global orchestrator instance."""
    global _orchestrator_instance
    return _orchestrator_instance

def init_api(orchestrator_instance=None):
    """Initialize the API service."""
    from quantum_orchestrator.api import init_api_service
    return init_api_service(orchestrator_instance)

# Initialize the orchestrator at module level if requested
if 'INIT_ORCHESTRATOR' in os.environ and os.environ['INIT_ORCHESTRATOR'].lower() == 'true':
    from quantum_orchestrator.core.config import Config
    from quantum_orchestrator.core.state_manager import StateManager
    from quantum_orchestrator.core.instruction_parser import InstructionParser
    
    try:
        config = Config()
        state_manager = StateManager()
        instruction_parser = InstructionParser()
        
        _orchestrator_instance = Orchestrator(
            state_manager=state_manager,
            instruction_parser=instruction_parser,
            config=config
        )
        
        logger.info("Global orchestrator instance initialized")
    except Exception as e:
        logger.error(f"Failed to initialize global orchestrator: {str(e)}")