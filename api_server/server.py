from flask import Flask, request, jsonify
import docker
import uuid

app = Flask(__name__)

docker_client = docker.from_env()
nodes = {}

@app.route("/", methods=["GET"])
def index():
    return "KubeLite is running!", 200

@app.route("/favicon.ico")
def favicon():
    return "", 204

@app.route("/node/add", methods=["POST"])
def add_node():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Missing JSON body"}), 400

        cpu_cores = data.get("cpu_cores")
        if cpu_cores is None:
            return jsonify({"error": "cpu_cores field is required"}), 400

        try:
            cpu_cores_float = float(cpu_cores)
        except ValueError:
            return jsonify({"error": "cpu_cores must be a number"}), 400

        cpuset_cpus = data.get("cpuset_cpus")

        node_id = str(uuid.uuid4())[:8]
        container = docker_client.containers.run(
            image="python:3.8-slim",
            command="tail -f /dev/null",
            detach=True,
            name=f"kube_node_{node_id}",
            cpu_period=100000,
            cpu_quota=int(cpu_cores_float * 100000),
            cpuset_cpus=cpuset_cpus if cpuset_cpus else None
        )

        nodes[node_id] = {
            "container_id": container.id,
            "cpu_cores": cpu_cores_float,
            "cpuset_cpus": cpuset_cpus if cpuset_cpus else "Any",
            "status": "active",
            "pods": []
        }

        return jsonify({
            "message": "Node added successfully",
            "node_id": node_id,
            "container_id": container.id,
            "cpu_cores": cpu_cores_float,
            "cpuset_cpus": cpuset_cpus if cpuset_cpus else "Any",
            "status": "active"
        }), 200

    except Exception as e:
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500


@app.route("/nodes", methods=["GET"])
def list_nodes():
    return jsonify(nodes), 200

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8000)