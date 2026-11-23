# Gladtidings Help Desk - Ticketing System

A FastAPI-based IT Help Desk ticketing system with SLA tracking, team management, and public review forms.

## Quick Start

```bash
# 1. Navigate to project
cd "gts ithd/ticketing-system"

# 2. Create virtual environment
python -m venv venv

# 3. Activate environment
# macOS/Linux:
source venv/bin/activate
# Windows PowerShell:
venv\Scripts\Activate.ps1
# Windows CMD:
venv\Scripts\activate.bat

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run the server
python main.py
```

## Access the App

Open your browser to: **http://localhost:8000**

## For Team Access (Multiple Users)

### Option 1: Run on One Machine, Share via LAN
1. Run the server on a machine that stays on (your machine, a spare laptop, etc.)
2. Find that machine's LAN IP: `ipconfig` (Windows) or `ifconfig` / `ip a` (macOS/Linux)
3. Teammates access: `http://<LAN-IP>:8000` (e.g., `http://192.168.1.50:8000`)
4. **Important**: Go to **Settings** → Set **Public Base URL** to `http://<LAN-IP>:8000`
   - This makes the "Review Form" link work on teammates' phones

### Option 2: Deploy to a VPS/Cloud (Recommended for Production)
Deploy to Railway, Render, Fly.io, DigitalOcean, etc.:
- Set up a process manager (systemd/supervisor) or use Docker
- Use nginx as reverse proxy with SSL
- Set **Public Base URL** to your domain (e.g., `https://helpdesk.yourcompany.com`)

### Option 3: Each Person Runs Locally
Each teammate runs the steps in "Quick Start" on their own machine.
- They'll have their own local database (tickets.db)
- Good for testing, not for shared ticket data

## Key Features

| Feature | Description |
|---------|-------------|
| **Ticket Management** | Create, update, park, close, reset, delete tickets |
| **SLA Tracking** | Auto-calculates SLA status (Met/Missed/Pending) based on priority targets |
| **Priority Levels** | Critical (2hr), Technical (8hr), Ordinary (24hr) - configurable |
| **Team Management** | Add/remove team members, assign ticket owners |
| **Public Review Form** | Shareable link for users to submit tickets |
| **Feedback Collection** | Send feedback requests on closed tickets |
| **Reports** | Weekly and monthly reports with SLA metrics |

## Settings Configuration

Go to **Settings** page to configure:

1. **Response Time Targets** - SLA hours for each priority
2. **Team Members** - Add your team, toggle active/inactive
3. **Public Base URL** - **Critical for mobile access**
   - Set to your public URL (e.g., `http://192.168.1.50:8000` or `https://helpdesk.company.com`)
   - The review form link will use this base URL
   - Without this, the link uses `localhost` which only works on the server machine

## Project Structure

```
ticketing-system/
├── main.py              # FastAPI application
├── models.py            # SQLAlchemy models
├── schemas.py           # Pydantic schemas
├── database.py          # Database configuration
├── requirements.txt     # Python dependencies
├── tickets.db           # SQLite database (created on first run)
├── templates/           # Jinja2 HTML templates
│   ├── base.html
│   ├── dashboard.html
│   ├── ticket_detail.html
│   ├── ticket_form.html
│   ├── settings.html
│   ├── public_form.html
│   └── partials/
└── static/              # Static assets (if any)
```

## Requirements

- Python 3.10+
- Dependencies in `requirements.txt`:
  - fastapi
  - uvicorn
  - sqlalchemy
  - pydantic
  - jinja2
  - python-multipart

## Common Issues

| Issue | Solution |
|-------|----------|
| "Address already in use" | Kill existing process: `pkill -f "python main.py"` |
| Review link doesn't work on phone | Set **Public Base URL** in Settings |
| SLA not calculating | Ensure tickets have `first_reply_at` set when first responding |
| Database locked | Only run one instance of the server at a time |

## License

Internal use - Gladtidings Software Ltd