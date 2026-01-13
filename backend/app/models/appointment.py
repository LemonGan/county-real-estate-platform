"""
看房预约数据模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Date, Time, Text, ForeignKey, Enum as SQLEnum, SmallInteger, Boolean, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class AppointmentStatus(int, enum.Enum):
    """预约状态枚举"""
    CANCELLED = 0  # 已取消
    PENDING = 1  # 待确认
    CONFIRMED = 2  # 已确认
    COMPLETED = 3  # 已完成


class AppointmentType(int, enum.Enum):
    """预约类型枚举"""
    ON_SITE = 1  # 实地看房
    VIDEO = 2  # 视频看房
    VR = 3  # VR看房


class Appointment(Base):
    """看房预约表 - 看房预约核心业务流程"""
    __tablename__ = "appointments"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    appointment_no = Column(String(30), unique=True, nullable=True, index=True, comment="预约编号")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="用户ID")
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True, comment="房源ID")
    agent_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="经纪人ID")
    
    # 预约详情
    appointment_date = Column(Date, nullable=False, index=True, comment="预约日期")
    appointment_time = Column(Time, nullable=False, comment="预约时间")
    duration_minutes = Column(Integer, default=30, comment="预约时长（分钟）")
    appointment_type = Column(SmallInteger, default=1, comment="预约类型：1实地看房，2视频看房，3VR看房")
    participants_count = Column(SmallInteger, default=2, comment="参与人数")
    
    # 联系信息
    contact_name = Column(String(50), nullable=False, comment="联系人姓名")
    contact_phone = Column(String(20), nullable=False, comment="联系电话")
    contact_wechat = Column(String(50), nullable=True, comment="微信号")
    special_requirements = Column(Text, nullable=True, comment="特殊要求")
    
    # 状态工作流
    status = Column(SmallInteger, default=1, index=True, comment="状态：0已取消，1待确认，2已确认，3已完成")
    confirmation_status = Column(SmallInteger, default=0, comment="确认状态")
    cancel_reason = Column(Text, nullable=True, comment="取消原因")
    cancel_time = Column(DateTime(timezone=True), nullable=True, comment="取消时间")
    
    # 看房反馈
    feedback_score = Column(SmallInteger, nullable=True, comment="满意度评分1-5")
    feedback_comment = Column(Text, nullable=True, comment="反馈评论")
    is_interested = Column(Boolean, nullable=True, comment="是否感兴趣")
    next_followup = Column(DateTime(timezone=True), nullable=True, comment="下次跟进时间")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    confirmed_at = Column(DateTime(timezone=True), nullable=True, comment="确认时间")
    completed_at = Column(DateTime(timezone=True), nullable=True, comment="完成时间")
    deleted_at = Column(DateTime(timezone=True), nullable=True, comment="删除时间（软删除）")
    
    # 关系
    property = relationship("Property", backref="appointments")
    user = relationship("User", foreign_keys=[user_id], backref="appointments")
    agent = relationship("User", foreign_keys=[agent_id], backref="agent_appointments")
    
    # 复合索引
    __table_args__ = (
        Index('idx_appointments_composite', 'user_id', 'property_id', 'status', 'appointment_date'),
        Index('idx_appointments_time_range', 'appointment_date', 'appointment_time', 'status'),
    )
    
    def __repr__(self):
        return f"<Appointment(id={self.id}, property_id={self.property_id}, user_id={self.user_id}, status={self.status})>"
