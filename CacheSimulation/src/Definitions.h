#include <fstream>
#include <string>
#include <stdlib.h>     /* atoi */


using namespace omnetpp;
using namespace std;

//Hardware
//#define POLICYSIZE 10000




//Delays:
#define MICROSECOND 0.000001


#define INTERVAL 1280*MICROSECOND
#define NUM_OF_APPS 2.0
#define START_TIME 3.0
#define TIME_INTERVAL_FOR_OUTPUTS 0.5
//#define PROCESSING_TIME_ON_DATA_PACKET_IN_SW 0.1*MICROSECOND
//#define INSERTION_DELAY 2*MICROSECOND
//#define EVICTION_DELAY 2*MICROSECOND


//Evictions of rules:
//#define CACHE_PERCENTAGE 0.8
//#define SAMPLE_SIZE 5 //The number of rules you sample and from will be evicted according to LRU
//#define RANDOM 1   //set 1 for random eviction or 0 for power of two choices


//Elephant Detector
/*
#define ELEPHANT_TABLE_SIZE 50
#define FLUSH_ELEPHANT_TIME 100*MICROSECOND
#define CHECK_FOR_ELEPHANT_TIME 10*MICROSECOND
#define ELEPHANT_SAMPLE_RX 1 //Every few packets we will sample a packet in RX
#define BANDWIDTH_ELEPHANT_THRESHOLD 1
#define ALREADY_REQUESTED_THRESHOLD 0.0001




//Traffic Generator:
//#define USE_TRAFFIC_GENERATOR 1 //Put 1 to use traffic generator and 0 to generate traffic with OMNET random functions
#define INTER_ARRIVAL_TIME_BETWEEN_PACKETS 7.5*MICROSECOND //change
#define INTER_ARRIVAL_TIME_BETWEEN_FLOWLETS 7.5*MICROSECOND //change


*/




//Partition:
#define PARTITION_RATE 0.05 //The rate at which the partition will be made



//Json file:
#define PATH "traces/packet_trace"  // The path suffix (".json") is added in the code
//#define PATH_DISTRIBUTION "size_distribution/FB_Hadoop_Inter_Rack_FlowCDF.csv"
//#define PATH_DISTRIBUTION "size_distribution/i-websearch.csv"
#define PATH_DATA "data/data.csv"




//Messages Type: (Must be different!!)
#define GENERATEPACKET 1
#define DATAPACKET 2
#define INSERTRULE_PUSH 3
#define INSERTRULE_PULL 4
#define HITPACKET 5
#define RULE_REQUEST 6
#define DATA_FOR_PARTITION 7
#define FLUSH_ELEPHANT_PKT 8
#define CHECK_FOR_ELEPHANT_PKT 9
#define INSERTION_DELAY_PCK 10
#define EVICTION_DELAY_PCK 11
#define HUB_QUEUE_MSG 12
#define HIST_MSG 13
#define INTERVAL_PCK 14
#define LZY_EVICT 15
#define RECORD_OR_CREATE_TRAFFIC_PCK 16
#define BOUNDS_IN_HOSTS_PCK 17
#define ESTIMATE_RATE_PCK 18
#define GENERAL_INSERTRULE 19




//General:
#define NOTFOUND 2 //MISS
#define FOUND 1 //HIT
#define THRESHOLDCROSS 21




//Switches Type: Fixed i.e Do not change
#define TOR 1001
#define AGGREGATION 1002
#define CONTROLLERSWITCH 1003




//Structs:
//Struct of a rule in the cache
typedef struct{
    unsigned long int count;  //count the packets that the rule managed to catch
    unsigned long long int bit_count; // count the bits that the rule managed to catch
    std::vector<simtime_t> first_packet;   //Intended for estimate the rate for each port-destination flow
    simtime_t last_time;   //Intended for calculation for LRU eviction
    simtime_t insertion_time;
    std::vector<double> port_dest_count;  //Intended for estimate the rate for each port-destination flow
    uint64_t rule_diversity = 0;
}ruleStruct;

//Elephant struct
typedef struct{
    unsigned long int count;
    unsigned long int byte_count; //necessary?
    simtime_t last_time;
    simtime_t first_appearance;
    int flow_size;
    long double rate;
}elephant_struct;

//Struct of partition rule for the miss table:
typedef struct{
    uint64_t low; //low limit
    uint64_t high; //high limit
    uint64_t range_size; //The size of the address range that the rule covers
    int port; //egress port
}partition_rule;

//The controller will store the following data in the rules database:
typedef struct{
    //bool from_single_sources = false; //store if the rule is from single source, false is also the initially state
    //int source;
    int count[20] = {0};
    bool diversity[20] = {false};
}controller_rule;



//General Functions:
uint64_t ip_to_int( std::string s); // Convert a string ip to number
std::string int_to_ip(uint64_t n);  // Convert a number to string ip
std::string create_id(uint64_t x,uint64_t y,uint64_t z); //Creates an id of type string "x.y.z"

std::string get_flow(const std::string& str);
long long int get_sequence(const std::string& str);
string get_parameter(vector<vector<string>> content,string key);
vector<vector<string>> read_data_file(string fname);
string my_to_string(long double x); // convert long double to string with precision level of 20 digits
int rate_to_bin(long double rate);
int sign(double x);
std::string mysplitstring(std::string str,std::string delimiter,int position_of_word);
void convert_xl_to_csv();
int count_one(uint64_t x);
int type_of_switch_to_index(int type); //returns the index of the switch according to type.ToR = 0, Agg = 1, conswitch = 2
int index_of_switch_to_type(int type); //returns the type of the switch according to index.


