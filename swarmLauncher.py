import random
import string
import subprocess
import celery
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# Define a function to generate a random string of characters
def generate_random_string(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(length))

# Prefix for the worker name
worker_name_prefix = "agent-"

# Start the Celery workers with the generated hostname
workers = []
try:
    for _ in range(3):  # 启动3个worker
        worker_name = worker_name_prefix + generate_random_string(8)
        print(f"Starting worker with name: {worker_name}")
        
        worker = subprocess.Popen(
            f"celery -A celery_worker worker --loglevel=INFO --hostname={worker_name} --pool=solo",
            shell=True,
            env=os.environ.copy()  # 确保环境变量被传递给子进程
        )
        workers.append(worker)
        print(f"Worker {worker_name} started with PID: {worker.pid}")

    # 等待所有worker完成
    for worker in workers:
        worker.wait()
except KeyboardInterrupt:
    print("\nShutting down workers...")
    for worker in workers:
        worker.terminate()
    print("All workers terminated")
except KeyError as e:
    print(f"Error: Required environment variable {str(e)} is not set")
except Exception as e:
    print(f"Error occurred: {e}")
    for worker in workers:
        worker.terminate()
