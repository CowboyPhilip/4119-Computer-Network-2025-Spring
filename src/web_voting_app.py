import flask
import os
import sys
import threading
import time
from client import Client

app = flask.Flask(__name__, static_folder='../static', template_folder='../templates')
client = None

@app.route('/')
def home():
    return flask.render_template('index.html')

@app.route('/vote')
def vote():
    return flask.render_template('vote.html')

@app.route('/vote/cast_vote', methods=['POST'])
def cast_vote():
    requestData = flask.request.get_json()
    success = client.create_transaction({'choice': requestData["candidate"]})
    responseData = {}
    if success:
        responseData["transaction_log"] = ("Vote cast for " + 
                                            requestData["candidate"] + "\n")
    else:
         responseData["error"] = ("Failed to cast vote. " + 
                                  "Have you already voted?")
    return flask.jsonify(responseData)

@app.route('/vote/mine_block', methods=['POST'])
def mine_block():
    responseData = {}
    if not client.blockchain.pending_transactions:
        responseData["info"] = "No pending transactions to mine."
    else:
        success = client.manually_mine_block()
        if success:
            responseData["transaction_log"] = ("Mining started...\n")
        else:
            responseData["error"] = "No pending transactions to mine."
    return flask.jsonify(responseData)

@app.route('/vote/auto_mine', methods=['POST'])
def auto_mine():
    requestData = flask.request.get_json()
    client.auto_mine = requestData["auto_mine"]
    return flask.jsonify(success=True)

@app.route('/blockchain')
def blockchain():
    return flask.render_template('blockchain.html')

@app.route('/blockchain/info')
def blockchain_info(): 
    info = client.get_blockchain_info()
    return flask.jsonify(info)

@app.route('/blockchain/display')
def blockchain_display():
    responseData = {}
    # Iterate through blocks
    index = 0
    for block in client.blockchain.chain:
        responseData[index] = {}
        responseData[index]["hash"] = block.hash
        responseData[index]["prev_hash"] = block.previous_hash
        responseData[index]["time"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(block.timestamp))
        responseData[index]["nonce"] = block.nonce
        responseData[index]["merkle_root"] = block.merkle_root
        responseData[index]["transactions"] = len(block.transactions)
        index += 1
    return flask.jsonify(responseData)

@app.route('/blockchain/transactions')
def blockchain_transactions():
    blockNum = int(flask.request.args.get("block"))
    print(blockNum)
    responseData = {}
    # Iterate through blocks
    block = None
    for b in client.blockchain.chain:
        if b.index == blockNum:
            block = b
            break
    # Iterate through transactions
    index = 0
    for tx in block.transactions:
        responseData[index] = {}
        responseData[index]["transaction_id"] = tx.transaction_id
        responseData[index]["voter_id"] = tx.voter_id
        responseData[index]["vote_data"] = tx.vote_data.get('choice', 'N/A').strip()
        responseData[index]["time"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(tx.timestamp))
        index += 1
    return flask.jsonify(responseData)
        
@app.route('/results')
def results():
    return flask.render_template('results.html')

@app.route('/network')
def network():
    return flask.render_template('network.html')

if __name__ == '__main__':
    
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

    # Initialize and start client
    client = Client(host, port, tracker_host, tracker_port, topology_file, mining_difficulty, auto_mine)
    client_thread = threading.Thread(target=client.start)
    client_thread.daemon = True
    client_thread.start()

    app.run(debug=True, port=5004)