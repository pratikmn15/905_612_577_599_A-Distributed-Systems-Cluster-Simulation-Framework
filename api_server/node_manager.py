import subprocess
import json
import os
from utils.config import NODES_DB, NODE_COUNTER_FILE

# Initialize node counter
if not os.path.exists(NODE_COUNTER_FILE):
    with open(NODE_COUNTER_FILE, 'w') as f:
        f.write('0')


def get_next_node_id():
    with open(NODE_COUNTER_FILE, 'r+') as f:
        count = int(f.read()) + 1
        f.seek(0)
        f.write(str(count))
        f.truncate()
    return f'N{count}'

def add_node(cpu_cores):
    node_id = get_next_node_id()
    container_name = f"node_{node_id}"

    subprocess.run(["docker", "run", "-dit", "--name", container_name, "python:3.8-slim", "bash"])

    # Store in DB
    if os.path.exists(NODES_DB):
        with open(NODES_DB, 'r') as f:
            nodes = json.load(f)
    else:
        nodes = {}

    nodes[node_id] = {
        'container': container_name,
        'cpu': cpu_cores,
        'status': 'Healthy',
        'pods': []
    }

    with open(NODES_DB, 'w') as f:
        json.dump(nodes, f, indent=2)

    return node_id
