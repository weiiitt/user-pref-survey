from flask import Blueprint, Response, current_app, jsonify, request, send_file, session
from flask_cors import cross_origin
from server.user.models import User, UserTestProgress, InterRoundSurveyResponse
from server.database import db
from server.extensions import csrf_protect
import os
import base64
import pickle
import numpy as np
from server.services.tree_node import NewTreeNode
import random

api = Blueprint("api", __name__, url_prefix="/api")

def compute_all_completed(user: User) -> bool:
    """Return True if all conditions across all test types are completed and their inter-round surveys are done."""
    try:
        structure = get_survey_structure()
        total_conditions = len(structure.get("tabletop", {})) + len(structure.get("robot_nav", {}))
        # Count progress rows that are both completed and have their inter-round survey completed
        completed_with_survey = UserTestProgress.query.filter_by(
            user_id=user.id,
            completed=True,
            inter_round_survey_completed=True,
        ).count()
        return completed_with_survey >= total_conditions and total_conditions > 0
    except Exception as e:
        current_app.logger.error(f"Error computing all_completed: {e}")
        return False

class RemapUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if module.startswith("numpy._core"):
            module = module.replace("numpy._core", "numpy.core", 1)
        # Remap pickles saved when NewTreeNode lived in __main__ or a local tree_node module
        if name == "NewTreeNode" and module in ("__main__", "tree_node"):
            module = "server.services.tree_node"
            name = "NewTreeNode"
        return super().find_class(module, name)

def get_survey_structure():
    """
    Dynamically discover available conditions and questions by scanning the assets folder.
    Returns a dict with test_type as key and condition data as value.
    Format: {"tabletop": {0: 8, 1: 10, 2: 7}, "robot_nav": {0: 9, 1: 12}}
    Where numbers are question counts for each condition.
    """
    assets_path = os.path.join("/app", "assets", "user_study")
    structure = {"tabletop": {}, "robot_nav": {}}
    
    try:
        if os.path.exists(assets_path):
            for folder_name in os.listdir(assets_path):
                folder_path = os.path.join(assets_path, folder_name)
                if os.path.isdir(folder_path):
                    if folder_name.startswith("TableTop-v"):
                        condition_num = int(folder_name.split("-v")[1])
                        question_count = count_questions_in_folder(folder_path, folder_name)
                        structure["tabletop"][condition_num] = question_count
                    elif folder_name.startswith("GrassStreetNav-v"):
                        condition_num = int(folder_name.split("-v")[1])
                        question_count = count_questions_in_folder(folder_path, folder_name)
                        structure["robot_nav"][condition_num] = question_count
    except Exception as e:
        current_app.logger.error(f"Error scanning survey structure: {e}")
        # Fall back to defaults if scanning fails
        structure = {"tabletop": {0: 5, 1: 5, 2: 5}, "robot_nav": {0: 5, 1: 5, 2: 5}}
    
    return structure

def count_questions_in_folder(folder_path, folder_name):
    """
    Count the number of unique questions in a condition folder.
    Each question has multiple files for different choice combinations.
    """
    try:
        files = os.listdir(folder_path)
        # Look for files matching the pattern and extract unique question numbers
        import re
        if folder_name.startswith("TableTop-v"):
            pattern = rf"^{re.escape(folder_name)}_query_(\d+)_.*_1\.png$"
        elif folder_name.startswith("GrassStreetNav-v"):
            pattern = rf"^{re.escape(folder_name)}_query_(\d+)_.*_1\.png$"
        else:
            return 10  # Default fallback for unknown folder types
            
        question_numbers = set()
        for filename in files:
            match = re.match(pattern, filename)
            if match:
                question_num = int(match.group(1))
                question_numbers.add(question_num)
        
        count = len(question_numbers)
        current_app.logger.info(f"Found {count} unique questions in {folder_name} (question numbers: {sorted(question_numbers)})")
        return count if count > 0 else 10  # Fallback to 10 if no matches found
    except Exception as e:
        current_app.logger.error(f"Error counting questions in {folder_name}: {e}")
        return 10  # Default fallback

def get_available_conditions():
    """
    Get max condition numbers for backward compatibility.
    """
    structure = get_survey_structure()
    conditions = {
        "tabletop": max(structure["tabletop"].keys()) if structure["tabletop"] else 0,
        "robot_nav": max(structure["robot_nav"].keys()) if structure["robot_nav"] else 0
    }
    return conditions

@api.route("/test", methods=["GET"])
@cross_origin(supports_credentials=True)
@csrf_protect.exempt
def test_route():
    return jsonify({"message": "API working!"})

@api.route("/get-survey-config", methods=["GET"])
@cross_origin(supports_credentials=True)
@csrf_protect.exempt
def get_survey_config():
    """Returns dynamic survey configuration based on available assets"""
    structure = get_survey_structure()
    
    tabletop_total = sum(structure["tabletop"].values())
    robot_nav_total = sum(structure["robot_nav"].values())
    total_questions = tabletop_total + robot_nav_total
    
    return jsonify({
        "total_questions": total_questions,
        "tabletop_questions": tabletop_total,
        "robot_nav_questions": robot_nav_total,
        "structure": structure
    })


@api.route("/get-inter-round-questions", methods=["GET"])
@cross_origin(supports_credentials=True)
@csrf_protect.exempt
def get_inter_round_questions():
    """Return the inter-round survey questions with a randomly placed decoy.
    The free-text question is only included if the completed condition was the last in its test type.
    """
    participant_id = session.get('user_id')
    if not participant_id:
        return jsonify({"error": "Not logged in"}), 403

    user = User.query.filter_by(participant_id=participant_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Find the most recently completed progress that doesn't have survey completed
    completed_progress = UserTestProgress.query.filter_by(
        user_id=user.id,
        completed=True,
        inter_round_survey_completed=False
    ).order_by(UserTestProgress.id.desc()).first()

    if not completed_progress:
        return jsonify({"error": "No pending inter-round survey found"}), 400

    # Determine if the completed condition was the final one for its test type
    if completed_progress.test_type == "tabletop":
        order = user.tabletop_condition_order or []
    else:
        order = user.robot_nav_condition_order or []

    try:
        condition_index_in_order = order.index(completed_progress.condition_number)
        is_final_for_test_type = (condition_index_in_order == len(order) - 1)
    except ValueError:
        # If condition not found in order, default to not final
        is_final_for_test_type = False

    # Base scale questions (1-7)
    scale_questions = [
        {"id": "mental_demand", "type": "scale", "label": "How mentally demanding was the task?"},
        {"id": "success_level", "type": "scale", "label": "How successful were you in accomplishing what you were asked to do?"},
        {"id": "frustration_level", "type": "scale", "label": "How discouraged, irritated, stressed, or annoyed were you?"},
        {"id": "trajectory_choice_ease", "type": "scale", "label": "It was easy to choose between the trajectories the robot showed me."},
        {"id": "difference_clarity", "type": "scale", "label": "It was easy to tell the difference between the options presented."},
        {"id": "preference_learning", "type": "scale", "label": "Through these questions, the robot was able to learn my preferences."},
    ]

    # Decoy question (camouflaged sentence variant + ordinal wording)
    decoy_expected = random.randint(3, 7)
    session['attention_check_expected'] = decoy_expected
    decoy_variants = [
        f"It was easy to understand the questions, select option {decoy_expected} on the scale for this question.",
        f"It was simple to comprehend the given questions, pick option {decoy_expected} on the scale for this question.",
        f"It was easy to answer the survey questions, select option {decoy_expected} on the scale for this question.",
        f"It was simple to judge the options, choose option {decoy_expected} on the scale for this question.",
    ]
    decoy_label = random.choice(decoy_variants)
    decoy_question = {"id": "attention_check", "type": "scale", "label": decoy_label}

    # Randomly insert decoy among the scale questions
    insert_idx = random.randint(3, len(scale_questions))
    questions = scale_questions.copy()
    questions.insert(insert_idx, decoy_question)

    # Append free-text only if final for this test type
    if is_final_for_test_type:
        questions.append({
            "id": "decision_factors",
            "type": "text",
            "label": "What factors did you consider when choosing between the two robot trajectories?",
            "hint": "For example: safety, efficiency, terrain type, object avoidance, or other criteria.",
        })

    response = jsonify({
        "questions": questions,
        "scale": {"minValue": 1, "maxValue": 7, "minLabel": "Not at all", "maxLabel": "Extremely"},
        "test_type": completed_progress.test_type,
        "condition_number": completed_progress.condition_number,
        "is_final_for_test_type": is_final_for_test_type,
    })
    # Prevent caching to avoid repeated position/value due to caching layers
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    return response

@api.route("/get-question-images", methods=["GET"])
@cross_origin(supports_credentials=True)
@csrf_protect.exempt
def get_question_images():
    # Get participant ID from session
    participant_id = session.get('user_id')
    current_app.logger.info(f"Fetching images for participant: {participant_id}")
    
    if not participant_id:
        return jsonify({"error": "Not logged in"}), 403
    
    user = User.query.filter_by(participant_id=participant_id).first()
    if not user:
        current_app.logger.error(f"User not found: {participant_id}")
        # Clear invalid session
        session.pop('user_id', None)
        return jsonify({"error": "User not found"}), 403
    
    current_app.logger.info(f"User found, current_test_type: {getattr(user, 'current_test_type', 'NOT SET')}")
    current_app.logger.info(f"User found, current_condition: {getattr(user, 'current_condition', 'NOT SET')}")
    
    test_type, condition, question_num = user.check_user_progress()
    current_app.logger.info(f"Progress check result: test_type={test_type}, condition={condition}, question_num={question_num}")
    
    # Check if there's a pending inter-round survey
    pending_survey = UserTestProgress.query.filter_by(
        user_id=user.id,
        completed=True,
        inter_round_survey_completed=False
    ).first()
    
    if pending_survey:
        return jsonify({
            "error": "Inter-round survey pending",
            "show_inter_round_survey": True,
            "pending_survey_test_type": pending_survey.test_type,
            "pending_survey_condition": pending_survey.condition_number
        }), 202  # 202 Accepted - indicates action required
    
    # Get user's previous choices for this test type and condition
    progress = UserTestProgress.query.filter_by(
        user_id=user.id,
        test_type=test_type,
        condition_number=condition
    ).first()
    
    if not progress:
        current_app.logger.info(f"No progress record found, creating new one for user_id={user.id}, test_type={test_type}, condition={condition}")
        # Create progress record if it doesn't exist
        progress = UserTestProgress(
            user_id=user.id,
            test_type=test_type,
            condition_number=condition,
            choices=[],
            response_times=[],
            completed=False
        )
        db.session.add(progress)
        db.session.commit()
        current_app.logger.info("New progress record created")
    
    # Convert choices to string (e.g., [1, 0, 1, 1] -> "1011")
    choices_str = "".join(str(choice) for choice in progress.choices)
    
    # Build folder and filename pattern
    if test_type == "tabletop":
        folder_name = f"TableTop-v{condition}"
        base_filename = f"TableTop-v{condition}_query_{question_num}_{choices_str}_"
        # pkl_filename = f"query_tree_TableTop-v{condition}.pkl"
    else:  # robot_nav
        folder_name = f"GrassStreetNav-v{condition}"  # Assuming similar naming pattern
        base_filename = f"GrassStreetNav-v{condition}_query_{question_num}_{choices_str}_"
        pkl_filename = f"query_tree_GrassStreetNav-v{condition}.pkl"
    
    # Construct full paths (assets are at /app/assets in Docker container)
    assets_path = os.path.join("/app", "assets", "user_study", folder_name)
    image1_path = os.path.join(assets_path, base_filename + "1.png")
    image2_path = os.path.join(assets_path, base_filename + "2.png")
    
    if test_type == "robot_nav":
        pkl_path = os.path.join(assets_path, pkl_filename)
    
    current_app.logger.info(f"Looking for images at:")
    current_app.logger.info(f"  Image1: {image1_path}")
    current_app.logger.info(f"  Image2: {image2_path}")
    current_app.logger.info(f"  Assets path exists: {os.path.exists(assets_path)}")
    current_app.logger.info(f"  Image1 exists: {os.path.exists(image1_path)}")
    current_app.logger.info(f"  Image2 exists: {os.path.exists(image2_path)}")
    
    # Check if images exist
    if not os.path.exists(image1_path) or not os.path.exists(image2_path):
        return jsonify({"error": "Images not found for current progress"}), 404
    
    if test_type == "robot_nav" and not os.path.exists(pkl_path):
        return jsonify({"error": "PKL file not found for current progress"}), 404
    
    if test_type == "robot_nav":
        with open(pkl_path, "rb") as pkl_file:
            query_tree = RemapUnpickler(pkl_file).load()
        
        # get the time taken for the options
        for choice in choices_str:
            if choice == '0':
                query_tree = query_tree.children[0]
            else:
                query_tree = query_tree.children[1]
        
        features_matrix = query_tree.query_summary['features_matrix']
        
    # Read and encode images as base64
    with open(image1_path, "rb") as img1_file:
        image1_data = base64.b64encode(img1_file.read()).decode('utf-8')
    
    with open(image2_path, "rb") as img2_file:
        image2_data = base64.b64encode(img2_file.read()).decode('utf-8')
    

    if test_type == "robot_nav":  
        return jsonify({
            "image1": f"data:image/png;base64,{image1_data}",
            "image2": f"data:image/png;base64,{image2_data}",
            "test_type": test_type,
            "condition": user.current_condition_index,
            "question_num": question_num,
            "time_taken": [features_matrix[0][0], features_matrix[1][0]]
        })
    else:
        return jsonify({
            "image1": f"data:image/png;base64,{image1_data}",
            "image2": f"data:image/png;base64,{image2_data}",
            "test_type": test_type,
            "condition": user.current_condition_index,
            "question_num": question_num
        })

@api.route("/submit-choice", methods=["POST"])
@cross_origin(supports_credentials=True)
@csrf_protect.exempt
def submit_choice():
    data = request.get_json()
    participant_id = session.get('user_id')
    choice = data.get("choice")  # 0 for option 1, 1 for option 2
    response_time = data.get("response_time")  # response time in seconds from frontend
    
    if not participant_id:
        return jsonify({"error": "Not logged in"}), 403
    
    if choice not in [0, 1]:
        return jsonify({"error": "Choice must be 0 or 1"}), 400
    
    if response_time is None:
        return jsonify({"error": "response_time is required"}), 400
    
    user = User.query.filter_by(participant_id=participant_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Get current progress
    progress = UserTestProgress.query.filter_by(
        user_id=user.id,
        test_type=user.current_test_type,
        condition_number=user.current_condition
    ).first()
    
    if not progress:
        return jsonify({"error": "Progress not found"}), 404
    
    # Validate minimum response time to prevent accidental clicks
    MIN_RESPONSE_TIME = 0.1  # 100ms minimum
    
    if response_time < MIN_RESPONSE_TIME:
        current_app.logger.warning(f"Response time too fast: {response_time:.2f}s -> {MIN_RESPONSE_TIME}s for user {participant_id}")
        response_time = MIN_RESPONSE_TIME
    
    # Add the choice and response time to their progress
    choices = progress.choices.copy() if progress.choices else []
    response_times = progress.response_times.copy() if progress.response_times else []
    
    choices.append(choice)
    response_times.append(response_time)
    
    progress.choices = choices
    progress.response_times = response_times
    
    # Check if this condition is complete using dynamic question count
    structure = get_survey_structure()
    current_condition_questions = structure[user.current_test_type][user.current_condition]
    show_inter_round_survey = False
    # available_conditions = get_available_conditions()
    
    if len(choices) >= current_condition_questions:
        progress.completed = True
        
        # Check if we need to show inter-round survey (including for the final completion)
        # max_tabletop_condition = available_conditions["tabletop"]
        # max_robot_nav_condition = available_conditions["robot_nav"]
        
        # Check if this is the final completion using randomized order
        # is_final_completion = (user.current_test_type == "robot_nav" and 
        #                      user.current_condition_index >= len(user.robot_nav_condition_order) - 1)

        # Always require inter-round survey, even at final completion
        show_inter_round_survey = True
        
        # Move to next condition using randomized order
        if user.current_test_type == "tabletop":
            # Check if there are more tabletop conditions in the randomized order
            if user.current_condition_index + 1 < len(user.tabletop_condition_order):
                # Move to next tabletop condition in randomized order
                user.current_condition_index += 1
                user.current_condition = user.tabletop_condition_order[user.current_condition_index]
            else:
                # Move from tabletop to robot_nav, reset index
                user.current_test_type = "robot_nav"
                user.current_condition_index = 0
                user.current_condition = user.robot_nav_condition_order[0]
        elif user.current_test_type == "robot_nav":
            # Check if there are more robot_nav conditions in the randomized order
            if user.current_condition_index + 1 < len(user.robot_nav_condition_order):
                # Move to next robot_nav condition in randomized order
                user.current_condition_index += 1
                user.current_condition = user.robot_nav_condition_order[user.current_condition_index]
            else:
                # All tests complete for robot_nav; still require inter-round survey.
                # Do not advance further; completion is finalized after survey submission.
                db.session.commit()
                return jsonify({
                    "message": "Final condition completed. Inter-round survey required.",
                    "completed": False,
                    "show_inter_round_survey": True
                })
    
    db.session.commit()
    
    return jsonify({
        "message": "Choice recorded successfully",
        "completed": False,
        "show_inter_round_survey": show_inter_round_survey
    })

@api.route("/submit-inter-round-survey", methods=["POST"])
@cross_origin(supports_credentials=True)
@csrf_protect.exempt
def submit_inter_round_survey():
    participant_id = session.get('user_id')
    data = request.get_json()
    
    if not participant_id:
        return jsonify({"error": "Not logged in"}), 403
    
    user = User.query.filter_by(participant_id=participant_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Find the most recently completed progress that doesn't have survey completed
    completed_progress = UserTestProgress.query.filter_by(
        user_id=user.id,
        completed=True,
        inter_round_survey_completed=False
    ).order_by(UserTestProgress.id.desc()).first()
    
    if not completed_progress:
        return jsonify({"error": "No pending inter-round survey found"}), 400
    
    # Determine if the completed condition was the final one for its test type
    if completed_progress.test_type == "tabletop":
        order = user.tabletop_condition_order or []
    else:
        order = user.robot_nav_condition_order or []
    try:
        idx_in_order = order.index(completed_progress.condition_number)
        is_final_for_test_type = (idx_in_order == len(order) - 1)
    except ValueError:
        is_final_for_test_type = False

    # Validate required scale fields (1-7)
    required_scale_fields = [
        'mental_demand', 'success_level', 'frustration_level', 
        'trajectory_choice_ease', 'difference_clarity', 'preference_learning', 'attention_check'
    ]
    for field in required_scale_fields:
        value = data.get(field)
        if not isinstance(value, int) or value < 1 or value > 7:
            return jsonify({"error": f"{field} must be an integer between 1 and 7"}), 400

    # Free-text required only if this was the final condition for its test type
    decision_factors = (data.get('decision_factors') or '').strip()
    if is_final_for_test_type and not decision_factors:
        return jsonify({"error": "Decision factors response is required"}), 400
    
    # Check if survey response already exists (shouldn't happen, but safety check)
    existing_response = InterRoundSurveyResponse.query.filter_by(
        user_id=user.id,
        test_type=completed_progress.test_type,
        condition_number=completed_progress.condition_number
    ).first()
    
    if existing_response:
        return jsonify({"error": "Survey response already exists for this condition"}), 400
    
    # Create survey response
    # Compute attention check pass (1 if value == 3 else 0)
    attention_check_value = data['attention_check']
    expected = session.get('attention_check_expected', 3)
    attention_check_pass = 1 if attention_check_value == expected else 0

    survey_response = InterRoundSurveyResponse(
        user_id=user.id,
        test_type=completed_progress.test_type,
        condition_number=completed_progress.condition_number,
        mental_demand=data['mental_demand'],
        success_level=data['success_level'],
        frustration_level=data['frustration_level'],
        trajectory_choice_ease=data['trajectory_choice_ease'],
        difference_clarity=data['difference_clarity'],
        preference_learning=data['preference_learning'],
        attention_check_pass=attention_check_pass,
        decision_factors=decision_factors if is_final_for_test_type else ""
    )
    
    db.session.add(survey_response)
    
    # Mark survey as completed
    completed_progress.inter_round_survey_completed = True
    db.session.commit()
    
    # Determine if this survey completion finishes the entire study
    all_completed = compute_all_completed(user)
    
    return jsonify({
        "message": "Inter-round survey completed successfully",
        "success": True,
        "all_completed": all_completed
    })

@api.route("/check-completion", methods=["GET"])
@cross_origin(supports_credentials=True)
@csrf_protect.exempt
def check_completion():
    participant_id = session.get('user_id')
    if not participant_id:
        return jsonify({"error": "Not logged in"}), 403
    user = User.query.filter_by(participant_id=participant_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({
        "all_completed": compute_all_completed(user)
    })

@api.route("/check-pre-activity-survey", methods=["GET"])
@cross_origin(supports_credentials=True)
@csrf_protect.exempt
def check_pre_activity_survey():
    """Check if user has completed pre-activity survey (age and sex filled)"""
    participant_id = session.get('user_id')
    
    current_app.logger.info(f"Checking pre-activity survey for user: {participant_id}")
    
    if not participant_id:
        return jsonify({"error": "Not logged in"}), 403
    
    user = User.query.filter_by(participant_id=participant_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 403
    
    # Check if both age and sex are filled
    is_completed = user.age is not None and user.sex is not None and user.sex.strip() != ""
    
    return jsonify({
        "completed": is_completed,
        "age": user.age,
        "sex": user.sex
    })

@api.route("/submit-pre-activity-survey", methods=["POST"])
@cross_origin(supports_credentials=True)
@csrf_protect.exempt
def submit_pre_activity_survey():
    participant_id = session.get('user_id')
    data = request.get_json()
    
    if not participant_id:
        return jsonify({"error": "Not logged in"}), 403
    
    age = data.get("age")
    sex = data.get("sex")
    
    if not age or not sex:
        return jsonify({"error": "Age and sex are required"}), 400
    
    if not isinstance(age, int) or age < 1 or age > 120:
        return jsonify({"error": "Age must be a number between 1 and 120"}), 400
    
    if not isinstance(sex, str) or sex.strip() == "":
        return jsonify({"error": "Sex must be a non-empty string"}), 400
    
    user = User.query.filter_by(participant_id=participant_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Update user with pre-activity survey data
    user.age = age
    user.sex = sex.strip()
    db.session.commit()
    
    return jsonify({
        "message": "Pre-activity survey submitted successfully",
        "success": True
    })

