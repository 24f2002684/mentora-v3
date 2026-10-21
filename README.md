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

Mentora includes 23 automated integration and workflow tests covering authentication, role-based redirects, student data isolation, multi-mentor task assignments, ReportLab PDF generation, trustee governance, and Socratic AI fallback handling.

### Running Tests Locally (Windows PowerShell / macOS / Linux)

```powershell
# Windows PowerShell:
.\.venv\Scripts\python.exe manage.py test --noinput

# Linux / macOS:
python manage.py test --noinput
```

**Verification Summary**:
```text
----------------------------------------------------------------------
Ran 23 tests in 47.821s

OK
Destroying test database for alias 'default'...
Found 23 test(s).
System check identified no issues (0 silenced).
```

---

## 6. Render Cloud Deployment Guide

This application is fully prepared for zero-downtime deployment on [Render](https://render.com/) with a managed PostgreSQL database, WhiteNoise static file caching, and Gunicorn WSGI.

### A. Deployment Architecture

| Component | Service Type on Render | Specification |
|---|---|---|
| **Web Service** | Web Service (Python 3) | `gunicorn mentora.wsgi:application` |
| **Build Script** | Shell script (`build.sh`) | Installs deps, collects static files, applies migrations |
| **Database** | PostgreSQL | Render Managed PostgreSQL (PostgreSQL 16) |
| **Static Files** | WhiteNoise | Compressed Manifest Storage with cache busting |
| **Uploads / Media** | Persistent Disk or Local | `MEDIA_ROOT` served via `re_path` |

### B. Build & Start Commands

- **Build Command**:
  ```bash
  ./build.sh
  ```
- **Start Command**:
  ```bash
  gunicorn mentora.wsgi:application
  ```

### C. Required Render Environment Variables

Configure these in the Render Dashboard under **Environment Variables**:

| Variable Name | Required | Example / Recommended Value | Description |
|---|---|---|---|
| `DATABASE_URL` | **Yes** | `postgres://user:pass@dpg-xxx.oregon-postgres.render.com/mentora_db` | Internal Database URL from your Render PostgreSQL instance |
| `SECRET_KEY` | **Yes** | *Generate a 50+ character random string* | Cryptographic signing key. Never use the default in production |
| `DEBUG` | **Yes** | `False` | Disables debug mode and activates security features |
| `ALLOWED_HOSTS` | Optional | `your-app.onrender.com,localhost` | Render automatically populates `RENDER_EXTERNAL_HOSTNAME` if omitted |
| `CSRF_TRUSTED_ORIGINS` | Optional | `https://your-app.onrender.com` | Automatically derived from `RENDER_EXTERNAL_HOSTNAME`, or set explicitly |
| `GEMINI_API_KEY` | **Yes** | `AIzaSy...` | Google Gemini API key for the Socratic AI Mentor |
| `GEMINI_MODEL` | Optional | `gemini-2.5-flash` | Gemini model identifier (default: `gemini-2.5-flash`) |
| `SESSION_COOKIE_SECURE`| Optional | `True` | Forces HTTPS for session cookies (defaults to `True` when `DEBUG=False`) |
| `CSRF_COOKIE_SECURE` | Optional | `True` | Forces HTTPS for CSRF cookies (defaults to `True` when `DEBUG=False`) |
| `SECURE_SSL_REDIRECT` | Optional | `True` | Redirects all HTTP traffic to HTTPS (defaults to `True` when `DEBUG=False`) |
| `MEDIA_ROOT` | Optional | `/var/data/media` | Path if a Render Persistent Disk is attached for scholar uploads |

---

### D. Step-by-Step Render Deployment Instructions

#### Step 1: Create a PostgreSQL Database on Render
1. Log in to your [Render Dashboard](https://dashboard.render.com/).
2. Click **New +** and select **PostgreSQL**.
3. Fill in the details:
   - **Name**: `mentora-postgres`
   - **Database**: `mentora_db`
   - **User**: `mentora_user`
   - **Region**: Choose the region closest to you (e.g. *Singapore* or *Oregon*).
   - **Plan**: *Free* or *Starter*.
4. Click **Create Database**.
5. Once provisioned, locate the **Internal Database URL** (e.g., `postgres://mentora_user:password@dpg-xxxx:5432/mentora_db`). Copy this connection string.

#### Step 2: Create the Web Service on Render
1. In the Render Dashboard, click **New +** and select **Web Service**.
2. Connect your GitHub repository (`mentora-v3`).
3. Configure the service settings:
   - **Name**: `mentora-vrcf`
   - **Region**: Select the **same region** as your PostgreSQL database.
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn mentora.wsgi:application`
   - **Plan**: *Free* or *Starter*.

#### Step 3: Add Environment Variables
1. Scroll down to **Environment Variables** (or open the **Environment** tab).
2. Add each key-value pair listed in the table above:
   - `DATABASE_URL`: Paste the Internal Database URL from Step 1.
   - `SECRET_KEY`: Enter a secure random string (Render can generate this automatically).
   - `DEBUG`: `False`
   - `GEMINI_API_KEY`: Enter your Google Gemini API key.
   - `GEMINI_MODEL`: `gemini-2.5-flash`
3. Click **Create Web Service**.

#### Step 4: Verify the Build & Deployment
Render will automatically execute `./build.sh`:
1. Installs dependencies from `requirements.txt`.
2. Runs `python manage.py collectstatic --no-input` (WhiteNoise caches all CSS, JS, and branding logos).
3. Runs `python manage.py migrate --no-input` (applies all schema migrations to your online PostgreSQL database).
4. Starts Gunicorn with `gunicorn mentora.wsgi:application`.

Once the logs display `==> Your service is live at https://mentora-vrcf.onrender.com`, the web platform is running!

---

### E. Importing the Real 43 VRCF Scholars into Production

> [!IMPORTANT]
> To preserve data integrity and prevent unintentional overwrites, the student workbook is **NOT** automatically imported during every deployment.
> Import the 43 scholars once into your new production PostgreSQL database following this procedure.

1. Open your Web Service in the Render Dashboard.
2. Click on the **Shell** tab on the left menu (or connect via SSH).
3. **Validate the workbook first (Dry Run)**:
   ```bash
   python manage.py import_students "prereq_data/VRCF Student DB.xlsx" --dry-run
   ```
   *Expected output*: `Identified 43 populated scholar rows. Dry run validation complete.`

4. **Execute the Real Import**:
   ```bash
   python manage.py import_students "prereq_data/VRCF Student DB.xlsx"
   ```
   *Output*:
   ```text
   === Mentora Student Importer ===
   Workbook Path: /opt/render/project/src/prereq_data/VRCF Student DB.xlsx
   Mode: REAL IMPORT
   Active Sheet: Form Responses 1 (Max rows: 44)
   Found 17 header columns.
   Identified 43 populated scholar rows.
   Seeded 10 core competencies.
   Seeded 4 curated academic resources.
   Seeded Admin, Trustee, and 4 Mentor foundation accounts (Lead, Manikandan, Avanthikaa, Ram Kumar).
   ----------------------------------------------------------------------------------------------------
   [1/43] VRCF-003 - Lakshanar (Cohort 1) -> User: lakshanar@gmail.com
   ...
   [43/43] VRCF-032 - Suhail Akthar S M (Cohort 2) -> User: suhailmobina95@gmail.com
   ----------------------------------------------------------------------------------------------------
   Successfully imported and verified 43 VRCF scholars into PostgreSQL.
   ```

All 43 scholar accounts, foundation trustee, administrators, and mentors (**Manikandan**, **Avanthikaa**, and **Ram Kumar**) are now live in the production database!

---

### F. Persistent Storage for Uploaded Media Files

- **ReportLab PDF Growth Reports** are generated in-memory (`io.BytesIO`) and streamed directly via HTTP. They do not touch the disk and are never lost on redeployment.
- **Scholar Avatars, Vision Boards & Task Attachments** are saved to `MEDIA_ROOT`.
  - On Render's Free tier, the filesystem is ephemeral and resets on each redeploy.
  - To persist user uploads across redeploys, add a **Render Disk** under the **Disks** tab:
    - **Mount Path**: `/var/data/media`
    - **Size**: 1 GB (or as needed)
    - Set the environment variable: `MEDIA_ROOT=/var/data/media`
  - Mentora's [urls.py](mentora/urls.py) automatically serves media from `MEDIA_ROOT` via `re_path`, ensuring photos and submissions remain available without requiring external S3 setup.

---

## 7. Windows-Friendly Local Testing

To test the application locally on Windows prior to deployment:

```powershell
# 1. Activate Virtual Environment
.\.venv\Scripts\activate

# 2. Run Django System Checks
.\.venv\Scripts\python.exe manage.py check

# 3. Test Static Collection
.\.venv\Scripts\python.exe manage.py collectstatic --noinput

# 4. Run Automated Test Suite
.\.venv\Scripts\python.exe manage.py test --noinput

# 5. Start Development Server
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

---

## 8. Database Backup & Restore

### Backup Local or Remote PostgreSQL Database:
```bash
pg_dump -U postgres -h <HOST> -p <PORT> -F c -b -v -f mentora_db_backup.dump <DBNAME>
```

### Restore to PostgreSQL Database:
```bash
pg_restore -U postgres -h <HOST> -p <PORT> -d <DBNAME> -v mentora_db_backup.dump
```

---

## 9. License & Attribution

Developed for the **Vasumathi Ramaswami Centenary Foundation (VRCF)**. All rights reserved.

