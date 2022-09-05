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
#include <fstream>
#include <string>
#include "messages_m.h"
#include "Definitions.h"

using namespace std;
using namespace omnetpp;

namespace cachesimulation {

/**
 * Implements the Txc simple module. See the NED file for more information.
 */
class Rack : public cSimpleModule
{
private:
    int id;
    vector<vector<string>> data_file;
    vector<vector<string>> size_distribution_file;
  protected:
    virtual void initialize();
    virtual void handleMessage(cMessage *msg);
    virtual uint64_t draw_flow_size();
    virtual void read_data_file();
    //virtual void set_parameters();
    virtual string get_parameter(vector<vector<string>> content,string key);
    virtual void create_traffic();
    virtual void enter_the_traffic_into_the_system();
};

}; // namespace

#endif
