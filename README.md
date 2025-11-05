# Bot Battles - Dots and Boxes

A competitive Dots and Boxes game framework where you can build AI agents in C++ or Python and battle them against each other through a web interface.

## Prerequisites

- **Python 3.9+** with pip
- **CMake 3.10+** (for C++ agents)
- **C++ compiler** with C++14 support (g++, clang, or MSVC)

## Install Python Dependencies

```bash
pip install fastapi uvicorn pydantic
```

## Launch Game Server

```bash
python3 ui.py
```

The server will start on `http://localhost:8000`. Open this URL in your web browser to access the game interface.

## Available Bots

### Starter Agents
- **python_agent** - Python starter agent (random moves)
- **cpp_agent** - C++ starter agent (random moves)
- **Human** - Play manually through the web interface

### Creating More Agents
The server **automatically recognizes** any new agents you create! Simply:
- Copy an existing agent folder (e.g., `cp -r python_agent python_agent2`)
- The new agent will appear in the dropdown automatically
- You can create as many agents as you want (python_agent2, cpp_agent2, cpp_agent3, etc.)

## How to Play

1. **Start the server:** Run `python3 ui.py`
2. **Open browser:** Navigate to `http://localhost:8000`
3. **Select agents:** Choose Player 1 and Player 2 from the dropdowns
4. **Configure board:** Set board dimensions (rows/cols) and initial random lines
5. **Start game:** Click "Start New Game"
6. **Watch or play:** 
   - If playing as **Human**, click on the board to draw lines
   - If watching **bots**, they will play automatically
7. **View results:** See final scores and time taken for each player

## Project Structure

```
starter-code/
├── ui.py                    # Main game server (DO NOT EDIT)
├── static/                  # Web interface (DO NOT EDIT)
├── python_agent/           # Python starter agent
│   ├── agent.py            # Agent framework
│   ├── board.py            # Board utilities
│   ├── controller.py       # Game controller
│   └── submission/         # EDIT THIS FOLDER
│       └── agent.py        # YOUR IMPLEMENTATION HERE
└── cpp_agent/              # C++ starter agent
    ├── src/
    │   └── submission/     # EDIT THIS FOLDER
    │       └── agent.cpp   # YOUR IMPLEMENTATION HERE
    ├── include/            # Headers (DO NOT EDIT)
    ├── cpp_board_lib/      # Board library (DO NOT EDIT)
    └── CMakeLists.txt      # Build config (DO NOT EDIT)
```

### Important: Submission Guidelines
- **ONLY edit files inside `submission/` folders**
- **Submit ONLY the file from the `submission/` folder**
- Do NOT modify any other files (agent.py, board.py, controller.py, CMakeLists.txt, etc.)
- The server expects the same folder structure

## Game Rules - Dots and Boxes

- Players take turns drawing lines between adjacent dots
- When a player completes a box (all 4 sides):
  - They capture that box and score **+1 point**
  - They get **another turn immediately**
- Game ends when all boxes are captured
- **Player with most boxes wins**

### Move Format
- **Horizontal line:** `row col true`
- **Vertical line:** `row col false`

---

## Building C++ Agents (Optional to test)


```bash
cd cpp_agent/build
cmake ..
cmake --build . --config Release
cd ../..
```


---

## Advanced: Creating Your Own Agent

To create your own agent, edit the `make_move` function (Python) or `makeMove` function (C++) in the appropriate file inside the `submission/` folder:

- **Python:** Edit `python_agent/submission/agent.py`
- **C++:** Edit `cpp_agent/src/submission/agent.cpp`

**Note:** For C++ agents, the UI automatically rebuilds your code when you start a game, so you don't need to manually run build commands!

### Debugging Your Agent

Both Python and C++ agents have access to a logger for debugging:

**Python:**
```python
from custom_logger import logger

def make_move(controller: Controller) -> Tuple[bool, Move]:
    log('Hi from make_move function')
    time_ms = controller.get_time_ms()
    log(f'Time remaining: {time_ms} ms')
    # Your code here
```

**C++:**
```cpp
#include "customLogger.h"

std::pair<bool, Move> makeMove(Controller &controller) {
    Log("Hi from makeMove function");
    Log(controller.getTimeMs());
    // Your code here
}
```

Logger output appears in the terminal where you ran `python3 ui.py`.

### Creating Multiple Bots (Optional)

If you want to create multiple bots, simply duplicate the agent folder:

**Python:**
```bash
cp -r python_agent python_agent2
# Edit python_agent2/submission/agent.py
```

**C++:**
```bash
cp -r cpp_agent cpp_agent2
# Edit cpp_agent2/src/submission/agent.cpp
# remember to delete the build folder in case you copied that as well
```

The server will automatically detect, build (for C++), and list your new agents!

---

## Troubleshooting

### "Agent did not respond" error
- **C++ agents:** Verify the agent is built: `ls cpp_agent/build/agent`
- **Python agents:** Test standalone: `python3 -m python_agent`
- Check for infinite loops or crashes in your code

### Build errors (C++)
```bash
# Clean and rebuild
cd cpp_agent/build
rm -rf *
cmake ..
cmake --build . --config Release
```

### Port already in use
```bash
# Kill existing server (macOS/Linux)
lsof -ti:8000 | xargs kill -9

# Or use a different port in ui.py
```

### Time limit exceeded
- For testing your code with the UI, we have set the time limit to be 60 seconds per move
- Optimize your search algorithm

---

## Configuration Options

Edit `ui.py` to customize:

```python
TIME_LIMIT_SECS = 60  # Total time per move (seconds)
```

---

## Agent Communication Protocol

Agents communicate with the server via stdin/stdout using these commands:

| Command | Description |
|---------|-------------|
| `!REQ_PLAYER_NUM` | Request player ID (1 or 2) |
| `!REQ_BOARD` | Request current board state |
| `!REQ_TIME` | Request remaining time in milliseconds |
| `!REQ_MOVES` | Request opponent's moves |
| `!SENDING_MOVES` | Send your moves to server |

The controller handles this automatically - you don't need to implement the protocol yourself.

---

**Happy Bot Building!**
