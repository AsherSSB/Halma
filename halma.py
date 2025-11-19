import sys
from copy import deepcopy
import tkinter as tk

# rules
FIRST_ROW_PAWN_COUNT = 4


class Halma:
    def __init__(self, grid_size: int, timeout: int, player_color: str):
        # game logical grid
        self.grid: list[list[int]] = self._initialize_grid(grid_size)
        # time allowed to make move before timeout
        self.timeout: int = timeout
        # time before current turn is over
        self.time_remaining: int = timeout
        # static "camps" tuple holds coordinates of camps for each team
        self.camps: tuple[tuple[int, ...], ...] = self._initialize_camps(self.grid)
        # can contain "highlighted" squares (3), not used for logic
        self.grid_display: list[list[int]] = deepcopy(self.grid)
        # pawns (ids) displayed in tkinter window
        self.pawns: list[list[tk.Canvas]] = []

        self.player_1_score: float = 0
        self.player_2_score: float = 0
        self.turn_number: int = 0  # total number of turns taken
        self.player_turn: int = 1  # number of player whos turn it is
        self.selected: tuple[int, int] = (-1, -1)  # row, col of selected piece
        self.previous_square: tuple[int, int] = tuple()  # previous pawn position
        self.after_timer_decrement: str = ""

        # tkinter graphical setup
        self.display: tk.Tk = tk.Tk()
        self.display.title("Halma")
        self.grid_options: dict[int, tuple[str, str]] = {
            0: ("", ""),  # empty square
            1: ("black", player_color),  # player 1 / human color
            2: ("black", "black"),  # player 2 / ai color
            3: ("black", "cyan"),  # highlighted possible moves colors
            4: ("black", "gold"),  # selected pawn color
            5: ("black", "gray"),  # previous move
        }
        # set up row labels
        for row_index in range(grid_size):
            row_label = tk.Label(self.display, text=str(row_index + 1))
            row_label.grid(row=row_index + 1, column=0)

        # set up column labels
        for col_index in range(grid_size):
            label_character = chr(ord("a") + col_index)
            col_label = tk.Label(self.display, text=label_character)
            col_label.grid(row=grid_size + 1, column=col_index + 1)

        # set up status bar
        self.player_turn_display: tk.Label = tk.Label(
            self.display, text="Player 1's turn"
        )
        self.player_turn_display.grid(row=0, column=1, columnspan=grid_size // 4)

        self.timer_display: tk.Label = tk.Label(
            self.display, text=f"Time: {self.time_remaining}"
        )
        self.timer_display.grid(
            row=0, column=(grid_size // 4) + 1, columnspan=grid_size // 4
        )

        self.player_1_score_display: tk.Label = tk.Label(self.display)
        self.player_1_score_display.grid(
            row=0, column=(grid_size // 4) * 2 + 1, columnspan=grid_size // 4
        )

        self.player_2_score_display: tk.Label = tk.Label(self.display)

        self._set_player_scores()

        self.player_2_score_display.grid(
            row=0, column=(grid_size // 4) * 3 + 1, columnspan=grid_size // 4
        )

        # setup input box
        self.move_input: tk.Entry = tk.Entry(self.display)
        self.move_input.bind("<Return>", self._process_move_input)
        self.move_input.grid(row=grid_size + 2, column=0, columnspan=grid_size // 2)

        # setup error messages
        self.error_message: tk.Label = tk.Label(self.display, fg="red")
        self.error_message.grid(
            row=grid_size + 2, column=grid_size // 2, columnspan=grid_size // 2 + 1
        )

    def start_game(self):
        self._initialize_tkinter_grid()
        self._redraw_tkinter_grid()
        # timer display loop
        self.after_timer_decrement = self.display.after(1000, self._decrement_timer)
        self.display.mainloop()

    def make_move(self, selected_row: int, selected_col: int):
        current_row, current_col = self.selected

        if self.grid_display[selected_row][selected_col] == 3:  # selected valid move
            self.grid[current_row][current_col] = 0
            self.grid[selected_row][selected_col] = self.player_turn
            self.grid_display = deepcopy(self.grid)

            # if player jumped another piece, they keep their turn, else swap turns
            self.previous_square = self.selected
            self.selected = (-1, -1)
            self._swap_turns()
        else:
            self._select_piece(selected_row, selected_col)

        self._redraw_tkinter_grid()

        for player in range(1, 3):
            if self._check_victory(player):
                self._end_game(winning_player=player)

    def _process_move_input(self, _):
        player_input = self.move_input.get()
        self.move_input.delete(0, tk.END)
        column_base_value = ord("a")
        try:  # some very suspicious and list unpacking
            starting_coordinate, dest_coordinate = player_input.strip().split("->")

            starting_col_char = starting_coordinate[0]
            starting_row_index = int(starting_coordinate[1:])
            starting_row_index = starting_row_index - 1
            starting_col_index = ord(starting_col_char) - column_base_value

            dest_col_char = dest_coordinate[0]
            dest_row_index = int(dest_coordinate[1:])
            dest_row_index = dest_row_index - 1
            dest_col_index = ord(dest_col_char) - column_base_value

            self._select_piece(starting_row_index, starting_col_index)
            self.make_move(dest_row_index, dest_col_index)
        except Exception:
            self.make_move(-1, -1)  # input move is invalid

    def _initialize_grid(self, grid_size: int) -> list[list[int]]:
        grid = [[0] * grid_size for _ in range(grid_size)]
        return self._initialize_players(grid)

    def _select_piece(self, selected_row: int, selected_col: int) -> None:
        self.grid_display = deepcopy(self.grid)  # deep copy to avoid mutation

        if self.grid[selected_row][selected_col] != self.player_turn:
            self.selected = (-1, -1)
            _ = self.error_message.config(text="Invalid move")
            return None  # piece is not current players'

        self.selected = (selected_row, selected_col)
        # mark possible moves
        self._highlight_valid_moves_for_square(selected_row, selected_col)

        # remove move from possible moves if it is not a forward move
        highlighted_moves = (
            (row_index, col_index)
            for row_index, row in enumerate(self.grid_display)
            for col_index, col in enumerate(row)
            if col == 3
        )

        for new_row_index, new_col_index in highlighted_moves:
            current_score = self._get_score_from_closest_camp(
                self.player_turn, selected_row, selected_col
            )
            new_score = self._get_score_from_closest_camp(
                self.player_turn, new_row_index, new_col_index
            )
            if new_score < current_score:
                self.grid_display[new_row_index][new_col_index] = 0

    def _highlight_valid_moves_for_square(
        self,
        row_index: int,
        col_index: int,
        explored_squares: set[tuple[int, int]] | None = None,
        jumped: bool = False,
    ) -> None:
        if not explored_squares:
            explored_squares = set()
        explored_squares.add((row_index, col_index))

        for delta_row in range(-2, 3):
            for delta_col in range(-2, 3):
                if self._is_valid_move(
                    row_index, col_index, delta_row, delta_col, jumped
                ):
                    move_row = row_index + delta_row
                    move_col = col_index + delta_col
                    self.grid_display[move_row][move_col] = 3  # 3 is highlight
                    if (move_row, move_col) not in explored_squares and (
                        delta_col == 2 or delta_row == 2
                    ):
                        self._highlight_valid_moves_for_square(
                            move_row, move_col, explored_squares, True
                        )

    def _check_victory(self, player: int):
        opponent = 2 if player == 1 else 1

        print("GAME")
        print("\n".join((str(row) for row in self.grid)), sep="\n")
        print("CAMPS")
        print("\n".join((str(row) for row in self.camps)), sep="\n")

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
                    row=row_index + 1,
                    column=col_index + 1,
                    padx=0,
                    pady=0,
                    sticky="nsew",
                )
                _ = canvas.bind(
                    "<Button-1>",
                    lambda _, row=row_index, col=col_index: self.make_move(row, col),
                )
            _ = self.display.grid_rowconfigure(row_index + 1, weight=0)
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

        outline, fill = self.grid_options[5]  # 5 is previous position colors
        if self.previous_square:
            previous_row, previous_col = self.previous_square
            _ = self.pawns[previous_row][previous_col].itemconfig(
                1, outline=outline, fill=fill
            )

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
        self.display.after_cancel(self.after_timer_decrement)
        self.time_remaining = self.timeout
        self.selected = (-1, -1)
        self.player_turn = 1 if self.player_turn == 2 else 2
        _ = self.player_turn_display.config(text=f"Player {self.player_turn}'s turn")

        # remove highlighted "possible move" squares
        self.grid_display = [
            [status if status != 3 else 0 for status in row]
            for row in self.grid_display
        ]

        self.turn_number += 1
        _ = self.error_message.config(text="")
        self._set_player_scores()
        self._redraw_tkinter_grid()
        self.after_timer_decrement = self.display.after(1000, self._decrement_timer)
        _ = self.timer_display.config(text=f"Time: {self.timeout}")

    def _is_valid_move(
        self,
        current_row: int,
        current_col: int,
        delta_row: int,
        delta_col: int,
        jumped: bool,
    ) -> bool:
        new_row = current_row + delta_row
        new_col = current_col + delta_col

        if not self._is_in_bounds(new_row, new_col):  # move out of bounds
            return False

        if jumped:  # previous move was a jump
            return self._is_valid_jump(current_row, current_col, delta_row, delta_col)

        elif abs(delta_col) < 2 and abs(delta_row) < 2:  # move is single square
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

    def _decrement_timer(self):
        self.time_remaining -= 1
        if self.time_remaining <= 0:
            winner = 2 if self.player_turn == 1 else 1
            self._end_game(winner, timeout=True)

        _ = self.timer_display.config(text=f"Time: {self.time_remaining}")
        self.after_timer_decrement = self.display.after(1000, self._decrement_timer)

    def _set_player_scores(self):
        self.player_1_score = self._calculate_score(1)
        self.player_2_score = self._calculate_score(2)
        _ = self.player_1_score_display.config(
            text=f"P1 Score: {self.player_1_score:.2f}"
        )
        _ = self.player_2_score_display.config(
            text=f"P2 Score: {self.player_2_score:.2f}"
        )

    def _calculate_score(self, player: int):
        return sum(
            self._get_score_from_closest_camp(player, row_index, col_index)
            for row_index, row in enumerate(self.grid)
            for col_index, col in enumerate(row)
            if col == player
        )

    def _get_score_from_closest_camp(
        self, player: int, row_index: int, col_index: int
    ) -> float:
        opponent = 2 if player == 1 else 1

        opponent_camp_coordinates = (
            (camp_row_index, camp_col_index)
            for camp_row_index, camp_row in enumerate(self.camps)
            for camp_col_index, camp_col in enumerate(camp_row)
            if camp_col == opponent
        )

        closest_euclidean_distance = min(
            self._get_euclidean_distance(
                row_index, col_index, camp_row_index, camp_col_index
            )
            for camp_row_index, camp_col_index in opponent_camp_coordinates
        )

        return 1 / closest_euclidean_distance if closest_euclidean_distance > 0 else 1

    def _get_euclidean_distance(self, x1: int, y1: int, x2: int, y2: int) -> float:
        return (((x1 - x2) ** 2) + ((y1 - y2) ** 2)) ** (1 / 2)

    def _end_game(self, winning_player: int, timeout: bool = False):
        # remake display with endscreen info
        for widget in self.display.winfo_children():
            widget.destroy()

        timeout_notification = "Timeout! " if timeout else ""

        winner_display = tk.Label(
            self.display, text=f"{timeout_notification}Player {winning_player} wins!"
        )
        winner_display.grid(row=0, column=0, columnspan=len(self.grid) + 1)

        player_1_score_display = tk.Label(
            self.display, text=f"Player 1 score: {self.player_1_score:.2f}"
        )
        player_2_score_display = tk.Label(
            self.display, text=f"Player 2 score: {self.player_2_score:.2f}"
        )
        player_1_score_display.grid(
            row=len(self.grid) // 2, column=0, columnspan=len(self.grid) // 2
        )
        player_2_score_display.grid(
            row=len(self.grid) // 2,
            column=len(self.grid) // 2,
            columnspan=len(self.grid) // 2,
        )

        exit_button = tk.Button(
            text="Exit", bg="red", fg="black", command=self.display.quit
        )

        exit_button.grid(row=len(self.grid), column=len(self.grid), columnspan=2)


if __name__ == "__main__":
    board_size: int
    timeout: int
    player_color: str

    try:
        board_size = int(sys.argv[1])
        if board_size != 8 and board_size != 10 and board_size != 16:
            raise Exception
    except Exception:
        print("board size may only be of size 8, 10, or 16")
        print("exiting Hamlma")
        sys.exit(1)

    try:
        timeout = int(sys.argv[2])
        if timeout < 1:
            raise Exception
    except Exception:
        print("timeout must be an integer greater than 0")
        print("exiting Hamlma")
        sys.exit(2)

    player_color = sys.argv[3]
    if player_color != "green" and player_color != "red":
        print("player_color must be set to either green or red!")
        print("exiting Hamlma")
        sys.exit(3)

    game = Halma(board_size, timeout, player_color)
    game.start_game()
    sys.exit(0)
