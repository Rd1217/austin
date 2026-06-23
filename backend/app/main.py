import csv
import hashlib
import hmac
import io
import os
import re
import secrets
import time
import zipfile
from datetime import datetime, timedelta, timezone
from typing import Any

import psycopg
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from pydantic import BaseModel, Field


ROLE_KEYS = [
    "super_admin",
    "sales_head",
    "presales_executive",
    "closing_manager",
    "channel_partner_manager",
    "developer_support",
    "telecaller",
    "relationship_manager",
    "accounts_finance",
    "external_channel_partner",
    "developer_contact",
]

INTERNAL_ROLE_KEYS = {
    "super_admin",
    "sales_head",
    "presales_executive",
    "closing_manager",
    "channel_partner_manager",
    "developer_support",
    "telecaller",
    "relationship_manager",
    "accounts_finance",
}

LEAD_STATUSES = [
    "new_lead",
    "attempted",
    "contacted",
    "qualified",
    "visit_planned",
    "visit_done",
    "negotiation",
    "booking_in_progress",
    "booked",
    "lost",
    "nurture",
]

LEAD_TEMPERATURES = ["cold", "warm", "hot"]
ACTIVITY_TYPES = ["note", "call", "task", "meeting", "whatsapp", "email"]

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRES_MINUTES = int(os.getenv("JWT_EXPIRES_MINUTES", "180"))

LOGIN_BUCKET: dict[str, list[float]] = {}
MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", "8"))
LOGIN_WINDOW_SECONDS = int(os.getenv("LOGIN_WINDOW_SECONDS", "300"))
CONTACT_BUCKET: dict[str, list[float]] = {}
MAX_CONTACT_SUBMISSIONS = int(os.getenv("MAX_CONTACT_SUBMISSIONS", "20"))
CONTACT_WINDOW_SECONDS = int(os.getenv("CONTACT_WINDOW_SECONDS", "300"))


class PublicLeadRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=180)
    company: str = Field(min_length=2, max_length=180)
    message: str = Field(min_length=3, max_length=5000)


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=120)
    password: str = Field(min_length=8, max_length=120)


class LeadUpdateRequest(BaseModel):
    lead_status: str | None = Field(default=None, max_length=40)
    lead_temperature: str | None = Field(default=None, max_length=20)
    preferred_location: str | None = Field(default=None, max_length=180)
    budget: str | None = Field(default=None, max_length=180)
    property_type: str | None = Field(default=None, max_length=80)
    buying_purpose: str | None = Field(default=None, max_length=80)
    next_follow_up_at: datetime | None = None
    lost_reason: str | None = Field(default=None, max_length=400)
    assigned_to_user_id: int | None = None


class LeadActivityRequest(BaseModel):
    activity_type: str = Field(min_length=3, max_length=20)
    subject: str = Field(min_length=2, max_length=200)
    details: str = Field(min_length=2, max_length=4000)
    due_at: datetime | None = None
    outcome: str | None = Field(default=None, max_length=200)


def get_connection():
    return psycopg.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME", "foursquare"),
        user=os.getenv("DB_USER", "foursquare_user"),
        password=os.getenv("DB_PASSWORD", "foursquare_pass"),
    )


def create_access_token(username: str, role_key: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRES_MINUTES)
    payload = {"sub": username, "role": role_key, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)


def hash_password(plain_password: str) -> str:
    salt = secrets.token_hex(16)
    iterations = 260000
    digest = hashlib.pbkdf2_hmac("sha256", plain_password.encode(), salt.encode(), iterations)
    return f"pbkdf2_sha256${iterations}${salt}${digest.hex()}"


def verify_password(plain_password: str, stored_hash: str) -> bool:
    try:
        algo, iterations, salt, digest_hex = stored_hash.split("$", 3)
        if algo != "pbkdf2_sha256":
            return False
        calculated = hashlib.pbkdf2_hmac("sha256", plain_password.encode(), salt.encode(), int(iterations)).hex()
        return hmac.compare_digest(calculated, digest_hex)
    except Exception:
        return False


def ensure_email_format(email: str):
    if not EMAIL_RE.match(email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email format")


def get_bearer_token(request: Request) -> str:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    return auth_header.replace("Bearer ", "", 1).strip()


def check_login_rate_limit(ip: str):
    now = time.time()
    attempts = LOGIN_BUCKET.get(ip, [])
    attempts = [ts for ts in attempts if (now - ts) <= LOGIN_WINDOW_SECONDS]
    if len(attempts) >= MAX_LOGIN_ATTEMPTS:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many login attempts")
    attempts.append(now)
    LOGIN_BUCKET[ip] = attempts


def check_contact_rate_limit(ip: str):
    now = time.time()
    attempts = CONTACT_BUCKET.get(ip, [])
    attempts = [ts for ts in attempts if (now - ts) <= CONTACT_WINDOW_SECONDS]
    if len(attempts) >= MAX_CONTACT_SUBMISSIONS:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many submissions")
    attempts.append(now)
    CONTACT_BUCKET[ip] = attempts


def serialize_lead(row: tuple[Any, ...]) -> dict[str, Any]:
    return {
        "id": row[0],
        "lead_number": row[1],
        "source": row[2],
        "campaign": row[3],
        "name": row[4],
        "phone": row[5],
        "whatsapp_number": row[6],
        "email": row[7],
        "city": row[8],
        "preferred_location": row[9],
        "budget": row[10],
        "property_type": row[11],
        "buying_purpose": row[12],
        "lead_status": row[13],
        "lead_score": row[14],
        "assigned_to_user_id": row[15],
        "assigned_to_name": row[16],
        "interested_projects": row[17],
        "last_follow_up_at": row[18].isoformat() if row[18] else None,
        "next_follow_up_at": row[19].isoformat() if row[19] else None,
        "lost_reason": row[20],
        "lead_temperature": row[21],
        "message": row[22],
        "inquiry_context": row[23],
        "created_at": row[24].isoformat() if row[24] else None,
        "updated_at": row[25].isoformat() if row[25] else None,
        "activity_count": row[26],
    }


def serialize_activity(row: tuple[Any, ...]) -> dict[str, Any]:
    return {
        "id": row[0],
        "lead_id": row[1],
        "activity_type": row[2],
        "subject": row[3],
        "details": row[4],
        "due_at": row[5].isoformat() if row[5] else None,
        "outcome": row[6],
        "created_by_name": row[7],
        "created_at": row[8].isoformat() if row[8] else None,
    }


def get_current_user(request: Request) -> dict[str, Any]:
    token = get_bearer_token(request)

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT u.id, u.username, u.full_name, u.is_active, r.system_role_key, r.name
                FROM users u
                JOIN roles r ON r.id = u.role_id
                WHERE u.username = %s
                LIMIT 1
                """,
                (username,),
            )
            row = cur.fetchone()

    if not row or not row[3]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not active")

    return {
        "id": row[0],
        "username": row[1],
        "full_name": row[2],
        "is_active": row[3],
        "role_key": row[4],
        "role_name": row[5],
    }


def require_internal_user(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    if user["role_key"] not in INTERNAL_ROLE_KEYS:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Portal user cannot access internal CRM")
    return user


def record_activity(
    conn: psycopg.Connection,
    lead_id: int,
    activity_type: str,
    subject: str,
    details: str,
    actor_user_id: int | None = None,
    due_at: datetime | None = None,
    outcome: str | None = None,
):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO lead_activities (
                lead_id, actor_user_id, activity_type, subject, details, due_at, outcome
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (lead_id, actor_user_id, activity_type, subject, details, due_at, outcome),
        )
        cur.execute(
            """
            UPDATE leads
            SET last_follow_up_at = NOW(), updated_at = NOW()
            WHERE id = %s
            """,
            (lead_id,),
        )


def bootstrap_db():
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "Admin@12345")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS roles (
                    id SERIAL PRIMARY KEY,
                    system_role_key VARCHAR(80) UNIQUE NOT NULL,
                    name VARCHAR(120) NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW()
                );
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    role_id INTEGER NOT NULL REFERENCES roles(id),
                    username VARCHAR(120) UNIQUE NOT NULL,
                    full_name VARCHAR(180) NOT NULL,
                    email VARCHAR(180),
                    phone VARCHAR(30),
                    password_hash TEXT NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    last_login_at TIMESTAMP NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
                );
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS leads (
                    id SERIAL PRIMARY KEY,
                    lead_number VARCHAR(40) UNIQUE,
                    source VARCHAR(80) NOT NULL DEFAULT 'website',
                    campaign VARCHAR(120),
                    name VARCHAR(120) NOT NULL,
                    phone VARCHAR(30),
                    whatsapp_number VARCHAR(30),
                    email VARCHAR(180),
                    city VARCHAR(120) DEFAULT 'Pune',
                    preferred_location VARCHAR(180),
                    budget VARCHAR(180),
                    property_type VARCHAR(80),
                    buying_purpose VARCHAR(80),
                    lead_status VARCHAR(40) NOT NULL DEFAULT 'new_lead',
                    lead_score INTEGER NOT NULL DEFAULT 0,
                    assigned_to_user_id INTEGER NULL REFERENCES users(id),
                    interested_projects TEXT,
                    last_follow_up_at TIMESTAMP NULL,
                    next_follow_up_at TIMESTAMP NULL,
                    lost_reason VARCHAR(400),
                    lead_temperature VARCHAR(20) NOT NULL DEFAULT 'warm',
                    message TEXT NOT NULL,
                    inquiry_context TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
                );
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS lead_activities (
                    id SERIAL PRIMARY KEY,
                    lead_id INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
                    actor_user_id INTEGER NULL REFERENCES users(id),
                    activity_type VARCHAR(20) NOT NULL,
                    subject VARCHAR(200) NOT NULL,
                    details TEXT NOT NULL,
                    due_at TIMESTAMP NULL,
                    outcome VARCHAR(200),
                    created_at TIMESTAMP NOT NULL DEFAULT NOW()
                );
                """
            )

            cur.execute("ALTER TABLE leads ADD COLUMN IF NOT EXISTS lead_number VARCHAR(40);")
            cur.execute("ALTER TABLE leads ADD COLUMN IF NOT EXISTS source VARCHAR(80) NOT NULL DEFAULT 'website';")
            cur.execute("ALTER TABLE leads ADD COLUMN IF NOT EXISTS campaign VARCHAR(120);")
            cur.execute("ALTER TABLE leads ADD COLUMN IF NOT EXISTS phone VARCHAR(30);")
            cur.execute("ALTER TABLE leads ADD COLUMN IF NOT EXISTS whatsapp_number VARCHAR(30);")
            cur.execute("ALTER TABLE leads ADD COLUMN IF NOT EXISTS city VARCHAR(120) DEFAULT 'Pune';")
            cur.execute("ALTER TABLE leads ADD COLUMN IF NOT EXISTS preferred_location VARCHAR(180);")
            cur.execute("ALTER TABLE leads ADD COLUMN IF NOT EXISTS budget VARCHAR(180);")
            cur.execute("ALTER TABLE leads ADD COLUMN IF NOT EXISTS property_type VARCHAR(80);")
            cur.execute("ALTER TABLE leads ADD COLUMN IF NOT EXISTS buying_purpose VARCHAR(80);")
            cur.execute("ALTER TABLE leads ADD COLUMN IF NOT EXISTS lead_status VARCHAR(40) NOT NULL DEFAULT 'new_lead';")
            cur.execute("ALTER TABLE leads ADD COLUMN IF NOT EXISTS lead_score INTEGER NOT NULL DEFAULT 0;")
            cur.execute("ALTER TABLE leads ADD COLUMN IF NOT EXISTS assigned_to_user_id INTEGER NULL REFERENCES users(id);")
            cur.execute("ALTER TABLE leads ADD COLUMN IF NOT EXISTS interested_projects TEXT;")
            cur.execute("ALTER TABLE leads ADD COLUMN IF NOT EXISTS last_follow_up_at TIMESTAMP NULL;")
            cur.execute("ALTER TABLE leads ADD COLUMN IF NOT EXISTS next_follow_up_at TIMESTAMP NULL;")
            cur.execute("ALTER TABLE leads ADD COLUMN IF NOT EXISTS lost_reason VARCHAR(400);")
            cur.execute("ALTER TABLE leads ADD COLUMN IF NOT EXISTS lead_temperature VARCHAR(20) NOT NULL DEFAULT 'warm';")
            cur.execute("ALTER TABLE leads ADD COLUMN IF NOT EXISTS inquiry_context TEXT;")

            cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_roles_system_key ON roles(system_role_key);")
            cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username ON users(username);")
            cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_leads_lead_number ON leads(lead_number);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads(created_at DESC);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(lead_status);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_leads_location ON leads(preferred_location);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_activities_lead_id ON lead_activities(lead_id, created_at DESC);")

            for role_key in ROLE_KEYS:
                cur.execute(
                    """
                    INSERT INTO roles (system_role_key, name)
                    VALUES (%s, %s)
                    ON CONFLICT (system_role_key) DO NOTHING
                    """,
                    (role_key, role_key.replace("_", " ").title()),
                )

            cur.execute("SELECT id FROM roles WHERE system_role_key = 'super_admin' LIMIT 1")
            super_admin_role_id = cur.fetchone()[0]

            cur.execute("SELECT id FROM users WHERE username = %s LIMIT 1", (admin_username,))
            existing_user = cur.fetchone()
            if not existing_user:
                cur.execute(
                    """
                    INSERT INTO users (role_id, username, full_name, email, password_hash, is_active)
                    VALUES (%s, %s, %s, %s, %s, TRUE)
                    """,
                    (
                        super_admin_role_id,
                        admin_username,
                        "System Administrator",
                        "admin@foursquare.local",
                        hash_password(admin_password),
                    ),
                )

            cur.execute(
                """
                UPDATE leads
                SET lead_number = CONCAT('LEAD-', LPAD(id::text, 6, '0'))
                WHERE lead_number IS NULL
                """
            )

        conn.commit()


app = FastAPI(title="Four Square CRM Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("CORS_ORIGIN", "http://localhost:3001")],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.on_event("startup")
def on_startup():
    bootstrap_db()


@app.middleware("http")
async def secure_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Cache-Control"] = "no-store"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; img-src 'self' https: data:; style-src 'self' 'unsafe-inline' "
        "https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; script-src 'self'; "
        "connect-src 'self'"
    )
    return response


@app.get("/api/health")
def health():
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        return {
            "status": "ok",
            "service": "four-square-backend-python",
            "database": "connected",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database check failed: {exc}")


@app.post("/api/contact")
def create_public_lead(payload: PublicLeadRequest, request: Request):
    ensure_email_format(payload.email)
    check_contact_rate_limit(request.client.host if request.client else "unknown")

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO leads (
                        source, campaign, name, email, city, preferred_location, budget, property_type,
                        buying_purpose, lead_status, lead_temperature, message, inquiry_context, created_at, updated_at
                    )
                    VALUES (
                        'website', 'website_form', %s, %s, 'Pune', NULL, %s, NULL,
                        'self_use', 'new_lead', 'warm', %s, %s, NOW(), NOW()
                    )
                    RETURNING id, name, email, budget, lead_status, lead_temperature, created_at, updated_at
                    """,
                    (
                        payload.name.strip(),
                        payload.email.strip().lower(),
                        payload.company.strip(),
                        payload.message.strip(),
                        f"Website enquiry context: {payload.company.strip()}",
                    ),
                )
                row = cur.fetchone()
                lead_number = f"LEAD-{row[0]:06d}"
                cur.execute("UPDATE leads SET lead_number = %s WHERE id = %s", (lead_number, row[0]))
                record_activity(
                    conn,
                    lead_id=row[0],
                    actor_user_id=None,
                    activity_type="note",
                    subject="Lead captured from website",
                    details=payload.message.strip(),
                )
            conn.commit()

        return {
            "message": "Lead submitted successfully.",
            "lead": {
                "id": row[0],
                "lead_number": lead_number,
                "name": row[1],
                "email": row[2],
                "budget": row[3],
                "lead_status": row[4],
                "lead_temperature": row[5],
                "created_at": row[6].isoformat() if row[6] else None,
                "updated_at": row[7].isoformat() if row[7] else None,
            },
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not submit lead: {exc}")


@app.post("/api/admin/login")
def admin_login(payload: LoginRequest, request: Request):
    check_login_rate_limit(request.client.host if request.client else "unknown")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT u.id, u.username, u.full_name, u.password_hash, u.is_active, r.system_role_key, r.name
                FROM users u
                JOIN roles r ON r.id = u.role_id
                WHERE u.username = %s
                LIMIT 1
                """,
                (payload.username,),
            )
            row = cur.fetchone()

    if not row:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    user_id, username, full_name, password_hash, is_active, role_key, role_name = row
    if not is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is disabled")
    if role_key not in INTERNAL_ROLE_KEYS:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Portal users cannot access internal CRM")
    if not verify_password(payload.password, password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(username, role_key)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE users SET last_login_at = NOW(), updated_at = NOW() WHERE id = %s", (user_id,))
        conn.commit()

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in_minutes": JWT_EXPIRES_MINUTES,
        "admin": {
            "id": user_id,
            "username": username,
            "full_name": full_name,
            "role_key": role_key,
            "role_name": role_name,
        },
    }


@app.get("/api/admin/me")
def admin_me(user=Depends(require_internal_user)):
    return {"admin": user}


@app.get("/api/admin/users")
def list_internal_users(user=Depends(require_internal_user)):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT u.id, u.full_name, u.username, r.system_role_key, r.name
                FROM users u
                JOIN roles r ON r.id = u.role_id
                WHERE r.system_role_key <> 'external_channel_partner'
                  AND r.system_role_key <> 'developer_contact'
                ORDER BY u.full_name ASC
                """
            )
            rows = cur.fetchall()

    return {
        "users": [
            {
                "id": row[0],
                "full_name": row[1],
                "username": row[2],
                "role_key": row[3],
                "role_name": row[4],
            }
            for row in rows
        ]
    }


@app.get("/api/admin/leads")
def list_leads(
    limit: int = Query(default=20, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    lead_status: str | None = Query(default=None),
    q: str | None = Query(default=None, max_length=120),
    user=Depends(require_internal_user),
):
    where_clauses = []
    params: list[Any] = []

    if lead_status:
        where_clauses.append("l.lead_status = %s")
        params.append(lead_status)

    if q:
        where_clauses.append(
            "(LOWER(l.name) LIKE %s OR LOWER(COALESCE(l.email, '')) LIKE %s OR LOWER(COALESCE(l.preferred_location, '')) LIKE %s)"
        )
        needle = f"%{q.lower()}%"
        params.extend([needle, needle, needle])

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM leads l {where_sql}", tuple(params))
            total = cur.fetchone()[0]

            cur.execute(
                f"""
                SELECT
                    l.id,
                    l.lead_number,
                    l.source,
                    l.campaign,
                    l.name,
                    l.phone,
                    l.whatsapp_number,
                    l.email,
                    l.city,
                    l.preferred_location,
                    l.budget,
                    l.property_type,
                    l.buying_purpose,
                    l.lead_status,
                    l.lead_score,
                    l.assigned_to_user_id,
                    u.full_name,
                    l.interested_projects,
                    l.last_follow_up_at,
                    l.next_follow_up_at,
                    l.lost_reason,
                    l.lead_temperature,
                    l.message,
                    l.inquiry_context,
                    l.created_at,
                    l.updated_at,
                    COUNT(a.id) AS activity_count
                FROM leads l
                LEFT JOIN users u ON u.id = l.assigned_to_user_id
                LEFT JOIN lead_activities a ON a.lead_id = l.id
                {where_sql}
                GROUP BY l.id, u.full_name
                ORDER BY l.created_at DESC
                LIMIT %s OFFSET %s
                """,
                tuple([*params, limit, offset]),
            )
            rows = cur.fetchall()

    return {"total": total, "limit": limit, "offset": offset, "leads": [serialize_lead(row) for row in rows]}


@app.get("/api/admin/leads/{lead_id}/timeline")
def get_lead_timeline(lead_id: int, user=Depends(require_internal_user)):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    a.id,
                    a.lead_id,
                    a.activity_type,
                    a.subject,
                    a.details,
                    a.due_at,
                    a.outcome,
                    COALESCE(u.full_name, 'System'),
                    a.created_at
                FROM lead_activities a
                LEFT JOIN users u ON u.id = a.actor_user_id
                WHERE a.lead_id = %s
                ORDER BY a.created_at DESC
                """,
                (lead_id,),
            )
            rows = cur.fetchall()

    return {"timeline": [serialize_activity(row) for row in rows]}


@app.patch("/api/admin/leads/{lead_id}")
def update_lead(lead_id: int, payload: LeadUpdateRequest, user=Depends(require_internal_user)):
    updates = []
    params: list[Any] = []
    activity_messages = []

    if payload.lead_status is not None:
        normalized_status = payload.lead_status.strip().lower()
        if normalized_status not in LEAD_STATUSES:
            raise HTTPException(status_code=400, detail=f"lead_status must be one of: {', '.join(LEAD_STATUSES)}")
        updates.append("lead_status = %s")
        params.append(normalized_status)
        activity_messages.append(f"Lead status changed to {normalized_status}")

    if payload.lead_temperature is not None:
        normalized_temperature = payload.lead_temperature.strip().lower()
        if normalized_temperature not in LEAD_TEMPERATURES:
            raise HTTPException(status_code=400, detail="lead_temperature must be cold, warm, or hot")
        updates.append("lead_temperature = %s")
        params.append(normalized_temperature)
        activity_messages.append(f"Lead temperature set to {normalized_temperature}")

    for field_name in ("preferred_location", "budget", "property_type", "buying_purpose", "lost_reason"):
        value = getattr(payload, field_name)
        if value is not None:
            updates.append(f"{field_name} = %s")
            params.append(value.strip() if isinstance(value, str) else value)

    if payload.next_follow_up_at is not None:
        updates.append("next_follow_up_at = %s")
        params.append(payload.next_follow_up_at)
        activity_messages.append("Next follow-up updated")

    if payload.assigned_to_user_id is not None:
        updates.append("assigned_to_user_id = %s")
        params.append(payload.assigned_to_user_id)
        activity_messages.append("Lead reassigned")

    if not updates:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    updates.append("updated_at = NOW()")
    params.append(lead_id)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                UPDATE leads
                SET {', '.join(updates)}
                WHERE id = %s
                RETURNING
                    id,
                    lead_number,
                    source,
                    campaign,
                    name,
                    phone,
                    whatsapp_number,
                    email,
                    city,
                    preferred_location,
                    budget,
                    property_type,
                    buying_purpose,
                    lead_status,
                    lead_score,
                    assigned_to_user_id,
                    (SELECT full_name FROM users WHERE id = leads.assigned_to_user_id),
                    interested_projects,
                    last_follow_up_at,
                    next_follow_up_at,
                    lost_reason,
                    lead_temperature,
                    message,
                    inquiry_context,
                    created_at,
                    updated_at,
                    (SELECT COUNT(*) FROM lead_activities WHERE lead_id = leads.id)
                """,
                tuple(params),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Lead not found")

            if activity_messages:
                record_activity(
                    conn,
                    lead_id=lead_id,
                    actor_user_id=user["id"],
                    activity_type="note",
                    subject="Lead updated",
                    details="; ".join(activity_messages),
                )
            conn.commit()

    return {"message": "Lead updated", "lead": serialize_lead(row)}


@app.post("/api/admin/leads/{lead_id}/activities")
def add_lead_activity(lead_id: int, payload: LeadActivityRequest, user=Depends(require_internal_user)):
    activity_type = payload.activity_type.strip().lower()
    if activity_type not in ACTIVITY_TYPES:
        raise HTTPException(status_code=400, detail=f"activity_type must be one of: {', '.join(ACTIVITY_TYPES)}")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM leads WHERE id = %s LIMIT 1", (lead_id,))
            exists = cur.fetchone()
            if not exists:
                raise HTTPException(status_code=404, detail="Lead not found")

            record_activity(
                conn,
                lead_id=lead_id,
                actor_user_id=user["id"],
                activity_type=activity_type,
                subject=payload.subject.strip(),
                details=payload.details.strip(),
                due_at=payload.due_at,
                outcome=payload.outcome.strip() if payload.outcome else None,
            )

            cur.execute(
                """
                SELECT
                    a.id,
                    a.lead_id,
                    a.activity_type,
                    a.subject,
                    a.details,
                    a.due_at,
                    a.outcome,
                    COALESCE(u.full_name, 'System'),
                    a.created_at
                FROM lead_activities a
                LEFT JOIN users u ON u.id = a.actor_user_id
                WHERE a.lead_id = %s
                ORDER BY a.created_at DESC
                LIMIT 1
                """,
                (lead_id,),
            )
            row = cur.fetchone()
        conn.commit()

    return {"message": "Activity added", "activity": serialize_activity(row)}


@app.get("/api/admin/backup")
def backup_crm(user=Depends(require_internal_user)):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    lead_number,
                    source,
                    campaign,
                    name,
                    phone,
                    whatsapp_number,
                    email,
                    city,
                    preferred_location,
                    budget,
                    property_type,
                    buying_purpose,
                    lead_status,
                    lead_score,
                    lead_temperature,
                    message,
                    inquiry_context,
                    created_at,
                    updated_at
                FROM leads
                ORDER BY created_at DESC
                """
            )
            leads = cur.fetchall()

            cur.execute(
                """
                SELECT
                    a.id,
                    l.lead_number,
                    a.activity_type,
                    a.subject,
                    a.details,
                    a.due_at,
                    a.outcome,
                    COALESCE(u.full_name, 'System'),
                    a.created_at
                FROM lead_activities a
                JOIN leads l ON l.id = a.lead_id
                LEFT JOIN users u ON u.id = a.actor_user_id
                ORDER BY a.created_at DESC
                """
            )
            activities = cur.fetchall()

    lead_csv = io.StringIO()
    lead_writer = csv.writer(lead_csv)
    lead_writer.writerow(
        [
            "lead_number",
            "source",
            "campaign",
            "name",
            "phone",
            "whatsapp_number",
            "email",
            "city",
            "preferred_location",
            "budget",
            "property_type",
            "buying_purpose",
            "lead_status",
            "lead_score",
            "lead_temperature",
            "message",
            "inquiry_context",
            "created_at",
            "updated_at",
        ]
    )
    for row in leads:
        lead_writer.writerow(row)

    activity_csv = io.StringIO()
    activity_writer = csv.writer(activity_csv)
    activity_writer.writerow(
        ["activity_id", "lead_number", "activity_type", "subject", "details", "due_at", "outcome", "created_by", "created_at"]
    )
    for row in activities:
        activity_writer.writerow(row)

    zip_stream = io.BytesIO()
    with zipfile.ZipFile(zip_stream, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("leads.csv", lead_csv.getvalue())
        zf.writestr("lead_activities.csv", activity_csv.getvalue())
        zf.writestr(
            "meta.txt",
            f"exported_at_utc={datetime.now(timezone.utc).isoformat()}\nlead_records={len(leads)}\nactivity_records={len(activities)}\n",
        )

    zip_stream.seek(0)
    filename = f"crm-backup-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}.zip"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(content=zip_stream.getvalue(), media_type="application/zip", headers=headers)
