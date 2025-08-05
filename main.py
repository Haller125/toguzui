# toguzkumalak_ui.py
"""
Minimal OOP‑style GUI skeleton for playing Toguz Kumalak against your own
engine, built with PySimpleGUI.

The focus is on the UI.  The actual game rules / AI are intentionally left as
place‑holders so you can plug in your existing implementation later.

Key features
------------
* **Board pane (≈ 70 % width, left)** – drawn on a `sg.Graph`, automatically
  resizes with the window.  Clickable pits (2×9) plus kazans (stores).
* **Move history pane (≈ 30 %, right)** – a two‑column `sg.Table`.
  Clicking a row rewinds the position to the chosen ply.
* **Clean OOP separation** – `ToguzBoard`, `MoveHistory`, and `GameUI` keep GUI
  logic, game state, and history separate.
* **Stub AI hooks** – just replace `self.engine_choice()` with calls to your
  own engine.

PySimpleGUI >= 4.60 is recommended.
"""

from __future__ import annotations

import copy
import sys
from dataclasses import dataclass, field
from typing import List, Tuple

try:
    import PySimpleGUI as sg
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    sg = None  # type: ignore[assignment]


# ──────────────────────────────────────────────────────────────────────────────
#  Game‑state helpers (SKELETON ― plug your own implementation here)
# ──────────────────────────────────────────────────────────────────────────────


@dataclass
class ToguzBoard:
    """Lightweight board model holding pit counts and kazans.

    Indexing convention (feel free to change):
        pits[0‥8]   – bottom row, left‑to‑right from the current player’s side
        pits[9‥17]  – top row, right‑to‑left (mirrored for natural display)
    """

    pits: List[int] = field(default_factory=lambda: [9] * 18)
    kazans: Tuple[int, int] = (0, 0)  # (current player, opponent)
    turn: int = 0  # 0 = Bottom side to move, 1 = Top side

    # ─────────── placeholders ───────────
    def generate_legal_moves(self) -> List[int]:
        """Return list of pit indices that represent legal moves."""
        # TODO: implement real rules
        return [i for i in range(9) if self.pits[i] > 0] if self.turn == 0 else [
            i for i in range(9, 18) if self.pits[i] > 0
        ]

    def apply_move(self, pit_index: int) -> "ToguzBoard":
        """Return *new* board after play ― **does not mutate self**."""
        # TODO: implement sowing & capture rules
        new_board = copy.deepcopy(self)
        new_board.turn ^= 1
        # Very naïve placeholder mechanics
        new_board.pits[pit_index] = 0
        return new_board

    # Convenience helpers -----------------------------------------------------
    def copy(self) -> "ToguzBoard":
        return copy.deepcopy(self)


@dataclass
class MoveRecord:
    ply: int
    notation: str
    board_snapshot: ToguzBoard


class MoveHistory:
    """Keeps a chronological list of `MoveRecord`s and exposes Table‑friendly
    views."""

    def __init__(self):
        self._records: List[MoveRecord] = []

    # API ---------------------------------------------------------------------
    def add(self, notation: str, board_snapshot: ToguzBoard) -> None:
        self._records.append(
            MoveRecord(len(self._records) + 1, notation, board_snapshot.copy())
        )

    def rewind_to(self, ply: int) -> ToguzBoard:
        """Return the board *before* the given ply (1‑based)."""
        if ply == 0:
            return ToguzBoard()
        return self._records[ply - 1].board_snapshot.copy()

    # Table helpers -----------------------------------------------------------
    @property
    def headings(self):
        return ["#", "Move"]

    def as_table(self):
        return [[rec.ply, rec.notation] for rec in self._records]


# ──────────────────────────────────────────────────────────────────────────────
#  User Interface (PySimpleGUI)
# ──────────────────────────────────────────────────────────────────────────────


class GameUI:
    BOARD_BG = "#EEE0CB"
    PIT_BG = "#9F6F43"
    TEXT_COL = "#000000"

    def __init__(self):
        if sg is None:  # pragma: no cover - defensive guard
            raise ImportError("PySimpleGUI is required to use GameUI")

        self.board_area: sg.Graph
        self.table: sg.Table
        self.window: sg.Window

        self.board_model = ToguzBoard()
        self.history = MoveHistory()

        self._setup_layout()
        self._draw_board()

    # Layout ------------------------------------------------------------------
    def _setup_layout(self):
        sg.theme("SystemDefault")

        # Left: Graph for the pits
        self.board_area = sg.Graph(
            canvas_size=(700, 400),
            graph_bottom_left=(0, 0),
            graph_top_right=(700, 400),
            background_color=self.BOARD_BG,
            enable_events=True,
            key="-BOARD-",
        )

        # Right: Move table
        self.table = sg.Table(
            values=[],
            headings=self.history.headings,
            auto_size_columns=False,
            col_widths=[4, 12],
            justification="center",
            alternating_row_color="#F2F2F2",
            enable_events=True,
            max_col_width=100,
            key="-TABLE-",
            expand_y=True,
        )

        left_col = sg.Column([[self.board_area]], expand_x=True, expand_y=True)
        right_col = sg.Column([[self.table]], expand_y=True)

        layout = [
            [left_col, right_col],
        ]

        self.window = sg.Window(
            "Toguz Kumalak", layout, resizable=True, finalize=True, element_justification="center"
        )

        # Make right column ~30 % width
        total_width = self.window.size[0]
        self.window["-TABLE-"].Widget.master.config(width=int(total_width * 0.3))

    # Board drawing -----------------------------------------------------------
    def _draw_board(self):
        g = self.board_area
        g.erase()

        w, h = g.get_size()
        pit_r = min(w / 18, h / 4) * 0.9  # radius heuristics

        def draw_pit(idx: int, x: float, y: float, count: int):
            g.draw_circle((x, y), pit_r, fill_color=self.PIT_BG, line_color="black", line_width=2)
            g.draw_text(str(count), (x, y), color=self.TEXT_COL, font=("Helvetica", int(pit_r)))

        # Bottom row (current player side)
        for i in range(9):
            cx = (i + 0.5) * 2 * pit_r
            cy = pit_r * 1.5
            draw_pit(i, cx, cy, self.board_model.pits[i])

        # Top row (opponent side) – reversed for natural orientation
        for i in range(9):
            cx = (8 - i + 0.5) * 2 * pit_r
            cy = h - pit_r * 1.5
            draw_pit(9 + i, cx, cy, self.board_model.pits[9 + i])

        # Kazans (stores)
        g.draw_rectangle((w - 2.5 * pit_r, h / 2 - 2 * pit_r), (w - 0.5 * pit_r, h / 2 + 2 * pit_r), fill_color="#D4C09B", line_color="black", line_width=2)
        g.draw_text(str(self.board_model.kazans[0]), (w - 1.5 * pit_r, h / 2 + pit_r * 1.2), font=("Helvetica", int(pit_r * 0.9)))
        g.draw_text(str(self.board_model.kazans[1]), (w - 1.5 * pit_r, h / 2 - pit_r * 1.2), font=("Helvetica", int(pit_r * 0.9)))

    def _screen_to_pit(self, x: int, y: int) -> int | None:
        """Return pit index if click is inside a pit, else None."""
        w, h = self.board_area.get_size()
        pit_r = min(w / 18, h / 4) * 0.9

        # Bottom row detection
        for i in range(9):
            cx = (i + 0.5) * 2 * pit_r
            cy = pit_r * 1.5
            if (x - cx) ** 2 + (y - cy) ** 2 <= pit_r ** 2:
                return i
        # Top row
        for i in range(9):
            cx = (8 - i + 0.5) * 2 * pit_r
            cy = h - pit_r * 1.5
            if (x - cx) ** 2 + (y - cy) ** 2 <= pit_r ** 2:
                return 9 + i
        return None

    # History helpers ---------------------------------------------------------
    def _push_history(self, move_notation: str):
        self.history.add(move_notation, self.board_model)
        self.table.update(values=self.history.as_table())

    # Engine stub -------------------------------------------------------------
    def _engine_move(self):
        """Very naïve AI placeholder – just picks first legal move."""
        legal = self.board_model.generate_legal_moves()
        if not legal:
            sg.popup("Game over!", keep_on_top=True)
            return
        chosen = legal[0]
        self._apply_move(chosen, by_engine=True)

    # Generic move application ------------------------------------------------
    def _apply_move(self, pit_index: int, by_engine: bool = False):
        move_str = f"{'AI' if by_engine else 'P'}:{pit_index + 1}"
        self.board_model = self.board_model.apply_move(pit_index)
        self._push_history(move_str)
        self._draw_board()

        # If player move ― launch AI reply
        if not by_engine:
            self._engine_move()

    # Main loop ---------------------------------------------------------------
    def run(self):
        while True:
            event, values = self.window.read(timeout=100)
            if event in (sg.WINDOW_CLOSED, "Exit"):
                break

            # Click on board
            if event == "-BOARD-":
                x, y = values["-BOARD-"]
                pit = self._screen_to_pit(x, y)
                if pit is not None and pit in self.board_model.generate_legal_moves():
                    self._apply_move(pit)

            # Click on move table -> rewind
            if event == "-TABLE-" and values["-TABLE-"]:
                row_idx = values["-TABLE-"][0]
                self.board_model = self.history.rewind_to(row_idx)
                # Trim history to that ply
                self.history._records = self.history._records[:row_idx]
                self.table.update(values=self.history.as_table())
                self._draw_board()

        self.window.close()


# ──────────────────────────────────────────────────────────────────────────────
#  Script entry point
# ──────────────────────────────────────────────────────────────────────────────

def main():
    if sg is None:  # pragma: no cover - defensive guard
        raise ImportError("PySimpleGUI is required to run the GUI")
    ui = GameUI()
    ui.run()


if __name__ == "__main__":
    if sys.version_info < (3, 9):
        if sg is not None:
            sg.popup_error("Python 3.9+ is required.")
        else:
            print("Python 3.9+ is required.", file=sys.stderr)
        sys.exit(1)
    if sg is None:
        print("PySimpleGUI is required to run this application.", file=sys.stderr)
        sys.exit(1)
    main()
