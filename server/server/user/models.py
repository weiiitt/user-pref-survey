# -*- coding: utf-8 -*-
"""User models."""
import datetime as dt

from flask_login import UserMixin
from sqlalchemy.ext.hybrid import hybrid_property

from server.database import Column, PkModel, db, reference_col, relationship
from server.extensions import bcrypt


class Role(PkModel):
    """A role for a user."""

    __tablename__ = "roles"
    name = Column(db.String(80), unique=True, nullable=False)
    user_id = reference_col("users", nullable=True)
    user = relationship("User", backref="roles")

    def __init__(self, name, **kwargs):
        """Create instance."""
        super().__init__(name=name, **kwargs)

    def __repr__(self):
        """Represent instance as a unique string."""
        return f"<Role({self.name})>"


class User(UserMixin, PkModel):
    """A user of the app."""

    __tablename__ = "users"
    participant_id = Column(db.String(4), unique=True, nullable=False, index=True)
    created_at = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    current_test_type = Column(db.String(20), nullable=False, default="tabletop")
    current_condition = Column(db.Integer, nullable=False, default=0)
    # Randomized condition orders stored as JSON arrays
    tabletop_condition_order = Column(db.JSON, nullable=True)  # e.g., [2, 0, 1]
    robot_nav_condition_order = Column(db.JSON, nullable=True)  # e.g., [1, 2, 0]
    current_condition_index = Column(db.Integer, nullable=False, default=0)  # Index in the randomized order
    age = Column(db.Integer, nullable=True)
    sex = Column(db.String(20), nullable=True)

    def get_current_condition_from_order(self):
        """Get the actual condition number based on randomized order."""
        if self.current_test_type == "tabletop":
            return self.tabletop_condition_order[self.current_condition_index]
        else:  # robot_nav
            return self.robot_nav_condition_order[self.current_condition_index]

    def check_user_progress(self):
        """Check user progress and return (test_type, condition, question_num)."""
        # Use randomized condition order if available
        actual_condition = self.get_current_condition_from_order()
        
        # Get current progress for the user's current test type and condition
        progress = UserTestProgress.query.filter_by(
            user_id=self.id,
            test_type=self.current_test_type,
            condition_number=actual_condition
        ).first()
        
        if progress:
            question_num = len(progress.choices)
        else:
            question_num = 0
            
        return (self.current_test_type, actual_condition, question_num)

    def __repr__(self):
        """Represent instance as a unique string."""
        return f"<User(id={self.id}, participant_id={self.participant_id!r})>"


class UserTestProgress(PkModel):
    """Track user progress through preference tests."""

    __tablename__ = "user_test_progress"
    user_id = reference_col("users", nullable=False)
    test_type = Column(db.String(20), nullable=False)  # "tabletop" or "robot_nav"
    condition_number = Column(db.Integer, nullable=False)  # 0, 1, or 2
    choices = Column(db.JSON, nullable=False, default=list)  # [1, 0, 1, 1, ...]
    response_times = Column(db.JSON, nullable=False, default=list)  # [2.5, 3.1, 1.8, ...] in seconds
    completed = Column(db.Boolean, default=False)
    inter_round_survey_completed = Column(db.Boolean, default=False)
    
    user = relationship("User", backref="test_progress")
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'test_type', 'condition_number'),
    )

    def __repr__(self):
        """Represent instance as a unique string."""
        return f"<UserTestProgress(user_id={self.user_id}, test_type={self.test_type!r}, condition={self.condition_number})>"


class InterRoundSurveyResponse(PkModel):
    """Store inter-round survey responses."""

    __tablename__ = "inter_round_survey_responses"
    user_id = reference_col("users", nullable=False)
    test_type = Column(db.String(20), nullable=False)  # "tabletop" or "robot_nav"
    condition_number = Column(db.Integer, nullable=False)  # 0, 1, or 2
    
    # Scale questions (1-5)
    mental_demand = Column(db.Integer, nullable=False)  # How mentally demanding was the task?
    success_level = Column(db.Integer, nullable=False)  # How successful were you in accomplishing what you were asked to do?
    frustration_level = Column(db.Integer, nullable=False)  # How discourage, irritated, stressed, and annoyed were you?
    trajectory_choice_ease = Column(db.Integer, nullable=False)  # It was easy to choose between the trajectories the robot showed me
    difference_clarity = Column(db.Integer, nullable=False)  # It was easy to tell the difference between the options presented
    preference_learning = Column(db.Integer, nullable=False)  # Through these questions, the robot was able to learn my preferences
    
    # Free response
    decision_factors = Column(db.Text, nullable=False)  # What factors did you consider when choosing between the two robot trajectories?
    
    created_at = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    
    user = relationship("User", backref="inter_round_survey_responses")
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'test_type', 'condition_number'),
    )

    def __repr__(self):
        """Represent instance as a unique string."""
        return f"<InterRoundSurveyResponse(user_id={self.user_id}, test_type={self.test_type!r}, condition={self.condition_number})>"


class AnonymousUser(UserMixin):
    """An anonymous user for session tracking."""
    def __init__(self, participant_id):
        self.id = participant_id

    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        # Flask-Login's UserMixin defaults is_anonymous to True.
        # For our "logged-in" anonymous user, we want this to be False,
        # indicating they have an active session, even if they are "anonymous"
        # in terms of identifiable data.
        return False

    def get_id(self):
        return str(self.id)


