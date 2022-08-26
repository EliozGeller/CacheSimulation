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
    string id;
    int request = 0; //Indicates whether this is an elephant packet and whether the switch wishes to insert the appropriate rule
}

packet InsertionPacket
{
    uint64_t rule;
    int type; //Push or Pull //delete
    int switch_type; //ToR,Aggregation or controller switch
    int destination; //The switch id
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








