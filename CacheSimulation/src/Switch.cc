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
#include "Definitions.h"
#include "messages_m.h"
#include <math.h>

namespace cachesimulation {

Define_Module(Switch);

void Switch::initialize()
{
    id = getIndex();

}

void Switch::handleMessage(cMessage *message)
{
    int egressPort;


    if(message->getKind() == DATAPACKET){
        DataPacket *msg = check_and_cast<DataPacket *>(message);
                               switch(cache_search(msg->getDestination())){
                                   case FOUND:
                                       delete msg;
                                       break;
                                   case NOTFOUND:
                                       egressPort = miss_table_search(msg->getDestination());
                                       send(msg, "port$o", egressPort);
                                       break;
                                   case THRESHOLDCROSS:
                                       cGate *gate = msg->getArrivalGate();
                                       int arrivalGate;
                                       if(gate)arrivalGate = gate->getIndex();   //Get arrivalport
                                       else return;
                                       ControlPacket *conpacket = new ControlPacket("Insert rule Packet");
                                       conpacket->setKind(INSERTRULE);
                                       conpacket->setRule(msg->getDestination());
                                       send(conpacket, "port$o", arrivalGate);
                                       delete msg;
                                       break;
                               }
    }
    if(message->getKind() == INSERTRULE){
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

int Switch::miss_table_search(uint64_t rule){
    int egressPort;
    EV << "NumOfAggregation = "<< (int)(getParentModule()->par("NumOfAggregation"))<< endl;
    switch((int)par("Type")){
            case TOR:
                //egressPort = (int)ceil((float)rule/(float)(POLICYSIZE/(int)(getParentModule()->par("NumOfAggregation"))));

                if(rule < 5000)egressPort = 1;
                else egressPort = 2;
              break;
            case AGGREGATION:
            case CONTROLLERSWITCH:
                egressPort = 0;
            break;

        }
    return egressPort;
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


}; // namespace