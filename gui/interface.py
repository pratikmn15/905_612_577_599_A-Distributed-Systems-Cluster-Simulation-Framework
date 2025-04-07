import tkinter as tk
from tkinter import messagebox
import requests

API_URL = "http://127.0.0.1:8000"

def add_node():
    try:
        cores = entry.get()
        if not cores:
            raise ValueError
        response = requests.post(f"{API_URL}/node/add", json={"cpu_cores": cores})
        if response.status_code == 200:
            messagebox.showinfo("Success", f"Node added!\n{response.json()}")
        else:
            messagebox.showerror("Error", response.json().get("error", "Unknown error"))
    except ValueError:
        messagebox.showwarning("Invalid Input", "Enter a valid number of CPU cores.")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def list_nodes():
    try:
        response = requests.get(f"{API_URL}/nodes")
        if response.status_code == 200:
            nodes = response.json()
            if nodes:
                info = "\n".join([f"ID: {k}, Cores: {v['cpu_cores']}, Status: {v['status']}" for k, v in nodes.items()])
            else:
                info = "No nodes found."
            messagebox.showinfo("Registered Nodes", info)
        else:
            messagebox.showerror("Error", "Unable to fetch nodes.")
    except Exception as e:
        messagebox.showerror("Error", str(e))

# GUI setup
root = tk.Tk()
root.title("CC KubeProject")
root.geometry("300x200")

label = tk.Label(root, text="Enter CPU cores:")
label.pack(pady=5)

entry = tk.Entry(root)
entry.pack(pady=5)

add_btn = tk.Button(root, text="Add Node", command=add_node)
add_btn.pack(pady=5)

list_btn = tk.Button(root, text="List Nodes", command=list_nodes)
list_btn.pack(pady=5)

root.mainloop()
