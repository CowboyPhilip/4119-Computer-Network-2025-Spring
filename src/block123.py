import hashlib
import json
import time
from typing import List, Dict, Any, Optional
import uuid


class Transaction:
    """Represents a vote transaction in the blockchain."""
    
    def __init__(self, voter_id: str, vote_data: Dict[str, Any], signature: str = None, 
                 transaction_id: str = None, timestamp: float = None):
        """
        Initialize a new transaction.
        
        Args:
            voter_id: The ID of the voter (public key)
            vote_data: The vote data (e.g., candidate, proposal)
            signature: Digital signature of the transaction
            transaction_id: Unique ID for this transaction
            timestamp: Time when transaction was created
        """
        self.transaction_id = transaction_id if transaction_id else str(uuid.uuid4())
        self.voter_id = voter_id
        self.vote_data = vote_data
        self.signature = signature
        self.timestamp = timestamp if timestamp else time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert transaction to dictionary for hashing and serialization."""
        return {
            'transaction_id': self.transaction_id,
            'voter_id': self.voter_id,
            'vote_data': self.vote_data,
            'signature': self.signature,
            'timestamp': self.timestamp
        }
    
    def compute_hash(self) -> str:
        """Compute SHA-256 hash of the transaction."""
        # Create a copy without the signature for hashing
        tx_dict = self.to_dict()
        tx_dict.pop('signature', None)
        
        transaction_string = json.dumps(tx_dict, sort_keys=True).encode()
        return hashlib.sha256(transaction_string).hexdigest()
    
    @staticmethod
    def from_dict(tx_dict: Dict[str, Any]) -> 'Transaction':
        """Create a Transaction object from a dictionary."""
        return Transaction(
            voter_id=tx_dict['voter_id'],
            vote_data=tx_dict['vote_data'],
            signature=tx_dict.get('signature'),
            transaction_id=tx_dict.get('transaction_id'),
            timestamp=tx_dict.get('timestamp')
        )
    
    @staticmethod
    def verify_signature(tx_dict: Dict[str, Any], public_key_func) -> bool:
        """
        Verify the signature of a transaction using the provided public key function.
        
        Args:
            tx_dict: Dictionary representation of the transaction
            public_key_func: Function to verify signature using public key
            
        Returns:
            True if the signature is valid, False otherwise
        """
        # In a real implementation, this would use cryptographic verification
        # For simplicity, we're using a function passed in
        try:
            # Create a copy without the signature for verification
            tx_copy = tx_dict.copy()
            signature = tx_copy.pop('signature', None)
            
            if not signature:
                return False
                
            # Hash the transaction data
            tx_string = json.dumps(tx_copy, sort_keys=True).encode()
            tx_hash = hashlib.sha256(tx_string).hexdigest()
            
            # Verify the signature
            return public_key_func(tx_hash, signature, tx_dict['voter_id'])
        except Exception as e:
            print(f"Signature verification failed: {e}")
            return False


class Block:
    """Represents a block in the blockchain."""
    
    def __init__(self, index: int, transactions: List[Transaction], previous_hash: str,
                 timestamp: float = None, nonce: int = 0, hash: str = None):
        """
        Initialize a new block.
        
        Args:
            index: Block number in the chain
            transactions: List of transactions in the block
            previous_hash: Hash of the previous block
            timestamp: Time of block creation
            nonce: Number used in mining (proof-of-work)
            hash: Hash of this block (if already computed)
        """
        self.index = index
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.timestamp = timestamp if timestamp else time.time()
        self.nonce = nonce
        self.merkle_root = self.calculate_merkle_root()
        self.hash = hash if hash else self.compute_hash()
    
    def calculate_merkle_root(self) -> str:
        """Calculate the Merkle root of the transactions."""
        if not self.transactions:
            return hashlib.sha256("".encode()).hexdigest()
        
        # Get transaction hashes
        tx_hashes = [tx.compute_hash() for tx in self.transactions]
        
        # Calculate Merkle root by hashing pairs of hashes until we have one hash
        while len(tx_hashes) > 1:
            # If odd number of hashes, duplicate the last one
            if len(tx_hashes) % 2 != 0:
                tx_hashes.append(tx_hashes[-1])
            
            # Hash pairs and create new level
            next_level = []
            for i in range(0, len(tx_hashes), 2):
                combined = tx_hashes[i] + tx_hashes[i+1]
                next_level.append(hashlib.sha256(combined.encode()).hexdigest())
            
            tx_hashes = next_level
        
        return tx_hashes[0] if tx_hashes else hashlib.sha256("".encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert block to dictionary for hashing and serialization."""
        return {
            'index': self.index,
            'transactions': [tx.to_dict() for tx in self.transactions],
            'previous_hash': self.previous_hash,
            'timestamp': self.timestamp,
            'nonce': self.nonce,
            'merkle_root': self.merkle_root
        }
    
    def compute_hash(self) -> str:
        """Compute SHA-256 hash of the block."""
        block_string = json.dumps(self.to_dict(), sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()
    
    def mine_block(self, difficulty: int) -> None:
        """
        Perform proof-of-work to find a valid hash.
        
        Args:
            difficulty: Number of leading zeros required in the hash
        """
        target = '0' * difficulty
        
        while not self.hash.startswith(target):
            self.nonce += 1
            self.hash = self.compute_hash()
    
    @staticmethod
    def from_dict(block_dict: Dict[str, Any]) -> 'Block':
        """Create a Block object from a dictionary."""
        transactions = [Transaction.from_dict(tx) for tx in block_dict.get('transactions', [])]
        
        return Block(
            index=block_dict['index'],
            transactions=transactions,
            previous_hash=block_dict['previous_hash'],
            timestamp=block_dict.get('timestamp'),
            nonce=block_dict.get('nonce', 0),
            hash=block_dict.get('hash')
        )


class Blockchain:
    """Implements a blockchain for the voting system."""
    
    def __init__(self, difficulty: int = 4):
        """
        Initialize a new blockchain.
        
        Args:
            difficulty: Mining difficulty (number of leading zeros required)
        """
        self.difficulty = difficulty
        self.chain = []
        self.pending_transactions = []
        
        # Create the genesis block
        self.create_genesis_block()
    
    def create_genesis_block(self) -> None:
        """Create the first block in the chain (genesis block)."""
        genesis_block = Block(0, [], "0")
        self.chain.append(genesis_block)
    
    @property
    def last_block(self) -> Block:
        """Get the last block in the chain."""
        return self.chain[-1]
    
    def add_transaction(self, transaction: Transaction, verify_signature_func=None) -> bool:
        """
        Add a new transaction to the pending transactions.
        
        Args:
            transaction: The transaction to add
            verify_signature_func: Function to verify signature (optional)
            
        Returns:
            True if transaction was added, False otherwise
        """
        # Check if this voter has already voted
        if self.has_voter_voted(transaction.voter_id):
            print(f"Voter {transaction.voter_id} has already voted")
            return False
        
        # Verify the signature if a verification function is provided
        if verify_signature_func and not Transaction.verify_signature(
                transaction.to_dict(), verify_signature_func):
            print(f"Invalid signature for transaction {transaction.transaction_id}")
            return False
        
        self.pending_transactions.append(transaction)
        return True
    
    def has_voter_voted(self, voter_id: str) -> bool:
        """
        Check if a voter has already voted.
        
        Args:
            voter_id: The ID of the voter to check
            
        Returns:
            True if the voter has voted, False otherwise
        """
        # Check pending transactions
        for tx in self.pending_transactions:
            if tx.voter_id == voter_id:
                return True
        
        # Check transactions in the blockchain
        for block in self.chain:
            for tx in block.transactions:
                if tx.voter_id == voter_id:
                    return True
        
        return False
    
    def mine_pending_transactions(self, miner_id: str) -> Optional[Block]:
        """
        Mine a new block with all pending transactions.
        
        Args:
            miner_id: ID of the miner
            
        Returns:
            The newly mined block, or None if no transactions to mine
        """
        if not self.pending_transactions:
            return None
        
        # Create a new block with all pending transactions
        new_block = Block(
            index=len(self.chain),
            transactions=self.pending_transactions,
            previous_hash=self.last_block.hash
        )
        
        # Mine the block
        new_block.mine_block(self.difficulty)
        
        # Add the block to the chain
        self.chain.append(new_block)
        
        # Clear the pending transactions
        self.pending_transactions = []
        
        return new_block
    
    def is_chain_valid(self) -> bool:
        """
        Validate the entire blockchain.
        
        Returns:
            True if the chain is valid, False otherwise
        """
        # Check each block in the chain
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]
            
            # Check if the hash is correct
            if current_block.hash != current_block.compute_hash():
                print(f"Block {i} has an invalid hash")
                return False
            
            # Check if the previous hash link is correct
            if current_block.previous_hash != previous_block.hash:
                print(f"Block {i} has an invalid previous hash link")
                return False
            
            # Check if the proof of work is valid
            if not current_block.hash.startswith('0' * self.difficulty):
                print(f"Block {i} does not have a valid proof-of-work")
                return False
        
        return True
    
    def is_valid_new_block(self, new_block: Block, previous_block: Block) -> bool:
        """
        Check if a new block is valid.
        
        Args:
            new_block: The block to check
            previous_block: The previous block
            
        Returns:
            True if the block is valid, False otherwise
        """
        # Check if the hash is correct
        if new_block.hash != new_block.compute_hash():
            return False
        
        # Check if the previous hash link is correct
        if new_block.previous_hash != previous_block.hash:
            return False
        
        # Check if the proof of work is valid
        if not new_block.hash.startswith('0' * self.difficulty):
            return False
        
        # Check if the index is correct
        if new_block.index != previous_block.index + 1:
            return False
        
        return True
    
    def resolve_conflicts(self, chains: List[List[Dict]]) -> bool:
        """
        Resolve conflicts between chains by selecting the longest valid chain.
        
        Args:
            chains: List of chains from other nodes
            
        Returns:
            True if our chain was replaced, False otherwise
        """
        max_length = len(self.chain)
        new_chain = None
        
        # Find the longest valid chain
        for chain_data in chains:
            # Convert dictionary to Block objects
            chain = [Block.from_dict(block_dict) for block_dict in chain_data]
            
            # Check length and validity
            if len(chain) > max_length and self.validate_chain(chain):
                max_length = len(chain)
                new_chain = chain
        
        # Replace our chain if a longer valid chain was found
        if new_chain:
            self.chain = new_chain
            return True
        
        return False
    
    def validate_chain(self, chain: List[Block]) -> bool:
        """
        Validate a chain from another node.
        
        Args:
            chain: The chain to validate
            
        Returns:
            True if the chain is valid, False otherwise
        """
        # Check the genesis block
        if len(chain) == 0 or chain[0].hash != self.chain[0].hash:
            return False
        
        # Check each block in the chain
        for i in range(1, len(chain)):
            current_block = chain[i]
            previous_block = chain[i-1]
            
            # Validate the block
            if not self.is_valid_new_block(current_block, previous_block):
                return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert blockchain to dictionary for serialization."""
        return {
            'chain': [block.to_dict() for block in self.chain],
            'pending_transactions': [tx.to_dict() for tx in self.pending_transactions],
            'difficulty': self.difficulty
        }
    
    @staticmethod
    def from_dict(blockchain_dict: Dict[str, Any]) -> 'Blockchain':
        """Create a Blockchain object from a dictionary."""
        blockchain = Blockchain(blockchain_dict.get('difficulty', 4))
        
        # Clear the genesis block
        blockchain.chain = []
        
        # Add all blocks
        for block_dict in blockchain_dict.get('chain', []):
            blockchain.chain.append(Block.from_dict(block_dict))
        
        # Add pending transactions
        for tx_dict in blockchain_dict.get('pending_transactions', []):
            blockchain.pending_transactions.append(Transaction.from_dict(tx_dict))
        
        return blockchain
    
    def get_vote_results(self) -> Dict[str, int]:
        """
        Get the results of the vote.
        
        Returns:
            Dictionary with candidate/option as key and vote count as value
        """
        results = {}
        
        # Count votes in the blockchain
        for block in self.chain:
            for tx in block.transactions:
                # Assuming vote_data has a 'choice' field
                choice = tx.vote_data.get('choice')
                if choice:
                    results[choice] = results.get(choice, 0) + 1
        
        return results