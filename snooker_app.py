import tkinter as tk
from tkinter import messagebox, simpledialog
from enum import Enum


class ColorButton(tk.Frame):

    def __init__(self, parent, *, text, command, bg, fg, font, width, height=1):
        super().__init__(parent, bg=bg, highlightthickness=2,
                         highlightbackground="#303030", cursor="hand2")
        self.command = command
        self.normal_bg = bg
        self.normal_fg = fg
        self.state = "normal"
        self.label = tk.Label(
            self, text=text, font=font, width=width, height=height,
            bg=bg, fg=fg, justify="center", cursor="hand2"
        )
        self.label.pack(padx=3, pady=3)
        for widget in (self, self.label):
            widget.bind("<Button-1>", self._click)
            widget.bind("<Enter>", self._enter)
            widget.bind("<Leave>", self._leave)

    def _click(self, _event=None):
        if self.state == "normal":
            self.command()

    def _enter(self, _event=None):
        if self.state == "normal":
            self.label.config(relief="raised", bd=1)

    def _leave(self, _event=None):
        self.label.config(relief="flat", bd=0)

    def config(self, cnf=None, **kwargs):
        """Support the ``state`` update used by ``update_display``."""
        if cnf:
            kwargs.update(cnf)
        if "state" in kwargs:
            self.state = kwargs.pop("state")
            if self.state == "disabled":
                bg, fg, cursor = "#59636A", "#C8CDD0", ""
            else:
                bg, fg, cursor = self.normal_bg, self.normal_fg, "hand2"
            self.config(bg=bg, cursor=cursor)
            self.label.config(bg=bg, fg=fg, cursor=cursor)
        if "text" in kwargs:
            self.label.config(text=kwargs.pop("text"))
        if kwargs:
            super().config(**kwargs)

    configure = config


class Ball(Enum):
    """Snooker balls with point values, colors, and styling."""
    RED = ("Red", 1, "#FF1900", "white")
    YELLOW = ("Yellow", 2, "#FFCC00", "black")
    GREEN = ("Green", 3, "#00FF6A", "black")
    BROWN = ("Brown", 4, "#8B4513", "white")
    BLUE = ("Blue", 5, "#0044FF", "white")
    PINK = ("Pink", 6, "#F700FF", "black")
    BLACK = ("Black", 7, "#17202A", "white")

    def __init__(self, color_name, points, bg, fg):
        self.color_name = color_name
        self.points = points
        self.bg = bg
        self.fg = fg


# Official order of colors during the final clearance phase
CLEARANCE_ORDER = [
    Ball.YELLOW,
    Ball.GREEN,
    Ball.BROWN,
    Ball.BLUE,
    Ball.PINK,
    Ball.BLACK
]


class SnookerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Snooker Score Counter & Rule Engine")
        self.root.geometry("800x750")
        self.root.configure(bg="#1E272C")

        # --- Game State Variables ---
        self.p1_name = "Player 1"
        self.p2_name = "Player 2"
        self.p1_score = 0
        self.p2_score = 0

        self.active_player = 1  # 1 or 2
        self.current_break = 0
        self.reds_remaining = 15

        # Target Logic: 'RED', 'ANY_COLOR', or a specific Ball during clearance
        self.target = 'RED'
        self.clearance_index = 0
        self.game_over = False

        self.setup_ui()
        self.update_display()

    def setup_ui(self):
        """Builds the graphical user interface."""
        # 1. Header Title
        title_label = tk.Label(
            self.root, 
            text="SNOOKER MATCH SCOREBOARD", 
            font=("Helvetica", 18, "bold"), 
            bg="#1E272C", 
            fg="#ECF0F1"
        )
        title_label.pack(pady=15)

        # 2. Scoreboard Cards Frame
        score_frame = tk.Frame(self.root, bg="#1E272C")
        score_frame.pack(fill="x", padx=30, pady=10)

        # Player 1 Display Card
        self.p1_card = tk.Frame(score_frame, bg="#2C3E50", bd=3, relief="groove")
        self.p1_card.pack(side="left", expand=True, fill="both", padx=10)

        self.p1_name_lbl = tk.Label(self.p1_card, text=self.p1_name, font=("Helvetica", 14, "bold"), bg="#2C3E50", fg="white")
        self.p1_name_lbl.pack(pady=5)

        self.p1_score_lbl = tk.Label(self.p1_card, text="0", font=("Helvetica", 36, "bold"), bg="#2C3E50", fg="#3498DB")
        self.p1_score_lbl.pack(pady=5)

        self.p1_turn_lbl = tk.Label(self.p1_card, text="[ IN HAND ]", font=("Helvetica", 10, "bold"), bg="#2C3E50", fg="#2ECC71")
        self.p1_turn_lbl.pack(pady=5)

        # Player 2 Display Card
        self.p2_card = tk.Frame(score_frame, bg="#2C3E50", bd=3, relief="groove")
        self.p2_card.pack(side="right", expand=True, fill="both", padx=10)

        self.p2_name_lbl = tk.Label(self.p2_card, text=self.p2_name, font=("Helvetica", 14, "bold"), bg="#2C3E50", fg="white")
        self.p2_name_lbl.pack(pady=5)

        self.p2_score_lbl = tk.Label(self.p2_card, text="0", font=("Helvetica", 36, "bold"), bg="#2C3E50", fg="#E74C3C")
        self.p2_score_lbl.pack(pady=5)

        self.p2_turn_lbl = tk.Label(self.p2_card, text="", font=("Helvetica", 10, "bold"), bg="#2C3E50", fg="#2ECC71")
        self.p2_turn_lbl.pack(pady=5)

        # 3. Match Status Info Panel
        status_frame = tk.Frame(self.root, bg="#34495E", bd=2, relief="ridge")
        status_frame.pack(fill="x", padx=40, pady=15)

        self.break_lbl = tk.Label(status_frame, text="Current Break: 0", font=("Helvetica", 13, "bold"), bg="#34495E", fg="#F1C40F")
        self.break_lbl.grid(row=0, column=0, padx=20, pady=8)

        self.reds_lbl = tk.Label(status_frame, text="Reds Left: 15", font=("Helvetica", 13, "bold"), bg="#34495E", fg="white")
        self.reds_lbl.grid(row=0, column=1, padx=20, pady=8)

        self.target_lbl = tk.Label(status_frame, text="Next Target: RED", font=("Helvetica", 13, "bold"), bg="#34495E", fg="#2ECC71")
        self.target_lbl.grid(row=0, column=2, padx=20, pady=8)

        # 4. Ball Potting Controls Section
        balls_frame = tk.LabelFrame(self.root, text=" Pot Ball ", font=("Helvetica", 12, "bold"), bg="#1E272C", fg="white", bd=2)
        balls_frame.pack(fill="x", padx=40, pady=10)

        btn_container = tk.Frame(balls_frame, bg="#1E272C")
        btn_container.pack(pady=10)

        self.ball_buttons = {}
        for ball in Ball:
            btn = ColorButton(
                btn_container,
                text=f"{ball.color_name}\n({ball.points})",
                font=("Helvetica", 10, "bold"),
                bg=ball.bg,
                fg=ball.fg,
                width=8,
                height=2,
                command=lambda b=ball: self.handle_pot(b)
            )
            btn.pack(side="left", padx=5)
            self.ball_buttons[ball] = btn

        # 5. Game Actions & Foul Controls
        actions_frame = tk.Frame(self.root, bg="#1E272C")
        actions_frame.pack(fill="x", padx=40, pady=15)

        end_turn_btn = ColorButton(
            actions_frame, text="End Turn / Miss", font=("Helvetica", 11, "bold"), 
            bg="#95A5A6", fg="black", width=18, command=self.end_turn
        )
        end_turn_btn.pack(side="left", padx=10)

        foul_btn = ColorButton(
            actions_frame, text="Record Foul ⚠️", font=("Helvetica", 11, "bold"), 
            bg="#E67E22", fg="white", width=18, command=self.open_foul_dialog
        )
        foul_btn.pack(side="left", padx=10)

        reset_btn = ColorButton(
            actions_frame, text="Reset Frame", font=("Helvetica", 11, "bold"), 
            bg="#C0392B", fg="white", width=18, command=self.reset_match
        )
        reset_btn.pack(side="right", padx=10)

    # --- Rule Engine Core Logic ---

    def handle_pot(self, ball: Ball):
        """Processes ball pots strictly following snooker rules."""
        if self.game_over:
            messagebox.showinfo("Frame Ended", "The frame is already completed!")
            return

        # 1. Red Phase Logic
        if self.reds_remaining > 0:
            if self.target == 'RED':
                if ball != Ball.RED:
                    messagebox.showerror("Illegal Shot", "Target is RED! Potting a color now is a foul.")
                    return
                # Successful Red pot
                self.award_points(ball.points)
                self.reds_remaining -= 1
                self.target = 'ANY_COLOR'

            elif self.target == 'ANY_COLOR':
                if ball == Ball.RED:
                    messagebox.showerror("Illegal Shot", "Target is a COLOR! Cannot pot another Red consecutively.")
                    return
                # Successful Color pot
                self.award_points(ball.points)
                if self.reds_remaining > 0:
                    self.target = 'RED'
                else:
                    # Transition to Final Color Clearance Phase
                    self.target = CLEARANCE_ORDER[0]
                    self.clearance_index = 0

        # 2. Final Color Clearance Phase Logic
        else:
            expected_ball = CLEARANCE_ORDER[self.clearance_index]
            if ball != expected_ball:
                messagebox.showerror("Illegal Shot", f"Sequence error! Next target must be {expected_ball.color_name}.")
                return

            self.award_points(ball.points)
            self.clearance_index += 1

            if self.clearance_index < len(CLEARANCE_ORDER):
                self.target = CLEARANCE_ORDER[self.clearance_index]
            else:
                # Frame Finished (All balls cleared)
                self.game_over = True
                self.target = "CLEARED"
                self.check_winner()

        self.update_display()

    def award_points(self, points: int):
        """Adds points to active player score and break counter."""
        if self.active_player == 1:
            self.p1_score += points
        else:
            self.p2_score += points
        self.current_break += points

    def end_turn(self):
        """Ends current player's turn on a safe shot or miss."""
        if self.game_over:
            return

        self.current_break = 0
        self.active_player = 2 if self.active_player == 1 else 1

        # Reset target back to Red if reds remain on table
        if self.reds_remaining > 0:
            self.target = 'RED'

        self.update_display()

    def open_foul_dialog(self):
        """Handles fouls by awarding points to opponent based on foul rules."""
        if self.game_over:
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Record Foul Penalty")
        dialog.geometry("380x280")
        dialog.configure(bg="#2C3E50")
        dialog.grab_set()

        tk.Label(dialog, text="Select Foul Penalty Points:", font=("Helvetica", 12, "bold"), bg="#2C3E50", fg="white").pack(pady=10)

        fouled_player = self.active_player
        opponent = 2 if fouled_player == 1 else 1

        def apply_foul(penalty, red_potted=False):
            # Award penalty points to opponent
            if opponent == 1:
                self.p1_score += penalty
            else:
                self.p2_score += penalty

            # If a red ball was pocketed during the foul, permanently remove it from table
            if red_potted and self.reds_remaining > 0:
                self.reds_remaining -= 1

            dialog.destroy()
            
            # Ending turn after foul
            self.end_turn()

        # Standard Foul Options (Minimum penalty is 4 points)
        btn_frame = tk.Frame(dialog, bg="#2C3E50")
        btn_frame.pack(pady=10)

        for p in [4, 5, 6, 7]:
            ColorButton(
                btn_frame, text=f"+{p} Points", font=("Helvetica", 10, "bold"),
                width=8, bg="#E74C3C", fg="white",
                command=lambda pts=p: apply_foul(pts)
            ).pack(side="left", padx=5)

        # Checkbox for Red potted during foul
        red_var = tk.BooleanVar()
        chk = tk.Checkbutton(dialog, text="Was a Red potted during foul?", variable=red_var, font=("Helvetica", 10), bg="#2C3E50", fg="white", selectcolor="#1E272C")
        chk.pack(pady=15)

        confirm_btn = ColorButton(
            dialog, text="Apply Foul & Switch Turn", font=("Helvetica", 10, "bold"),
            bg="#2ECC71", fg="black", width=24,
            command=lambda: apply_foul(4, red_var.get())
        )
        confirm_btn.pack(pady=5)

    def update_display(self):
        """Updates UI scores, labels, and button enable/disable states."""
        self.p1_score_lbl.config(text=str(self.p1_score))
        self.p2_score_lbl.config(text=str(self.p2_score))
        self.break_lbl.config(text=f"Current Break: {self.current_break}")
        self.reds_lbl.config(text=f"Reds Left: {self.reds_remaining}")

        # Active player indicator
        if self.active_player == 1:
            self.p1_turn_lbl.config(text="[ IN HAND ]")
            self.p2_turn_lbl.config(text="")
            self.p1_card.config(bd=4, relief="ridge")
            self.p2_card.config(bd=1, relief="flat")
        else:
            self.p1_turn_lbl.config(text="")
            self.p2_turn_lbl.config(text="[ IN HAND ]")
            self.p1_card.config(bd=1, relief="flat")
            self.p2_card.config(bd=4, relief="ridge")

        # Target label formatting
        if isinstance(self.target, Ball):
            target_str = self.target.color_name.upper()
        else:
            target_str = str(self.target)
        self.target_lbl.config(text=f"Next Target: {target_str}")

        # --- Dynamic Button Enable/Disable Enforcement ---
        for ball, btn in self.ball_buttons.items():
            if self.game_over:
                btn.config(state="disabled")
            elif self.reds_remaining > 0:
                if self.target == 'RED':
                    btn.config(state="normal" if ball == Ball.RED else "disabled")
                elif self.target == 'ANY_COLOR':
                    btn.config(state="normal" if ball != Ball.RED else "disabled")
            else:
                # Color Clearance Phase
                if isinstance(self.target, Ball):
                    btn.config(state="normal" if ball == self.target else "disabled")

    def check_winner(self):
        """Determines winner at the conclusion of frame."""
        if self.p1_score > self.p2_score:
            winner_text = f"🎉 {self.p1_name} Wins the Frame! ({self.p1_score} - {self.p2_score})"
        elif self.p2_score > self.p1_score:
            winner_text = f"🎉 {self.p2_name} Wins the Frame! ({self.p2_score} - {self.p1_score})"
        else:
            winner_text = "Frame Tied! (Re-spotted Black required)"

        messagebox.showinfo("Frame Complete", winner_text)

    def reset_match(self):
        """Resets the match to starting status."""
        if messagebox.askyesno("Reset Frame", "Are you sure you want to reset the entire frame?"):
            self.p1_score = 0
            self.p2_score = 0
            self.active_player = 1
            self.current_break = 0
            self.reds_remaining = 15
            self.target = 'RED'
            self.clearance_index = 0
            self.game_over = False
            self.update_display()


if __name__ == "__main__":
    root = tk.Tk()
    app = SnookerApp(root)
    root.mainloop()
