"""The simplest possible Python script to run in Docker."""
import sys
import platform
import os

print("=" * 50)
print("  Hello from inside a Docker container!")
print("=" * 50)
print(f"  Python version : {sys.version.split()[0]}")
print(f"  OS             : {platform.system()} {platform.release()}")
print(f"  Architecture   : {platform.machine()}")
print(f"  User           : {os.getenv('USER', 'root')}")
print(f"  Working dir    : {os.getcwd()}")
print(f"  Home dir       : {os.path.expanduser('~')}")
print("=" * 50)
print()
print("This is NOT your laptop's Python.")
print("This is a completely isolated Linux environment.")
print()

# Compare with host
print("Try these yourself:")
print("  docker run -it hello-docker bash")
print("  → then: ls /  |  cat /etc/os-release  |  pip list  |  exit")
print()
print("  docker run hello-docker python -c \"print(2+2)\"")
print("  docker run hello-docker cat /etc/os-release")
