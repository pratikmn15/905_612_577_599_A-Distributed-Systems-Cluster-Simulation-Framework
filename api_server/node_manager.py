import subprocess
import json
import os
import requests
import messagebox
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

def add_node():
    try:
        cores = int(entry.get())
        if cores <= 0:
            raise ValueError("CPU cores must be positive.")
        headers = {"Content-Type": "application/json"}
        response = requests.post(f"{API_URL}/add_node", json={"cpu_cores": cores}, headers=headers)
        if response.status_code == 200:
            messagebox.showinfo("Success", "Node added successfully!")
            entry.delete(0, tk.END)  # Clear input after success
        else:
            messagebox.showerror("Error", f"Failed to add node:\n{response.text}")
    except ValueError:
        messagebox.showwarning("Invalid Input", "Please enter a valid number of CPU cores.")
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Connection Error", f"Cannot reach server:\n{e}")

