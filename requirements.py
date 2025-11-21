import subprocess

# Generate requirements.txt from your current environment
subprocess.run(["pip", "freeze", "--local", ">", "requirements.txt"], shell=True)

print("requirements.txt created!")