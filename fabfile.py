from fabric.api import *

env.hosts = [
    "slice316.pcvm3-1.geni.case.edu",
#    "slice316.pcvm1-1.geni.it.cornell.edu",
    "slice316.pcvm3-1.instageni.metrodatacenter.com",
    "slice316.pcvm2-2.instageni.rnoc.gatech.edu",
#    "slice316.pcvm3-2.instageni.illinois.edu",
#    "slice316.pcvm5-7.lan.sdn.uky.edu",
    "slice316.pcvm3-1.instageni.lsu.edu",
    "slice316.pcvm2-2.instageni.maxgigapop.net",
#    "slice316.pcvm1-1.instageni.iu.edu",
#    "slice316.pcvm3-4.instageni.rnet.missouri.edu",
    "slice316.pcvm3-7.instageni.nps.edu",
#    "slice316.pcvm2-1.instageni.nysernet.org",
#    "slice316.pcvm3-11.genirack.nyu.edu",
#    "slice316.pcvm5-1.instageni.northwestern.edu",
#    "slice316.pcvm5-2.instageni.cs.princeton.edu",
#    "slice316.pcvm3-3.instageni.rutgers.edu",
#    "slice316.pcvm1-6.instageni.sox.net",
#    "slice316.pcvm3-1.instageni.stanford.edu",
#    "slice316.pcvm2-1.instageni.idre.ucla.edu",
#    "slice316.pcvm4-1.utahddc.geniracks.net",
#    "slice316.pcvm1-1.instageni.wisc.edu",
  ]

Node = ["slice316.pcvm3-1.instageni.metrodatacenter.com",
        "slice316.pcvm2-2.instageni.rnoc.gatech.edu",
        "slice316.pcvm3-1.instageni.lsu.edu",
        "slice316.pcvm2-2.instageni.maxgigapop.net",
        "slice316.pcvm3-7.instageni.nps.edu",]
Client = ["slice316.pcvm3-1.geni.case.edu"]

env.key_filename="./id_rsa"
env.use_ssh_config = True
env.ssh_config_path = './ssh-config'
env.roledefs.update({'node': Node,
                     'client': Client})

def pingtest():
    run('ping -c 3 www.yahoo.com')

def uptime():
    run('uptime')

def getip():
    run("hostname -I | cut -f1 -d' '")

def saveip():
    run("hostname -I | cut -f1 -d' ' > address")

def getls():
    run('ls')


@parallel
@roles('node')
def upload_node():
    put('node.py')

@parallel
@roles('client')
def upload_client():
    put('client.py')



@parallel
@roles('node')
def run_node():
    run('python node.py')

@parallel
@roles('client')
def run_client():
    run('python client.py')


@parallel
@roles('node')
def get_raftlog():
    get('raftlog')


@parallel
@roles('node')
def clean_node():
    run('rm -f raftlog')
    run('rm -f persistent')

