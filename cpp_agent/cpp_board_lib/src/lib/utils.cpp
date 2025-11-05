#include "lib/utils.h"
#include <vector>

bool isCapturingAbove(const Board &board, const Move &move)
{
    if (move.row > 0 && move.isHorizontal)
    {
        return board.verticalLines[move.row - 1][move.col] != 0 &&
               board.verticalLines[move.row - 1][move.col + 1] != 0 &&
               board.horizontalLines[move.row - 1][move.col] != 0;
    }
    return false;
}

bool isCapturingBelow(const Board &board, const Move &move)
{
    if (move.row < board.rows - 1 && move.isHorizontal)
    {
        return board.verticalLines[move.row][move.col] != 0 &&
               board.verticalLines[move.row][move.col + 1] != 0 &&
               board.horizontalLines[move.row + 1][move.col] != 0;
    }
    return false;
}

bool isCapturingLeft(const Board &board, const Move &move)
{
    if (move.col > 0 && !move.isHorizontal)
    {
        return board.horizontalLines[move.row][move.col - 1] != 0 &&
               board.horizontalLines[move.row + 1][move.col - 1] != 0 &&
               board.verticalLines[move.row][move.col - 1] != 0;
    }
    return false;
}

bool isCapturingRight(const Board &board, const Move &move)
{
    if (move.col < board.cols - 1 && !move.isHorizontal)
    {
        return board.horizontalLines[move.row][move.col] != 0 &&
               board.horizontalLines[move.row + 1][move.col] != 0 &&
               board.verticalLines[move.row][move.col + 1] != 0;
    }
    return false;
}

vector<pair<int, int>> getCapturingGrids(const Board &board, const Move &move)
{
    vector<pair<int, int>> capturingGrids;
    if (isCapturingAbove(board, move))
        capturingGrids.emplace_back(move.row - 1, move.col);
    if (isCapturingBelow(board, move))
        capturingGrids.emplace_back(move.row, move.col);
    if (isCapturingLeft(board, move))
        capturingGrids.emplace_back(move.row, move.col - 1);
    if (isCapturingRight(board, move))
        capturingGrids.emplace_back(move.row, move.col);
    return capturingGrids;
}