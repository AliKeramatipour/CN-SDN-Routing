from ryu.base import app_manager
from ryu.controller import mac_to_port
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.mac import haddr_to_bin
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib import mac
from ryu.topology.api import get_switch, get_link
from ryu.app.wsgi import ControllerBase
from ryu.topology import event, switches
from collections import defaultdict

#   list of all switches
switches = []

#   mymac[srcmac]->(switch, port)
#   MAC address table
mymac={}

#   adjacency map [sw1][sw2]->port from sw1 to sw2
adjacency=defaultdict(lambda:defaultdict(lambda:None))

#   returns switch with the least distance in Q
def minimum_distance(distance, Q):
    min = float('Inf')
    node = 0
    for v in Q:
        if distance[v] < min:
            min = distance[v]
            node = v
    return node

 
#   finds the shortest path  between src and dst using Dijkstra
def get_path (src,dst,first_port,final_port):
    #   Dijkstra's algorithm

    print("get_path is called, src=",src," dst=",dst, " first_port=", first_port, " final_port=", final_port)

    #   Initialization
    distance = {}
    previous = {}
    for dpid in switches:
        distance[dpid] = float('Inf')
        previous[dpid] = None
    distance[src]=0
    Q=set(switches)
    #   find each switch's minimum cost to get to dst
    while len(Q)>0:
        u = minimum_distance(distance, Q)
        Q.remove(u)
        for p in switches:
            if adjacency[u][p]!=None:
                w = 1
                if distance[u] + w < distance[p]:
                    distance[p] = distance[u] + w
                    previous[p] = u
    r=[]
    p=dst
    r.append(p)
    q=previous[p]
    #   go back from dst to src to save path
    while q is not None:
        if q == src:
            r.append(q)
            break
        p=q
        r.append(p)
        q=previous[p]
    r.reverse()
    if src==dst:
        path=[src]
    else:
        path=r

    # Now add the ports
    r = []
    in_port = first_port
    for s1,s2 in zip(path[:-1],path[1:]):
        out_port = adjacency[s1][s2]
        r.append((s1,in_port,out_port))
        in_port = adjacency[s2][s1]
    r.append((dst,in_port,final_port))
    print("Path:    ", path)
    return r
    
class ProjectController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        print("init is called")
        super(ProjectController, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.topology_api_app = self
        self.datapath_list=[]

    # Handy function that lists all attributes in the given object
    def ls(self,obj):
        print("\n".join([x for x in dir(obj) if x[0] != "_"]))

    def add_flow(self, datapath, in_port, dst, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser      
        match = datapath.ofproto_parser.OFPMatch(in_port=in_port, eth_dst=dst)
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,actions)] 
        mod = datapath.ofproto_parser.OFPFlowMod(datapath=datapath, match=match, cookie=0,command=ofproto.OFPFC_ADD, idle_timeout=0, hard_timeout=0,priority=ofproto.OFP_DEFAULT_PRIORITY, instructions=inst)
        datapath.send_msg(mod)

    # install a flow in the found path to avoid packet_in next time
    def install_path(self, p, ev, src_mac, dst_mac):
        print ("install_path is called")
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        for sw, in_port, out_port in p:#   go through all switches in the path
            print("install_path switch:     ", sw)
            match=parser.OFPMatch(in_port=in_port, eth_src=src_mac, eth_dst=dst_mac)    #match this flow to the specified packets
            actions=[parser.OFPActionOutput(out_port)]  #   do output action
            datapath=self.datapath_list[int(sw)-1]      #   get sw's datapath from datapath_list
            inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS , actions)]
            mod = datapath.ofproto_parser.OFPFlowMod(datapath=datapath, match=match, idle_timeout=0, hard_timeout=0,priority=1, instructions=inst)
            datapath.send_msg(mod)  #send msg from sw

    #   waiting to recieve a new switch's features
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures , CONFIG_DISPATCHER)
    def switch_features_handler(self , ev):
        print("switch_features_handler is called")
        print("Event's msg:     ", ev.msg)
        datapath = ev.msg.datapath  #switch's datapath instance
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        match = parser.OFPMatch()   #match this flow to all packets
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]   #   do output action
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS ,actions)]
        mod = datapath.ofproto_parser.OFPFlowMod(datapath=datapath, match=match, cookie=0,command=ofproto.OFPFC_ADD, idle_timeout=0, hard_timeout=0,priority=0, instructions=inst)
        datapath.send_msg(mod)  #send msg from sw
        print("msg is sent")

    #   when a new packet is recieved
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):

        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']
        pkt = packet.Packet(msg.data)   #   make an instance of packet with recieved data
        eth = pkt.get_protocol(ethernet.ethernet)   #   get protocol
        
        #   avodi broadcast from LLDP
        if eth.ethertype==35020:
            return

        dst = eth.dst       #   packet's destination
        src = eth.src       #   packet's source
        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

        if src not in mymac.keys():         #   add source to my mac (if does'nt already exist)
            print("adding source to mymac")
            mymac[src]=( dpid,  in_port)

        if dst in mymac.keys():#    if dst exists in mymac then find a new path from dst to src and install it to avoid packet-in next time
            print("dst exists in mymac")
            print("SRC  DST",src, dst)
            p = get_path(mymac[src][0], mymac[dst][0], mymac[src][1], mymac[dst][1])
            self.install_path(p, ev, src, dst)
            out_port = p[0][2]  #   out_port is the next switch's port_in in the path
            print("packet_in_handler 'out_port': ", out_port)
        else:                   #   if dst does not exist in mymac then out_port is all physical ports
            out_port = ofproto.OFPP_FLOOD   #   all ports
        actions = [parser.OFPActionOutput(out_port)]    #output action

        if out_port != ofproto.OFPP_FLOOD:  
            match = parser.OFPMatch(in_port=in_port, eth_src=src, eth_dst=dst)
        
        data=None       #   get message data
        if msg.buffer_id==ofproto.OFP_NO_BUFFER:
            data=msg.data
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id, in_port=in_port,actions=actions, data=data)
        datapath.send_msg(out)      #send message

    @set_ev_cls(event.EventSwitchEnter)
    def get_topology_data(self, ev):
        print("get_topology_data is called")
        global switches
        switch_list = get_switch(self.topology_api_app, None)       #   get topology's switches
        switches=[switch.dp.id for switch in switch_list]           #   get switch's datapath
        self.datapath_list=[switch.dp for switch in switch_list]    #get switch's datapath
        self.datapath_list = sorted(self.datapath_list, key=lambda x:x.id, reverse=False)   # sort datapath_list based on dpid
        print("switches=    ", switches)
        links_list = get_link(self.topology_api_app, None)                                  #   get topology's links
        mylinks=[(link.src.dpid,link.dst.dpid,link.src.port_no,link.dst.port_no) for link in links_list]
        print("links=       ", mylinks)
        for s1,s2,port1,port2 in mylinks:       #   make adjacency's matrix
            adjacency[s1][s2]=port1
            adjacency[s2][s1]=port2
        print("adjacancy matrix is made")