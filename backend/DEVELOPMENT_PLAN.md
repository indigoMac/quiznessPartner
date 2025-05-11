# Development Plan & Milestones (Backend)

This document is a copy of the root DEVELOPMENT_PLAN.md and is used to track backend progress. Check off items as you complete them!

---

## 1. Project Initialization

- [x] Set up project folder structure
- [x] Create README and .gitignore
- [x] Initialize backend (FastAPI) and frontend (Vite + React)
- [x] Add Docker and docker-compose setup

## 2. Backend Core

- [x] Set up environment variable management (.env, dotenv) (completed locally)
- [x] Implement database models (User, Quiz, Question, Result)
- [x] Set up database migrations (Alembic)
- [x] Implement API endpoints:
  - [x] `POST /upload-document` (accepts text or file)
  - [x] `POST /generate-quiz` (calls GPT, returns quiz)
  - [x] `POST /submit-answer` (records answers)
  - [x] `GET /quiz/:id` (fetches quiz data)
- [x] Integrate LangChain + OpenAI for quiz generation
- [x] Add PDF parsing (PyMuPDF)
- [x] Add unit tests (pytest, mock GPT calls)

## 3. Frontend Core

- [x] Set up Tailwind CSS
- [x] Set up React Query for API calls
- [ ] Create main pages:
  - [ ] Home / Upload page
  - [ ] Quiz page (interactive UI)
  - [ ] Results page
- [ ] Create reusable components:
  - [ ] File/Text upload
  - [ ] Quiz question display
  - [ ] Answer selection & feedback
- [ ] Connect frontend to backend APIs
- [ ] Add frontend tests (Vitest/Jest)

## 4. Database & Persistence

- [ ] Set up PostgreSQL with Docker
- [ ] Implement ORM models (SQLAlchemy)
- [ ] Store quizzes and results
- [ ] Add user model (for future auth)

## 5. Infrastructure & DevOps

- [ ] Add GitHub Actions for CI (run tests on push)
- [ ] Add pre-commit hooks (Black, flake8, isort)
- [ ] Add environment variable documentation
- [ ] Add production Docker optimizations

## 6. Documentation & Polish

- [ ] Update README with usage instructions
- [ ] Add API documentation (FastAPI docs)
- [ ] Add code comments and docstrings
- [ ] Add screenshots/gifs to README

## 7. Future Features (Post-MVP)

- [ ] User authentication & saved progress
- [ ] Support for more file types (Word, HTML, etc.)
- [ ] Difficulty selection
- [ ] Quiz formats beyond multiple-choice
- [ ] Audio/text-to-speech support
- [ ] Leaderboards/gamification

---

**How to use:**

- Check off items as you complete them (replace `[ ]` with `[x]`).
- Add new tasks or notes as needed.
- Use this as your single source of truth for project progress!
