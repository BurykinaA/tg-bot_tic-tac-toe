from typing import Final, Literal, TypeAlias, Optional
from copy import deepcopy


FREE_SPACE: Final = "."
CROSS: Final = "X"
ZERO: Final = "O"


Move: TypeAlias = tuple[int, int]
Symbol: TypeAlias = Literal[".", "X", "O"]
Field: TypeAlias = list[list[Symbol]]


DEFAULT_STATE = [[FREE_SPACE for _ in range(3)] for _ in range(3)]


def get_default_state() -> Field:
    """Helper function to get default state of the game"""
    return deepcopy(DEFAULT_STATE)


def next_move(grid: Field, symbol: Symbol) -> Move:
    best_score = float('-inf')
    best_move: Optional[Move] = None

    for i in range(3):
        for j in range(3):
            if grid[i][j] == FREE_SPACE:
                grid[i][j] = symbol
                score = minimax(grid, 0, False)
                grid[i][j] = FREE_SPACE  # отменяем ход

                if score > best_score:
                    best_score = score
                    best_move = (i, j)

    return Move(best_move)


def minimax(grid: Field, depth: int, is_maximizing: bool) -> int:
    scores = {'X': 1, 'O': -1, 'Tie': 0}

    result = check_winner(grid)
    if result is not None:
        return scores[result]

    if is_maximizing:
        best_score = float('-inf')
        for i in range(3):
            for j in range(3):
                if grid[i][j] == FREE_SPACE:
                    grid[i][j] = 'X'
                    score = minimax(grid, depth + 1, False)
                    grid[i][j] = FREE_SPACE  # отменяем ход
                    best_score = max(score, best_score)
        return best_score

    else:
        best_score = float('inf')
        for i in range(3):
            for j in range(3):
                if grid[i][j] == FREE_SPACE:
                    grid[i][j] = 'O'
                    score = minimax(grid, depth + 1, True)
                    grid[i][j] = FREE_SPACE  # отменяем ход
                    best_score = min(score, best_score)
        return best_score


def check_winner(grid: Field) -> Optional[str]:
    for row in grid:
        if all(cell == row[0] and cell != FREE_SPACE for cell in row):
            return row[0]  # выигрыш по горизонтали

    for col in range(3):
        if all(row[col] == grid[0][col] and row[col] != FREE_SPACE for row in grid):
            return grid[0][col]  # выигрыш по вертикали

    if all(grid[i][i] == grid[0][0] and grid[i][i] != FREE_SPACE for i in range(3)):
        return grid[0][0]  # выигрыш по диагонали (слева направо)

    if all(grid[i][2 - i] == grid[0][2] and grid[i][2 - i] != FREE_SPACE for i in range(3)):
        return grid[0][2]  # выигрыш по диагонали (справа налево)

    if all(cell != FREE_SPACE for row in grid for cell in row):
        return 'Tie'  # ничья

    return None  # нет выигрыша


class Handler:
    symbol: Symbol
    _game: "Game"

    def __init__(self, game: "Game", symbol: Symbol) -> None:
        self._game = game
        self.symbol: Symbol = symbol

    def __call__(self, move: Move) -> None:
        print(self.symbol)
        print(move)
        self._game.full_handle(move, self.symbol)

    def is_my_turn(self) -> bool:
        return self._game.current_move == self.symbol


class Game:
    def __init__(self):
        self.grid: Field = get_default_state()
        self._available_marks: set[Symbol] = {CROSS, ZERO}
        self.current_move: Symbol = CROSS  # first move
        self.is_game_over: bool = False

    def full_handle(self, move: Move, symbol: Symbol) -> None:
        self.make_move(move, symbol)
        if self.n_empty_cells() == 0 or self.get_winner() is not None:
            self.is_game_over = True
        self.current_move = ZERO if symbol == CROSS else CROSS

    def get_handle(
        self,
        mark: Symbol | None = None,
        what_is_left: bool = False,
    ) -> Handler:
        if what_is_left and len(self._available_marks) == 2:
            mark = CROSS
        elif not mark or what_is_left:
            mark = list(self._available_marks)[0]

        self._available_marks.remove(mark)
        handle = Handler(self, mark)
        return handle

    def make_move(self, move: Move, symbol) -> None:
        print(move)
        print(self.grid)
        cell = self.grid[move[0]][move[1]]
        if cell == FREE_SPACE:
            self.grid[move[0]][move[1]] = symbol

    def n_empty_cells(self) -> int:
        return sum(elem == FREE_SPACE for row in self.grid for elem in row)

    def get_winner(self) -> Symbol | None:
        for row in self.grid:
            if all(cell == row[0] and cell != FREE_SPACE for cell in row):
                return row[0]  

        for col in range(3):
            if all(row[col] == self.grid[0][col] and row[col] != FREE_SPACE for row in self.grid):
                return self.grid[0][col] 

        if all(self.grid[i][i] == self.grid[0][0] and self.grid[i][i] != FREE_SPACE for i in range(3)):
            return self.grid[0][0]

        if all(self.grid[i][2 - i] == self.grid[0][2] and self.grid[i][2 - i] != FREE_SPACE for i in range(3)):
            return self.grid[0][2] 

        return None 

    @property
    def result(self) -> Symbol | None:
        winner = self.get_winner(self.grid)
        if self.n_empty_cells(self.grid) == 0 or winner is not None:
            return winner
        return None
    


