import docker
import platform
import os

def test_docker_connection():
    """Test multiple ways to connect to Docker"""
    connection_methods = [
        ("Default from environment", lambda: docker.from_env()),
        ("Windows named pipe", lambda: docker.DockerClient(base_url="npipe:////./pipe/docker_engine")),
        ("TCP connection", lambda: docker.DockerClient(base_url="tcp://localhost:2375")),
        ("Socket connection", lambda: docker.DockerClient(base_url="unix:///var/run/docker.sock"))
    ]
    
    for name, connection_method in connection_methods:
        try:
            print(f"\nTrying {name}...")
            client = connection_method()
            version = client.version()
            print(f"✅ SUCCESS with {name}")
            print(f"Docker version: {version.get('Version', 'unknown')}")
            print(f"API version: {version.get('ApiVersion', 'unknown')}")
            return client
        except Exception as e:
            print(f"❌ FAILED with {name}: {e}")
    
    print("\n❌ All connection methods failed")
    return None

if __name__ == "__main__":
    print("Testing Docker connectivity...")
    client = test_docker_connection()
    if client:
        print("\n🐳 Docker is working correctly!")
    else:
        print("\n⚠️ Could not connect to Docker")