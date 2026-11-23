# Gladtidings Help Desk - Ticketing System

A FastAPI-based IT Help Desk ticketing system with SLA tracking, team management, and public review forms.

## 🚀 Quickest Team Setup: Deploy to Railway (Free, 2 minutes)

**No local installation needed for teammates.** Deploy once, everyone uses the URL.

### Deploy to Railway
1. Go to **https://railway.app** → Login with GitHub
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Select `gladtidings-softwere.co-ticketing-system` → **"Deploy Now"**
4. Wait ~2 minutes for build/deploy
5. Click service → **Settings** → **Domains** → Copy URL (e.g., `https://gladtidings-helpdesk.up.railway.app`)
6. Open URL → **Settings** page → Set **Public Base URL** to your Railway URL → Save
7. **Share the URL with your team** - works on any device (phone, laptop, tablet)

### Auto-Updates
Push to GitHub → Railway auto-redeploys:
```bash
git add . && git commit -m "changes" && git push
```

---

## 💻 Local Development Setup

```bash
# 1. Clone
git clone https://github.com/Nictitan/gladtidings-softwere.co-ticketing-system.git
cd gladtidings-softwere.co-ticketing-system

# 2. Virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\Activate.ps1

# 3. Install deps
pip install -r requirements.txt

# 4. Run
python main.py
```

**Access:** http://localhost:8000

---

## 🌐 Team Access Options

| Option | Best For | Setup Effort |
|--------|----------|--------------|
| **Railway (Recommended)** | Production team use | ⭐ Easiest - 2 min, free |
| **LAN Sharing** | Quick local testing | Low - run on one machine |
| **Render/Fly.io** | Alternative cloud | Low - similar to Railway |
| **Local per person** | Development only | Each runs own copy |

### Option 1: Railway (Recommended) ✅
- Free tier, auto-deploys from GitHub
- Permanent URL, HTTPS, custom domains
- **Teammates just click the link**

### Option 2: LAN Sharing (Quick Test)
1. Run `python main.py` on a machine that stays on
2. Find LAN IP: `ipconfig` (Win) / `ifconfig` (Mac/Linux)
3. Team accesses: `http://<LAN-IP>:8000`
4. **Settings → Public Base URL = `http://<LAN-IP>:8000`**

### Option 3: Render (Alternative)
1. https://render.com → New → Web Service
2. Connect GitHub repo → Auto-deploys
3. Same steps as Railway

### Option 4: Each Runs Locally (Dev Only)
- Each person runs Quick Start steps
- Separate databases (not shared)

---

## ⚙️ Settings Configuration

Go to **Settings** page in the app:

1. **Response Time Targets** - SLA hours per priority
2. **Team Members** - Add team, toggle active/inactive
3. **Public Base URL** - **Required for mobile access**
   - Railway: `https://your-app.up.railway.app`
   - LAN: `http://192.168.1.50:8000`
   - Custom domain: `https://helpdesk.company.com`
   - Without this, review links use `localhost` (broken on phones)

---

## 📱 Mobile Usage

**No app install needed** - it's a responsive web app:
1. Open the URL in Chrome/Safari
2. **Menu → "Add to Home Screen"** → Works like a native app
3. Already includes PWA manifest for offline-ready experience

---

## 🏗️ Project Structure

```
ticketing-system/
├── main.py              # FastAPI application
├── models.py            # SQLAlchemy models
├── schemas.py           # Pydantic schemas
├── database.py          # Database configuration
├── requirements.txt     # Python dependencies
├── railway.json         # Railway deployment config
├── Procfile             # Render/Heroku config
├── runtime.txt          # Python version
├── tickets.db           # SQLite database (auto-created)
├── templates/           # Jinja2 HTML templates
│   ├── base.html
│   ├── dashboard.html
│   ├── ticket_detail.html
│   ├── ticket_form.html
│   ├── settings.html
│   ├── public_form.html
│   └── partials/
└── static/              # Static assets
```

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| **Ticket Management** | Create, update, park, close, reset, delete tickets |
| **SLA Tracking** | Auto-calculates Met/Missed/Pending based on priority targets |
| **Priority Levels** | Critical (2hr), Technical (8hr), Ordinary (24hr) - configurable |
| **Team Management** | Add/remove members, assign ticket owners |
| **Public Review Form** | Shareable link for users to submit tickets |
| **Feedback Collection** | Send feedback requests on closed tickets |
| **Reports** | Weekly/monthly with SLA metrics |

---

## 🔧 Requirements

- Python 3.10+
- Dependencies: `fastapi`, `uvicorn`, `sqlalchemy`, `pydantic`, `jinja2`, `python-multipart`

---

## 🐛 Common Issues

| Issue | Solution |
|-------|----------|
| "Address already in use" | `pkill -f "python main.py"` |
| Review link broken on phone | Set **Public Base URL** in Settings |
| SLA not calculating | Ensure `first_reply_at` is set on first response |
| Database locked | Only run one server instance |
| Railway deploy fails | Check build logs, ensure `requirements.txt` is correct |

---

## 📄 License

Internal use - Gladtidings Software Ltd