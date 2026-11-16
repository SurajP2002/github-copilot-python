from flask import Blueprint, current_app, jsonify, render_template, request

from . import logic

sudoku_blueprint = Blueprint("sudoku", __name__)


@sudoku_blueprint.route("/")
def index():
    return render_template("index.html")


@sudoku_blueprint.route("/new")
def new_game():
    difficulty = request.args.get("difficulty", "medium").lower()
    if difficulty not in logic.DIFFICULTY_CLUES:
        return jsonify({"error": "Difficulty must be easy, medium, or hard"}), 400

    try:
        clues = int(
            request.args.get("clues", logic.DIFFICULTY_CLUES[difficulty])
        )
    except ValueError:
        return jsonify({"error": "Clue count must be an integer"}), 400

    if not logic.MINIMUM_UNIQUE_CLUES <= clues <= logic.SIZE * logic.SIZE:
        return jsonify({
            "error": (
                "Clue count must be between "
                f"{logic.MINIMUM_UNIQUE_CLUES} and {logic.SIZE * logic.SIZE}"
            )
        }), 400

    try:
        puzzle, solution = logic.generate_puzzle(clues)
    except RuntimeError as error:
        return jsonify({"error": str(error)}), 503

    current_game = current_app.config["CURRENT_GAME"]
    current_game["puzzle"] = puzzle
    current_game["solution"] = solution
    return jsonify({"puzzle": puzzle})


@sudoku_blueprint.route("/check", methods=["POST"])
def check_solution():
    data = request.json
    board = data.get("board")
    solution = current_app.config["CURRENT_GAME"].get("solution")
    if solution is None:
        return jsonify({"error": "No game in progress"}), 400

    incorrect_cells = []
    for row in range(logic.SIZE):
        for col in range(logic.SIZE):
            if (
                board[row][col] != logic.EMPTY
                and board[row][col] != solution[row][col]
            ):
                incorrect_cells.append([row, col])
    return jsonify({
        "incorrect": incorrect_cells,
        "conflicts": logic.find_conflicts(board),
        "solved": board == solution,
    })


@sudoku_blueprint.route("/validate", methods=["POST"])
def validate_board():
    solution = current_app.config["CURRENT_GAME"].get("solution")
    if solution is None:
        return jsonify({"error": "No game in progress"}), 400

    data = request.get_json(silent=True)
    board = data.get("board") if isinstance(data, dict) else None
    if not logic.is_well_formed_board(board):
        return jsonify({
            "error": "Board must be a 9x9 grid containing numbers from 0 to 9"
        }), 400

    incorrect_cells = [
        [row, col]
        for row in range(logic.SIZE)
        for col in range(logic.SIZE)
        if board[row][col] != logic.EMPTY
        and board[row][col] != solution[row][col]
    ]
    return jsonify({
        "incorrect": incorrect_cells,
        "conflicts": logic.find_conflicts(board),
        "solved": board == solution,
    })


@sudoku_blueprint.route("/hint", methods=["POST"])
def provide_hint():
    current_game = current_app.config["CURRENT_GAME"]
    puzzle = current_game.get("puzzle")
    solution = current_game.get("solution")
    if puzzle is None or solution is None:
        return jsonify({"error": "No game in progress"}), 400

    data = request.get_json(silent=True)
    board = data.get("board") if isinstance(data, dict) else None
    if not logic.is_well_formed_board(board):
        return jsonify({
            "error": "Board must be a 9x9 grid containing numbers from 0 to 9"
        }), 400

    hint = logic.find_hint(puzzle, solution, board)
    if hint is None:
        return jsonify({"error": "No empty cells are available for a hint"}), 409
    row, col, value = hint
    return jsonify({"row": row, "col": col, "value": value})
