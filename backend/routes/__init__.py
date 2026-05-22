from routes.analytics import analytics_bp
from routes.auth import auth_bp
from routes.companies import companies_bp
from routes.evaluate import evaluate_bp
from routes.feedback import feedback_bp
from routes.progress import progress_bp
from routes.questions import questions_bp
from routes.timer_settings import timer_bp
from routes.users import users_bp

ALL_BLUEPRINTS = (
    auth_bp,
    companies_bp,
    questions_bp,
    progress_bp,
    evaluate_bp,
    feedback_bp,
    users_bp,
    analytics_bp,
    timer_bp,
)


def register_blueprints(app):
    for blueprint in ALL_BLUEPRINTS:
        app.register_blueprint(blueprint)
