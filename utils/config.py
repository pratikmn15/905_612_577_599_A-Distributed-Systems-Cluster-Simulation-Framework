import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NODES_DB = {}
NODE_COUNTER_FILE = os.path.join(BASE_DIR, 'node_counter.txt')