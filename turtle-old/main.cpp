#include <iostream>
#include <fstream>
#include <string>

// separate classes for lexer, file handling, preprocessor
// TODO: parse out the empty lines and comments

int main()
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
    return 0;
}
