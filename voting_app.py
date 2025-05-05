import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
import sys
import json
import logging
from client import Client
from block123 import Block, Transaction

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("voting_app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class VotingApp:
    """
    GUI application for the decentralized voting system.
    
    This application provides a user interface for:
    - Creating votes
    - Mining blocks
    - Viewing the blockchain
    - Viewing voting results
    - Viewing network status
    """
    
    def __init__(self, root, client):
        """
        Initialize the voting application.
        
        Args:
            root: Tkinter root window
            client: Client instance
        """
        self.root = root
        self.client = client
        
        # Set the UI callback function
        self.client.set_ui_callback(self.update_ui)
        
        # Set up the UI
        self.setup_ui()
        
        # Start a thread to periodically update the UI
        self.update_thread = threading.Thread(target=self.periodic_update)
        self.update_thread.daemon = True
        self.update_thread.start()
    
    def setup_ui(self):
        """Set up the user interface."""
        self.root.title("Decentralized Voting System")
        self.root.geometry("800x600")
        self.root.minsize(800, 600)
        
        # Create a notebook with tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.voting_tab = ttk.Frame(self.notebook)
        self.blockchain_tab = ttk.Frame(self.notebook)
        self.results_tab = ttk.Frame(self.notebook)
        self.network_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.voting_tab, text="Vote")
        self.notebook.add(self.blockchain_tab, text="Blockchain")
        self.notebook.add(self.results_tab, text="Results")
        self.notebook.add(self.network_tab, text="Network")
        
        # Set up each tab
        self.setup_voting_tab()
        self.setup_blockchain_tab()
        self.setup_results_tab()
        self.setup_network_tab()
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def setup_voting_tab(self):
        """Set up the voting tab."""
        # Frame for voting controls
        control_frame = ttk.LabelFrame(self.voting_tab, text="Create Vote")
        control_frame.pack(fill=tk.X, expand=False, padx=10, pady=10)
        
        # Vote option
        ttk.Label(control_frame, text="Candidate:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.vote_option_var = tk.StringVar()
        
        # Predefined options for this demo
        options = ["Candidate A", "Candidate B", "Candidate C"]
        self.vote_option_combobox = ttk.Combobox(control_frame, textvariable=self.vote_option_var, values=options)
        self.vote_option_combobox.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Vote button
        self.vote_button = ttk.Button(control_frame, text="Cast Vote", command=self.cast_vote)
        self.vote_button.grid(row=0, column=2, padx=5, pady=5)
        
        # Mine button
        self.mine_button = ttk.Button(control_frame, text="Mine Block", command=self.mine_block)
        self.mine_button.grid(row=0, column=3, padx=5, pady=5)
        
        # Auto-mine checkbox
        self.auto_mine_var = tk.BooleanVar(value=self.client.auto_mine)
        self.auto_mine_check = ttk.Checkbutton(
            control_frame, text="Auto-Mine", variable=self.auto_mine_var, command=self.toggle_auto_mine
        )
        self.auto_mine_check.grid(row=0, column=4, padx=5, pady=5)
        
        # Frame for transaction log
        log_frame = ttk.LabelFrame(self.voting_tab, text="Transaction Log")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Transaction log
        self.transaction_log = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, width=40, height=10)
        self.transaction_log.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.transaction_log.config(state=tk.DISABLED)
    
    def setup_blockchain_tab(self):
        """Set up the blockchain tab."""
        # Frame for blockchain info
        info_frame = ttk.LabelFrame(self.blockchain_tab, text="Blockchain Information")
        info_frame.pack(fill=tk.X, expand=False, padx=10, pady=10)
        
        # Blockchain info fields
        self.chain_length_var = tk.StringVar(value="Chain Length: 0")
        ttk.Label(info_frame, textvariable=self.chain_length_var).grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.last_block_var = tk.StringVar(value="Last Block: None")
        ttk.Label(info_frame, textvariable=self.last_block_var).grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.pending_tx_var = tk.StringVar(value="Pending Transactions: 0")
        ttk.Label(info_frame, textvariable=self.pending_tx_var).grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.mining_status_var = tk.StringVar(value="Mining: No")
        ttk.Label(info_frame, textvariable=self.mining_status_var).grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        
        # Frame for blockchain display
        chain_frame = ttk.LabelFrame(self.blockchain_tab, text="Blockchain")
        chain_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Treeview for blocks
        self.block_tree = ttk.Treeview(chain_frame, columns=("Index", "Hash", "Prev Hash", "Timestamp", "Transactions"))
        self.block_tree.heading("#0", text="")
        self.block_tree.heading("Index", text="Index")
        self.block_tree.heading("Hash", text="Hash")
        self.block_tree.heading("Prev Hash", text="Prev Hash")
        self.block_tree.heading("Timestamp", text="Timestamp")
        self.block_tree.heading("Transactions", text="Transactions")
        
        self.block_tree.column("#0", width=0, stretch=tk.NO)
        self.block_tree.column("Index", width=50, anchor=tk.CENTER)
        self.block_tree.column("Hash", width=100)
        self.block_tree.column("Prev Hash", width=100)
        self.block_tree.column("Timestamp", width=150, anchor=tk.CENTER)
        self.block_tree.column("Transactions", width=100, anchor=tk.CENTER)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(chain_frame, orient=tk.VERTICAL, command=self.block_tree.yview)
        self.block_tree.configure(yscroll=scrollbar.set)
        
        # Pack everything
        self.block_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Double-click event to show block details
        self.block_tree.bind("<Double-1>", self.show_block_details)
    
    def setup_results_tab(self):
        """Set up the results tab."""
        # Frame for results
        results_frame = ttk.LabelFrame(self.results_tab, text="Voting Results")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Canvas for chart
        self.results_canvas = tk.Canvas(results_frame, bg="white")
        self.results_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Frame for results buttons
        button_frame = ttk.Frame(self.results_tab)
        button_frame.pack(fill=tk.X, expand=False, padx=10, pady=10)
        
        # Refresh button
        refresh_button = ttk.Button(button_frame, text="Refresh Results", command=self.refresh_results)
        refresh_button.pack(side=tk.RIGHT, padx=5, pady=5)
    
    def setup_network_tab(self):
        """Set up the network tab."""
        # Frame for network info
        info_frame = ttk.LabelFrame(self.network_tab, text="Network Information")
        info_frame.pack(fill=tk.X, expand=False, padx=10, pady=10)
        
        # Client ID
        self.client_id_var = tk.StringVar(value=f"Client ID: {self.client.id}")
        ttk.Label(info_frame, textvariable=self.client_id_var).grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        # Tracker info
        self.tracker_info_var = tk.StringVar(value=f"Tracker: {self.client.tracker_host}:{self.client.tracker_port}")
        ttk.Label(info_frame, textvariable=self.tracker_info_var).grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        
        # Peer count
        self.peer_count_var = tk.StringVar(value="Peers: 0")
        ttk.Label(info_frame, textvariable=self.peer_count_var).grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        
        # Frame for peer list
        peers_frame = ttk.LabelFrame(self.network_tab, text="Peers")
        peers_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Treeview for peers
        self.peer_tree = ttk.Treeview(peers_frame, columns=("ID", "Host", "Port"))
        self.peer_tree.heading("#0", text="")
        self.peer_tree.heading("ID", text="Peer ID")
        self.peer_tree.heading("Host", text="Host")
        self.peer_tree.heading("Port", text="Port")
        
        self.peer_tree.column("#0", width=0, stretch=tk.NO)
        self.peer_tree.column("ID", width=200)
        self.peer_tree.column("Host", width=150)
        self.peer_tree.column("Port", width=100, anchor=tk.CENTER)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(peers_frame, orient=tk.VERTICAL, command=self.peer_tree.yview)
        self.peer_tree.configure(yscroll=scrollbar.set)
        
        # Pack everything
        self.peer_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def cast_vote(self):
        """Cast a vote."""
        option = self.vote_option_var.get()
        
        if not option:
            messagebox.showerror("Error", "Please select a candidate")
            return
        
        # Create vote transaction
        vote_data = {'choice': option}
        success = self.client.create_transaction(vote_data)
        
        if success:
            self.status_var.set(f"Vote cast for {option}")
            messagebox.showinfo("Success", f"Your vote for {option} has been cast")
            self.add_to_transaction_log(f"Vote cast for {option}")
        else:
            self.status_var.set(f"Failed to cast vote")
            messagebox.showerror("Error", f"Failed to cast vote. Have you already voted?")
    
    def mine_block(self):
        """Manually mine a block."""
        if not self.client.blockchain.pending_transactions:
            messagebox.showinfo("Info", "No pending transactions to mine")
            return
        
        success = self.client.manually_mine_block()
        
        if success:
            self.status_var.set("Mining started")
            self.add_to_transaction_log("Mining started...")
        else:
            self.status_var.set("Failed to start mining")
            messagebox.showerror("Error", "Failed to start mining")
    
    def toggle_auto_mine(self):
        """Toggle auto-mining."""
        self.client.auto_mine = self.auto_mine_var.get()
        self.status_var.set(f"Auto-mining: {'On' if self.client.auto_mine else 'Off'}")
    
    def refresh_results(self):
        """Refresh the voting results."""
        self.update_results_chart()
    
    def add_to_transaction_log(self, message):
        """Add a message to the transaction log."""
        self.transaction_log.config(state=tk.NORMAL)
        self.transaction_log.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n")
        self.transaction_log.see(tk.END)
        self.transaction_log.config(state=tk.DISABLED)
    
    def update_ui(self, event_type, data):
        """
        Update the UI based on events from the client.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        if event_type == 'transaction_created':
            self.add_to_transaction_log(f"Transaction created: {data.transaction_id}")
        elif event_type == 'transaction_added':
            self.add_to_transaction_log(f"Transaction received: {data.transaction_id}")
            self.update_blockchain_info()
        elif event_type == 'block_mined':
            self.add_to_transaction_log(f"Block mined: {data.index}")
            self.update_blockchain_info()
            self.update_blockchain_display()
        elif event_type == 'block_added':
            self.add_to_transaction_log(f"Block received: {data.index}")
            self.update_blockchain_info()
            self.update_blockchain_display()
        elif event_type == 'blockchain_updated':
            self.add_to_transaction_log(f"Blockchain updated")
            self.update_blockchain_info()
            self.update_blockchain_display()
        elif event_type == 'peer_list_updated':
            self.update_peer_list(data)
        elif event_type == 'vote_results_updated':
            self.add_to_transaction_log(f"Updated voting results")
            self.update_results_chart()
    
    def update_blockchain_info(self):
        """Update the blockchain information display."""
        # Get blockchain info
        info = self.client.get_blockchain_info()
        
        # Update display
        self.chain_length_var.set(f"Chain Length: {info['chain_length']}")
        self.last_block_var.set(f"Last Block: {info['last_block_hash'][:10]}... (truncated)")
        self.pending_tx_var.set(f"Pending Transactions: {info['pending_transactions']}")
        self.mining_status_var.set(f"Mining: {'Yes' if info['mining'] else 'No'}")
    
    def update_blockchain_display(self):
        """Update the blockchain display."""
        # Clear the treeview
        for item in self.block_tree.get_children():
            self.block_tree.delete(item)
        
        # Add blocks to the treeview
        for block in self.client.blockchain.chain:
            self.block_tree.insert(
                "", tk.END, values=(
                    block.index,
                    block.hash[:10] + "...",
                    block.previous_hash[:10] + "...",
                    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(block.timestamp)),
                    len(block.transactions)
                )
            )
    
    def update_results_chart(self):
        """Update the voting results chart."""
        # Get voting results
        results = self.client.vote_results

        # Clear the canvas
        self.results_canvas.delete("all")
        
        # If no votes, show a message
        if not results:
            self.results_canvas.create_text(
                self.results_canvas.winfo_width() // 2,
                self.results_canvas.winfo_height() // 2,
                text="No votes yet",
                font=("Arial", 14)
            )
            return
        
        # Calculate total votes
        total_votes = sum(results.values())
        
        # Draw the chart
        chart_width = self.results_canvas.winfo_width() - 100
        chart_height = self.results_canvas.winfo_height() - 50
        
        if chart_width <= 0 or chart_height <= 0:
            # Canvas not yet sized, schedule an update
            self.root.after(100, self.update_results_chart)
            return
        
        # Bar width based on number of options
        bar_width = min(80, chart_width // len(results))
        spacing = 20
        
        # Draw bars
        x = 50
        max_value = max(results.values())
        
        for option, votes in results.items():
            # Calculate bar height
            if max_value > 0:
                bar_height = (votes / max_value) * (chart_height - 50)
            else:
                bar_height = 0
            
            # Draw the bar
            self.results_canvas.create_rectangle(
                x, chart_height - bar_height,
                x + bar_width, chart_height,
                fill="blue", outline="black"
            )
            
            # Draw the option label
            self.results_canvas.create_text(
                x + bar_width // 2, chart_height + 10,
                text=option,
                anchor=tk.N
            )
            
            # Draw the vote count
            self.results_canvas.create_text(
                x + bar_width // 2, chart_height - bar_height - 10,
                text=str(votes),
                anchor=tk.S
            )
            
            # Draw the percentage
            percentage = (votes / total_votes) * 100 if total_votes > 0 else 0
            self.results_canvas.create_text(
                x + bar_width // 2, chart_height - bar_height - 30,
                text=f"{percentage:.1f}%",
                anchor=tk.S
            )
            
            # Move to the next bar
            x += bar_width + spacing
    
    def update_peer_list(self, peers):
        """
        Update the peer list display.
        
        Args:
            peers: Dictionary of peers {peer_id: (host, port)}
        """
        # Update peer count
        self.peer_count_var.set(f"Peers: {len(peers)}")
        
        # Clear the treeview
        for item in self.peer_tree.get_children():
            self.peer_tree.delete(item)
        
        # Add peers to the treeview
        for peer_id, (host, port) in peers.items():
            self.peer_tree.insert("", tk.END, values=(peer_id, host, port))
    
    def show_block_details(self, event):
        """
        Show block details when a block is double-clicked.
        
        Args:
            event: The event object
        """
        # Get the selected item
        item = self.block_tree.selection()[0]
        values = self.block_tree.item(item, "values")
        
        if not values:
            return
        
        # Get the block index
        block_index = int(values[0])
        
        # Find the block
        block = None
        for b in self.client.blockchain.chain:
            if b.index == block_index:
                block = b
                break
        
        if not block:
            return
        
        # Create a new window for block details
        details_window = tk.Toplevel(self.root)
        details_window.title(f"Block {block.index} Details")
        details_window.geometry("600x400")
        details_window.minsize(600, 400)
        
        # Create a notebook with tabs
        notebook = ttk.Notebook(details_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Block info tab
        info_tab = ttk.Frame(notebook)
        notebook.add(info_tab, text="Block Info")
        
        # Transactions tab
        tx_tab = ttk.Frame(notebook)
        notebook.add(tx_tab, text="Transactions")
        
        # Block info
        ttk.Label(info_tab, text="Index:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Label(info_tab, text=str(block.index)).grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(info_tab, text="Hash:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Label(info_tab, text=block.hash).grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(info_tab, text="Previous Hash:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Label(info_tab, text=block.previous_hash).grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(info_tab, text="Timestamp:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Label(info_tab, text=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(block.timestamp))).grid(row=3, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(info_tab, text="Nonce:").grid(row=4, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Label(info_tab, text=str(block.nonce)).grid(row=4, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(info_tab, text="Merkle Root:").grid(row=5, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Label(info_tab, text=block.merkle_root).grid(row=5, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(info_tab, text="Transaction Count:").grid(row=6, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Label(info_tab, text=str(len(block.transactions))).grid(row=6, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Transactions
        tx_tree = ttk.Treeview(tx_tab, columns=("ID", "Voter", "Choice", "Timestamp"))
        tx_tree.heading("#0", text="")
        tx_tree.heading("ID", text="Transaction ID")
        tx_tree.heading("Voter", text="Voter ID")
        tx_tree.heading("Choice", text="Vote")
        tx_tree.heading("Timestamp", text="Timestamp")
        
        tx_tree.column("#0", width=0, stretch=tk.NO)
        tx_tree.column("ID", width=100)
        tx_tree.column("Voter", width=100)
        tx_tree.column("Choice", width=100)
        tx_tree.column("Timestamp", width=150)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(tx_tab, orient=tk.VERTICAL, command=tx_tree.yview)
        tx_tree.configure(yscroll=scrollbar.set)
        
        # Pack everything
        tx_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add transactions to the treeview
        for tx in block.transactions:
            tx_tree.insert(
                "", tk.END, values=(
                    tx.transaction_id[:10] + "...",
                    tx.voter_id[:10] + "...",
                    tx.vote_data.get('choice', 'N/A'),
                    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(tx.timestamp))
                )
            )
    
    def periodic_update(self):
        """Periodically update the UI."""
        while True:
            try:
                # Update blockchain info
                self.update_blockchain_info()
                
                # Update results chart
                self.update_results_chart()
                
                # Sleep for 5 seconds
                time.sleep(5)
            except Exception as e:
                logger.error(f"Error in periodic update: {e}")
                time.sleep(5)


def main():
    # Parse command line arguments
    if len(sys.argv) < 5:
        print(f"Usage: {sys.argv[0]} <host> <port> <tracker_host> <tracker_port> [topology_file] [mining_difficulty] [auto_mine]")
        sys.exit(1)
    
    host = sys.argv[1]
    port = int(sys.argv[2])
    tracker_host = sys.argv[3]
    tracker_port = int(sys.argv[4])
    topology_file = sys.argv[5] if len(sys.argv) > 5 else "topology.dat"
    auto_mine = sys.argv[6].lower() == "true" if len(sys.argv) > 6 else False
    
    # Create client
    client = Client(host, port, tracker_host, tracker_port, topology_file, auto_mine)
    
    # Create UI
    root = tk.Tk()
    app = VotingApp(root, client)
    
    # Start client in a separate thread
    client_thread = threading.Thread(target=client.start)
    client_thread.daemon = True
    client_thread.start()
    
    # Start UI
    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass
    finally:
        client.stop()
        sys.exit(0)


if __name__ == "__main__":
    main()