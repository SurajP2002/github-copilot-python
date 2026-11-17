import pytest

import app as sudoku_app
from sudoku import create_app
from sudoku import logic as sudoku_logic


def test_app_factory_registers_blueprint_and_isolates_game_state():
    first_app = create_app()
    second_app = create_app()
    route_paths = {rule.rule for rule in first_app.url_map.iter_rules()}

    assert "sudoku" in first_app.blueprints
    assert {"/", "/new", "/check", "/validate", "/hint"} <= route_paths

    first_app.config["CURRENT_GAME"]["solution"] = sudoku_logic.create_empty_board()
    assert second_app.config["CURRENT_GAME"]["solution"] is None


@pytest.fixture
def client():
    sudoku_app.app.config.update(TESTING=True)
    current_game = sudoku_app.app.config["CURRENT_GAME"]
    current_game.update(puzzle=None, solution=None)
    with sudoku_app.app.test_client() as test_client:
        yield test_client
    current_game.update(puzzle=None, solution=None)


def test_index_route_renders_game_page(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"Sudoku Game" in response.data


@pytest.mark.parametrize(
    "asset",
    ["styles.css", "main.js", "leaderboard.mjs", "theme.mjs"],
)
def test_static_assets_are_available(client, asset):
    response = client.get(f"/static/{asset}")

    assert response.status_code == 200


@pytest.mark.parametrize(
    ("query_string", "expected_clues"),
    [
        ({}, 35),
        ({"difficulty": "easy"}, 45),
        ({"difficulty": "medium"}, 35),
        ({"difficulty": "hard"}, 25),
    ],
)
def test_new_game_route_generates_unique_puzzle_for_difficulty(
    client, query_string, expected_clues
):
    response = client.get("/new", query_string=query_string)

    assert response.status_code == 200
    puzzle = response.get_json()["puzzle"]
    solution = sudoku_app.app.config["CURRENT_GAME"]["solution"]

    assert len(puzzle) == sudoku_logic.SIZE
    assert all(len(row) == sudoku_logic.SIZE for row in puzzle)
    assert (
        sum(value != sudoku_logic.EMPTY for row in puzzle for value in row)
        == expected_clues
    )
    assert sudoku_logic.count_solutions(puzzle) == 1
    assert len(solution) == sudoku_logic.SIZE
    assert all(
        value == sudoku_logic.EMPTY or value == solution[row][col]
        for row, values in enumerate(puzzle)
        for col, value in enumerate(values)
    )


def test_new_game_route_rejects_unknown_difficulty(client):
    response = client.get("/new", query_string={"difficulty": "expert"})

    assert response.status_code == 400
    assert response.get_json() == {
        "error": "Difficulty must be easy, medium, or hard"
    }


@pytest.mark.parametrize(
    ("clue_count", "expected_status"),
    [("not-a-number", 400), ("16", 400), ("82", 400)],
)
def test_new_game_route_rejects_invalid_clue_count(
    client, clue_count, expected_status
):
    response = client.get("/new", query_string={"clues": clue_count})

    assert response.status_code == expected_status
    assert "error" in response.get_json()


def test_index_page_offers_all_difficulty_levels(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b'value="easy"' in response.data
    assert b'value="medium"' in response.data
    assert b'value="hard"' in response.data
    assert b'id="current-difficulty"' in response.data
    assert b"Current difficulty: Medium" in response.data
    assert b'id="timer"' in response.data
    assert b">00:00</span>" in response.data
    assert b'id="use-hint"' in response.data
    assert b'id="hints-used"' in response.data
    assert b">0</span>" in response.data
    assert b"Top 10 Fastest Times" in response.data
    assert b'id="player-name-dialog"' in response.data
    assert b'id="theme-toggle"' in response.data
    assert b'aria-pressed="false"' in response.data


def test_check_route_reports_error_when_no_game_is_in_progress(client):
    response = client.post("/check", json={"board": sudoku_logic.create_empty_board()})

    assert response.status_code == 400
    assert response.get_json() == {"error": "No game in progress"}


def test_validate_route_reports_incorrect_nonempty_entries(client):
    _, solution = sudoku_logic.generate_puzzle(clues=81)
    sudoku_app.app.config["CURRENT_GAME"]["solution"] = solution
    board = sudoku_logic.create_empty_board()
    board[0][0] = solution[0][0] % sudoku_logic.SIZE + 1

    response = client.post("/validate", json={"board": board})

    assert response.status_code == 200
    assert response.get_json() == {
        "incorrect": [[0, 0]],
        "conflicts": [],
        "solved": False,
    }


def test_validate_route_reports_conflicting_cells(client):
    _, solution = sudoku_logic.generate_puzzle(clues=81)
    sudoku_app.app.config["CURRENT_GAME"]["solution"] = solution
    board = sudoku_logic.create_empty_board()
    conflicting_value = next(
        value
        for value in range(1, sudoku_logic.SIZE + 1)
        if value not in (solution[0][0], solution[0][1])
    )
    board[0][0] = conflicting_value
    board[0][1] = conflicting_value

    response = client.post("/validate", json={"board": board})

    assert response.status_code == 200
    assert response.get_json() == {
        "incorrect": [[0, 0], [0, 1]],
        "conflicts": [[0, 0], [0, 1]],
        "solved": False,
    }


def test_validate_route_marks_a_complete_solution_as_solved(client):
    _, solution = sudoku_logic.generate_puzzle(clues=81)
    sudoku_app.app.config["CURRENT_GAME"]["solution"] = solution

    response = client.post("/validate", json={"board": solution})

    assert response.status_code == 200
    assert response.get_json() == {
        "incorrect": [],
        "conflicts": [],
        "solved": True,
    }


def test_validate_route_rejects_malformed_board(client):
    _, solution = sudoku_logic.generate_puzzle(clues=81)
    sudoku_app.app.config["CURRENT_GAME"]["solution"] = solution

    response = client.post("/validate", json={"board": [[0] * 8] * 9})

    assert response.status_code == 400
    assert "error" in response.get_json()


def test_hint_route_uses_an_empty_non_prefilled_cell_and_correct_value(client):
    _, solution = sudoku_logic.generate_puzzle(clues=81)
    puzzle = [row[:] for row in solution]
    puzzle[0][0] = sudoku_logic.EMPTY
    puzzle[0][1] = sudoku_logic.EMPTY
    sudoku_app.app.config["CURRENT_GAME"].update(
        puzzle=puzzle,
        solution=solution,
    )
    board = [row[:] for row in puzzle]
    board[0][1] = solution[0][1]

    response = client.post("/hint", json={"board": board})

    assert response.status_code == 200
    assert response.get_json() == {
        "row": 0,
        "col": 0,
        "value": solution[0][0],
    }


def test_hint_route_rejects_request_without_active_game(client):
    response = client.post(
        "/hint",
        json={"board": sudoku_logic.create_empty_board()},
    )

    assert response.status_code == 400
    assert response.get_json() == {"error": "No game in progress"}


def test_hint_route_rejects_malformed_board(client):
    _, solution = sudoku_logic.generate_puzzle(clues=81)
    sudoku_app.app.config["CURRENT_GAME"].update(
        puzzle=sudoku_logic.create_empty_board(),
        solution=solution,
    )

    response = client.post("/hint", json={"board": [[0] * 8] * 9})

    assert response.status_code == 400
    assert "error" in response.get_json()


def test_hint_route_never_selects_an_original_prefilled_cell(client):
    _, solution = sudoku_logic.generate_puzzle(clues=81)
    puzzle = [row[:] for row in solution]
    puzzle[0][1] = sudoku_logic.EMPTY
    puzzle[0][2] = sudoku_logic.EMPTY
    sudoku_app.app.config["CURRENT_GAME"].update(
        puzzle=puzzle,
        solution=solution,
    )
    board = sudoku_logic.create_empty_board()
    board[0][2] = solution[0][2]

    response = client.post("/hint", json={"board": board})

    assert response.status_code == 200
    assert response.get_json() == {
        "row": 0,
        "col": 1,
        "value": solution[0][1],
    }


def test_hint_route_rejects_when_no_empty_cells_are_available(client):
    _, solution = sudoku_logic.generate_puzzle(clues=81)
    sudoku_app.app.config["CURRENT_GAME"].update(
        puzzle=sudoku_logic.create_empty_board(),
        solution=solution,
    )

    response = client.post("/hint", json={"board": solution})

    assert response.status_code == 409
    assert response.get_json() == {"error": "No empty cells are available for a hint"}


def test_check_route_reports_coordinates_that_do_not_match_solution(client):
    _, solution = sudoku_logic.generate_puzzle(clues=81)
    sudoku_app.app.config["CURRENT_GAME"]["solution"] = solution
    board = [row[:] for row in solution]
    board[0][0] = solution[0][0] % sudoku_logic.SIZE + 1

    response = client.post("/check", json={"board": board})

    assert response.status_code == 200
    result = response.get_json()
    assert result["incorrect"] == [[0, 0]]
    conflicts = {tuple(cell) for cell in result["conflicts"]}
    assert (0, 0) in conflicts
    assert (0, solution[0].index(board[0][0])) in conflicts
    assert result["solved"] is False


def test_check_route_returns_no_incorrect_cells_for_matching_solution(client):
    _, solution = sudoku_logic.generate_puzzle(clues=81)
    sudoku_app.app.config["CURRENT_GAME"]["solution"] = solution

    response = client.post("/check", json={"board": solution})

    assert response.status_code == 200
    assert response.get_json() == {
        "incorrect": [],
        "conflicts": [],
        "solved": True,
    }


def test_check_route_does_not_mark_blank_cells_as_incorrect(client):
    _, solution = sudoku_logic.generate_puzzle(clues=81)
    sudoku_app.app.config["CURRENT_GAME"]["solution"] = solution
    board = [row[:] for row in solution]
    board[0][0] = sudoku_logic.EMPTY

    response = client.post("/check", json={"board": board})

    assert response.status_code == 200
    assert response.get_json() == {
        "incorrect": [],
        "conflicts": [],
        "solved": False,
    }
