#pragma once

#include "lib/move.h"
#include <lib/board.h>
#include <vector>
#include <iostream>

class Controller {
    Board board;
    vector<Move> outstandingMoves;
    PlayerSide playerSide;
    bool useProtocol = true; // when false, do not emit !REQ_* or read stdin (server/test mode)
    bool arePreviousMovesCached = true;
    vector<Move> previousOpponentMoves{};

  public:
    Controller() {
        cout << "!REQ_PLAYER_NUM\n";
        cout.flush();
        cin >> playerSide;

        cout << "!REQ_BOARD\n";
        cout.flush();
        cin >> board;
    }

    Controller(const Board &snapshot, PlayerSide side, bool useProtocol = false)
        : board(snapshot), playerSide(side), useProtocol(useProtocol) {}

    /**
     * Returns true if you needs to make more moves
     */
    bool makeMove(const Move &move);

    /**
     * Returns true if you needs to make more moves
     */
    bool makeMove(const vector<Move> &moves);

    /**
     * Returns the current state of the board
     */
    const Board &getCurrentBoard() { return board; }

    PlayerSide getMySide() { return playerSide; }

    PlayerSide getOpponentSide() {
        return playerSide == PlayerSide::FIRST_PLAYER
                   ? PlayerSide::SECOND_PLAYER
                   : PlayerSide::FIRST_PLAYER;
    }

    int getTimeMs();

    /**
     * Returns the set of moves made by opponent in the last move
     */
    vector<Move> &getOpponentMoves();

  private:
    void flushOutlyingMoves();
};
