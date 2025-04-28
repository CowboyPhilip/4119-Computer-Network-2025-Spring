# Decentralized Voting System

A peer-to-peer blockchain-based voting system that allows users to cast votes in a secure, transparent, and decentralized manner.

## Overview

This project implements a simplified peer-to-peer blockchain network with a voting application. The system consists of:

1. A tracker node that coordinates the network
2. Multiple peer nodes that maintain the blockchain
3. A voting application interface for users to cast votes

## Features

- **P2P Network**: Decentralized network with peer discovery
- **Blockchain Implementation**: Secure, tamper-resistant ledger
- **Consensus Mechanism**: Proof-of-work mining and longest chain rule
- **Voting System**: Secure voting with prevention of double voting
- **GUI Interface**: User-friendly interface for voting and blockchain visualization

## Requirements

- Python 3.7 or higher
- Required Python packages:
  - tkinter (for GUI)

## Project Structure

```
├── block.py              # Blockchain implementation
├── client.py             # Client peer implementation
├── crypto_utils.py       # Cryptographic utilities
├── network.py            # Network communication layer
├── tracker.py            # Tracker node implementation
├── voting_app.py         # GUI application
├── topology.dat          # Network topology configuration
├── start_network.py      # Script to start the network
├── README.md             # Project documentation
├── DESIGN.md             # Design documentation
└── TESTING.md            # Testing documentation
```

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/decentralized-voting.git
   cd decentralized-voting
   ```

2. Make sure Python 3.7+ is installed.

3. Make sure tkinter is installed (for GUI). On Debian/Ubuntu systems:
   ```
   sudo apt-get install python3-tk
   ```

## Usage

### Starting the Network

The easiest way to start the network is using the provided script:

```
python start_network.py --peers 3 --difficulty 4 --auto-mine
```

Options:
- `--peers`: Number of peer nodes to start (default: 3)
- `--difficulty`: Mining difficulty (default: 4)
- `--auto-mine`: Enable automatic mining on peers

### Running Components Individually

#### Start the Tracker

```
python tracker.py <host> <port> [topology_file]
```

Example:
```
python tracker.py 127.0.0.1 5000 topology.dat
```

#### Start a Client Node with GUI

```
python voting_app.py <host> <port> <tracker_host> <tracker_port> [topology_file] [mining_difficulty] [auto_mine]
```

Example:
```
python voting_app.py 127.0.0.1 5001 127.0.0.1 5000 topology.dat 4 true
```

#### Start a Client Node without GUI

```
python client.py <host> <port> <tracker_host> <tracker_port> [topology_file] [mining_difficulty] [auto_mine]
```

Example:
```
python client.py 127.0.0.1 5001 127.0.0.1 5000 topology.dat 4 true
```

### Using the Voting Application

1. **Cast a Vote**: Select a candidate from the dropdown menu and click "Cast Vote". Each client can only vote once.

2. **Mine Blocks**: Click "Mine Block" to mine a new block with pending transactions. If auto-mine is enabled, blocks will be mined automatically when transactions are available.

3. **View Blockchain**: The "Blockchain" tab shows the current state of the blockchain with all blocks.

4. **View Results**: The "Results" tab shows a chart of the current voting results.

5. **View Network**: The "Network" tab shows information about connected peers.

## Network Topology

The network topology is defined in the `topology.dat` file. Each line defines a node and its neighboring nodes in the format:

```
<node_id> -> <neighbor1>, <neighbor2>, ...
```

Example:
```
127.0.0.1:5001 -> 127.0.0.1:5002, 127.0.0.1:5003
127.0.0.1:5002 -> 127.0.0.1:5001, 127.0.0.1:5003
```

## Blockchain Design

The blockchain consists of:

- **Block**: Contains transactions, timestamp, previous block hash, and proof-of-work.
- **Transaction**: Represents a vote with voter ID, vote data, and signature.
- **Merkle Tree**: Used for efficiently verifying transaction integrity.

### Consensus Algorithm

The system uses:

1. **Proof-of-Work**: Miners solve a cryptographic puzzle to add blocks.
2. **Longest Chain Rule**: In case of forks, the longest valid chain is chosen.

## Implementation Details

### Tracker

- Maintains a list of active peers
- Handles peer registration
- Broadcasts updated peer lists
- Serves as a reference point for blockchain state

### Client Node

- Connects to the tracker and other peers
- Maintains a local copy of the blockchain
- Creates and validates transactions
- Mines new blocks
- Resolves conflicts with other peers

### Voting Application

- Provides a GUI for user interaction
- Displays blockchain state and voting results
- Allows users to cast votes
- Shows network status

## Security Features

- Each vote is signed with the voter's private key
- Votes are verified before being added to the blockchain
- Double voting is prevented through transaction validation
- Blockchain integrity is ensured through hash linking
- Proof-of-work prevents tampering with the blockchain

## Limitations

This is a simplified implementation for educational purposes:

- The cryptographic implementation is simplified
- The P2P network is simulated locally
- Mining difficulty is set low for demonstration purposes
- No advanced consensus mechanisms are implemented

## Future Improvements

Potential enhancements:

- Implement proper cryptographic signing
- Add dynamic difficulty adjustment
- Implement sharding for scalability
- Add more advanced voting mechanisms
- Improve network resilience
- Implement smart contracts for voting rules

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.