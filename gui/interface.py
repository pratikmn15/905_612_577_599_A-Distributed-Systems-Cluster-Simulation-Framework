import requests
import tkinter as tk
from tkinter import scrolledtext, messagebox, StringVar, ttk
import time
import threading
import json
from queue import Queue

class KubernetesSimulationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Kubernetes Simulation System")
        self.root.geometry("800x700")
        self.api_url = "http://localhost:8000"
        
        # Queue for communication between threads
        self.update_queue = Queue()

        # Status variables
        self.status_var = StringVar()
        self.status_var.set("Server Status: Unknown")
        self.cluster_status_var = StringVar()
        self.cluster_status_var.set("Cluster: N/A")
        
        # Create UI elements
        self.setup_ui()
        
        # # Start server status checker
        # self.check_server_status() # Initial check
        
        # Start background thread for API calls and auto-refresh
        self.api_thread = threading.Thread(target=self.background_api_worker, daemon=True)
        self.api_thread.start()

        # Start processing updates from the queue in the main thread
        self.process_updates()
    
    def setup_ui(self):
        # Status bar frame
        status_frame = tk.Frame(self.root, bd=1, relief=tk.SUNKEN)
        status_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        # Server status label
        self.status_label = tk.Label(status_frame, textvariable=self.status_var, font=("Helvetica", 10), anchor="w")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # Cluster status label
        self.cluster_status_label = tk.Label(status_frame, textvariable=self.cluster_status_var, font=("Helvetica", 10), anchor="e")
        self.cluster_status_label.pack(side=tk.RIGHT, padx=5)
        
        # Title
        title_label = tk.Label(self.root, text="Kubernetes Simulation System", font=("Helvetica", 16, "bold"))
        title_label.grid(row=1, column=0, columnspan=2, pady=10)
        
        # Notebook for tabbed interface
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        
        # Create tabs
        self.nodes_tab = ttk.Frame(self.notebook)
        self.pods_tab = ttk.Frame(self.notebook)
        self.cluster_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.nodes_tab, text="Nodes")
        self.notebook.add(self.pods_tab, text="Pods")
        self.notebook.add(self.cluster_tab, text="Cluster Status")
        
        # Set up nodes tab
        self.setup_nodes_tab()
        
        # Set up pods tab
        self.setup_pods_tab()
        
        # Set up cluster tab
        self.setup_cluster_tab()
        
        # Make the window resizable
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(2, weight=1)
    
    def setup_nodes_tab(self):
        # Button frame
        button_frame = tk.Frame(self.nodes_tab)
        button_frame.grid(row=0, column=0, columnspan=2, pady=5, sticky="ew")
        
        # Button to fetch nodes (now triggers background refresh)
        fetch_nodes_button = tk.Button(button_frame, text="Refresh Nodes", command=lambda: self.trigger_refresh('nodes'), width=15, bg="#4CAF50", fg="white")
        fetch_nodes_button.pack(side=tk.LEFT, padx=5)
        
        # Text area for node information
        self.nodes_text_area = scrolledtext.ScrolledText(self.nodes_tab, wrap=tk.WORD, width=90, height=20)
        self.nodes_text_area.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        
        # Node creation frame
        node_create_frame = tk.LabelFrame(self.nodes_tab, text="Add New Node", padx=10, pady=10)
        node_create_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        
        # CPU cores input
        cpu_cores_label = tk.Label(node_create_frame, text="CPU Cores:", font=("Helvetica", 11))
        cpu_cores_label.grid(row=0, column=0, padx=10, pady=5)
        
        self.cpu_cores_entry = tk.Entry(node_create_frame, width=10)
        self.cpu_cores_entry.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        
        # Add node button
        add_node_button = tk.Button(node_create_frame, text="Add Node", command=self.add_node, width=15, bg="#2196F3", fg="white")
        add_node_button.grid(row=0, column=2, padx=10, pady=5)
        
        # Node actions frame
        node_actions_frame = tk.LabelFrame(self.nodes_tab, text="Node Actions", padx=10, pady=10)
        node_actions_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        
        # Node ID input for actions
        node_id_label = tk.Label(node_actions_frame, text="Node ID:", font=("Helvetica", 11))
        node_id_label.grid(row=0, column=0, padx=10, pady=5)
        
        self.node_id_entry = tk.Entry(node_actions_frame, width=36)
        self.node_id_entry.grid(row=0, column=1, padx=10, pady=5)
        
        # Fail node button (for testing)
        fail_node_button = tk.Button(node_actions_frame, text="Simulate Node Failure", command=self.fail_node, width=20, bg="#FF5722", fg="white")
        fail_node_button.grid(row=0, column=2, padx=10, pady=5)
        
        # Make text area resizable
        self.nodes_tab.columnconfigure(0, weight=1)
        self.nodes_tab.rowconfigure(1, weight=1)
    
    def setup_pods_tab(self):
        # Button frame
        button_frame = tk.Frame(self.pods_tab)
        button_frame.grid(row=0, column=0, columnspan=2, pady=5, sticky="ew")
        
        # Button to fetch pods (now triggers background refresh)
        fetch_pods_button = tk.Button(button_frame, text="Refresh Pods", command=lambda: self.trigger_refresh('pods'), width=15, bg="#4CAF50", fg="white")
        fetch_pods_button.pack(side=tk.LEFT, padx=5)
        
        # Text area for pod information
        self.pods_text_area = scrolledtext.ScrolledText(self.pods_tab, wrap=tk.WORD, width=90, height=20)
        self.pods_text_area.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        
        # Pod creation frame
        pod_create_frame = tk.LabelFrame(self.pods_tab, text="Request New Pod", padx=10, pady=10)
        pod_create_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        
        # CPU cores input for pod
        pod_cpu_label = tk.Label(pod_create_frame, text="Required CPU:", font=("Helvetica", 11))
        pod_cpu_label.grid(row=0, column=0, padx=10, pady=5)
        
        self.pod_cpu_entry = tk.Entry(pod_create_frame, width=10)
        self.pod_cpu_entry.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        
        # Deploy pod button
        deploy_pod_button = tk.Button(pod_create_frame, text="Deploy Pod", command=self.deploy_pod, width=15, bg="#FF9800", fg="white")
        deploy_pod_button.grid(row=0, column=2, padx=10, pady=5)
        
        # Pod actions frame
        pod_actions_frame = tk.LabelFrame(self.pods_tab, text="Pod Actions", padx=10, pady=10)
        pod_actions_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        
        # Pod ID input for actions
        pod_id_label = tk.Label(pod_actions_frame, text="Pod ID:", font=("Helvetica", 11))
        pod_id_label.grid(row=0, column=0, padx=10, pady=5)
        
        self.pod_id_entry = tk.Entry(pod_actions_frame, width=36)
        self.pod_id_entry.grid(row=0, column=1, padx=10, pady=5)
        
        # Remove pod button
        remove_pod_button = tk.Button(pod_actions_frame, text="Remove Pod", command=self.remove_pod, width=15, bg="#F44336", fg="white")
        remove_pod_button.grid(row=0, column=2, padx=10, pady=5)
        
        # Make text area resizable
        self.pods_tab.columnconfigure(0, weight=1)
        self.pods_tab.rowconfigure(1, weight=1)
    
    def setup_cluster_tab(self):
        # Cluster status text area
        self.cluster_text_area = scrolledtext.ScrolledText(self.cluster_tab, wrap=tk.WORD, width=90, height=30)
        self.cluster_text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Refresh button (now triggers background refresh)
        refresh_button = tk.Button(self.cluster_tab, text="Refresh Status", command=lambda: self.trigger_refresh('cluster'), width=15, bg="#4CAF50", fg="white")
        refresh_button.pack(pady=10)
    
    def process_updates(self):
        """Process updates from the background thread queue."""
        try:
            while not self.update_queue.empty():
                update_type, data = self.update_queue.get_nowait()
                if update_type == "server_status":
                    self._update_server_status(data)
                elif update_type == "nodes":
                    self._update_nodes_display(data)
                elif update_type == "pods":
                    self._update_pods_display(data)
                elif update_type == "cluster":
                    # Cluster update now expects pod data as well
                    nodes_data, pods_data, cluster_data = data
                    self._update_cluster_display(cluster_data, pods_data) # Pass pod data
                elif update_type == "message":
                    level, title, message = data
                    if level == "info":
                        messagebox.showinfo(title, message)
                    elif level == "error":
                        messagebox.showerror(title, message)
                elif update_type == "clear_entry":
                    entry_widget = data
                    entry_widget.delete(0, tk.END)
                elif update_type == "refresh_all":
                    # Triggered after successful actions
                    self.trigger_refresh('all')

        except Exception as e:
            print(f"Error processing update queue: {e}")
        finally:
            # Schedule the next check
            self.root.after(100, self.process_updates)

    def background_api_worker(self):
        """Handles background API calls and periodic refreshes."""
        last_refresh_time = 0
        refresh_interval = 10 # seconds

        while True:
            current_time = time.time()

            # --- Periodic Refresh ---
            if current_time - last_refresh_time >= refresh_interval:
                self._background_check_server_status()
                self._background_fetch_all_data()
                last_refresh_time = current_time

            # --- Check for Manual Refresh Triggers (Optional, handled by direct calls now) ---
            # Can add logic here if needed for more complex background tasks

            time.sleep(1) # Check queue/time periodically

    def trigger_refresh(self, refresh_type='all'):
        """Triggers a data refresh in the background thread."""
        # This function can be called directly by buttons
        # The background worker will pick up the refresh task implicitly
        # or we can explicitly signal it if needed (using another queue, etc.)
        # For simplicity, we'll just let the periodic refresh handle it,
        # but for immediate feedback, we call the background fetch directly.
        if refresh_type == 'all':
            threading.Thread(target=self._background_fetch_all_data, daemon=True).start()
        elif refresh_type == 'nodes':
             threading.Thread(target=self._background_fetch_nodes, daemon=True).start()
        elif refresh_type == 'pods':
             threading.Thread(target=self._background_fetch_pods, daemon=True).start()
        elif refresh_type == 'cluster':
             threading.Thread(target=self._background_fetch_cluster_status, daemon=True).start()


    def _background_check_server_status(self):
        """Check server status in the background."""
        status_data = {"status": "Not Connected", "color": "red"}
        try:
            response = requests.get(f"{self.api_url}/", timeout=3)
            if response.status_code == 200:
                status_data = {"status": "Connected", "color": "green"}
            else:
                status_data = {"status": "Error", "color": "red"}
        except requests.exceptions.RequestException:
            pass # Keep status as Not Connected
        self.update_queue.put(("server_status", status_data))

    def _update_server_status(self, status_data):
        """Update server status UI elements (runs in main thread)."""
        self.status_var.set(f"Server Status: {status_data['status']}")
        self.status_label.config(fg=status_data['color'])
        # Optionally trigger cluster status update if server just connected
        # if status_data['status'] == "Connected":
        #     self.trigger_refresh('cluster')


    def _background_fetch_all_data(self):
        """Fetch all data types in the background."""
        nodes_data = self._fetch_data("/nodes", "nodes")
        pods_data = self._fetch_data("/pods", "pods")
        cluster_data = self._fetch_data("/cluster/status", "cluster")

        if nodes_data is not None:
            self.update_queue.put(("nodes", nodes_data))
        if pods_data is not None:
            self.update_queue.put(("pods", pods_data))
        if cluster_data is not None and pods_data is not None and nodes_data is not None:
             # Pass all data needed for cluster display including pod counts
            self.update_queue.put(("cluster", (nodes_data, pods_data, cluster_data)))


    def _background_fetch_nodes(self):
        nodes_data = self._fetch_data("/nodes", "nodes")
        if nodes_data is not None:
            self.update_queue.put(("nodes", nodes_data))

    def _background_fetch_pods(self):
        pods_data = self._fetch_data("/pods", "pods")
        if pods_data is not None:
            self.update_queue.put(("pods", pods_data))

    def _background_fetch_cluster_status(self):
         # Cluster status needs pod data too for counts
        nodes_data = self._fetch_data("/nodes", "nodes") # Fetch nodes for consistency if needed
        pods_data = self._fetch_data("/pods", "pods")
        cluster_data = self._fetch_data("/cluster/status", "cluster")
        if cluster_data is not None and pods_data is not None and nodes_data is not None:
            self.update_queue.put(("cluster", (nodes_data, pods_data, cluster_data)))


    def _fetch_data(self, endpoint, data_key):
        """Helper function to fetch data from an API endpoint."""
        url = f"{self.api_url}{endpoint}"
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {endpoint}: {e}")
            # Optionally put an error message in the queue for display
            # self.update_queue.put(("message", ("error", f"API Error", f"Failed to fetch {data_key}: {e}")))
            return None
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from {endpoint}: {e}")
            # self.update_queue.put(("message", ("error", f"API Error", f"Invalid response from server for {data_key}.")))
            return None


    def _update_nodes_display(self, data):
        """Update the nodes text area (runs in main thread)."""
        self.nodes_text_area.config(state=tk.NORMAL)
        self.nodes_text_area.delete(1.0, tk.END)
        if not data or 'nodes' not in data or not data['nodes']:
            self.nodes_text_area.insert(tk.END, "No nodes found or error fetching nodes.")
            self.nodes_text_area.config(state=tk.DISABLED)
            return

        self.nodes_text_area.insert(tk.END, "NODES STATUS:\n\n")
        nodes_map = data['nodes']

        for node_id, node_info in nodes_map.items():
            # ... (rest of the node formatting logic remains the same) ...
            if node_info['status'] == 'active':
                self.nodes_text_area.insert(tk.END, f"Node ID: {node_id} ", "node_id")
                self.nodes_text_area.insert(tk.END, "(ACTIVE)\n", "active")
            else:
                self.nodes_text_area.insert(tk.END, f"Node ID: {node_id} ", "node_id")
                self.nodes_text_area.insert(tk.END, "(FAILED)\n", "failed")

            self.nodes_text_area.insert(tk.END, f"Container ID: {node_info.get('container_id', 'N/A')[:12]}\n")
            self.nodes_text_area.insert(tk.END, f"CPU Cores: {node_info.get('cpu_cores', 'N/A')}\n")

            if "heartbeat_age" in node_info:
                heartbeat_age = node_info["heartbeat_age"]
                status_color = "green" if heartbeat_age < 10 else "orange" if heartbeat_age < 15 else "red"
                self.nodes_text_area.insert(tk.END, f"Last Heartbeat: {heartbeat_age:.1f} seconds ago\n", status_color)

            used_cpu = sum(float(pod.get('cpu_cores', 0)) for pod in node_info.get('pods', []))
            total_cpu = float(node_info.get('cpu_cores', 0))
            available_cpu = total_cpu - used_cpu
            self.nodes_text_area.insert(tk.END, f"Resource Usage: {used_cpu:.2f}/{total_cpu} CPU cores (Available: {available_cpu:.2f})\n")

            pod_count = len(node_info.get('pods', []))
            if pod_count > 0:
                self.nodes_text_area.insert(tk.END, f"Running Pods ({pod_count}):\n")
                for pod in node_info.get('pods', []):
                    self.nodes_text_area.insert(tk.END, f"  - Pod ID: {pod.get('pod_id', 'N/A')[:8]}... (CPU: {pod.get('cpu_cores', 'N/A')})\n")
            else:
                self.nodes_text_area.insert(tk.END, "Running Pods: None\n")

            self.nodes_text_area.insert(tk.END, "-" * 60 + "\n\n")

        # Configure text tags for colors
        self.nodes_text_area.tag_configure("active", foreground="green", font=("Helvetica", 10, "bold"))
        self.nodes_text_area.tag_configure("failed", foreground="red", font=("Helvetica", 10, "bold"))
        self.nodes_text_area.tag_configure("node_id", font=("Helvetica", 10, "bold"))
        self.nodes_text_area.tag_configure("green", foreground="green")
        self.nodes_text_area.tag_configure("orange", foreground="orange")
        self.nodes_text_area.tag_configure("red", foreground="red")
        self.nodes_text_area.config(state=tk.DISABLED)


    def _update_pods_display(self, data):
        """Update the pods text area (runs in main thread)."""
        self.pods_text_area.config(state=tk.NORMAL)
        self.pods_text_area.delete(1.0, tk.END)

        if not data or 'pods' not in data or not data['pods']:
            self.pods_text_area.insert(tk.END, "No pods found or error fetching pods.")
            self.pods_text_area.config(state=tk.DISABLED)
            return

        self.pods_text_area.insert(tk.END, "PODS STATUS:\n\n")
        pods_map = data['pods']

        for pod_id, pod_info in pods_map.items():
            # ... (rest of the pod formatting logic remains the same) ...
            self.pods_text_area.insert(tk.END, f"Pod ID: {pod_id}\n", "pod_id")

            node_id = pod_info.get('node_id', None)
            node_display = f"{node_id[:8]}..." if node_id else "None (pending assignment)"
            self.pods_text_area.insert(tk.END, f"Assigned to Node: {node_display}\n")

            cpu_cores = pod_info.get('cpu_cores', 'N/A')
            self.pods_text_area.insert(tk.END, f"CPU Resources: {cpu_cores}\n")

            status = pod_info.get('status', 'unknown').upper()
            status_tag = "running" if status == 'RUNNING' else "pending" if status == 'PENDING' else "default_status"
            self.pods_text_area.insert(tk.END, f"Status: {status}\n", status_tag)

            if 'created_at' in pod_info:
                created_time_str = "Invalid timestamp"
                try:
                    created_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(float(pod_info['created_at'])))
                    created_time_str = created_time
                except (ValueError, TypeError):
                     pass # Keep default "Invalid timestamp"
                self.pods_text_area.insert(tk.END, f"Created: {created_time_str}\n")

            self.pods_text_area.insert(tk.END, "-" * 60 + "\n\n")

        # Configure text tags for colors
        self.pods_text_area.tag_configure("pod_id", font=("Helvetica", 10, "bold"))
        self.pods_text_area.tag_configure("running", foreground="green", font=("Helvetica", 10, "bold"))
        self.pods_text_area.tag_configure("pending", foreground="orange", font=("Helvetica", 10, "bold"))
        self.pods_text_area.tag_configure("default_status", foreground="black") # Default color
        self.pods_text_area.config(state=tk.DISABLED)


    def _update_cluster_display(self, cluster_data, pods_data):
        """Update the cluster status text area (runs in main thread)."""
        self.cluster_text_area.config(state=tk.NORMAL)
        self.cluster_text_area.delete(1.0, tk.END)

        if not cluster_data:
            self.cluster_text_area.insert(tk.END, "Error retrieving cluster status.")
            self.cluster_text_area.config(state=tk.DISABLED)
            return

        # Update the status bar label
        active_nodes = cluster_data.get('active_nodes', 0)
        total_pods = cluster_data.get('total_pods', 0)
        cpu_util = cluster_data.get('utilization_percentage', 0)
        self.cluster_status_var.set(f"Nodes: {active_nodes}, Pods: {total_pods}, CPU Util: {cpu_util:.1f}%")

        # Update the text area with detailed information
        self.cluster_text_area.insert(tk.END, "CLUSTER STATUS SUMMARY\n", "header")
        self.cluster_text_area.insert(tk.END, "=" * 70 + "\n\n")

        # Nodes section
        self.cluster_text_area.insert(tk.END, "Nodes\n", "section")
        self.cluster_text_area.insert(tk.END, f"Active Nodes: {cluster_data.get('active_nodes', 0)}\n")
        self.cluster_text_area.insert(tk.END, f"Failed Nodes: {cluster_data.get('failed_nodes', 0)}\n")
        total_nodes = cluster_data.get('active_nodes', 0) + cluster_data.get('failed_nodes', 0)
        self.cluster_text_area.insert(tk.END, f"Total Nodes: {total_nodes}\n\n")

        # Resources section
        self.cluster_text_area.insert(tk.END, "Resources\n", "section")
        self.cluster_text_area.insert(tk.END, f"Total CPU Cores: {cluster_data.get('total_cpu', 0):.2f}\n")
        self.cluster_text_area.insert(tk.END, f"Used CPU Cores: {cluster_data.get('used_cpu', 0):.2f}\n")
        self.cluster_text_area.insert(tk.END, f"Available CPU Cores: {cluster_data.get('available_cpu', 0):.2f}\n")
        self.cluster_text_area.insert(tk.END, f"CPU Utilization: {cluster_data.get('utilization_percentage', 0):.2f}%\n\n")

        # Workloads section
        self.cluster_text_area.insert(tk.END, "Workloads\n", "section")
        self.cluster_text_area.insert(tk.END, f"Total Pods: {cluster_data.get('total_pods', 0)}\n")

        # Use the passed pods_data to count statuses
        running_pods = 0
        pending_pods = 0
        if pods_data and 'pods' in pods_data:
             running_pods = sum(1 for pod in pods_data['pods'].values() if pod.get('status') == 'running')
             pending_pods = sum(1 for pod in pods_data['pods'].values() if pod.get('status') == 'pending')

        self.cluster_text_area.insert(tk.END, f"Running Pods: {running_pods}\n")
        self.cluster_text_area.insert(tk.END, f"Pending Pods: {pending_pods}\n\n")

        if pending_pods > 0:
            self.cluster_text_area.insert(tk.END, "Note: There are pending pods that need additional resources.\n")
            self.cluster_text_area.insert(tk.END, "Consider adding more nodes to the cluster.\n\n")

        # Text styling
        self.cluster_text_area.tag_configure("header", font=("Helvetica", 12, "bold"))
        self.cluster_text_area.tag_configure("section", font=("Helvetica", 11, "bold"))
        self.cluster_text_area.config(state=tk.DISABLED)


    def _run_action_in_background(self, action_func, *args):
        """Runs a given action function in a background thread."""
        threading.Thread(target=action_func, args=args, daemon=True).start()

    # --- Action Methods (Trigger background execution) ---

    def add_node(self):
        cpu_cores = self.cpu_cores_entry.get().strip()
        if not cpu_cores:
            messagebox.showerror("Error", "Please specify CPU cores for the new node")
            return
        try:
            float(cpu_cores)
        except ValueError:
            messagebox.showerror("Error", "CPU cores must be a number")
            return
        self._run_action_in_background(self._background_add_node, cpu_cores)

    def fail_node(self):
        node_id = self.node_id_entry.get().strip()
        if not node_id:
            messagebox.showerror("Error", "Please enter a Node ID")
            return
        self._run_action_in_background(self._background_fail_node, node_id)

    def deploy_pod(self):
        cpu_cores = self.pod_cpu_entry.get().strip()
        if not cpu_cores:
            messagebox.showerror("Error", "Please specify CPU cores for the pod")
            return
        try:
            float(cpu_cores)
        except ValueError:
            messagebox.showerror("Error", "CPU cores must be a number")
            return
        self._run_action_in_background(self._background_deploy_pod, cpu_cores)

    def remove_pod(self):
        pod_id = self.pod_id_entry.get().strip()
        if not pod_id:
            messagebox.showerror("Error", "Please enter a Pod ID")
            return
        self._run_action_in_background(self._background_remove_pod, pod_id)


    # --- Background Action Implementations ---

    def _background_add_node(self, cpu_cores):
        """Add node API call (runs in background thread)."""
        try:
            data = {"cpu_cores": cpu_cores}
            response = requests.post(f"{self.api_url}/node/add", json=data, timeout=10)
            response.raise_for_status()
            result = response.json()
            self.update_queue.put(("message", ("info", "Success", f"Node added successfully. Node ID: {result.get('node_id', 'Unknown')}")))
            self.update_queue.put(("clear_entry", self.cpu_cores_entry))
            self.update_queue.put(("refresh_all", None)) # Signal refresh
        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to add node: {e}"
            try: # Try to get server error message
                error_msg = f"Failed to add node: {e.response.json().get('error', e)}"
            except: pass
            self.update_queue.put(("message", ("error", "Error", error_msg)))
        except Exception as e: # Catch other potential errors
             self.update_queue.put(("message", ("error", "Error", f"An unexpected error occurred: {e}")))


    def _background_fail_node(self, node_id):
        """Fail node API call (runs in background thread)."""
        try:
            response = requests.post(f"{self.api_url}/node/fail/{node_id}", timeout=10)
            response.raise_for_status()
            result = response.json()
            self.update_queue.put(("message", ("info", "Success", result.get('message', 'Node failure simulated successfully'))))
            self.update_queue.put(("clear_entry", self.node_id_entry))
            self.update_queue.put(("refresh_all", None)) # Signal refresh
        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to simulate node failure: {e}"
            try:
                error_msg = f"Failed to simulate node failure: {e.response.json().get('error', e)}"
            except: pass
            self.update_queue.put(("message", ("error", "Error", error_msg)))
        except Exception as e:
             self.update_queue.put(("message", ("error", "Error", f"An unexpected error occurred: {e}")))


    def _background_deploy_pod(self, cpu_cores):
        """Deploy pod API call (runs in background thread)."""
        try:
            data = {"cpu_cores": cpu_cores}
            response = requests.post(f"{self.api_url}/pod/request", json=data, timeout=10)

            if response.status_code == 400 and "error" in response.json():
                 # Handle specific user errors like no suitable node
                 error_msg = response.json().get('error', 'Failed to deploy pod')
                 self.update_queue.put(("message", ("error", "Scheduling Error", error_msg)))
                 return # Don't proceed further

            response.raise_for_status() # Raise for other HTTP errors (5xx, 404 etc)

            result = response.json()
            self.update_queue.put(("message", ("info", "Success",
                               f"Pod scheduled successfully.\nPod ID: {result.get('pod_id', 'Unknown')}\n"
                               f"Node ID: {result.get('node_id', 'Unknown')}")))
            self.update_queue.put(("clear_entry", self.pod_cpu_entry))
            self.update_queue.put(("refresh_all", None)) # Signal refresh
        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to deploy pod: {e}"
            try:
                error_msg = f"Failed to deploy pod: {e.response.json().get('error', e)}"
            except: pass
            self.update_queue.put(("message", ("error", "Error", error_msg)))
        except Exception as e:
             self.update_queue.put(("message", ("error", "Error", f"An unexpected error occurred: {e}")))


    def _background_remove_pod(self, pod_id):
        """Remove pod API call (runs in background thread)."""
        try:
            response = requests.delete(f"{self.api_url}/pod/remove/{pod_id}", timeout=10)

            if response.status_code == 404:
                self.update_queue.put(("message", ("error", "Error", "Pod not found")))
                return

            response.raise_for_status()
            result = response.json()
            self.update_queue.put(("message", ("info", "Success", result.get('message', 'Pod removed successfully'))))
            self.update_queue.put(("clear_entry", self.pod_id_entry))
            self.update_queue.put(("refresh_all", None)) # Signal refresh
        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to remove pod: {e}"
            try:
                error_msg = f"Failed to remove pod: {e.response.json().get('error', e)}"
            except: pass
            self.update_queue.put(("message", ("error", "Error", error_msg)))
        except Exception as e:
             self.update_queue.put(("message", ("error", "Error", f"An unexpected error occurred: {e}")))


    # Remove old fetch methods (replaced by _update_*_display and background fetches)
    # def fetch_nodes(self): ...
    # def fetch_pods(self): ...
    # def fetch_cluster_status(self): ...
    # def fetch_pod_status_counts(self): ... # Integrated into _update_cluster_display

    # Remove old auto_refresh and check_server_status (replaced by background worker)
    # def auto_refresh(self): ...
    # def check_server_status(self): ...


# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = KubernetesSimulationGUI(root)
    root.mainloop()