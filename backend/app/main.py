# ─── main.py ──────────────────────────────────────────────────────────────────
# FastAPI application entry point.
# Registers all routes, configures CORS, and runs startup logic.
# ──────────────────────────────────────────────────────────────────────────────

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.db.database import engine, Base, SessionLocal
from app.models import Admin, Election
from app.core.security import get_password_hash
from app.core.config import settings

# Import all route modules
from app.api import auth, admin, elections, votes, stats

# ─── Create all DB tables ─────────────────────────────────────────────────────
# SQLAlchemy reads all classes that inherit from Base and creates their tables.
# This is idempotent — running it twice doesn't drop or duplicate anything.
Base.metadata.create_all(bind=engine)

# ─── FastAPI App ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="CampusTally API",
    description="Backend for the CampusTally university e-voting platform.",
    version="1.0.0"
)

# ─── CORS ─────────────────────────────────────────────────────────────────────
# CORS (Cross-Origin Resource Sharing) controls which origins can call this API.
# In development, we allow all origins. In production, restrict to your domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],         # Replace with your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Register Routers ────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(elections.router)
app.include_router(votes.router)
app.include_router(stats.router)


# ─── Startup: Seed the database ───────────────────────────────────────────────
@app.on_event("startup")
def seed_database():
    """
    Runs once when the server starts.
    Creates the root admin account if it doesn't exist.
    Seeds default elections if the elections table is empty.
    """
    db: Session = SessionLocal()
    try:
        _seed_admin(db)
        _seed_elections(db)
    finally:
        db.close()


def _seed_admin(db: Session):
    """Create the root admin from .env credentials if it doesn't exist."""
    existing = db.query(Admin.Admin).filter(Admin.Admin.fullname == settings.ADMIN_USERNAME).first()
    if not existing:
        root = Admin.Admin(
            fullname    = settings.ADMIN_USERNAME,
            hashed_password = get_password_hash(settings.ADMIN_PASSWORD),
            is_root       = True
        )
        db.add(root)
        db.commit()
        print(f"[seed] Root admin '{settings.ADMIN_USERNAME}' created.")


def _seed_elections(db: Session):
    """Seed default elections (same data as the frontend's defaultElections())."""
    if db.query(Election.Election).count() > 0:
        return  # Already seeded — don't overwrite

    import time, json
    from app.models.Election import Election as ElModel

    elections_data = _default_elections()
    for data in elections_data:
        el = ElModel(
            id         = data["id"],
            title      = data["title"],
            short_name = data.get("shortName", data["title"]),
            category   = data["category"],
            status     = data["status"],
            start_date = data.get("startDate"),
            start_time = data.get("startTime"),
            end_date   = data.get("endDate"),
            end_time   = data.get("endTime"),
        )
        el.positions  = data.get("positions", [])
        el.seed_votes = data.get("seedVotes", [])
        db.add(el)
    db.commit()
    print(f"[seed] {len(elections_data)} default elections seeded.")


# ─── Health Check ─────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "ok", "app": "CampusTally API", "version": "1.0.0"}


# ─── Default election data (mirrors app.js defaultElections()) ────────────────
def _default_elections():
    return [
        {
            "id": "src_2024", "title": "SRC General Election 2024",
            "shortName": "SRC Elections", "category": "SRC Election", "status": "active",
            "startDate": "2024-10-20", "startTime": "08:00",
            "endDate":   "2024-10-26", "endTime":   "18:00",
            "seedVotes": [
                [2340, 1820, 1040], [2640, 1494, 847],
                [3193, 1957, 0],    [2200, 1800, 1200], [1900, 1500, 900]
            ],
            "positions": [
                { "title": "SRC President", "candidates": [
                    { "name": "Guru",     "emoji": "👤", "info": { "role": "SRC Presidential Candidate",      "score": "87/100", "manifesto": "A New Dawn for Students",    "body": "I pledge to improve student welfare, reduce bureaucracy, and create a more transparent SRC.", "policies": ["Free printing stations in all labs", "24/7 student counselling centre"] } },
                    { "name": "Akrobeto", "emoji": "👤", "info": { "role": "SRC Presidential Candidate",      "score": "82/100", "manifesto": "Students First Always",        "body": "Together we can build a stronger student body.", "policies": ["Discounted transport scheme", "Industry attachment facilitation"] } },
                    { "name": "Lilwin",   "emoji": "👤", "info": { "role": "SRC Presidential Candidate",      "score": "75/100", "manifesto": "Rising Together",             "body": "A grassroots approach to student leadership.", "policies": ["Monthly SRC open forums", "Departmental grant fund"] } }
                ]},
                { "title": "SRC Vice President", "candidates": [
                    { "name": "Asamoah Gyan", "emoji": "👤", "info": { "role": "SRC Vice Presidential Candidate", "score": "88/100", "manifesto": "Supporting Every Student", "body": "Bridging the gap between students and administration.", "policies": ["Student ID card discounts", "Extended library hours"] } },
                    { "name": "Kwame Messi",  "emoji": "👤", "info": { "role": "SRC Vice Presidential Candidate", "score": "79/100", "manifesto": "Empowering the Youth",    "body": "A youth-first agenda prioritising innovation.", "policies": ["Startup incubator", "Mentorship programs"] } },
                    { "name": "Yaw Ronaldo",  "emoji": "👤", "info": { "role": "SRC Vice Presidential Candidate", "score": "71/100", "manifesto": "Fairness for All",         "body": "Equal opportunities for every student.", "policies": ["Scholarship awareness drive", "Welfare fund expansion"] } }
                ]},
                { "title": "SRC General Secretary", "candidates": [
                    { "name": "Russell Kusi", "emoji": "👤", "info": { "role": "SRC General Secretary Candidate", "score": "90/100", "manifesto": "Transparency & Accountability", "body": "Complete overhaul of SRC record-keeping.", "policies": ["Monthly financial reports", "Open SRC minutes"] } },
                    { "name": "Haleem Abdul", "emoji": "👤", "info": { "role": "SRC General Secretary Candidate", "score": "84/100", "manifesto": "Organized & Efficient",         "body": "Streamlining SRC operations.", "policies": ["Digital SRC portal", "Online petition system"] } },
                    { "name": "Gibson Ofori", "emoji": "👤", "info": { "role": "SRC General Secretary Candidate", "score": "77/100", "manifesto": "Service Before Self",           "body": "Committed to serving with transparency.", "policies": ["Student grievance hotline", "Suggestion boxes"] } }
                ]},
                { "title": "SRC Financial Secretary", "candidates": [
                    { "name": "Ken Ofori Atta", "emoji": "👤", "info": { "role": "SRC Financial Secretary Candidate", "score": "92/100", "manifesto": "Fiscal Responsibility", "body": "Prudent management of SRC funds.", "policies": ["Quarterly budget audits", "Student welfare fund"] } },
                    { "name": "Ato Forson",     "emoji": "👤", "info": { "role": "SRC Financial Secretary Candidate", "score": "86/100", "manifesto": "Every Pesewa Counts",  "body": "Zero wastage policy.", "policies": ["Digital receipts", "Bursary fund expansion"] } },
                    { "name": "Wayomi",         "emoji": "👤", "info": { "role": "SRC Financial Secretary Candidate", "score": "73/100", "manifesto": "Invest in Students",    "body": "Redirecting SRC funds to students.", "policies": ["Free printing credits", "Emergency student fund"] } }
                ]},
                { "title": "SRC Women's Commissioner", "candidates": [
                    { "name": "Abena Korkor", "emoji": "👤", "info": { "role": "Women's Commissioner Candidate", "score": "89/100", "manifesto": "Women Rising",      "body": "Championing gender equality on campus.", "policies": ["Safe walk program", "Women mentorship series"] } },
                    { "name": "Nana Ama",     "emoji": "👤", "info": { "role": "Women's Commissioner Candidate", "score": "83/100", "manifesto": "Her Voice Matters", "body": "Amplifying women voices in governance.", "policies": ["Monthly women town halls", "Sanitary product subsidies"] } },
                    { "name": "Efua Bright",  "emoji": "👤", "info": { "role": "Women's Commissioner Candidate", "score": "76/100", "manifesto": "Together We Shine", "body": "Building an empowered community.", "policies": ["Women safety app", "Female leadership training"] } }
                ]}
            ]
        },
        {
            "id": "nugs_2024", "title": "Local NUGS Elections 2024",
            "shortName": "Local NUGS", "category": "NUGS Election", "status": "active",
            "startDate": "2024-10-20", "startTime": "08:00",
            "endDate":   "2024-10-26", "endTime":   "18:00",
            "seedVotes": [
                [2640, 2160, 800], [2200, 1700, 1100],
                [3000, 1800, 600], [2500, 1500, 1200], [1900, 1600, 1000]
            ],
            "positions": [
                { "title": "LNUGS President", "candidates": [
                    { "name": "Mama Pat", "emoji": "👤", "info": { "role": "LNUGS Presidential Candidate", "score": "91/100", "manifesto": "For All Students", "body": "Building bridges through grassroots engagement.", "policies": ["NUGS welfare fund", "Industry engagement nights"] } },
                    { "name": "Delay",    "emoji": "👤", "info": { "role": "LNUGS Presidential Candidate", "score": "85/100", "manifesto": "Progress & Unity", "body": "A progressive agenda built on unity.", "policies": ["National student network", "Joint campus events"] } },
                    { "name": "Tupac",    "emoji": "👤", "info": { "role": "LNUGS Presidential Candidate", "score": "72/100", "manifesto": "Student Power",    "body": "Uniting students under one powerful voice.", "policies": ["Student solidarity fund", "Advocacy campaigns"] } }
                ]},
                { "title": "LNUGS Vice President", "candidates": [
                    { "name": "Akabenezer",  "emoji": "👤", "info": { "role": "LNUGS Vice Presidential Candidate", "score": "87/100", "manifesto": "Action & Results", "body": "Focused on tangible results.", "policies": ["Internship database", "Study resources portal"] } },
                    { "name": "Kwame Alidu", "emoji": "👤", "info": { "role": "LNUGS Vice Presidential Candidate", "score": "80/100", "manifesto": "Students United",   "body": "Unifying diverse student groups.", "policies": ["Cross-campus dialogues", "Cultural exchange program"] } },
                    { "name": "Yaw Mensah",  "emoji": "👤", "info": { "role": "LNUGS Vice Presidential Candidate", "score": "74/100", "manifesto": "Bold Leadership",   "body": "Leading with courage and empathy.", "policies": ["Leadership bootcamp", "Youth entrepreneurship fund"] } }
                ]},
                { "title": "LNUGS General Secretary", "candidates": [
                    { "name": "Russell Kusi", "emoji": "👤", "info": { "role": "LNUGS General Secretary Candidate", "score": "90/100", "manifesto": "Efficient & Open",       "body": "Modern management practices for NUGS.", "policies": ["Digital communication", "Weekly updates"] } },
                    { "name": "Haleem Abdul", "emoji": "👤", "info": { "role": "LNUGS General Secretary Candidate", "score": "83/100", "manifesto": "Serving with Excellence", "body": "Administrative excellence for all.", "policies": ["Member newsletter", "Open forum meetings"] } },
                    { "name": "Gibson Ofori", "emoji": "👤", "info": { "role": "LNUGS General Secretary Candidate", "score": "77/100", "manifesto": "Accountability First",   "body": "Transparent NUGS secretariat.", "policies": ["Published meeting minutes", "Annual NUGS report"] } }
                ]},
                { "title": "LNUGS Financial Secretary", "candidates": [
                    { "name": "Ken Ofori Atta", "emoji": "👤", "info": { "role": "LNUGS Financial Secretary Candidate", "score": "93/100", "manifesto": "Responsible Finance", "body": "Strategic management of NUGS finances.", "policies": ["Financial transparency dashboard", "Emergency grants"] } },
                    { "name": "Ato Forson",     "emoji": "👤", "info": { "role": "LNUGS Financial Secretary Candidate", "score": "87/100", "manifesto": "Smart Spending",      "body": "Maximising impact of every contribution.", "policies": ["Cost-benefit reviews", "Student discount partnerships"] } },
                    { "name": "Wayomi",         "emoji": "👤", "info": { "role": "LNUGS Financial Secretary Candidate", "score": "74/100", "manifesto": "Invest Wisely",        "body": "Long-term financial reserves for students.", "policies": ["Savings scheme", "Annual bursary awards"] } }
                ]},
                { "title": "LNUGS Women's Commissioner", "candidates": [
                    { "name": "Adwoa Sarfo",    "emoji": "👤", "info": { "role": "Women's Commissioner Candidate", "score": "88/100", "manifesto": "Women Empowered", "body": "Safe and empowering spaces for women.", "policies": ["Safe campus initiative", "Women leadership summits"] } },
                    { "name": "Gifty Anti",     "emoji": "👤", "info": { "role": "Women's Commissioner Candidate", "score": "82/100", "manifesto": "Her Future Now",  "body": "Investing in women's futures.", "policies": ["Skills training", "Scholarship drive"] } },
                    { "name": "Serwaa Amihere", "emoji": "👤", "info": { "role": "Women's Commissioner Candidate", "score": "76/100", "manifesto": "Voices Heard",    "body": "Every woman's voice at decision tables.", "policies": ["Women advisory council", "Gender policy review"] } }
                ]}
            ]
        },
        {
            "id": "eng_2024", "title": "School of Engineering Elections",
            "shortName": "School of Engineering", "category": "Faculty / School", "status": "upcoming",
            "startDate": "2024-10-28", "startTime": "08:00",
            "endDate":   "2024-10-29", "endTime":   "18:00",
            "seedVotes": [],
            "positions": [
                { "title": "Engineering President", "candidates": [
                    { "name": "Kwesi Mensah", "emoji": "👤", "info": { "role": "Engineering Presidential Candidate", "score": "91/100", "manifesto": "Engineering the Future", "body": "A strong voice for all engineering students.", "policies": ["Lab access extension", "Industry visits"] } },
                    { "name": "Abena Asante", "emoji": "👤", "info": { "role": "Engineering Presidential Candidate", "score": "85/100", "manifesto": "Innovation First",        "body": "Driving innovation within the faculty.", "policies": ["Hackathon series", "Equipment grants"] } }
                ]}
            ]
        },
        {
            "id": "dept_2023", "title": "Departmental / Assocs Elections 2023",
            "shortName": "Departmental / Assocs", "category": "Departmental", "status": "closed",
            "startDate": "2023-10-15", "startTime": "08:00",
            "endDate":   "2023-10-16", "endTime":   "18:00",
            "seedVotes": [[1400, 1100]],
            "positions": [
                { "title": "CS Dept. President", "candidates": [
                    { "name": "Emmanuel Tetteh", "emoji": "👤", "info": { "role": "CS Dept. Presidential Candidate", "score": "94/100", "manifesto": "Code the Change",  "body": "Empowering CS students with better resources.", "policies": ["Free cloud credits", "Internship network"] } },
                    { "name": "Grace Addo",      "emoji": "👤", "info": { "role": "CS Dept. Presidential Candidate", "score": "88/100", "manifesto": "Inclusive Tech",    "body": "Building an inclusive CS student community.", "policies": ["Study groups fund", "Open source drive"] } }
                ]}
            ]
        }
    ]