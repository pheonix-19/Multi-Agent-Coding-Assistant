import openai
import json
from typing import Dict, List, Any

class DebuggerAgent:
    def __init__(self, openai_api_key: str):
        self.api_key = openai_api_key
        openai.api_key = openai_api_key
        
    def debug_code(self, code_solution: Dict[str, Any], test_results: Dict[str, Any], 
                  analysis: Dict[str, Any], conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Debug the code based on test results"""
        
        # Extract code and language
        code = code_solution.get("code", "")
        language = code_solution.get("language", "python")
        
        # Extract failed tests and suggestions
        failed_tests = [test for test in test_results.get("results", []) 
                       if not test.get("passed", True)]
        suggestions = test_results.get("suggestions", [])
        
        # Construct prompt for debugging
        prompt = f"""
        You are a specialized AI debugger. Fix the following code based on the failed test results.
        
        Original Code:
        ```{language}
        {code}
        ```
        
        Failed Tests:
        {json.dumps(failed_tests, indent=2)}
        
        Suggestions from Test Analysis:
        {' '.join(suggestions)}
        
        Task Analysis:
        - Main Objective: {analysis.get('main_objective', 'Not specified')}
        
        Fix the code to make all tests pass. Explain your changes.
        """
        
        # Call GPT-4 with function calling
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            functions=[{
                "name": "provide_fixed_code",
                "description": "Provide fixed code that addresses the identified issues",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "fixed_code": {"type": "string"},
                        "explanation": {"type": "string"},
                        "changes_made": {
                            "type": "array", 
                            "items": {
                                "type": "object",
                                "properties": {
                                    "issue": {"type": "string"},
                                    "solution": {"type": "string"}
                                }
                            }
                        }
                    },
                    "required": ["fixed_code", "explanation", "changes_made"]
                }
            }],
            function_call={"name": "provide_fixed_code"}
        )
        
        # Extract and parse the debug results
        function_call = response.choices[0].message.function_call
        debug_results = json.loads(function_call.arguments)
        
        return debug_results