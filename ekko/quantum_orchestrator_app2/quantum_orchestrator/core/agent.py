# File: ~/Projects/quantum_orchestrator_app/quantum_orchestrator/core/agent.py
# Version: 1.1 - Integrated recovered Replit code with config.py & refinements

"""
Orchestrator: The central component of the Quantum Orchestrator system.

Integrates recovered Replit logic. Implements the Neural Flow Pipeline concept
through instruction routing and coordinates the Cognitive Fusion Core of
specialized AI agents. Adheres to TPC standards and Drake v0.1 protocols.
"""

import asyncio
import importlib
import inspect
import json
import logging
import os
import pkgutil
import sys
import time
import traceback
from functools import partial, lru_cache
from pathlib import Path
from queue import Queue # Consider asyncio.Queue for fully async operation later
from threading import Lock
from typing import Any, Callable, Dict, List, Optional, Type, Union

# --- Core Imports ---
# Uses the final config module
from .config import Settings, get_settings

# --- Component Imports (Attempt actuals, fallback to placeholders) ---
# This structure allows gradual implementation without breaking the agent

try:
    from .state_manager import StateManager
    logger.debug("Successfully imported StateManager")
except ImportError:
    logger.warning("StateManager not found, using placeholder.")
    class StateManager: # Placeholder Definition
        def __init__(self, config: Optional[Settings] = None): logger.info("StateManagerPlaceholder Initialized.")
        def begin_transaction(self, id: str): logger.debug(f"Placeholder: Begin Transaction {id}")
        def commit_transaction(self, id: str): logger.debug(f"Placeholder: Commit Transaction {id}")
        def rollback_transaction(self, id: str): logger.warning(f"Placeholder: Rollback Transaction {id}")
        def get_state(self, key: str, default: Any = None) -> Any: logger.debug(f"Placeholder: Get State '{key}'"); return default
        def set_state(self, key: str, value: Any): logger.debug(f"Placeholder: Set State '{key}'")
        def update(self, key: str, value: Any): self.set_state(key, value) # Alias

try:
    from .instruction_parser import InstructionParser
    logger.debug("Successfully imported InstructionParser")
except ImportError:
    logger.warning("InstructionParser not found, using placeholder.")
    class InstructionParser: # Placeholder Definition
        def __init__(self, schema_path: Optional[str] = None): logger.info("InstructionParserPlaceholder Initialized.")
        def parse(self, instruction_data: Dict) -> Dict: return instruction_data # Simple pass-through
        def validate(self, instruction_data: Dict) -> Dict: # Basic validation
            logger.debug(f"Placeholder: Validating instruction: {instruction_data.get('step_id', 'N/A')}")
            valid = isinstance(instruction_data.get("type"), str)
            return {"valid": valid, "errors": [] if valid else ["Missing or invalid 'type' field."]}

try:
    from ..services.llm_service import LLMService
    logger.debug("Successfully imported LLMService")
except ImportError:
    logger.warning("LLMService not found, using placeholder.")
    class LLMService: # Placeholder Definition
        def __init__(self, settings: Settings): self.settings = settings; logger.info("LLMServicePlaceholder Initialized.")
        async def generate_text(self, prompt: str, model: Optional[str] = None) -> str:
            logger.info(f"LLM Placeholder generating text (model: {model or self.settings.llm_service.model_name})...")
            await asyncio.sleep(0.05)
            return f"LLM Placeholder Response: {prompt[:50]}"
        async def generate_code(self, prompt: str, language: str = "python") -> str:
            logger.info(f"LLM Placeholder generating code (model: {model or self.settings.llm_service.model_name})...")
            await asyncio.sleep(0.05)
            return f"# LLM Placeholder Code: {prompt[:50]}"

try:
    from ..ai_agents.planning_agent import PlanningAgent
    logger.debug("Successfully imported PlanningAgent")
except ImportError:
    logger.warning("PlanningAgent not found, using placeholder.")
    class PlanningAgent: # Placeholder Definition
        def __init__(self, orchestrator: Any): logger.info("PlanningAgentPlaceholder Initialized.")
        async def design_workflow(self, intent: str, available_tools: Dict) -> List[Dict]:
            logger.info(f"Placeholder plan generation for intent: {intent}")
            await asyncio.sleep(0.05)
            return [{"type": "PLACEHOLDER_ACTION", "description": f"Placeholder step for intent: {intent}"}]

try: from ..ai_agents.code_agent import CodeAgent; logger.debug("Imported CodeAgent")
except ImportError: logger.warning("CodeAgent not found, placeholder active."); class CodeAgent: pass
try: from ..ai_agents.test_agent import TestAgent; logger.debug("Imported TestAgent")
except ImportError: logger.warning("TestAgent not found, placeholder active."); class TestAgent: pass
try: from ..ai_agents.optimization_agent import OptimizationAgent; logger.debug("Imported OptimizationAgent")
except ImportError: logger.warning("OptimizationAgent not found, placeholder active."); class OptimizationAgent: def __init__(self, *args): logger.info("OptimizationAgentPlaceholder Initialized.")
try: from ..ai_agents.meta_agent import MetaAgent; logger.debug("Imported MetaAgent")
except ImportError: logger.warning("MetaAgent not found, placeholder active."); class MetaAgent: def __init__(self, *args): logger.info("MetaAgentPlaceholder Initialized.")
try: from ..ai_agents.core_team import CoreTeamSimulator; logger.debug("Imported CoreTeamSimulator")
except ImportError: logger.warning("CoreTeamSimulator not found, placeholder active."); class CoreTeamSimulator: pass

try:
    # Assumes a decorator @handler exists in handlers/__init__.py
    from ..handlers import handler
    logger.debug("Imported @handler decorator.")
except ImportError:
    logger.warning("Could not import @handler decorator. Defining dummy.")
    def handler(*args, **kwargs):
        def decorator(func):
            func.is_handler = True
            func._handler_metadata = { # Store metadata in a standard attribute
                "name": kwargs.get("name", func.__name__),
                "description": kwargs.get("description", func.__doc__ or "No description"),
                "parameters": kwargs.get("parameters", {}),
                "returns": kwargs.get("returns", {})
            }
            return func
        return decorator

try:
    from ..utils.logging_utils import get_logger
    logger.debug("Imported logging utils.")
except ImportError:
    get_logger = logging.getLogger # Fallback

try:
    from ..utils.telemetry import Telemetry
    logger.debug("Imported Telemetry")
except ImportError:
    logger.warning("Telemetry not found, using placeholder.")
    class Telemetry: # Placeholder Definition
         def __init__(self): self.start_time = time.time(); self.execution_count = 0; self.success_count = 0; self.total_time = 0.0; logger.info("TelemetryPlaceholder Initialized.")
         def record_start_execution(self): self.execution_count += 1
         def record_execution_complete(self, *args, **kwargs):
             if kwargs.get("success"): self.success_count += 1
             self.total_time += kwargs.get("execution_time", 0)
         @property
         def success_rate(self): return (self.success_count / self.execution_count) * 100 if self.execution_count else 0
         @property
         def average_execution_time(self): return self.total_time / self.execution_count if self.execution_count else 0

# --- Global Logger ---
logger = get_logger(__name__)


# --- Orchestrator Class Implementation ---
class Orchestrator:
    """
    The central orchestrator for receiving instructions, managing state,
    dispatching actions to handlers, and coordinating AI agents.
    Embodies the 'Neural Flow Pipeline' concept through its execution logic.
    """

    def __init__(self):
        """Initializes the Orchestrator instance."""
        self.settings: Settings = get_settings() # Use the cached settings instance
        logger.info(f"Initializing Orchestrator '{self.settings.app_name}'...")
        logger.info(f"LLM Service Config: Provider='{self.settings.llm_service.default_provider}', Model='{self.settings.llm_service.model_name}', Base='{self.settings.llm_service.api_base}'")

        # Initialize core components
        self.state_manager = StateManager() # Uses placeholder if real one not imported
        schema_file = PROJECT_ROOT_DIR / "instruction_schema.json" # Use resolved path
        self.parser = InstructionParser(schema_path=str(schema_file)) # Uses placeholder if real one not imported
        self.llm_service = LLMService(self.settings) # Uses placeholder if real one not imported
        self.telemetry = Telemetry() # Uses placeholder if real one not imported

        # Handler / Tool Registry
        self.handlers: Dict[str, Callable] = {}
        self.handler_lock = Lock()
        self.available_tools: Dict[str, Any] = {} # Attribute expected by verification
        self._register_handlers()
        self._update_available_tools() # Populate based on registered handlers

        # Initialize AI Agents (uses placeholders if real ones not imported)
        self.planning_agent = PlanningAgent(self)
        self.code_agent = CodeAgent(self) if 'CodeAgent' in globals() and CodeAgent.__name__ != 'type' else None
        self.test_agent = TestAgent(self) if 'TestAgent' in globals() and TestAgent.__name__ != 'type' else None
        self.optimization_agent = OptimizationAgent(self) if 'OptimizationAgent' in globals() and OptimizationAgent.__name__ != 'type' else None
        self.meta_agent = MetaAgent(self) if 'MetaAgent' in globals() and MetaAgent.__name__ != 'type' else None
        self.core_team = CoreTeamSimulator() if 'CoreTeamSimulator' in globals() and CoreTeamSimulator.__name__ != 'type' else None

        self.agents: Dict[str, Optional[Any]] = {
            "planning": self.planning_agent, "code": self.code_agent, "test": self.test_agent,
            "optimization": self.optimization_agent, "meta": self.meta_agent, "core_team": self.core_team
        }

        # Communication queues
        self.message_queues: Dict[str, Queue] = { name: Queue() for name in list(self.agents.keys()) + ["orchestrator"] if self.agents.get(name) or name=="orchestrator"}

        logger.info("Orchestrator initialization complete.")

    def _register_handlers(self):
        """Dynamically discovers and registers handlers with the @handler decorator."""
        logger.info("Registering action handlers...")
        handlers_package_dir = Path(__file__).parent.parent / "handlers"
        package_name = "quantum_orchestrator.handlers"
        logger.debug(f"Scanning for handlers in: {handlers_package_dir}")

        with self.handler_lock:
            self.handlers = {}
            for importer, modname, ispkg in pkgutil.iter_modules(path=[str(handlers_package_dir)], prefix=package_name + '.'):
                if ispkg:
                    sub_path = [str(handlers_package_dir / modname.split('.')[-1])]
                    for sub_importer, sub_modname, sub_ispkg in pkgutil.iter_modules(path=sub_path, prefix=modname + '.'):
                         if not sub_ispkg: # Load modules, not sub-packages directly here
                             self._load_handlers_from_module(sub_modname)
                else:
                    self._load_handlers_from_module(modname)

            if not self.handlers:
                logger.warning("No handlers registered dynamically. Using placeholder.")
                self.handlers["PLACEHOLDER_ACTION"] = self._placeholder_handler

            logger.info(f"Registered {len(self.handlers)} handlers: {list(self.handlers.keys())}")

    def _load_handlers_from_module(self, module_name: str):
        """Helper to load and register handlers from a specific module."""
        try:
            module = importlib.import_module(module_name)
            for attribute_name in dir(module):
                attribute = getattr(module, attribute_name)
                if callable(attribute) and hasattr(attribute, "is_handler") and getattr(attribute, "is_handler", False):
                    metadata = getattr(attribute, "_handler_metadata", {})
                    handler_name = metadata.get("name", attribute.__name__)
                    if handler_name in self.handlers:
                        logger.warning(f"Duplicate handler name '{handler_name}' found in {module_name}. Overwriting.")
                    self.handlers[handler_name] = attribute
                    logger.debug(f"Registered handler: '{handler_name}' from {module_name}")
        except Exception as e:
            logger.error(f"Failed to load or register handlers from module {module_name}: {e}", exc_info=True)

    def _update_available_tools(self):
        """Updates the registry of tools available for AI agents."""
        logger.debug("Updating available tools registry...")
        with self.handler_lock:
            self.available_tools = {}
            for name, handler_func in self.handlers.items():
                 metadata = getattr(handler_func, "_handler_metadata", {})
                 self.available_tools[name] = {
                     "description": metadata.get("description", "No description available."),
                     "parameters": metadata.get("parameters", {}),
                     "returns": metadata.get("returns", {}),
                     "module": handler_func.__module__
                 }
        logger.info(f"Updated available_tools registry with {len(self.available_tools)} tools.")

    def get_status(self) -> Dict[str, Any]:
        """Returns the current operational status of the Orchestrator."""
        uptime = time.time() - self.telemetry.start_time if hasattr(self.telemetry, 'start_time') else 0
        return {
            "status": "running",
            "app_name": self.settings.app_name,
            "handlers_count": len(self.handlers),
            "registered_handlers": list(self.handlers.keys()),
            "timestamp": time.time(),
            "uptime_seconds": uptime,
            "telemetry": { # Safely access telemetry attributes
                "execution_count": getattr(self.telemetry, 'execution_count', 0),
                "success_rate": getattr(self.telemetry, 'success_rate', 0),
                "average_execution_time": getattr(self.telemetry, 'average_execution_time', 0)
            }
        }

    # --- Core Instruction Processing Logic ---

    async def execute_instruction(self, instruction: Union[Dict[str, Any], str]) -> Dict[str, Any]:
        """
        Executes a single instruction or a workflow, handling different types.
        Uses asyncio for potentially concurrent operations.
        """
        start_time = time.time()
        if hasattr(self, 'telemetry'): self.telemetry.record_start_execution()

        # 1. Parse and Validate Input
        instruction_dict: Dict[str, Any] = {}
        if isinstance(instruction, str):
            try: instruction_dict = json.loads(instruction)
            except json.JSONDecodeError as e: return {"success": False, "error": f"Invalid JSON: {e}", "execution_time": 0}
        elif isinstance(instruction, dict): instruction_dict = instruction
        else: return {"success": False, "error": "Invalid instruction format (must be dict or JSON string).", "execution_time": 0}

        step_id = instruction_dict.get("step_id", f"instr_{time.time_ns()}")

        validation_result = self.parser.validate(instruction_dict)
        if not validation_result["valid"]:
            logger.error(f"Invalid instruction (ID: {step_id}): {validation_result['errors']}")
            return {"success": False, "step_id": step_id, "error": f"Invalid instruction: {validation_result['errors']}", "execution_time": 0}

        # 2. Route based on Type
        instruction_type = instruction_dict.get("type", "").lower()
        logger.info(f"Routing instruction ID: {step_id}, Type: {instruction_type}")

        result: Dict[str, Any] = {}
        try:
            if instruction_type == "intent":
                result = await self._process_intent_instruction(step_id, instruction_dict)
            elif instruction_type == "direct_action": # Assume direct actions are specified this way
                result = await self._process_direct_action(step_id, instruction_dict)
            elif instruction_type == "workflow":
                result = await self._process_workflow_instruction(step_id, instruction_dict)
            elif instruction_type == "generate_tool":
                result = await self._process_tool_generation(step_id, instruction_dict)
            else:
                raise ValueError(f"Unknown instruction type: '{instruction_type}'")

        except Exception as e:
            logger.error(f"Core execution error for instruction ID {step_id}: {e}", exc_info=True)
            result = {"success": False, "error": f"Core execution error: {type(e).__name__}: {e}", "traceback": traceback.format_exc()}

        # Finalize result
        result["success"] = result.get("status", "").upper() == "COMPLETED" or result.get("success", False)
        result["step_id"] = step_id
        result["execution_time"] = time.time() - start_time
        if hasattr(self, 'telemetry'): self.telemetry.record_execution_complete(success=result["success"], execution_time=result["execution_time"])

        logger.info(f"Completed instruction ID: {step_id} | Success: {result['success']} | Time: {result['execution_time']:.3f}s")
        return result

    async def _process_intent_instruction(self, step_id: str, instruction: Dict[str, Any]) -> Dict[str, Any]:
        """Processes intent by generating and executing a workflow."""
        intent = instruction.get("intent", "")
        if not intent: return {"success": False, "error": "Missing 'intent' field."}
        logger.info(f"Processing intent for ID {step_id}: '{intent[:100]}...'")

        if not self.planning_agent or not hasattr(self.planning_agent, 'design_workflow'):
            return {"success": False, "error": "Planning agent not available or lacks 'design_workflow' method."}

        try:
            workflow_steps = await self.planning_agent.design_workflow(intent, self.available_tools)
            if not workflow_steps or not isinstance(workflow_steps, list):
                raise ValueError("Planning agent did not return a valid list of steps.")
        except Exception as e:
             logger.error(f"Planning agent failed for intent '{intent}': {e}", exc_info=True)
             return {"success": False, "error": f"Planning agent failed: {e}"}

        workflow_instruction = {
            "type": "workflow",
            "description": f"Workflow generated for intent: {intent}",
            "steps": workflow_steps,
            "fail_fast": instruction.get("fail_fast", True)
        }
        logger.info(f"Executing generated workflow with {len(workflow_steps)} steps for ID: {step_id}")
        return await self._process_workflow_instruction(f"{step_id}_workflow", workflow_instruction)

    async def _process_direct_action(self, step_id: str, action: Dict[str, Any]) -> Dict[str, Any]:
        """Processes a single direct action by dispatching to the correct handler."""
        action_type = action.get("type")
        if not action_type: return {"success": False, "error": "Direct action missing 'type' field."}
        params = {k: v for k, v in action.items() if k != "type"}
        logger.info(f"Processing direct action for ID {step_id}: Type '{action_type}'")

        if action_type not in self.handlers:
            return {"success": False, "error": f"Unknown handler/action type: '{action_type}'"}

        handler = self.handlers[action_type]
        transaction_id = f"tx_{step_id}_{action_type}_{time.time_ns()}"

        try:
            self.state_manager.begin_transaction(transaction_id)
            logger.debug(f"Executing handler '{action_type}' with params: {params}")

            if inspect.iscoroutinefunction(handler):
                handler_result = await handler(params=params)
            else:
                loop = asyncio.get_running_loop()
                handler_result = await loop.run_in_executor(None, partial(handler, params=params))

            if not isinstance(handler_result, dict) or 'success' not in handler_result:
                 raise TypeError(f"Handler '{action_type}' returned invalid result format: {type(handler_result)}")

            if handler_result["success"]:
                logger.info(f"Handler '{action_type}' executed successfully.")
                self.state_manager.commit_transaction(transaction_id)
                # TODO: Optional optimization step?
                # if action.get("optimize", False) and "code" in handler_result and self.optimization_agent:
                #     optimized = await self.optimization_agent.refine_code(handler_result["code"], {"context": action})
                #     if optimized: handler_result["optimized_code"] = optimized
                return handler_result
            else:
                raise RuntimeError(f"Handler '{action_type}' reported failure: {handler_result.get('error', 'Unknown error')}")

        except Exception as e:
            logger.error(f"Error executing handler '{action_type}' for ID {step_id}: {e}", exc_info=True)
            self.state_manager.rollback_transaction(transaction_id)
            return {"success": False, "action_type": action_type, "error": f"Error executing '{action_type}': {type(e).__name__}: {e}", "traceback": traceback.format_exc()}

    async def _process_workflow_instruction(self, step_id: str, instruction: Dict[str, Any]) -> Dict[str, Any]:
        """Processes a workflow instruction containing multiple steps."""
        steps = instruction.get("steps", [])
        if not steps: return {"success": False, "error": "Workflow instruction has no 'steps'."}

        parallel = instruction.get("parallel", False)
        fail_fast = instruction.get("fail_fast", True)
        workflow_results: List[Dict[str, Any]] = []
        overall_success = True

        logger.info(f"Starting workflow ID: {step_id} with {len(steps)} steps. Parallel={parallel}, FailFast={fail_fast}")

        # --- Simplified Sequential Execution for Now ---
        # TODO: Implement parallel/DAG execution later (Neural Flow Pipeline V2)
        if parallel:
            logger.warning("Parallel workflow execution requested but using sequential execution.")

        for i, step in enumerate(steps):
            step_start_time = time.time()
            step_internal_id = f"{step_id}_step{i}"
            if not isinstance(step, dict) or 'type' not in step:
                 logger.warning(f"Workflow {step_id}, Step {i+1}: Invalid format, skipping.")
                 step_result = {"step_index": i, "success": False, "error": "Invalid step format"}
            else:
                 # Assume step is a direct action for now
                 step_result = await self._process_direct_action(step_internal_id, step)
                 step_result["step_index"] = i # Add index for clarity

            step_result["step_duration"] = time.time() - step_start_time
            workflow_results.append(step_result)

            if not step_result["success"]:
                overall_success = False
                logger.warning(f"Workflow {step_id}, Step {i+1} (Type: {step.get('type', 'N/A')}) failed. FailFast={fail_fast}")
                if fail_fast:
                    break

        logger.info(f"Workflow ID: {step_id} finished. Overall Success: {overall_success}")
        return {
            "success": overall_success,
            "status": "COMPLETED" if overall_success else "FAILED",
            "workflow_results": workflow_results
        }

    async def _process_tool_generation(self, step_id: str, instruction: Dict[str, Any]) -> Dict[str, Any]:
        """Processes a request to generate and optionally integrate a new tool."""
        description = instruction.get("description", "")
        suggested_name = instruction.get("suggested_name", "")
        integrate = instruction.get("integrate", True)

        logger.info(f"Processing tool generation request ID: {step_id}. Desc: {description[:50]}...")

        if not description: return {"success": False, "error": "Tool description is required."}
        if not self.meta_agent or not hasattr(self.meta_agent, 'generate_tool'):
             return {"success": False, "error": "Meta agent not available or lacks 'generate_tool' method."}

        try:
            tool_code = await self.meta_agent.generate_tool(description, suggested_name)
            if not tool_code: raise RuntimeError("Meta agent failed to generate tool code.")

            # Basic extraction of function name
            match = re.search(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)', tool_code)
            func_name = match.group(1) if match else suggested_name or f"custom_tool_{time.time_ns()}"
            handler_name = func_name

            result_payload = {
                "success": True, "message": f"Tool code generated for '{handler_name}'.",
                "tool_name": handler_name, "tool_code": tool_code, "integrated": False
            }

            if integrate:
                logger.info(f"Attempting to integrate generated tool: {handler_name}")
                try:
                    # Define path for custom handlers relative to this file
                    custom_handlers_dir = Path(__file__).parent.parent / "handlers" / "custom"
                    custom_handlers_dir.mkdir(parents=True, exist_ok=True)
                    init_path = custom_handlers_dir / "__init__.py"
                    init_path.touch(exist_ok=True)

                    # Prepare full code with imports and decorator
                    # Ensure the @handler decorator is properly imported or defined
                    full_tool_code = f"""\
# File: {custom_handlers_dir / f"{handler_name}.py"}
# Automatically generated tool by MetaAgent for instruction {step_id}
\"\"\"
Generated handler: {handler_name}
Description: {description}
\"\"\"
import json, os, asyncio
from typing import Dict, Any, Optional, List, Union
# Assuming the decorator is importable like this:
from quantum_orchestrator.handlers import handler

{tool_code}
"""
                    tool_file_path = custom_handlers_dir / f"{handler_name}.py"
                    with open(tool_file_path, "w", encoding="utf-8") as f: f.write(full_tool_code)
                    logger.info(f"Saved generated tool code to: {tool_file_path}")

                    # Dynamically import and register
                    module_name = f"quantum_orchestrator.handlers.custom.{handler_name}"
                    if module_name in sys.modules: del sys.modules[module_name] # Force re-import

                    module = importlib.import_module(module_name)
                    # importlib.reload(module) # Reload might be needed in some envs

                    registered = False
                    for name, obj in module.__dict__.items():
                        if hasattr(obj, "is_handler") and obj.is_handler:
                            self.register_handler(obj.handler_name, obj) # Use instance method
                            registered = True
                            result_payload.update({
                                "message": f"Tool '{obj.handler_name}' generated and integrated.",
                                "integrated": True, "tool_file": str(tool_file_path)
                            })
                            break
                    if not registered: raise ImportError(f"Could not find @handler decorated function in {tool_file_path}")

                except Exception as integration_e:
                    logger.error(f"Failed to integrate generated tool '{handler_name}': {integration_e}", exc_info=True)
                    result_payload.update({
                        "success": False, # Mark as failed if integration failed
                        "error": f"Tool generated but integration failed: {integration_e}",
                        "integrated": False,
                        "tool_file": str(tool_file_path) if 'tool_file_path' in locals() else None
                    })
            return result_payload

        except Exception as e:
             logger.error(f"Error processing tool generation request ID {step_id}: {e}", exc_info=True)
             return {"success": False, "error": f"Tool generation error: {type(e).__name__}: {e}", "traceback": traceback.format_exc()}

    # --- Placeholder Handler ---
    def _placeholder_handler(self, params: Dict) -> Dict:
         """Dummy handler for testing."""
         logger.info(f"Executed _placeholder_handler with params: {params}")
         return {"success": True, "result": "Placeholder OK"}

# --- Main Execution Logic (Consider moving to main.py) ---
async def main_async():
    """Async main function for testing."""
    print("Initializing Orchestrator for async test...")
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    try:
        orchestrator = Orchestrator()
        print("Orchestrator initialized.")

        test_instr = {
            "step_id": "test-async-001",
            "description": "Test async placeholder",
            "type": "direct_action", # Use direct_action type
            # Ensure the action type matches a registered handler key
            "action_type_key": "PLACEHOLDER_ACTION", # Need to clarify how action type is passed
            "detail": "Async test data"
        }
         # Correcting how action type is passed based on _process_direct_action structure:
        test_instr_corrected = {
             "step_id": "test-async-001",
             "description": "Test async placeholder",
             "type": "PLACEHOLDER_ACTION", # The type *is* the handler key
             "detail": "Async test data"
         }

        print("\nProcessing test instruction:")
        result = await orchestrator.execute_instruction(test_instr_corrected)
        print("\nTest Instruction Result:")
        print(json.dumps(result, indent=2))

    except ValueError as e:
        print(f"\n--- CRITICAL CONFIGURATION ERROR ---")
        print(f"Error: {e}")
    except Exception as e:
        print(f"\n--- Error during Orchestrator test execution ---")
        print(f"Error: {type(e).__name__}: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    # If run directly, execute the async main function
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\nExecution interrupted.")
