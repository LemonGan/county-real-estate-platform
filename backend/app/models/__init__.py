"""
数据模型模块
"""
from app.models.user import User
from app.models.user_preference import UserPreference
from app.models.user_behavior import UserBehavior
from app.models.property import Property, PropertyStatus, PropertyType, TransactionType
from app.models.property_image import PropertyImage
from app.models.property_favorite import PropertyFavorite
from app.models.property_review import PropertyReview
from app.models.appointment import Appointment, AppointmentStatus, AppointmentType
from app.models.agent_availability import AgentAvailability
from app.models.short_video import ShortVideo
from app.models.video_recommendation import VideoRecommendation
from app.models.audit_log import AuditLog
from app.models.feedback import Feedback
from app.models.message import Message

__all__ = [
    "User",
    "UserPreference",
    "UserBehavior",
    "Property",
    "PropertyStatus",
    "PropertyType",
    "TransactionType",
    "PropertyImage",
    "PropertyFavorite",
    "PropertyReview",
    "Appointment",
    "AppointmentStatus",
    "AppointmentType",
    "AgentAvailability",
    "ShortVideo",
    "VideoRecommendation",
    "AuditLog",
    "Feedback",
    "Message",
]
