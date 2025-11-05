#include "agent.h"
#include "controller.h"
#include <memory>

using namespace std;

int main(int argc, char *argv[]) {
    Agent agent(std::make_unique<Controller>());
    agent.init();
    agent.run();
    return 0;
}
