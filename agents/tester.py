import openai
import json
import tempfile
import subprocess
import os
from typing import Dict, List, Any
import openai

class TesterAgent:
    def __init__(self, openai_api_key: str):
        self.api_key = openai_api_key
        openai.api_key = openai_api_key
        self.client = openai
        
    def test_code(self, code_solution: Dict[str, Any], analysis: Dict[str, Any], 
                  conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate and run tests for the provided code"""
        
        # Extract code and language
        code = code_solution.get("code", "")
        language = code_solution.get("language", "python")
        
        # Generate test cases
        test_cases = self._generate_test_cases(code, analysis, language)
        
        # Run the tests
        test_results = self._run_tests(code, test_cases, language)
        
        return {
            "passed": test_results.get("all_passed", False),
            "test_cases": test_cases.get("test_cases", []),
            "results": test_results.get("results", []),
            "summary": test_results.get("summary", ""),
            "suggestions": test_results.get("suggestions", [])
        }
    
    def _generate_test_cases(self, code: str, analysis: Dict[str, Any], language: str) -> Dict[str, Any]:
        """Generate appropriate test cases for the code"""
        
        # Construct prompt for test case generation
        prompt = f"""
        You are a specialized AI test engineer. Generate comprehensive test cases for the following code.
        
        Code:
        ```{language}
        {code}
        ```
        
        Task Analysis:
        - Main Objective: {analysis.get('main_objective', 'Not specified')}
        - Expected Inputs: {', '.join(analysis.get('inputs', ['Not specified']))}
        - Expected Outputs: {', '.join(analysis.get('outputs', ['Not specified']))}
        - Edge Cases to Handle: {', '.join(analysis.get('edge_cases', ['None specified']))}
        
        Create test cases that cover:
        1. Basic functionality
        2. Edge cases
        3. Error handling
        4. Performance (if relevant)
        
        For each test case, provide:
        - Test name/description
        - Input values
        - Expected output/behavior
        - The code to run the test (appropriate for the language)
        """
        
        # Call GPT-4 with function calling
        #self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        response = self.client.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            functions=[{
                "name": "provide_test_cases",
                "description": "Provide test cases for the code",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "test_cases": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "description": {"type": "string"},
                                    "inputs": {"type": "object"},
                                    "expected_output": {"type": "string"},
                                    "test_code": {"type": "string"}
                                }
                            }
                        },
                        "test_file": {"type": "string"},
                        "language": {"type": "string"}
                    },
                    "required": ["test_cases", "test_file", "language"]
                }
            }],
            function_call={"name": "provide_test_cases"}
        )
        
        # Extract and parse the test cases
        function_call = response.choices[0].message.function_call
        test_cases = json.loads(function_call.arguments)
        
        return test_cases
    
    def _run_tests(self, code: str, test_cases: Dict[str, Any], language: str) -> Dict[str, Any]:
        """Run the generated tests against the code"""
        # This would be implemented with Docker for safe execution
        
        # For demo purposes, using a simplified approach
        results = []
        all_passed = True
        
        # Create temporary directory for code and tests
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write code to file
            code_file = os.path.join(temp_dir, f"code.{language}")
            with open(code_file, "w") as f:
                f.write(code)
            
            # Write test file
            test_file = os.path.join(temp_dir, f"test.{language}")
            with open(test_file, "w") as f:
                f.write(test_cases.get("test_file", ""))
            
            # Run tests based on language
            if language == "python":
                try:
                    result = subprocess.run(
                        ["python", test_file],
                        cwd=temp_dir,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    for test_case in test_cases.get("test_cases", []):
                        test_name = test_case.get("name", "Unknown test")
                        
                        # Check if test name appears in output with "PASS"
                        if f"{test_name}: PASS" in result.stdout:
                            results.append({
                                "test_name": test_name,
                                "passed": True,
                                "output": "Test passed successfully"
                            })
                        else:
                            all_passed = False
                            # Extract error message if any
                            error_lines = [line for line in result.stdout.split('\n') 
                                         if test_name in line and "FAIL" in line]
                            error_msg = error_lines[0] if error_lines else "Test failed"
                            
                            results.append({
                                "test_name": test_name,
                                "passed": False,
                                "output": error_msg
                            })
                            
                except Exception as e:
                    all_passed = False
                    results.append({
                        "test_name": "Test execution",
                        "passed": False,
                        "output": f"Error running tests: {str(e)}"
                    })
            
            # Handle other languages similarly
        
        # Generate summary and suggestions
        summary = "All tests passed successfully!" if all_passed else "Some tests failed."
        suggestions = []
        
        if not all_passed:
            # Generate suggestions based on failed tests
            failed_tests = [r for r in results if not r.get("passed", False)]
            prompt = f"""
            You are a specialized AI test analyst. The following tests have failed:
            
            {json.dumps(failed_tests, indent=2)}
            
            For the code:
            ```{language}
            {code}
            ```
            
            Provide suggestions on how to fix the issues.
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}]
            )
            
            suggestions = response.choices[0].message.content.split("\n")
        
        return {
            "all_passed": all_passed,
            "results": results,
            "summary": summary,
            "suggestions": suggestions
        }