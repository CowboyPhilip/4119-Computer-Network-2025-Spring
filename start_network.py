import subprocess
import sys
import os
import time
import signal
import argparse

# List to keep track of started processes
processes = []

def signal_handler(sig, frame):
    """Handle Ctrl+C to gracefully shut down all processes."""
    print("\nShutting down all nodes...")
    for process in processes:
        try:
            process.terminate()
        except:
            pass
    sys.exit(0)

def main():
    """Start the blockchain network."""
    parser = argparse.ArgumentParser(description='Start a blockchain voting network.')
    
    parser.add_argument('--peers', type=int, default=3, help='Number of peers to start (default: 3)')
    parser.add_argument('--difficulty', type=int, default=4, help='Mining difficulty (default: 4)')
    parser.add_argument('--auto-mine', action='store_true', help='Enable auto-mining on peers')
    
    args = parser.parse_args()
    
    # Register signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    print("Starting blockchain voting network...")
    
    # Start the tracker
    tracker_host = "127.0.0.1"
    tracker_port = 5000
    
    print(f"Starting tracker at {tracker_host}:{tracker_port}...")
    tracker_process = subprocess.Popen(
        [sys.executable, "tracker.py", tracker_host, str(tracker_port), "topology.dat"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    processes.append(tracker_process)
    
    # Give the tracker some time to start
    time.sleep(2)
    
    # Start the peers
    base_port = 5001
    for i in range(args.peers):
        peer_host = "127.0.0.1"
        peer_port = base_port + i
        
        # Start the peer with the voting GUI
        print(f"Starting peer {i+1} at {peer_host}:{peer_port}...")
        
        auto_mine_arg = "true" if args.auto_mine else "false"
        
        peer_process = subprocess.Popen(
            [
                sys.executable, "voting_app.py", 
                peer_host, str(peer_port), 
                tracker_host, str(tracker_port),
                "topology.dat", str(args.difficulty), auto_mine_arg
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        processes.append(peer_process)
        
        # Give each peer some time to start to avoid overwhelming the tracker
        time.sleep(1)

        if peer_process.poll() is not None:
            _, err = peer_process.communicate()
            print(f"❌ Peer {i+1} failed to start. Error:")
            print(err.decode())
        else:
            print(f"✅ Peer {i+1} started successfully.")
            processes.append(peer_process)

            
    print(f"Network started with 1 tracker and {args.peers} peers.")
    print("Press Ctrl+C to shut down the network.")
    
    # Keep the main process running
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()