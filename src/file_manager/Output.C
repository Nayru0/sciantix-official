//////////////////////////////////////////////////////////////////////////////////////
//       _______.  ______  __       ___      .__   __. .___________. __  ___   ___  //
//      /       | /      ||  |     /   \     |  \ |  | |           ||  | \  \ /  /  //
//     |   (----`|  ,----'|  |    /  ^  \    |   \|  | `---|  |----`|  |  \  V  /   //
//      \   \    |  |     |  |   /  /_\  \   |  . `  |     |  |     |  |   >   <    //
//  .----)   |   |  `----.|  |  /  _____  \  |  |\   |     |  |     |  |  /  .  \   //
//  |_______/     \______||__| /__/     \__\ |__| \__|     |__|     |__| /__/ \__\  //
//                                                                                  //
//  Originally developed by D. Pizzocri & T. Barani                                 //
//                                                                                  //
//  Version: 2.2.1                                                                  //
//  Year: 2026                                                                      //
//  Authors: D. Pizzocri, G. Zullo.                                                 //
//                                                                                  //
//////////////////////////////////////////////////////////////////////////////////////

#include <sys/stat.h>
#include "Simulation.h"
#include <nlohmann/json.hpp>

/**
 * @brief Function to check if a file exists.
 * @return 0/1
 * @author G. Zullo
 */
inline bool if_exist(const std::string& name)
{
    struct stat buffer;
    return (stat(name.c_str(), &buffer) == 0);
}

std::string indspaces(int ident)
{
    return std::string(ident * 2, ' ');
}

std::string formatName(const std::string& input)
{
    std::string result = input;
    for (char& c : result)
    {
        if (c == ' ')
            c = '-';
        else
            c = std::tolower(c);
    }
    return result;
}
std::string getLastDirectory(const std::string& path)
{
    std::filesystem::path p(path);
    if (p.filename().empty())
        p = p.parent_path();
    return p.filename().string();
}
std::string removeParentheses(const std::string& unit)
{
    if (unit.size() >= 2 && unit.front() == '(' && unit.back() == ')')
        return unit.substr(1, unit.size() - 2);

    return unit;
}

// This function outputs the simulation results to a JSON file and an overview text file.
// OutdatedOuput.c is the original version of thi function, writing txt files instead of JSON files. It is kept for reference and comparison purposes.
void Simulation::output()
{
    bool isLast = false;
    int i = 0;
    std::string variableID;
    std::string  output_name = TestPath + "output.json";
    std::fstream output_file;
    output_file.open(output_name, std::fstream::in | std::fstream::out | std::fstream::app); 

    // iOutput == 1 --> output.json
    if (int(input_variable["iOutput"].getValue()) == 1)
    {
        if (history_variable["Time step number"].getFinalValue() == 0)
        {
            //Initialize the JSON object with the metadata
            data.clear();
            data["format_version"] = "0.1.0";
            data["schema"] = "../metadata/schema/output.schema.json";
            data["case_id"] = getLastDirectory(TestPath);
            data["generated_at_utc"] = "Null";
            data["dcterms_sources"] = {"../metadata/sources/white2004.jsonld", "../metadata/sources/ifpe_cagr_uox_swell.jsonld"};
            data["table"]["columns"] = nlohmann::ordered_json::array();
            data["table"]["rows"] = nlohmann::ordered_json::array();

            for (auto& variable : history_variable)
            {
                if (variable.getOutput()){
                    variableID = "sciantix-variable:history_variable:" + formatName(variable.getName());
                    data["table"]["columns"].push_back({
                        {"index", i},
                        {"name", variable.getName() + " " + variable.getUOM()},
                        {"label", variable.getName()},
                        {"unit", removeParentheses(variable.getUOM())},
                        {"unitURI", catalogVariables[variableID]["unitURI"]},
                        {"catalogVariable", variableID}
                    });
                    i++;
                }
            }
            for (auto& variable : sciantix_variable)
            {
                if (variable.getOutput()){
                    variableID = "sciantix-variable:state_variable:" + formatName(variable.getName());
                    data["table"]["columns"].push_back({
                        {"index", i},
                        {"name", variable.getName() + " " + variable.getUOM()},
                        {"label", variable.getName()},
                        {"unit", removeParentheses(variable.getUOM())},
                        {"unitURI", catalogVariables[variableID]["unitURI"]},
                        {"catalogVariable", variableID}
                    });
                    i++;
                }
            }
        }

        isLast = (Time_h >= Time_end_h);
        if ((int)history_variable["Time step number"].getFinalValue() % 1 == 0)
        {
            data["table"]["rows"].push_back(nlohmann::ordered_json::array());

            for (auto& variable : history_variable)
            {
                if (variable.getOutput()){
                    data["table"]["rows"].back().push_back(variable.getFinalValue());
                }
            }

            for (auto& variable : sciantix_variable)
            {
                if (variable.getOutput()){
                    data["table"]["rows"].back().push_back(variable.getFinalValue());
                }
            }
        }
        if (isLast)
        {
            output_file << data.dump(2) << std::endl;
        }
    }

    // iOutput = 2 prints the complete output.exe file
    // else if ((int)input_variable["iOutput"].getValue() == 2)
    // {
    //     if (history_variable["Time step number"].getFinalValue() == 0)
    //     {
    //         for (auto& variable : history_variable)
    //         {
    //             output_file << variable.getName() << " " << variable.getUOM() << "\t";
    //         }
    //         for (auto& variable : sciantix_variable)
    //         {
    //             output_file << variable.getName() << " " << variable.getUOM() << "\t";
    //         }
    //         output_file << "\n";
    //     }

    //     if ((int)history_variable["Time step number"].getFinalValue() % 1 == 0)
    //     {
    //         for (auto& variable : history_variable)
    //         {
    //             output_file << std::setprecision(10) << variable.getFinalValue() << "\t";
    //         }

    //         for (auto& variable : sciantix_variable)
    //         {
    //             output_file << std::setprecision(7) << variable.getFinalValue() << "\t";
    //         }
    //         output_file << "\n";
    //     }
    // }

    output_file.close();

    std::string overview_name = TestPath + "overview.txt";

    if (history_variable["Time step number"].getFinalValue() == 0 && if_exist(overview_name))
        remove(overview_name.c_str());  // from string to const char*

    std::fstream overview_file;
    if (history_variable["Time step number"].getFinalValue() == 0 && !if_exist(overview_name))
    {
        overview_file.open(overview_name, std::fstream::in | std::fstream::out | std::fstream::app);

        for (auto& model_ : model)
        {
            overview_file << "Model" << "\t";
            overview_file << model_.getName() << "\t";
            overview_file << model_.getRef() << "\n";
        }

        overview_file << "\n";

        for (auto& matrix_ : matrices)
        {
            overview_file << "Matrix" << "\t";
            overview_file << matrix_.getName() << "\t";
            overview_file << matrix_.getRef() << "\n";
        }

        overview_file << "\n";

        for (auto& system : sciantix_system)
        {
            overview_file << "System" << "\t";
            overview_file << system.getName() << "\t";
            overview_file << system.getRef() << "\n";
        }

        overview_file << "\n";

        for (auto& input_variable_ : input_variable)
        {
            overview_file << "Input setting" << "\t";
            overview_file << input_variable_.getName() << " = ";
            overview_file << input_variable_.getValue() << "\n";
        }

        overview_file << "\n";
    }
    overview_file.close();
}
