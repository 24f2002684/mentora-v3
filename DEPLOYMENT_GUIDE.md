# MENTORA — Cloud Deployment Guide
**Architecture: Render (Web Service) + Supabase (PostgreSQL & Storage)**
*Vasumathi Ramaswami Centenary Foundation (VRCF)*

---

## Architecture Overview

```
                      +---------------------------------------+
                      |             End Users                 |
                      |  (Scholars, Mentors, Trustees, Admin) |
                      +-------------------+-------------------+
                                          | HTTPS
                                          v
                      +---------------------------------------+
                      |         Render Web Service            |
                      |  - Runtime: Python 3.11 / Django 5.2  |
                      |  - WSGI Server: Gunicorn              |
                      |  - Static Files: WhiteNoise           |
                      |  - Health: /health/ and /health/db/   |
                      +---------+-------------------+---------+
                                |                   |
                 PostgreSQL SSL |                   | S3 Presigned URLs
               (Session Pooler) |                   | (1-hour expiry)
                                v                   v
          +-----------------------+     +-----------------------+
          |  Supabase PostgreSQL  |     |   Supabase Storage    |
          |  - Host: pooler...    |     |  - S3 Gateway API     |
          |  - Port: 5432 (IPv4)  |     |  - Private Bucket:    |
          |  - DB: postgres       |     |    'mentora-media'    |
          +-----------------------+     +-----------------------+
                                |
                                v
                      +-------------------+
                      | Google Gemini API |
                      | (Socratic Mentor) |
                      +-------------------+
```

---

## Prerequisites

Before starting, ensure you have:
1. A **GitHub account** with access to the Mentora repository (`https://github.com/24f2002684/mentora-v3`).
2. A free **Supabase account** ([supabase.com](https://supabase.com)).
3. A free **Render account** ([render.com](https://render.com)).
4. A **Google Gemini API Key** ([aistudio.google.com](https://aistudio.google.com)).

---

## Step 1: Create and Configure the Supabase Project

1. Log in to your [Supabase Dashboard](https://supabase.com/dashboard).
2. Click **New project**.
3. Fill in the project details:
   - **Name**: `mentora-vrcf`
   - **Database Password**: Choose a strong password and **save it safely** (you will need it for the connection string).
   - **Region**: Choose the region closest to your users (e.g., `Singapore (ap-southeast-1)` or `Mumbai (ap-south-1)`).
   - **Pricing Plan**: Free Tier.
4. Click **Create new project** and wait 1-2 minutes for provisioning to finish.
5. Note your **Project Reference ID** (found in the URL: `https://supabase.com/dashboard/project/<PROJECT_REF>`).

---

## Step 2: Get the IPv4 Session Pooler Connection String

> [!IMPORTANT]
> Render free web services communicate primarily over IPv4. Supabase's direct connection (`db.<ref>.supabase.co:5432`) resolves to IPv6 only on newer projects. You **MUST** use the **Session Pooler** connection string on **Port 5432** to ensure seamless, reliable connectivity.

1. In the Supabase Dashboard, go to **Project Settings** (gear icon at the bottom of the left sidebar).
2. Click **Database** in the sidebar.
3. Scroll down to the **Connection Pooling** section:
   - **Mode**: Select **Session** (Port `5432`).
   - **Type**: Select **URI**.
4. The connection string will look like this:
   ```text
   postgresql://postgres.[PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres
   ```
5. Replace `[YOUR-PASSWORD]` with the database password you chose in Step 1.
   *(If your password contains special characters like `@`, `#`, or `/`, URL-encode them, e.g. `@` becomes `%40`)*.
6. Copy this complete string — this is your `DATABASE_URL`.

---

## Step 3: Create the Private Supabase Storage Bucket

Mentora uses Supabase Storage for persistent media files (student profile photos, vision boards, task attachments).

1. In the Supabase left navigation bar, click **Storage**.
2. Click **New bucket**.
3. Enter:
   - **Bucket name**: `mentora-media`
   - **Public bucket**: **Disabled (OFF)** *(Mentora uses short-lived signed URLs for security)*.
4. Click **Save**.

---

## Step 4: Generate S3 Access Keys in Supabase

Supabase Storage provides an S3-compatible API that connects directly to Django's `storages.backends.s3.S3Storage`:

1. In the Supabase Dashboard, click **Project Settings** (gear icon) → **Storage**.
2. Scroll to the **S3 Access Keys** section.
3. Click **New access key** (or **Generate credentials**).
4. Enter a description like `mentora-render` and click **Create access key**.
5. Copy the credentials:
   - **Access Key ID** (e.g. `2418a9...`)
   - **Secret Access Key** (e.g. `982f1b...`)
   - **Endpoint**: `https://<PROJECT-REF>.storage.supabase.co/storage/v1/s3`

---

## Step 5: Create and Configure the Render Web Service

1. Log in to [dashboard.render.com](https://dashboard.render.com).
2. Click **New +** → **Web Service**.
3. Select **Build and deploy from a Git repository**.
4. Select `24f2002684/mentora-v3` (or connect your GitHub repository).
5. Configure the service settings:
   - **Name**: `mentora-vrcf`
   - **Region**: Choose the region closest to your Supabase region (e.g., `Singapore` or `Frankfurt`).
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn mentora.wsgi:application`
   - **Instance Type**: `Free`
6. Scroll down to **Environment Variables** and add the following keys:

| Environment Variable | Recommended Value | Notes |
| :--- | :--- | :--- |
| `SECRET_KEY` | *(50+ char random string)* | Django cryptographic key |
| `DEBUG` | `False` | Disables debug mode in production |
| `DATABASE_URL` | *(Session Pooler URI from Step 2)* | Port 5432 Supabase pooler URL |
| `CONN_MAX_AGE` | `60` | Recommended pooler connection age |
| `USE_SUPABASE_STORAGE` | `True` | Activates Supabase S3 file storage |
| `SUPABASE_PROJECT_REF` | `<your-project-ref>` | Supabase reference ID |
| `SUPABASE_STORAGE_ACCESS_KEY_ID` | `<access-key-id>` | S3 Access Key from Step 4 |
| `SUPABASE_STORAGE_SECRET_ACCESS_KEY` | `<secret-access-key>` | S3 Secret Key from Step 4 |
| `SUPABASE_STORAGE_ENDPOINT_URL` | `https://<ref>.storage.supabase.co/storage/v1/s3` | S3 Gateway Endpoint |
| `SUPABASE_STORAGE_BUCKET_NAME` | `mentora-media` | Bucket created in Step 3 |
| `SUPABASE_STORAGE_REGION` | `us-east-1` | Supabase S3 default region |
| `GEMINI_API_KEY` | *(Your Gemini API Key)* | Required for Socratic AI tutor |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Stable, fast AI model |
| `ALLOWED_HOSTS` | `mentora-vrcf.onrender.com` | Or your custom domain |
| `CSRF_TRUSTED_ORIGINS` | `https://mentora-vrcf.onrender.com` | Full HTTPS domain |
| `PYTHON_VERSION` | `3.11.9` | Python runtime version |

7. Click **Create Web Service**.

---

## Step 6: Deploy and Monitor the Build

1. Render will automatically run `./build.sh`:
   - Installs all dependencies from `requirements.txt` (including `psycopg`, `django-storages`, and `boto3`).
   - Collects and compresses static files via WhiteNoise (`collectstatic --no-input`).
   - Connects to Supabase PostgreSQL and applies all initial migrations (`migrate --no-input`).
2. Once the build finishes, Gunicorn starts:
   ```text
   ==> Running 'gunicorn mentora.wsgi:application'
   [INFO] Starting gunicorn 22.0.0
   [INFO] Listening at: http://0.0.0.0:10000
   ==> Your service is live 🎉
   ```
3. Visit your live Render URL (e.g., `https://mentora-vrcf.onrender.com`).

---

## Step 7: Import Real Student Records into Supabase PostgreSQL

> [!NOTE]
> The student import command is deliberately **not** executed in `build.sh` so that student records are not re-processed on every deploy. You run this command **once** from the Render Shell.

1. In the Render Dashboard, navigate to your `mentora-vrcf` web service.
2. Click the **Shell** tab on the left to open a secure console inside the running container.
3. **Step 7A: Run Dry-Run Validation** (validates the spreadsheet without modifying the database):
   ```bash
   python manage.py import_students "prereq_data/VRCF Student DB.xlsx" --dry-run
   ```
   *Expected Output*:
   ```text
   [DRY RUN] Successfully validated 43 scholar records with 0 duplicate VRCF IDs.
   ------------------------------------------------------------------------------------------
   Row   | VRCF ID    | Scholar Name             | Cohort     | Username   | Course              
   ------------------------------------------------------------------------------------------
   2     | VRCF-003   | Lakshana R               | Cohort 1   | vrcf3      | B.Com
   ...
   All 43 records verified. Dry-run complete (no database modifications were made).
   ```
4. **Step 7B: Execute the Real Import**:
   ```bash
   python manage.py import_students "prereq_data/VRCF Student DB.xlsx"
   ```
   *Output*:
   ```text
   Seeded 10 core competencies.
   Seeded 6 curated academic resources.
   Seeded Admin, Trustee, and 4 Mentor foundation accounts.
   Successfully imported and provisioned 43 VRCF scholars!
   Generated IMPORT_REPORT.md successfully.
   ```
   *Note: If run again in the future, this command is completely idempotent. It uses `update_or_create` and preserves any passwords students have already changed.*

---

## Step 8: (Optional) Migrate Existing Local Media Files to Supabase

If you have existing student photos or vision boards in your local `media/` directory that you want uploaded to your Supabase bucket:

From your local Windows PowerShell terminal (with Supabase environment variables active):
```powershell
# 1. Preview what files will be uploaded
.\.venv\Scripts\python.exe manage.py upload_media_to_supabase --dry-run

# 2. Upload to Supabase Storage
.\.venv\Scripts\python.exe manage.py upload_media_to_supabase
```

Or you can drag and drop them directly into the `mentora-media` bucket in the Supabase Storage web dashboard.

---

## Step 9: Verify Application Health and Uptime

Mentora provides two health check endpoints:

1. **Web Process Liveness Check**:
   ```text
   GET https://mentora-vrcf.onrender.com/health/
   ```
   - **Response**: `{"status": "healthy", "service": "mentora-web", "version": "3.0"}` (HTTP 200)
   - Fast, lightweight check verifying that Django and Gunicorn are responding. Does not hit the database.

2. **Database Readiness Check**:
   ```text
   GET https://mentora-vrcf.onrender.com/health/db/
   ```
   - **Response**: `{"status": "healthy", "database": "connected", "service": "mentora-web"}` (HTTP 200)
   - Executes a minimal `SELECT 1;` query against Supabase PostgreSQL. Never exposes credentials or SQL errors.

> [!NOTE]
> A successful HTTP health check alone does not guarantee that the database or all external AI services are healthy. Monitor both `/health/` and `/health/db/` for full observability.

---

## Default Administrative Accounts

After running the student import, the following foundation accounts are available:

| Role | Username / Email | Initial Password | Access Level |
| :--- | :--- | :--- | :--- |
| **System Admin** | `admin` / `admin@gmail.com` | `admin@123` | Full access (`/admin/` & `/admin-tools/`) |
| **VRCF Trustee** | `trustee` / `trustee@gmail.com` | `trustee@123` | Strategic analytics & student oversight |
| **Lead Mentor** | `mentor` / `mentor@gmail.com` | `mentor@123` | Tasks, evaluations, and growth reports |
| **Mentor Manikandan** | `manikandan` / `manikandan@vrcf.org` | `mentor@123` | Mentor dashboard & task assignments |
| **Mentor Avanthikaa** | `avanthikaa` / `avanthikaa@vrcf.org` | `mentor@123` | Mentor dashboard & task assignments |
| **Mentor Ram Kumar** | `ramkumar` / `ramkumar@vrcf.org` | `mentor@123` | Mentor dashboard & task assignments |
| **Scholars (43)** | `vrcf<id>` or registered email | `vrcf<id>` | Individual scholar dashboard & AI tutor |

*(Users can update their password at any time via the user profile menu).*
