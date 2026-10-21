# MENTORA — Workbook Import & Validation Report
**Vasumathi Ramaswami Centenary Foundation (VRCF)**

---

## 1. Import Execution Summary

| Parameter | Value |
| :--- | :--- |
| **Execution Timestamp** | 2026-10-21 (Authoritative Run) |
| **Source Workbook** | `VRCF Student DB.xlsx` (`prereq_data/VRCF Student DB.xlsx`) |
| **Target Database** | PostgreSQL 16 (`mentora_db`) |
| **Total Populated Rows in Excel** | 43 |
| **Records Processed** | 43 |
| **Records Imported to PostgreSQL** | 43 |
| **Duplicate VRCF IDs** | 0 |
| **Conflicts / Unresolved Rows** | 0 |
| **Database Transaction Status** | Committed (Atomic transaction) |

---

## 2. Seeded Administrative & Oversight Accounts

| Role | Name | Email | Username | Initial Password | Access Level |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **ADMIN** | System Administrator | `admin@gmail.com` | `admin` | `admin@123` | Full Administrative & Provisioning |
| **TRUSTEE** | VRCF Foundation Trustee | `trustee@gmail.com` | `trustee` | `trustee@123` | Organizational Oversight & Analytics |
| **MENTOR** | VRCF Lead Mentor | `mentor@gmail.com` | `mentor` | `mentor@123` | Scholar Roster & Assignment Reviews |

---

## 3. Imported Scholars Roster (43 Students)

All accounts have been initialized with standard default credentials (`vrcf<VRCF_ID_numeric>`), and scholars can update their password in their Settings.

| # | VRCF ID | Scholar Name | Cohort | Registered Email | Username | Default Password | Degree Course | District |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | VRCF-003 | Lakshana R | Cohort 1 | lakshana042006@gmail.com | vrcf3 | `vrcf3` | B.Com | Coimbatore |
| 2 | VRCF-018 | Jasmiya J | Cohort 2 | jasmiya495@gmail.com | vrcf18 | `vrcf18` | B.Com Accounting and Fina | Mayiladuthurai |
| 3 | VRCF-042 | Suja S | Cohort 3 | ssuja.it2025@citchennai.net | vrcf42 | `vrcf42` | B.Tech IT | Villupuram |
| 4 | VRCF-049 | AVP Varshith | Cohort 3 | avpvarshith1@gmail.com | vrcf49 | `vrcf49` | B.Sc CS with Cybersecurit | Coimbatore |
| 5 | VRCF-031 | Balabharathi A | Cohort 2 | balabharathiannadurai@gmail.com | vrcf31 | `vrcf31` | IT | Cuddalore |
| 6 | VRCF-047 | Bhavani M | Cohort 3 | bhavanim3092006@gmail.com | vrcf47 | `vrcf47` | B.E CSE | Chennai |
| 7 | VRCF-030 | Komugi S | Cohort 2 | swissgi08@gmail.com | vrcf30 | `vrcf30` | B.E CSE | Perambalur |
| 8 | VRCF-036 | Kalaivani S | Cohort 1 | kalaivanigokul55@gmail.com | vrcf36 | `vrcf36` | B.E CSE | Tiruchirappalli |
| 9 | VRCF-037 | Kaviya M | Cohort 1 | murugankaviya007@gmail.com | vrcf37 | `vrcf37` | AI & DS | Villupuram |
| 10 | VRCF-034 | Kavin G S | Cohort 2 | kavings2007@gmail.com | vrcf34 | `vrcf34` | B.E CSE | Cuddalore |
| 11 | VRCF-035 | Supritha R | Cohort 2 | supritha21122007@gmail.com | vrcf35 | `vrcf35` | B.E CSE | Cuddalore |
| 12 | VRCF-007 | Pavithra P | Cohort 1 | pavithra.212123@gmail.com | vrcf7 | `vrcf7` | BSMS | Nagapattinam |
| 13 | VRCF-044 | Najiya Nasrin | Cohort 3 | najiyanasrin674@gmail.com | vrcf44 | `vrcf44` | B.Tech CSE (AIML) | Nilgiris |
| 14 | VRCF-022 | Sivachitrakumar R V | Cohort 1 | dr.sivaofficial3161@gmail.com | vrcf22 | `vrcf22` | BSMS | Nagapattinam |
| 15 | VRCF-027 | Kaviya S | Cohort 2 | sankarmageshwari2021@gmail.com | vrcf27 | `vrcf27` | B.Sc Biotechnology | Kanchipuram |
| 16 | VRCF-012 | B. Muthulakshmi | Cohort 1 | mlakshmi2860@gmail.com | vrcf12 | `vrcf12` | B.Com | Theni |
| 17 | VRCF-008 | Varsha | Cohort 1 | varsha17813@gmail.com | vrcf8 | `vrcf8` | BBA | Karur |
| 18 | VRCF-038 | Nilashini S | Cohort 1 | nilashini2007@gmail.com | vrcf38 | `vrcf38` | B.E CSE | Chennai |
| 19 | VRCF-046 | Arthardan Muthu G | Cohort 3 | arthuarthu230@gmail.com | vrcf46 | `vrcf46` | B.E CSE | Thiruvarur |
| 20 | VRCF-040 | Ashwini A | Cohort 3 | ashwiniannamalai27@gmail.com | vrcf40 | `vrcf40` | B.E CSE | Chennai |
| 21 | VRCF-026 | Meena | Cohort 2 | amuthameena580@gmail.com | vrcf26 | `vrcf26` | B.Pharm | Nagapattinam |
| 22 | VRCF-029 | Vijayaragavan K | Cohort 2 | vijayragavan6578@gmail.com | vrcf29 | `vrcf29` | AI & DS | Cuddalore |
| 23 | VRCF-043 | Shakilan R | Cohort 3 | shakilanr16@gmail.com | vrcf43 | `vrcf43` | AI & DS | Mayiladuthurai |
| 24 | VRCF-048 | Surendhar V | Cohort 3 | surendharv2108@gmail.com | vrcf48 | `vrcf48` | B.E CSE | Cuddalore |
| 25 | VRCF-033 | Raghul M | Cohort 2 | raghulmurugadoss6013@gmail.com | vrcf33 | `vrcf33` | B.E ECE | Krishnagiri |
| 26 | VRCF-021 | Ramya R | Cohort 1 | ramyaramasamy2006@gmail.com | vrcf21 | `vrcf21` | BSMS | Nagapattinam |
| 27 | VRCF-019 | Saruthi S | Cohort 2 | saruthis0@gmail.com | vrcf19 | `vrcf19` | B.A. LL.B (Hons) | Nagapattinam |
| 28 | VRCF-017 | Aakash B | Cohort 2 | tsbaakash232008@gmail.com | vrcf17 | `vrcf17` | B.E CSE | Thiruvarur |
| 29 | VRCF-024 | Janardhanan B | Cohort 2 | janardhananbalasubramani@gmail.com | vrcf24 | `vrcf24` | B.Tech Rubber and Plastic | Chengalpattu |
| 30 | VRCF-009 | Madhu | Cohort 1 | madhumadhu80041@gmail.com | vrcf9 | `vrcf9` | B.E ECE | Thoothukudi |
| 31 | VRCF-023 | Vijay | Cohort 1 | vijayv@student.tce.edu | vrcf23 | `vrcf23` | B.Tech CSBS | Nagapattinam |
| 32 | VRCF-045 | Keshavarthan K | Cohort 3 | kdkeshav0223@gmail.com | vrcf45 | `vrcf45` | B.E CSE | Kanchipuram |
| 33 | VRCF-039 | Monisha E | Cohort 3 | emonisha.cse2025@citchennai.net | vrcf39 | `vrcf39` | B.E CSE | Tiruvallur |
| 34 | VRCF-006 | S. Selvaleka | Cohort 1 | selvalekapandiyan16@gmail.com | vrcf6 | `vrcf6` | B.Sc (Hons) Agriculture | Thanjavur |
| 35 | VRCF-032 | Suhail Akthar S M | Cohort 2 | suhailmobina95@gmail.com | vrcf32 | `vrcf32` | B.Tech IT & B.S in DS | Cuddalore |
| 36 | VRCF-050 | Nithiya Sri G | Cohort 3 | 25ad105@rmkcet.ac.in | vrcf50 | `vrcf50` | B.E CSE (AI) | Theni |
| 37 | VRCF-011 | Ashvini | Cohort 1 | ashvini16102005@gmail.com | vrcf11 | `vrcf11` | MBBS | Namakkal |
| 38 | VRCF-025 | Johnveshlin | Cohort 2 | johnvesleen1010@gmail.com | vrcf25 | `vrcf25` | B.Sc Operation Theatre an | Nagapattinam |
| 39 | VRCF-004 | Dhineshkumar R | Cohort 1 | dhineshrp2007@gmail.com | vrcf4 | `vrcf4` | B.Com | Karur |
| 40 | VRCF-051 | Ramprasath B | Cohort 3 | ramprasathb99@gmail.com | vrcf51 | `vrcf51` | B.E EIE | Kanchipuram |
| 41 | VRCF-041 | Jannathur Raabiya | Cohort 3 | jannathurraabiya311007@gmail.com | vrcf41 | `vrcf41` | B.E CSE | Chennai |
| 42 | VRCF-005 | Mukilvendan P | Cohort 1 | mukilvendan7@gmail.com | vrcf5 | `vrcf5` | B.E CSE | Namakkal |
| 43 | VRCF-015 | Suganya L | Cohort 1 | boopathisugusugu@gmail.com | vrcf15 | `vrcf15` | B.E EEE | Salem |

---

## 4. Key Entity Invariants Verified

1. **Authentication:**
   - Scholars can log in using either their registered **Email** or their **Username** (`vrcf<id>`).
   - Specifically, scholar **Suhail Akthar S M** (`VRCF-032`) authenticates with `suhailmobina95@gmail.com` and initial password `vrcf32`.
2. **Mentorship Assignment:**
   - All 43 imported scholars are linked to the VRCF Lead Mentor profile with an active onboarding assignment.
3. **Data Integrity:**
   - Zero fabricated records.
   - All profile details (residence, hostel fees, tuition payment terms, parent contact numbers) faithfully match the submitted form data.
