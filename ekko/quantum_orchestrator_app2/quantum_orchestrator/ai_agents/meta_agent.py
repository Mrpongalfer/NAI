"""
MetaAgent: AI agent responsible for generating new tools and components.

Part of the Cognitive Fusion Core, responsible for meta-generative capabilities
that extend the system's functionality.
"""

import asyncio
import json
import logging
import time
import re
import os
from typing import Any, Dict, List, Optional, Union, Tuple

from quantum_orchestrator.utils.logging_utils import get_logger
from quantum_orchestrator.services.llm_service import generate_completion, generate_completion_async
from quantum_orchestrator.handlers import handler

class MetaAgent:
    """
    MetaAgent: Responsible for generating new tools and components.
    
    Creates handler templates, suggests new capabilities, and dynamically
    extends the system's functionality.
    """
    
    def __init__(self, orchestrator: Any):
        """
        Initialize the MetaAgent.
        
        Args:
            orchestrator: The central Orchestrator instance
        """
        self.logger = get_logger(__name__)
        self.orchestrator = orchestrator
        self.generated_tools = {}  # Track generated tools
        self.logger.info("MetaAgent initialized")
    
    async def generate_tool(self, description: str, name: str = "") -> str:
        """
        Generate a new tool (handler) based on a description.
        
        Args:
            description: Description of the tool's functionality
            name: Optional name for the tool
            
        Returns:
            Generated tool code
        """
        self.logger.info(f"Generating tool for: {description}")
        
        # Generate a name if not provided
        if not name:
            name = self._generate_tool_name(description)
        
        # Check if tool was already generated
        if name in self.generated_tools:
            self.logger.info(f"Tool {name} already generated, returning existing code")
            return self.generated_tools[name]
        
        # Prepare prompt for the LLM
        prompt = f'''Generate a complete Python handler function for the Quantum Orchestrator system based on this description:

Description: {description}

The handler should follow these requirements:
1. Use the @handler decorator from quantum_orchestrator.handlers
2. Include comprehensive docstrings and comments
3. Follow the function signature pattern: def function_name(params: Dict[str, Any]) -> Dict[str, Any]
4. Handle all potential errors and edge cases
5. Return a dictionary with at least a 'success' key
6. Include detailed parameter and return value documentation

The @handler decorator should include:
- name: The name of the handler (if not specified, uses the function name)
- description: A clear description of what the handler does
- parameters: Dictionary describing expected parameters
- returns: Dictionary describing return values

Here is an example handler structure:

```python
from typing import Any, Dict, List, Optional
from quantum_orchestrator.handlers import handler
from quantum_orchestrator.utils.logging_utils import get_logger

logger = get_logger(__name__)

@handler(
    name="example_handler",
    description="Example handler that demonstrates the structure",
    parameters={
        "param1": {"type": "string", "description": "First parameter"},
        "param2": {"type": "integer", "description": "Second parameter", "default": 0}
    },
    returns={
        "success": {"type": "boolean", "description": "Whether the operation was successful"},
        "result": {"type": "string", "description": "Operation result"},
        "error": {"type": "string", "description": "Error message if operation failed"}
    }
)
def example_handler(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Example handler that demonstrates the structure.
    
    Args:
        params: Dictionary containing param1 and param2
        
    Returns:
        Dict containing success flag, result, and error message if any
    """
    try:
        param1 = params.get("param1", "")
        param2 = params.get("param2", 0)
        
        # Validate parameters
        if not param1:
            return {"success": False, "error": "param1 is required"}
        
        # Perform operation
        result = f"{param1}: {param2}"
        
        return {
            "success": True,
            "result": result
        }
    
    except Exception as e:
        logger.error(f"Error in example_handler: {str(e)}")
        return {"success": False, "error": f"Error: {str(e)}"}
```

Now, generate a complete Python handler function for: {description}
If a name was suggested ({name}), use that as the function name.
'''
        try:
            # Call the LLM service
            model_name = self.orchestrator.config.get("llm", {}).get("model", "gpt-4")
            temperature = 0.2  # Lower temperature for more deterministic output
            
            # Replace with actual LLM call when available
            response = await self._generate_handler_code(prompt, model_name, temperature)
            
            # Extract the code from the response
            code = self._extract_code_from_response(response, name)
            
            if code:
                # Store the generated tool
                self.generated_tools[name] = code
                return code
            else:
                self.logger.error("Failed to extract handler code from LLM response")
                return self._generate_fallback_handler(description, name)
            
        except Exception as e:
            self.logger.error(f"Error generating tool: {str(e)}")
            return self._generate_fallback_handler(description, name)
            
    def _generate_tool_name(self, description: str) -> str:
        """
        Generate a name for a tool based on its description.
        
        Args:
            description: Description of the tool's functionality
            
        Returns:
            Generated tool name
        """
        # Extract keywords from description
        keywords = re.findall(r'\b[a-zA-Z]{3,}\b', description.lower())
        
        if not keywords:
            return f"tool_{int(time.time())}"
        
        # Generate a name from the most relevant keywords
        name_parts = []
        for kw in keywords[:3]:  # Use up to 3 keywords
            if kw not in ['the', 'and', 'for', 'that', 'this', 'with', 'from']:
                name_parts.append(kw)
                if len(name_parts) >= 2:
                    break
        
        if not name_parts:
            return f"tool_{int(time.time())}"
        
        return "_".join(name_parts) + "_handler"
        
    async def _generate_handler_code(self, prompt: str, model: str, temperature: float) -> str:
        """
        Generate code using an LLM.
        
        Args:
            prompt: The prompt to send to the LLM
            model: The LLM model to use
            temperature: The temperature parameter for generation
            
        Returns:
            Generated code
        """
        # Production implementation would use an actual LLM service
        try:
            # This is a placeholder for the actual LLM call
            # In a production system, this would call an external API or local model
            
            response = await generate_completion_async(
                prompt=prompt,
                model=model,
                temperature=temperature,
                max_tokens=2000
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error calling LLM service: {str(e)}")
            
            # For now, provide a simple deterministic response for basic development
            return self._generate_simulation_response(prompt)
    
    def _generate_simulation_response(self, prompt: str) -> str:
        """
        Generate a simulated LLM response for development purposes.
        
        Args:
            prompt: The prompt that would be sent to an LLM
            
        Returns:
            Simulated response
        """
        # Extract the description from the prompt
        match = re.search(r'Description: (.*?)(?:\n|$)', prompt)
        description = match.group(1) if match else "unknown functionality"
        
        # Generate a simple handler based on the description
        description_keywords = re.findall(r'\b[a-zA-Z]{3,}\b', description.lower())
        function_name = "_".join(description_keywords[:2]) + "_handler" if description_keywords else "custom_handler"
        
        # Create a basic handler template
        return f'''
```python
from typing import Any, Dict, List, Optional
from quantum_orchestrator.handlers import handler
from quantum_orchestrator.utils.logging_utils import get_logger

logger = get_logger(__name__)

@handler(
    name="{function_name}",
    description="Handler for {description}",
    parameters={{
        "input": {{"type": "string", "description": "Input for the operation"}},
        "options": {{"type": "object", "description": "Optional parameters for the operation", "default": {{}}}}
    }},
    returns={{
        "success": {{"type": "boolean", "description": "Whether the operation was successful"}},
        "result": {{"type": "string", "description": "Operation result"}},
        "error": {{"type": "string", "description": "Error message if operation failed"}}
    }}
)
def {function_name}(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler for {description}.
    
    Args:
        params: Dictionary containing input and options
        
    Returns:
        Dict containing success flag, result, and error message if any
    """
    try:
        input_value = params.get("input", "")
        options = params.get("options", {{}})
        
        # Validate parameters
        if not input_value:
            return {{"success": False, "error": "input is required"}}
        
        # Process the input based on the description
        result = f"Processed {{input_value}} with options {{options}}"
        
        # Return the result
        return {{
            "success": True,
            "result": result
        }}
    
    except Exception as e:
        logger.error(f"Error in {function_name}: {{str(e)}}")
        return {{"success": False, "error": f"Error: {{str(e)}}"}}
```
'''
    
    def _extract_code_from_response(self, response: str, name: str = "") -> str:
        """
        Extract code from an LLM response.
        
        Args:
            response: The LLM response text
            name: The suggested name for the handler
            
        Returns:
            Extracted code
        """
        # Try to extract code between triple backticks
        code_match = re.search(r'```(?:python)?(.*?)```', response, re.DOTALL)
        if code_match:
            code = code_match.group(1).strip()
            
            # If a name was suggested, ensure the function uses that name
            if name and not name.endswith('_handler'):
                name = f"{name}_handler"
                
            if name:
                # Try to replace the function name in the code
                function_def_match = re.search(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', code)
                if function_def_match:
                    original_name = function_def_match.group(1)
                    code = code.replace(f"def {original_name}", f"def {name}")
                    code = code.replace(f'name="{original_name}"', f'name="{name}"')
                    
            return code
        
        # Fallback: if no code block is found, return the entire response
        return response.strip()
    
    def _generate_fallback_handler(self, description: str, name: str = "") -> str:
        """
        Generate a fallback handler if LLM generation fails.
        
        Args:
            description: Description of the tool's functionality
            name: Optional name for the tool
            
        Returns:
            Fallback handler code
        """
        # Use the provided name or generate one
        handler_name = name if name else self._generate_tool_name(description)
        
        # Create a basic handler
        return f'''
from typing import Any, Dict, List, Optional
from quantum_orchestrator.handlers import handler
from quantum_orchestrator.utils.logging_utils import get_logger

logger = get_logger(__name__)

@handler(
    name="{handler_name}",
    description="Handler for {description}",
    parameters={{
        "input": {{"type": "string", "description": "Input for the operation"}},
        "options": {{"type": "object", "description": "Optional configuration parameters", "default": {{}}}}
    }},
    returns={{
        "success": {{"type": "boolean", "description": "Whether the operation was successful"}},
        "result": {{"type": "object", "description": "Operation result"}},
        "error": {{"type": "string", "description": "Error message if operation failed"}}
    }}
)
def {handler_name}(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler for {description}.
    
    Args:
        params: Dictionary containing input and options
        
    Returns:
        Dict containing success flag, result, and error message if any
    """
    try:
        input_value = params.get("input", "")
        options = params.get("options", {{}})
        
        # Validate parameters
        if not input_value:
            return {{"success": False, "error": "input is required"}}
        
        # Perform operation based on description
        result = f"Processed {{input_value}} for {description}"
        
        return {{
            "success": True,
            "result": result,
            "description": "{description}"
        }}
    
    except Exception as e:
        logger.error(f"Error in {handler_name}: {{str(e)}}")
        return {{"success": False, "error": f"Error: {{str(e)}}"}}
'''
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the status of the MetaAgent.
        
        Returns:
            Dict containing status information
        """
        return {
            "status": "ready",
            "type": "meta",
            "tools_generated": len(self.generated_tools),
            "recent_tools": list(self.generated_tools.keys())[-5:] if self.generated_tools else []
        }
