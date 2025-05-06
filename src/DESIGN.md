# Decentralized Voting System Design

This document describes the design and implementation details of our decentralized voting system based on blockchain technology.

## 1. System Architecture

The system is composed of three main components:

1. **Blockchain Core**: The fundamental data structure and algorithms
2. **P2P Network**: Communication layer between nodes
3. **Voting Application**: User interface and application logic

### 1.1 High-Level Architecture

```
                      +----------------+
                      |                |
                      |    Tracker     |
                      |                |
                      +----------------+
                              |
              +---------------+---------------+
              |               |               |
    +-----------------+ +-----------------+ +-----------------+
    |                 | |                 | |                 |
    |  Peer Node 1    | |  Peer Node 2    | |  Peer Node 3    |
    | (with Voting UI)| | (with Voting UI)| | (with Voting UI)|
    |                 | |                 | |                 |
    +-----------------+ +-----------------+ +-----------------+
```

## 2. Blockchain Design

### 2.1 Block Structure

Each block in the blockchain has the following structure:

```
+------------------------+
| Block Header           |
|  - Index               |
|  - Timestamp           |
|  - Previous Block Hash |
|  - Merkle Root         |
|  - Nonce               |
+------------------------+
| Transactions           |
|  - Vote Transactions   |
+------------------------+
```

- **Index**: Position of the block in the blockchain
- **Timestamp**: Time when the block was created
- **Previous Block Hash**: Hash of the previous block for chain integrity
- **Merkle Root**: Root of the Merkle tree of transactions
- **Nonce**: Value used for Proof-of-Work mining
- **Transactions**: List of vote transactions in the block
- **Miner ID**: Id of the miner working on the block
- **Stake Value**: Stake value of the miner working on the block, used for 
                     Proof-of-Stake mining

### 2.2 Transaction Structure

```
+------------------------+
| Transaction            |
|  - Transaction ID      |
|  - Voter ID            |
|  - Vote Data           |
|  - Signature           |
|  - Timestamp           |
+------------------------+
```

- **Transaction ID**: Unique identifier for the transaction
- **Voter ID**: Public key of the voter
- **Vote Data**: The actual vote content (candidate, proposal, etc.)
- **Signature**: Digital signature of the transaction
- **Timestamp**: Time when the transaction was created

### 2.3 Consensus Mechanism

The system uses two primary mechanisms for consensus:

1. **Proof-of-Stake (PoS)**: 
   - Miners must find a nonce value that results in a block hash with a specified 
      number of leading zeros, refered to as the 'mining difficulty' of the block.
   - The mining difficulty of any given block is determined by the stake value of the 
      miner working on the block. Stake values for miners are stored and updated by the tracker when resolving the canonical chain.

2. **Longest Chain by Total Stake Rule**:
   - In case of forks, nodes follow the longest valid chain.
   - In case of a tie between two or more valid chains of equal length, the chain with 
      the highest total stake value (sum of all stake values in a chain's blocks) will be selected.
   - This ensures that the network converges to a single canonical chain.

### 2.4 Fork Resolution

When a fork occurs (two blocks are mined at a similar time):
1. Each node receives both blocks and maintains awareness of both chains.
2. Nodes continue adding to the chain they received first.
3. The longest chain by total stake rule determines the canonical chain.
4. When a chain becomes longer, nodes switch to that chain.

## 3. P2P Network Protocol

### 3.1 Network Components

1. **Tracker**:
   - Central registry of active peers
   - Distributes peer lists
   - Helps with initial network bootstrapping
   - Monitors the network via heartbeats

2. **Peer Nodes**:
   - Connect to the tracker and other peers
   - Maintain a local copy of the blockchain
   - Broadcast and receive transactions and blocks
   - Mine new blocks

### 3.2 Communication Protocol

All messages in the network follow this JSON format:
```json
{
  "type": "MESSAGE_TYPE",
  "data": { /* Message-specific data */ },
  "timestamp": "TIMESTAMP",
  "sender": "NODE_ID"
}
```

### 3.3 Message Types

1. **REGISTER**:
   - Sent by peers to register with the tracker
   - Contains peer information (host, port)

2. **PEER_LIST**:
   - Sent by the tracker to update peers about network changes
   - Contains a list of active peers

3. **NEW_BLOCK**:
   - Broadcast when a new block is mined
   - Contains the serialized block data

4. **NEW_TRANSACTION**:
   - Broadcast when a new vote transaction is created
   - Contains the serialized transaction data

5. **CHAIN_REQUEST**:
   - Sent to request the blockchain from another peer
   - Used for synchronization

6. **CHAIN_RESPONSE**:
   - Response to a chain request
   - Contains the serialized blockchain data

7. **HEARTBEAT**:
   - Sent periodically by peers to the tracker
   - Indicates the peer is still active
   - Contains the current blockchain state

8. **GET_MINER**:
   - Sent by a peer to the tracker
   - Used to access a peer's miner id and stake value tied to mining a block

9. **GET_VOTE_RESULTS**:
   - Sent by peer to the tracker or the tracker to the peer
   - Used to request or broadcast tracker's voting results

### 3.4 Network Topology

The network topology is defined in a configuration file (`topology.dat`):
- Each node has a list of neighboring nodes.
- Messages are broadcast according to this topology.
- This simulates a real P2P network with limited connectivity.

## 4. Voting Application Design

### 4.1 Application Features

The voting application provides:

1. **Voter Registration**:
   - Each client generates a key pair for identity and signing.
   - No additional registration is necessary beyond joining the network.

2. **Vote Casting**:
   - Users select a candidate/option through the UI.
   - A signed transaction is created and broadcast to the network.
   - Preventing double-voting is ensured through blockchain validation.

3. **Result Display**:
   - Real-time counting of votes from the blockchain.
   - Visual representation of voting results.

4. **Blockchain Explorer**:
   - View the current state of the blockchain.
   - Inspect blocks and transactions.

### 4.2 User Interface

The UI's (both windowed and web) has four main tabs:

1. **Vote Tab**:
   - Vote casting controls
   - Transaction log

2. **Blockchain Tab**:
   - Blockchain information
   - Block explorer

3. **Results Tab**:
   - Vote tallying
   - Results visualization

4. **Network Tab**:
   - Peer list
   - Network status

## 5. Security Design

### 5.1 Transaction Integrity

- Each transaction is signed with the voter's private key.
- Signatures are verified before accepting transactions.
- Merkle trees efficiently verify transaction integrity within blocks.

### 5.2 Double-Voting Prevention

- The blockchain is checked to ensure each voter can only vote once.
- This check happens both when:
  - Adding transactions to the pending pool
  - Validating blocks from other peers

### 5.3 Tamper Resistance

- Each block contains the hash of the previous block.
- Changing a block would invalidate all subsequent blocks.
- Proof-of-Work makes it computationally expensive to alter the blockchain.
- Proof-of-Stake adds a security measure to punish potentially malicious peers. 

## 6. Implementation Notes

### 6.1 Simplified Cryptography

For educational purposes, the current implementation uses:
- Simplified key generation (hash-based)
- Simplified digital signatures
- A real implementation would use proper cryptographic libraries

### 6.2 Local Network Simulation

- The P2P network is simulated locally.
- Network delays and failures are not fully modeled.
- A production system would need more robust networking.

### 6.3 Scalability Considerations

The current implementation has limitations:
- All nodes store the complete blockchain.
- No optimization for large-scale voting.

A production system would need:
- Sharding for scalability
- Optimized storage and verification

## 7. Future Enhancements

Potential improvements include:

1. **Advanced Cryptography**:
   - Implement proper asymmetric cryptography
   - Add zero-knowledge proofs for privacy

2. **Smart Contracts**:
   - Implement voting rules as smart contracts
   - Allow for more complex voting mechanisms

3. **Enhanced Security**:
   - Add more robust network security features

4. **Scalability Improvements**:
   - Implement sharding for horizontal scaling
   - Optimize storage with pruning techniques

5. **User Experience**:
   - Add mobile application support
   - Improve visualization and analytics