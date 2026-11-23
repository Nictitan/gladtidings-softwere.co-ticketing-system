from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List
from models import PriorityEnum, StatusEnum, SourceEnum, ProductEnum


class TicketBase(BaseModel):
    source: SourceEnum = SourceEnum.REVIEW_PAGE
    reporter_name: str
    school_institution: Optional[str] = None
    contact: Optional[str] = None
    product: ProductEnum
    description: str
    priority: PriorityEnum = PriorityEnum.ORDINARY
    owner: Optional[str] = None


class TicketCreate(TicketBase):
    pass


class TicketCreatePublic(BaseModel):
    reporter_name: str
    school_institution: Optional[str] = None
    contact: Optional[str] = None
    product: ProductEnum
    working_well: Optional[str] = None
    not_working: Optional[str] = None
    priority: PriorityEnum = PriorityEnum.ORDINARY


class TicketUpdate(BaseModel):
    status: Optional[StatusEnum] = None
    owner: Optional[str] = None
    first_reply_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    cause: Optional[str] = None
    escalated_to_board: Optional[bool] = None
    escalated_at: Optional[datetime] = None
    faq_written: Optional[bool] = None
    feedback_sent: Optional[bool] = None


class TicketResponse(TicketBase):
    id: int
    ticket_number: str
    created_at: datetime
    status: StatusEnum
    first_reply_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    cause: Optional[str] = None
    escalated_to_board: bool
    escalated_at: Optional[datetime] = None
    faq_written: bool
    feedback_sent: bool

    class Config:
        from_attributes = True


class TicketDetail(TicketResponse):
    pass


class SettingsUpdate(BaseModel):
    response_target_critical_hours: Optional[int] = None
    response_target_technical_hours: Optional[int] = None
    response_target_ordinary_hours: Optional[int] = None


class TeamMemberCreate(BaseModel):
    name: str


class TeamMemberResponse(BaseModel):
    id: int
    name: str
    is_active: bool

    class Config:
        from_attributes = True


class FeedbackCreate(BaseModel):
    ticket_number: str
    resolved: str
    response_time: str
    comment: Optional[str] = None


class DashboardStats(BaseModel):
    open_tickets: int
    critical_open: int
    technical_open: int
    ordinary_open: int
    parked_count: int
    escalated_count: int
    sla_met_percent: float


class WeeklySummary(BaseModel):
    week_start: str
    received: int
    closed: int
    critical_received: int
    technical_received: int
    ordinary_received: int
    avg_first_reply_hours: Optional[float]
    sla_met_percent: Optional[float]


class MonthlyReport(BaseModel):
    month: str
    product: str
    priority: str
    tickets_received: int
    tickets_closed: int
    recurring_causes: List[str]
    sla_met_percent: Optional[float]
    escalated_count: int
    faq_written_count: int
    avg_resolution_days: Optional[float]