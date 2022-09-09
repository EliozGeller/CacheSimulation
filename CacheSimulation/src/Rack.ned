// Immediately sends out any message it receives. It can optionally generate
// a message at the beginning of the simulation, to bootstrap the process.
//
package cachesimulation;

module Rack
{
    parameters:
        int number_of_hosts;
    gates:
        inout port[];
    submodules:
        hub: Hub {
            @display("p=363,69;i=device/hub");
        }
        host[number_of_hosts]: Host {
            @display("p=363,290,r,50;i=device/pc");
        }
    connections:
        hub.port++ <--> port++;
        for i=0..number_of_hosts-1 {
            host[i].port++ <--> hub.port++;
        }
}
