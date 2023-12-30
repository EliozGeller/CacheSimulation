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




#include "Destination.h"
#include "Definitions.h"

#include <iostream>
#include <fstream>
using namespace std;



namespace cachesimulation {

Define_Module(Destination);

void Destination::initialize()
{


    //take the start time of the simulation:
    start = std::chrono::steady_clock::now();

    //set names of histograms:
    miss_count.setName("miss count");
    out_of_order.setName("out of order");
    miss_count_by_apps.setName("miss_count_by_apps");



    //set the byte count in the destination:
    byte_counter = 0;


    ////start the process of the the intervals for outputs:
    bandwidth_hist.setName("bandwidth hist");
    cMessage *hist_msg = new cMessage("hist_msg");
    hist_msg->setKind(HIST_MSG);
    scheduleAt(simTime() + START_TIME + TIME_INTERVAL_FOR_OUTPUTS,hist_msg);


    //start the process of the the intervals:
    cMessage *m = new cMessage("flow_count");
    m->setKind(INTERVAL_PCK);
    scheduleAt(simTime() + START_TIME + INTERVAL,m);
    //end new histogram

    //set the directory for the txt files outputs:
    dir = getParentModule()->par("output_file").stdstringValue();


    //record simulation parameters:
    recordScalar("run_elephant: ",getParentModule()->par("run_elephant").boolValue());
    recordScalar("run_push: ",getParentModule()->par("run_push").boolValue());
    recordScalar("cache_size: ",stoi(getParentModule()->par("cache_size").stdstringValue()));
    recordScalar("scale: ",getParentModule()->par("scale").doubleValue());
    recordScalar("total_rate_in_tor: ",stold(getParentModule()->par("total_rate_in_tor").stdstringValue())/(getParentModule()->par("scale").doubleValue()));

}

void Destination::handleMessage(cMessage *message)
{
    switch(message->getKind()){
    case HITPACKET:
    case DATAPACKET:
    {
        DataPacket *msg = check_and_cast<DataPacket *>(message);
        byte_counter += msg->getByteLength();


        //statistics for miss count
        miss_count.collect(msg->getMiss_hop());
        miss_count_by_apps.collect(msg->getMiss_hop() + ( msg->getApp_type() / NUM_OF_APPS));
        //cout << "x = " << msg->getMiss_hop() + ( msg->getApp_type() / NUM_OF_APPS) << endl;

        //statistics for out of order
        out_of_order_statistics(msg);


        //miss_count_map:
        unsigned int flow_size = msg->getFlow_size();
        int rate =  rate_to_bin(msg->getRate());

        EV << "rate = " << rate << "   org = " << msg->getRate()<<endl;

        miss_count_map[std::make_pair(flow_size,rate)] = std::make_pair(miss_count_map[std::make_pair(flow_size,rate)].first + 1,miss_count_map[std::make_pair(flow_size,rate)].second + msg->getMiss_hop());
        //out_of_order_map[std::make_pair(flow_size,rate)] = std::make_pair(out_of_order_map[std::make_pair(flow_size,rate)].first + 1,out_of_order_map[std::make_pair(flow_size,rate)].second + diff);


        delete msg;
        //cancelAndDelete(msg);

        break;
    }
    case INTERVAL_PCK:
    {
       bandwidth_hist.collect((long double)(byte_counter*8)/(long double)(INTERVAL));
       byte_counter = 0;

       scheduleAt(simTime() + INTERVAL,message);
       break;
    }
    case HIST_MSG://histogram per 1 sec:
    {
        //handle bandwidth_hist:
        string name1,name =  "";
        simtime_t t = simTime() - TIME_INTERVAL_FOR_OUTPUTS,t1 =  simTime();
        name =  name + my_to_string(t.dbl()) + "  -  " + my_to_string(t1.dbl());
        name1 = name + ":bandwidth_hist";
        bandwidth_hist.recordAs(name1.c_str());


        //handle miss count/out of order"
        name1 = name + ":miss_count";
        miss_count.recordAs(name1.c_str());
        name1 = name + ":out_of_order";
        out_of_order.recordAs(name1.c_str());

        //print  maps:


        ofstream MyFile(dir + name + ".txt");
        //print miss count:
        MyFile << "#######################################################\nmiss_count_map:{size,rate,count,value}\n{\n";
        for( std::map<std::pair<unsigned int,unsigned long long int>, std::pair<unsigned long long int,unsigned long long int>>::const_iterator it = miss_count_map.begin();
          it != miss_count_map.end(); ++it)
        {
          MyFile << "{" << it->first.first << "," << it->first.second << "," << it->second.first << "," << it->second.second << "},\n";
        }
        MyFile << "}"<< std::endl;

        ////print out of order:
        MyFile << "#######################################################\nout of order:{size,rate,count,value}\n{\n";
        for( std::map<std::pair<unsigned int,unsigned long long int>, std::pair<unsigned long long int,unsigned long long int>>::const_iterator it = out_of_order_map.begin();
          it != out_of_order_map.end(); ++it)
        {
           MyFile << "{" << it->first.first << "," << it->first.second << "," << it->second.first << "," << it->second.second << "},\n";
        }
        MyFile << "}"<< std::endl;
        MyFile.close();

        scheduleAt(simTime() + TIME_INTERVAL_FOR_OUTPUTS,message);
        break;
    }
    }



}

void Destination::out_of_order_statistics(DataPacket* msg)
{
    total_packets++;
    long long int diff = get_sequence(msg->getId()) - expected_sequence[get_flow(msg->getId())];
    if(diff > 0)out_of_order_counter += diff;
    expected_sequence[get_flow(msg->getId())] = get_sequence(msg->getId()) + 1;
}

void Destination::finish()
{
    // This function is called by OMNeT++ at the end of the simulation.
    EV << "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" << endl;
    EV << "Miss count in the Destination, mean:   " << miss_count.getMean() << endl;
    EV << "Total arrived packets in the Destination:   " << byte_counter << endl;
    EV << "simtime =    " << simTime() << endl;
    EV << "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" << endl;

    miss_count.recordAs("miss count");
    out_of_order.recordAs("out of order");
    bandwidth_hist.recordAs("bandwidth to destination");
    miss_count_by_apps.recordAs("miss_count_by_apps");


    recordScalar("Out of order percentage: ", (double)out_of_order_counter / (double)total_packets);






    //print  maps:
   ofstream MyFile(dir + "Total" + ".txt");
   //print miss count:
   MyFile << "#######################################################\nmiss_count_map:{size,rate,count,value}\n{\n";
   for( std::map<std::pair<unsigned int,unsigned long long int>, std::pair<unsigned long long int,unsigned long long int>>::const_iterator it = miss_count_map.begin();
     it != miss_count_map.end(); ++it)
   {
     MyFile << "{" << it->first.first << "," << it->first.second << "," << it->second.first << "," << it->second.second << "},\n";
   }
   MyFile << "}"<< std::endl;

   ////print out of order:
   MyFile << "#######################################################\nout of order:{size,rate,count,value}\n{\n";
   for( std::map<std::pair<unsigned int,unsigned long long int>, std::pair<unsigned long long int,unsigned long long int>>::const_iterator it = out_of_order_map.begin();
     it != out_of_order_map.end(); ++it)
   {
      MyFile << "{" << it->first.first << "," << it->first.second << "," << it->second.first << "," << it->second.second << "},\n";
   }
   MyFile << "}"<< std::endl;
   MyFile.close();


   //Measure the simulation duration:
   // Record the end time
   auto end = std::chrono::steady_clock::now();

   // Calculate the duration in seconds
   auto duration_time = std::chrono::duration_cast<std::chrono::seconds>(end - start).count();

   EV << "Simulation took " << (duration_time/60.0) << " minutes" << endl;
   recordScalar("Simulation duration (in minutes). By chrono library: ",(duration_time/60.0));

}





}; // namespace
