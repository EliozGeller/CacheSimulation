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

#include "Controller.h"


namespace cachesimulation {

Define_Module(Controller);

void Controller::initialize()
{

    //set all parameters from csv file;
    set_all_parameters();
    initialization_start_time_for_flows();
    byte_counter = 0;

    // Define the initial partition
    miss_table_size = getParentModule()->par("NumOfAggregation");
    partition = new partition_rule[miss_table_size];

    uint64_t policy_size =  stoull(getParentModule()->par("policy_size").stdstringValue());

    uint64_t last = 0;
    uint64_t diff = (uint64_t)(policy_size/(int)(getParentModule()->par("NumOfAggregation")));
    for(int i = 0;i < miss_table_size;i++){
        partition[i].low = last;
        partition[i].high = last + diff;
        partition[i].port = i + 1;
        last = last + diff + 1;
    }
    // End Define the initial partition

    //set processing_time_on_data_packet_in_controller:
    processing_time_on_data_packet_in_controller = (simtime_t)stold(getParentModule()->par("processing_time_on_data_packet_in_controller").stdstringValue());


    //new Histogram;
    bandwidth_hist.setName("bandwidth hist");
    cMessage *hist_msg = new cMessage("hist_msg");
    hist_msg->setKind(HIST_MSG);
    scheduleAt(simTime() + START_TIME + TIME_INTERVAL_FOR_OUTPUTS,hist_msg);

    cMessage *m = new cMessage("flow_count");
    m->setKind(INTERVAL_PCK);
    scheduleAt(simTime() + START_TIME + INTERVAL,m);
    //end new histogram


    //Start scheduling partition messages
    //Data_for_partition* pkt = new Data_for_partition("Data for partition msg");
    //pkt->setKind(DATA_FOR_PARTITION);
    //sendDelayed(pkt, PARTITION_RATE, "port$o", 0);




}

void Controller::handleMessage(cMessage *message)
{
    DataPacket *msg;
    InsertionPacket *conpacket;
    Data_for_partition *pkt;
    switch(message->getKind()){
    case DATAPACKET:
        msg = check_and_cast<DataPacket *>(message);
        byte_counter += msg->getByteLength();
        conpacket = new InsertionPacket("Insert rule Packet");
        conpacket->setKind(INSERTRULE_PUSH);
        conpacket->setRule(msg->getDestination());
        sendDelayed(conpacket,processing_time_on_data_packet_in_controller, "port$o", 0); //Model the processing time on a data packet
        msg->setExternal_destination(1);
        msg->setKind(HITPACKET);
        msg->setName("Hit packet");
        sendDelayed(msg,processing_time_on_data_packet_in_controller, "port$o", 0); //Model the processing time on a data packet
        break;
    case DATA_FOR_PARTITION://change
        pkt = check_and_cast<Data_for_partition *>(message);
        delete pkt;
        /*
        partition_calculation(pkt);
        update_miss_forwarding();
        sendDelayed(pkt, PARTITION_RATE, "port$o", 0);//
        */
        break;

    case RULE_REQUEST:
    {
        conpacket = check_and_cast<InsertionPacket *>(message);
        conpacket->setKind(INSERTRULE_PULL);
        conpacket->setName("Insert rule Packet");
        //The rule and the switch destination are already sets
        sendDelayed(conpacket,processing_time_on_data_packet_in_controller, "port$o", 0); //Model the processing time on a data packet
        break;
    }
    case INTERVAL_PCK:
    {
        bandwidth_hist.collect(((long double)(byte_counter*8))/(long double)(INTERVAL*1000000000000.0));
        byte_counter = 0;


        scheduleAt(simTime() + INTERVAL,message);
        break;
    }
    case HIST_MSG:
    {
        string name1,name =  "";
        simtime_t t = simTime() - TIME_INTERVAL_FOR_OUTPUTS,t1 =  simTime();
        name =  name + my_to_string(t.dbl()) + "  -  " + my_to_string(t1.dbl());
        name1 = name + ":bandwidth_hist";
        bandwidth_hist.recordAs(name1.c_str());

        scheduleAt(simTime() + TIME_INTERVAL_FOR_OUTPUTS,message);
        break;
    }

    }
}


void Controller::set_all_parameters(){
    string s;
    vector<vector<string>> data_file = read_data_file(PATH_DATA);


    s = get_parameter(data_file,"Policy size");
    getParentModule()->par("policy_size").setStringValue(s);

    s = get_parameter(data_file,"Cache size");
    getParentModule()->par("cache_size").setStringValue(s);

    s = get_parameter(data_file,"Propagation");
    getParentModule()->par("propagation_time").setStringValue(s);

    s = get_parameter(data_file,"Processing time on a data packet in switch");
    getParentModule()->par("processing_time_on_data_packet_in_sw").setStringValue(s);

    s = get_parameter(data_file,"Processing time on a data packet in controller");
    getParentModule()->par("processing_time_on_data_packet_in_controller").setStringValue(s);

    s = get_parameter(data_file,"Processing time for rule insertion");
    getParentModule()->par("insertion_delay").setStringValue(s);

    s = get_parameter(data_file,"Processing time for rule eviction");
    getParentModule()->par("eviction_delay").setStringValue(s);

    s = get_parameter(data_file,"Elephant table size");
    getParentModule()->par("elephant_table_size").setStringValue(s);

    s = get_parameter(data_file,"Elephant flush table timer");
    getParentModule()->par("flush_elephant_time").setStringValue(s);

    s = get_parameter(data_file,"Elephant detection timer");
    getParentModule()->par("check_for_elephant_time").setStringValue(s);

    s = get_parameter(data_file,"Sample rate");
    getParentModule()->par("elephant_sample_rx").setStringValue(s);

    s = get_parameter(data_file,"Bandwidth threshold");
    getParentModule()->par("bandwidth_elephant_threshold").setStringValue(s);

    s = get_parameter(data_file,"Timestamp threshold");
    getParentModule()->par("already_requested_threshold").setStringValue(s);

    s = get_parameter(data_file,"Threshold in aggregation");
    getParentModule()->par("push_threshold_in_aggregation").setStringValue(s);

    s = get_parameter(data_file,"Threshold in controller switch");
    getParentModule()->par("push_threshold_in_controller_switch").setStringValue(s);

    s = get_parameter(data_file,"Cache percentage");
    getParentModule()->par("cache_percentage").setStringValue(s);

    s = get_parameter(data_file,"sample size");
    getParentModule()->par("eviction_sample_size").setStringValue(s);

    s = get_parameter(data_file,"Inter arrival time between packets");
    getParentModule()->par("inter_arrival_time_between_packets").setStringValue(s);

    s = get_parameter(data_file,"Inter arrival time between flowlets");
    getParentModule()->par("inter_arrival_time_between_flowlets").setStringValue(s);

    s = get_parameter(data_file,"Inter arrival time between flows");
    getParentModule()->par("inter_arrival_time_between_flows").setStringValue(s);

    s = get_parameter(data_file,"Large flow");
    getParentModule()->par("large_flow").setStringValue(s);

}

void Controller::initialization_start_time_for_flows(){
    int NumOfToRs = getParentModule()->par("NumOfToRs").intValue();
    int number_of_hosts =  getParentModule()->getSubmodule("rack",0)->par("number_of_hosts").intValue();


    long double flow_appearance = 0,last_flow = 0;
    long double inter_arrival_time_between_flows = stold(getParentModule()->par("inter_arrival_time_between_flows").stdstringValue());

    string s;



    for(int i = 0;i < NumOfToRs;i++){
        int initial_number_of_flows = 0;//632;
        for(int j = 0;j < number_of_hosts;j++){
            if(initial_number_of_flows <= 0){
                flow_appearance = last_flow + exponential(inter_arrival_time_between_flows);
                last_flow = flow_appearance;
            }
            else {
                initial_number_of_flows--;
            }


            s =  my_to_string(flow_appearance);
            getParentModule()->getSubmodule("rack",i)->getSubmodule("host",j)->par("flow_appearance").setStringValue(s); //set flow_appearance in host j in rack i


            //s = to_string(draw_flow_size()); //change
            //getParentModule()->getSubmodule("rack",i)->getSubmodule("host",j)->par("flow_size").setStringValue(s); //set flow_size in host j in rack i
        }
        last_flow = 0;
        flow_appearance = 0;
    }
}








void Controller::partition_calculation(Data_for_partition* msg){

}

void Controller::update_miss_forwarding(){

}

void Controller::finish()
{
    // This function is called by OMNeT++ at the end of the simulation.
    EV << "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" << endl;
    EV << "Total arrived packets in the Controller:   " << byte_counter << endl;
    EV << "Time in the Controller:   " << simTime() << endl;
    EV << "Average throughput in the Controller:   " << (float)(byte_counter / simTime()) << endl;
    EV << "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" << endl;

    delete[] partition;

    recordScalar("INTERVAL: ", INTERVAL);
    bandwidth_hist.recordAs("Total_bandwidth_hist");
}


}; // namespace
