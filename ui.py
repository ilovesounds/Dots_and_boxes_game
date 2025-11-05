import os
import signal
import sys
import subprocess as sps
import time
from typing import List
from collections import deque

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from pydantic import BaseModel

import asyncio

'''
STEP 0: Define globals and schemas
'''
TIME_LIMIT_SECS = 60

class Board(BaseModel):
    rows: int
    cols: int
    horizontalLines: List[List[int]]
    verticalLines: List[List[int]]
    gridOwner: List[List[int]]

    def __str__(self):
        stringify_grid = lambda grid: '\n'.join([' '.join([str(x) for x in row]) for row in grid])

        return '\n'.join([
            f"{self.rows} {self.cols}",
            stringify_grid(self.horizontalLines),
            stringify_grid(self.verticalLines),
            stringify_grid(self.gridOwner)
        ])

class NewGameRequest(BaseModel):
    bot1: str
    bot2: str
    board: Board

class MoveBotRequest(BaseModel):
    playerID: int
    previousMoves: List[List[int]]

class MoveBotResponse(BaseModel):
    row: int
    col: int
    isHorizontal: int
    time: float


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

cpp_agents = []
python_agents = []
processes = [None, None]
is_bot_initialized = [False, False]
time_taken = [None, None]
bot1 = None
bot2 = None
bot_moves = [None, None]
current_board: Board = None



'''
STEP #1: get all the agents
'''

def is_cpp_agent(dir):
    '''
    If a folder has CMakeLists.txt then consider it as a cpp_agent
    '''
    return os.path.isfile(os.path.join(dir, "CMakeLists.txt"))


def is_python_agent(dir):
    '''
    If a folder has agent.py then consider it as a python_agent
    '''
    return os.path.isfile(os.path.join(dir, "agent.py"))


def get_all_agents(dir):
    cpp_agents = [
        name for name in os.listdir(dir)
        if os.path.isdir(os.path.join(dir, name)) and \
            is_cpp_agent(os.path.join(dir, name))
    ]

    python_agents = [
        name for name in os.listdir(dir)
        if os.path.isdir(os.path.join(dir, name)) and \
            is_python_agent(os.path.join(dir, name))
    ]

    return cpp_agents, python_agents



'''
STEP 2: Build the cpp agents
'''

def build_cpp_agent(dir):
    '''
    dir: expects full path
    returns: path to agent executable
    '''
    # create build directory
    build_dir = os.path.join(dir, "build")
    os.makedirs(build_dir, exist_ok=True)

    # create build configs and run make
    sps.run(['cmake', '..'], cwd=build_dir, check=True, stdout=sps.DEVNULL, stderr=sps.DEVNULL)
    sps.run(["cmake", "--build", "."], cwd=build_dir, check=True, stdout=sps.DEVNULL, stderr=sps.DEVNULL)

    return [os.path.join(build_dir, 'agent')]


def get_python_agent(bot):
    return f"{sys.executable} -m {bot}".split()


'''
STEP 2.5: Handle board updates
'''
def is_capturing_above(move):
    global current_board
    return move['row'] > 0 and move['isHorizontal'] and \
        current_board.verticalLines[move['row']-1][move['col']] != 0 and \
        current_board.verticalLines[move['row']-1][move['col']+1] != 0 and \
        current_board.horizontalLines[move['row']-1][move['col']] != 0


def is_capturing_below(move):
    global current_board
    return move['row'] < current_board.rows-1 and move['isHorizontal'] and \
        current_board.verticalLines[move['row']][move['col']] != 0 and \
        current_board.verticalLines[move['row']][move['col']+1] != 0 and \
        current_board.horizontalLines[move['row']+1][move['col']] != 0


def is_capturing_left(move):
    global current_board
    return move['col'] > 0 and not move['isHorizontal'] and \
        current_board.horizontalLines[move['row']][move['col']-1] != 0 and \
        current_board.horizontalLines[move['row']+1][move['col']-1] != 0 and \
        current_board.verticalLines[move['row']][move['col']-1] != 0


def is_capturing_right(move):
    global current_board
    return move['col'] < current_board.cols-1 and not move['isHorizontal'] and \
        current_board.horizontalLines[move['row']][move['col']] != 0 and \
        current_board.horizontalLines[move['row']+1][move['col']] != 0 and \
        current_board.verticalLines[move['row']][move['col']+1] != 0


def update_ownership(move, playerID):
    global current_board

    if move['isHorizontal']:
        if is_capturing_above(move):
            current_board.gridOwner[move['row']-1][move['col']] = playerID
        if is_capturing_below(move):
            current_board.gridOwner[move['row']][move['col']] = playerID
    else:
        if is_capturing_left(move):
            current_board.gridOwner[move['row']][move['col']-1] = playerID
        if is_capturing_right(move):
            current_board.gridOwner[move['row']][move['col']] = playerID


def play_single_move(move, playerID):
    global current_board
    
    row = move['row']
    col = move['col']
    is_horizontal = move['isHorizontal']

    if is_horizontal:
        assert current_board.horizontalLines[row][col] == 0, "ILLEGAL MOVE"
        # current_board.horizontalLines[row][col] = playerID
        current_board.horizontalLines[row][col] = 1
    else:
        assert current_board.verticalLines[row][col] == 0, "ILLEGAL MOVE"
        # current_board.verticalLines[row][col] = playerID
        current_board.verticalLines[row][col] = 1
    
    update_ownership(move, playerID)


def play_moves_on_current_board(moves, playerID):
    global current_board
    for move in moves:
        play_single_move({
            'row': move[0],
            'col': move[1],
            'isHorizontal': move[2],
        }, playerID)




'''
STEP 3: Handle stdio process
'''
async def forward_stderr_to_stdout(process):
    """Continuously forward stderr of the process to this script's stdout."""
    while True:
        line = await process.stderr.readline()
        if not line:
            break
        # Decode and write directly to stdout
        sys.stdout.write(line.decode())
        sys.stdout.flush()


async def close_procs():
    global processes, bot1, bot2, bot_moves, current_board, is_bot_initialized, time_taken

    print('closing processes....')

    for proc in processes:
        if proc is None:
            continue

        proc.stdin.close()
        try:
            await asyncio.wait_for(proc.wait(), timeout=1)  # wait max 1 sec
        except asyncio.TimeoutError:
            proc.terminate()
            await asyncio.wait_for(proc.wait(), timeout=2)
    
    processes = [None, None]
    bot1 = None
    bot2 = None
    bot_moves = [None, None]
    current_board = None
    is_bot_initialized = [False, False]
    time_taken = [None, None]


async def get_line(proc):
    try:
        line = await asyncio.wait_for(proc.stdout.readline(), timeout=TIME_LIMIT_SECS)
        line = line.decode().strip()
    except asyncio.TimeoutError:
        print(f"No response for Agent (timeout)")
        print(f"Check agent for any bugs")
        await close()
    return line


async def send_line(proc, cmd):
    try:
        proc.stdin.write((str(cmd) + "\n").encode())
        await proc.stdin.drain()
    except (BrokenPipeError, ConnectionResetError):
        print("Agent did not accept any input. Fix bugs in agent")
        await close()


async def get_moves(proc, playerID):
    global time_taken
    start_time = time.perf_counter()

    while True:
        line = await get_line(proc)
        if line == '!REQ_TIME':
            await send_line(proc, int(1000*(TIME_LIMIT_SECS - time_taken[playerID-1] - (time.perf_counter() - start_time))))
            continue
        elif not line:
            # program ended
            print(f'Agent did not respond, program ended.')
            await close()
        break

    assert line == '!SENDING_MOVES', "Agent not configured properly!"

    num_moves = await get_line(proc)
    num_moves = int(num_moves)
    moves = []

    for _ in range(num_moves):
        move = await get_line(proc)
        move = list(map(int, move.split()))
        moves.append(move)
    
    end_time = time.perf_counter()

    return moves, end_time - start_time


async def send_moves(proc, moves):
    moves_str = f'{len(moves)}\n'
    moves_str += '\n'.join([' '.join([str(x) for x in move]) for move in moves])
    await send_line(proc, moves_str)


async def init_bot(proc, playerID, board):
    global bot_moves, time_taken

    # get initial playID setup request by bot
    line = await get_line(proc)
    assert line == '!REQ_PLAYER_NUM', "Agent not configured properly!"

    # send playerID
    await send_line(proc, playerID)

    line = await get_line(proc)
    assert line == '!REQ_BOARD', "Agent not configured properly!"

    time_taken[playerID-1] = 0


async def start_new_game(bot1_, bot2_, board):
    global processes, bot1, bot2, current_board, time_taken, bot_moves
    bot1 = bot1_
    bot2 = bot2_
    current_board = board
    time_taken = [0, 0]
    bot_moves = [deque(), deque()]

    for i, bot in enumerate([bot1_, bot2_]):
        if bot == 'Human':
            continue

        bot_path = ''
        if bot in cpp_agents:
            bot_path = build_cpp_agent(os.path.join(os.getcwd(), bot))
        elif bot in python_agents:
            bot_path = get_python_agent(bot)

        processes[i] = await asyncio.create_subprocess_exec(
            *bot_path,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        asyncio.create_task(forward_stderr_to_stdout(processes[i]))

        # now send the init stuff
        await init_bot(processes[i], i+1, current_board)


async def update_bot_and_get_move(proc, playerID, previousMoves):
    global current_board, is_bot_initialized, time_taken

    if not is_bot_initialized[playerID-1]:

        if playerID == 2 and bot1 == 'Human':
            # play human's moves
            play_moves_on_current_board(previousMoves, playerID=1)

        # send the board to initialise
        await send_line(proc, current_board)

        # get moves
        moves, time_taken_for_move = await get_moves(proc, playerID)
        time_taken[playerID-1] += time_taken_for_move

        for move in moves:
            bot_moves[playerID-1].append({
                'row': move[0],
                'col': move[1],
                'isHorizontal': move[2],
                'time': time_taken[playerID-1]
            })
        
        is_bot_initialized[playerID-1] = True
        play_moves_on_current_board(moves, playerID)


    if len(bot_moves[playerID-1]) > 0:
        # continous moves
        return bot_moves[playerID-1].popleft()
        
    # send previous move to bot
    line = await get_line(proc)
    assert line == "!REQ_MOVES", "Bot is not asking for opponent moves!"

    await send_moves(proc, previousMoves)

    moves, time_taken_for_move = await get_moves(proc, playerID)
    time_taken[playerID-1] += time_taken_for_move

    for move in moves:
        bot_moves[playerID-1].append({
            'row': move[0],
            'col': move[1],
            'isHorizontal': move[2],
            'time': time_taken[playerID-1]
        })

    current_move = bot_moves[playerID-1].popleft()
    play_single_move(current_move, playerID)
    return current_move



'''
STEP 4: Setup the server
'''
@app.get("/")
async def home():
    return FileResponse('./static/index.html')


@app.get("/all-agents")
def send_all_agents():
    global cpp_agents, python_agents
    return cpp_agents + python_agents


@app.post("/start-game")
async def start_new_game_endpoint(request: NewGameRequest):
    await close_procs()

    # sanitize the board for backend
    board = request.board
    for i, row in enumerate(board.horizontalLines):
        for j, ele in enumerate(row):
            if ele != 0:
                board.horizontalLines[i][j] = 1

    for i, row in enumerate(board.verticalLines):
        for j, ele in enumerate(row):
            if ele != 0:
                board.verticalLines[i][j] = 1


    await start_new_game(request.bot1, request.bot2, board)


@app.post("/move-bot")
async def play_move_endpoint(request: MoveBotRequest) -> MoveBotResponse:
    global processes
    move = await update_bot_and_get_move(processes[request.playerID-1], request.playerID, request.previousMoves)
    return MoveBotResponse(**move)

'''
STEP 5: init & close
'''

def init():
    global cpp_agents, python_agents
    cpp_agents, python_agents = get_all_agents(os.getcwd())
    assert len(cpp_agents) + len(python_agents) > 0, "ERROR: No agents found!"

    print(f"UI Started! Go to http://localhost:8000/")


async def close():
    print('exiting gracefully...')
    await close_procs()
    os.kill(os.getpid(), signal.SIGINT)

'''
Step 6: Run the server
'''

async def test_bots():
    init()

    board = Board(
        rows=2,
        cols=2,
        horizontalLines=[[0], [0]],
        verticalLines=[[0, 0]],
        gridOwner=[[0]]
    )

    await start_new_game_endpoint(NewGameRequest(
        bot1='cpp_agent',
        bot2='Human',
        board=board
    ))

    move_response = await play_move_endpoint(MoveBotRequest(
        playerID=1,
        previousMoves=[]
    ))



if __name__ == '__main__':
    init()
    uvicorn.run(app, port=8000, log_level='warning')
    # uvicorn.run(app, port=8000)


    # # test
    # asyncio.run(test_bots())
