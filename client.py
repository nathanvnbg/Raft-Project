
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
    tid = 0
    nodes = []
    nodeIds = ["8000", "8001", "8002", "8003", "8004"]

    for nodeId in nodeIds:
        node = xmlrpclib.Server("http://localhost:"+nodeId, allow_none=True)
        nodes.append(node)

    addEntry(nodes, tid, "test")

    print 'Client Done'


if __name__ == "__main__":
    main()
