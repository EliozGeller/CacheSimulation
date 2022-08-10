#!/usr/bin/env python

class InsertionAlg():
    def __init__(self, aging_factor=0.99,threshold=2):
        self.pending = {} # key: ip, value = (idx,count)
        self.counter = 0
        self.aging_factor = aging_factor
        self.threshold = threshold

    def process_packet(self, ip):
        # returns true if 
        self.counter += 1
        value,last_update = self.pending.get(ip,(0,self.counter))
        value = 1+ value * (self.aging_factor ** (self.counter-last_update))
        if value > self.threshold:
            self.pending.pop(ip,None)
            return True
        else:
            self.pending[ip] = (value,self.counter)
            return False
