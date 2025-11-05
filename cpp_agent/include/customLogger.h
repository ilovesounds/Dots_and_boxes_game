#pragma once

#include <iostream>

template<typename T>
void Log(const T& x) {
    std::cerr << x << std::endl;
}