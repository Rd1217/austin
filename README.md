# Four Square Sales Platform

Professional full-stack sales website with animated frontend, Python API, PostgreSQL storage, and Docker orchestration.

## Stack
- Frontend: React + Vite + custom CSS animations
- Backend: Python + FastAPI + PostgreSQL client
- Database: PostgreSQL 16
- Containers: Docker Compose

## Project Structure
- `frontend/` React website and UI assets
- `backend/` FastAPI backend and contact endpoint
- `db/init.sql` schema + seed data
- `docker-compose.yml` local orchestration

## Run with Docker
```bash
docker compose up --build
```

## App URLs
- Website: `http://localhost:3001`
- Backend API: `http://localhost:5001/api/health`
- PostgreSQL: `localhost:5433` (container `5432`)

## API Endpoints
- `GET /api/health`
- `POST /api/contact`
- `POST /api/admin/login`
- `GET /api/admin/contacts` (Bearer token required)
- `PATCH /api/admin/contacts/{id}` (Bearer token required)
- `GET /api/admin/backup` (Bearer token required, returns ZIP)

## Admin Credentials (Default)
- Username: `admin`
- Password: `Admin@12345`

Change these in [`docker-compose.yml`](/Users/rahulpratapdalvi/Desktop/austin/docker-compose.yml) before production:
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `JWT_SECRET_KEY`

## CRM Notes
- Contact submissions are always inserted as new rows (duplicates are allowed).
- CRM fields include status, called flag, call notes, follow-up date, and updated time.
- Contacts are indexed and paginated for scale (`limit`/`offset`).
- Backup export downloads all contacts as a ZIP file containing `contacts.csv`.
