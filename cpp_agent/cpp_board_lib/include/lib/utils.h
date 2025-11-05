#pragma once

#include <vector>
#include <utility>
#include "move.h"
#include "board.h"

using namespace std;

bool isCapturingAbove(const Board &board, const Move &move);
bool isCapturingBelow(const Board &board, const Move &move);
bool isCapturingLeft(const Board &board, const Move &move);
bool isCapturingRight(const Board &board, const Move &move);

vector<pair<int, int>> getCapturingGrids(const Board &board, const Move &move);
