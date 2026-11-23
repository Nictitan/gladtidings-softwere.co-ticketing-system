from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Enum as SQLEnum
from sqlalchemy.sql import func
from database import Base
import enum


class PriorityEnum(str, enum.Enum):
    CRITICAL = "Critical (users blocked)"
    TECHNICAL = "Technical problem (not working properly)"
    ORDINARY = "Ordinary enquiry"


class StatusEnum(str, enum.Enum):
    NEW = "New"
    IN_PROGRESS = "In progress"
    PARKED = "Parked (waiting for information)"
    ESCALATED = "Escalated"
    CLOSED = "Closed"


class SourceEnum(str, enum.Enum):
    REVIEW_PAGE = "Review page"
    PHONE_CALL = "Phone call"
    WHATSAPP = "WhatsApp"
    EMAIL = "Email"


class ProductEnum(str, enum.Enum):
    ZAMED = "Zamed"
    COINFOMAS = "Coinfomas"
    ZAMPREP = "ZamPrep"
    SOFTWARE_DEV = "Software development"
    WEB_DEV = "Web development"
    NETWORKING = "Computer networking"
    IT_TRAINING = "IT training"


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    ticket_number = Column(String, unique=True, index=True, nullable=False)
    
    # Date/time received
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Source
    source = Column(SQLEnum(SourceEnum), nullable=False, default=SourceEnum.REVIEW_PAGE)
    
    # Reporter info
    reporter_name = Column(String, nullable=False)
    school_institution = Column(String, nullable=True)
    contact = Column(String, nullable=True)
    
    # Product/Service
    product = Column(SQLEnum(ProductEnum), nullable=False)
    
    # Description
    description = Column(Text, nullable=False)
    
    # Priority
    priority = Column(SQLEnum(PriorityEnum), nullable=False, default=PriorityEnum.ORDINARY)
    
    # Status
    status = Column(SQLEnum(StatusEnum), nullable=False, default=StatusEnum.NEW)
    
    # Owner
    owner = Column(String, nullable=True)
    
    # First reply date/time
    first_reply_at = Column(DateTime(timezone=True), nullable=True)
    
    # Closed date/time and cause
    closed_at = Column(DateTime(timezone=True), nullable=True)
    cause = Column(Text, nullable=True)
    
    # Escalated to board
    escalated_to_board = Column(Boolean, default=False, nullable=False)
    escalated_at = Column(DateTime(timezone=True), nullable=True)
    
    # FAQ written
    faq_written = Column(Boolean, default=False, nullable=False)
    
    # Feedback sent
    feedback_sent = Column(Boolean, default=False, nullable=False)


class Setting(Base):
    __tablename__ = "settings"

    key = Column(String, primary_key=True)
    value = Column(String, nullable=False)


class TeamMember(Base):
    __tablename__ = "team_members"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)