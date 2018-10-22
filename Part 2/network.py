'''
Created on Oct 12, 2016

@author: mwittie
'''
import queue
import threading


## wrapper class for a queue of packets
class Interface:
    ## @param maxsize - the maximum size of the queue storing packets
    def __init__(self, maxsize=0):
        self.queue = queue.Queue(maxsize)
        self.mtu = None
    
    ##get packet from the queue interface
    def get(self):
        try:
            return self.queue.get(False)
        except queue.Empty:
            return None
        
    ##put the packet into the interface queue
    # @param pkt - Packet to be inserted into the queue
    # @param block - if True, block until room in queue, if False may throw queue.Full exception
    def put(self, pkt, block=False):
        self.queue.put(pkt, block)
        
        
## Implements a network layer packet (different from the RDT packet 
# from programming assignment 2).
# NOTE: This class will need to be extended to for the packet to include
# the fields necessary for the completion of this assignment.
class NetworkPacket:
    ## packet encoding lengths 
    dst_addr_S_length = 5
    flags_S_length = 1
    frag_offset_S_length = 4
    total_header_S_length = dst_addr_S_length + flags_S_length + frag_offset_S_length
    
    ##@param dst_addr: address of the destination host
    # @param data_S: packet payload
    def __init__(self, dst_addr, data_S, frag_flag = 0, frag_offset = 0):
        self.dst_addr = dst_addr
        self.data_S = data_S
        self.frag_flag = frag_flag
        self.frag_offset = frag_offset
        
    ## called when printing the object
    def __str__(self):
        return self.to_byte_S()
        
    ## convert packet to a byte string for transmission over links
    def to_byte_S(self):
        byte_S = str(self.frag_flag)
        byte_S += str(self.frag_offset).zfill(self.frag_offset_S_length)
        byte_S += str(self.dst_addr).zfill(self.dst_addr_S_length)
        byte_S += self.data_S
        return byte_S
    
    ## extract a packet object from a byte string
    # @param byte_S: byte string representation of the packet
    @classmethod
    def from_byte_S(self, byte_S):
        p = NetworkPacket(None,None)
        p.frag_flag = int(byte_S[0])
        p.frag_offset = int(byte_S[self.flags_S_length : self.flags_S_length+self.frag_offset_S_length])
        p.dst_addr = int(byte_S[self.flags_S_length+self.frag_offset_S_length : self.flags_S_length+self.frag_offset_S_length+self.dst_addr_S_length])
        p.data_S = byte_S[self.total_header_S_length : ]
        return p
    

    

## Implements a network host for receiving and transmitting data
class Host:
    
    ##@param addr: address of this node represented as an integer
    def __init__(self, addr):
        self.addr = addr
        self.in_intf_L = [Interface()]
        self.out_intf_L = [Interface()]
        self.stop = False #for thread termination
    
    ## called when printing the object
    def __str__(self):
        return 'Host_%s' % (self.addr)
       
    ## create a packet and enqueue for transmission
    # @param dst_addr: destination address for the packet
    # @param data_S: data being transmitted to the network layer
    def udt_send(self, dst_addr, data_S):
        p_L = []
        maxDataLen = self.out_intf_L[0].mtu - NetworkPacket.total_header_S_length
        while len(data_S):
            p_L += [NetworkPacket(dst_addr, data_S[:maxDataLen])]
            data_S = data_S[maxDataLen:]
        for p in p_L:
            self.out_intf_L[0].put(p.to_byte_S()) #send packets always enqueued successfully
            print('%s: sending packet "%s" on the out interface with mtu=%d' % (self, p, self.out_intf_L[0].mtu))
        
    ## receive packet from the network layer
    def udt_receive(self):
        pkt_S = self.in_intf_L[0].get()
        if pkt_S is not None:
            #print('%s: received first frag "%s" on the in interface' % (self, pkt_S))
            pkt = NetworkPacket.from_byte_S(pkt_S)
            frags = []
            while pkt.frag_flag:
                frag_S = self.in_intf_L[0].get()
                if frag_S is not None:
                    #print('%s: received frag "%s" on the in interface' % (self, frag_S))
                    frags += [NetworkPacket.from_byte_S(frag_S)]
                elif not len(frags):
                    continue 
                frags = frags[-1:]+frags[:-1]
                if frags[0].frag_offset is len(pkt.data_S):
                    pkt.data_S += frags[0].data_S
                    pkt.frag_flag = frags[0].frag_flag
                    del frags[0]
            print('%s: received packet "%s" on the in interface' % (self, pkt.data_S))
       
    ## thread target for the host to keep receiving data
    def run(self):
        print (threading.currentThread().getName() + ': Starting')
        while True:
            #receive data arriving to the in interface
            self.udt_receive()
            #terminate
            if(self.stop):
                print (threading.currentThread().getName() + ': Ending')
                return
        


## Implements a multi-interface router described in class
class Router:
    
    ##@param name: friendly router name for debugging
    # @param intf_count: the number of input and output interfaces 
    # @param max_queue_size: max queue length (passed to Interface)
    def __init__(self, name, intf_count, max_queue_size):
        self.stop = False #for thread termination
        self.name = name
        #create a list of interfaces
        self.in_intf_L = [Interface(max_queue_size) for _ in range(intf_count)]
        self.out_intf_L = [Interface(max_queue_size) for _ in range(intf_count)]

    ## called when printing the object
    def __str__(self):
        return 'Router_%s' % (self.name)

    ## look through the content of incoming interfaces and forward to
    # appropriate outgoing interfaces
    def forward(self):
        for i in range(len(self.in_intf_L)):
            pkt_S = None
            try:
                #get packet from interface i
                pkt_S = self.in_intf_L[i].get()
                #if packet exists make a forwarding decision
                if pkt_S is not None:
                    p = NetworkPacket.from_byte_S(pkt_S) #parse a packet out
                    # HERE you will need to implement a lookup into the 
                    # forwarding table to find the appropriate outgoing interface
                    # for now we assume the outgoing interface is also i
                    p_L = []
                    maxDataLen = self.out_intf_L[0].mtu - NetworkPacket.total_header_S_length
                    offset = 0
                    while len(p.data_S) > maxDataLen:  
                        frag = NetworkPacket(p.dst_addr,p.data_S[:maxDataLen],1,offset)  
                        offset += len(frag.data_S)                   
                        p.data_S = p.data_S[maxDataLen:]
                        p_L += [frag]
                    p.frag_offset = offset
                    p_L += [p]
                    for p in p_L:
                        self.out_intf_L[i].put(p.to_byte_S(), True)
                        print('%s: forwarding packet "%s" from interface %d to %d with mtu %d' \
                            % (self, p, i, i, self.out_intf_L[i].mtu))
            except queue.Full:
                print('%s: packet "%s" lost on interface %d' % (self, p, i))
                pass
                
    ## thread target for the host to keep forwarding data
    def run(self):
        print (threading.currentThread().getName() + ': Starting')
        while True:
            self.forward()
            if self.stop:
                print (threading.currentThread().getName() + ': Ending')
                return 