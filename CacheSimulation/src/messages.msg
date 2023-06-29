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



namespace cachesimulation;

packet DataPacket
{
    uint64_t destination;
    uint64_t external_destination = 0;
    int miss_hop = 0;
    int miss_path[3]; //{ToR,Agg,Controllerswitch}
    uint8_t app_type;
    string id;
    int request = 0; //Indicates whether this is an elephant packet and whether the switch wishes to insert the appropriate rule
    uint64_t flow_size = 0;
    double rate;
    int first_packet = 0;
    bool last_packet = false;
}

packet InsertionPacket
{
    uint64_t rule;
    int type; //Push or Pull //delete
    int switch_type; //ToR,Aggregation or controller switch
    int destination; //The switch id
    int s;
    string insert_to_switch[3];//{ToR,Agg,Controllerswitch}."insert" means to insert the rule into the switch,"remove" means to remove the rule from the switch and "null" is do nothing
    int path[3]; //{ToR,Agg,Controllerswitch}
    bool LRU = true; //Indicates whether to exclude a rule ри LRU or a specific one, if true then it will exclude according to LRU, if false it will remove "rule"
}

packet Data_for_partition
{
    uint64_t counters[100]; //Should be the size of the aggregation number
}

packet Partition_update_msg
{
    uint64_t lows[100]; //Should be the size of the aggregation number
    uint64_t highs[100]; //Should be the size of the aggregation number
    int ports[100]; //Should be the size of the aggregation number
}








