#include "funcshared.h"
#include "funcstatic.h"

#include <iostream>

int funcshared() {
    std::cout << "funcshared" << std::endl;
    funcstatic();
    return 0;
}
