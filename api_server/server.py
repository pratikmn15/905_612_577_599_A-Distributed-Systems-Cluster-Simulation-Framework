from flask import Flask, request, jsonify
from utils.config import NODES_DB
from api_server.node_manager import add_node

app = Flask(__name__)

@app.route('/add_node', methods=['POST'])
def handle_add_node():
    data = request.get_json()
    cpu = data.get('cpu')
    if not cpu:
        return jsonify({'error': 'CPU core count is required'}), 400
    node_id = add_node(cpu)
    return jsonify({'message': f'Node {node_id} added successfully', 'node_id': node_id})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)