
import httplib
import math
import os.path
import pickle
import random
import socket
import sys
import SimpleXMLRPCServer
import threading
import time
import xmlrpclib

class RaftNode(object):
    
    def __init__(self):

        self.id = ""
        self.nodes = []

        # persistent - update before responding to RPC
        self.currentTerm = 0
        self.votedFor = None
        self.numLog = 0
        self.log = []

        # volatile (all)
        self.commitIndex = 0
        self.lastApplied = 0

        # volatile (leader)
        self.nextIndex = []
        self.matchIndex = []


        self.state = 'Follower'

        self.electionTimeout = self.getElectionTimeout()
        self.startTime = time.clock()
        self.votes = 0

        self.socketTimeout = None#0.05

        self.clientRunning = False
        self.leaderLock = threading.Lock()


        # Used for debugging
        self.nextState = 'None'
        self.nextTerm = -1


        # initial log entry
        entry = {}
        entry["term"] = 1
        entry["tid"] = -1
        entry["data"] = "start"

        self.numLog = 1
        self.log.append(entry)


        # load persistent data
        #if os.path.isfile('persistent'):
        #    self.readPersistent()
        #if os.path.isfile('raftlog'):
        #    self.readLog()


        self.running = True


    def terminate(self):
        self.running = False
        return 1


    def readIp(self):
        with open('address', 'r') as f:
           self.id = f.read().strip()


    def writeLog(self):
        with open('raftlog', 'w') as f:
           pickle.dump(self.log, f)

    def readLog(self):
        with open('raftlog', 'r') as f:
           self.log = pickle.load(f)
           self.numLog = len(self.log)


    def writePersistent(self):
        with open('persistent', 'w') as f:
           pickle.dump([self.currentTerm, self.votedFor], f)

    def readPersistent(self):
        with open('persistent', 'r') as f:
           line = pickle.load(f)
           self.currentTerm = line[0]
           self.votedFor = line[1]
           
    def setCurrentTerm(self, t):
        self.currentTerm = t
        self.writePersistent()

    def setVotedFor(self, v):
        self.votedFor = v
        self.writePersistent()


    def getElectionTimeout(self):
        return random.randint(500,5000)/1000.0

    def getHeartbeatTimeout(self):
        return 5.0


    def getLogIndex(self):
        return self.numLog-1

    def getLogTerm(self):
        if self.numLog == 0:
            return 0
        entry = self.log[self.numLog-1]
        return entry["term"]


    def initFollower(self, term):
        #print 'Convert to Follower'
        self.state = 'Follower'
        self.setCurrentTerm(term)
        self.setVotedFor(None)

    def initCandidate(self):
        #print 'Convert to Candidate'
        self.state = 'Candidate'
        self.setCurrentTerm(self.currentTerm+1)
        self.electionTimeout = self.getElectionTimeout()
        #print self.electionTimeout
        self.startTime = time.clock()

    def initLeader(self):
        #print 'Convert to Leader'
        self.state = 'Leader'
        self.nextIndex = []
        self.matchIndex = []

        for n in self.nodes:
            self.nextIndex.append(self.getLogIndex()+1)
            self.matchIndex.append(0)

        # Send empty appendEntriesRPC() entries to followers
        self.updateLeader()


    # Check if election timeout elapses. If so, convert to candidate.
    def updateFollower(self):
        if (self.startTime + self.electionTimeout) < time.clock():
            self.initCandidate()

    # Send vote requests to all other nodes
    def updateCandidate(self):
        self.votes = 1
        self.setVotedFor(self.id)
        for n in self.nodes:
            lastLogIndex = self.getLogIndex()
            lastLogTerm = self.getLogTerm()

            try:
                socket.setdefaulttimeout(self.socketTimeout)
                t,v = n.requestVoteRPC(self.currentTerm, self.id, lastLogIndex, lastLogTerm)
                socket.setdefaulttimeout(None)

                if t > self.currentTerm:
                    self.initFollower(t)
                    break
                if v == True:
                    self.votes += 1
                
            except httplib.HTTPException, e:
                print e
            except Exception, e:
                print e

        if self.votes > math.ceil((len(self.nodes)+1)/2.0):
            self.initLeader()
        else:
            self.initFollower(self.currentTerm)
            self.electionTimeout = self.getElectionTimeout()
            self.startTime = time.clock()


    # Make sure log entries on other servers are up to date
    def updateLeader(self):

        self.leaderLock.acquire()

        commitCount = 1
        for i in range(0, len(self.nodes)):

            n = self.nodes[i]
            prevLogIndex = self.nextIndex[i]-1
            #print self.nextIndex[i]
            #print self.log
            prevLogTerm = self.log[prevLogIndex]["term"]
            entries = self.log[self.nextIndex[i]:]

            try:
                socket.setdefaulttimeout(self.socketTimeout)
                t,v = n.appendEntriesRPC(self.currentTerm, self.id,
                                     prevLogIndex, prevLogTerm,
                                     entries, self.commitIndex)
                socket.setdefaulttimeout(None)

                if t > self.currentTerm:
                    self.initFollower(t)
                    break
                if v == True:
                    self.nextIndex[i] = self.getLogIndex()+1
                    commitCount += 1
                elif v == False:
                    self.nextIndex[i] -= 1

            except httplib.HTTPException, e:
                print e
            except Exception, e:
                print e

        self.leaderLock.release()

        return commitCount
        


    def run(self):
        #print self.log
        if (self.nextState != self.state) or (self.nextTerm != self.currentTerm):
            print 'Run ' + self.state + ' ' + str(self.currentTerm)
            self.nextState = self.state
            self.nextTerm = self.currentTerm
            
        if self.commitIndex > self.lastApplied:
            self.lastApplied += 1
            #apply self.log[self.lastApplied] to state machine


        if self.state == 'Follower':
            self.updateFollower()

        elif self.state == 'Candidate':
            self.updateCandidate()

        elif self.state == 'Leader':
            if self.clientRunning == False:
                self.updateLeader()



    # Invoked by candidates to gather votes
    def requestVoteRPC(self, term, candidateId, lastLogIndex, lastLogTerm):
        print 'Vote Request ' + candidateId + ' ' + str(self.currentTerm) + ' ' + str(term)
        if term < self.currentTerm:
            return (self.currentTerm, False)
        elif term > self.currentTerm:
            self.initFollower(term)

        if (self.votedFor is None) or (self.votedFor == candidateId):
            # Return False is voter has more complete log
            if (self.getLogTerm() > lastLogTerm) or (self.getLogTerm() == lastLogTerm) and (self.getLogIndex() > lastLogIndex):
                return (self.currentTerm, False)
            else:
                self.setVotedFor(candidateId)
                return (self.currentTerm, True)
        
        return (self.currentTerm, False)


    # Invoked by leader to replicate log entries
    # Also used as a heartbeat
    def appendEntriesRPC(self, term, leaderId, prevLogIndex, prevLogTerm, entries, leaderCommit):
        print 'Heartbeat ' + leaderId + ' ' + str(self.currentTerm) + ' ' + str(term) + ' ' + str(entries)
        if term < self.currentTerm:
            return (self.currentTerm, False)
        elif term > self.currentTerm:
            self.initFollower(term)

        # Reset timeout
        self.electionTimeout = self.getHeartbeatTimeout()
        self.startTime = time.clock()

        if prevLogIndex < len(self.log):
            entry = self.log[prevLogIndex]
            logTerm = entry["term"]
            #print 'logTerm ' + str(logTerm)

            if logTerm == prevLogTerm:
                #print self.log
                self.log = self.log[:(prevLogIndex+1)] + entries
                #print self.log
                self.writeLog()

                if self.commitIndex < leaderCommit:
                    self.commitIndex = leaderCommit

                #print 'append True'
                return (self.currentTerm, True)

        return (self.currentTerm, False)




    # Invoked by clients
    # Returns true if this node is the leader
    def isLeader(self):
        return self.state == 'Leader'


    # Invoked by clients to add entry to state machine
    def addEntry(self, tid, data):

        print 'addEntry ' + str(tid) + ' ' + data

        self.clientRunning = True

        entry = {}
        entry["term"] = self.currentTerm
        entry["tid"] = tid
        entry["data"] = data

        # Note: transaction id should not already be in log
        #       to avoid duplicate transactions

        self.numLog += 1
        self.log.append(entry)
        self.writeLog()

        committed = False

        count = 0

        while committed == False and self.state == 'Leader':
            #print committed
            commitCount = self.updateLeader()

            # Commit entries
            if commitCount > math.ceil((len(self.nodes)+1)/2.0):
                committed = True
                self.commitIndex += 1

            count += 1
            if count == 20:
                break

        self.clientRunning = False

        return committed

    


def main(argv):
    #print argv

    node = RaftNode()

    node.readIp()
    print "Id:"
    print node.id

    nodeIds = ["10.2.0.242", "10.3.0.237", "10.6.1.9", "10.7.0.251", "10.10.0.51"]
    nodeIds.remove(node.id)
    print nodeIds

    #print node.id
    #print nodeIds

    server = SimpleXMLRPCServer.SimpleXMLRPCServer(("", 8000), allow_none=True)
    server.register_instance(node)


    for nodeId in nodeIds:
        n = xmlrpclib.Server("http://"+nodeId+":8000", allow_none=True)
        node.nodes.append(n)
    
    print("Raft node ready.")
    #server.serve_forever()

    t = threading.Thread(target=server.serve_forever)
    t.start()

    while node.running:
        node.run()


if __name__ == "__main__":
   main(sys.argv[1:])

