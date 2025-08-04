# -*- coding: utf-8 -*-
"""Public section, including homepage and signup."""
from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
    jsonify,
    session,
)
from flask_login import login_required, login_user, logout_user, UserMixin
import random

from server.database import db
from server.extensions import login_manager, csrf_protect
from server.user.models import AnonymousUser, User

blueprint = Blueprint("public", __name__, static_folder="../static")

@login_manager.user_loader
def load_user(participant_id):
    """Load user by participant_id string from session."""
    # This function is called by Flask-Login with the user_id (our participant_id)
    # that was stored in the session when login_user() was called.
    # We just need to return an instance of our AnonymousUser.
    return AnonymousUser(participant_id)

@blueprint.route("/generate-participant-id/", methods=["GET"])
@csrf_protect.exempt
def generate_unique_participant_id():
    """Generate a unique 4-digit participant ID that doesn't exist in the database."""
    max_attempts = 100  # Prevent infinite loop in case database is nearly full
    
    for _ in range(max_attempts):
        # Generate a random 4-digit ID (0000-9999)
        participant_id = f"{random.randint(0, 9999):04d}"
        
        # Check if this ID already exists
        existing_user = User.query.filter_by(participant_id=participant_id).first()
        if not existing_user:
            return jsonify({"participant_id": participant_id}), 200
    
    # If we can't find a unique ID after max_attempts, return an error
    return jsonify({"error": "Unable to generate unique participant ID. Please try again."}), 500

@blueprint.route("/register/", methods=["POST"])
@csrf_protect.exempt
def register_anonymous():
    """Register an anonymous user with a 4-digit participant ID."""
    data = request.get_json()
    participant_id = data.get('participant_id')
    
    if not participant_id:
        return jsonify({"error": "Participant ID is required."}), 400
    
    if len(participant_id) != 4 or not participant_id.isdigit():
        return jsonify({"error": "Participant ID must be exactly 4 digits."}), 400
    
    # Check if participant ID already exists
    existing_user = User.query.filter_by(participant_id=participant_id).first()
    if existing_user:
        return jsonify({"error": "Participant ID already exists. Please try logging in instead."}), 409
    
    # Generate randomized condition orders
    from server.api import get_available_conditions
    available_conditions = get_available_conditions()
    tabletop_conditions = list(range(available_conditions["tabletop"] + 1))  # [0, 1, 2]
    robot_nav_conditions = list(range(available_conditions["robot_nav"] + 1))  # [0, 1, 2]
    
    random.shuffle(tabletop_conditions)
    random.shuffle(robot_nav_conditions)
    
    # Create a new User record with randomized condition orders
    new_user = User(
        participant_id=participant_id,
        tabletop_condition_order=tabletop_conditions,
        robot_nav_condition_order=robot_nav_conditions,
        current_condition=tabletop_conditions[0]  # Start with first condition in randomized order
    )
    db.session.add(new_user)
    db.session.commit()

    # Store the participant_id in session
    session['user_id'] = participant_id

    # Create an anonymous user object and log them in
    anon_user = AnonymousUser(participant_id)
    login_user(anon_user) 
    current_app.logger.info(f"Anonymous user registered with participant ID: {participant_id}")
    return jsonify({"message": "Anonymous user registered successfully.", "participant_id": participant_id}), 200

@blueprint.route("/login/", methods=["POST"])
@csrf_protect.exempt
def login_anonymous():
    """Login an existing anonymous user with their participant ID."""
    data = request.get_json()
    participant_id = data.get('participant_id')
    
    if not participant_id:
        return jsonify({"error": "Participant ID is required."}), 400
    
    if len(participant_id) != 4 or not participant_id.isdigit():
        return jsonify({"error": "Participant ID must be exactly 4 digits."}), 400
    
    # Check if participant ID exists
    existing_user = User.query.filter_by(participant_id=participant_id).first()
    if not existing_user:
        return jsonify({"error": "Participant ID not found. Please register first."}), 404
    
    # Store the participant_id in session
    session['user_id'] = participant_id

    # Create an anonymous user object and log them in
    anon_user = AnonymousUser(participant_id)
    login_user(anon_user) 
    current_app.logger.info(f"Anonymous user logged in with participant ID: {participant_id}")
    return jsonify({"message": "Login successful.", "participant_id": participant_id}), 200

@blueprint.route("/logout/", methods=["POST"])
@csrf_protect.exempt
def logout_anonymous():
    """Logout the current user and clear session."""
    if 'user_id' in session:
        participant_id = session['user_id']
        current_app.logger.info(f"User with participant ID {participant_id} logged out")
    
    # Clear the session
    session.pop('user_id', None)
    logout_user()
    
    return jsonify({"message": "Logout successful."}), 200

def is_user_logged_in():
    """Check if the user is logged in."""
    return 'user_id' in session

@blueprint.route("/check-login/")
def check_login():
    """Check if the user is logged in."""
    if is_user_logged_in():
        participant_id = session.get('user_id')
        return jsonify({"message": "User is logged in.", "participant_id": participant_id}), 200
    else:
        return jsonify({"message": "User is not logged in."}), 401
