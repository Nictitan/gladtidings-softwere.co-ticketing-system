from fastapi import FastAPI, Request, Depends, Form, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_, cast, Date
from datetime import datetime, timedelta, date, timezone
from typing import Optional, List
import json

from database import get_db, init_db
from models import Ticket, Setting, TeamMember, PriorityEnum, StatusEnum, SourceEnum, ProductEnum
from schemas import TicketCreate, TicketCreatePublic, TicketUpdate, SettingsUpdate, TeamMemberCreate, FeedbackCreate

app = FastAPI(title="Gladtidings Help Desk")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize DB on startup
init_db()


# ---------- Helper Functions ----------
def get_setting(db: Session, key: str, default: str) -> str:
    setting = db.query(Setting).filter(Setting.key == key).first()
    return setting.value if setting else default


def get_settings_dict(db: Session) -> dict:
    return {
        "response_target_critical_hours": int(get_setting(db, "response_target_critical_hours", "2")),
        "response_target_technical_hours": int(get_setting(db, "response_target_technical_hours", "8")),
        "response_target_ordinary_hours": int(get_setting(db, "response_target_ordinary_hours", "24")),
        "public_base_url": get_setting(db, "public_base_url", ""),
    }


def get_target_hours(db: Session, priority: PriorityEnum) -> int:
    settings = get_settings_dict(db)
    if priority == PriorityEnum.CRITICAL:
        return settings["response_target_critical_hours"]
    elif priority == PriorityEnum.TECHNICAL:
        return settings["response_target_technical_hours"]
    return settings["response_target_ordinary_hours"]


def generate_ticket_number(db: Session) -> str:
    today = datetime.now().strftime("%Y%m%d")
    count = db.query(Ticket).filter(Ticket.ticket_number.like(f"TK-{today}%")).count()
    return f"TK-{today}-{count + 1}"


def calculate_age_hours(created_at: datetime) -> float:
    return round((datetime.now() - created_at.replace(tzinfo=None)).total_seconds() / 3600, 1)


def is_sla_met(ticket: Ticket, db: Session) -> Optional[bool]:
    if not ticket.first_reply_at:
        return None
    target = get_target_hours(db, ticket.priority)
    # Handle timezone: make both naive for comparison
    created = ticket.created_at.replace(tzinfo=None) if ticket.created_at.tzinfo else ticket.created_at
    first_reply = ticket.first_reply_at.replace(tzinfo=None) if ticket.first_reply_at.tzinfo else ticket.first_reply_at
    elapsed = (first_reply - created).total_seconds() / 3600
    return elapsed <= target


# ---------- Routes ----------

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    # Open tickets sorted by priority then age
    priority_order = {
        PriorityEnum.CRITICAL: 0,
        PriorityEnum.TECHNICAL: 1,
        PriorityEnum.ORDINARY: 2,
    }
    
    open_tickets = db.query(Ticket).filter(Ticket.status != StatusEnum.CLOSED).all()
    
    # Sort by priority then age (oldest first)
    open_tickets.sort(key=lambda t: (priority_order.get(t.priority, 99), t.created_at))
    
    # Enrich with computed fields
    tickets_data = []
    for t in open_tickets:
        age = calculate_age_hours(t.created_at)
        target = get_target_hours(db, t.priority)
        sla_status = "pending"
        if t.first_reply_at:
            elapsed = (t.first_reply_at - t.created_at).total_seconds() / 3600
            sla_status = "met" if elapsed <= target else "missed"
        
        tickets_data.append({
            "ticket": t,
            "age_hours": age,
            "target_hours": target,
            "sla_status": sla_status,
            "is_parked": t.status == StatusEnum.PARKED,
        })
    
    # Stats
    stats = {
        "open": len(open_tickets),
        "critical": sum(1 for t in open_tickets if t.priority == PriorityEnum.CRITICAL),
        "technical": sum(1 for t in open_tickets if t.priority == PriorityEnum.TECHNICAL),
        "ordinary": sum(1 for t in open_tickets if t.priority == PriorityEnum.ORDINARY),
        "parked": sum(1 for t in open_tickets if t.status == StatusEnum.PARKED),
        "escalated": sum(1 for t in open_tickets if t.status == StatusEnum.ESCALATED),
    }
    
    # SLA met % for open tickets with replies
    replied = [t for t in open_tickets if t.first_reply_at]
    sla_met = sum(1 for t in replied if is_sla_met(t, db))
    stats["sla_met_pct"] = round(sla_met / len(replied) * 100, 1) if replied else 0
    
    team = db.query(TeamMember).filter(TeamMember.is_active == True).all()
    settings = get_settings_dict(db)
    
    # Build public form URL
    public_form_url = settings.get("public_base_url", "")
    if public_form_url:
        public_form_url = public_form_url.rstrip("/") + "/public"
    else:
        public_form_url = str(request.url_for('public_form'))
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "tickets": tickets_data,
        "stats": stats,
        "team": team,
        "settings": settings,
        "priorities": list(PriorityEnum),
        "statuses": list(StatusEnum),
        "products": list(ProductEnum),
        "sources": list(SourceEnum),
        "public_form_url": public_form_url,
    })


@app.get("/tickets/new", response_class=HTMLResponse)
async def new_ticket_form(request: Request, db: Session = Depends(get_db)):
    team = db.query(TeamMember).filter(TeamMember.is_active == True).all()
    return templates.TemplateResponse("ticket_form.html", {
        "request": request,
        "team": team,
        "priorities": list(PriorityEnum),
        "products": list(ProductEnum),
        "sources": list(SourceEnum),
        "ticket": None,
    })


@app.post("/tickets")
async def create_ticket(
    request: Request,
    source: SourceEnum = Form(...),
    reporter_name: str = Form(...),
    school_institution: str = Form(""),
    contact: str = Form(""),
    product: ProductEnum = Form(...),
    description: str = Form(...),
    priority: PriorityEnum = Form(...),
    owner: str = Form(""),
    db: Session = Depends(get_db),
):
    ticket = Ticket(
        ticket_number=generate_ticket_number(db),
        source=source,
        reporter_name=reporter_name,
        school_institution=school_institution or None,
        contact=contact or None,
        product=product,
        description=description,
        priority=priority,
        owner=owner or None,
        status=StatusEnum.NEW,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    
    # HTMX redirect
    response = HTMLResponse("")
    response.headers["HX-Redirect"] = f"/tickets/{ticket.id}"
    return response


@app.get("/tickets/{ticket_id}", response_class=HTMLResponse)
async def ticket_detail(request: Request, ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    age = calculate_age_hours(ticket.created_at)
    target = get_target_hours(db, ticket.priority)
    sla_status = "pending"
    if ticket.first_reply_at:
        elapsed = (ticket.first_reply_at - ticket.created_at).total_seconds() / 3600
        sla_status = "met" if elapsed <= target else "missed"
    
    team = db.query(TeamMember).filter(TeamMember.is_active == True).all()
    
    return templates.TemplateResponse("ticket_detail.html", {
        "request": request,
        "ticket": ticket,
        "age_hours": age,
        "target_hours": target,
        "sla_status": sla_status,
        "team": team,
        "priorities": list(PriorityEnum),
        "statuses": list(StatusEnum),
        "products": list(ProductEnum),
    })


@app.post("/tickets/{ticket_id}")
async def update_ticket(
    ticket_id: int,
    request: Request,
    status: Optional[StatusEnum] = Form(None),
    owner: Optional[str] = Form(None),
    first_reply_at: Optional[str] = Form(None),
    closed_at: Optional[str] = Form(None),
    cause: Optional[str] = Form(None),
    escalated_to_board: Optional[bool] = Form(None),
    escalated_at: Optional[str] = Form(None),
    faq_written: Optional[bool] = Form(None),
    feedback_sent: Optional[bool] = Form(None),
    db: Session = Depends(get_db),
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Track status changes for first_reply_at auto-set
    old_status = ticket.status
    
    if status is not None:
        ticket.status = status
        # Auto-set first_reply_at when moving from New to In progress
        if old_status == StatusEnum.NEW and status == StatusEnum.IN_PROGRESS and not ticket.first_reply_at:
            ticket.first_reply_at = datetime.now()
    
    if owner is not None:
        ticket.owner = owner or None
    
    if first_reply_at:
        # Make timezone-aware (assume local time, store as UTC)
        dt = datetime.fromisoformat(first_reply_at)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        ticket.first_reply_at = dt
    
    if closed_at:
        dt = datetime.fromisoformat(closed_at)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        ticket.closed_at = dt
    
    if cause is not None:
        ticket.cause = cause or None
    
    if escalated_to_board is not None:
        ticket.escalated_to_board = escalated_to_board
        if escalated_to_board and not ticket.escalated_at:
            ticket.escalated_at = datetime.now()
    
    if escalated_at:
        dt = datetime.fromisoformat(escalated_at)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        ticket.escalated_at = dt
    
    if faq_written is not None:
        ticket.faq_written = faq_written
    
    if feedback_sent is not None:
        ticket.feedback_sent = feedback_sent
    
    # Auto-set closed_at when status changes to Closed
    if status == StatusEnum.CLOSED and not ticket.closed_at:
        ticket.closed_at = datetime.now()
    
    db.commit()
    db.refresh(ticket)
    
    # Return updated partial for HTMX
    age = calculate_age_hours(ticket.created_at)
    target = get_target_hours(db, ticket.priority)
    sla_status = "pending"
    if ticket.first_reply_at:
        elapsed = (ticket.first_reply_at - ticket.created_at).total_seconds() / 3600
        sla_status = "met" if elapsed <= target else "missed"
    
    return templates.TemplateResponse("partials/ticket_row.html", {
        "request": request,
        "ticket": ticket,
        "age_hours": age,
        "target_hours": target,
        "sla_status": sla_status,
        "is_parked": ticket.status == StatusEnum.PARKED,
        "priorities": list(PriorityEnum),
        "statuses": list(StatusEnum),
    })


@app.delete("/tickets/{ticket_id}")
async def delete_ticket(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    db.delete(ticket)
    db.commit()
    return JSONResponse({"success": True, "message": "Ticket deleted"})


@app.post("/tickets/{ticket_id}/reset")
async def reset_ticket(request: Request, ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Reset ticket to NEW status and clear resolution fields
    ticket.status = StatusEnum.NEW
    ticket.closed_at = None
    ticket.cause = None
    ticket.first_reply_at = None
    ticket.escalated_to_board = False
    ticket.escalated_at = None
    ticket.faq_written = False
    ticket.feedback_sent = False
    
    db.commit()
    db.refresh(ticket)
    
    # Return updated ticket row
    age = calculate_age_hours(ticket.created_at)
    target = get_target_hours(db, ticket.priority)
    sla_status = "pending"
    
    return templates.TemplateResponse("partials/ticket_row.html", {
        "request": request,
        "ticket": ticket,
        "age_hours": age,
        "target_hours": target,
        "sla_status": sla_status,
        "is_parked": ticket.status == StatusEnum.PARKED,
        "priorities": list(PriorityEnum),
        "statuses": list(StatusEnum),
    })


@app.post("/tickets/{ticket_id}/park")
async def park_ticket(request: Request, ticket_id: int, db: Session = Depends(get_db)):
    """Put ticket on wait (parked) - dedicated endpoint for better UX"""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    ticket.status = StatusEnum.PARKED
    db.commit()
    db.refresh(ticket)
    
    # Return updated ticket row
    age = calculate_age_hours(ticket.created_at)
    target = get_target_hours(db, ticket.priority)
    sla_status = "pending"
    if ticket.first_reply_at:
        elapsed = (ticket.first_reply_at - ticket.created_at).total_seconds() / 3600
        sla_status = "met" if elapsed <= target else "missed"
    
    return templates.TemplateResponse("partials/ticket_row.html", {
        "request": request,
        "ticket": ticket,
        "age_hours": age,
        "target_hours": target,
        "sla_status": sla_status,
        "is_parked": ticket.status == StatusEnum.PARKED,
        "priorities": list(PriorityEnum),
        "statuses": list(StatusEnum),
    })


@app.get("/public", response_class=HTMLResponse)
async def public_form(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("public_form.html", {
        "request": request,
        "products": list(ProductEnum),
        "priorities": list(PriorityEnum),
    })


@app.post("/public")
async def create_public_ticket(
    request: Request,
    reporter_name: str = Form(...),
    school_institution: str = Form(""),
    contact: str = Form(""),
    product: ProductEnum = Form(...),
    working_well: str = Form(""),
    not_working: str = Form(""),
    priority: PriorityEnum = Form(...),
    db: Session = Depends(get_db),
):
    description = f"What's working well:\n{working_well}\n\nWhat isn't working:\n{not_working}"
    
    ticket = Ticket(
        ticket_number=generate_ticket_number(db),
        source=SourceEnum.REVIEW_PAGE,
        reporter_name=reporter_name,
        school_institution=school_institution or None,
        contact=contact or None,
        product=product,
        description=description,
        priority=priority,
        status=StatusEnum.NEW,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    
    return templates.TemplateResponse("public_thanks.html", {
        "request": request,
        "ticket_number": ticket.ticket_number,
    })


@app.get("/feedback/{ticket_number}", response_class=HTMLResponse)
async def feedback_form(request: Request, ticket_number: str, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.ticket_number == ticket_number).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    return templates.TemplateResponse("feedback_form.html", {
        "request": request,
        "ticket": ticket,
    })


@app.post("/feedback/{ticket_number}")
async def submit_feedback(
    ticket_number: str,
    resolved: str = Form(...),
    response_time: str = Form(...),
    comment: str = Form(""),
    db: Session = Depends(get_db),
):
    ticket = db.query(Ticket).filter(Ticket.ticket_number == ticket_number).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Store feedback in cause field or create separate table later
    feedback_text = f"Feedback: Resolved={resolved}, Response={response_time}, Comment={comment}"
    if ticket.cause:
        ticket.cause += f"\n\n{feedback_text}"
    else:
        ticket.cause = feedback_text
    
    ticket.feedback_sent = True
    db.commit()
    
    return templates.TemplateResponse("feedback_thanks.html", {"request": request})


@app.get("/reports/weekly", response_class=HTMLResponse)
async def weekly_report(request: Request, db: Session = Depends(get_db)):
    # Get last 8 weeks
    weeks = []
    for i in range(8):
        week_start = date.today() - timedelta(days=date.today().weekday() + i * 7)
        week_end = week_start + timedelta(days=6)
        
        received = db.query(Ticket).filter(
            func.date(Ticket.created_at) >= week_start,
            func.date(Ticket.created_at) <= week_end
        ).count()
        
        closed = db.query(Ticket).filter(
            func.date(Ticket.closed_at) >= week_start,
            func.date(Ticket.closed_at) <= week_end
        ).count()
        
        critical = db.query(Ticket).filter(
            func.date(Ticket.created_at) >= week_start,
            func.date(Ticket.created_at) <= week_end,
            Ticket.priority == PriorityEnum.CRITICAL
        ).count()
        
        technical = db.query(Ticket).filter(
            func.date(Ticket.created_at) >= week_start,
            func.date(Ticket.created_at) <= week_end,
            Ticket.priority == PriorityEnum.TECHNICAL
        ).count()
        
        ordinary = db.query(Ticket).filter(
            func.date(Ticket.created_at) >= week_start,
            func.date(Ticket.created_at) <= week_end,
            Ticket.priority == PriorityEnum.ORDINARY
        ).count()
        
        # Avg first reply time
        replied_tickets = db.query(Ticket).filter(
            func.date(Ticket.created_at) >= week_start,
            func.date(Ticket.created_at) <= week_end,
            Ticket.first_reply_at.isnot(None)
        ).all()
        
        avg_reply = None
        sla_met = None
        if replied_tickets:
            total_hours = sum((t.first_reply_at - t.created_at).total_seconds() / 3600 for t in replied_tickets)
            avg_reply = round(total_hours / len(replied_tickets), 1)
            met = sum(1 for t in replied_tickets if is_sla_met(t, db))
            sla_met = round(met / len(replied_tickets) * 100, 1)
        
        weeks.append({
            "week_start": week_start.strftime("%Y-%m-%d"),
            "received": received,
            "closed": closed,
            "critical": critical,
            "technical": technical,
            "ordinary": ordinary,
            "avg_reply": avg_reply,
            "sla_met": sla_met,
        })
    
    return templates.TemplateResponse("weekly_report.html", {
        "request": request,
        "weeks": weeks,
    })


@app.get("/reports/monthly", response_class=HTMLResponse)
async def monthly_report(request: Request, db: Session = Depends(get_db)):
    # Current month
    today = date.today()
    month_start = date(today.year, today.month, 1)
    if today.month == 12:
        next_month = date(today.year + 1, 1, 1)
    else:
        next_month = date(today.year, today.month + 1, 1)
    
    tickets = db.query(Ticket).filter(
        func.date(Ticket.created_at) >= month_start,
        func.date(Ticket.created_at) < next_month
    ).all()
    
    # Group by product and priority
    report_data = {}
    for t in tickets:
        key = (t.product.value, t.priority.value)
        if key not in report_data:
            report_data[key] = {
                "product": t.product.value,
                "priority": t.priority.value,
                "received": 0,
                "closed": 0,
                "causes": [],
                "replied": [],
                "escalated": 0,
                "faq_written": 0,
                "resolution_days": [],
            }
        report_data[key]["received"] += 1
        if t.status == StatusEnum.CLOSED:
            report_data[key]["closed"] += 1
            if t.cause:
                report_data[key]["causes"].append(t.cause)
            if t.closed_at:
                days = (t.closed_at - t.created_at).total_seconds() / 86400
                report_data[key]["resolution_days"].append(days)
        if t.first_reply_at:
            report_data[key]["replied"].append(t)
        if t.escalated_to_board:
            report_data[key]["escalated"] += 1
        if t.faq_written:
            report_data[key]["faq_written"] += 1
    
    rows = []
    for key, data in report_data.items():
        unique_causes = list(set(data["causes"]))[:5]  # Top 5
        sla_met = None
        if data["replied"]:
            met = sum(1 for t in data["replied"] if is_sla_met(t, db))
            sla_met = round(met / len(data["replied"]) * 100, 1)
        avg_res = round(sum(data["resolution_days"]) / len(data["resolution_days"]), 1) if data["resolution_days"] else None
        
        rows.append({
            "product": data["product"],
            "priority": data["priority"],
            "received": data["received"],
            "closed": data["closed"],
            "causes": unique_causes,
            "sla_met": sla_met,
            "escalated": data["escalated"],
            "faq_written": data["faq_written"],
            "avg_resolution": avg_res,
        })
    
    # Sort by product then priority
    priority_order = {p.value: i for i, p in enumerate(PriorityEnum)}
    rows.sort(key=lambda r: (r["product"], priority_order.get(r["priority"], 99)))
    
    return templates.TemplateResponse("monthly_report.html", {
        "request": request,
        "month": month_start.strftime("%Y-%m"),
        "rows": rows,
    })


@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request, db: Session = Depends(get_db)):
    settings = get_settings_dict(db)
    team = db.query(TeamMember).all()
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "settings": settings,
        "team": team,
    })


@app.post("/settings")
async def update_settings(
    request: Request,
    response_target_critical_hours: int = Form(...),
    response_target_technical_hours: int = Form(...),
    response_target_ordinary_hours: int = Form(...),
    public_base_url: str = Form(""),
    db: Session = Depends(get_db),
):
    for key, value in [
        ("response_target_critical_hours", str(response_target_critical_hours)),
        ("response_target_technical_hours", str(response_target_technical_hours)),
        ("response_target_ordinary_hours", str(response_target_ordinary_hours)),
        ("public_base_url", public_base_url.strip()),
    ]:
        setting = db.query(Setting).filter(Setting.key == key).first()
        if setting:
            setting.value = value
        else:
            setting = Setting(key=key, value=value)
            db.add(setting)
    db.commit()
    
    return RedirectResponse(url="/settings?saved=1", status_code=303)


@app.post("/team")
async def add_team_member(
    name: str = Form(...),
    db: Session = Depends(get_db),
):
    member = TeamMember(name=name, is_active=True)
    db.add(member)
    db.commit()
    return RedirectResponse(url="/settings", status_code=303)


@app.post("/team/{member_id}/toggle")
async def toggle_team_member(member_id: int, db: Session = Depends(get_db)):
    member = db.query(TeamMember).filter(TeamMember.id == member_id).first()
    if member:
        member.is_active = not member.is_active
        db.commit()
    return RedirectResponse(url="/settings", status_code=303)


# API endpoints for HTMX partials
@app.get("/api/tickets/open")
async def api_open_tickets(db: Session = Depends(get_db)):
    priority_order = {PriorityEnum.CRITICAL: 0, PriorityEnum.TECHNICAL: 1, PriorityEnum.ORDINARY: 2}
    tickets = db.query(Ticket).filter(Ticket.status != StatusEnum.CLOSED).all()
    tickets.sort(key=lambda t: (priority_order.get(t.priority, 99), t.created_at))
    
    result = []
    for t in tickets:
        age = calculate_age_hours(t.created_at)
        target = get_target_hours(db, t.priority)
        sla_status = "pending"
        if t.first_reply_at:
            elapsed = (t.first_reply_at - t.created_at).total_seconds() / 3600
            sla_status = "met" if elapsed <= target else "missed"
        result.append({
            "id": t.id,
            "ticket_number": t.ticket_number,
            "reporter": t.reporter_name,
            "school": t.school_institution,
            "product": t.product.value,
            "description": t.description[:100] + "..." if len(t.description) > 100 else t.description,
            "priority": t.priority.value,
            "status": t.status.value,
            "owner": t.owner,
            "age_hours": age,
            "target_hours": target,
            "sla_status": sla_status,
            "is_parked": t.status == StatusEnum.PARKED,
        })
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)