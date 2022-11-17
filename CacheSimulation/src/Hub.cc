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

#ifndef __CACHESIMULATION_TCX_H
#define __CACHESIMULATION_TCX_H

#include <omnetpp.h>
#include "messages_m.h"
#include "Definitions.h"

#include <map>

using namespace omnetpp;

namespace cachesimulation {

/**
 * Implements the Txc simple module. See the NED file for more information.
 */
class Hub : public cSimpleModule
{
private:
    cQueue msg_queue;
    unsigned long long int byte_count = 0;
    unsigned long long int window_byte_count = 0;
    unsigned long long int flowlet_count_size = 0;
    cOutVector flowlet_count;
    cHistogram bandwidth_hist;
    cHistogram bandwidth_hist_per_sec;
    simtime_t end_time = 0;
    cHistogram flow_count_hist;
    std::map<string, int> flow_count;
    std::map<string, int> flow_count_total;
  protected:
    virtual void initialize();
    virtual void handleMessage(cMessage *msg);
    virtual void my_send(cMessage *msg);
    virtual void finish();
};

}; // namespace

#endif

#include <map>


namespace cachesimulation {

Define_Module(Hub);

void Hub::initialize()
{
    flow_count_hist.setName("flow count");
    bandwidth_hist.setName("bandwidth hist");
    bandwidth_hist_per_sec.setName("bandwidth_hist_per_sec");

    cMessage *m = new cMessage("flow_count");
    m->setKind(FLOW_COUNT_M);
    scheduleAt(simTime() + INTERVAL,m);


    //new Histogram;

    cMessage *hist_msg = new cMessage("hist_msg");
    hist_msg->setKind(HIST_MSG);
    scheduleAt(simTime() + 1,hist_msg);
    //end new histogram

    flowlet_count.setName("flowlet_count");

}

void Hub::handleMessage(cMessage *msg)
{

    //histogram per 1 sec:
    if(msg->getKind() == HIST_MSG){
       string name =  "";
       simtime_t t = simTime(),t1 =  simTime() + 1;
       name =  name + my_to_string(t.dbl()) + "  -  " + my_to_string(t1.dbl());
       bandwidth_hist_per_sec.recordAs(name.c_str());
       bandwidth_hist_per_sec.clear();

       scheduleAt(simTime() + 1,msg);
       return;
    }
    //end histogram per 1 s



    //
    static int x = 0;
    //


    //byte count:
    if(!msg->isSelfMessage()){
        DataPacket *m = check_and_cast<DataPacket *>(msg);
        byte_count += m->getByteLength();
        window_byte_count += m->getByteLength();
        flowlet_count_size += m->getFlow_size();


    }
    //end byte count


    //flow_count
    int kind_of_packet = msg->getKind();
    if( kind_of_packet == DATAPACKET ||  kind_of_packet == HITPACKET){
        DataPacket *pkt = check_and_cast<DataPacket *>(msg);
        flow_count.insert({get_flow(pkt->getId()),1});
        flow_count_total.insert({get_flow(pkt->getId()),1});

        //
        if(pkt->getExternal_destination() == 1001){
            flow_count.erase(get_flow(pkt->getId()));
            delete pkt;
            x++;
            return;
        }
        //
    }
    if(msg->getKind() == FLOW_COUNT_M){
        flow_count_hist.collect(flow_count.size() + x);
        EV << "flow_count: "<< flow_count.size() << endl;
        //flow_count.clear();
        x = 0;
        scheduleAt(simTime() + INTERVAL,msg);



        bandwidth_hist.collect((long double)(window_byte_count*8)/(long double)(INTERVAL*1000000000.0));
        bandwidth_hist_per_sec.collect((long double)(window_byte_count*8)/(long double)(INTERVAL*1000000000.0));
        window_byte_count = 0;


        flowlet_count.record((long double)(flowlet_count_size*8)/(INTERVAL));
        flowlet_count_size = 0;


        return;
    }
    //end flow count


    //regular send:
    send(msg, "port$o", 0);
    return;

    //Queueing:
    if(msg->getKind() != HUB_QUEUE_MSG){// packet from host
        my_send(msg);
    }
    else {//schedule packet from queue
        if(msg_queue.isEmpty())return;
        cMessage *pkt = (cMessage *)msg_queue.pop();
        //my_send(pkt);
        send(pkt, "port$o",0);
        if(msg)delete msg;
        return;
    }
}

void Hub::my_send(cMessage *msg){


    //test:
    EV << "size of the queue: " << msg_queue.getLength() << endl;
    //end test
    cChannel *txChannel = gate("port$o",0)->getTransmissionChannel();
    simtime_t txFinishTime = txChannel->getTransmissionFinishTime();
    //if (txFinishTime <= simTime())
    if(end_time <= simTime())
    {
    // channel free; send out packet immediately
       send(msg, "port$o",0);
       end_time = simTime() + txChannel->calculateDuration(msg);
    }
    else
    {
    // store packet and schedule timer; when the timer expires,
    // the packet should be removed from the queue and sent out

       cMessage *q_msg = new cMessage("Queue_msg");
       q_msg->setKind(HUB_QUEUE_MSG);//Kind of Queue message
       scheduleAt(end_time, q_msg);
       end_time += txChannel->calculateDuration(msg);
       msg_queue.insert(msg);
    }
}

void Hub::finish(){
    EV << "Bandwidth in Hub: "<< (long double)(byte_count*8)/simTime().dbl()<< "bps"<< endl;
    EV << "queue size: " <<  msg_queue.getLength() << endl;

    flow_count_hist.recordAs("flow count");
    bandwidth_hist.recordAs("bandwidth hist");

    recordScalar("scalar: Total number of flows in the simulation:", flow_count_total.size());
    EV << " Total number of flows in the simulation : " << flow_count_total.size() << endl;

}
}; // namespace
