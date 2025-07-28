from flask import Blueprint, Response, current_app, jsonify, request, send_file
from flask_cors import cross_origin
from server.user.models import User, UserTestProgress
from server.database import db
from server.extensions import csrf_protect
import os
import base64
import time

api = Blueprint("api", __name__, url_prefix="/api")

@api.route("/test", methods=["GET"])
@cross_origin(supports_credentials=True)
@csrf_protect.exempt
def test_route():
    return jsonify({"message": "API working!"})

@api.route("/get-user-progress", methods=["GET"])
@cross_origin(supports_credentials=True)
@csrf_protect.exempt
def get_user_progress() -> int:
    user_id = request.args.get("user_id")
    user = User.query.filter_by(id=user_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    test_type, condition, question_num = user.check_user_progress()
    
    if test_type == "tabletop":
        return jsonify({"percent_answered": (condition * 10 + question_num) / 60})
    elif test_type == "robot_nav":
        return jsonify({"percent_answered": (30 + condition * 10 + question_num) / 60})
    else:
        raise RuntimeError(f"Invalid test type: {test_type}")

@api.route("/get-question-images", methods=["GET"])
@cross_origin(supports_credentials=True)
@csrf_protect.exempt
def get_question_images():
    # Get participant ID from session
    from flask import session
    participant_id = session.get('user_id')
    current_app.logger.info(f"Fetching images for participant: {participant_id}")
    
    if not participant_id:
        return jsonify({"error": "Not logged in"}), 401
    
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
        folder_name = f"RobotNav-v{condition}"  # Assuming similar naming pattern
        base_filename = f"RobotNav-v{condition}_query_{question_num}_{choices_str}_"
    
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
        "condition": condition,
        "question_num": question_num,
        "question_start_time": time.time()
    })

@api.route("/submit-choice", methods=["POST"])
@cross_origin(supports_credentials=True)
@csrf_protect.exempt
def submit_choice():
    from flask import session
    data = request.get_json()
    participant_id = session.get('user_id')
    choice = data.get("choice")  # 0 for option 1, 1 for option 2
    question_start_time = data.get("question_start_time")  # timestamp from when question was shown
    
    if not participant_id:
        return jsonify({"error": "Not logged in"}), 401
    
    if choice not in [0, 1]:
        return jsonify({"error": "Choice must be 0 or 1"}), 400
    
    if question_start_time is None:
        return jsonify({"error": "question_start_time is required"}), 400
    
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
    
    # Calculate response time with validation
    response_time = time.time() - question_start_time
    
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
    
    # Check if this condition is complete (assuming 10 questions per condition)
    questions_per_condition = 10
    show_inter_round_survey = False
    
    if len(choices) >= questions_per_condition:
        progress.completed = True
        
        # Check if we need to show inter-round survey (not for the final completion)
        is_final_completion = (user.current_condition == 2 and user.current_test_type == "robot_nav")
        
        if not is_final_completion:
            show_inter_round_survey = True
        
        # Move to next condition or test type
        if user.current_condition < 2:  # Move to next condition
            user.current_condition += 1
        elif user.current_test_type == "tabletop":  # Move to robot_nav
            user.current_test_type = "robot_nav"
            user.current_condition = 0
        else:  # All tests complete
            db.session.commit()
            return jsonify({
                "message": "All tests completed!",
                "completed": True,
                "show_inter_round_survey": False
            })
    
    db.session.commit()
    
    # Return current status
    test_type, condition, question_num = user.check_user_progress()
    return jsonify({
        "message": "Choice recorded successfully",
        "completed": False,
        "show_inter_round_survey": show_inter_round_survey,
        "current_test_type": test_type,
        "current_condition": condition,
        "current_question": question_num
    })

@api.route("/submit-inter-round-survey", methods=["POST"])
@cross_origin(supports_credentials=True)
@csrf_protect.exempt
def submit_inter_round_survey():
    from flask import session
    participant_id = session.get('user_id')
    
    if not participant_id:
        return jsonify({"error": "Not logged in"}), 401
    
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
    
    # Mark survey as completed
    completed_progress.inter_round_survey_completed = True
    db.session.commit()
    
    return jsonify({
        "message": "Inter-round survey completed successfully",
        "success": True
    })

