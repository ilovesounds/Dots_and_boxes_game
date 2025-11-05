#include <controller.h>
#include <vector>
#include <iostream>

int Controller::getTimeMs() {
    if (!useProtocol) {
        // In snapshot/server mode, time is not managed here; return a sentinel like -1
        return -1;
    }
    cout << "!REQ_TIME\n";
    cout.flush();
    int time;
    cin >> time;
    return time;
}

bool Controller::makeMove(const Move &move) {
    outstandingMoves.push_back(move);

    if (board.requiresContinuation(move)) {  // this(requirescontinuation cause requiresContinuation assumes the move to be valid, this case it would be duplicate) should have been used before making the move
        board.makeMove(move, getMySide());
        return true;
    }
    board.makeMove(move, getMySide());
    if (useProtocol) {
    flushOutlyingMoves();
        if (!board.isCompleted()) {
            vector<Move> moves = getOpponentMoves();
            for (auto &move : moves) {
                board.makeMove(move, getOpponentSide());
            }
        }
    } else {
        // In snapshot/server mode, we do not talk to engine; the caller is responsible
        // for applying opponent moves externally if needed.
        outstandingMoves.clear();
    }
    return false;
}

void Controller::flushOutlyingMoves() {
    cout << "!SENDING_MOVES\n";
    cout << outstandingMoves.size() << "\n";
    for (const Move &move : outstandingMoves) {
        cout << move << "\n";
    }
    cout.flush();
    
    outstandingMoves.clear();
    arePreviousMovesCached = false;
}

bool Controller::makeMove(const vector<Move> &moves) {
    bool requriesMoreMoves = false;
    for (auto &move : moves) {
        requriesMoreMoves = makeMove(move);
    }
    return requriesMoreMoves;
}

vector<Move>& Controller::getOpponentMoves() {
    if(!useProtocol || arePreviousMovesCached) return previousOpponentMoves;

    cout << "!REQ_MOVES\n";
    cout.flush();
    int numMoves;
    cin >> numMoves;
    previousOpponentMoves.clear();

    for (int i = 0; i < numMoves; ++i) {
        Move move;
        cin >> move;
        previousOpponentMoves.push_back(move);
    }

    // for (auto &move : moves) {
    //     board.makeMove(move, getOpponentSide());
    // }

    arePreviousMovesCached = true;
    return previousOpponentMoves;
}
