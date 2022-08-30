#include <omnetpp.h>
#include "Definitions.h"


uint64_t ip_to_int( std::string s){
    uint64_t result = 0;
    std::string delimiter = ".";

    size_t pos = 0;
    std::string token;
    while ((pos = s.find(delimiter)) != std::string::npos) {
        token = s.substr(0, pos);
        result = (result << 8) | std::stoi(token);
        s.erase(0, pos + delimiter.length());
    }
    result = (result << 8) | std::stoi(s);
    return result;
}

std::string int_to_ip(uint64_t n){
    std::string oct1 = std::to_string((n >> 24) & (0xFF));
    std::string oct2 = std::to_string((n >> 16) & (0xFF));
    std::string oct3 = std::to_string((n >> 8) & (0xFF));
    std::string oct4 = std::to_string((n) & (0xFF));
    std::string result = oct1 + "." + oct2 + "." +oct3 + "." +oct4;
    return result;
}


std::string get_flow(const std::string& str)
{
  std::size_t found = str.find_last_of(".");
  return str.substr(0,found);
}

long long int get_sequence(const std::string& str)
{
  std::size_t found = str.find_last_of(".");
  return std::stoll(str.substr(found+1));
}

std::string create_id(int x,int y,int z){
    std::string s = "";
    return s + std::to_string(x) + "." + std::to_string(y) + "." + std::to_string(z);
}


/*
 *
 *
#include <arpa/inet.h>


int ip_to_int(const char* s){
    return inet_addr(s);
}

char* int_to_ip(int n){
    struct in_addr in;
    in.s_addr = n;
    return inet_ntoa(in);
}
 */
