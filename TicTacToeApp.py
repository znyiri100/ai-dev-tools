import tkinter as tk
from tkinter import messagebox
import random
import os
import sys

#!/usr/bin/env python3

class TicTacToeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Tic-Tac-Toe")
        self.resizable(False, False)
        self.board = [""] * 9
        self.current = "X"
        self.mode = tk.StringVar(value="Human vs Human")
        self.scores = {"X": 0, "O": 0, "Tie": 0}
        self._build_ui()

    def _build_ui(self):
        top = tk.Frame(self)
        top.pack(padx=10, pady=6)

        mode_menu = tk.OptionMenu(top, self.mode, "Human vs Human", "Human vs Computer", command=self._on_mode_change)
        mode_menu.pack(side="left")

        reset_btn = tk.Button(top, text="Reset Scores", command=self.reset_scores)
        reset_btn.pack(side="left", padx=6)

        new_btn = tk.Button(top, text="New Game", command=self.reset_board)
        new_btn.pack(side="left")

        self.status = tk.Label(self, text="X's turn", font=("Helvetica", 12))
        self.status.pack(pady=(2, 8))

        board_frame = tk.Frame(self)
        board_frame.pack(padx=10, pady=6)

        self.buttons = []
        for i in range(9):
            b = tk.Button(board_frame, text="", width=6, height=3, font=("Helvetica", 20),
                          command=lambda idx=i: self.on_click(idx))
            b.grid(row=i // 3, column=i % 3, padx=3, pady=3)
            self.buttons.append(b)

        self.score_label = tk.Label(self, text=self._score_text(), font=("Helvetica", 10))
        self.score_label.pack(pady=(6,10))

    def _on_mode_change(self, _=None):
        self.reset_board()

    def _score_text(self):
        return f"Scores — X: {self.scores['X']}   O: {self.scores['O']}   Ties: {self.scores['Tie']}"

    def on_click(self, idx):
        if self.board[idx] or self.check_winner() is not None:
            return
        if self.mode.get() == "Human vs Computer" and self.current == "O":
            return  # don't allow human to play O in this mode
        self.make_move(idx, self.current)
        winner = self.check_winner()
        if winner or all(self.board):
            self._finish_round(winner)
            return
        self.current = "O" if self.current == "X" else "X"
        self.status.config(text=f"{self.current}'s turn")
        if self.mode.get() == "Human vs Computer" and self.current == "O":
            self.after(200, self._computer_move)

    def make_move(self, idx, player):
        self.board[idx] = player
        self.buttons[idx].config(text=player, state="disabled", disabledforeground="black")

    def _computer_move(self):
        # Use minimax for optimal play
        idx = self.best_move("O")
        if idx is None:
            idx = random.choice([i for i, v in enumerate(self.board) if v == ""])
        self.make_move(idx, "O")
        winner = self.check_winner()
        if winner or all(self.board):
            self._finish_round(winner)
            return
        self.current = "X"
        self.status.config(text="X's turn")

    def best_move(self, player):
        opponent = "X" if player == "O" else "O"

        def minimax(board, turn):
            winner = self._evaluate_board(board)
            if winner is not None:
                return winner
            moves = []
            for i, v in enumerate(board):
                if v == "":
                    nb = board[:]
                    nb[i] = turn
                    score = minimax(nb, "O" if turn == "X" else "X")
                    moves.append((i, score))
            if turn == player:
                # maximize
                best = max(moves, key=lambda x: x[1])
                return best[1]
            else:
                # minimize
                best = min(moves, key=lambda x: x[1])
                return best[1]

        best_score = None
        best_idx = None
        for i, v in enumerate(self.board):
            if v == "":
                nb = self.board[:]
                nb[i] = player
                score = minimax(nb, opponent)
                if best_score is None or score > best_score:
                    best_score = score
                    best_idx = i
        return best_idx

    def _evaluate_board(self, board):
        wins = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
        for a,b,c in wins:
            if board[a] and board[a] == board[b] == board[c]:
                return 1 if board[a] == "O" else -1  # O is maximizing in minimax usage
        if all(board):
            return 0
        return None

    def check_winner(self):
        wins = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
        for a,b,c in wins:
            if self.board[a] and self.board[a] == self.board[b] == self.board[c]:
                return self.board[a]
        if all(self.board):
            return "Tie"
        return None

    def _finish_round(self, winner):
        if winner == "Tie":
            self.scores["Tie"] += 1
            self.status.config(text="It's a tie!")
        elif winner:
            self.scores[winner] += 1
            self.status.config(text=f"{winner} wins!")
            for i in range(9):
                if self.board[i] == winner:
                    self.buttons[i].config(bg="#b3ffb3")
        else:
            self.status.config(text="Game over")
        for b in self.buttons:
            b.config(state="disabled")
        self.score_label.config(text=self._score_text())

    def reset_board(self):
        self.board = [""] * 9
        self.current = "X"
        self.status.config(text="X's turn")
        for b in self.buttons:
            b.config(text="", state="normal", bg="SystemButtonFace")
        if self.mode.get() == "Human vs Computer" and self.current == "O":
            self.after(200, self._computer_move)

    def reset_scores(self):
        self.scores = {"X": 0, "O": 0, "Tie": 0}
        self.score_label.config(text=self._score_text())
        self.reset_board()

if __name__ == "__main__":
    # Detect headless environment (no X11/Wayland display) and give instructions.
    if sys.platform.startswith("linux") and not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
        print("No display detected. To run the GUI in a headless environment, install Xvfb and run:")
        print("  xvfb-run -s '-screen 0 1024x768x24' python TicTacToeApp.py")
        sys.exit(1)
    app = TicTacToeApp()
    app.mainloop()