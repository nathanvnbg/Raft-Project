
import httplib
import xmlrpclib

def getLeader(nodes):
    leader = None
    for n in nodes:
        try:
            if n.isLeader():
                leader = n
                break
        except httplib.HTTPException:
            print 'HTTPException'
        except Exception:
            print 'Exception'
    return leader

def addEntry(nodes, tid, data):
    committed = False
    while committed == False:
        try:
            leader = getLeader(nodes)
            if leader is not None:
                committed = leader.addEntry(tid, data)
        except httplib.HTTPException:
            print 'HTTPException'
        except Exception:
            print 'Exception'


def main():
    tid = 0    # unique transaction id
    nodes = []
    nodeIds = ["10.2.0.242", "10.3.0.237", "10.6.1.9", "10.7.0.251", "10.10.0.51"]

    for nodeId in nodeIds:
        node = xmlrpclib.Server("http://"+nodeId+":8000", allow_none=True)
        nodes.append(node)

    addEntry(nodes, tid, "test")
    #tid += 1
    #addEntry(nodes, tid, "abcd")

    print 'Client Done'


if __name__ == "__main__":
    main()
