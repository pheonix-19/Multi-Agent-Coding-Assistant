import docker

try:
    client = docker.DockerClient(base_url="npipe:////./pipe/docker_engine")
    print(client.version())
except Exception as e:
    print(f"Error connecting to Docker: {e}")