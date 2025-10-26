import sys
from copy import deepcopy
import tkinter as tk

# rules
FIRST_ROW_PAWN_COUNT = 4


class Halma:
    def __init__(self, grid_size: int):
        # game logical grid
        self.grid: list[list[int]] = self.initialize_grid(grid_size)
        # static "camps" tuple holds coordinates of camps for each team
        self.camps: tuple[tuple[int, ...], ...] = self._initialize_camps(self.grid)
        # can contain "highlighted" squares (3), not used for logic
        self.grid_display: list[list[int]] = deepcopy(self.grid)
        # pawns (ids) displayed in tkinter window
        self.pawns: list[list[tk.Canvas]] = []

        self.player_turn: int = 1  # number of player whos turn it is
        self.selected: tuple[int, int] = (0, 0)  # row, col of currently selected piece

        # tkinter graphical setup
        self.display: tk.Tk = tk.Tk()
        self.display.title("Halma")
        self.grid_options: dict[int, tuple[str, str]] = {
            0: ("", ""),
            1: ("black", "blue"),
            2: ("black", "red"),
            3: ("black", "green"),
        }
        self._initialize_tkinter_grid()
        self._redraw_tkinter_grid()
        self.player_turn_display: tk.Label = tk.Label(
            self.display, fg="blue", text="Player 1's turn"
        )
        self.player_turn_display.grid(row=grid_size, columnspan=grid_size)
        self.display.mainloop()

    def make_move(self, selected_row: int, selected_col: int):
        print("making move", selected_row, selected_col)
        current_row, current_col = self.selected
        delta_row = selected_row - current_row
        delta_col = selected_col - current_col

        if self._is_valid_move(current_row, current_col, delta_row, delta_col):
            self.grid[current_row][current_col] = 0
            self.grid[selected_row][selected_col] = self.player_turn
            self.grid_display = deepcopy(self.grid)

            # if player jumped another piece, they keep their turn, else swap turns
            if abs(delta_row) != 2 and abs(delta_col) != 2:
                self._swap_turns()
        else:
            self.select_piece(selected_row, selected_col)

        self._redraw_tkinter_grid()

        for player in range(1, 3):
            if self._check_victory(player):
                print(f"Player {player} wins!")
                self.display.quit()

    def initialize_grid(self, grid_size: int) -> list[list[int]]:
        grid = [[0] * grid_size for _ in range(grid_size)]
        return self._initialize_players(grid)

    def print_grid(self):
        print(*self.grid_display, sep="\n")

    def select_piece(self, selected_row: int, selected_col: int) -> None:
        self.grid_display = deepcopy(self.grid)  # deep copy to avoid mutation

        if self.grid[selected_row][selected_col] != self.player_turn:
            return None  # piece is not current players'

        self.selected = (selected_row, selected_col)

        # display possible moves
        for delta_row in range(-2, 3):
            for delta_col in range(-2, 3):
                if self._is_valid_move(
                    selected_row, selected_col, delta_row, delta_col
                ):
                    move_row = selected_row + delta_row
                    move_col = selected_col + delta_col
                    self.grid_display[move_row][move_col] = 3  # 3 is highlight

    def _check_victory(self, player: int):
        opponent = 2 if player == 1 else 1

        piece_coordinates = [
            (row_index, col_index)
            for row_index, row in enumerate(self.grid)
            for col_index, col in enumerate(row)
            if col == player
        ]

        return all(
            self.camps[row_index][col_index] == opponent
            for row_index, col_index in piece_coordinates
        )

    def _initialize_tkinter_grid(self):
        for row_index in range(len(self.grid)):
            row_pawns: list[tk.Canvas] = []
            for col_index in range(len(self.grid)):
                canvas = tk.Canvas(width=50, height=50, relief="solid", borderwidth=1)

                row_pawns.append(canvas)

                _ = canvas.create_oval(
                    8, 8, 50, 50, outline="black", fill="red", width=2
                )

                canvas.grid(
                    row=row_index, column=col_index, padx=0, pady=0, sticky="nsew"
                )
                _ = canvas.bind(
                    "<Button-1>",
                    lambda _, row=row_index, col=col_index: self.make_move(row, col),
                )
            self.pawns.append(row_pawns)

    def _redraw_tkinter_grid(self):
        for row_index, row in enumerate(self.pawns):
            for col_index, pawn in enumerate(row):
                outline, fill = self.grid_options[
                    self.grid_display[row_index][col_index]
                ]
                _ = pawn.itemconfig(1, outline=outline, fill=fill)

    def _initialize_players(self, grid: list[list[int]]):
        for row_index in range(FIRST_ROW_PAWN_COUNT):
            player_1_row = grid[row_index]
            player_2_row = grid[-row_index - 1]
            for col_index in range(FIRST_ROW_PAWN_COUNT - row_index):
                player_1_row[col_index] = 1
                player_2_row[-col_index - 1] = 2

        return grid

    def _initialize_camps(self, game_grid: list[list[int]]):
        grid = deepcopy(game_grid)

        for row_index in range(FIRST_ROW_PAWN_COUNT + 1):
            player_1_row = grid[row_index]
            player_2_row = grid[-row_index - 1]
            for col_index in range(FIRST_ROW_PAWN_COUNT + 1 - row_index):
                player_1_row[col_index] = 1
                player_2_row[-col_index - 1] = 2

        return tuple((tuple(row) for row in grid))

    def _swap_turns(self):
        self.player_turn = 1 if self.player_turn == 2 else 2
        _, color = self.grid_options[self.player_turn]
        _ = self.player_turn_display.config(
            text=f"Player {self.player_turn}'s turn", fg=color
        )

    def _is_valid_move(
        self, current_row: int, current_col: int, delta_row: int, delta_col: int
    ) -> bool:
        new_row = current_row + delta_row
        new_col = current_col + delta_col

        if not self._is_in_bounds(new_row, new_col):  # move out of bounds
            return False

        elif abs(delta_col) < 2 and abs(delta_row) < 2:  # move is single square
            return self.grid[new_row][new_col] == 0  # true if no piece present

        elif (
            abs(delta_col) == 2
            and abs(delta_row) == 2
            or abs(delta_col) == 2
            and abs(delta_row) == 0
            or abs(delta_col) == 0
            and abs(delta_row) == 2
        ):  # if orthogonal or diagonal
            adjacent_row = current_row + self._decrease_magnitude(delta_row)
            adjacent_col = current_col + self._decrease_magnitude(delta_col)
            return (
                self.grid[new_row][new_col] == 0  # no piece on destination
                and self.grid[adjacent_row][adjacent_col] != 0  # piece present to jump
            )
        else:  # move is not orthogonal or diagonal OR move is greater than 2
            return False

    def _is_in_bounds(self, row: int, col: int) -> bool:
        grid_size = len(self.grid)
        return row >= 0 and row < grid_size and col >= 0 and col < grid_size

    def _decrease_magnitude(self, number: int) -> int:
        if number > 0:
            return number - 1
        elif number < 0:
            return number + 1
        return number  # number is already 0


if __name__ == "__main__":
    game = Halma(int(sys.argv[1]))
