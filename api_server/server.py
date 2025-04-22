from flask import Flask, request, jsonify
import docker
import uuid
import threading
import time

app = Flask(__name__)
docker_client = docker.from_env()

# Data structures to track nodes, pods, and heartbeats
nodes = {}  # Stores node information
pods = {}   # Stores pod information separately for recovery
heartbeats = {}  # Tracks last heartbeat time for each node

class PodScheduler:
    @staticmethod
    def select_node(cpu_requirement):
        """Select the best node for pod placement based on available resources"""
        best_node = None
        min_remaining_cpu = float('inf')
        
        for node_id, node_info in nodes.items():
            # Skip failed nodes
            if node_info["status"] != "active":
                continue
                
            # Calculate used CPU on this node
            used_cpu = sum(float(pod["cpu_cores"]) for pod in node_info.get("pods", []))
            # Calculate available CPU
            available_cpu = float(node_info["cpu_cores"]) - used_cpu
            
            # Check if this node has enough resources
            if available_cpu >= float(cpu_requirement):
                # Use best-fit strategy: choose the node with least remaining resources after placement
                remaining_cpu = available_cpu - float(cpu_requirement)
                if remaining_cpu < min_remaining_cpu:
                    min_remaining_cpu = remaining_cpu
                    best_node = node_id
        
        return best_node

def simulate_heartbeats():
    """
    Simulate heartbeat signals from active nodes
    In a real implementation, nodes would send their own heartbeats
    """
    while True:
        for node_id, node_info in list(nodes.items()):
            if node_info["status"] == "active":
                # Update heartbeat for active nodes
                heartbeats[node_id] = time.time()
                print(f"Simulated heartbeat from node {node_id[:8]}...")
        time.sleep(5)  # Send heartbeats every 5 seconds

def monitor_heartbeats():
    """Monitor node heartbeats and handle recovery of failed nodes"""
    while True:
        time.sleep(10)  # Check every 10 seconds
        current_time = time.time()
        
        for node_id in list(nodes.keys()):
            # Skip nodes already marked as failed
            if nodes[node_id]["status"] == "failed":
                continue
                
            # Check if we have a heartbeat for this node
            if node_id not in heartbeats:
                heartbeats[node_id] = current_time  # Initialize if missing
                continue
                
            # Check if heartbeat is too old
            if current_time - heartbeats[node_id] > 15:  # Node timeout after 15 seconds
                print(f"Node {node_id[:8]}... unresponsive. Marking as failed...")
                
                # Mark node as failed
                nodes[node_id]["status"] = "failed"
                
                # Get pods running on the failed node
                failed_pods = nodes[node_id].get("pods", [])
                
                # Remove pods from failed node
                nodes[node_id]["pods"] = []
                
                # Attempt to reschedule each pod
                for pod in failed_pods:
                    pod_id = pod["pod_id"]
                    cpu_cores = pod["cpu_cores"]
                    
                    print(f"Rescheduling pod {pod_id[:8]}... (CPU: {cpu_cores})...")
                    
                    # Try to reschedule the pod
                    new_node = PodScheduler.select_node(cpu_cores)
                    if new_node:
                        # Add pod to new node
                        nodes[new_node]["pods"].append({"pod_id": pod_id, "cpu_cores": cpu_cores})
                        # Update pod's node assignment
                        pods[pod_id]["node_id"] = new_node
                        pods[pod_id]["status"] = "running"
                        print(f"Pod {pod_id[:8]}... rescheduled to node {new_node[:8]}...")
                    else:
                        # Mark pod as pending if no suitable node found
                        pods[pod_id]["status"] = "pending"
                        pods[pod_id]["node_id"] = None
                        print(f"Pod {pod_id[:8]}... marked as pending - no suitable node found")

# Start the heartbeat simulation and monitoring threads
heartbeat_sim_thread = threading.Thread(target=simulate_heartbeats, daemon=True)
heartbeat_sim_thread.start()

heartbeat_monitor_thread = threading.Thread(target=monitor_heartbeats, daemon=True)
heartbeat_monitor_thread.start()

@app.route("/", methods=["GET"])
def index():
    return "API Server is running", 200

@app.route("/nodes", methods=["GET"])
def get_nodes():
    # Add heartbeat information to response
    nodes_info = {}
    for node_id, node_data in nodes.items():
        nodes_info[node_id] = node_data.copy()
        if node_id in heartbeats:
            nodes_info[node_id]["last_heartbeat"] = heartbeats[node_id]
            nodes_info[node_id]["heartbeat_age"] = time.time() - heartbeats[node_id]
    
    return jsonify({"nodes": nodes_info}), 200

@app.route("/pods", methods=["GET"])
def get_pods():
    return jsonify({"pods": pods}), 200

@app.route("/node/add", methods=["POST"])
def add_node():
    data = request.get_json()
    cpu_cores = data.get("cpu_cores")
    
    if not cpu_cores:
        return jsonify({"error": "Missing CPU cores specification"}), 400
    
    try:
        cpu_cores = float(cpu_cores)
    except ValueError:
        return jsonify({"error": "CPU cores must be a number"}), 400
    
    node_id = str(uuid.uuid4())
    
    try:
        # Launch a container to simulate the node
        container = docker_client.containers.run(
            image="python:3.8-slim",
            command="python -c \"import time; time.sleep(3600)\"",
            detach=True,
            name=f"node_{node_id[:8]}",
            cpu_period=100000,
            cpu_quota=int(cpu_cores * 100000)
        )
        
        # Register the node
        nodes[node_id] = {
            "container_id": container.id, 
            "cpu_cores": cpu_cores, 
            "status": "active", 
            "pods": []
        }
        
        # Initialize heartbeat
        heartbeats[node_id] = time.time()
        
        print(f"Added new node {node_id[:8]}... with {cpu_cores} CPU cores")
        
        return jsonify({
            "message": "Node added successfully", 
            "node_id": node_id, 
            "container_id": container.id
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to add node: {str(e)}"}), 500

@app.route("/node/heartbeat/<node_id>", methods=["POST"])
def node_heartbeat(node_id):
    if node_id in nodes:
        heartbeats[node_id] = time.time()
        return jsonify({"message": "Heartbeat received"}), 200
    return jsonify({"error": "Node not found"}), 404

@app.route("/pod/request", methods=["POST"])
def request_pod():
    data = request.get_json()
    cpu_cores = data.get("cpu_cores")

    if cpu_cores is None:
        return jsonify({"error": "Missing 'cpu_cores' field"}), 400
    
    try:
        cpu_cores = float(cpu_cores)
    except ValueError:
        return jsonify({"error": "CPU cores must be a number"}), 400

    # Use the pod scheduler to select the best node
    selected_node = PodScheduler.select_node(cpu_cores)
    
    if selected_node:
        # Generate pod ID
        pod_id = str(uuid.uuid4())
        
        # Update node's pod list
        pod_data = {"pod_id": pod_id, "cpu_cores": cpu_cores}
        nodes[selected_node]["pods"].append(pod_data)
        
        # Store pod information for recovery
        pods[pod_id] = {
            "node_id": selected_node,
            "cpu_cores": cpu_cores,
            "status": "running",
            "created_at": time.time()  # Track creation time
        }
        
        print(f"Pod {pod_id[:8]}... scheduled on node {selected_node[:8]}... (CPU: {cpu_cores})")
        
        return jsonify({
            "message": "Pod scheduled successfully", 
            "node_id": selected_node, 
            "pod_id": pod_id
        }), 200
    
    return jsonify({"error": "No suitable node found with enough resources"}), 400

@app.route("/pod/remove/<pod_id>", methods=["DELETE"])
def remove_pod(pod_id):
    if pod_id not in pods:
        return jsonify({"error": "Pod not found"}), 404
    
    node_id = pods[pod_id]["node_id"]
    
    if node_id in nodes:
        # Remove pod from node's pod list
        nodes[node_id]["pods"] = [pod for pod in nodes[node_id]["pods"] if pod["pod_id"] != pod_id]
    
    # Remove pod from pods dictionary
    del pods[pod_id]
    
    print(f"Pod {pod_id[:8]}... removed successfully")
    
    return jsonify({"message": f"Pod {pod_id} removed successfully"}), 200

@app.route("/cluster/status", methods=["GET"])
def cluster_status():
    """Get overall cluster status including resources"""
    total_cpu = 0
    used_cpu = 0
    active_nodes = 0
    failed_nodes = 0
    
    for node_id, node_info in nodes.items():
        if node_info["status"] == "active":
            active_nodes += 1
            node_cpu = float(node_info["cpu_cores"])
            total_cpu += node_cpu
            
            # Calculate used CPU on this node
            node_used_cpu = sum(float(pod["cpu_cores"]) for pod in node_info.get("pods", []))
            used_cpu += node_used_cpu
        else:
            failed_nodes += 1
    
    return jsonify({
        "active_nodes": active_nodes,
        "failed_nodes": failed_nodes,
        "total_pods": len(pods),
        "total_cpu": total_cpu,
        "used_cpu": used_cpu,
        "available_cpu": total_cpu - used_cpu,
        "utilization_percentage": (used_cpu / total_cpu * 100) if total_cpu > 0 else 0
    }), 200

# For testing: Endpoint to manually fail a node
@app.route("/node/fail/<node_id>", methods=["POST"])
def fail_node(node_id):
    if node_id not in nodes:
        return jsonify({"error": "Node not found"}), 404
    
    if nodes[node_id]["status"] == "failed":
        return jsonify({"message": "Node is already marked as failed"}), 200
    
    # Mark node as failed
    nodes[node_id]["status"] = "failed"
    
    print(f"Manually failing node {node_id[:8]}...")
    
    # Get pods running on the failed node
    failed_pods = nodes[node_id].get("pods", [])
    
    # Remove pods from failed node
    nodes[node_id]["pods"] = []
    
    # Attempt to reschedule each pod
    for pod in failed_pods:
        pod_id = pod["pod_id"]
        cpu_cores = pod["cpu_cores"]
        
        print(f"Rescheduling pod {pod_id[:8]}... (CPU: {cpu_cores})...")
        
        # Try to reschedule the pod
        new_node = PodScheduler.select_node(cpu_cores)
        if new_node:
            # Add pod to new node
            nodes[new_node]["pods"].append({"pod_id": pod_id, "cpu_cores": cpu_cores})
            # Update pod's node assignment
            pods[pod_id]["node_id"] = new_node
            pods[pod_id]["status"] = "running"
            print(f"Pod {pod_id[:8]}... rescheduled to node {new_node[:8]}...")
        else:
            # Mark pod as pending if no suitable node found
            pods[pod_id]["status"] = "pending"
            pods[pod_id]["node_id"] = None
            print(f"Pod {pod_id[:8]}... marked as pending - no suitable node found")
    
    return jsonify({"message": f"Node {node_id} marked as failed and pods rescheduled"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)