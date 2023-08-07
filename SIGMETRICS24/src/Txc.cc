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



#include "Txc.h"

using namespace std;


namespace sigmetrics24 {

Define_Module(Txc);

void Txc::initialize()
{
    //measure time:
        //take the start time of the simulation:
    std::chrono::time_point<std::chrono::steady_clock> start;
    start = std::chrono::steady_clock::now();

    //strart:
    if (par("sendInitialMessage").boolValue()){return;}



    cout << "Hello world" << endl;

    //parameters:
    alpha = getParentModule()->par("alpha").doubleValue();

    uint64_t traffic_length = 0;


    //Read the traffic:
    //std::ifstream file("RR.csv");

    for(int i = 0;i < 1; i++){
        //std::string path = "C:/omnetpp-5.6.1/samples/CacheSimulation/simulations/";
         //path = path + "traffic" + to_string(i) + ".csv";

        std::string path = "";
        path = path + "Traffic " + getParentModule()->par("prob_App_A").stdstringValue() + " for App A.csv";

        std::ifstream file(path);
        if (file) {
            std::string line;
            while (std::getline(file, line)) {
                std::stringstream ss(line);
                std::vector<uint64_t> row;
                uint64_t value;
                while (ss >> value) {
                    row.push_back(value);
                    if (ss.peek() == ',')
                        ss.ignore();
                }
                traffic[i].push_back(row);
            }
            file.close();
        } else {
            std::cout << "Error opening file" << std::endl;
        }
    }


    for(int i = 0;i < NUM_OF_ToRs ; i++){
        traffic_size[i] = traffic[i].size();
    }

    //Measure the simulation duration:
    // Record the end time
    auto end1 = std::chrono::steady_clock::now();

    // Calculate the duration in seconds
    auto duration_time1 = std::chrono::duration_cast<std::chrono::seconds>(end1 - start).count();
    std::cout << "Finish to read traffic.  Took  " << (duration_time1/60.0) << " minutes" << std::endl;

    //End of read the traffic




    k_agg =  getParentModule()->par("k_agg").intValue();
    int k_ToR =  getParentModule()->par("k_ToR").intValue();
    for(int i = 0;i < NUM_OF_ToRs;i++)k[i] = k_ToR;



    int alg = getParentModule()->par("algorithm").intValue();
    switch(alg){
    case 1://Naive:
    {

        double p = 1 - (double)(k_agg)/(double)(NUM_OF_ToRs * k[0]);//probability to insert to ToRs
        for (const auto& row : traffic[0]) {//Start run on traffic
            r = (uint64_t)row[0];
            j = (int)row[1];
            if(j > NUM_OF_ToRs - 1)continue;
            //j=0;
            //r=t;

            //cout << r << "  ,  " << j << endl;
            total_miss_cost += miss_cost_at_time_t();

            if(!agg.count(r) and !tor[j].count(r)){ //if it is not in both caches:
                if(uniform(0,1) <= p){//insert to ToR
                    insert_rule_to("ToR");
                }
                else{//insert to Agg:
                    insert_rule_to("Agg");
                }
                total_insertion_cost += alpha;
            }
            t++;
            //if(t >= 700)break;
        }//End run on traffic
        break;
    }//End Naive:
    case 2://vanilla:
    {
        std::map<uint64_t, uint32_t> lambda[NUM_OF_ToRs];
        std::map<uint64_t, uint32_t> k_largest_rule[NUM_OF_ToRs];

        uint64_t sum_on_total_lambda[NUM_OF_ToRs] = {0};
        uint64_t sum_on_k_largest[NUM_OF_ToRs] = {0};
        uint64_t tail_sum;

        for (const auto& row : traffic[0]) {//Start run on traffic
            r = (uint64_t)row[0];
            j = (int)row[1];
            if(j > NUM_OF_ToRs - 1)continue;
            //j=1;
            //cout << r << "  ,  " << j << endl;
            //cout << agg[r] <<  "   ,   "  << tor[j][r] << endl;
            total_miss_cost += miss_cost_at_time_t();



            if(tor[j].count(r) == 0){
                lambda[j][r] = lambda[j][r] + 1;
                //cout << "gggg  "  <<  lambda[j][r]  <<  endl;
                sum_on_total_lambda[j]++;
                //tail sum:
                if(k_largest_rule[j].size() == k[j]){
                    if(k_largest_rule[j].count(r) > 0){//if the rule is one of the k max
                        k_largest_rule[j][r] = lambda[j][r];
                        sum_on_k_largest[j]++;
                    }
                    else{
                        uint64_t r_min;
                        uint64_t min = -1;

                        //find min_rule in k_largest_rule:
                        for (const auto& rule : k_largest_rule[j]){//Find LRU
                            if(rule.second < min){
                                min = rule.second;
                                r_min = rule.first;
                            }
                        }
                        if(lambda[j][r] > lambda[j][r_min]){//swap between r and r_min
                            k_largest_rule[j].erase(r_min); // evict r_min
                            k_largest_rule[j][r] = lambda[j][r];
                            //sum_on_k_largest = sum_on_k_largest - lambda[j][r_min] + lambda[j][r];
                            sum_on_k_largest[j]++;
                        }
                    }
                }
                else{
                    k_largest_rule[j][r] = lambda[j][r];
                    sum_on_k_largest[j]++;
                }



                tail_sum = sum_on_total_lambda[j] - sum_on_k_largest[j];
                //End tail sum
                //if(tail_sum < alpha)cout << "t = "  <<  t  << "  tail_sum = "  <<  tail_sum  <<  "  sum_on_total_lambda = "  <<  sum_on_total_lambda  << "  sum_on_k_largest  =  "  << sum_on_k_largest << endl;



                if(tail_sum >= alpha){//Flush;
                    for(int j_tag = 0;j_tag < NUM_OF_ToRs;j_tag++){
                        lambda[j_tag].clear();
                        k_largest_rule[j_tag].clear();
                        sum_on_total_lambda[j_tag] = 0;
                        sum_on_k_largest[j_tag] = 0;
                        tor[j_tag].clear();
                    }
                    agg.clear();
                }//End Flush
                else{
                    //cout << "aaaaa  "  << lambda[j][r]  << endl;
                    if(lambda[j][r] >= alpha){
                        //cout << tor[j][r] << endl;
                        insert_rule_to("ToR");
                        //cout << tor[j][r] << endl;
                        //cout << endl;
                        total_insertion_cost += alpha;
                    }
                }
            }

            t++;
            //if(t >= 5000)break;
        }//End run on traffic
        break;
    }//End vaniala
    case 3://Improved vanilla LRU:
    {
        std::map<uint64_t, uint32_t> lambda[NUM_OF_ToRs];
        std::map<uint64_t, uint32_t> k_largest_rule[NUM_OF_ToRs];

        uint64_t sum_on_total_lambda[NUM_OF_ToRs] = {0};
        uint64_t sum_on_k_largest[NUM_OF_ToRs] = {0};
        uint64_t tail_sum;

        for (const auto& row : traffic[0]) {//Start run on traffic
            r = (uint64_t)row[0];
            j = (int)row[1];
            if(j > NUM_OF_ToRs - 1)continue;
            //j=1;
            //cout << r << "  ,  " << j << endl;
            //cout << agg[r] <<  "   ,   "  << tor[j][r] << endl;
            total_miss_cost += miss_cost_at_time_t();



            if(tor[j].count(r) == 0){
                lambda[j][r] = lambda[j][r] + 1;
                //cout << "gggg  "  <<  lambda[j][r]  <<  endl;
                sum_on_total_lambda[j]++;
                //tail sum:
                if(k_largest_rule[j].size() == k[j]){
                    if(k_largest_rule[j].count(r) > 0){//if the rule is one of the k max
                        k_largest_rule[j][r] = lambda[j][r];
                        sum_on_k_largest[j]++;
                    }
                    else{
                        uint64_t r_min;
                        uint64_t min = -1;

                        //find min_rule in k_largest_rule:
                        for (const auto& rule : k_largest_rule[j]){//Find LRU
                            if(rule.second < min){
                                min = rule.second;
                                r_min = rule.first;
                            }
                        }
                        if(lambda[j][r] > lambda[j][r_min]){//swap between r and r_min
                            k_largest_rule[j].erase(r_min); // evict r_min
                            k_largest_rule[j][r] = lambda[j][r];
                            //sum_on_k_largest = sum_on_k_largest - lambda[j][r_min] + lambda[j][r];
                            sum_on_k_largest[j]++;
                        }
                    }
                }
                else{
                    k_largest_rule[j][r] = lambda[j][r];
                    sum_on_k_largest[j]++;
                }



                tail_sum = sum_on_total_lambda[j] - sum_on_k_largest[j];
                //End tail sum
                //if(tail_sum < alpha)cout << "t = "  <<  t  << "  tail_sum = "  <<  tail_sum  <<  "  sum_on_total_lambda = "  <<  sum_on_total_lambda  << "  sum_on_k_largest  =  "  << sum_on_k_largest << endl;



                if(tail_sum >= alpha){//Flush;
                    for(int j_tag = 0;j_tag < NUM_OF_ToRs;j_tag++){
                        lambda[j_tag].clear();
                        k_largest_rule[j_tag].clear();
                        sum_on_total_lambda[j_tag] = 0;
                        sum_on_k_largest[j_tag] = 0;
                    }
                }//End Flush
                else{
                    //cout << "aaaaa  "  << lambda[j][r]  << endl;
                    if(lambda[j][r] >= alpha){
                        insert_rule_to("ToR");
                        total_insertion_cost += alpha;
                    }
                }
            }

            t++;
            //if(t >= 5000)break;
        }//End run on traffic
        break;
    }//End Improved vanilla LRU
    case 4://Improved vanilla Agg:
    {
        std::map<uint64_t, uint32_t> lambda[NUM_OF_ToRs];
        std::map<uint64_t, uint32_t> k_largest_rule[NUM_OF_ToRs];

        uint64_t sum_on_total_lambda[NUM_OF_ToRs] = {0};
        uint64_t sum_on_k_largest[NUM_OF_ToRs] = {0};
        uint64_t tail_sum;

        for (const auto& row : traffic[0]) {//Start run on traffic
            r = (uint64_t)row[0];
            j = (int)row[1];
            if(j > NUM_OF_ToRs - 1)continue;
            //cout << r << "  ,  " << j << endl;
            //cout << agg[r] <<  "   ,   "  << tor[j][r] << endl;
            total_miss_cost += miss_cost_at_time_t();



            if(tor[j].count(r) == 0){
                lambda[j][r] = lambda[j][r] + 1;
                //cout << "gggg  "  <<  lambda[j][r]  <<  endl;
                sum_on_total_lambda[j]++;
                //tail sum:
                if(k_largest_rule[j].size() == k[j]){
                    if(k_largest_rule[j].count(r) > 0){//if the rule is one of the k max
                        k_largest_rule[j][r] = lambda[j][r];
                        sum_on_k_largest[j]++;
                    }
                    else{
                        uint64_t r_min;
                        uint64_t min = -1;

                        //find min_rule in k_largest_rule:
                        for (const auto& rule : k_largest_rule[j]){//Find LRU
                            if(rule.second < min){
                                min = rule.second;
                                r_min = rule.first;
                            }
                        }
                        if(lambda[j][r] > lambda[j][r_min]){//swap between r and r_min
                            k_largest_rule[j].erase(r_min); // evict r_min
                            k_largest_rule[j][r] = lambda[j][r];
                            //sum_on_k_largest = sum_on_k_largest - lambda[j][r_min] + lambda[j][r];
                            sum_on_k_largest[j]++;
                        }
                    }
                }
                else{
                    k_largest_rule[j][r] = lambda[j][r];
                    sum_on_k_largest[j]++;
                }



                tail_sum = sum_on_total_lambda[j] - sum_on_k_largest[j];
                //End tail sum
                //if(tail_sum < alpha)cout << "t = "  <<  t  << "  tail_sum = "  <<  tail_sum  <<  "  sum_on_total_lambda = "  <<  sum_on_total_lambda  << "  sum_on_k_largest  =  "  << sum_on_k_largest << endl;



                if(tail_sum >= alpha){//Flush;
                    for(int j_tag = 0;j_tag < NUM_OF_ToRs;j_tag++){
                        lambda[j_tag].clear();
                        k_largest_rule[j_tag].clear();
                        sum_on_total_lambda[j_tag] = 0;
                        sum_on_k_largest[j_tag] = 0;
                        tor[j_tag].clear();
                    }
                    agg.clear();
                }//End Flush
                else{
                    //cout << "aaaaa  "  << lambda[j][r]  << endl;
                    if(lambda[j][r] >= alpha){
                        insert_rule_to("ToR");
                        total_insertion_cost += alpha;
                    }
                    //if(r == 1161)cout << "bbbbb  "  << tor[j][r]  << endl;
                    else{
                        if(agg.count(r) == 0){ // if the rule is not in the aggregation:
                            uint64_t local_sum = 0;
                            for(int j_tag = 0;j_tag < NUM_OF_ToRs;j_tag++){
                                local_sum += (!(tor[j_tag].count(r)))*lambda[j_tag][r];
                            }
                            //local_sum = 0;
                            if(local_sum >= 1*alpha){
                                insert_rule_to("Agg");
                                total_insertion_cost += alpha;
                            }
                        }

                    }
                }
            }

            t++;
            //if(t >= 5000)break;
        }//End run on traffic
        break;
    }//End Improved vanilla Agg:
    case 5://Improved vanilla LRU Agg:
    {
        std::map<uint64_t, uint32_t> lambda[NUM_OF_ToRs];
        std::map<uint64_t, uint32_t> k_largest_rule[NUM_OF_ToRs];

        uint64_t sum_on_total_lambda[NUM_OF_ToRs] = {0};
        uint64_t sum_on_k_largest[NUM_OF_ToRs] = {0};
        uint64_t tail_sum;

        for (const auto& row : traffic[0]) {//Start run on traffic
            r = (uint64_t)row[0];
            j = (int)row[1];
            if(j > NUM_OF_ToRs - 1)continue;
            //j=1;
            //cout << r << "  ,  " << j << endl;
            //cout << agg[r] <<  "   ,   "  << tor[j][r] << endl;
            total_miss_cost += miss_cost_at_time_t();



            if(tor[j].count(r) == 0){
                lambda[j][r] = lambda[j][r] + 1;
                //cout << "gggg  "  <<  lambda[j][r]  <<  endl;
                sum_on_total_lambda[j]++;
                //tail sum:
                if(k_largest_rule[j].size() == k[j]){
                    if(k_largest_rule[j].count(r) > 0){//if the rule is one of the k max
                        k_largest_rule[j][r] = lambda[j][r];
                        sum_on_k_largest[j]++;
                    }
                    else{
                        uint64_t r_min;
                        uint64_t min = -1;

                        //find min_rule in k_largest_rule:
                        for (const auto& rule : k_largest_rule[j]){//Find LRU
                            if(rule.second < min){
                                min = rule.second;
                                r_min = rule.first;
                            }
                        }
                        if(lambda[j][r] > lambda[j][r_min]){//swap between r and r_min
                            k_largest_rule[j].erase(r_min); // evict r_min
                            k_largest_rule[j][r] = lambda[j][r];
                            //sum_on_k_largest = sum_on_k_largest - lambda[j][r_min] + lambda[j][r];
                            sum_on_k_largest[j]++;
                        }
                    }
                }
                else{
                    k_largest_rule[j][r] = lambda[j][r];
                    sum_on_k_largest[j]++;
                }



                tail_sum = sum_on_total_lambda[j] - sum_on_k_largest[j];
                //End tail sum



                if(tail_sum >= 200*alpha){//Flush;
                    for(int j_tag = 0;j_tag < NUM_OF_ToRs;j_tag++){
                        lambda[j_tag].clear();
                        k_largest_rule[j_tag].clear();
                        sum_on_total_lambda[j_tag] = 0;
                        sum_on_k_largest[j_tag] = 0;
                    }
                }//End Flush
                else{
                    //cout << "aaaaa  "  << lambda[j][r]  << endl;
                    if(lambda[j][r] >= alpha){
                        //cout << tor[j][r] << endl;
                        insert_rule_to("ToR");
                        //cout << tor[j][r] << endl;
                        //cout << endl;
                        total_insertion_cost += alpha;
                    }
                    //if(r == 1161)cout << "bbbbb  "  << tor[j][r]  << endl;
                    else{
                        if(agg.count(r) == 0){ // if the rule is not in the aggregation:
                            uint64_t local_sum = 0;
                            for(int j_tag = 0;j_tag < NUM_OF_ToRs;j_tag++){
                                local_sum += (!(tor[j_tag].count(r)))*lambda[j_tag][r];
                            }
                            //local_sum = 0;
                            if(local_sum >= 1*alpha){
                                insert_rule_to("Agg");
                                total_insertion_cost += alpha;
                            }
                        }

                    }
                }
            }

            t++;
            //if(t >= 5000)break;
        }//End run on traffic
        break;
    }//End Improved vanilla LRU Agg:

    }//End Switch

    cout <<  "&&&&&&&&&&&&&&&&&&&&&&&"  <<  endl;

    cout << "total cost of Alg(" << alg <<") with alpha = " << alpha <<" is:\ntotal miss cost = "<< total_miss_cost <<
            "\ntotal insertion cost = "  <<  total_insertion_cost  <<
            "\ntotal cost = "  << total_miss_cost + total_insertion_cost  <<endl;

    recordScalar("total_miss_cost: ",total_miss_cost);
    recordScalar("total_insertion_cost: ",total_insertion_cost);
    recordScalar("total_cost: ",total_miss_cost + total_insertion_cost);

    recordScalar("Hit_ratio_ToR: ",(long double)(num_Hit_ToR)/(long double)(t));
    recordScalar("Hit_ratio_Agg: ",(long double)(num_Hit_Agg)/(long double)(total_traffic_Agg));
    recordScalar("Hit_ratio_Agg_from_all_traffic: ",(long double)(num_Hit_Agg)/(long double)(t));

    recordScalar("insertion_rate: ",total_insertion_cost/alpha);

    cout <<  "Hit_ratio_ToR = "  <<  (long double)(num_Hit_ToR)/(long double)(t)  << endl;
    cout <<  "Hit_ratio_Agg = "  <<  (long double)(num_Hit_Agg)/(long double)(total_traffic_Agg)  << endl;
    cout <<  "insertion_rate = "  <<  total_insertion_cost/alpha  << endl;


    //Measure the simulation duration:
    // Record the end time
    auto end = std::chrono::steady_clock::now();

    // Calculate the duration in seconds
    auto duration_time = std::chrono::duration_cast<std::chrono::seconds>(end - start).count();

    cout << "Simulation took " << (duration_time/60.0) << " minutes" << endl;
    recordScalar("Simulation duration (in minutes). By chrono library: ",(duration_time/60.0));

    cout << "tor size = "  <<  tor[0].size() <<  "   num_Hit_ToR = "  <<  num_Hit_ToR<< endl;

    cout <<  "&&&&&&&&&&&&&&&&&&&&&&&"  <<  endl;
}

void Txc::handleMessage(cMessage *msg)
{

}

void Txc::insert_rule_to(string where_to_insert){

    uint64_t evicted_rule_key;
    uint64_t min = -1;

    if(where_to_insert == "Agg"){//insert to Agg
        if(agg_cache_size == k_agg){//Evict By LRU
                for (const auto& rule : agg){//Find LRU
                    if(rule.second < min){
                        min = rule.second;
                        evicted_rule_key = rule.first;
                    }
                }
                agg.erase(evicted_rule_key); // evict the rule
                agg_cache_size--;
            }

            agg[r] = t;//insert the rule
            agg_cache_size++;
    }
    if(where_to_insert == "ToR"){//insert to Agg
        if(tor_cache_size[j] >= k[j]){//Evict By LRU
                for (const auto& rule : tor[j]){//Find LRU
                    if(rule.second < min and rule.second > 0){
                        min = rule.second;
                        evicted_rule_key = rule.first;
                    }
                }
                //cout << "r = "  <<r << "  j = "  <<  j <<"  evicted_rule_key = " <<evicted_rule_key <<"   tor[j][evicted_rule_key] = "  << tor[j][evicted_rule_key]  <<  endl;
                //cout <<  "size = "  <<  tor[j].size()  << endl;
                tor[j].erase(evicted_rule_key); // evict the rule
                //cout <<  "size = "  <<  tor[j].size()  << endl;
                //cout << "tor[j][evicted_rule_key] = "  << tor[j][evicted_rule_key]  << endl << endl;
                tor_cache_size[j]--;
            }

            tor[j][r] = t;//insert the rule
            tor_cache_size[j]++;
    }
}

bool Txc::get_packet(uint64_t* r,int* j){
    double min = 9999999;
    uint64_t r_min;
    int j_min;

    for(int i = 0;i < NUM_OF_ToRs; i++){
        if(index_of_file[i] < traffic_size[i]){
            if(traffic[i][index_of_file[i]][2] < min){
                min = traffic[i][index_of_file[i]][2];
                r_min = traffic[i][index_of_file[i]][0];
                j_min = traffic[i][index_of_file[i]][1];
            }
        }

    }

    if(min == 9999999){
        return false;
    }
    *r = r_min;
    *j = j_min;
    return true;
}


long double Txc::miss_cost_at_time_t(){
    //also update LRU
    if(tor[j].count(r) > 0){
        tor[j][r] = t;
        num_Hit_ToR++;
        return cost_model[0];
    }
    total_traffic_Agg++;
    if(agg.count(r) > 0){
        agg[r] = t;
        num_Hit_Agg++;
        return cost_model[1];
    }
    return cost_model[2];
}

}; // namespace
