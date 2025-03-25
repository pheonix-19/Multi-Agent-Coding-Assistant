import os
import argparse
import json
from dotenv import load_dotenv
from orchestrator import Orchestrator

def main():
    """Main entry point for the Autonomous Coding Assistant"""
    
    # Load environment variables
    load_dotenv()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Autonomous Coding Assistant')
    parser.add_argument('--task', type=str, help='The coding task description')
    parser.add_argument('--task-file', type=str, help='File containing the coding task description')
    parser.add_argument('--output', type=str, default='output', help='Output directory for the solution')
    args = parser.parse_args()
    
    # Get API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        return
    
    # Get task description
    task_description = ""
    if args.task:
        task_description = args.task
    elif args.task_file:
        try:
            with open(args.task_file, 'r') as f:
                task_description = f.read()
        except Exception as e:
            print(f"Error reading task file: {str(e)}")
            return
    else:
        task_description = input("Please enter your coding task description: ")
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output, exist_ok=True)
    
    # Initialize orchestrator
    orchestrator = Orchestrator(api_key)
    
    # Process the task
    print(f"Starting autonomous coding process for task: {task_description[:50]}...")
    result = orchestrator.process_task(task_description)
    
    # Save results
    save_results(result, args.output,orchestrator)
    
    print(f"\n✅ Autonomous coding complete! Results saved to {args.output} directory")
    print(f"Final code execution result: {'SUCCESS' if result['execution_result']['success'] else 'FAILED'}")

def save_results(result, output_dir, orchestrator):
    """Save all artifacts from the coding process"""
    
    # Save analysis
    with open(os.path.join(output_dir, 'analysis.json'), 'w') as f:
        json.dump(result['analysis'], f, indent=2)
    
    # Save initial codesum 
    language = result['initial_code'].get('language').lower()
    language_ext = orchestrator.get_file_extension(language)
    with open(os.path.join(output_dir, f'initial_code.{language}'), 'w') as f:
        f.write(result['initial_code'].get('code', ''))
    
    # Save test results
    with open(os.path.join(output_dir, 'test_results.json'), 'w') as f:
        json.dump(result['test_results'], f, indent=2)
    
    # Save final code
    with open(os.path.join(output_dir, f'final_code.{language_ext}'), 'w') as f:
        f.write(result['final_code'])
    
    # Save execution results
    with open(os.path.join(output_dir, 'execution_result.json'), 'w') as f:
        json.dump(result['execution_result'], f, indent=2)
    
    # Save full process report
    report = f"""
    # Autonomous Coding Assistant - Process Report
    
    ## Task Description
    {result['task_description']}
    
    ## Analysis Summary
    - Main Objective: {result['analysis'].get('main_objective', 'Not specified')}
    - Recommended Language: {result['analysis'].get('recommended_language', 'Not specified')}
    - Key Features: {', '.join(result['analysis'].get('key_features', []))}
    
    ## Initial Code Generation
    The initial code solution was generated in {result['initial_code'].get('language', 'Unknown')} language.
    
    ## Testing Results
    Overall Test Status: {'PASSED' if result['test_results'].get('passed', False) else 'FAILED'}
    
    Number of Test Cases: {len(result['test_results'].get('test_cases', []))}
    Passed Tests: {sum(1 for r in result['test_results'].get('results', []) if r.get('passed', False))}
    Failed Tests: {sum(1 for r in result['test_results'].get('results', []) if not r.get('passed', False))}
    
    ## Execution Results
    Exit Code: {result['execution_result'].get('exit_code', -1)}
    Success: {'Yes' if result['execution_result'].get('success', False) else 'No'}
    
    ## Output Preview
    ```
    {result['execution_result'].get('output', 'No output')[:500]}
    ```
    """
    
    with open(os.path.join(output_dir, 'report.md'), 'w') as f:
        f.write(report)

if __name__ == "__main__":
    main()