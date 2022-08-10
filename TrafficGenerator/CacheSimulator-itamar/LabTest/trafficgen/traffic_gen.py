#!/usr/bin/ python 

import numpy as np
import argparse
import sys
import socket
import random
import struct
import re

from time import time,sleep
from functools import lru_cache
from scapy.all import sendp, send, srp1, raw
from scapy.all import Packet, hexdump
from scapy.all import Ether, IP, Raw, UDP
from scapy.all import bind_layers, conf


def load_size_pdf(packet_size=1000):
    my_data = np.genfromtxt('/labhome/oshabtai/oshabtai/work/trafficgen/CacheSimulator/data/traffic/FBHadoop/msgSizeDist_AllLoc_Facebook_Hadoop.csv', delimiter=',')
    size = (my_data[1:,0] // 1000) + 1
    pdf = my_data[1:,1]-my_data[:-1,1]
    return size, pdf


def get_flow_size(rng,pdf,size):
    return rng.choice(size, 1, p=pdf)
    

#@lru_cache()
def main(args):
    
    ip_dest_high = np.ceil(np.sqrt(np.sqrt(float(args.dest_num))))
    real_dest_num = ip_dest_high**(4)
    print(f"randomizing traffic to {real_dest_num} destinations")


    flow_sizes, flow_size_pdf = load_size_pdf()
    rng = np.random.default_rng()
    
    s = ''
    iface = 'ens7'
    data = 'a'*1000
    s = conf.L2socket(iface=iface)
    t_start = time()
    runtime = 10
    t_start = time()
    t_end = t_start + runtime
    # print ("sending")
    total_packets = 0
    flow_count = 0 
    while (time()<t_end):
    # for j in range(2):
        flow_size = int(rng.choice(flow_sizes, 1, p=flow_size_pdf)[0])
    
        ip = '.'.join([str(x) for x in np.random.randint(low=0, high=ip_dest_high, size=4, dtype=int)])
        if args.verbose:
            print(ip, flow_size)
        # pkt = Ether(dst="ff:ff:ff:ff:ff:ff",src="0f:0f:0f:0f:0f:0f")/IP(dst=ip)/UDP(dport=1002)/ Raw(load=data)
        pkt = Ether()/IP(dst=ip)/UDP(dport=1002)/ Raw(load=data)
        # pkt = IP(dst=10)/UDP(dport=1002)/ Raw(load=data)
        byte_frame = bytearray(raw(pkt))
        
        # print(byte_frame)
        # flow_size = 1
        for i in range(flow_size):
            s.send(byte_frame) 
            sleep(args.sleep)

        total_packets += flow_size
        flow_count +=1
    t2 = time()
    pps = total_packets/(t2-t_start)
    print (f"sending {total_packets} packets, from {flow_count} flows finished, pps ={pps}, runtime: {t2-t_start}")
    

    #except Exception as error:
    #        print (f'error --> {error}' )


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--dest_num', dest='dest_num', default=4000,
                    help='unique dest')
    parser.add_argument('--sleep', dest='sleep', default=0,type=float,
                    help='interpacket gap [sec]')

    parser.add_argument('-v', dest='verbose', action='store_const',
                    const=True, default=False,
                    help='show ip, packets per dest')
    # parser.add_argument('-v', dest='verbose', action='store_const',
    #                 const=True, default=False,
    #                 help='show ip, packets per dest')

    args = parser.parse_args()
    main(args)
