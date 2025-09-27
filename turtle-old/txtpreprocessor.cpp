
#include "txtpreprocessor.h"
#include <string>
#include <iostream>
#include <fstream>

txtpreproc::txtpreproc(std::string fpath)
{
    std::string     line ="";
    std::ifstream   file("sample.cfg");
    if (file.is_open())
    {
        while ( std::getline(file, line) )
            std::cout << line << '\n';
        file.close();
    } else
    {
        std::cout << "Unable to open the file! " << std::endl;
    }

}

