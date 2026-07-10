# Team Roles — Coursewright

Five people, five lanes. Swap in real names and adjust as ownership shifts — this is a starting split, not a contract.

## Hassan — Hosting, Infra & AI/App Security
- `infra/` (entire folder)
- `.github/workflows/` (CI/CD pipelines)
- `backend/Dockerfile`, root `docker-compose.yml`
- `backend/app/core/security.py`, `backend/app/core/config.py`
- Both `.env.example` files — defines what secrets exist, never real values
- Access control on `admin_review.py`, rate-limiting/abuse prevention on `chat.py`
- `docs/architecture.md`

## Backend Teammate (Python/FastAPI) — Core API & Data
- `backend/app/models/`, `backend/app/schemas/`, `backend/app/crud/`
- `backend/app/db/`, `backend/alembic/`
- Endpoints: users, fields, specializations, roadmaps, resources, tasks, quizzes, certificates
  (auth.py shared with Hassan)
- `backend/app/main.py`, `backend/app/api/v1/router.py`
- `backend/tests/`, `backend/requirements.txt`
- `docs/api-spec.md`

## AI/Data Teammate — AI Logic & Content Pipeline
- `backend/app/services/` — ai_service.py, roadmap_generator.py, resource_curator.py, review_service.py
- `chat.py` logic (paired with Hassan's security layer)
- `admin_review.py` logic (paired with Hassan's access control)
- `docs/content-review-guidelines.md`

## Generalist 1 — Frontend: Discovery Flow
- Pages: Onboarding, FieldExplorer, SpecializationDetail, Login, Signup, Profile
- `components/onboarding/`, `components/common/`, `components/layout/`
- `services/authService.js`, `services/specializationService.js`
- `docs/onboarding-flow.md`

## Generalist 2 — Frontend: Core Experience
- Pages: Home, Roadmap, TaskWorkspace
- `components/roadmap/`, `components/chatbot/`, `components/tasks/`
- `services/roadmapService.js`, `services/taskService.js`, `services/chatService.js`

## Shared / day-one setup
- `App.jsx`, `main.jsx`, `router.jsx`, `package.json`, `vite.config.js`, `tailwind.config.js`, `index.html`
- `hooks/`, `context/`, `utils/`, `styles/`
- Whoever starts frontend first scaffolds these; both frontend owners build on top of them.

## Suggested build order
1. Backend teammate sets up DB models + basic CRUD + auth skeleton — the foundation everything else hooks into.
2. Hassan gets local docker-compose running and AWS/IAM + secrets pattern decided, in parallel.
3. AI teammate can prototype ai_service.py independently against mock data — doesn't need to wait on the real DB.
4. Frontend pair can start against the Stitch-generated designs and mocked data, then wire up to real endpoints as they land.
