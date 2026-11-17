import pytest

from sudoku import logic as sudoku_logic

UNIQUE_PUZZLE = [
    [5, 3, 0, 0, 7, 0, 0, 0, 0],
    [6, 0, 0, 1, 9, 5, 0, 0, 0],
    [0, 9, 8, 0, 0, 0, 0, 6, 0],
    [8, 0, 0, 0, 6, 0, 0, 0, 3],
    [4, 0, 0, 8, 0, 3, 0, 0, 1],
    [7, 0, 0, 0, 2, 0, 0, 0, 6],
    [0, 6, 0, 0, 0, 0, 2, 8, 0],
    [0, 0, 0, 4, 1, 9, 0, 0, 5],
    [0, 0, 0, 0, 8, 0, 0, 7, 9],
]

UNIQUE_SOLUTION = [
    [5, 3, 4, 6, 7, 8, 9, 1, 2],
    [6, 7, 2, 1, 9, 5, 3, 4, 8],
    [1, 9, 8, 3, 4, 2, 5, 6, 7],
    [8, 5, 9, 7, 6, 1, 4, 2, 3],
    [4, 2, 6, 8, 5, 3, 7, 9, 1],
    [7, 1, 3, 9, 2, 4, 8, 5, 6],
    [9, 6, 1, 5, 3, 7, 2, 8, 4],
    [2, 8, 7, 4, 1, 9, 6, 3, 5],
    [3, 4, 5, 2, 8, 6, 1, 7, 9],
]


def assert_valid_solution(board):
    expected = set(range(1, sudoku_logic.SIZE + 1))

    assert len(board) == sudoku_logic.SIZE
    assert all(len(row) == sudoku_logic.SIZE for row in board)
    assert all(set(row) == expected for row in board)
    assert all(
        {board[row][col] for row in range(sudoku_logic.SIZE)} == expected
        for col in range(sudoku_logic.SIZE)
    )
    for box_row in range(0, sudoku_logic.SIZE, 3):
        for box_col in range(0, sudoku_logic.SIZE, 3):
            box = {
                board[row][col]
                for row in range(box_row, box_row + 3)
                for col in range(box_col, box_col + 3)
            }
            assert box == expected


def create_unsolvable_puzzle():
    puzzle = [row[:] for row in UNIQUE_PUZZLE]
    puzzle[0][2] = 1
    return puzzle


def test_create_empty_board_returns_independent_nine_by_nine_grid():
    board = sudoku_logic.create_empty_board()

    expected = [
        [sudoku_logic.EMPTY] * sudoku_logic.SIZE
        for _ in range(sudoku_logic.SIZE)
    ]
    assert board == expected
    board[0][0] = 1
    assert board[1][0] == sudoku_logic.EMPTY


def test_deep_copy_does_not_share_nested_rows():
    board = sudoku_logic.create_empty_board()

    copied_board = sudoku_logic.deep_copy(board)
    copied_board[0][0] = 1

    assert board[0][0] == sudoku_logic.EMPTY


@pytest.mark.parametrize(
    ("row", "col", "existing_row", "existing_col"),
    [
        (0, 1, 0, 0),
        (1, 0, 0, 0),
        (1, 1, 0, 0),
    ],
)
def test_is_safe_rejects_values_already_in_row_column_or_box(
    row, col, existing_row, existing_col
):
    board = sudoku_logic.create_empty_board()
    board[existing_row][existing_col] = 5

    assert not sudoku_logic.is_safe(board, row, col, 5)


def test_is_safe_accepts_value_not_present_in_related_cells():
    board = sudoku_logic.create_empty_board()
    board[0][0] = 5

    assert sudoku_logic.is_safe(board, 4, 4, 5)


@pytest.mark.parametrize(
    "positions",
    [
        [(0, 0), (0, 1)],
        [(0, 0), (1, 0)],
        [(0, 0), (1, 1)],
    ],
)
def test_find_conflicts_identifies_duplicate_cells(positions):
    board = sudoku_logic.create_empty_board()
    for row, col in positions:
        board[row][col] = 5

    assert sudoku_logic.find_conflicts(board) == [list(cell) for cell in positions]


def test_find_hint_only_returns_an_original_and_currently_empty_cell():
    puzzle = [row[:] for row in UNIQUE_SOLUTION]
    puzzle[0][0] = sudoku_logic.EMPTY
    puzzle[0][1] = sudoku_logic.EMPTY
    board = [row[:] for row in puzzle]
    board[0][1] = UNIQUE_SOLUTION[0][1]

    hint = sudoku_logic.find_hint(puzzle, UNIQUE_SOLUTION, board)

    assert hint == (0, 0, UNIQUE_SOLUTION[0][0])


def test_find_hint_returns_none_when_no_empty_cells_are_available():
    assert sudoku_logic.find_hint(
        UNIQUE_SOLUTION,
        UNIQUE_SOLUTION,
        UNIQUE_SOLUTION,
    ) is None


def test_fill_board_completes_a_valid_solution():
    board = sudoku_logic.create_empty_board()

    assert sudoku_logic.fill_board(board)
    assert_valid_solution(board)


def test_solve_board_solves_puzzle_without_mutating_input():
    puzzle = [row[:] for row in UNIQUE_PUZZLE]

    solution = sudoku_logic.solve_board(puzzle)

    assert solution == UNIQUE_SOLUTION
    assert puzzle == UNIQUE_PUZZLE


def test_count_solutions_finds_unique_solution():
    assert sudoku_logic.count_solutions(UNIQUE_PUZZLE) == 1


def test_count_solutions_accepts_immutable_board_rows():
    immutable_puzzle = tuple(tuple(row) for row in UNIQUE_PUZZLE)

    assert sudoku_logic.count_solutions(immutable_puzzle) == 1


def test_count_solutions_stops_at_limit_for_underconstrained_board():
    assert sudoku_logic.count_solutions(sudoku_logic.create_empty_board()) == 2


def test_count_solutions_rejects_unsolvable_board_without_direct_conflicts():
    unsolvable_puzzle = create_unsolvable_puzzle()

    assert sudoku_logic.find_conflicts(unsolvable_puzzle) == []
    assert sudoku_logic.count_solutions(unsolvable_puzzle) == 0
    assert sudoku_logic.solve_board(unsolvable_puzzle) is None


def test_count_solutions_rejects_conflicting_board():
    invalid_board = [row[:] for row in UNIQUE_SOLUTION]
    invalid_board[0][0] = invalid_board[0][1]

    assert sudoku_logic.count_solutions(invalid_board) == 0
    assert sudoku_logic.solve_board(invalid_board) is None


@pytest.mark.parametrize("clues", [0, 16, 82])
def test_generate_puzzle_rejects_impossible_clue_counts(clues):
    with pytest.raises(ValueError):
        sudoku_logic.generate_puzzle(clues)


def test_remove_cells_preserves_unique_solution():
    puzzle = [row[:] for row in UNIQUE_SOLUTION]

    sudoku_logic.remove_cells(puzzle, clues=80)

    assert sum(value != sudoku_logic.EMPTY for row in puzzle for value in row) == 80
    assert sudoku_logic.count_solutions(puzzle) == 1


@pytest.mark.parametrize(
    "puzzle",
    [
        pytest.param(create_unsolvable_puzzle(), id="no-solution"),
        pytest.param(
            sudoku_logic.create_empty_board(),
            id="multiple-solutions",
        ),
    ],
)
def test_remove_cells_rejects_puzzles_without_exactly_one_solution(puzzle):
    with pytest.raises(RuntimeError, match="unique puzzle"):
        sudoku_logic.remove_cells([row[:] for row in puzzle], clues=81)


def test_generate_puzzle_returns_requested_clues_and_valid_solution():
    clues = 35

    puzzle, solution = sudoku_logic.generate_puzzle(clues)

    assert_valid_solution(solution)
    assert sum(value != sudoku_logic.EMPTY for row in puzzle for value in row) == clues
    assert sudoku_logic.count_solutions(puzzle) == 1
    assert all(
        value == sudoku_logic.EMPTY or value == solution[row][col]
        for row, values in enumerate(puzzle)
        for col, value in enumerate(values)
    )
