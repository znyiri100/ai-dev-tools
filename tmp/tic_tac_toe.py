"""
Tic-Tac-Toe Game with GUI
A classic two-player tic-tac-toe game using tkinter with AI opponent
"""

import tkinter as tk
from tkinter import messagebox
from typing import Optional
import random
import winsound
import threading


class TicTacToe:
    def __init__(self, root):
        self.root = root
        self.root.title("Tic-Tac-Toe")
        self.root.resizable(False, False)

        # Game state
        self.current_player = "X"
        self.board = [""] * 9  # Empty board
        self.game_over = False
        self.game_mode = None  # "player" or "ai"
        self.ai_difficulty = None  # "easy", "medium", "hard"
        self.player_symbol = "X"
        self.ai_symbol = "O"

        # Show mode selection
        self.show_mode_selection()

    def play_sound(self, sound_type):
        """Play sound effect in background thread"""
        def _play():
            try:
                if sound_type == "move":
                    # Short click sound
                    winsound.Beep(800, 100)
                elif sound_type == "win":
                    # Victory sound - ascending tones
                    winsound.Beep(523, 150)  # C
                    winsound.Beep(659, 150)  # E
                    winsound.Beep(784, 150)  # G
                    winsound.Beep(1047, 300) # C high
                elif sound_type == "lose":
                    # Defeat sound - descending tones
                    winsound.Beep(784, 150)  # G
                    winsound.Beep(659, 150)  # E
                    winsound.Beep(523, 150)  # C
                    winsound.Beep(392, 300)  # G low
                elif sound_type == "draw":
                    # Draw sound - neutral tone
                    winsound.Beep(440, 200)  # A
                    winsound.Beep(440, 200)  # A
                elif sound_type == "button":
                    # Button click sound
                    winsound.Beep(600, 80)
            except:
                # Silently fail if sound doesn't work
                pass

        # Play sound in background to not block UI
        threading.Thread(target=_play, daemon=True).start()

    def show_mode_selection(self):
        """Display mode selection dialog"""
        selection_frame = tk.Frame(self.root, bg="#2c3e50", padx=40, pady=40)
        selection_frame.pack()

        title = tk.Label(
            selection_frame,
            text="Tic-Tac-Toe",
            font=("Arial", 24, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title.pack(pady=(0, 20))

        subtitle = tk.Label(
            selection_frame,
            text="Choose Game Mode",
            font=("Arial", 14),
            bg="#2c3e50",
            fg="#ecf0f1"
        )
        subtitle.pack(pady=(0, 30))

        # 2 Player button
        player_btn = tk.Button(
            selection_frame,
            text="2 Players",
            font=("Arial", 14, "bold"),
            bg="#3498db",
            fg="white",
            activebackground="#2980b9",
            command=lambda: self.start_game("player"),
            padx=40,
            pady=15,
            width=15
        )
        player_btn.pack(pady=10)

        # VS AI button
        ai_btn = tk.Button(
            selection_frame,
            text="VS AI",
            font=("Arial", 14, "bold"),
            bg="#e74c3c",
            fg="white",
            activebackground="#c0392b",
            command=self.show_difficulty_selection,
            padx=40,
            pady=15,
            width=15
        )
        ai_btn.pack(pady=10)

        self.root.configure(bg="#2c3e50")

    def show_difficulty_selection(self):
        """Display AI difficulty selection"""
        # Clear current widgets
        for widget in self.root.winfo_children():
            widget.destroy()

        selection_frame = tk.Frame(self.root, bg="#2c3e50", padx=40, pady=40)
        selection_frame.pack()

        title = tk.Label(
            selection_frame,
            text="Select Difficulty",
            font=("Arial", 20, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title.pack(pady=(0, 30))

        # Easy button
        easy_btn = tk.Button(
            selection_frame,
            text="Easy",
            font=("Arial", 14, "bold"),
            bg="#27ae60",
            fg="white",
            activebackground="#229954",
            command=lambda: self.start_game("ai", "easy"),
            padx=40,
            pady=12,
            width=15
        )
        easy_btn.pack(pady=8)

        # Medium button
        medium_btn = tk.Button(
            selection_frame,
            text="Medium",
            font=("Arial", 14, "bold"),
            bg="#f39c12",
            fg="white",
            activebackground="#e67e22",
            command=lambda: self.start_game("ai", "medium"),
            padx=40,
            pady=12,
            width=15
        )
        medium_btn.pack(pady=8)

        # Hard button
        hard_btn = tk.Button(
            selection_frame,
            text="Hard (Unbeatable)",
            font=("Arial", 14, "bold"),
            bg="#e74c3c",
            fg="white",
            activebackground="#c0392b",
            command=lambda: self.start_game("ai", "hard"),
            padx=40,
            pady=12,
            width=15
        )
        hard_btn.pack(pady=8)

        # Back button
        back_btn = tk.Button(
            selection_frame,
            text="Back",
            font=("Arial", 12),
            bg="#34495e",
            fg="white",
            activebackground="#2c3e50",
            command=self.back_to_mode_selection,
            padx=20,
            pady=8
        )
        back_btn.pack(pady=(20, 0))

    def back_to_mode_selection(self):
        """Return to mode selection screen"""
        for widget in self.root.winfo_children():
            widget.destroy()
        self.show_mode_selection()

    def start_game(self, mode, difficulty=None):
        """Start the game with selected mode"""
        self.game_mode = mode
        self.ai_difficulty = difficulty

        # Clear selection widgets
        for widget in self.root.winfo_children():
            widget.destroy()

        # Create game UI
        self.create_widgets()

    def create_widgets(self):
        """Create the game UI elements"""
        # Status label
        mode_text = "2 Player Mode" if self.game_mode == "player" else f"VS AI ({self.ai_difficulty.capitalize()})"
        status_text = f"Player {self.current_player}'s turn" if self.game_mode == "player" else "Your turn (X)"

        self.mode_label = tk.Label(
            self.root,
            text=mode_text,
            font=("Arial", 12),
            bg="#2c3e50",
            fg="#95a5a6",
            pady=5
        )
        self.mode_label.pack(fill=tk.X)

        self.status_label = tk.Label(
            self.root,
            text=status_text,
            font=("Arial", 16, "bold"),
            bg="#2c3e50",
            fg="white",
            pady=10
        )
        self.status_label.pack(fill=tk.X)

        # Game board frame
        board_frame = tk.Frame(self.root, bg="#34495e")
        board_frame.pack(padx=10, pady=10)

        # Create 3x3 grid of buttons
        self.buttons = []
        for i in range(9):
            button = tk.Button(
                board_frame,
                text="",
                font=("Arial", 32, "bold"),
                width=5,
                height=2,
                bg="#ecf0f1",
                fg="#2c3e50",
                activebackground="#bdc3c7",
                command=lambda idx=i: self.make_move(idx)
            )
            row = i // 3
            col = i % 3
            button.grid(row=row, column=col, padx=2, pady=2)
            self.buttons.append(button)

        # Control buttons frame
        control_frame = tk.Frame(self.root, bg="#2c3e50")
        control_frame.pack(fill=tk.X, padx=10, pady=5)

        # New Game button
        new_game_btn = tk.Button(
            control_frame,
            text="New Game",
            font=("Arial", 12, "bold"),
            bg="#27ae60",
            fg="white",
            activebackground="#229954",
            command=self.reset_game,
            padx=20,
            pady=5
        )
        new_game_btn.pack(side=tk.LEFT, padx=5)

        # Quit button
        quit_btn = tk.Button(
            control_frame,
            text="Quit",
            font=("Arial", 12, "bold"),
            bg="#e74c3c",
            fg="white",
            activebackground="#c0392b",
            command=self.root.quit,
            padx=20,
            pady=5
        )
        quit_btn.pack(side=tk.RIGHT, padx=5)

        # Set window background
        self.root.configure(bg="#2c3e50")

    def make_move(self, index: int):
        """Handle a player's move"""
        if self.game_over or self.board[index] != "":
            return

        # Play move sound
        self.play_sound("move")

        # Place the mark
        self.board[index] = self.current_player
        self.buttons[index].config(
            text=self.current_player,
            fg="#e74c3c" if self.current_player == "X" else "#3498db",
            state="disabled"
        )

        # Check for winner or draw
        if self.check_winner():
            self.game_over = True
            win_text = "You win!" if self.game_mode == "ai" and self.current_player == "X" else f"Player {self.current_player} wins!"

            # Play appropriate win/lose sound
            if self.game_mode == "ai":
                if self.current_player == "X":
                    self.play_sound("win")
                else:
                    self.play_sound("lose")
            else:
                self.play_sound("win")

            self.status_label.config(text=win_text)
            self.highlight_winning_line()
            messagebox.showinfo("Game Over", win_text)
        elif self.check_draw():
            self.game_over = True
            self.play_sound("draw")
            self.status_label.config(text="It's a draw!")
            messagebox.showinfo("Game Over", "It's a draw!")
        else:
            # Switch player
            self.current_player = "O" if self.current_player == "X" else "X"

            # Update status based on mode
            if self.game_mode == "player":
                self.status_label.config(text=f"Player {self.current_player}'s turn")
            else:
                if self.current_player == self.ai_symbol:
                    self.status_label.config(text="AI is thinking...")
                    # AI makes move after short delay
                    self.root.after(500, self.ai_move)
                else:
                    self.status_label.config(text="Your turn (X)")

    def check_winner(self) -> bool:
        """Check if current player has won"""
        # All possible winning combinations
        winning_combos = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Rows
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Columns
            [0, 4, 8], [2, 4, 6]              # Diagonals
        ]

        for combo in winning_combos:
            if (self.board[combo[0]] == self.board[combo[1]] ==
                self.board[combo[2]] == self.current_player):
                self.winning_combo = combo
                return True
        return False

    def check_draw(self) -> bool:
        """Check if the game is a draw"""
        return all(cell != "" for cell in self.board)

    def highlight_winning_line(self):
        """Highlight the winning combination"""
        for idx in self.winning_combo:
            self.buttons[idx].config(bg="#f39c12")

    def ai_move(self):
        """Make AI move based on difficulty"""
        if self.game_over:
            return

        if self.ai_difficulty == "easy":
            move = self.easy_ai_move()
        elif self.ai_difficulty == "medium":
            move = self.medium_ai_move()
        else:  # hard
            move = self.hard_ai_move()

        if move is not None:
            self.make_move(move)

    def get_available_moves(self):
        """Get list of available move indices"""
        return [i for i in range(9) if self.board[i] == ""]

    def easy_ai_move(self):
        """Easy AI: Random moves"""
        available = self.get_available_moves()
        return random.choice(available) if available else None

    def medium_ai_move(self):
        """Medium AI: 50% chance of best move, 50% random"""
        if random.random() < 0.5:
            return self.hard_ai_move()
        else:
            return self.easy_ai_move()

    def hard_ai_move(self):
        """Hard AI: Unbeatable using minimax"""
        best_score = float('-inf')
        best_move = None

        for move in self.get_available_moves():
            # Try the move
            self.board[move] = self.ai_symbol
            score = self.minimax(0, False)
            self.board[move] = ""

            if score > best_score:
                best_score = score
                best_move = move

        return best_move

    def minimax(self, depth, is_maximizing):
        """Minimax algorithm for optimal play"""
        # Check terminal states
        if self.check_winner_for_symbol(self.ai_symbol):
            return 10 - depth
        if self.check_winner_for_symbol(self.player_symbol):
            return depth - 10
        if self.check_draw():
            return 0

        if is_maximizing:
            best_score = float('-inf')
            for move in self.get_available_moves():
                self.board[move] = self.ai_symbol
                score = self.minimax(depth + 1, False)
                self.board[move] = ""
                best_score = max(score, best_score)
            return best_score
        else:
            best_score = float('inf')
            for move in self.get_available_moves():
                self.board[move] = self.player_symbol
                score = self.minimax(depth + 1, True)
                self.board[move] = ""
                best_score = min(score, best_score)
            return best_score

    def check_winner_for_symbol(self, symbol):
        """Check if a specific symbol has won"""
        winning_combos = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Rows
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Columns
            [0, 4, 8], [2, 4, 6]              # Diagonals
        ]

        for combo in winning_combos:
            if (self.board[combo[0]] == self.board[combo[1]] ==
                self.board[combo[2]] == symbol):
                return True
        return False

    def reset_game(self):
        """Reset the game to initial state"""
        self.current_player = "X"
        self.board = [""] * 9
        self.game_over = False
        self.winning_combo = None

        # Reset all buttons
        for button in self.buttons:
            button.config(
                text="",
                state="normal",
                bg="#ecf0f1",
                fg="#2c3e50"
            )

        # Reset status
        if self.game_mode == "player":
            self.status_label.config(text=f"Player {self.current_player}'s turn")
        else:
            self.status_label.config(text="Your turn (X)")


def main():
    """Main entry point"""
    root = tk.Tk()
    game = TicTacToe(root)

    # Center window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"+{x}+{y}")

    root.mainloop()


if __name__ == "__main__":
    main()
