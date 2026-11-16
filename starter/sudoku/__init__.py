from flask import Flask

from .routes import sudoku_blueprint


def create_app():
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )
    app.config["CURRENT_GAME"] = {"puzzle": None, "solution": None}
    app.register_blueprint(sudoku_blueprint)
    return app
