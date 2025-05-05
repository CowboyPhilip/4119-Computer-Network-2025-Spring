import socket
import threading
import time
import logging
import sys
import json
import hashlib
import random
from typing import Dict, Any, List, Tuple, Optional, Callable
from network import (
    Network, MSG_REGISTER, MSG_PEER_LIST, MSG_HEARTBEAT, 
    MSG_CHAIN_REQUEST, MSG_CHAIN_RESPONSE, MSG_NEW_BLOCK, MSG_NEW_TRANSACTION
)
from block123 import Blockchain, Block, Transaction
from crypto_utils import generate_key_pair

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Client(Network):
    """
    Client node in the P2P network that maintains a blockchain and participates
    in the consensus protocol.
    """
    
    def __init__(self, 
                 host: str, 
                 port: int, 
                 tracker_host: str, 
                 tracker_port: int,
                 topology_file: str = "topology.dat",
                 mining_difficulty: int = 4,
                 auto_mine: bool = False):
        """
        Initialize the client.
        
        Args:
            host: Host IP address
            port: Port to listen on
            tracker_host: Tracker's host
            tracker_port: Tracker's port
            topology_file: File containing network topology
            mining_difficulty: Difficulty for mining (proof-of-work)
            auto_mine: Whether to automatically mine blocks
        """
        super().__init__(host, port, topology_file)
        self.tracker_host = tracker_host
        self.tracker_port = tracker_port
        self.blockchain = Blockchain(mining_difficulty)
        self.auto_mine = auto_mine
        self.mining = False
        self.mining_thread = None
        self.heartbeat_thread = None
        self.peers = {}
        
        # Generate key pair for this client
        self.private_key, self.public_key = generate_key_pair()
        
        # Callback for UI updates
        self.ui_callback = None
    
    def set_ui_callback(self, callback: Callable[[str, Any], None]) -> None:
        """
        Set the callback function for UI updates.
        
        Args:
            callback: Function to call when UI updates are needed
        """
        self.ui_callback = callback
    
    def start(self) -> None:
        """Start the client."""
        super().start()
        
        # Register with tracker
        self._register_with_tracker()
        
        # Start heartbeat thread
        self.heartbeat_thread = threading.Thread(target=self._send_heartbeats)
        self.heartbeat_thread.daemon = True
        self.heartbeat_thread.start()
        
        # Start mining thread if auto-mine is enabled
        if self.auto_mine:
            self._start_mining()
        
        logger.info("Client is fully initialized and running")
    
    def stop(self) -> None:
        """Stop the client."""
        self.mining = False
        super().stop()
        logger.info("Client stopped")
    
    def _register_with_tracker(self) -> None:
        """Register this client with the tracker."""
        register_message = {
            'type': MSG_REGISTER,
            'data': {
                'host': self.host,
                'port': self.port
            },
            'timestamp': time.time(),
            'sender': self.id
        }
        
        success = self.send_message((self.tracker_host, self.tracker_port), register_message)
        
        if success:
            logger.info(f"Registered with tracker at {self.tracker_host}:{self.tracker_port}")
        else:
            logger.error("Failed to register with tracker")
    
    def _send_heartbeats(self) -> None:
        """Send regular heartbeats to the tracker."""
        while self.running:
            heartbeat_message = {
                'type': MSG_HEARTBEAT,
                'data': {
                    'blockchain': self.blockchain.to_dict()
                },
                'timestamp': time.time(),
                'sender': self.id
            }
            
            self.send_message((self.tracker_host, self.tracker_port), heartbeat_message)
            logger.debug("Sent heartbeat to tracker")
            
            # Sleep for 10 seconds
            time.sleep(10)
    
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
                
                if msg_type == MSG_PEER_LIST:
                    self._handle_peer_list(message)
                elif msg_type == MSG_CHAIN_REQUEST:
                    self._handle_chain_request(message, client_socket)
                elif msg_type == MSG_CHAIN_RESPONSE:
                    self._handle_chain_response(message)
                elif msg_type == MSG_NEW_BLOCK:
                    self._handle_new_block(message)
                elif msg_type == MSG_NEW_TRANSACTION:
                    self._handle_new_transaction(message)
                else:
                    logger.warning(f"Received unknown message type: {msg_type}")
            
            client_socket.close()
        except Exception as e:
            logger.error(f"Error handling client: {e}")
            client_socket.close()
    
    def _handle_peer_list(self, message: Dict[str, Any]) -> None:
        """
        Handle peer list message.
        
        Args:
            message: Peer list message
        """
        if 'data' in message:
            peer_list = message['data']
            
            # Update our peer list
            self.peers = {}
            for peer_id, peer_data in peer_list.items():
                if 'host' in peer_data and 'port' in peer_data:
                    host = peer_data['host']
                    port = int(peer_data['port'])
                    self.peers[peer_id] = (host, port)
            
            logger.info(f"Updated peer list: {len(self.peers)} peers")
            
            # Update UI if callback is set
            if self.ui_callback:
                self.ui_callback('peer_list_updated', self.peers)
    
    def _handle_chain_request(self, message: Dict[str, Any], client_socket: socket.socket) -> None:
        """
        Handle blockchain request.
        
        Args:
            message: Chain request message
            client_socket: Socket to respond on
        """
        # Send our blockchain
        response = {
            'type': MSG_CHAIN_RESPONSE,
            'data': self.blockchain.to_dict(),
            'timestamp': time.time(),
            'sender': self.id
        }
        
        # Serialize and send the response
        serialized_response = self.serialize_message(response)
        client_socket.sendall(serialized_response)
        
        logger.info(f"Sent blockchain to {message.get('sender', 'unknown')}")
    
    def _handle_chain_response(self, message: Dict[str, Any]) -> None:
        """
        Handle blockchain response.
        
        Args:
            message: Chain response message
        """
        if 'data' in message:
            blockchain_data = message['data']
            
            # Create a temporary blockchain from the data
            temp_chain = Blockchain.from_dict(blockchain_data)
            
            # If the received chain is longer and valid, update our chain
            if len(temp_chain.chain) > len(self.blockchain.chain) and temp_chain.is_chain_valid():
                self.blockchain = temp_chain
                logger.info(f"Updated blockchain from {message.get('sender', 'unknown')}")
                
                # Update UI if callback is set
                if self.ui_callback:
                    self.ui_callback('blockchain_updated', self.blockchain)
    
    def _handle_new_block(self, message: Dict[str, Any]) -> None:
        """
        Handle new block message.
        
        Args:
            message: New block message
        """
        if 'data' in message:
            block_data = message['data']
            
            # Create a Block object from the data
            try:
                block = Block.from_dict(block_data)
                
                # Verify the block
                if len(self.blockchain.chain) > 0 and self.blockchain.is_valid_new_block(block, self.blockchain.last_block):
                    # Add the block to our chain
                    self.blockchain.chain.append(block)
                    logger.info(f"Added new block from {message.get('sender', 'unknown')}")
                    
                    # Clear pending transactions that are now in the blockchain
                    self._clear_confirmed_transactions(block)
                    
                    # Update UI if callback is set
                    if self.ui_callback:
                        self.ui_callback('block_added', block)
                else:
                    # Request the full chain if this block doesn't fit
                    self._request_blockchain()
            except Exception as e:
                logger.error(f"Error processing new block: {e}")
    
    def _handle_new_transaction(self, message: Dict[str, Any]) -> None:
        """
        Handle new transaction message.
        
        Args:
            message: New transaction message
        """
        if 'data' in message:
            tx_data = message['data']
            
            # Create a Transaction object from the data
            try:
                transaction = Transaction.from_dict(tx_data)
                
                # Add the transaction to our pending transactions
                if self.blockchain.add_transaction(transaction, self._verify_signature):
                    logger.info(f"Added new transaction from {message.get('sender', 'unknown')}")
                    
                    # Update UI if callback is set
                    if self.ui_callback:
                        self.ui_callback('transaction_added', transaction)
                    
                    # Start mining if auto-mine is enabled
                    if self.auto_mine and not self.mining:
                        self._start_mining()
                else:
                    logger.warning(f"Invalid transaction from {message.get('sender', 'unknown')}")
            except Exception as e:
                logger.error(f"Error processing new transaction: {e}")
    
    def _clear_confirmed_transactions(self, block: Block) -> None:
        """
        Clear transactions that are now confirmed in a block.
        
        Args:
            block: The block containing confirmed transactions
        """
        # Get all transaction IDs in the block
        block_tx_ids = [tx.transaction_id for tx in block.transactions]
        
        # Remove transactions that are now in the blockchain
        self.blockchain.pending_transactions = [
            tx for tx in self.blockchain.pending_transactions 
            if tx.transaction_id not in block_tx_ids
        ]
    
    def _verify_signature(self, tx_hash: str, signature: str, public_key: str) -> bool:
        """
        Verify a transaction signature.
        
        Args:
            tx_hash: Hash of the transaction
            signature: Signature to verify
            public_key: Public key to verify with
            
        Returns:
            True if the signature is valid, False otherwise
        """
        # In a real implementation, this would use cryptographic verification
        # For simplicity, we'll just return True
        return True
    
    def _request_blockchain(self) -> None:
        """Request the blockchain from peers."""
        request = {
            'type': MSG_CHAIN_REQUEST,
            'data': None,
            'timestamp': time.time(),
            'sender': self.id
        }
        
        # Send to a random peer
        if self.peers:
            peer_id = random.choice(list(self.peers.keys()))
            host, port = self.peers[peer_id]
            
            self.send_message((host, port), request)
            logger.info(f"Requested blockchain from {peer_id}")
    
    def _start_mining(self) -> None:
        """Start the mining process in a separate thread."""
        if not self.mining and self.blockchain.pending_transactions:
            self.mining = True
            
            self.mining_thread = threading.Thread(target=self._mine_block)
            self.mining_thread.daemon = True
            self.mining_thread.start()
            
            logger.info("Started mining process")
    
    def _mine_block(self) -> None:
        """Mine a new block with pending transactions."""
        try:
            # Mine a new block
            new_block = self.blockchain.mine_pending_transactions(self.id)
            
            if new_block:
                logger.info(f"Mined new block: {new_block.index}")
                
                # Broadcast the new block
                self._broadcast_block(new_block)
                
                # Update UI if callback is set
                if self.ui_callback:
                    self.ui_callback('block_mined', new_block)
        except Exception as e:
            logger.error(f"Error mining block: {e}")
        
        self.mining = False
    
    def _broadcast_block(self, block: Block) -> None:
        """
        Broadcast a new block to all peers.
        
        Args:
            block: Block to broadcast
        """
        message = {
            'type': MSG_NEW_BLOCK,
            'data': block.to_dict(),
            'timestamp': time.time(),
            'sender': self.id
        }
        
        # Broadcast to neighbors according to topology
        self.broadcast_to_neighbors(message)
        logger.info(f"Broadcast block {block.index} to neighbors")
    
    def create_transaction(self, vote_data: Dict[str, Any]) -> bool:
        """
        Create a new vote transaction and broadcast it.
        
        Args:
            vote_data: Vote data (e.g., candidate, proposal)
            
        Returns:
            True if the transaction was created, False otherwise
        """
        # Check if this client has already voted
        if self.blockchain.has_voter_voted(self.public_key):
            logger.warning("This client has already voted")
            return False
        
        # Create a new transaction
        transaction = Transaction(
            voter_id=self.public_key,
            vote_data=vote_data
        )
        
        # Sign the transaction (in a real implementation)
        # For simplicity, we'll just use a hash
        transaction.signature = hashlib.sha256(
            (transaction.transaction_id + self.public_key).encode()
        ).hexdigest()
        
        # Add the transaction to our pending transactions
        if self.blockchain.add_transaction(transaction, self._verify_signature):
            logger.info(f"Created new transaction: {transaction.transaction_id}")
            
            # Broadcast the transaction
            self._broadcast_transaction(transaction)
            
            # Start mining if auto-mine is enabled
            if self.auto_mine and not self.mining:
                self._start_mining()
            
            # Update UI if callback is set
            if self.ui_callback:
                self.ui_callback('transaction_created', transaction)
            
            return True
        
        return False
    
    def _broadcast_transaction(self, transaction: Transaction) -> None:
        """
        Broadcast a new transaction to all peers.
        
        Args:
            transaction: Transaction to broadcast
        """
        message = {
            'type': MSG_NEW_TRANSACTION,
            'data': transaction.to_dict(),
            'timestamp': time.time(),
            'sender': self.id
        }
        
        # Broadcast to neighbors according to topology
        self.broadcast_to_neighbors(message)
        logger.info(f"Broadcast transaction {transaction.transaction_id} to neighbors")
    
    def get_blockchain_info(self) -> Dict[str, Any]:
        """
        Get information about the blockchain.
        
        Returns:
            Dictionary with blockchain information
        """
        info = {
            'chain_length': len(self.blockchain.chain),
            'pending_transactions': len(self.blockchain.pending_transactions),
            'last_block_hash': self.blockchain.last_block.hash if self.blockchain.chain else None,
            'difficulty': self.blockchain.difficulty,
            'mining': self.mining
        }
        
        return info
    
    def get_vote_results(self) -> Dict[str, int]:
        """
        Get the current vote results.
        
        Returns:
            Dictionary with voting results
        """
        return self.blockchain.get_vote_results()
    
    def manually_mine_block(self) -> bool:
        """
        Manually start the mining process.
        
        Returns:
            True if mining started, False otherwise
        """
        if not self.mining and self.blockchain.pending_transactions:
            self._start_mining()
            return True
        
        return False
    
    def get_peers(self):
        return self.peers


if __name__ == "__main__":
    # Parse command line arguments
    if len(sys.argv) < 5:
        print(f"Usage: {sys.argv[0]} <host> <port> <tracker_host> <tracker_port> [topology_file] [mining_difficulty] [auto_mine]")
        sys.exit(1)
    
    host = sys.argv[1]
    port = int(sys.argv[2])
    tracker_host = sys.argv[3]
    tracker_port = int(sys.argv[4])
    topology_file = sys.argv[5] if len(sys.argv) > 5 else "topology.dat"
    mining_difficulty = int(sys.argv[6]) if len(sys.argv) > 6 else 4
    auto_mine = sys.argv[7].lower() == "true" if len(sys.argv) > 7 else False
    
    # Create and start client
    client = Client(host, port, tracker_host, tracker_port, topology_file, mining_difficulty, auto_mine)
    
    try:
        client.start()
        
        # Simple command line interface
        print("Client started. Commands:")
        print("  create <choice> - Create a vote transaction")
        print("  mine - Manually mine a block")
        print("  results - Show voting results")
        print("  info - Show blockchain info")
        print("  exit - Exit the client")
        
        while True:
            command = input("> ").strip().split()
            
            if not command:
                continue
            
            if command[0] == "create" and len(command) > 1:
                choice = command[1]
                result = client.create_transaction({'choice': choice})
                print(f"Transaction created: {result}")
            elif command[0] == "mine":
                result = client.manually_mine_block()
                print(f"Mining started: {result}")
            elif command[0] == "results":
                results = client.get_vote_results()
                print("Vote results:")
                for choice, count in results.items():
                    print(f"  {choice}: {count} votes")
            elif command[0] == "info":
                info = client.get_blockchain_info()
                print("Blockchain info:")
                for key, value in info.items():
                    print(f"  {key}: {value}")
            elif command[0] == "exit":
                break
            else:
                print("Unknown command")
    
    except KeyboardInterrupt:
        print("Shutting down client...")
    
    finally:
        client.stop()
        sys.exit(0)