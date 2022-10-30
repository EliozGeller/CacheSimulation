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

package cachesimulation.simulations;

import cachesimulation.Host;
import cachesimulation.Switch;
import cachesimulation.Controller;
import cachesimulation.Destination;
import cachesimulation.Rack;





network Network
{
    parameters:
        @display("i=block/routing");
        int NumOfToRs;
        int NumOfAggregation;
        double linedelay;
        @display("bgb=725,450");

        //int Do_generate_traffic;
        //int generate_online_traffic;



        //simulation parameters:
        //Hardware:
        string policy_size;
        string cache_size;

        //Delays:
        string propagation_time;
        string processing_time_on_data_packet_in_sw;
        string processing_time_on_data_packet_in_controller;
        string insertion_delay;
        string eviction_delay;
        //Elephant Detector:
        string elephant_table_size;
        string flush_elephant_time;
        string check_for_elephant_time;
        string elephant_sample_rx;
        string bandwidth_elephant_threshold;
        string already_requested_threshold;

        //Push insertion:
        string push_threshold_in_aggregation;
        string push_threshold_in_controller_switch;
        //Eviction:
        string cache_percentage;
        string eviction_sample_size;
        //Traffic:
        string inter_arrival_time_between_packets;
        string inter_arrival_time_between_flowlets;
        string inter_arrival_time_between_flows;
        string large_flow;
        
        //creation of new flow:
        string last_flow_id;
        string last_flow_appearance;


        //end simulation parameters
    types:
        channel delay_ch extends ned.DelayChannel
        {
            delay = 0.1 us; //micros
        }
        
        channel rate_ch extends ned.DatarateChannel
        {
            datarate = 1.6 Tbps;
            delay = 100us;
        }
    submodules:
        controller: Controller {
            @display("p=254,430;i=device/server");
        }
        rack[NumOfToRs]: Rack {
            @display("p=363,430,r,50;i=device/router_l");
        }
        tor[NumOfToRs]: Switch {
            @display("p=363,349,r,50;i=device/switch");
        }
        agg[NumOfAggregation]: Switch {
            @display("p=363,241,r,50;i=device/switch");
        }
        controllerswitch: Switch {
            @display("p=254,349;i=device/switch");
        }
        dest: Destination {
            @display("p=363,130;i=abstract/penguin");
        }
    connections:
        for i=0..NumOfToRs-1 {
            rack[i].port++ <--> rate_ch <--> tor[i].port++;
        }
        controllerswitch.port++ <--> delay_ch <--> controller.port++;
        for i=0..NumOfAggregation-1 {
            agg[i].port++ <--> delay_ch <--> controllerswitch.port++;
        }
        for i=0..NumOfAggregation-1 {
            agg[i].port++ <--> delay_ch <--> dest.port++;
        }
        for i=0..NumOfToRs-1, for j=0..NumOfAggregation-1 {
            tor[i].port++ <--> delay_ch <--> agg[j].port++;
        }
}
