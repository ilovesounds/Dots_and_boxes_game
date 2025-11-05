#pragma once

#include "controller.h"
#include <utility>
#include <memory>


using namespace std;

class Agent {

  public:
    Agent(std::unique_ptr<Controller> controller) {
        this->controller = std::move(controller);
    }

    Controller &getController() { return *controller; }

    void init();

    void run();

  private:
    std::unique_ptr<Controller> controller;
};
