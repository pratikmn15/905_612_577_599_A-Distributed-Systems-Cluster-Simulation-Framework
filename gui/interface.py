import tkinter as tk
from tkinter import messagebox
import requests

def add_node():
    try:
        cpu = int(cpu_entry.get())
        response = requests.post('http://localhost:5000/add_node', json={'cpu': cpu})
        if response.status_code == 200:
            node_id = response.json().get('node_id')
            messagebox.showinfo('Success', f'Node {node_id} added successfully')
        else:
            messagebox.showerror('Error', response.json().get('error'))
    except Exception as e:
        messagebox.showerror('Error', str(e))

app = tk.Tk()
app.title("Cluster Node Manager")
app.geometry("300x150")

tk.Label(app, text="CPU Cores:").pack(pady=10)
cpu_entry = tk.Entry(app)
cpu_entry.pack()

tk.Button(app, text="Add Node", command=add_node).pack(pady=20)

app.mainloop()