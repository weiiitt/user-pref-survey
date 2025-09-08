# -*- coding: utf-8 -*-
"""The app module, containing the app factory function."""
import sys
sys.stdout = sys.__stdout__  # Force stdout to be unbuffered
import logging

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS

from server import commands, public, user
from server.extensions import (
    bcrypt,
    cache,
    csrf_protect,
    db,
    debug_toolbar,
    flask_static_digest,
    login_manager,
    migrate,
)


def create_app(config_object="server.settings"):
    """Create application factory, as explained here: http://flask.pocoo.org/docs/patterns/appfactories/.

    :param config_object: The configuration object to use.
    """
    app = Flask(__name__.split(".")[0])
    
        # Enable CORS for specific origins
    app.config.from_object(config_object)
    CORS(
        app, 
        origins=
        [
            "http://localhost:5173", 
            "http://localhost:5174", 
            "https://weiiitt.github.io", 
            "https://minnow-tolerant-usefully.ngrok-free.app", 
            "https://uesrpref.loclx.io",
        ], 
        supports_credentials=True,
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "ngrok-skip-browser-warning"],  # add any custom headers used by the client
        expose_headers=["Content-Type"],  
    )  # Allow frontend origins
    register_extensions(app)
    register_blueprints(app)
    register_errorhandlers(app)
    register_shellcontext(app)
    register_commands(app)
    configure_logger(app)
    return app


def register_extensions(app):
    """Register Flask extensions."""
    bcrypt.init_app(app)
    cache.init_app(app)
    db.init_app(app)
    csrf_protect.init_app(app)
    login_manager.init_app(app)

    # Define a custom unauthorized handler for Flask-Login
    @login_manager.unauthorized_handler
    def unauthorized():
        return jsonify(message="Authentication required."), 403

    debug_toolbar.init_app(app)
    migrate.init_app(app, db)
    flask_static_digest.init_app(app)
    return None


def register_blueprints(app):
    """Register Flask blueprints."""
    app.register_blueprint(public.views.blueprint)
    app.register_blueprint(user.views.blueprint)
    
    # Debug: Try to import and register API blueprint
    try:
        from server import api
        app.register_blueprint(api.api)
        app.logger.info("API blueprint registered successfully")
    except Exception as e:
        app.logger.error(f"Failed to register API blueprint: {e}")
    
    return None


def register_errorhandlers(app):
    """Register error handlers."""

    def json_error(error):
        """Return JSON error for API routes, template for others."""
        error_code = getattr(error, "code", 500)
        
        # For API routes, return JSON
        if request.path.startswith('/api/'):
            return jsonify({"error": f"HTTP {error_code}", "message": str(error)}), error_code
        
        # For other routes, return simple text (no templates)
        return f"Error {error_code}", error_code

    for errcode in [401, 404, 500]:
        app.errorhandler(errcode)(json_error)
    return None


def register_shellcontext(app):
    """Register shell context objects."""

    def shell_context():
        """Shell context objects."""
        return {"db": db, "User": user.models.User}

    app.shell_context_processor(shell_context)


def register_commands(app):
    """Register Click commands."""
    app.cli.add_command(commands.test)
    app.cli.add_command(commands.lint)


def configure_logger(app):
    """Configure loggers."""
    handler = logging.StreamHandler(sys.stdout)
    if not app.logger.handlers:
        app.logger.addHandler(handler)
