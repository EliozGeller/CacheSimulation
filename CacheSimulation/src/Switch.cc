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
#include <math.h>

namespace cachesimulation {

Define_Module(Switch);



void Switch::initialize()
{
    id = getIndex();
    if((int)par("Type") == TOR){
        miss_table_size = getParentModule()->par("NumOfAggregation");
        miss_table = new partition_rule[miss_table_size];


        // Define the initial partition , Should be deleted when there will be a real partition
        uint64_t last = 0;
        uint64_t diff = (uint64_t)(POLICYSIZE/(int)(getParentModule()->par("NumOfAggregation")));
        for(int i = 0;i < miss_table_size;i++){
            miss_table[i].low = last;
            miss_table[i].high = last + diff;
            miss_table[i].port = i + 1;
            last = last + diff + 1;
        }

        // End Define the initial partition
    }
    else{
        miss_table_size = 1;
        miss_table = new partition_rule[miss_table_size];
        miss_table[0].low = 0;
        miss_table[0].high = POLICYSIZE;
        miss_table[0].port = 0;
    }


    //initialize Elephant process:
    elephant_count = 0;
    cMessage* m1 = new cMessage("Flush elephant timer");
    cMessage* m2 = new cMessage("Check for elephant timer");

    m1->setKind(FLUSH_ELEPHANT_PKT);
    m2->setKind(CHECK_FOR_ELEPHANT_PKT);

    scheduleAt(simTime() + FLUSH_ELEPHANT_TIME,m1);
    scheduleAt(simTime() + CHECK_FOR_ELEPHANT_TIME,m2);

}

void Switch::handleMessage(cMessage *message)
{
    int egressPort;
    int kind_of_packet = message->getKind();
    int s;
    DataPacket *msg;
    InsertionPacket *pck,*m1,*m2;



    //RX:
    //Elephant Detector
    if((int)par("Type") == TOR && kind_of_packet == DATAPACKET){ // Act only if this is a Data packet in the ToR
        msg = check_and_cast<DataPacket *>(message);
        uint64_t dest = msg->getDestination();
        if(elephant_table.size() == ELEPHANT_TABLE_SIZE){
            if(elephant_table.count(dest) > 0){//The flow is in the table
                elephant_table[dest].count++;
                elephant_table[dest].last_time = simTime();
            }
        }
        else {
            if(elephant_count % ELEPHANT_SAMPLE_RX == 0){ //Every few packets we will sample a packet in RX
                elephant_struct new_pkt;
                //new_pkt.byte_count = 0;
                new_pkt.count = 0;
                new_pkt.first_appearance = simTime();
                new_pkt.last_time = simTime();
                elephant_table[dest] = new_pkt;
            }
        }
    }





    //TX:
    switch(kind_of_packet){
        case DATAPACKET:
        case HITPACKET:
        {
            msg = check_and_cast<DataPacket *>(message);
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
            sendDelayed(msg,PROCESSING_TIME_ON_AD_DATA_PACKET, "port$o", egressPort); //Model the processing time on a data packet
            break; // end case
        }
        case INSERTRULE_PULL:
        {
            pck = check_and_cast<InsertionPacket *>(message);
            if(!(pck->getSwitch_type() == (int)par("Type") &&  pck->getDestination() == id)){ //If this switch is not the destination
                egressPort = internal_forwarding_port(pck);
                send(pck, "port$o", egressPort);
                break;
            }
            //break; //in purpose
        }
        case INSERTRULE_PUSH:
        {
            pck = check_and_cast<InsertionPacket *>(message);
            m1 = new InsertionPacket("Insertion delay packet");
            m1->setKind(INSERTION_DELAY_PCK);
            m1->setRule(pck->getRule()); //not necessary
            scheduleAt(simTime() + INSERTION_DELAY,m1);

            if(cache.size() < CACHE_PERCENTAGE * (int)par("CacheSize")){
                s = SAMPLE_SIZE;
            }
            else{
                s = 1;
            }
            uint64_t rule_for_eviction = which_rule_to_evict(s);

            m2 = new InsertionPacket("Eviction delay packet");
            m2->setKind(EVICTION_DELAY_PCK);
            m2->setRule(rule_for_eviction);
            scheduleAt(simTime() + s*EVICTION_DELAY,m2);
            delete pck;
            break; // end case
        }
        case INSERTION_DELAY_PCK:
        {
            pck = check_and_cast<InsertionPacket *>(message);
            ruleStruct new_rule;
            new_rule.count = 0;
            new_rule.last_time = simTime();
            cache.insert({ pck->getRule(), new_rule });
            delete pck;
            break; // end case
        }
        case EVICTION_DELAY_PCK:
        {
            pck = check_and_cast<InsertionPacket *>(message);
            cache.erase( pck->getRule()); // evict the rule
            delete pck;
            break; // end case

        }
        case FLUSH_ELEPHANT_PKT:
        {
            elephant_table.clear(); //clear the elephant_table
            scheduleAt(simTime() + FLUSH_ELEPHANT_TIME,message);
            break; // end case
        }
        case CHECK_FOR_ELEPHANT_PKT:
        {
            for (std::map<uint64_t, elephant_struct>::iterator it=elephant_table.begin(); it!=elephant_table.end(); ++it){
                if((it->second).count/(simTime() - (it->second).first_appearance) > BANDWIDTH_ELEPHANT_THRESHOLD && (simTime() - (it->second).last_time) > ALREADY_REQUESTED_THRESHOLD && (cache.count(it->first)) == 0){
                    //If the bandwidth of this flow is greater than a certain threshold and also that it has not been requested recently and also is not in the cache
                    //send request pkt:
                    pck = new InsertionPacket("Request for a rule");
                    pck->setKind(RULE_REQUEST);
                    pck->setRule(it->first);
                    //pkt->setType(PULL); delete
                    pck->setSwitch_type((int)par("Type"));
                    pck->setDestination(id);
                    egressPort = miss_table_search(it->first);
                    send(pck, "port$o", egressPort);

                }
            }
            scheduleAt(simTime() + CHECK_FOR_ELEPHANT_TIME,message);
            break; // end case
        }
        case RULE_REQUEST:
        {
            pck = check_and_cast<InsertionPacket *>(message);
            if(cache.count(pck->getRule()) > 0){//The rule is in the cache
                pck->setKind(INSERTRULE_PULL);
                pck->setName("Insert rule Packet");
                //The rule and the switch destination are already sets
                egressPort = internal_forwarding_port(pck);
                send(pck, "port$o", egressPort);
            }
            else { // forward the packet like a miss
                egressPort = miss_table_search(pck->getDestination());
                send(pck, "port$o", egressPort);
            }
            break; // end case
        }
    }
}
void Switch::fc_send(DataPacket *msg){
    cGate *gate = msg->getArrivalGate();
    int arrivalGate;
    if(gate)arrivalGate = gate->getIndex();   //Get arrival port
    else return;
    uint64_t rule = msg->getDestination();
    InsertionPacket *conpacket = new InsertionPacket("Insert rule Packet");
    conpacket->setKind(INSERTRULE_PUSH);
    conpacket->setRule(rule);
    cache[rule].count = 0; //set the counter to zero in order to avoid burst of fc_send
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

uint64_t Switch::which_rule_to_evict(int s){
    uint64_t samples[SAMPLE_SIZE];
    uint64_t evicted_rule_key;
    simtime_t min = 1000000;

    auto iter =  cache.begin();

    for(int i = 0;i < s;i++){
        std::advance(iter,uniform(0, cache.size()));
        samples[i] = iter->first;
        iter =  cache.begin();
    }
    for(int i = 0;i < s;i++){
        if(cache[samples[i]].last_time < min){
            min = cache[samples[i]].last_time;
            evicted_rule_key = samples[i];
        }
    }

    return evicted_rule_key;
}

int Switch::internal_forwarding_port (InsertionPacket *msg){
    int destination_type  = msg->getSwitch_type();
    int destination = msg->getDestination();
    int egress_port;
    int num_of_agg = (int)(getParentModule()->par("NumOfAggregation"));
    switch((int)par("Type")){
        case CONTROLLERSWITCH:
            if(destination_type == AGGREGATION){
                egress_port = destination + 1; // Because the id starts from 0 and the controller switch is connected to the aggregation on ports 1, 2,...
            }
            else {
                egress_port = (int)uniform(1,num_of_agg + 1); //Draw a random port , the aggregation will know how to deal
            }
            break;
        case AGGREGATION:
            egress_port = destination + 2; // Because the id starts from 0 and the controller switch is connected to the aggregation on ports 2, 3,...
            break;
    }
    return egress_port;
}

int Switch::hash(uint64_t dest){
    int num_of_agg = (int)(getParentModule()->par("NumOfAggregation"));
    return (int)ceil((float)dest/(float)(POLICYSIZE/num_of_agg));
    //return (int)uniform(1,num_of_agg + 1);
}

void Switch::finish(){
    delete[] miss_table;
}


}; // namespace
