import socket
import threading
import time
import logging
from typing import Dict, Any, List, Tuple, Optional
import json
import sys
from network import Network, MSG_REGISTER, MSG_PEER_LIST, MSG_HEARTBEAT, MSG_CHAIN_RESPONSE, MSG_GET_MINER
from block123 import Blockchain

DEFAULT_STAKEVALUE = 0

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Tracker(Network):
    """
    Tracker node that coordinates the peer-to-peer network.
    
    The tracker maintains a list of all active peers and distributes
    this list to all peers when changes occur. It also maintains a
    reference blockchain that can be used to resolve conflicts.
    """
    
    def __init__(self, host: str, port: int, topology_file: str = "topology.dat"):
        """
        Initialize the tracker.
        
        Args:
            host: Host IP address
            port: Port to listen on
            topology_file: File containing network topology
        """
        super().__init__(host, port, topology_file)
        self.assigned_ids = 0
        self.active_peers = {}  # {peer_id: (host, port, last_heartbeat, stake_value)}
        self.miners = {}
        self.blockchain = Blockchain()  # Reference blockchain
        
        # Start heartbeat check thread
        self.heartbeat_thread = None
    
    def start(self) -> None:
        """Start the tracker server."""
        super().start()
        
        # Start heartbeat checker
        self.heartbeat_thread = threading.Thread(target=self._check_heartbeats)
        self.heartbeat_thread.daemon = True
        self.heartbeat_thread.start()
        
        logger.info("Tracker is fully initialized and running")
    
    def stop(self) -> None:
        """Stop the tracker server."""
        super().stop()
        logger.info("Tracker stopped")
    
    def _handle_client(self, client_socket: socket.socket) -> None:
        """
        Handle client connection.
        
        Args:
            client_socket: The client socket
        """
        try:
            # Receive message
            message = self.receive_message(client_socket)
            
            if message and 'type' in message:
                msg_type = message['type']
                
                if msg_type == MSG_REGISTER:
                    self._handle_register(message)
                elif msg_type == MSG_HEARTBEAT:
                    self._handle_heartbeat(message)
                elif msg_type == MSG_GET_MINER:
                    self._handle_get_miner(message)
                else:
                    logger.warning(f"Received unknown message type: {msg_type}")
            
            client_socket.close()
        except Exception as e:
            logger.error(f"Error handling client: {e}")
            client_socket.close()
    
    def _handle_register(self, message: Dict[str, Any]) -> None:
        """
        Handle peer registration.
        
        Args:
            message: Registration message
        """
        if 'data' in message and 'sender' in message:
            peer_data = message['data']
            peer_id = message['sender']
            
            if 'host' in peer_data and 'port' in peer_data:
                host = peer_data['host']
                port = int(peer_data['port'])

                if peer_id not in self.peers:
                    self.assigned_ids += 1
                    miner_id = self.assigned_ids
                    self.miners[miner_id] = DEFAULT_STAKEVALUE
                else:
                    miner_id = self.peers[peer_id][2]

                # Add peer to active peers
                self.active_peers[peer_id] = (host, port, time.time())
                self.peers[peer_id] = (host, port, miner_id)
                
                logger.info(f"Registered peer {peer_id} at {host}:{port}")
                
                # Send updated peer list to all peers
                self._broadcast_peer_list()
                
                # Send current blockchain to the new peer
                self._send_blockchain_to_peer(peer_id)
    
    def _handle_heartbeat(self, message: Dict[str, Any]) -> None:
        """
        Handle peer heartbeat.
        
        Args:
            message: Heartbeat message
        """
        if 'sender' in message:
            peer_id = message['sender']
            
            if peer_id in self.active_peers:
                host, port, _ = self.active_peers[peer_id]
                self.active_peers[peer_id] = (host, port, time.time())
                
                # Update reference blockchain if needed
                if 'data' in message and 'blockchain' in message['data']:
                    blockchain_data = message['data']['blockchain']
                    
                    # Create a temporary blockchain from the data
                    temp_chain = Blockchain.from_dict(blockchain_data)
                    
                    # If the peer's chain is longer and valid, update our chain
                    temp_chain_check, miner_results = temp_chain.is_chain_valid()
                    if len(temp_chain.chain) > len(self.blockchain.chain) and temp_chain_check:
                        self.blockchain = temp_chain
                        logger.info(f"Updated reference blockchain from peer {peer_id}")
                    
                    for miner_id, result in miner_results:
                        # 2nd element = stake_value
                        stake_value = self.miners[miner_id]
                        if result:
                            # 3rd element = stake_value
                            stake_value += 1
                        else:
                            stake_value -= 1
                        self.miners[miner_id] = stake_value
    
    def _check_heartbeats(self) -> None:
        """Check for dead peers and remove them."""
        while self.running:
            current_time = time.time()
            dead_peers = []
            
            # Find peers that haven't sent a heartbeat in 30 seconds
            for peer_id, (host, port, last_heartbeat) in self.active_peers.items():
                if current_time - last_heartbeat > 30:
                    dead_peers.append(peer_id)
            
            # Remove dead peers
            for peer_id in dead_peers:
                host, port, _ = self.active_peers[peer_id]
                logger.info(f"Removing dead peer {peer_id} at {host}:{port}")
                
                self.active_peers.pop(peer_id)
                self.peers.pop(peer_id, None)
            
            # If any peers were removed, send updated list
            if dead_peers:
                self._broadcast_peer_list()
            
            # Sleep for 10 seconds
            time.sleep(10)
    
    def _broadcast_peer_list(self) -> None:
        """Broadcast the peer list to all active peers."""
        # Create peer list message
        peer_list = {}
        for peer_id, (host, port, _) in self.active_peers.items():
            peer_list[peer_id] = {'host': host, 'port': port}
        
        message = {
            'type': MSG_PEER_LIST,
            'data': peer_list,
            'timestamp': time.time(),
            'sender': self.id
        }
        
        # Broadcast to all active peers
        for peer_id, (host, port, _) in self.active_peers.items():
            self.send_message((host, port), message)
        
        logger.info(f"Broadcast peer list to {len(self.active_peers)} peers")
    
    def _send_blockchain_to_peer(self, peer_id: str) -> None:
        """
        Send the current blockchain to a peer.
        
        Args:
            peer_id: ID of the peer to send to
        """
        if peer_id in self.active_peers:
            host, port, _ = self.active_peers[peer_id]
            
            message = {
                'type': MSG_CHAIN_RESPONSE,
                'data': self.blockchain.to_dict(),
                'timestamp': time.time(),
                'sender': self.id
            }
            
            self.send_message((host, port), message)
            logger.info(f"Sent blockchain to peer {peer_id}")

    def _handle_get_miner(self, message: Dict[str, any]):
        if 'sender' in message:
            peer_id = message['sender']

            if peer_id in self.active_peers:
                host, port, _ = self.active_peers[peer_id]
                # miner_id is 3rd element in self.peers
                miner_id = self.peers[peer_id][2]
                stake_value = self.miners[miner_id]
                difficulty = Blockchain.get_difficulty(stake_value)

                message = {
                    'type': MSG_GET_MINER,
                    'data': {
                        'miner id' : miner_id,
                        'difficulty' : difficulty
                    },
                    'timestamp': time.time(),
                    'sender': self.id
                }

                self.send_message((host, port), message)
                logger.info(f"Sent mining id and difficulty to {peer_id}")

if __name__ == "__main__":
    # Parse command line arguments
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <host> <port> [topology_file]")
        sys.exit(1)
    
    host = sys.argv[1]
    port = int(sys.argv[2])
    topology_file = sys.argv[3] if len(sys.argv) > 3 else "topology.dat"
    
    # Create and start tracker
    tracker = Tracker(host, port, topology_file)
    
    try:
        tracker.start()
        
        # Keep the main thread running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down tracker...")
        tracker.stop()
        sys.exit(0)