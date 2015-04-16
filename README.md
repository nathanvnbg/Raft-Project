# Raft-Project

Implementation of Raft consensus algorithm for UVic CSC 562 - Distributed Computing in Python 2.7 (using XML-RPC) on the Geni Experiment Engine. Consensus algorithms are used to add fault-tolerance to distributed systems, where multiple nodes must perform some agreement before committing state changes. Raft is designed to be equivalent to Paxos in fault-tolerance and performance but much easier to understand and implement.



## Install

This project runs on the Geni Experiment Engine and uses a fabfile for installation.

1. fabfile.py should be edited to add the addresses of the GEE nodes to be used. node.py and client.py should be edited to add the ip addresses of the machines in the nodeIds variable in main().

2. node.py should be uploaded to the GEE nodes. This can be done by using the 'fab upload_node' command.

3. Each GEE node should be edited to add a file called 'address' with a single line containing the ip address of that machine. This should match one of the ip addresses in the nodeIds variable. The 'fab saveip' command should do this automatically.

4. Nodes can now be started by logging into each GEE node and running node.py. There are 5 nodes available by default.

5. A simple client can be run using 'fab upload_client' and 'fab run_client' commands.

6. The 'raftlog' can be downloaded using the 'fab get_raftlog' command.



## Description

Raft is a consensus algorithm used to maintain a consistent state across multiple nodes. Raft decomposes this problem into two easier sub-problems: that of leader election and log replication.

Leader Election: Where a node becomes a candidate and starts an election. If it gains a majority of votes, it becomes the new leader.

Log Replication: When the client sends a request to modify the state machine, the leader’s log is updated and log entries must be sent to its followers. After a majority of nodes contain the same log entries, the request is committed and the state machine can be updated.



## Design

### Raft Nodes

Raft nodes are implemented in node.py. Nodes can be in one of three states:

Follower:
Nodes in the follower state wait and respond to RPCs. If the election timeout elapses then it converts to a candidate.

Candidate:
Starts an election by voting for self then sending requestVotesRPCs to other raft nodes. Converts to leader if a majority of votes is received, else converts to follower.

Leader:
Waits for requests from clients to append entries to the log. It periodically sends heartbeats to it's followers and makes sure that the followers log file has the same format as the leader.



### Raft Node Interface

requestVotesRPC(term, candidateId, lastLogIndex, lastLogTerm)

- Called by candidates during the leader election phase. Returns true if callee has not voted yet and if the candidate has an up to date log.


appendEntriesRPC(term, leaderId, prevLogIndex, prevLogTerm, entries)

- Called by leaders to append log entries and send heartbeats. Returns true if callee log was updated successfully.



### Client Interface

isLeader()

- Returns true if the current node is the leader.

addEntry(tid, data)

- Adds an entry to the log file with the specified tid (transaction id) and data. Log entries are sent using heartbeats to other raft nodes and waits for a majority for it to be committed. Currently, tid does not do anything but could be used to prevent prevent adding duplicate entries to the log file.


### Client

I created a very simple client in client.py to add a single entry to the log. The client queries every raft node to find the leader then calls addEntry() to add a new log entry to the leader's log.



## Testing

I've only done some simple test cases. I have not tested what happens when networks are partitioned.


1. Testing Leader Elections
Raft was tested running on 5 GEE nodes and making sure the leader is elected properly. I manually shut down the leader and checked that another leader was correctly chosen. Then I tested restarting the node and made sure it was added back as a follower.


2. Testing Log Replication
Testing was done by running the client.py file and checking that the 'raftlog' files of the followers contains the new entry.



## Known Issues

Nodes sometimes are not able to choose a new leader and get stuck in Candidate/Follower states. This seems to occur more often when only 3 nodes are available and may be related to timeouts.

The client can sometimes get stuck unable to connect to the leader, possibly there are too many connections. This can be fixed by restarting the leader. The client should be able to connect to the next elected leader.

Sometimes it seems that two leaders can be elected at the same time.



## Future Work

This implementation of Raft only uses a log file and does not modify a state machine. Currently, my implementation just replicates log entries but in the future maybe a state machine (or SQL database) could be added.

RPCs are done in sequence and could be improved by getting them to run in parallel.




