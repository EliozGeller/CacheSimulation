#include <omnetpp.h>
#include "Definitions.h"


int type_of_switch_to_index(int type){
    return (type - 1001); // ToR = 0, Agg = 1, conswitch = 2. Do not change the value of the defines TOR,AGGREGATION,CONTROLLERSWITCH!!!!
}

int index_of_switch_to_type(int type){
    return (type + 1001); // ToR = 1001, Agg = 1002, conswitch = 1003. Do not change the value of the defines TOR,AGGREGATION,CONTROLLERSWITCH!!!!
}



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


std::string get_flowlet(const std::string& id_str)
{
  std::size_t found = id_str.find_last_of(".");
  return id_str.substr(0,found);
}

uint32_t get_flow(const std::string& id_str){
    std::size_t found = id_str.find_first_of(".");
    return std::stoul(id_str.substr(0,found));
}

unsigned long long int get_sequence(const std::string& str)
{
  std::size_t found = str.find_last_of(".");
  return std::stoll(str.substr(found+1));
}

std::string create_id(uint64_t x,uint64_t y,uint64_t z){
    std::string s = "";
    return s + std::to_string(x) + "." + std::to_string(y) + "." + std::to_string(z);
}

string get_parameter(vector<vector<string>> content,string key){
    for(int i = 0;i < content.size();i++){
        if(content[i][0] == key)return content[i][10];
    }
    return "";
}


vector<vector<string>> read_data_file(string fname){
    vector<vector<string>> data_file;

    vector<string> row;
    string line, word;


    //Read the data file:
    fstream file;
    file.open(fname, ios::in);
    if(file.is_open())
    {
        while(getline(file, line))
        {
            row.clear();

            stringstream str(line);

            while(getline(str, word, ','))
                row.push_back(word);
            data_file.push_back(row);
        }
    }
    else
        cout<<"Could not open the file\n";
    file.close();
    return data_file;
}

string my_to_string(long double x){
    stringstream stream;
    // Set precision level to 20
    stream.precision(20);
    stream << fixed;

    // Convert double to string
    stream<<x;
    string str  = stream.str();
    return str;

}


int rate_to_bin(long double rate){
    return (int)((rate)/(100000000.0));
}

int sign(double x){
    return (x >= 0)?(1):(-1);
}

std::string mysplitstring(std::string str,std::string delimiter,int position_of_word){
    std::string result;
    int pos =  0;

    for(int i = 0;i < position_of_word;i++){
        pos = str.find(delimiter,pos + 1);
    }
    int last_pos = str.find(delimiter,pos + 1);

    if(pos == 0)result = str.substr(pos,last_pos-pos);
    else result = str.substr(pos + 1,last_pos-pos - 1);

    return result;

}


void convert_xl_to_csv() {
    // Open the .xlsx file for reading
    ifstream xlsxFile("data/data.xlsx");

    // Open the .csv file for writing
    ofstream csvFile("bbb.csv", std::ios::trunc);

    // Read each line of the .xlsx file
    string line;
    while (getline(xlsxFile, line)) {
        // Split the line into cells using the comma delimiter
        cout << line << endl;
        cout << (line == "") << endl;
        size_t pos = 0;
        string cell;
        while ((pos = line.find(',')) != string::npos) {
            cell = line.substr(0, pos);
            // Write the cell to the .csv file
            csvFile << cell << ",";
            // Remove the cell from the line
            line.erase(0, pos + 1);
        }
        // Write the last cell in the line to the .csv file
        csvFile << line << endl;
    }

    cout<< "rggr" << endl;

    // Close the .xlsx and .csv files
    xlsxFile.close();
    csvFile.close();
}


int count_one(uint64_t x) {
    x = (x & 0x5555555555555555) + ((x >> 1) & 0x5555555555555555);
    x = (x & 0x3333333333333333) + ((x >> 2) & 0x3333333333333333);
    x = (x & 0x0f0f0f0f0f0f0f0f) + ((x >> 4) & 0x0f0f0f0f0f0f0f0f);
    x = (x & 0x00ff00ff00ff00ff) + ((x >> 8) & 0x00ff00ff00ff00ff);
    x = (x & 0x0000ffff0000ffff) + ((x >> 16) & 0x0000ffff0000ffff);
    x = (x & 0x00000000ffffffff) + ((x >> 32) & 0x00000000ffffffff);
    return (int)x;
}
