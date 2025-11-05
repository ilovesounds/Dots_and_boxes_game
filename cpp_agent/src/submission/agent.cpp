#include "agent.h"
#include "customLogger.h"
#include <cstdlib>
#include <ctime>
#include <iostream>
#include <utility>

void Agent::init() { srand(time(NULL)); }

// Picks one random move, applies it via Controller, returns {requiresContinuation, move}
std::pair<bool, Move> makeMove(Controller &controller) {
    Log("Hi from makeMove function");
    Log(controller.getTimeMs());
    
    Board board = controller.getCurrentBoard();
    auto validMoves = board.getValidMoves();
    if (validMoves.empty()) {
        return {false, Move{0,0,true}}; // no moves to play
    }
    const Move &m = validMoves[rand() % validMoves.size()];
    bool cont = controller.makeMove(m);
    // log my move
    string logMessage = "Agent made move: " + to_string(m.row) + " " + to_string(m.col) + " " + to_string(m.isHorizontal);
    Log(logMessage);
    return {cont, m};
}

void Agent::run() {
    //play until the board is full or no moves remain.
    while (!controller->getCurrentBoard().isCompleted()) {
        while (true) {
            auto [requiresMoreMoves, move] = makeMove(*controller);
            if (!requiresMoreMoves || controller->getCurrentBoard().isCompleted()) break;
        }
        if (controller->getCurrentBoard().isCompleted()) {
            break;
        }
    }
}
