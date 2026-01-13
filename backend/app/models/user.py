"""
用户数据模型
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, SmallInteger, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class User(Base):
    """用户表 - 支持微信登录、角色权限、地理位置管理"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # 微信相关
    openid = Column(String(100), unique=True, nullable=True, index=True, comment="微信openid")
    unionid = Column(String(100), unique=True, nullable=True, index=True, comment="微信unionid")
    session_key = Column(String(100), nullable=True, comment="微信session_key")
    subscribe_scene = Column(String(100), nullable=True, comment="关注场景")
    subscribe_time = Column(DateTime(timezone=True), nullable=True, comment="关注时间")
    
    # 登录信息
    phone = Column(String(20), unique=True, index=True, nullable=False, comment="手机号")
    email = Column(String(100), nullable=True, comment="邮箱")
    hashed_password = Column(String(255), nullable=True, comment="加密密码")
    
    # 基本信息
    nickname = Column(String(50), nullable=True, comment="昵称")
    avatar = Column(String(500), nullable=True, comment="头像URL")
    real_name = Column(String(50), nullable=True, comment="真实姓名")
    id_card = Column(String(18), nullable=True, comment="身份证号")
    gender = Column(SmallInteger, nullable=True, comment="性别：0未知，1男，2女")
    
    # 县域特色 - 地理位置
    current_city = Column(String(50), nullable=True, comment="当前城市")
    hometown_city = Column(String(50), nullable=True, index=True, comment="家乡城市（返乡用户关键字段）")
    preferred_districts = Column(JSON, nullable=True, comment="偏好区域数组")
    
    # 角色权限
    user_type = Column(SmallInteger, default=1, comment="用户类型：1普通用户，2改善用户，3投资用户")
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_superuser = Column(Boolean, default=False, comment="是否超级用户")
    is_verified = Column(Boolean, default=False, comment="是否实名认证")
    is_agent = Column(Boolean, default=False, comment="是否经纪人")
    agent_license = Column(String(50), nullable=True, comment="经纪人执业证号")
    
    # 营销分析
    source_channel = Column(String(50), nullable=True, comment="来源渠道")
    utm_campaign = Column(String(100), nullable=True, comment="UTM活动")
    registration_ip = Column(String(50), nullable=True, comment="注册IP")
    
    # 状态管理
    status = Column(SmallInteger, default=1, comment="状态：1正常，0禁用")
    last_login_at = Column(DateTime(timezone=True), nullable=True, comment="最后登录时间")
    last_login_ip = Column(String(50), nullable=True, comment="最后登录IP")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    deleted_at = Column(DateTime(timezone=True), nullable=True, comment="删除时间（软删除）")
    
    # 关系
    preferences = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    behaviors = relationship("UserBehavior", back_populates="user", cascade="all, delete-orphan")
    favorites = relationship("PropertyFavorite", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, phone={self.phone}, nickname={self.nickname})>"
