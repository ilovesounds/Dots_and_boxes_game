# Python Agent (starter-code)

A Python port of the C++ `cpp_agent` starter. It speaks the same engine protocol:

- Prints `!REQ_PLAYER_NUM` and reads a single integer (1 or 2)
- Prints `!REQ_BOARD` then reads the full board
- Prints `!REQ_TIME` for time budget (optional usage)
- Sends moves via `!SENDING_MOVES` followed by count and each move as `row col isHorizontal` (isHorizontal: 1/0)
- Asks for opponent moves via `!REQ_MOVES` and reads the count followed by that many moves

## Layout

- `python_agent/`
  - `__main__.py` – entrypoint (`python -m python_agent`)
  - `agent.py` – Agent wrapper (init/run)
  - `controller.py` – engine I/O and board state
  - `board.py` – Board data model and rules
  - `move.py` – Move struct
  - `token_stream.py` – Token reader helper
  - `submission/agent.py` – put your bot logic here (implement `make_move(controller)`)

## Run

From `starter-code/`:

```bash
python3 -m python_agent
```

The engine will run the process and communicate via stdin/stdout using the same protocol used by the C++ agent.

## Notes

- Line presence is detected as non-zero (consistent with the UI sending 1/2 for line owner).
- Grid ownership uses `GridOwner` values (0 empty, 1/2 owned).
- The default submission picks random valid moves. Replace it with your strategy.
