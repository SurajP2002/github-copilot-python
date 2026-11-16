import copy
import random

SIZE = 9
EMPTY = 0
MINIMUM_UNIQUE_CLUES = 17
DIFFICULTY_CLUES = {"easy": 45, "medium": 35, "hard": 25}
MAX_GENERATION_ATTEMPTS = 50


def deep_copy(board):
    return copy.deepcopy(board)


def create_empty_board():
    return [[EMPTY for _ in range(SIZE)] for _ in range(SIZE)]


def is_safe(board, row, col, number):
    for index in range(SIZE):
        if board[row][index] == number or board[index][col] == number:
            return False

    start_row = row - row % 3
    start_col = col - col % 3
    for box_row in range(start_row, start_row + 3):
        for box_col in range(start_col, start_col + 3):
            if board[box_row][box_col] == number:
                return False
    return True


def fill_board(board):
    for row in range(SIZE):
        for col in range(SIZE):
            if board[row][col] == EMPTY:
                candidates = list(range(1, SIZE + 1))
                random.shuffle(candidates)
                for candidate in candidates:
                    if is_safe(board, row, col, candidate):
                        board[row][col] = candidate
                        if fill_board(board):
                            return True
                        board[row][col] = EMPTY
                return False
    return True


def is_well_formed_board(board):
    if not isinstance(board, (list, tuple)) or len(board) != SIZE:
        return False
    if any(not isinstance(row, (list, tuple)) or len(row) != SIZE for row in board):
        return False

    if any(
        type(value) is not int or value < EMPTY or value > SIZE
        for row in board
        for value in row
    ):
        return False
    return True


def _is_valid_board(board):
    if not is_well_formed_board(board):
        return False

    for row in range(SIZE):
        values = [value for value in board[row] if value != EMPTY]
        if len(values) != len(set(values)):
            return False

    for col in range(SIZE):
        values = [board[row][col] for row in range(SIZE)]
        values = [value for value in values if value != EMPTY]
        if len(values) != len(set(values)):
            return False

    for box_row in range(0, SIZE, 3):
        for box_col in range(0, SIZE, 3):
            values = [
                board[row][col]
                for row in range(box_row, box_row + 3)
                for col in range(box_col, box_col + 3)
                if board[row][col] != EMPTY
            ]
            if len(values) != len(set(values)):
                return False
    return True


def find_conflicts(board):
    if not is_well_formed_board(board):
        raise ValueError("Board must be a 9x9 grid containing numbers from 0 to 9.")

    units = [
        [(row, col) for col in range(SIZE)]
        for row in range(SIZE)
    ]
    units.extend(
        [(row, col) for row in range(SIZE)]
        for col in range(SIZE)
    )
    units.extend(
        [
            (row, col)
            for row in range(box_row, box_row + 3)
            for col in range(box_col, box_col + 3)
        ]
        for box_row in range(0, SIZE, 3)
        for box_col in range(0, SIZE, 3)
    )

    conflicting_cells = set()
    for unit in units:
        positions_by_number = {}
        for row, col in unit:
            number = board[row][col]
            if number == EMPTY:
                continue
            if number in positions_by_number:
                conflicting_cells.update(positions_by_number[number])
                conflicting_cells.add((row, col))
            else:
                positions_by_number[number] = [(row, col)]

    return [list(cell) for cell in sorted(conflicting_cells)]


def find_hint(puzzle, solution, board):
    if not all(
        is_well_formed_board(candidate)
        for candidate in (puzzle, solution, board)
    ):
        raise ValueError("Puzzle, solution, and board must be valid 9x9 grids.")

    available_cells = [
        (row, col)
        for row in range(SIZE)
        for col in range(SIZE)
        if puzzle[row][col] == EMPTY and board[row][col] == EMPTY
    ]
    if not available_cells:
        return None

    row, col = random.choice(available_cells)
    return row, col, solution[row][col]


def _find_most_constrained_cell(board):
    best_cell = None
    best_candidates = None

    for row in range(SIZE):
        for col in range(SIZE):
            if board[row][col] != EMPTY:
                continue

            candidates = [
                number
                for number in range(1, SIZE + 1)
                if is_safe(board, row, col, number)
            ]
            if not candidates:
                return row, col, []
            if best_candidates is None or len(candidates) < len(best_candidates):
                best_cell = row, col
                best_candidates = candidates
                if len(candidates) == 1:
                    return row, col, candidates

    if best_cell is None:
        return None
    return best_cell[0], best_cell[1], best_candidates


def _search_solutions(board, limit, first_solution=None):
    next_cell = _find_most_constrained_cell(board)
    if next_cell is None:
        if first_solution is not None:
            first_solution.append(deep_copy(board))
        return 1

    row, col, candidates = next_cell
    solution_count = 0
    for candidate in candidates:
        board[row][col] = candidate
        solution_count += _search_solutions(
            board,
            limit - solution_count,
            first_solution,
        )
        board[row][col] = EMPTY
        if solution_count >= limit:
            break
    return solution_count


def solve_board(board):
    """Return one completed board, or None if the input cannot be solved."""
    if not _is_valid_board(board):
        return None

    working_board = [list(row) for row in board]
    solutions = []
    _search_solutions(working_board, 1, solutions)
    return solutions[0] if solutions else None


def count_solutions(board, limit=2):
    """Count solutions up to limit; invalid boards have no solutions."""
    if not isinstance(limit, int) or limit < 1 or not _is_valid_board(board):
        return 0
    working_board = [list(row) for row in board]
    return _search_solutions(working_board, limit)


def remove_cells(board, clues):
    if not MINIMUM_UNIQUE_CLUES <= clues <= SIZE * SIZE:
        raise ValueError(
            "Clue count must be between "
            f"{MINIMUM_UNIQUE_CLUES} and {SIZE * SIZE}."
        )
    if count_solutions(board, limit=2) != 1:
        raise RuntimeError("Cells can only be removed from a unique puzzle.")

    remaining_clues = sum(value != EMPTY for row in board for value in row)
    if remaining_clues < clues:
        raise ValueError("The board does not contain enough clues.")
    cell_positions = [
        row * SIZE + col
        for row in range(SIZE)
        for col in range(SIZE)
        if board[row][col] != EMPTY
    ]
    random.shuffle(cell_positions)

    for position in cell_positions:
        if remaining_clues == clues:
            break

        row, col = divmod(position, SIZE)
        value = board[row][col]
        board[row][col] = EMPTY
        if count_solutions(board, limit=2) == 1:
            remaining_clues -= 1
        else:
            board[row][col] = value

    if remaining_clues != clues:
        raise RuntimeError(f"Unable to remove cells down to {clues} clues.")


def generate_puzzle(clues=35):
    if not MINIMUM_UNIQUE_CLUES <= clues <= SIZE * SIZE:
        raise ValueError(
            "Clue count must be between "
            f"{MINIMUM_UNIQUE_CLUES} and {SIZE * SIZE}."
        )

    for _ in range(MAX_GENERATION_ATTEMPTS):
        solution = create_empty_board()
        fill_board(solution)
        puzzle = deep_copy(solution)

        try:
            remove_cells(puzzle, clues)
        except RuntimeError:
            continue
        else:
            return puzzle, solution

    raise RuntimeError(f"Unable to generate a unique puzzle with {clues} clues.")
