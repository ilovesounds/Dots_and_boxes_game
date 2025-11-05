#include <iostream>
#include <istream>
#include <vector>
#include <map>
#include <random>
#include <utility>
#include <lib/board.h>
#include <lib/utils.h>

Board::Board(int r, int c, int seed, int numLinesTaken) : rows(r), cols(c) {
    mt19937 gen(seed);

    horizontalLines.resize(rows, vector<int>(cols - 1, 0));
    verticalLines.resize(rows - 1, vector<int>(cols, 0));

    int numHorizontalLines = gen() % (numLinesTaken + 1);
    int numVerticalLines = numLinesTaken - numHorizontalLines;
    for (int i = 0; i < numHorizontalLines; ++i) {
        int row = gen() % rows;
        int col = gen() % (cols - 1);
        if (horizontalLines[row][col])
            i--;
        else
            horizontalLines[row][col] = 1;
    }
    for (int i = 0; i < numVerticalLines; ++i) {
        int row = gen() % (rows - 1);
        int col = gen() % cols;
        if (verticalLines[row][col])
            i--;
        else
            verticalLines[row][col] = 1;
    }

    gridOwner.resize(
        rows - 1,
        vector<GridOwner>(cols - 1,
                          GridOwner::UNSPECIFIED)); // 0 indicates no owner
    int numGridsTaken = 0;
    for (int i = 0; i < rows - 1; ++i) {
        for (int j = 0; j < cols - 1; ++j) {
            if (horizontalLines[i][j] == 1 && horizontalLines[i + 1][j] == 1 &&
                verticalLines[i][j] == 1 && verticalLines[i][j + 1] == 1) {
                gridOwner[i][j] = GridOwner::PRE_FILLED;
                numGridsTaken++;
            }
        }
    }

    numEmptyGrids = (rows - 1) * (cols - 1) - numGridsTaken;
    numHorizontalLinesLeft = (rows * (cols - 1)) - numHorizontalLines;
    numVerticalLinesLeft = ((rows - 1) * cols) - numVerticalLines;
    scores.clear();
}

Board::Board(int r, int c, vector<vector<int>> hLines,
             vector<vector<int>> vLines, vector<vector<GridOwner>> gOwner)
    : rows(r), cols(c), horizontalLines(hLines), verticalLines(vLines),
      gridOwner(gOwner) {
    cerr << "Initializing Board with given lines and owner." << endl;
    numEmptyGrids = 0;
    numHorizontalLinesLeft = 0;
    numVerticalLinesLeft = 0;
    scores.clear();
    for (int i = 0; i < rows - 1; ++i) {
        for (int j = 0; j < cols - 1; ++j) {
            cerr << "Grid (" << i << ", " << j
                 << ") owned by: " << gOwner[i][j] << endl;
            if (gridOwner[i][j] == GridOwner::UNSPECIFIED) {
                cerr << "Grid (" << i << ", " << j << ") is empty." << endl;
                numEmptyGrids++;
            }
        }
    }
    for (int i = 0; i < rows; ++i) {
        for (int j = 0; j < cols - 1; ++j) {
            if (horizontalLines[i][j] == 0) {
                numHorizontalLinesLeft++;
            }
        }
    }
    for (int i = 0; i < rows - 1; ++i) {
        for (int j = 0; j < cols; ++j) {
            if (verticalLines[i][j] == 0) {
                numVerticalLinesLeft++;
            }
        }
    }
}

bool Board::isValidMove(Move move) const {
    if (move.isHorizontal) {
        if (move.row < 0 || move.row >= rows || move.col < 0 ||
            move.col >= cols - 1)
            return false;
        return horizontalLines[move.row][move.col] ==
               0; // Check if the line is not already drawn
    } else {
        if (move.row < 0 || move.row >= rows - 1 || move.col < 0 ||
            move.col >= cols)
            return false;
        return verticalLines[move.row][move.col] ==
               0; // Check if the line is not already drawn
    }
}

bool Board::requiresContinuation(Move move) const {
    return !isCompletingMove(move) && isCapturingMove(move);
}

bool Board::isCompletingMove(Move move) const {
    return (numHorizontalLinesLeft + numVerticalLinesLeft) ==
           1; // Presumes move is valid
}

bool Board::isCapturingMove(Move move) const {
    return !getCapturingGrids(*this, move).empty();
}

bool Board::makeMove(Move move, PlayerSide moveSide) {
    bool isCapturing;
    bool isCompleting = isCompletingMove(move);

    // mark the grid as owned by the player if capturing
    for (auto [gridRow, gridCol] : getCapturingGrids(*this, move)) {
        gridOwner[gridRow][gridCol] = moveSide == PlayerSide::FIRST_PLAYER
                                          ? GridOwner::FIRST_PLAYER
                                          : GridOwner::SECOND_PLAYER;
        isCapturing = true;
        numEmptyGrids--;
        scores[moveSide]++;
    }

    // Mark the line as drawn

    if (move.isHorizontal) {
        horizontalLines[move.row][move.col] =
            1; // Mark the horizontal line as drawn
        numHorizontalLinesLeft--;
    } else {
        verticalLines[move.row][move.col] =
            1; // Mark the vertical line as drawn
        numVerticalLinesLeft--;
    }
    return isCapturing && !isCompleting;
}

bool Board::isCompleted() const { return numEmptyGrids == 0; }

const map<PlayerSide, int> &Board::getScores() const { return scores; }

vector<Move> Board::getValidMoves() const {
    vector<Move> validMoves;
    for (int r = 0; r < rows; ++r) {
        for (int c = 0; c < cols - 1; ++c) {
            if (horizontalLines[r][c] ==
                0) // If the horizontal line is not drawn
            {
                validMoves.emplace_back(r, c, true);
            }
        }
    }
    for (int r = 0; r < rows - 1; ++r) {
        for (int c = 0; c < cols; ++c) {
            if (verticalLines[r][c] == 0) // If the vertical line is not drawn
            {
                validMoves.emplace_back(r, c, false);
            }
        }
    }
    return validMoves;
}

ostream &operator<<(std::ostream &os, const Board &board) {
    os << board.rows << " " << board.cols << endl;
    for (const auto &row : board.horizontalLines) {
        for (int line : row) {
            os << line << " ";
        }
        os << endl;
    }
    for (const auto &row : board.verticalLines) {
        for (int line : row) {
            os << line << " ";
        }
        os << endl;
    }
    for (const auto &row : board.gridOwner) {
        for (GridOwner owner : row) {
            os << owner << " ";
        }
        os << endl;
    }
    return os;
}

istream &operator>>(std::istream &is, Board &board) {
    is >> board.rows >> board.cols;
    board.horizontalLines.resize(board.rows, vector<int>(board.cols - 1));
    board.verticalLines.resize(board.rows - 1, vector<int>(board.cols));
    board.gridOwner.resize(
        board.rows - 1,
        vector<GridOwner>(board.cols - 1, GridOwner::UNSPECIFIED));
    board.numEmptyGrids = 0;
    board.numHorizontalLinesLeft = 0;
    board.numVerticalLinesLeft = 0;
    board.scores.clear();
    for (int i = 0; i < board.rows; ++i) {
        for (int j = 0; j < board.cols - 1; ++j) {
            is >> board.horizontalLines[i][j];
            if (board.horizontalLines[i][j] == 0) {
                board.numHorizontalLinesLeft++;
            }
        }
    }
    for (int i = 0; i < board.rows - 1; ++i) {
        for (int j = 0; j < board.cols; ++j) {
            is >> board.verticalLines[i][j];
            if (board.verticalLines[i][j] == 0) {
                board.numVerticalLinesLeft++;
            }
        }
    }
    for (int i = 0; i < board.rows - 1; ++i) {
        for (int j = 0; j < board.cols - 1; ++j) {
            is >> board.gridOwner[i][j];
            switch (board.gridOwner[i][j]) {
            case GridOwner::UNSPECIFIED:
                board.numEmptyGrids++;
                break;
            case GridOwner::FIRST_PLAYER:
                board.scores[PlayerSide::FIRST_PLAYER]++;
                break;
            case GridOwner::SECOND_PLAYER:
                board.scores[PlayerSide::SECOND_PLAYER]++;
                break;
            case GridOwner::PRE_FILLED:
                // don nothing:
                break;
            }
        }
    }
    return is;
}
std::istream &operator>>(istream &is, PlayerSide &ps) {
    is >> (int &)ps;
    return is;
}

std::ostream &operator<<(ostream &os, const PlayerSide &ps) {
    os << (int)ps;
    return os;
}

std::istream &operator>>(istream &is, GridOwner &go) {
    is >> (int &)go;
    return is;
}

std::ostream &operator<<(ostream &os, const GridOwner &go) {
    os << (int)go;
    return os;
}

