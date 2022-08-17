//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU Lesser General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Lesser General Public License for more details.
//
// You should have received a copy of the GNU Lesser General Public License
// along with this program.  If not, see http://www.gnu.org/licenses/.
//

#include "Switch.h"
#include "messages_m.h"
#include <math.h>

namespace cachesimulation {

Define_Module(Switch);



void Switch::initialize()
{
    id = getIndex();
    if((int)par("Type") == TOR){
        miss_table_size = getParentModule()->par("NumOfAggregation");
        miss_table = new partition_rule[miss_table_size];


        //
        uint64_t last = 0;
        uint64_t diff = (uint64_t)(POLICYSIZE/(int)(getParentModule()->par("NumOfAggregation")));
        for(int i = 0;i < miss_table_size;i++){
            miss_table[i].low = last;
            miss_table[i].high = last + diff;
            miss_table[i].port = i + 1;
            last = last + diff + 1;
        }

        //
    }
    else{
        miss_table_size = 1;
        miss_table = new partition_rule[miss_table_size];
        miss_table[0].low = 0;
        miss_table[0].high = POLICYSIZE;
        miss_table[0].port = 0;
    }

}

void Switch::handleMessage(cMessage *message)
{
    int egressPort;
    EV << "Switchhhhhhh!!!!!!!!!!"<<endl;
    int kind_of_packet = message->getKind();
    if(kind_of_packet == DATAPACKET || kind_of_packet == HITPACKET){
        DataPacket *msg = check_and_cast<DataPacket *>(message);
        EV << "Dest in handle = "<<msg->getDestination()<<endl;
        if(msg->getExternal_destination() == 1){
            egressPort = hit_forward(msg->getDestination());
        }
        else {
            switch(cache_search(msg->getDestination())){
                case THRESHOLDCROSS: //in case of THRESHOLDCROSS also case of FOUND will activate
                    if((int)par("Type") != TOR)fc_send(msg);
                    //break; //in purpose
                case FOUND:
                    egressPort = hit_forward(msg->getDestination());
                    msg->setExternal_destination(1);
                    msg->setKind(HITPACKET);
                    break;
                case NOTFOUND:
                    egressPort = miss_table_search(msg->getDestination());
                    msg->setMiss_hop(msg->getMiss_hop() + 1);
                    break;
         }
        }
        EV << "egressPort in Switch = "<<egressPort<<endl;
        send(msg, "port$o", egressPort);

    }
    if(kind_of_packet == INSERTRULE){
        ControlPacket *pck = check_and_cast<ControlPacket *>(message);
                  if(cache.size() >= (int)par("CacheSize")){ //evict rule by LRU
                      evict_rule();
                  }
                  ruleStruct new_rule;
                  new_rule.count = 0;
                  new_rule.last_time = simTime();
                  cache.insert({ pck->getRule(), new_rule });
    }

}
void Switch::fc_send(cMessage *message){
    DataPacket *msg = check_and_cast<DataPacket *>(message);
    cGate *gate = msg->getArrivalGate();
    int arrivalGate;
    if(gate)arrivalGate = gate->getIndex();   //Get arrivalport
    else return;
    ControlPacket *conpacket = new ControlPacket("Insert rule Packet");
    conpacket->setKind(INSERTRULE);
    conpacket->setRule(msg->getDestination());
    send(conpacket, "port$o", arrivalGate);
}
int Switch::cache_search(uint64_t rule){
    auto it = cache.find(rule);

    if (it == cache.end()) {// not found
        return NOTFOUND;
    } else {// found

        it->second.count = it->second.count + 1;
        it->second.last_time = simTime();

        if( it->second.count > (int)par("threshold")){
            return THRESHOLDCROSS;
        }
        else {
            return FOUND;
        }
    }
}

int Switch::hit_forward(uint64_t dest){
    int egressPort;
    switch((int)par("Type")){
            case AGGREGATION:
                egressPort = 1;
              break;
            case TOR:
            case CONTROLLERSWITCH:
                egressPort = hash(dest);
            break;
        }
    return egressPort;
}

int Switch::miss_table_search(uint64_t dest){
    int egressPort;
    for(int i = 0;i < miss_table_size;i++){
        if(dest >= miss_table[i].low && dest <= miss_table[i].high){
            egressPort = miss_table[i].port;
            return egressPort;
        }
    }

}

void Switch::evict_rule(){
    simtime_t min = 1000000;
    uint64_t min_rule;
    for(std::map<uint64_t,ruleStruct >::const_iterator it = cache.begin();
        it != cache.end(); ++it)
    {
        if(it->second.last_time < min){
            min = it->second.count;
            min_rule = it->first;
        }
    }

    cache.erase(min_rule);

}

int Switch::hash(uint64_t dest){
    return (int)ceil((float)dest/(float)(POLICYSIZE/(int)(getParentModule()->par("NumOfAggregation"))));
}

void Switch::finish(){
    delete[] miss_table;
}


}; // namespace
