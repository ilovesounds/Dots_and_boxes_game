#pragma once

#include <iostream>
#include <vector>
#include <string>

using namespace std;

struct Move
{
    int row;
    int col;
    bool isHorizontal;

    Move(int r, int c, bool h) : row(r), col(c), isHorizontal(h) {}
    Move() {}

    friend ostream &operator<<(ostream &os, const Move &move)
    {
        os << move.row << " " << move.col << " " << move.isHorizontal;
        return os;
    }
    friend istream &operator>>(istream &is, Move &move)
    {
        is >> move.row >> move.col >> move.isHorizontal;
        return is;
    }
};
