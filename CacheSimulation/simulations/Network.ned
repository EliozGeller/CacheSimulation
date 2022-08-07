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

import cachesimulation.Rack;
import cachesimulation.Switch;
import cachesimulation.Controller;

//
// Two instances (tic and toc) of Txc connected.
//
network Network
{
    parameters:
        @display("i=block/routing");
        int NumOfToRs;
        int NumOfAggregation;
        @display("bgb=725,450");
    types:
        channel C extends ned.DelayChannel
        {
            delay = 100ms;
        }
    submodules:
        rack[3]: Rack {
            @display("p=363,430,r,50");
        }
        tor[3]: Switch {
            @display("p=363,349,r,50");
        }
        agg[2]: Switch {
            @display("p=363,241,r,50");
        }
        controllerswitch: Switch {
            @display("p=363,146");
        }
        controller: Controller {
            @display("p=363,56");
        }
    connections:
        for i=0..NumOfToRs-1 {
            rack[i].port++ <--> C <--> tor[i].port++;
        }
        controllerswitch.port++ <--> C <--> controller.port++;
        for i=0..NumOfAggregation-1 {
            agg[i].port++ <--> C <--> controllerswitch.port++;
        }
        for i=0..NumOfToRs-1, for j=0..NumOfAggregation-1 {
            tor[i].port++ <--> C <--> agg[j].port++;
        }
}