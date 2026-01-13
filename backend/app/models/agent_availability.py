"""
经纪人时间表数据模型
"""
from sqlalchemy import Column, Integer, Date, Boolean, DateTime, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class AgentAvailability(Base):
    """经纪人可用时间表 - 支持预约时间管理"""
    __tablename__ = "agent_availability"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    agent_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="经纪人ID")
    available_date = Column(Date, nullable=False, index=True, comment="可用日期")
    available_slots = Column(JSON, nullable=True, comment="可用时段数组，格式：[{'start': '09:00', 'end': '12:00'}, ...]")
    is_fully_booked = Column(Boolean, default=False, comment="是否已全部预约")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    agent = relationship("User", backref="availability_slots")
    
    # 唯一约束
    __table_args__ = (
        UniqueConstraint('agent_id', 'available_date', name='uq_agent_availability'),
    )
    
    def __repr__(self):
        return f"<AgentAvailability(agent_id={self.agent_id}, available_date={self.available_date})>"
