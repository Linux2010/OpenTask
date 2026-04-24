"""
Bot Task Model

SQLAlchemy model for bot_task table.
"""

from sqlalchemy import Column, BigInteger, String, Text, Integer, DateTime, SmallInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class BotTask(Base):
    """Bot task model"""
    
    __tablename__ = "bot_task"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_name = Column(String(100), nullable=False)
    task_description = Column(Text)
    task_params = Column(Text)
    assigned_to = Column(String(50), nullable=False)
    priority = Column(String(10), nullable=False, default="P2")
    status = Column(String(20), nullable=False, default="pending")
    progress = Column(Integer, default=0)
    created_time = Column(DateTime, nullable=False, server_default=func.now())
    started_time = Column(DateTime)
    completed_time = Column(DateTime)
    result = Column(Text)
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    max_retry = Column(Integer, default=3)
    created_by = Column(String(50), nullable=False)
    deleted = Column(SmallInteger, default=0)
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<BotTask(id={self.id}, name={self.task_name}, status={self.status})>"