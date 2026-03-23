"""
Resume/JD Comparator backend: receives job description + resume, runs a simple
single-call matching pipeline (direct JD/resume -> one LLM scoring call),
and returns a structured match score and explanation.
"""
import os

from flask import Flask

from backend.views.compare_view import compare_bp


def create_app() -> Flask:
    from dotenv import load_dotenv
    from flask_cors import CORS

    from backend.error_handlers import register_error_handlers
    from backend.extensions import limiter
    from backend.infrastructure.config.settings import get_settings
    from backend.infrastructure.observability.langsmith import configure_langsmith
    from backend.infrastructure.observability.logging import configure_logging

    load_dotenv()

    settings = get_settings()
    configure_logging(level=settings.log_level, structured=settings.structured_logs)
    configure_langsmith(settings)

    import logging
    logger = logging.getLogger(__name__)

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    frontend_dist_dir = os.path.join(project_root, "front", "dist")
    static_dir = frontend_dist_dir if os.path.isdir(frontend_dist_dir) else os.path.join(project_root, "static")
    flask_app = Flask(__name__, static_folder=static_dir, static_url_path="")

    cors_origins = settings.cors_origins_for_flask
    CORS(flask_app, resources={r"/api/*": {"origins": cors_origins}})

    limiter.init_app(flask_app)
    register_error_handlers(flask_app)

    @flask_app.route("/")
    def index():
        index_path = os.path.join(flask_app.static_folder or "", "index.html")
        if os.path.exists(index_path):
            return flask_app.send_static_file("index.html")
        return (
            "Frontend is now in /front (Vue + Tailwind). "
            "Run `npm run dev` in /front or build /front for static hosting.",
            200,
        )

    @flask_app.route("/health")
    def health():
        return {"status": "ok"}, 200

    flask_app.register_blueprint(compare_bp)

    logger.info(
        "Backend app initialized app_env=%s langsmith_tracing=%s",
        settings.app_env,
        settings.langsmith_tracing,
    )
    return flask_app


app = create_app()


if __name__ == "__main__":
    is_dev = os.environ.get("APP_ENV", "development") == "development"
    app.run(host="0.0.0.0", port=5000, debug=is_dev)
