import socket
import json
import time
from typing import Dict, Any, List, Tuple, Optional
import threading
import os
import logging


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Message types
MSG_NEW_BLOCK = "NEW_BLOCK"
MSG_PEER_LIST = "PEER_LIST"
MSG_GET_MINER = "GET_MINER"
MSG_CHAIN_REQUEST = "CHAIN_REQUEST"
MSG_CHAIN_RESPONSE = "CHAIN_RESPONSE"
MSG_NEW_TRANSACTION = "NEW_TRANSACTION"
MSG_REGISTER = "REGISTER"
MSG_HEARTBEAT = "HEARTBEAT"

class Network:
    """Handles network operations for the blockchain."""
    
    def __init__(self, host: str, port: int, topology_file: str = "topology.dat"):
        """
        Initialize the network.
        
        Args:
            host: Host IP address
            port: Port to listen on
            topology_file: File containing network topology
        """
        self.host = host
        self.port = port
        self.id = f"{host}:{port}"
        self.peers = {}  # {peer_id: (host, port)}
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.running = False
        self.topology_file = topology_file
        self.neighbor_peers = []  # List of peer IDs that are neighbors in the topology
        
        # Load network topology if file exists
        self._load_topology()
        
    def _load_topology(self) -> None:
        """Load network topology from file."""
        if os.path.exists(self.topology_file):
            try:
                with open(self.topology_file, 'r') as f:
                    lines = f.readlines()
                    
                for line in lines:
                    if line.strip():
                        parts = line.strip().split('->')
                        if len(parts) == 2:
                            source = parts[0].strip()
                            destinations = [d.strip() for d in parts[1].split(',')]
                            
                            if source == self.id:
                                self.neighbor_peers = destinations
                                logger.info(f"Loaded neighbors from topology: {self.neighbor_peers}")
            except Exception as e:
                logger.error(f"Error loading topology: {e}")
    
    def start(self) -> None:
        """Start the network server."""
        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            self.running = True
            logger.info(f"Network server started on {self.host}:{self.port}")
            
            # Start listening thread
            listen_thread = threading.Thread(target=self._listen)
            listen_thread.daemon = True
            listen_thread.start()
        except Exception as e:
            logger.error(f"Error starting network: {e}")
            raise
    
    def stop(self) -> None:
        """Stop the network server."""
        self.running = False
        self.socket.close()
        logger.info("Network server stopped")
    
    def _listen(self) -> None:
        """Listen for incoming connections."""
        while self.running:
            try:
                client_socket, address = self.socket.accept()
                logger.debug(f"Connection from {address}")
                
                # Handle client in a new thread
                client_thread = threading.Thread(target=self._handle_client, args=(client_socket,))
                client_thread.daemon = True
                client_thread.start()
            except Exception as e:
                if self.running:
                    logger.error(f"Error accepting connection: {e}")
    
    def _handle_client(self, client_socket: socket.socket) -> None:
        """
        Handle client connection.
        
        Args:
            client_socket: The client socket
        """
        try:
            # Receive data
            message = self.receive_message(client_socket)
            
            if message and 'type' in message:
                # Process the message based on its type
                logger.debug(f"Received message of type {message['type']} from {message.get('sender', 'unknown')}")
                
                # The actual message handling will be done by the client/tracker classes
                # This method will be overridden in those classes
                
            client_socket.close()
        except Exception as e:
            logger.error(f"Error handling client: {e}")
            client_socket.close()
    
    def send_message(self, destination: Tuple[str, int], message: Dict[str, Any]) -> bool:
        """
        Send a message to a peer.
        
        Args:
            destination: Tuple of (host, port)
            message: Message to send
            
        Returns:
            True if message was sent successfully, False otherwise
        """
        try:
            # Add sender information
            if 'sender' not in message:
                message['sender'] = self.id
            
            # Add timestamp
            if 'timestamp' not in message:
                message['timestamp'] = time.time()
            
            # Connect to the peer
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(5)  # 5 second timeout
            client_socket.connect(destination)
            
            # Serialize and send the message
            serialized_message = self.serialize_message(message)
            client_socket.sendall(serialized_message)
            
            client_socket.close()
            return True
        except Exception as e:
            logger.error(f"Error sending message to {destination}: {e}")
            return False
    
    def broadcast_to_neighbors(self, message: Dict[str, Any]) -> None:
        """
        Broadcast a message to all neighbor peers based on topology.
        
        Args:
            message: Message to broadcast
        """
        for peer_id in self.neighbor_peers:
            if peer_id in self.peers:
                host, port = self.peers[peer_id]
                self.send_message((host, port), message)
    
    def broadcast_to_all(self, message: Dict[str, Any]) -> None:
        """
        Broadcast a message to all peers.
        
        Args:
            message: Message to broadcast
        """
        for peer_id, (host, port) in self.peers.items():
            if peer_id != self.id:  # Don't send to self
                self.send_message((host, port), message)
    
    @staticmethod
    def serialize_message(message: Dict[str, Any]) -> bytes:
        """
        Serialize a message to JSON.
        
        Args:
            message: Message to serialize
            
        Returns:
            Serialized message as bytes
        """
        try:
            # Convert message to JSON
            json_message = json.dumps(message).encode('utf-8')
            
            # Prepend message length for proper receiving
            message_length = len(json_message)
            length_bytes = message_length.to_bytes(4, byteorder='big')
            
            return length_bytes + json_message
        except Exception as e:
            logger.error(f"Error serializing message: {e}")
            raise
    
    @staticmethod
    def receive_message(client_socket: socket.socket) -> Optional[Dict[str, Any]]:
        """
        Receive a message from a socket.
        
        Args:
            client_socket: Socket to receive from
            
        Returns:
            Received message as dictionary, or None if error
        """
        try:
            # Receive message length (first 4 bytes)
            length_bytes = client_socket.recv(4)
            if not length_bytes:
                return None
            
            message_length = int.from_bytes(length_bytes, byteorder='big')
            
            # Receive the message data
            chunks = []
            bytes_received = 0
            
            while bytes_received < message_length:
                chunk = client_socket.recv(min(message_length - bytes_received, 4096))
                if not chunk:
                    break
                chunks.append(chunk)
                bytes_received += len(chunk)
            
            message_data = b''.join(chunks)
            
            # Deserialize the message
            return json.loads(message_data.decode('utf-8'))
        except Exception as e:
            logger.error(f"Error receiving message: {e}")
            return None