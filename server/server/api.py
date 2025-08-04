from flask import Blueprint, Response, current_app, jsonify, request, send_file, session
from flask_cors import cross_origin
from server.user.models import User, UserTestProgress, InterRoundSurveyResponse
from server.database import db
from server.extensions import csrf_protect
import os
import base64

api = Blueprint("api", __name__, url_prefix="/api")

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

def calculate_user_progress_internal(user):
    """
    Calculate user progress based on randomized condition order.
    Returns dict with current_progress and total_questions.
    """
    test_type, condition, question_num = user.check_user_progress()
    structure = get_survey_structure()
    
    # Calculate total questions dynamically
    tabletop_total = sum(structure["tabletop"].values())
    robot_nav_total = sum(structure["robot_nav"].values())
    total_questions = tabletop_total + robot_nav_total
    
    if test_type == "tabletop":
        # Sum questions from completed tabletop conditions based on randomized order
        completed_tabletop = 0
        if user.current_condition_index > 0:
            for i in range(user.current_condition_index):
                completed_condition = user.tabletop_condition_order[i]
                completed_tabletop += structure["tabletop"].get(completed_condition, 0)
        
        current_progress = completed_tabletop + question_num + 1
    else:  # robot_nav
        # Sum ALL completed tabletop questions (user finished all tabletop conditions)
        completed_tabletop = 0
        for condition in user.tabletop_condition_order:
            completed_tabletop += structure["tabletop"].get(condition, 0)
        
        # Sum questions from completed robot_nav conditions based on randomized order
        completed_robot_nav = 0
        if user.current_condition_index > 0:
            for i in range(user.current_condition_index):
                completed_condition = user.robot_nav_condition_order[i]
                completed_robot_nav += structure["robot_nav"].get(completed_condition, 0)
        
        current_progress = completed_tabletop + completed_robot_nav + question_num + 1
    
    return {
        "current_progress": current_progress,
        "total_questions": total_questions
    }

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
    else:  # robot_nav
        folder_name = f"GrassStreetNav-v{condition}"  # Assuming similar naming pattern
        base_filename = f"GrassStreetNav-v{condition}_query_{question_num}_{choices_str}_"
    
    # Construct full paths (assets are at /app/assets in Docker container)
    assets_path = os.path.join("/app", "assets", "user_study", folder_name)
    image1_path = os.path.join(assets_path, base_filename + "1.png")
    image2_path = os.path.join(assets_path, base_filename + "2.png")
    
    current_app.logger.info(f"Looking for images at:")
    current_app.logger.info(f"  Image1: {image1_path}")
    current_app.logger.info(f"  Image2: {image2_path}")
    current_app.logger.info(f"  Assets path exists: {os.path.exists(assets_path)}")
    current_app.logger.info(f"  Image1 exists: {os.path.exists(image1_path)}")
    current_app.logger.info(f"  Image2 exists: {os.path.exists(image2_path)}")
    
    # Check if images exist
    if not os.path.exists(image1_path) or not os.path.exists(image2_path):
        return jsonify({"error": "Images not found for current progress"}), 404
    
    # Read and encode images as base64
    with open(image1_path, "rb") as img1_file:
        image1_data = base64.b64encode(img1_file.read()).decode('utf-8')
    
    with open(image2_path, "rb") as img2_file:
        image2_data = base64.b64encode(img2_file.read()).decode('utf-8')
    
    return jsonify({
        "image1": f"data:image/png;base64,{image1_data}",
        "image2": f"data:image/png;base64,{image2_data}",
        "test_type": test_type,
        "condition": user.current_condition_index,
        "question_num": question_num,
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
    available_conditions = get_available_conditions()
    
    if len(choices) >= current_condition_questions:
        progress.completed = True
        
        # Check if we need to show inter-round survey (not for the final completion)
        max_tabletop_condition = available_conditions["tabletop"]
        max_robot_nav_condition = available_conditions["robot_nav"]
        
        # Check if this is the final completion using randomized order
        is_final_completion = (user.current_test_type == "robot_nav" and 
                             user.current_condition_index >= len(user.robot_nav_condition_order) - 1)
        
        if not is_final_completion:
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
                # All tests complete
                db.session.commit()
                return jsonify({
                    "message": "All tests completed!",
                    "completed": True,
                    "show_inter_round_survey": False
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
    
    # Validate survey data
    required_scale_fields = [
        'mental_demand', 'success_level', 'frustration_level', 
        'trajectory_choice_ease', 'difference_clarity', 'preference_learning'
    ]
    
    for field in required_scale_fields:
        value = data.get(field)
        if not isinstance(value, int) or value < 1 or value > 5:
            return jsonify({"error": f"{field} must be an integer between 1 and 5"}), 400
    
    decision_factors = data.get('decision_factors', '').strip()
    if not decision_factors:
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
        decision_factors=decision_factors
    )
    
    db.session.add(survey_response)
    
    # Mark survey as completed
    completed_progress.inter_round_survey_completed = True
    db.session.commit()
    
    return jsonify({
        "message": "Inter-round survey completed successfully",
        "success": True
    })

@api.route("/check-pre-activity-survey", methods=["GET"])
@cross_origin(supports_credentials=True)
@csrf_protect.exempt
def check_pre_activity_survey():
    """Check if user has completed pre-activity survey (age and sex filled)"""
    participant_id = session.get('user_id')
    
    if not participant_id:
        return jsonify({"error": "Not logged in"}), 403
    
    user = User.query.filter_by(participant_id=participant_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
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

