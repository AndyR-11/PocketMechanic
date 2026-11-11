# PocketMechanic

PocketMechanic is a web app for keeping track of your vehicles. You can register your cars, log maintenance and service history, and record expenses, all in one place.

The project has two parts:

- **Backend:** a REST API built with FastAPI, SQLAlchemy and PostgreSQL.
- **Frontend:** a single-page app built with SvelteKit (Svelte 5) and TypeScript.

---

## Features

- **Accounts:** register, log in and log out, and edit your name and email. Passwords are hashed with Argon2. Sessions are stored server-side and sent as an HTTP-only cookie that lasts 7 days.
- **Vehicles:** add, edit and delete vehicles (make, model, year, mileage, VIN, license plate).
  - VINs are checked: 17 characters, letters and digits only, and no `I`, `O` or `Q`.
  - The model year can be at most one year past the current year.
  - Mileage can go up but never down.
- **Maintenance:** log service records for each vehicle (service type, date, mileage, cost, notes), and view the full history for a vehicle or across all of them.
- **Expenses:** record expenses for each vehicle (amount, category, date, notes) and filter them by vehicle.
- **Dashboard:** an overview of your garage and your most recent maintenance.
- **Data isolation:** every vehicle, maintenance and expense endpoint only returns records that belong to the logged-in user.

> **Planned:** the sidebar has a **Reminders** link, but that page has not been built yet.

---

## Tech Stack

| Layer    | Technology                                                     |
| -------- | -------------------------------------------------------------- |
| Frontend | SvelteKit 3, Svelte 5 (runes), TypeScript, Vite, Lucide icons  |
| Backend  | Python 3.12, FastAPI, Uvicorn, SQLAlchemy 2, Pydantic          |
| Auth     | Cookie-based sessions, `pwdlib` (Argon2) password hashing      |
| Database | PostgreSQL 15                                                  |
| Tooling  | Docker and Docker Compose                                      |

---

## Project Structure

```
PocketMechanic/
├── compose.yaml            # Postgres + backend services
├── .env.example            # Template for database credentials
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py         # FastAPI app, routers, CORS, health checks
│   │   ├── api/            # Route handlers (auth, vehicles, maintenance, expenses)
│   │   ├── services/       # Business logic and validation rules
│   │   ├── models/         # SQLAlchemy ORM models
│   │   ├── schemas/        # Pydantic request/response schemas
│   │   └── db/database.py  # Engine, session factory, get_db dependency
│   └── tests/
│       └── test_expenses.py
└── frontend/
    ├── package.json
    ├── vite.config.ts
    └── src/
        ├── lib/api.ts      # Fetch wrapper, shared types, formatters
        └── routes/         # Pages: dashboard, login, register, account,
                            #        vehicles, vehicles/[id], maintenance, expenses
```

---

## Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) with Docker Compose
- [Node.js](https://nodejs.org/) (a current LTS release) and npm

### 1. Configure environment variables

From the project root, copy the example file and set your own password:

Mac:
```bash
cp .env.example .env
```

Windows:
```bash
copy .env.example .env
```

```env
POSTGRES_USER=pocketmechanic
POSTGRES_PASSWORD=replace_with_local_password
POSTGRES_DB=pocketmechanic
```

`.env` is git-ignored, so it won't be committed.

### 2. Start the database and the backend

```bash
docker compose up --build
```

This starts:

- **PostgreSQL** on `localhost:5432`
- **FastAPI backend** on `http://localhost:8000`

The backend waits until the database passes its health check before starting. Tables are created automatically on startup. The database is stored in the `postgres_data` volume, so your data is kept between restarts.

Check that it's running:

- `http://localhost:8000/health` should return `{"status": "ok"}`
- `http://localhost:8000/db-health` should return `{"database": "connected"}`
- `http://localhost:8000/docs` opens the interactive Swagger UI

### 3. Start the frontend

In a second terminal:

```bash
cd frontend
```

```bash
npm install
```

```bash
npm run dev
```

Open **http://localhost:5173**, create an account, and log in.

> The backend's CORS settings only allow `http://localhost:5173`, and the frontend expects the API at `http://localhost:8000` (set in `src/lib/api.ts`). If you change either port, update both places.

---

## Running the Backend Without Docker (optional)

You still need a PostgreSQL instance running. Then:

```bash
cd backend
```

```bash
python -m venv .venv && source .venv/bin/activate
```

```bash
pip install -r requirements.txt
```

```bash
export DATABASE_URL="postgresql+psycopg2://pocketmechanic:<password>@localhost:5432/pocketmechanic"
```

```bash
uvicorn app.main:app --reload --port 8000
```

---

## Running Tests

The backend tests use Python's built-in `unittest` with an in-memory SQLite database, so you don't need Postgres or Docker to run them. From the `backend/` directory, with the requirements installed:

```bash
python -m unittest discover -s tests -v
```

The tests currently cover the expense service: creating, reading, updating and deleting expenses, checking that users can only see their own vehicles' expenses, and rejecting invalid input.

For type-checking the frontend:

```bash
cd frontend && npm run check
```

