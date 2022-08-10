//Traffic Generator:
#define USE_TRAFFIC_GENERATOR 1 //Put 1 to use traffic generator and 0 to generate traffic with OMNET random functions


//Messages Type:
#define GENERATEPACKET 1
#define DATAPACKET 2
#define INSERTRULE 3

//Hardware
#define POLICYSIZE 10000
#define RACKRATE 0.1 //Necessary if the traffic generator is not used

//General:
#define NOTFOUND 2 //MISS
#define FOUND 1 //HIT
#define THRESHOLDCROSS 21


//Json file:
#define PATH "traces/packet_trace"  // The path suffix (".json") is added in the code


//Switches Type: Fixed i.e Do not change
#define TOR 1001
#define AGGREGATION 1002
#define CONTROLLERSWITCH 1003
