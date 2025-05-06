# How to Test the Code in One Line


## Command
type "python start_network.py --peers 3 --auto-mine" to run the network with 3 nodes in local machine. 

![alt text](images/image-7.png)

The GUI will open immediately on Windows/MacOS, as shown below

![alt text](images/image.png)

For Linux servers, access the address of the app (e.g. 127.0.0.1:5000, 127.0.0.1:5001) if connected and forwarded with SHH session.


## Functions
This app basically allow users to select a candidate, vote for him, and cast the voting results to peers with a mining in block chain.

### Select Candidate

![alt text](images/image-1.png)

### Cast Voting
After clicking at "Cast Vote", the current app will mine a block on the tail of block chain and spread the new chain through peers

![alt text](images/image-2.png)

### See Results
Right after clicking at "Cast Vote", every app's terminal will give necessary info

E.g. from another app terminal,

![alt text](images/image-3.png)

Also, the "block chain" tab will show the details of the unchangeable hashed blocks,

![alt text](images/image-4.png)

The "results" tab shows a straight forward, real-time-update histogram result.

![alt text](images/image-5.png)

The "network" tab shows current peers in the network,

![alt text](images/image-6.png)

# How to test with self-difined parameters

## Command

First, run the tracker to manipulate peers,

![alt text](images/image-8.png)

Next, run several clients in seperate terminals as you like,

![alt text](images/image-9.png)

Now you can see the same app window as the last section. All behaviors are the same.

![alt text](images/image-10.png)