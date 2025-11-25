import subprocess
import sys

result = subprocess.run(
    [sys.executable, "-m", "rag_pipline.test_pipeline"],
    capture_output=True,
    text=True,
    cwd=r"C:\Users\23add\workspace\Nexus"
)

print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
