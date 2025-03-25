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
import re
class Orchestrator:
    def __init__(self, openai_api_key: str):
        self.openai_api_key = openai_api_key
        try:
            self.docker_client = docker.DockerClient(base_url="tcp://localhost:2375")
            print("Connected to Docker using TCP connection")
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
    def get_file_extension(self, language):
        """Map programming language to appropriate file extension"""
        extensions = {
            "python": "py",
            "javascript": "js",
            "java": "java",
            "c": "c",
            "cpp": "cpp",
            "ruby": "rb",
            # Add more as needed
        }
        return extensions.get(language.lower(), language.lower())
    def get_execution_command(self, language, file_path):
        """Get the appropriate command to execute code in the given language"""
        commands = {
            "python": ["python", file_path],
            "javascript": ["node", file_path],
            "java": ["java", file_path.replace(".java", "")],
            "ruby": ["ruby", file_path],
            # Add more as needed
        }
        return commands.get(language.lower(), [language.lower(), file_path])
    
    def _execute_in_docker(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Execute code safely in a Docker container"""
        # Check if Docker client is available
        if self.docker_client is None:
            return {
                "exit_code": -1,
                "output": "Docker is not available. Cannot execute code in a container.",
                "success": False
            }
        code = code.strip("`")
        
        # Use proper file extension based on language
        file_extension = self.get_file_extension(language)
        temp_file_name = f"temp_code.{file_extension}"
        container_file_path = f"/app/{temp_file_name}"
        
        # # Handle input() function calls for non-interactive environments
        if "input(" in code and language.lower() == "python":
            # Use regex to replace input() calls with mock values
            def input_replacement(match):
                prompt = match.group(1) if match.group(1) else '"Input requested"'
                return f'(lambda p: print(p) or "5")({prompt})'
            
            # Replace all input() calls
            code = re.sub(r'input\((.*?)\)', input_replacement, code)
        
        # Create a temporary file with the code
        with open(temp_file_name, "w") as f:
            f.write(code)
            
        try:
            # Run in a container with appropriate image based on language
            image_name = f"{language}:latest"
            
            # Get the appropriate command for the language
            execution_command = self.get_execution_command(language, container_file_path)
            
            # Create and run the container
            container = self.docker_client.containers.run(
                image_name,
                command=execution_command,
                volumes={
                    os.path.abspath(temp_file_name): {
                        'bind': container_file_path, 
                        'mode': 'ro'
                    }
                },
                working_dir="/app",  # Set working directory
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
            if os.path.exists(temp_file_name):
                os.remove(temp_file_name)
    
    def _add_to_history(self, role: str, content: Dict[str, Any]) -> None:
        """Add interaction to conversation history"""
        self.conversation_history.append({
            "role": role,
            "content": content
        })