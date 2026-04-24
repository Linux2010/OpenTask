"""
Bot Task Log Model

SQLAlchemy model for bot_task_log table.
"""

from sqlalchemy import Column, BigInteger, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class BotTaskLog(Base):
    """Bot task log model"""
    
    __tablename__ = "bot_task_log"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_id = Column(BigInteger, nullable=False)
    action = Column(String(50), nullable=False)
    message = Column(Text)
    old_status = Column(String(20))
    new_status = Column(String(20))
    operator = Column(String(50))
    created_time = Column(DateTime, nullable=False, server_default=func.now())
    
    def __repr__(self):
        return f"<BotTaskLog(id={self.id}, task_id={self.task_id}, action={self.action})>"