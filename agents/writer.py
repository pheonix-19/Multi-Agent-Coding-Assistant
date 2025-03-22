import openai
import json
from typing import Dict, List, Any

class WriterAgent:
    def __init__(self, openai_api_key: str):
        self.api_key = openai_api_key
        openai.api_key = openai_api_key
        
    def generate_code(self, analysis: Dict[str, Any], conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate code based on the task analysis"""
        
        # Extract key information from analysis
        language = analysis.get("recommended_language", "python")
        features = analysis.get("key_features", [])
        libraries = analysis.get("recommended_libraries", [])
        steps = analysis.get("implementation_steps", [])
        
        # Construct prompt for the writer
        prompt = f"""
        You are a specialized AI code writer. Your job is to write high-quality, readable, and efficient code 
        based on the given analysis.
        
        Task Analysis:
        - Main Objective: {analysis.get('main_objective', 'Not specified')}
        - Programming Language: {language}
        - Key Features Required: {', '.join(features)}
        - Recommended Libraries: {', '.join(libraries)}
        - Implementation Steps: {' '.join([f"Step {i+1}: {step}" for i, step in enumerate(steps)])}
        
        Write complete, working code that fulfills all requirements. Include:
        1. Proper imports
        2. Clear comments
        3. Error handling
        4. Well-structured functions/classes
        5. Type hints (if applicable in the language)
        
        Return the code and explanation of your implementation decisions.
        """
        
        # Call GPT-4 with function calling
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            functions=[{
                "name": "provide_code_solution",
                "description": "Provide code solution for the task",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string"},
                        "language": {"type": "string"},
                        "explanation": {"type": "string"},
                        "file_structure": {
                            "type": "array", 
                            "items": {
                                "type": "object",
                                "properties": {
                                    "filename": {"type": "string"},
                                    "content": {"type": "string"}
                                }
                            }
                        }
                    },
                    "required": ["code", "language", "explanation"]
                }
            }],
            function_call={"name": "provide_code_solution"}
        )
        
        # Extract and parse the code solution
        function_call = response.choices[0].message.function_call
        code_solution = json.loads(function_call.arguments)
        
        return code_solution