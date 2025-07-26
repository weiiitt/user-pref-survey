from flask import Blueprint, Response, current_app, jsonify, request
from flask_cors import cross_origin
from server.user.models import User, UserTestProgress

api = Blueprint("api", __name__, url_prefix="/api")

@api.route("/get-user-progress", methods=["GET"])
@cross_origin()
def get_user_progress() -> int:
    user_id = request.args.get("user_id")
    user = User.query.filter_by(id=user_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    test_type, condition, question_num = user.check_user_progress()
    
    if test_type == "tabletop":
        return jsonify({"total_questions_answered": condition * 10 + question_num})
    elif test_type == "robot_nav":
        return jsonify({"total_questions_answered": 30 + condition * 10 + question_num})
    else:
        raise RuntimeError(f"Invalid test type: {test_type}")

