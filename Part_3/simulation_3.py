'''
Created on Oct 12, 2016

@author: mwittie
'''
import network_3
import link
import threading
from time import sleep

# configuration parameters
router_queue_size = 0  # 0 means unlimited
# give the network_3 sufficient time to transfer all packets before quitting
simulation_time = 10

if __name__ == '__main__':
    object_L = []  # keeps track of objects, so we can kill their threads

    # create network_3 nodes
    client_1 = network_3.Host(1)
    object_L.append(client_1)
    client_2 = network_3.Host(2)
    object_L.append(client_2)

    server_1 = network_3.Host(3)
    object_L.append(server_1)
    server_2 = network_3.Host(4)
    object_L.append(server_2)

    table_a = [(2, 3), (3, 4)] #first tuple entry is output port, second address to forward to

    router_a = network_3.Router(name='A', intf_count=4,
                              max_queue_size=router_queue_size, forward_t = table_a)
    object_L.append(router_a)
    
    table_b = [(1,3)]

    router_b = network_3.Router(name='B', intf_count=2,
                              max_queue_size=router_queue_size,  forward_t = table_b)
    object_L.append(router_b)
    
    table_c = [( 1, 4)]

    router_c = network_3.Router(name='C', intf_count=2,
                              max_queue_size=router_queue_size, forward_t =  table_c)
    object_L.append(router_c)
    
    table_d = [(2, 3), (3, 4)]

    router_d = network_3.Router(name='D', intf_count=4,
                              max_queue_size=router_queue_size,   forward_t = table_d)
    object_L.append(router_d)
    # create a Link Layer to keep track of links between network_3 nodes
    link_layer = link.LinkLayer()
    object_L.append(link_layer)

    # add all the links
    # link parameters: from_node, from_intf_num, to_node, to_intf_num, mtu
    # connect client 1 to router a
    link_layer.add_link(link.Link(client_1, 0, router_a, 0, 50))
    # connect client 2 to router a
    link_layer.add_link(link.Link(client_2, 0, router_a, 1, 50))

    #Upper port values are OUTPUT ports else input
    link_layer.add_link(
        link.Link(router_a, 2, router_b, 0, 50))  # connect a to b
    link_layer.add_link(
        link.Link(router_b, 1, router_d, 0, 50))  # connect b to d
    link_layer.add_link(
        link.Link(router_a, 3, router_c, 0, 50))  # connect a to c
    link_layer.add_link(
        link.Link(router_c, 1, router_d, 1, 50))  # connect c to d

    # connect server 1 to router d
    link_layer.add_link(link.Link( router_d, 2, server_1, 0, 50))
    # connect server 2 to router d
    link_layer.add_link(link.Link( router_d, 3, server_2, 0, 50))

    # start all the objects
    thread_L = []
    thread_L.append(threading.Thread(
        name=client_1.__str__(), target=client_1.run))
    thread_L.append(threading.Thread(
        name=client_2.__str__(), target=client_2.run))

    thread_L.append(threading.Thread(
        name=server_1.__str__(), target=server_1.run))
    thread_L.append(threading.Thread(
        name=server_2.__str__(), target=server_2.run))

    thread_L.append(threading.Thread(
        name=router_a.__str__(), target=router_a.run))
    thread_L.append(threading.Thread(
        name=router_b.__str__(), target=router_b.run))
    thread_L.append(threading.Thread(
        name=router_c.__str__(), target=router_c.run))
    thread_L.append(threading.Thread(
        name=router_d.__str__(), target=router_d.run))

    thread_L.append(threading.Thread(name="network_3", target=link_layer.run))

    for t in thread_L:
        t.start()

    # create some send events
    for i in range(3):
        client_2.udt_send(4, 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.')

    # give the network_3 sufficient time to transfer all packets before quitting
    sleep(simulation_time)

    # join all threads
    for o in object_L:
        o.stop = True
    for t in thread_L:
        t.join()

    print("All simulation threads joined")


# writes to host periodically
