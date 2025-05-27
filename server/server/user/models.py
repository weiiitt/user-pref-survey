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
    uuid = Column(db.String(36), unique=True, nullable=False, index=True)
    email = Column(db.String(80), unique=True, nullable=True)
    created_at = Column(
        db.DateTime, nullable=False, default=dt.datetime.now(dt.timezone.utc)
    )
    belief = Column(db.LargeBinary, nullable=True)

    @hybrid_property
    def password(self):
        """Hashed password."""
        return self._password

    @password.setter
    def password(self, value):
        """Set password."""
        self._password = bcrypt.generate_password_hash(value)

    def check_password(self, value):
        """Check password."""
        return bcrypt.check_password_hash(self._password, value)

    @property
    def full_name(self):
        """Full user name."""
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        """Represent instance as a unique string."""
        return f"<User(id={self.id}, uuid={self.uuid!r})>"


class AnonymousUser(UserMixin):
    """An anonymous user for session tracking."""
    def __init__(self, uuid):
        self.id = uuid

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


class GeneratedRoute(PkModel):
    __tablename__ = "generated_routes"

    route_guid = Column(db.String(36), unique=True, nullable=False, index=True) # External unique ID
    distance = Column(db.Float, nullable=False)
    elevation_gain = Column(db.Float, nullable=False)
    avg_grade = Column(db.Float, nullable=False)
    left_turns = Column(db.Integer, nullable=False)
    right_turns = Column(db.Integer, nullable=False)
    travel_time = Column(db.Float, nullable=False)
    source_node_id = Column(db.String(255), nullable=False) # Assuming node IDs can be long
    source_coordinates = Column(db.JSON, nullable=False)
    destination_node_id = Column(db.String(255), nullable=False)
    destination_coordinates = Column(db.JSON, nullable=False)
    response_id = Column(db.Integer, nullable=False)
    created_at = Column(
        db.DateTime, nullable=False, default=dt.datetime.now(dt.timezone.utc)
    )
    trajectory_obj = Column(db.LargeBinary, nullable=False)
    reward_weights = Column(db.JSON, nullable=False)

    # preferences = relationship("RoutePreference", backref="selected_route_detail") # If one route can be selected many times

    def __init__(self, route_guid, distance, elevation_gain, avg_grade, left_turns, right_turns, travel_time, source_node_id, source_coordinates, destination_node_id, destination_coordinates, **kwargs):
        super().__init__(
            route_guid=route_guid,
            distance=distance,
            elevation_gain=elevation_gain,
            avg_grade=avg_grade,
            left_turns=left_turns,
            right_turns=right_turns,
            travel_time=travel_time,
            source_node_id=source_node_id,
            source_coordinates=source_coordinates,
            destination_node_id=destination_node_id,
            destination_coordinates=destination_coordinates,
            **kwargs
        )

    def __repr__(self):
        return f"<GeneratedRoute(id={self.id}, route_guid={self.route_guid})>"


class RoutePreference(PkModel):
    __tablename__ = "route_preferences"

    user_uuid = Column(db.String(36), nullable=False, index=True) # UUIDs are 36 chars
    selected_generated_route_id = reference_col("generated_routes", nullable=False) # Foreign Key
    # Relationship to access the full GeneratedRoute object if needed
    selected_route = relationship("GeneratedRoute", foreign_keys=[selected_generated_route_id])
    
    presented_routes_ids = Column(db.JSON, nullable=False) # Storing as JSON array of GeneratedRoute.id (integers)
    created_at = Column(
        db.DateTime, nullable=False, default=dt.datetime.now(dt.timezone.utc)
    )

    def __init__(self, user_uuid, selected_generated_route_id, presented_routes_ids, **kwargs):
        """Create instance."""
        super().__init__(
            user_uuid=user_uuid,
            selected_generated_route_id=selected_generated_route_id,
            presented_routes_ids=presented_routes_ids,
            **kwargs
        )

    def __repr__(self):
        """Represent instance as a unique string."""
        return f"<RoutePreference(user_uuid={self.user_uuid}, selected_generated_route_id={self.selected_generated_route_id})>"
