import openai
import json
from typing import Dict, List, Any
import openai 
import os

class AnalyzerAgent:
    def __init__(self, openai_api_key: str):
        self.api_key = openai_api_key
        openai.api_key = openai_api_key
        self.client = openai
        
    def analyze_task(self, task_description: str, conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze the coding task and provide structured requirements"""
        
        # Construct prompt for the analyzer
        prompt = f"""
        You are a specialized AI task analyzer. Your role is to analyze programming tasks and break them down into clear specifications.
        
        Task Description:
        {task_description}
        
        Please provide a structured analysis including:
        1. Main objective
        2. Programming language recommendation with justification
        3. Key features required
        4. Potential libraries/frameworks to use
        5. Expected inputs and outputs
        6. Potential edge cases to handle
        7. Breaking down the task into smaller implementation steps
        
        Return your analysis in a structured format.
        """
        
        # Call GPT-4 with function calling
        #self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        response = self.client.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            functions=[{
                "name": "provide_task_analysis",
                "description": "Provide structured analysis of the programming task",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "main_objective": {"type": "string"},
                        "recommended_language": {"type": "string"},
                        "language_justification": {"type": "string"},
                        "key_features": {"type": "array", "items": {"type": "string"}},
                        "recommended_libraries": {"type": "array", "items": {"type": "string"}},
                        "inputs": {"type": "array", "items": {"type": "string"}},
                        "outputs": {"type": "array", "items": {"type": "string"}},
                        "edge_cases": {"type": "array", "items": {"type": "string"}},
                        "implementation_steps": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["main_objective", "recommended_language", "key_features", 
                                "implementation_steps"]
                }
            }],
            function_call={"name": "provide_task_analysis"}
        )
        
        # Extract and parse the analysis
        function_call = response.choices[0].message.function_call
        analysis = json.loads(function_call.arguments)
        
        return analysis