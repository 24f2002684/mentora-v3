# Mentora — VRCF Student Development & Socratic Mentoring Platform

**Mentora** is a full-stack, production-ready web application built for the **Vasumathi Ramaswami Centenary Foundation (VRCF)**. It empowers college scholars supported by the foundation to cultivate academic excellence, analytical reasoning, leadership, and long-term career aspirations through personalized learning pathways, mentor-reviewed assignments, reflective milestones, and an AI-powered Socratic coaching engine.

The platform is seeded and fully synced with the **43 real VRCF college scholars** from the foundation's official student database (`prereq_data/VRCF Student DB.xlsx`).

---

## 1. Core Architecture & System Features

### A. Role-Based Portals (Strict Server-Side Validation)
Mentora enforces granular authorization across three primary foundation roles plus administration:
- **Scholar (`STUDENT`)**: Private profile management, personal vision & aim statement, milestone roadmap, mentor assignments & self-tasks, Socratic AI mentor, competency analytics radar, and curated resource library. Strict data isolation prevents students from viewing or altering other scholars' submissions or evaluations.
- **Mentor (`MENTOR`)**: Roster directory of assigned scholars, multi-scholar task assignment with rubrics, submission evaluation queue with 1–5 scoring and written feedback, competency scoring (10 domains), support alerts (open/acknowledged/resolved), and one-click downloadable ReportLab PDF Growth Reports.
- **Trustee (`TRUSTEE`)**: Executive governance dashboard, total scholar roster view, interactive Chart.js analytics across cohorts and competencies, mentorship program oversight, and direct guidance/encouragement messaging with real-time in-app scholar notifications.
- **Administrator (`ADMIN`)**: Real-time scholar provisioning with duplicate VRCF ID and email detection, and workbook import audit reporting.

### B. Visual Identity & Design System
- **Brand Aesthetic**: Refined teal primary accent (`#0d9488`), dark slate and charcoal tones, generous whitespace, accessible contrast, and zero neon/decorative clutter.
- **Themes**: System-wide Light and Dark themes, with theme persistence in local storage and cookies to prevent theme flashing on page load.
- **Official Asset Integration**: The official 225x225 Mentora logo (`prereq_data/Mentora_Logo.png`) is integrated across the login screen, sidebar, topbar, and PWA manifest.
- **Progressive Web App (PWA)**: Manifest and service worker caching for offline resilience and mobile home-screen installability.

### C. Data Integrity — The 43 Real Scholars
- **Zero Mock Data**: No fake records, fabricated grades, or hardcoded stats. Every dashboard metric queries live PostgreSQL tables.
- **Excel Import Management Command**:
  ```bash
  python manage.py import_students prereq_data/VRCF\ Student\ DB.xlsx --dry-run
  python manage.py import_students prereq_data/VRCF\ Student\ DB.xlsx
  ```
- **Atomicity & Audit**: 43 real scholars parsed and mapped to `StudentProfile` with zero conflicts or duplicate VRCF IDs.

### D. AI Socratic Mentor (Google Gemini API)
- **Philosophy**: Acts as an intellectually rigorous learning coach using the Socratic method—guiding students with hints, conceptual breakdowns, and reflective questions rather than generating answers.
- **Model**: Powered by `gemini-3.8-flash` via the official `google-genai` Python SDK.
- **Resilience & Fallback**: Handles quota limits or connection disruptions gracefully with built-in Socratic heuristics, ensuring the application remains functional even offline.
- **Formative Separation**: AI evaluations are strictly marked as provisional formative observations and never overwrite official mentor grades.

### E. Professional PDF Growth Reports (ReportLab)
- Mentors can generate and download comprehensive PDF progress reports on demand.
- True PDF binary generation using ReportLab (never browser print dialogs).
- Includes VRCF branding, scholar vitals, goal progress, mentor review history, and competency progression table.

---

## 2. Pre-Configured Accounts & Credentials

| Role | Username / Email | Initial Password | Redirect Path |
|---|---|---|---|
| **Administrator** | `admin@gmail.com` | `admin@123` | `/trustee/dashboard/` |
| **Foundation Trustee** | `trustee@gmail.com` | `trustee@123` | `/trustee/dashboard/` |
| **VRCF Lead Mentor** | `mentor@gmail.com` | `mentor@123` | `/mentor/dashboard/` |
| **Scholar (Example)** | `suhailmobina95@gmail.com` (Suhail Akthar S M, VRCF-032) | `vrcf32` | `/student/dashboard/` |
| **All Other Scholars** | Scholar's registered email from workbook | `vrcf<VRCF_ID_numeric>` (e.g. `vrcf3` for VRCF-003, `vrcf45` for VRCF-045) | `/student/dashboard/` |

*Scholars can update their password anytime in their **Settings** panel.*

---

## 3. Technology Stack

- **Backend**: Python 3.11+, Django 5.1+, Django ORM, WhiteNoise.
- **Database**: PostgreSQL 16 (Authoritative database with relational constraints and indexes).
- **Frontend**: HTML5, Vanilla CSS3 (Custom Mentora Design System), Bootstrap 5.3, Bootstrap Icons, Chart.js.
- **PDF Generation**: ReportLab 4.2+.
- **AI Integration**: Google GenAI SDK (`google-genai`).
- **Data Ingestion**: `openpyxl`.

---

## 4. Local Development Setup

### Prerequisites
- Python 3.11 or 3.12
- PostgreSQL 15 or 16 installed locally

### Step-by-Step Instructions

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/24f2002684/mentora-v3.git
   cd mentora-v3
   ```

2. **Create and Activate Virtual Environment**:
   ```bash
   python -m venv .venv
   # Windows:
   .\.venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**:
   Create a `.env` file from `.env.example`:
   ```bash
   cp .env.example .env
   ```
   Configure your PostgreSQL connection and Gemini API Key:
   ```env
   SECRET_KEY=your-secure-django-secret-key
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:5432/mentora_db
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_MODEL=gemini-3.8-flash
   ```

5. **Apply Database Migrations**:
   ```bash
   python manage.py migrate
   ```

6. **Import the Real 43 VRCF Scholars**:
   ```bash
   python manage.py import_students "prereq_data/VRCF Student DB.xlsx"
   ```

7. **Collect Static Assets**:
   ```bash
   python manage.py collectstatic --noinput
   ```

8. **Run the Development Server**:
   ```bash
   python manage.py runserver 127.0.0.1:8000
   ```
   Open your browser at `http://127.0.0.1:8000/`.

---

## 5. Automated Test Suite

Mentora includes 22 automated integration tests covering authentication, role-based redirects, student data isolation, mentor task workflows, ReportLab PDF generation, trustee governance, and Socratic AI fallback handling.

To run the automated test suite:
```bash
python manage.py test --noinput
```

**Test Verification Summary**:
```text
----------------------------------------------------------------------
Ran 22 tests in 67.718s

OK
System check identified no issues (0 silenced).
```

---

## 6. Production Deployment Guidance

### Recommended: Conventional Production Host (VPS / Cloud Run / AWS EC2 / Render)
A conventional Python WSGI server with Gunicorn, WhiteNoise, and managed PostgreSQL is recommended:
```bash
gunicorn mentora.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

**Production Checklist**:
1. Set `DEBUG=False` in `.env`.
2. Generate a cryptographically strong `SECRET_KEY`.
3. Set `SESSION_COOKIE_SECURE=True` and `CSRF_COOKIE_SECURE=True` for HTTPS.
4. Set `ALLOWED_HOSTS` to your production domain (e.g. `mentora.vrcf.org`).
5. Configure persistent object storage (e.g., AWS S3 or GCP Cloud Storage) for uploaded scholar photos and submission attachments.

### Vercel Deployment Considerations
If deploying to Vercel via `@vercel/python`:
- Requires an external managed PostgreSQL database (e.g., Neon or AWS RDS).
- Media files must use remote S3/GCS storage since serverless functions have ephemeral local filesystems.
- Migrations and student import must be executed during CI/CD build steps or from an administrative CLI, not during HTTP request handling.

---

## 7. Database Backup & Restore

### Backup
```bash
pg_dump -U postgres -h 127.0.0.1 -p 5433 -F c -b -v -f mentora_db_backup.dump mentora_db
```

### Restore
```bash
pg_restore -U postgres -h 127.0.0.1 -p 5433 -d mentora_db -v mentora_db_backup.dump
```

---

## 8. License & Attribution

Developed for the **Vasumathi Ramaswami Centenary Foundation (VRCF)**. All rights reserved.
