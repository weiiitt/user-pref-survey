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
import osmnx as ox
import networkx as nx
import random
import numpy as np
import pandas as pd
import uuid
import pickle # Added for belief serialization
import traceback

from server.database import db
from server.extensions import login_manager, csrf_protect
from server.user.models import AnonymousUser, RoutePreference, GeneratedRoute, User # Added User model
from server.services.osmnx import osmnx_service
from server.services.APReL_wrapper import aprel_wrapper # aprel_wrapper instance
import aprel # Import aprel

blueprint = Blueprint("public", __name__, static_folder="../static")

@login_manager.user_loader
def load_user(user_uuid):
    """Load user by UUID string from session."""
    # This function is called by Flask-Login with the user_id (our UUID)
    # that was stored in the session when login_user() was called.
    # We just need to return an instance of our AnonymousUser.
    return AnonymousUser(user_uuid)

@blueprint.route("/register/", methods=["POST"])
@csrf_protect.exempt
def register_anonymous():
    """Register an anonymous user by generating a UUID and storing it in the session."""
    user_uuid = str(uuid.uuid4())
    session['user_id'] = user_uuid # Store the uuid in session

    # Initialize APReL components from the wrapper
    env = aprel_wrapper.env
    
    # Create random initial weights for a new user
    # Assuming env.features_dim is accessible and correct
    params = {'weights': aprel.utils.util_funs.get_random_normalized_vector(env.features_dim)}
    user_model = aprel.learning.SoftmaxUser(params)
    
    # Initialize belief with empty dataset and uniform prior
    initial_belief = aprel.learning.SamplingBasedBelief(user_model, [], params,
                                             logprior=aprel.utils.uniform_logprior,
                                             num_samples=100) # Default num_samples, adjust if needed
    
    # Serialize the belief object
    serialized_belief = pickle.dumps(initial_belief)

    # Create a new User record
    new_user = User(uuid=user_uuid, belief=serialized_belief)
    db.session.add(new_user)
    db.session.commit()

    # Create an anonymous user object and log them in
    anon_user = AnonymousUser(user_uuid)
    login_user(anon_user) 
    current_app.logger.info(f"Anonymous user registered with UUID: {user_uuid} and initial belief stored.")
    return jsonify({"message": "Anonymous user registered successfully.", "user_uuid": user_uuid}), 200

# @blueprint.route("/logout/")
# @login_required
# def logout():
#     """Logout."""
#     logout_user()
#     flash("You are logged out.", "info")
#     return redirect(url_for("public.home"))


# @blueprint.route("/register/", methods=["GET", "POST"])
# def register():
#     """Register new user."""
#     form = RegisterForm(request.form)
#     if form.validate_on_submit():
#         User.create(
#             username=form.username.data,
#             email=form.email.data,
#             password=form.password.data,
#             active=True,
#         )
#         flash("Thank you for registering. You can now log in.", "success")
#         return redirect(url_for("public.home"))
#     else:
#         flash_errors(form)
#     return render_template("public/register.html", form=form)

@blueprint.route("/generate-routes/", methods=["GET"])
@login_required
def generate_routes():
    """Generate routes for the logged-in user."""
    try:
        # get the user's belief
        user_uuid = session.get("user_id")
        if not user_uuid:
            return jsonify({"error": "User not logged in"}), 401

        user = User.query.filter_by(uuid=user_uuid).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        belief = pickle.loads(user.belief)
        routes = aprel_wrapper.optimize_query(belief)
        route1 = routes.slate.trajectories[0].trajectory
        route1 = [node for node, _ in route1]
        route1 = [a for a, b in zip(route1, [None] + route1) if a != b]
        
        route2 = routes.slate.trajectories[1].trajectory
        route2 = [node for node, _ in route2]
        route2 = [a for a, b in zip(route2, [None] + route2) if a != b]
        
        path_nodes = [route1, route2]
        
        graph = osmnx_service.get_graph()

        # First, filter out routes with missing nodes
        valid_path_nodes = []
        for idx, route in enumerate(path_nodes):
            if not route:
                current_app.logger.warning(f"Route {idx} is empty")
                continue
            
            # Check if all nodes in the route exist in the graph
            missing_nodes = [node for node in route if node not in graph.nodes]
            if missing_nodes:
                current_app.logger.error(f"Route {idx} contains missing nodes: {missing_nodes[:5]}...")  # Log first 5 for brevity
                continue  # Skip this route
            
            valid_path_nodes.append((idx, route))
        
        if len(valid_path_nodes) < 2:
            current_app.logger.error(f"Could not find enough valid routes. Only {len(valid_path_nodes)} valid routes found.")
            return jsonify({"error": "Could not generate two valid routes. Please try again."}), 500

        routes_data = []
        presented_route_db_ids = []

        for original_idx, route in valid_path_nodes:
            route_guid = str(uuid.uuid4()) # GUID for external reference
            coords = [[graph.nodes[node]['y'], graph.nodes[node]['x']] for node in route]
            distance = sum(
                min(edge_data.get('length', 0) for edge_data in graph.get_edge_data(u, v).values())
                for u, v in zip(route[:-1], route[1:])
            )
            
            elevation_gain = 0
            avg_abs_grade = 0
            
            try:
                # Calculate elevation changes (both up and down)
                elevation_changes = [
                    abs(graph.nodes[route[i+1]].get('elevation', 0) - graph.nodes[route[i]].get('elevation', 0))
                    for i in range(len(route)-1)
                ]
                elevation_gain = sum(elevation_changes)
                
                if distance > 0:
                    grades = [
                        abs((graph.nodes[route[i+1]].get('elevation', 0) - graph.nodes[route[i]].get('elevation', 0)) / 
                            min(edge_data.get('length', 1) for edge_data in graph.get_edge_data(route[i], route[i+1]).values()))
                        for i in range(len(route)-1) if min(edge_data.get('length', 0) for edge_data in graph.get_edge_data(route[i], route[i+1]).values()) > 0 # Avoid division by zero
                    ]
                    if grades: # Ensure grades list is not empty
                        avg_abs_grade = sum(grades) / len(grades) * 100
            except Exception as e:
                current_app.logger.warning(f"Error calculating elevation data for a route: {str(e)}")

            left_turns, right_turns = osmnx_service.count_turns(route)
            
            travel_time = sum(
                min(edge_data.get('travel_time', 0) for edge_data in graph.get_edge_data(u, v).values())
                for u, v in zip(route[:-1], route[1:])
            )
            
            source_coords = [graph.nodes[route[0]]['y'], graph.nodes[route[0]]['x']]
            dest_coords = [graph.nodes[route[-1]]['y'], graph.nodes[route[-1]]['x']]
            
            # Save to GeneratedRoute table
            try:
                generated_route_db = GeneratedRoute.create(
                    route_guid=route_guid,
                    distance=float(distance),
                    elevation_gain=float(elevation_gain),
                    avg_grade=float(avg_abs_grade),
                    left_turns=left_turns,
                    right_turns=right_turns,
                    travel_time=float(travel_time),
                    source_node_id=str(route[0]),
                    source_coordinates=source_coords,
                    destination_node_id=str(route[-1]),
                    destination_coordinates=dest_coords,
                    response_id=original_idx,
                    trajectory_obj=pickle.dumps(routes.slate.trajectories[original_idx]),
                    reward_weights=list(routes.reward_weights[original_idx])
                )
                db.session.commit()
                current_app.logger.info(f"Saved GeneratedRoute with id: {generated_route_db.id} and guid: {route_guid}")
                
                route_info_for_response = {
                    "route": {
                        "id": generated_route_db.id, # Use DB PK ID for client-side
                        "response_id": original_idx,
                        "route_guid": route_guid, # Can also include guid if useful for client
                        "coordinates": coords,
                        "distance": float(distance),
                        "elevationGain": float(elevation_gain),
                        "avgGrade": float(avg_abs_grade),
                        "leftTurns": left_turns,
                        "rightTurns": right_turns,
                        "travelTime": float(travel_time)
                    },
                    "source": {
                        "coordinates": source_coords
                    },
                    "destination": {
                        "coordinates": dest_coords
                    }
                }
                routes_data.append(route_info_for_response)
                presented_route_db_ids.append(generated_route_db.id)
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error saving GeneratedRoute (guid: {route_guid}): {str(e)}")
                # Decide how to handle this error - skip route, return error, etc.
                # For now, let's append a None or an error structure
                routes_data.append({"error": "Failed to save route", "guid": route_guid})
                # Not adding to presented_route_db_ids if save failed
                # Or, re-raise to fail the whole request: raise 
                
        valid_routes_data = [r for r in routes_data if r and "error" not in r]
        if not valid_routes_data or len(valid_routes_data) < 2 : # check if at least two routes are generated.
            current_app.logger.error(f"Could not generate two valid routes.")
            return jsonify({"error": "Could not generate two valid routes. Please try again."}), 500

        response = {"routes": valid_routes_data}
        return jsonify(response)
        
    except Exception as e:
        current_app.logger.error(f"Error generating routes: {str(e)}")
        current_app.logger.error(f"Full traceback: {traceback.format_exc()}")
        db.session.rollback() 
        return jsonify({"error": str(e)}), 500

def is_user_logged_in():
    """Check if the user is logged in."""
    return 'user_id' in session

@blueprint.route("/check-login/")
def check_login():
    """Check if the user is logged in."""
    if is_user_logged_in():
        return jsonify({"message": "User is logged in."}), 200
    else:
        return jsonify({"message": "User is not logged in."}), 401

@blueprint.route("/prefer-route/", methods=["POST"])
@login_required
@csrf_protect.exempt
def prefer_route():
    """Save user's preferred route."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400

    selected_route_id = data.get("selected_route_id") # This is now GeneratedRoute.id
    presented_routes_ids = data.get("presented_routes_ids") # List of GeneratedRoute.id

    if selected_route_id is None or not presented_routes_ids: # selected_route_id can be 0 if it's a valid PK
        return jsonify({"error": "Missing selected_route_id or presented_routes_ids"}), 400
    
    if not isinstance(presented_routes_ids, list):
        return jsonify({"error": "presented_routes_ids must be a list"}), 400
    
    # Optionally, validate that selected_route_id is in presented_routes_ids
    if selected_route_id not in presented_routes_ids:
        return jsonify({"error": "selected_route_id must be one of the presented_routes_ids"}), 400

    user_uuid = session.get("user_id")
    if not user_uuid:
        return jsonify({"error": "User not logged in"}), 401

    presented_routes_ids = sorted(presented_routes_ids)

    try:
        # Get the user and their belief
        user = User.query.filter_by(uuid=user_uuid).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        belief = pickle.loads(user.belief)
        
        # Retrieve the GeneratedRoute objects for the presented routes
        presented_routes_objects = GeneratedRoute.query.filter(GeneratedRoute.id.in_(presented_routes_ids)).all()
        if len(presented_routes_objects) != len(presented_routes_ids):
            return jsonify({"error": "Some presented routes not found"}), 400
        
        # Sort the routes objects to match the order of presented_routes_ids 
        route_id_to_obj = {route.id: route for route in presented_routes_objects}
        sorted_route_objects = [route_id_to_obj[route_id] for route_id in presented_routes_ids]
        
        # Extract trajectory objects from the database and deserialize them
        trajectories = []
        reward_weights = []
        for route_obj in sorted_route_objects:
            trajectory_obj = pickle.loads(route_obj.trajectory_obj)
            trajectories.append(trajectory_obj)
            reward_weights.append(np.array(route_obj.reward_weights))
        
        # Create a TrajectorySet and PreferenceQuery
        trajectory_set = aprel.TrajectorySet(trajectories)
        query = aprel.PreferenceQuery(trajectory_set)
        
        # Set the reward weights on the query
        query.reward_weights = reward_weights
        
        # Determine the response index (which trajectory was selected)
        selected_index = presented_routes_ids.index(selected_route_id)
        
        # Create a Preference object
        preference = aprel.Preference(query, selected_index)
        
        # Check if a preference for these presented routes already exists for this user
        existing_preference = RoutePreference.query.filter_by(
            user_uuid=user_uuid,
            presented_routes_ids=presented_routes_ids 
        ).first()

        # Update the belief with the new preference
        if existing_preference and existing_preference.selected_generated_route_id != selected_route_id:
            # If preference changed, we need to update the belief
            # For now, let's just add the new preference to the dataset
            # In a more sophisticated approach, we might want to handle belief updates differently
            belief.update(preference)
            current_app.logger.info(f"Updated belief for user {user_uuid} due to preference change")
        elif not existing_preference:
            # New preference, update belief
            belief.update(preference)
            current_app.logger.info(f"Updated belief for user {user_uuid} with new preference")
        
        # Save the updated belief back to the database
        user.belief = pickle.dumps(belief)
        db.session.add(user)
        db.session.commit()

        if existing_preference:
            # Update existing preference
            existing_preference.update(selected_generated_route_id=selected_route_id)
            # db.session.commit() # PkModel.update already commits by default.
            current_app.logger.info(f"Route preference updated for user {user_uuid}, selected generated route id {selected_route_id}")
            return jsonify({"message": "Preference updated successfully.", "preference_id": existing_preference.id}), 200
        else:
            # Create new preference
            preference_record = RoutePreference.create(
                user_uuid=user_uuid,
                selected_generated_route_id=selected_route_id, # Storing GeneratedRoute.id
                presented_routes_ids=presented_routes_ids, # Storing list of GeneratedRoute.id
            )
            # db.session.commit() # PkModel.create already commits by default.
            current_app.logger.info(f"Route preference saved for user {user_uuid}, selected generated route id {selected_route_id}")
            return jsonify({"message": "Preference saved successfully.", "preference_id": preference_record.id}), 201
    except Exception as e:
        current_app.logger.error(f"Error saving route preference: {str(e)}")
        db.session.rollback() 
        return jsonify({"error": "Could not save preference."}), 500

@blueprint.route("/previous-answers/", methods=["GET"])
@login_required
def previous_answers():
    """Return all previous answers for the logged-in user."""
    user_uuid = session.get("user_id")
    if not user_uuid:
        # This case should ideally be caught by @login_required,
        # but as a safeguard:
        return jsonify({"error": "User not logged in"}), 401

    try:
        preferences = RoutePreference.query.filter_by(user_uuid=user_uuid).order_by(RoutePreference.created_at.desc()).all()
        
        results = []
        for pref in preferences:
            selected_route_details = None
            if pref.selected_route: # pref.selected_route is the relationship to GeneratedRoute
                selected_route_details = {
                    "id": pref.selected_route.id,
                    "route_guid": pref.selected_route.route_guid,
                    "distance": pref.selected_route.distance,
                    "elevationGain": pref.selected_route.elevation_gain,
                    "avgGrade": pref.selected_route.avg_grade,
                    "leftTurns": pref.selected_route.left_turns,
                    "rightTurns": pref.selected_route.right_turns,
                    "travelTime": pref.selected_route.travel_time,
                    "source_node_id": pref.selected_route.source_node_id,
                    "source_coordinates": pref.selected_route.source_coordinates,
                    "destination_node_id": pref.selected_route.destination_node_id,
                    "destination_coordinates": pref.selected_route.destination_coordinates,
                }
            
            presented_routes_details = []
            if pref.presented_routes_ids:
                # Fetch details for each presented route ID
                # Assuming presented_routes_ids is a list of GeneratedRoute.id
                presented_routes_objects = GeneratedRoute.query.filter(GeneratedRoute.id.in_(pref.presented_routes_ids)).all()
                for route_obj in presented_routes_objects:
                    presented_routes_details.append({
                        "id": route_obj.id,
                        "route_guid": route_obj.route_guid,
                        "distance": route_obj.distance,
                        "elevationGain": route_obj.elevation_gain,
                        "avgGrade": route_obj.avg_grade,
                        "leftTurns": route_obj.left_turns,
                        "rightTurns": route_obj.right_turns,
                        "travelTime": route_obj.travel_time,
                        "source_node_id": route_obj.source_node_id,
                        "source_coordinates": route_obj.source_coordinates,
                        "destination_node_id": route_obj.destination_node_id,
                        "destination_coordinates": route_obj.destination_coordinates,
                    })

            results.append({
                "preference_id": pref.id,
                "user_uuid": pref.user_uuid,
                "selected_generated_route_id": pref.selected_generated_route_id,
                "selected_route_details": selected_route_details,
                "presented_routes_ids": pref.presented_routes_ids,
                "presented_routes_details": presented_routes_details,
                "created_at": pref.created_at.isoformat() if pref.created_at else None,
            })
            
        return jsonify({"previous_answers": results}), 200
    except Exception as e:
        current_app.logger.error(f"Error fetching previous answers for user {user_uuid}: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Could not retrieve previous answers."}), 500
