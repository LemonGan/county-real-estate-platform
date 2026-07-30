"""短视频互动数据模型。"""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, SmallInteger, Text, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class VideoLike(Base):
    """用户对短视频的点赞记录。"""
    __tablename__ = "video_likes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    video_id = Column(Integer, ForeignKey("short_videos.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", foreign_keys=[user_id])
    video = relationship("ShortVideo", foreign_keys=[video_id])

    __table_args__ = (
        UniqueConstraint("user_id", "video_id", name="uq_video_likes_user_video"),
        Index("idx_video_likes_video_created", "video_id", "created_at"),
    )


class VideoFavorite(Base):
    """用户对短视频的收藏记录。"""
    __tablename__ = "video_favorites"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    video_id = Column(Integer, ForeignKey("short_videos.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", foreign_keys=[user_id])
    video = relationship("ShortVideo", foreign_keys=[video_id])

    __table_args__ = (
        UniqueConstraint("user_id", "video_id", name="uq_video_favorites_user_video"),
        Index("idx_video_favorites_video_created", "video_id", "created_at"),
    )


class VideoComment(Base):
    """短视频评论；删除采用软删除，保留回复链路。"""
    __tablename__ = "video_comments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    video_id = Column(Integer, ForeignKey("short_videos.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey("video_comments.id", ondelete="SET NULL"), nullable=True, index=True)
    content = Column(Text, nullable=False)
    like_count = Column(Integer, nullable=False, default=0)
    status = Column(SmallInteger, nullable=False, default=0, index=True, comment="0待审核，1已公开，2已驳回")
    reviewed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    review_note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", foreign_keys=[user_id])
    video = relationship("ShortVideo", foreign_keys=[video_id])
    parent = relationship("VideoComment", remote_side=[id], foreign_keys=[parent_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])

    __table_args__ = (
        Index("idx_video_comments_video_created", "video_id", "created_at"),
    )


class VideoCommentLike(Base):
    """用户对短视频评论的点赞记录。"""
    __tablename__ = "video_comment_likes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    comment_id = Column(Integer, ForeignKey("video_comments.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", foreign_keys=[user_id])
    comment = relationship("VideoComment", foreign_keys=[comment_id])

    __table_args__ = (
        UniqueConstraint("user_id", "comment_id", name="uq_video_comment_likes_user_comment"),
        Index("idx_video_comment_likes_comment_created", "comment_id", "created_at"),
    )
