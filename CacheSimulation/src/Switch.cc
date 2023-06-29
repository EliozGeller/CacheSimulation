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
#include <fstream>

namespace cachesimulation {

Define_Module(Switch);


void Switch::initialize()
{

    //flow_count:
    flow_count_hist.setName("flow count");

    //insertion_count:
    insertion_count.setName("insertion_count");
    best_flow_size.setName("best_flow_size");

    activity_time_of_a_rule_A.setName("activity_time_of_a_rule_A");
    activity_time_of_a_rule_B.setName("activity_time_of_a_rule_B");

    //set id:
    id = getIndex();

    //set the number of ports:
    number_of_ports = gateSize("port");

    //start of par:
    type = par("Type").intValue();
    elephant_sample_rx = stoi(getParentModule()->par("elephant_sample_rx").stdstringValue());
    processing_time_on_data_packet_in_sw = stold(getParentModule()->par("processing_time_on_data_packet_in_sw").stdstringValue());
    insertion_delay = stold(getParentModule()->par("insertion_delay").stdstringValue());
    cache_percentage = stold(getParentModule()->par("cache_percentage").stdstringValue());


    max_cache_size = (int)par("max_cache_size").doubleValue();




    if(type == AGGREGATION)packet_index_for_decision = getParentModule()->par("packet_index_for_decision_Agg").intValue();
    if(type == CONTROLLERSWITCH)packet_index_for_decision = getParentModule()->par("packet_index_for_decision_cosw").intValue();
    if(type == AGGREGATION)diversity_th = getParentModule()->par("diversity_th").intValue();
    if(type == CONTROLLERSWITCH)diversity_th = 1000;
    algorithm = getParentModule()->par("algorithm").stdstringValue();



    recordScalar("max_cache_size: ",max_cache_size);
    eviction_sample_size = stoi(getParentModule()->par("eviction_sample_size").stdstringValue());
    eviction_delay = stold(getParentModule()->par("eviction_delay").stdstringValue());
    flush_elephant_time = stold(getParentModule()->par("flush_elephant_time").stdstringValue());
    check_for_elephant_time = stold(getParentModule()->par("check_for_elephant_time").stdstringValue());
    elephant_table_max_size = stoi(getParentModule()->par("elephant_table_size").stdstringValue());
    num_of_agg = (int)(getParentModule()->par(  "NumOfAggregation"));
    //end of par
    byte_count = 0;
    for(int i = 0; i < 10;i++){
        byte_count_per_link[i] = 0;
        before_hit_byte_count[i] = 0;
        after_hit_byte_count[i] = 0;
    }
    policy_size = stold(getParentModule()->par("policy_size").stdstringValue());
    bandwidth_elephant_threshold = stoull(getParentModule()->par("bandwidth_elephant_threshold").stdstringValue());
    EV << "bandwidth_elephant_threshold = " << bandwidth_elephant_threshold << endl;
    already_requested_threshold = (simtime_t)stold( getParentModule()->par("already_requested_threshold").stdstringValue());;
    if(par("Type").intValue() == AGGREGATION){
        threshold = getParentModule()->par("push_threshold_in_aggregation").doubleValue();
    }
    if(par("Type").intValue() == CONTROLLERSWITCH){
        threshold = getParentModule()->par("push_threshold_in_controller_switch").doubleValue();
    }
    recordScalar("push threshold: ",threshold);
    if(type == TOR){
        miss_table_size = getParentModule()->par("NumOfAggregation");
        miss_table = new partition_rule[miss_table_size];


        // Define the initial partition , Should be deleted when there will be a real partition
        uint64_t last = 0;
        uint64_t diff = (uint64_t)(policy_size/(int)(getParentModule()->par("NumOfAggregation")));
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
        miss_table[0].high = policy_size;
        miss_table[0].port = 0;
    }

    cache_occupancy.setName("cache_occupancy");

    //Schedule events:
    //new Histogram;
    cMessage *hist_msg = new cMessage("hist_msg");
    hist_msg->setKind(HIST_MSG);
    scheduleAt(simTime() + START_TIME + TIME_INTERVAL_FOR_OUTPUTS,hist_msg);

    cMessage *m = new cMessage("flow_count");
    m->setKind(INTERVAL_PCK);
    scheduleAt(simTime() + START_TIME + INTERVAL,m);
    //end new histogram



    //initialize Push process:
    if(!getParentModule()->par("run_push").boolValue()){
        threshold = (unsigned long long)(-1) ;//will set infinity
    }

    //initialize Elephant process:
    run_elephant = getParentModule()->par("run_elephant").boolValue();
    if(run_elephant && type == TOR){
        elephant_count = 0;
        cMessage* m1 = new cMessage("Flush elephant timer");
        cMessage* m2 = new cMessage("Check for elephant timer");

        m1->setKind(FLUSH_ELEPHANT_PKT);
        m2->setKind(CHECK_FOR_ELEPHANT_PKT);

        scheduleAt(simTime() + START_TIME ,m1);
        scheduleAt(simTime() + START_TIME,m2);
    }

    estimate_rate_interval = getParentModule()->par("estimate_rate_interval").doubleValue();
    if(threshold != (unsigned long long)(-1) /* infinity */ and threshold != 0){
        //estimate_rate_interval = (1500.0 * 8.0 * 10.0 /*10 packets*/)/(threshold);
    }
    estimate_rate_interval = 100e-6;
    if(true){
        //cMessage* m1 = new cMessage("Estimate rate packet");
        //m1->setKind(ESTIMATE_RATE_PCK);
        //scheduleAt(simTime() + START_TIME + estimate_rate_interval,m1);
    }




    /*
    cMessage* lzy_evict = new cMessage("Lazy eviction timer for insertion");
    lzy_evict->setKind(LZY_EVICT);
    scheduleAt(simTime() + START_TIME + 1000*MICROSECOND ,lzy_evict);
*/

}

void Switch::handleMessage(cMessage *message)
{

    static int number_of_flows_which_ends_during_the_interval= 0;
    int egressPort;
    int kind_of_packet = message->getKind();
    int ingressPort = -1;
    if (!message->isSelfMessage())ingressPort =  message->getArrivalGate()->getIndex();
    int s;
    DataPacket *msg;
    InsertionPacket *pck,*m1,*m2;

    //flow_count and byte_count:
    if( kind_of_packet == DATAPACKET ||  kind_of_packet == HITPACKET){
        msg = check_and_cast<DataPacket *>(message);
        flow_count.insert({msg->getDestination(),1});

        //insert last message:
        if(msg->getLast_packet() and false){ // not in use
           flow_count.erase(msg->getDestination());
           //delete pkt;
           number_of_flows_which_ends_during_the_interval++;
           //return;
        }




        //byte_count:
        byte_count += msg->getByteLength();
        byte_count_per_link[ingressPort] += msg->getByteLength();
        if(msg->getExternal_destination() != 1){
           before_hit_byte_count[ingressPort] += msg->getByteLength();
        }
        else{
           after_hit_byte_count[ingressPort] += msg->getByteLength();
        }
    }



    if(kind_of_packet == INTERVAL_PCK){
        flow_count_hist.collect(flow_count.size());
        number_of_flows_which_ends_during_the_interval = 0;
        flow_count.clear();

        cache_occupancy.collect((double)((double)(cache.size())/(max_cache_size)?max_cache_size:1));
        //if( which_switch_i_am() == " ToR[0] ")std::cout << "c = " << (double)((double)(cache.size())/max_cache_size) <<"    " << cache.size() <<"    " << cache.size() << which_switch_i_am() <<endl;

        number_of_insertions.collect(insertion_count_pull + insertion_count_push);
        insertion_count.collect(((insertion_count_pull + insertion_count_push) ?((long double)(insertion_count_pull))/((long double)(insertion_count_pull + insertion_count_push)) : 0));
        insertion_count_push = 0;
        insertion_count_pull = 0;

        scheduleAt(simTime() + INTERVAL,message);
        return;
    }
    //end flow count


    //histogram per 1 sec:
    if(kind_of_packet == HIST_MSG){
      string name =  "";
      simtime_t t = simTime() - TIME_INTERVAL_FOR_OUTPUTS,t1 =  simTime();
      name =  name + my_to_string(t.dbl()) + "  -  " + my_to_string(t1.dbl());
      string name1 = name + ":flow_count";
      flow_count_hist.recordAs(name1.c_str());
      name1 = name + ":cache_occupancy";
      cache_occupancy.recordAs(name1.c_str());
      name1 = name + ":insertion_count";
      insertion_count.recordAs(name1.c_str());
      name1 = name + ":number_of_insertions";
      number_of_insertions.recordAs(name1.c_str());
      name1 = name + ":best_flow_size";
      recordScalar(name1.c_str(),sizes[index_flow_size]);

      recordScalar("Bandwidth: ", (long double)(byte_count*8)/(simTime().dbl() - START_TIME));

      ofstream MyFile("best_flow_size reset.txt");
      MyFile <<  best_flow_size.str() << std::endl;
      MyFile.close();

      scheduleAt(simTime() + TIME_INTERVAL_FOR_OUTPUTS,message);
      return;
    }
    //end histogram per 1 s









    //RX:
    //Elephant Detector:
    if(run_elephant and type == TOR and kind_of_packet == DATAPACKET and (elephant_count % elephant_sample_rx == 0)){ // Act only if this is a Data packet in the ToR
        elephant_count++;
        msg = check_and_cast<DataPacket *>(message);


        uint64_t dest = msg->getDestination();

        if(elephant_table.count(dest) > 0){//The flow is in the table
            elephant_table[dest].count++;
            elephant_table[dest].last_time = simTime();
        }
        else {
            if( elephant_table_size <= elephant_table_max_size){ //Every few packets we will sample a packet in RX
               elephant_table_size++;
               elephant_struct new_pkt;
               //new_pkt.byte_count = 0;
               new_pkt.count = 0;
               new_pkt.first_appearance = simTime();
               new_pkt.last_time = simTime();
               new_pkt.flow_size = (int)msg->getFlow_size();
               new_pkt.rate = msg->getRate();
               EV << "  new_pkt.flow_size = " <<  new_pkt.flow_size << endl;
               elephant_table[dest] = new_pkt;
           }
        }

    }








    //TX:
    switch(kind_of_packet){
        case HITPACKET:
        {
            msg = check_and_cast<DataPacket *>(message);
            egressPort = hit_forward(msg->getDestination());
            sendDelayed(msg,processing_time_on_data_packet_in_sw, "port$o", egressPort); //Model the processing time on a data packet
            break; // end case
        }
        case DATAPACKET:
        {

            //
            EV << which_switch_i_am()  <<  "  t = "  <<  simTime()  <<  endl;
            //
            msg = check_and_cast<DataPacket *>(message);
            switch(cache_search(msg,ingressPort)){
              case THRESHOLDCROSS: //in case of THRESHOLDCROSS also case of FOUND will activate
                  if(type != TOR)fc_send(msg);
                  //break; //in purpose
              case FOUND:
                  egressPort = hit_forward(msg->getDestination());
                  msg->setExternal_destination(1);
                  msg->setKind(HITPACKET);
                  hit_packets++;
                  break;
              case NOTFOUND:
                  int switch_index_type = type_of_switch_to_index(type);
                  msg->setMiss_path(switch_index_type,id);
                  egressPort = miss_table_search(msg->getDestination());
                  msg->setMiss_hop(msg->getMiss_hop() + 1);
                  miss_packets++;
                  break;
            }

            sendDelayed(msg,processing_time_on_data_packet_in_sw, "port$o", egressPort); //Model the processing time on a data packet
            break; // end case
        }
        case GENERAL_INSERTRULE:
        {
            pck = check_and_cast<InsertionPacket *>(message);

            bubble(pck->getInsert_to_switch(type_of_switch_to_index(type)));

            string action  = pck->getInsert_to_switch(type_of_switch_to_index(type));
            if(action == "insert"){//insert the rule:
                cache_size_t++;
                //Schedule an insertion
                pck = check_and_cast<InsertionPacket *>(message);
                m1 = new InsertionPacket("Insertion delay packet");
                m1->setKind(INSERTION_DELAY_PCK);
                m1->setRule(pck->getRule()); //not necessary
                scheduleAt(simTime() + insertion_delay,m1);


                if(cache_size_t >= 0.8 * max_cache_size){
                    if(cache_size_t < 0.9 * max_cache_size){
                        s = eviction_sample_size ;
                    }
                    else {
                        s = 1;
                    }
                    //uint64_t rule_for_eviction = which_rule_to_evict(s);

                    //Schedule an eviction
                    m2 = new InsertionPacket("Eviction delay packet");
                    m2->setKind(EVICTION_DELAY_PCK);
                    m2->setS(s);
                    scheduleAt(simTime() + s*eviction_delay,m2);

                }
                //end Schedule an insertion
            }
            if(action == "remove"){//remove the rule:
                //Schedule an eviction
                m2 = new InsertionPacket("Eviction delay packet");
                m2->setKind(EVICTION_DELAY_PCK);
                m2->setLRU(false);
                m2->setRule(pck->getRule());
                scheduleAt(simTime() + eviction_delay,m2);
            }




            //forward the packet or delete it:
            if(type == TOR){
                delete pck; //delete the packet if it's in the ToR
            }
            else{//forward the packet down stream:
                pck->setDestination(pck->getPath(type_of_switch_to_index(type) - 1));
                pck->setSwitch_type(index_of_switch_to_type(type_of_switch_to_index(type) - 1));
                egressPort = internal_forwarding_port(pck);
                sendDelayed(pck,processing_time_on_data_packet_in_sw, "port$o", egressPort); //Model the processing time on a data packet
            }
            break;
        }
        case INSERTRULE_PULL:
        {
            pck = check_and_cast<InsertionPacket *>(message);
            if(!(pck->getSwitch_type() == type &&  pck->getDestination() == id)){ //If this switch is not the destination
                egressPort = internal_forwarding_port(pck);
                //send(pck, "port$o", egressPort);
                sendDelayed(pck,processing_time_on_data_packet_in_sw, "port$o", egressPort); //Model the processing time on a data packet
                break;
            }
            //break; //in purpose
        }
        case INSERTRULE_PUSH: // The real insertion:
        {

           //statics:
           if(kind_of_packet == INSERTRULE_PULL){
               insertion_count_pull++;
           }
           else {
               insertion_count_push++;
           }
            //increment the cache size:
            cache_size_t++;

            //Schedule an insertion
            pck = check_and_cast<InsertionPacket *>(message);
            m1 = new InsertionPacket("Insertion delay packet");
            m1->setKind(INSERTION_DELAY_PCK);
            m1->setRule(pck->getRule()); //not necessary
            scheduleAt(simTime() + insertion_delay,m1);


            if(cache_size_t >= 0.8 * max_cache_size){
                if(cache_size_t < 0.9 * max_cache_size){
                    s = eviction_sample_size ;
                }
                else {
                    s = 1;
                }
                //uint64_t rule_for_eviction = which_rule_to_evict(s);

                //Schedule an eviction
                m2 = new InsertionPacket("Eviction delay packet");
                m2->setKind(EVICTION_DELAY_PCK);
                m2->setS(s);
                scheduleAt(simTime() + s*eviction_delay,m2);

            }

            delete pck;
            break; // end case
        }
        case INSERTION_DELAY_PCK://The real insertion:
        {
            pck = check_and_cast<InsertionPacket *>(message);
            ruleStruct new_rule;
            new_rule.count = 0;
            new_rule.bit_count = 0;
            new_rule.last_time = simTime();
            new_rule.insertion_time = simTime();
            new_rule.port_dest_count.assign(number_of_ports, 0);
            new_rule.first_packet.assign(number_of_ports, 0);
            new_rule.rule_diversity = 0;
            cache.insert({ pck->getRule(), new_rule });
            delete pck;
            bubble("rule insertion");
            break; // end case
        }
        case EVICTION_DELAY_PCK: //The real eviction:
        {
            pck = check_and_cast<InsertionPacket *>(message);
            uint64_t rule_for_eviction;
            bool remove_rule = false;
            if(!pck->getLRU()){//Remove NOT according to LRU, but a specific rule. if so, remove "rule" from the cache:
                rule_for_eviction = pck->getRule();
                remove_rule = true;
            }
            else {
                if(cache.size() >= 0.8 * max_cache_size){
                    rule_for_eviction = which_rule_to_evict( pck->getS() /*s*/);
                    remove_rule = true;
                }
            }
            if(remove_rule){//Does we going to remove the rule?
                //activity_time_of_a_rule.collect(cache[rule_for_eviction].last_time - cache[rule_for_eviction].insertion_time);//pick living time of the rule
                if(rule_for_eviction >= 10001){//App A
                    activity_time_of_a_rule_A.collect(cache[rule_for_eviction].last_time - cache[rule_for_eviction].insertion_time);//pick living time of the rule
                }
                else {//App B
                    activity_time_of_a_rule_B.collect(cache[rule_for_eviction].last_time - cache[rule_for_eviction].insertion_time);//pick living time of the rule
                }
                cache.erase(rule_for_eviction); // evict the rule
                cache_size_t--;
            }

            delete pck;
            bubble("rule eviction");
            break; // end case

        }
        case FLUSH_ELEPHANT_PKT:
        {
            elephant_table.clear(); //clear the elephant_table
            elephant_count = 0;
            elephant_table_size = 0;


            //Update bandwidth_elephant_threshold:
/*
            double hit_ratio = (hit_packets + miss_packets)?(((double)(hit_packets))/((double)(hit_packets + miss_packets))):(0);
            int next_step = sign(hit_ratio - abs(last_hit_ratio))*sign(last_hit_ratio);//if we are good proceed, else change direct;
            index_flow_size = min(42,max(25,index_flow_size + next_step));

            //if(id == 0 && type == TOR)std::cout <<"CCCC!!!!!!! time = "<< simTime() <<"  best_flow_size = "<< sizes[index_flow_size] <<"  ,index_flow_size = " << index_flow_size<< "  prove = "<< sign(hit_ratio - abs(last_hit_ratio)) <<endl;
            //Reset Hit Ratio:
            hit_packets = 0;
            miss_packets = 0;
            last_hit_ratio = (double)(next_step)*hit_ratio;//keep the last step;
            best_flow_size.record(index_flow_size);

            //End bandwidth_elephant_threshold:

*/




            scheduleAt(simTime() + flush_elephant_time,message);
            break; // end case
        }
        case CHECK_FOR_ELEPHANT_PKT:
        {
            for (std::map<uint64_t, elephant_struct>::iterator it=elephant_table.begin(); it!=elephant_table.end(); ++it){
                if(/*(it->second).count >= bandwidth_elephant_threshold*/  (it->second).rate >= bandwidth_elephant_threshold &&  (cache.count(it->first)) == 0 /* &&(simTime() - (it->second).last_time) > already_requested_threshold */){
                    //If the bandwidth of this flow is greater than a certain threshold and also that it has not been requested recently and also is not in the cache
                    //send request pkt:
                    pck = new InsertionPacket("Request for a rule");
                    pck->setKind(RULE_REQUEST);
                    pck->setRule(it->first);
                    //pkt->setType(PULL); delete
                    pck->setSwitch_type(type);
                    pck->setDestination(id);
                    egressPort = miss_table_search(it->first);
                    send(pck, "port$o", egressPort); //needed delay?

                }
            }
            scheduleAt(simTime() + check_for_elephant_time,message);
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
                sendDelayed(pck,processing_time_on_data_packet_in_sw, "port$o", egressPort); //Model the processing time on a data packet
            }
            else { // forward the packet like a miss
                egressPort = miss_table_search(pck->getDestination());
                sendDelayed(pck,processing_time_on_data_packet_in_sw, "port$o", egressPort); //Model the processing time on a data packet
            }
            break; // end case
        }
        case LZY_EVICT:
        {

            if(cache.size() >= 0.9 * max_cache_size){
                s = eviction_sample_size ;
                uint64_t rule_for_eviction = which_rule_to_evict(s);

                m2 = new InsertionPacket("Eviction delay packet");
                m2->setKind(EVICTION_DELAY_PCK);
                m2->setRule(rule_for_eviction);
                scheduleAt(simTime() + s*eviction_delay,m2);

            }


            scheduleAt(simTime() + 1000*MICROSECOND ,message);
            break;
        }
        case ESTIMATE_RATE_PCK: //Reset the port-destination counters in window:
        { //delete

            //hit ratio:
            double hit_ratio = (hit_packets + miss_packets)?(((double)(hit_packets))/((double)(hit_packets + miss_packets))):(0);
            hit_packets = 0;
            miss_packets = 0;

            par("hit_ratio").setDoubleValue(hit_ratio);


            //print cache content:
            static ofstream MyFile("switch.txt");
            MyFile << which_switch_i_am() <<"  hit_ratio = "  << hit_ratio  << "  time = "  <<  simTime() << "\ncache content:" <<  endl;


            int i = 0;
            for (auto it = cache.begin(); simTime() == 3.001 and it != cache.end(); ++it){
                MyFile << "cache[" <<  i  <<  "] = " << it->first << endl;
                i++;
            }

            //


            for (auto it = cache.begin(); it != cache.end(); ++it) {
                for (int i = 0; i < number_of_ports; i++) {
                    it->second.port_dest_count[i] = 0;
                }
                it->second.bit_count = 0;
            }
            scheduleAt(simTime() + estimate_rate_interval,message);
            break;
        }
    }
}
void Switch::fc_send(DataPacket *msg){
    //this function generate an insert packet in the switch and send it with the corresponds rule to the ingress port.
    cGate *gate = msg->getArrivalGate();
    int arrivalGate;
    if(gate)arrivalGate = gate->getIndex();   //Get arrival port
    else return;
    uint64_t rule = msg->getDestination();
    InsertionPacket *conpacket = new InsertionPacket("Insert rule Packet");
    conpacket->setKind(INSERTRULE_PUSH);
    conpacket->setRule(rule);
    //cache[rule].count = 0; //set the counter to zero in order to avoid burst of fc_send
    sendDelayed(conpacket,processing_time_on_data_packet_in_sw, "port$o", arrivalGate); //Model the processing time on a data packet
}
int Switch::cache_search(DataPacket *msg,int ingressPort){
    /*ingressPort is int between 2 to m + 1 where m is the number of ToRs if the switch is aggregation switch
    and 1 to number of aggregation  if is controller switch */
    uint64_t rule = msg->getDestination();
    auto it = cache.find(rule);

    if (it == cache.end()) {// not found
        return NOTFOUND;
    }
    else {// found

        if(it->second.port_dest_count[ingressPort] == 0){ //set the first packet as the first packet that the rule manage to catch
            it->second.first_packet[ingressPort] = simTime();
        }

        it->second.port_dest_count[ingressPort] += msg->getBitLength();
        it->second.bit_count += msg->getBitLength();
        it->second.count++;
        it->second.last_time = simTime();
        it->second.rule_diversity |= (uint64_t)(1<<((ingressPort - 2 >= 0)?(ingressPort - 2):(0)));





        //!!! algorithm list = {"Push" , "Fast" , "Fast n-th" ,"diversity-Push" ,"non Push"}!!!!!!!!


        if(algorithm == "Push"){
            if(((it->second.port_dest_count[ingressPort] - 12000.0)/(simTime() - it->second.first_packet[ingressPort])) >= threshold  and it->second.port_dest_count[ingressPort] > packet_index_for_decision*1500.0*8.0){  //port-dest rate estimate
                return THRESHOLDCROSS;
            }
            else {
                return FOUND;
            }
        }
        if(algorithm == "Fast"){
            return THRESHOLDCROSS;
        }
        if(algorithm == "Fast n-th"){
            if(it->second.port_dest_count[ingressPort] > packet_index_for_decision*1500.0*8.0){  //fast cach from 10th packet
                return THRESHOLDCROSS;
            }
            else {
                return FOUND;
            }
        }
        if(algorithm == "diversity-Push"){
            if(count_one(it->second.rule_diversity) <= diversity_th and it->second.count >= packet_index_for_decision){
                return THRESHOLDCROSS;
            }
            else {
                return FOUND;
            }
        }
        if(algorithm == "non Push" or  algorithm == "cFast"){
            return FOUND;
        }
    }
}

int Switch::hit_forward(uint64_t dest){
    int egressPort;
    switch(type){
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
    std::cout << "ERROR in miss_table_search function: try to find the port and fail. destination =  "<< dest <<endl;

}

uint64_t Switch::which_rule_to_evict(int s){
    uint64_t samples[100]; //change
    uint64_t evicted_rule_key;
    simtime_t min = 1000000;

    //auto iter =  cache.begin();

    for(int i = 0;i < s;i++){
        auto iter =  cache.begin();
        std::advance(iter,uniform(0, cache.size()));
        samples[i] = iter->first;
        //iter =  cache.begin();
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
    switch(type){
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
    EV<< "dest = "<< dest<<endl;
    return (int)ceil((float)dest/(float)(policy_size/num_of_agg));
    //return (int)uniform(1,num_of_agg + 1);
}

double Switch::get_hit_ratio(){
    return (hit_packets + miss_packets)?(((double)(hit_packets))/((double)(hit_packets + miss_packets))):(0);
}

std::string Switch::which_switch_i_am(){
    string s = "";
    switch(type){
    case TOR:
        s = s + " ToR[" + to_string(id) + "] ";
        break;
    case AGGREGATION:
        s = s + " Aggregation[" + to_string(id) + "] ";
        break;
    case CONTROLLERSWITCH:
        s = s + " ControllerSwitch ";
        break;
    }

    return s;
}



void Switch::finish(){
    delete[] miss_table;
    //if(type == TOR)EV << "Bandwidth in ToR "<< id << " is " << abs(8*byte_count/simTime()) << " bps" <<  endl;
    string s;
    if(type == TOR)s = "ToR";
    if(type == AGGREGATION)s = "AGGREGATION";
    if(type == CONTROLLERSWITCH)s = "CONTROLLERSWITCH";

    EV<< s << " " << id << ":" << endl;
    EV << "Bandwidth: " << (long double)(byte_count*8)/simTime().dbl() << " bps" <<  endl;
    recordScalar("Bandwidth: ", (long double)(byte_count*8)/(simTime().dbl() - START_TIME));
    for(int i = 0;i < 10;i++){
        if(byte_count_per_link[i])EV << "Bandwidth on link " << i << " is  " << abs(8*byte_count_per_link[i]/simTime()) << " bps" <<  endl;
        if(before_hit_byte_count[i])EV << "Bandwidth of packets before hit on link " << i << " is  " << abs(8*before_hit_byte_count[i]/simTime()) << " bps" <<  endl;
        if(after_hit_byte_count[i])EV << "Bandwidth of packets after hit on link " << i << " is  " << abs(8*after_hit_byte_count[i]/simTime()) << " bps" <<  endl;
    }
    EV  <<  endl;
    EV  <<  endl;

    flow_count_hist.recordAs("flow count");
    cache_occupancy.recordAs("cache_occupancy");
    activity_time_of_a_rule_A.recordAs("activity_time_of_a_rule_A");
    activity_time_of_a_rule_B.recordAs("activity_time_of_a_rule_B");

    int cache_content_by_app_count = 0;
    for (const auto& rule : cache) {
            if(rule.first > 10000)cache_content_by_app_count++;
            if(rule.first >= 10001){//App A
                activity_time_of_a_rule_A.collect(cache[rule.first].last_time - cache[rule.first].insertion_time);//pick living time of the rule
            }
            else {//App B
                activity_time_of_a_rule_B.collect(cache[rule.first].last_time - cache[rule.first].insertion_time);//pick living time of the rule
            }

    }

    recordScalar("cache_content_by_app: ", ((double)cache_content_by_app_count)/((double)cache.size()));




}


}; // namespace
