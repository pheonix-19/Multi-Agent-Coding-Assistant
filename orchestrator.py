import os
import json
import requests
import docker
from typing import Dict, List, Any
from agents.analyzer import AnalyzerAgent
from agents.writer import WriterAgent
from agents.tester import TesterAgent
from agents.debugger import DebuggerAgent
from docker.errors import DockerException
from docker import DockerClient
from docker.errors import DockerException
class Orchestrator:
    def __init__(self, openai_api_key: str):
        self.openai_api_key = openai_api_key
        try:
            self.docker_client = DockerClient(base_url="npipe:////./pipe/docker_engine")
        except DockerException as e:
            print(f"Error initializing Docker client: {e}")
            self.docker_client = None
        # Removed duplicate docker client initialization
        self.analyzer = AnalyzerAgent(openai_api_key)
        self.writer = WriterAgent(openai_api_key)
        self.tester = TesterAgent(openai_api_key)
        self.debugger = DebuggerAgent(openai_api_key)
        self.conversation_history = []
        
    def process_task(self, task_description: str) -> Dict[str, Any]:
        """Main method to process a coding task from start to finish"""
        self._add_to_history("user", task_description)
        
        # Step 1: Analyze the task
        analysis = self.analyzer.analyze_task(task_description, self.conversation_history)
        self._add_to_history("analyzer", analysis)
        print(f"✅ Task Analysis Complete")
        
        # Step 2: Generate initial code
        code_solution = self.writer.generate_code(analysis, self.conversation_history)
        self._add_to_history("writer", code_solution)
        print(f"✅ Initial Code Generated")
        
        # Step 3: Test the code
        test_results = self.tester.test_code(code_solution, analysis, self.conversation_history)
        self._add_to_history("tester", test_results)
        print(f"✅ Code Testing Complete")
        
        # Step 4: Debug if necessary
        if not test_results.get("passed", False):
            debug_results = self.debugger.debug_code(
                code_solution, 
                test_results, 
                analysis,
                self.conversation_history
            )
            self._add_to_history("debugger", debug_results)
            final_code = debug_results.get("fixed_code", code_solution)
            print(f"✅ Debugging Complete")
        else:
            final_code = code_solution.get("code", "")
            
        # Execute the code in Docker for safety
        execution_result = self._execute_in_docker(final_code)
        
        return {
            "task_description": task_description,
            "analysis": analysis,
            "initial_code": code_solution,
            "test_results": test_results,
            "final_code": final_code,
            "execution_result": execution_result
        }
    
    def _execute_in_docker(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Execute code safely in a Docker container"""
        # Check if Docker client is available
        if self.docker_client is None:
            return {
                "exit_code": -1,
                "output": "Docker is not available. Cannot execute code in a container.",
                "success": False
            }
            
        # Create a temporary file with the code
        temp_file = f"temp_code.{language}"
        with open(temp_file, "w") as f:
            f.write(code)
            
        try:
            # Run in a container with appropriate image based on language
            image_name = f"{language}:latest"
            
            container = self.docker_client.containers.run(
                image_name,
                command=f"{language} /{temp_file}",
                volumes={os.path.abspath(temp_file): {'bind': f'/{temp_file}', 'mode': 'ro'}},
                detach=True,
                mem_limit='100m',  # Limit resources for safety
                network_mode='none'  # No network access
            )
            
            # Get output with timeout
            result = container.wait(timeout=30)
            logs = container.logs().decode('utf-8')
            container.remove()
            
            return {
                "exit_code": result.get("StatusCode", -1),
                "output": logs,
                "success": result.get("StatusCode", -1) == 0
            }
            
        except Exception as e:
            return {
                "exit_code": -1,
                "output": f"Error executing code: {str(e)}",
                "success": False
            }
        finally:
            # Clean up
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    def _add_to_history(self, role: str, content: Dict[str, Any]) -> None:
        """Add interaction to conversation history"""
        self.conversation_history.append({
            "role": role,
            "content": content
        })