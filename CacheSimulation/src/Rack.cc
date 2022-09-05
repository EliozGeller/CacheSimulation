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






#include <stdlib.h>     /* atoi */
#include "Rack.h"





namespace cachesimulation {

Define_Module(Rack);

void Rack::initialize()
{
    id = getIndex();
    read_data_file();
    EV << get_parameter(data_file,"Avarage flow size")<< endl;


    if((int)getParentModule()->par("Do_generate_traffic") == 1)
        create_traffic();

    //start the simulation:

    enter_the_traffic_into_the_system();
    //cMessage *m = new cMessage;
    //m->setKind(GENERATEPACKET);
    //scheduleAt(0,m);

}

void Rack::handleMessage(cMessage *message)
{
    switch(message->getKind()){
        case GENERATEPACKET:
        {
            enter_the_traffic_into_the_system();
            break;
        }
        case DATAPACKET:
        {
            send(message, "port$o", 0);
            break;
        }
    }

}

void Rack::read_data_file(){
    string fname = "data/data.csv";

    vector<string> row;
    string line, word;


    //Read the data file:
    fstream file;
    file.open(fname, ios::in);
    if(file.is_open())
    {
        while(getline(file, line))
        {
            row.clear();

            stringstream str(line);

            while(getline(str, word, ','))
                row.push_back(word);
            data_file.push_back(row);
        }
    }
    else
        cout<<"Could not open the file\n";
    file.close();



    //Read the distribution file:
    fname = "size_distribution/datamining.csv";
    file.open(fname, ios::in);
    if(file.is_open())
    {
       while(getline(file, line))
       {
           row.clear();

           stringstream str(line);

           while(getline(str, word, ','))
               row.push_back(word);
           size_distribution_file.push_back(row);
       }
    }
    else
       cout<<"Could not open the file\n";
    file.close();
}

string Rack::get_parameter(vector<vector<string>> content,string key){
    for(int i = 0;i < content.size();i++){
        if(content[i][0] == key)return content[i][4];
    }
}



void Rack::create_traffic(){
    int number_of_flowlets;
    uint64_t destination,flow_size,flow_num,flow_id;

    long long int flowlet_size;

    simtime_t time,flow_appearance,last_flow = 0;

    simtime_t inter_arrival_time_between_flows = (simtime_t)stold(get_parameter(data_file,"Inter arrival time between flows")); //change,not large enopgh
    simtime_t inter_arrival_time_between_flowlets = (simtime_t)stold(get_parameter(data_file,"Inter arrival time between flowlets")); //change,not large enopgh
    simtime_t inter_arrival_time_between_packets = (simtime_t)stold(get_parameter(data_file,"Inter arrival time between packets")); //change,not large enopgh
    EV << "inter_arrival_time_between_flows"<<inter_arrival_time_between_flows<< endl;

    int packet_size = stoi(get_parameter(data_file,"packet size"));

    uint64_t number_of_flows = stoull(get_parameter(data_file,"number of flows"));
    uint64_t large_flow_threshold = stoull(get_parameter(data_file,"Large flow"));

    //file
    string trace_file = "";
    trace_file = trace_file + "traces/trace" + to_string(id) + ".csv";
    fstream fout;
    fout.open(trace_file,ios::out | ios::trunc);


    for(flow_num = 0;flow_num < number_of_flows;flow_num++){
        flow_id = id * number_of_flows + flow_num;
        flow_size = draw_flow_size();
        flow_appearance = last_flow + exponential(inter_arrival_time_between_flows);
        last_flow = flow_appearance;
        time = flow_appearance;
        destination = (uint64_t)uniform(0,POLICYSIZE); //change

        if(flow_size > large_flow_threshold){
            number_of_flowlets = 10;
        }
        else {
            number_of_flowlets = 1;
        }




        //transmit flow:
        for(int flowlet_count = 0;flowlet_count < number_of_flowlets;flowlet_count++){
            flowlet_size = flow_size/number_of_flowlets;
            uint64_t count = 0;
            while(flowlet_size > 0){
                //send packet:
                int src = id;
                string pck_id = create_id(flow_id,flowlet_count,count);

                if((int)getParentModule()->par("generate_online_traffic") == 0){
                    fout<< src << "," << destination << "," << packet_size << "," << time << "," << pck_id << std::endl;
                }
                if((int)getParentModule()->par("generate_online_traffic") == 1){
                    DataPacket *msg = new DataPacket("Data Packet");
                    msg->setKind(DATAPACKET);

                    // uint64_t src = stoull(row[0]); //need?

                    msg->setDestination(destination);

                    msg->setByteLength(packet_size);

                    simtime_t arrival_time = (simtime_t)time;

                    msg->setId(pck_id.c_str());

                    scheduleAt(arrival_time,msg);
                }




                //packet structure:
                // (src,dst,size,time,id)


                count++;
                flowlet_size -= packet_size;
                time = time + exponential(inter_arrival_time_between_packets);
            }
            time = time + exponential(inter_arrival_time_between_flowlets);
        }
    }
    fout.close();

}

void Rack::enter_the_traffic_into_the_system(){
    uint64_t count = 0;
    string trace_file = "";
    trace_file = trace_file + "traces/trace" + to_string(id) + ".csv";
    string word,line;
    vector<string> row;

    fstream file;
    DataPacket *msg;


    file.open(trace_file, ios::in);
    if(file.is_open())
    {
        while(getline(file, line))
        {

            if(count >= 10000)break;
            row.clear();

            stringstream str(line);

            while(getline(str, word, ','))
                row.push_back(word);
            //create a packet and scheduleAt it:
            //packet structure:
                // (src,dst,size,time,id)
            msg = new DataPacket("Data Packet");
            msg->setKind(DATAPACKET);

            // uint64_t src = stoull(row[0]); //need?

            uint64_t destination = stoull(row[1]);
            msg->setDestination(destination);

            int size = stoi(row[2]);
            msg->setByteLength(size);

            simtime_t arrival_time = (simtime_t)stold(row[3]);

            std::string pck_id =  row[4];
            msg->setId(pck_id.c_str());

            //sendDelayed(msg, arrival_time, "port$o", 0);
            scheduleAt(arrival_time,msg);
            //end creation of packet
            count++;
        }
    }
    else
        cout<<"Could not open the file\n";
    file.close();
    EV << "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" << endl;
    EV << "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" << endl;
    EV << "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" << endl;

    EV << "end of create events" << endl;

    EV << "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" << endl;
    EV << "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" << endl;
    EV << "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" << endl;
}

uint64_t Rack::draw_flow_size(){
    /*
     * Here there is an option to check each row whether it is float or not,
     *  but right now it is just searching starting from the second row
     */
    float x = uniform(0,1);
    for(int i = 1 /*start from the second row*/;i < size_distribution_file.size();i++){ //
        if(x < stold(size_distribution_file[i][1])){
            return (uint64_t)stoull(size_distribution_file[i][0]);
        }
    }
}
}; // namespace
