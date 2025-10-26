import sys
from copy import deepcopy
import tkinter as tk

# rules
FIRST_ROW_PAWN_COUNT = 4


class Halma:
    def __init__(self, grid_size: int):
        # game logical grid
        self.grid: list[list[int]] = self._initialize_grid(grid_size)
        # static "camps" tuple holds coordinates of camps for each team
        self.camps: tuple[tuple[int, ...], ...] = self._initialize_camps(self.grid)
        # can contain "highlighted" squares (3), not used for logic
        self.grid_display: list[list[int]] = deepcopy(self.grid)
        # pawns (ids) displayed in tkinter window
        self.pawns: list[list[tk.Canvas]] = []

        self.player_turn: int = 1  # number of player whos turn it is
        self.selected: tuple[int, int] = (-1, -1)  # row, col of selected piece
        self.jumped: bool = False

        # tkinter graphical setup
        self.display: tk.Tk = tk.Tk()
        self.display.title("Halma")
        self.grid_options: dict[int, tuple[str, str]] = {
            0: ("", ""),
            1: ("black", "white"),
            2: ("black", "black"),
            3: ("black", "green"),
            4: ("black", "gold"),
        }
        self.player_turn_display: tk.Label = tk.Label(
            self.display, text="Player 1's turn"
        )
        self.pass_turn_button: tk.Button = tk.Button(
            self.display, text="Pass turn", state=tk.DISABLED, command=self._swap_turns
        )
        self.player_turn_display.grid(
            row=grid_size, column=0, columnspan=grid_size // 2
        )
        self.pass_turn_button.grid(
            row=grid_size, column=grid_size // 2, columnspan=grid_size // 2
        )

        # start game
        self._initialize_tkinter_grid()
        self._redraw_tkinter_grid()
        self.display.mainloop()

    def make_move(self, selected_row: int, selected_col: int):
        current_row, current_col = self.selected
        delta_row = selected_row - current_row
        delta_col = selected_col - current_col

        if self._is_valid_move(current_row, current_col, delta_row, delta_col):
            self.grid[current_row][current_col] = 0
            self.grid[selected_row][selected_col] = self.player_turn
            self.grid_display = deepcopy(self.grid)

            # if player jumped another piece, they keep their turn, else swap turns
            if abs(delta_row) != 2 and abs(delta_col) != 2:
                self.selected = (-1, -1)
                self._swap_turns()
            else:
                self.selected = (selected_row, selected_col)
                self.jumped = True
                _ = self.pass_turn_button.config(state=tk.ACTIVE)
                self._select_piece(*self.selected)  # displays possible moves
        else:
            self._select_piece(selected_row, selected_col)

        self._redraw_tkinter_grid()

        for player in range(1, 3):
            if self._check_victory(player):
                print(f"Player {player} wins!")
                self.display.quit()

    def _initialize_grid(self, grid_size: int) -> list[list[int]]:
        grid = [[0] * grid_size for _ in range(grid_size)]
        return self._initialize_players(grid)

    def _select_piece(self, selected_row: int, selected_col: int) -> None:
        self.grid_display = deepcopy(self.grid)  # deep copy to avoid mutation

        if not self.jumped:  # if player hasnt jumped this turn
            if self.grid[selected_row][selected_col] != self.player_turn:
                self.selected = (-1, -1)
                return None  # piece is not current players'

            self.selected = (selected_row, selected_col)  # select new pawn

        else:
            selected_row, selected_col = self.selected

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

                _ = canvas.create_rectangle(
                    8, 8, 50, 50, outline="black", fill="green", width=2
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
                square_state = self.grid_display[row_index][col_index]
                outline, fill = self.grid_options[square_state]
                if (row_index, col_index) == self.selected:
                    outline, fill = self.grid_options[4]  # 4 is highlighted piece
                    _ = pawn.itemconfig(2, outline="", fill="")
                    _ = pawn.itemconfig(1, outline=outline, fill=fill)
                elif square_state == 3:  # potential move
                    _ = pawn.itemconfig(2, outline=outline, fill=fill)
                else:
                    _ = pawn.itemconfig(2, outline="", fill="")
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
        self.jumped = False
        self.selected = (-1, -1)
        self.player_turn = 1 if self.player_turn == 2 else 2
        _ = self.pass_turn_button.config(state=tk.DISABLED)
        _ = self.player_turn_display.config(text=f"Player {self.player_turn}'s turn")

        # remove highlighted "possible move" squares
        self.grid_display = [
            [status if status != 3 else 0 for status in row]
            for row in self.grid_display
        ]

        self._redraw_tkinter_grid()

    def _is_valid_move(
        self, current_row: int, current_col: int, delta_row: int, delta_col: int
    ) -> bool:
        new_row = current_row + delta_row
        new_col = current_col + delta_col

        if not self._is_in_bounds(new_row, new_col):  # move out of bounds
            return False

        if self.jumped:  # previous move was a jump
            return self._is_valid_jump(current_row, current_col, delta_row, delta_col)

        if abs(delta_col) < 2 and abs(delta_row) < 2:  # move is single square
            return self.grid[new_row][new_col] == 0  # true if no piece present

        else:
            return self._is_valid_jump(current_row, current_col, delta_row, delta_col)

    def _is_valid_jump(
        self, current_row: int, current_col: int, delta_row: int, delta_col: int
    ):
        new_row = current_row + delta_row
        new_col = current_col + delta_col

        adjacent_row = current_row + self._decrease_magnitude(delta_row)
        adjacent_col = current_col + self._decrease_magnitude(delta_col)

        is_orthag_or_diag = (
            abs(delta_col) == 2
            and abs(delta_row) == 2
            or abs(delta_col) == 2
            and abs(delta_row) == 0
            or abs(delta_col) == 0
            and abs(delta_row) == 2
        )

        adjactent_piece_precent = self.grid[adjacent_row][adjacent_col] != 0

        no_piece_at_destination = (
            self.grid[new_row][new_col] == 0
        )  # no piece on destination

        return is_orthag_or_diag and adjactent_piece_precent and no_piece_at_destination

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
