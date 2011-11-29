#include <iostream>

#include "teststatic/funcstatic.h"
#include "testshared/funcshared.h"
#include <mili/mili.h>

int main(int /*argc*/, char* /*argv*/[]) {
    std::cout << "Hola Mundo!!!" << std::endl;
    funcstatic();
    funcshared();
    return 0;
}
