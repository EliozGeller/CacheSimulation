#!/usr/bin/env python

import argparse
import sys
import socket
import random
import struct
import re

from time import time
from functools import lru_cache
from scapy.all import sendp, send, srp1, raw
from scapy.all import Packet, hexdump
from scapy.all import Ether,IP, StrFixedLenField, XByteField, IntField,BitField, TCP, Raw, UDP
from scapy.all import bind_layers, conf
import readline


#@lru_cache()
def main():
    s = ''
    iface = 'ens7'
    h009_mac = "b8:ce:f6:72:b0:fc"
    h004_mac = "b8:ce:f6:b6:18:1d"
    h009_ip = "1.1.247.7"
    h004_ip = "1.1.247.2"
    data = 'a'*1000

    #while True:
    #    s = str(input('> '))
    #    if s == "quit":
    #        break
    #    print (s)
            #pkt = Ether(src=h009_mac, dst=h004_mac, type=) / IP(dst="1.1.247.3",src="1.1.247.16")
    s = conf.L2socket(iface=iface)
    pkt = IP(dst="1.1.247.3")/UDP(dport=1002)/ Raw(load=data)
    byte_frame = bytearray(raw(pkt))
    #pkt.show()
    print ("sending")
    t1 = time()
    count=int(1e7)
    for i in range(count):
        #s.send(pkt)
        s.send(byte_frame) 
    #send(pkt, iface=iface, count = count,verbose=False)
    t2 = time()
    pps = count/(t2-t1)
    print (f"sending {count} packets finished, pps ={pps}")
    #except Exception as error:
    #        print (f'error --> {error}' )


if __name__ == '__main__':
    main()
