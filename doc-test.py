import docker
import platform

try:
    # Use named pipe for Windows, default for other platforms
    if platform.system() == "Windows":
        client = docker.DockerClient(base_url="npipe:////./pipe/docker_engine")
    else:
        client = docker.DockerClient()  # Default for non-Windows systems

    # Test Docker connection
    print("Docker client version:", client.version())
except docker.errors.DockerException as e:
    print(f"Error connecting to Docker: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")