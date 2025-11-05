#pragma once

#include "move.h"
#include <vector>
#include <map>
#include <istream>
#include <ostream>

using namespace std;

enum class PlayerSide : int {  FIRST_PLAYER = 1, SECOND_PLAYER = 2 };
enum class GridOwner : int { UNSPECIFIED = 0,FIRST_PLAYER=1,SECOND_PLAYER=2,PRE_FILLED=3};

istream &operator>>(istream &is, PlayerSide &ps);

ostream &operator<<(ostream &os, const PlayerSide &ps);

istream &operator>>(istream &is, GridOwner &go);

ostream &operator<<(ostream &os, const GridOwner &go);

struct Board {
    int rows;
    int cols;
    int numEmptyGrids;
    int numHorizontalLinesLeft;
    int numVerticalLinesLeft;
    map<PlayerSide, int> scores;
    vector<vector<int>> horizontalLines;
    vector<vector<int>> verticalLines;
    vector<vector<GridOwner>> gridOwner;

    Board() = default;
    Board(int r, int c, int seed, int numLinesTaken = 0);
    Board(int r, int c, vector<vector<int>> hLines, vector<vector<int>> vLines,
          vector<vector<GridOwner>> gOwner);

    bool isValidMove(Move move) const;
    // returns true if move is capturing and not completing
    bool requiresContinuation(Move move) const;
    bool isCompletingMove(Move move) const;
    bool isCapturingMove(Move move) const;
    // Returns true if the move is requires continuation
    bool makeMove(Move move, PlayerSide moveSide);
    bool isCompleted() const;
    const map<PlayerSide, int>& getScores() const;
    vector<Move> getValidMoves() const;
    Board clone() const{
        return *this;
    }
    friend ostream &operator<<(std::ostream &os, const Board &board);
    friend istream &operator>>(std::istream &is, Board &board);
};
