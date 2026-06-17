# 🧾 OCR Invoice — Handwritten Multilingual Invoice OCR System

> **Snap a bill. Get structured data. In any Indian language.**

AI-powered web app that scans handwritten invoices and extracts product names, quantities, prices and totals — supporting English, Hindi, Marathi, Gujarati, Tamil and Telugu.

---

## ✨ What It Does

| Feature | Detail |
|---|---|
| 📸 Image Upload | Drag & drop JPG / PNG / TIFF / BMP (max 10 MB) |
| 🔍 OCR Engine | PaddleOCR with multilingual script support |
| 🧠 AI Parser | Converts raw text → validated JSON (regex + NLP + rule engine) |
| 🌐 6 Languages | EN · HI · MR · GU · TA · TE (auto-detect available) |
| 🗄️ Cloud DB | Supabase PostgreSQL — invoice master + line items |
| 🔐 Auth | JWT login/register, 24-hr token, bcrypt passwords |
| 📊 Dashboard | Confidence metrics, language volume, recent runs |
| 🗂️ History | Searchable, sortable, paginated invoice records |

---

## 🏗️ Tech Stack

```
Frontend  →  React 18 + Vite 5 + Tailwind CSS
Backend   →  FastAPI (Python 3.11) + Uvicorn
OCR       →  PaddleOCR / EasyOCR (Claude Vision ready)
Database  →  Supabase PostgreSQL (asyncpg + SQLAlchemy 2.0)
Auth      →  JWT HS256 + bcrypt
```

---

## 🚀 Quick Start

### Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# add .env with DATABASE_URL and SECRET_KEY
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev          # → http://localhost:5173
```

> API docs live at **http://localhost:8000/docs**

---

## 🔌 API Endpoints

```
POST   /api/v1/invoice/upload   Upload & process a handwritten invoice
GET    /api/v1/invoices         Paginated invoice list (search + sort)
GET    /api/v1/invoices/{id}    Full invoice detail with line items
DELETE /api/v1/invoices/{id}    Remove invoice record
POST   /api/v1/auth/token       Login → get JWT
POST   /api/v1/auth/register    Create new account
GET    /api/v1/health           API + DB health check
```

---

## 🧩 OCR Pipeline

```
Upload → OpenCV Preprocessing → OCR Engine → AI Parser → Validator → Database
           │                       │              │            │
      Denoise / Deskew /      PaddleOCR     Regex + NLP   Total
      Binarize / Enhance      Multilingual  Line Items    Cross-check
```

---

## 🗃️ Database Schema

**invoice_master** — `id · invoice_number · grand_total · confidence_score · language_detected · raw_text · warnings · created_at`

**invoice_items** — `id · invoice_id (FK) · product_name · quantity · unit_price · total_amount`

---

## 🌍 Supported Languages

| Code | Language | Script |
|---|---|---|
| `en` | English | Latin |
| `hi` | Hindi | Devanagari |
| `mr` | Marathi | Devanagari |
| `gu` | Gujarati | Gujarati |
| `ta` | Tamil | Tamil |
| `te` | Telugu | Telugu |

---

## 📁 Project Structure

```
├── backend/
│   ├── api/v1/endpoints/     # invoices · auth · health
│   ├── ocr/                  # ocr_engine · parser · adapter
│   ├── preprocessing/        # image_processor (OpenCV)
│   ├── services/             # ocr_service (pipeline orchestrator)
│   ├── repositories/         # invoice_repository (async DB)
│   ├── models/               # SQLAlchemy ORM models
│   ├── schemas/              # Pydantic request/response schemas
│   └── validators/           # invoice_validator
└── frontend/
    └── src/
        ├── pages/            # Dashboard · Upload · History · Login
        ├── components/       # InvoiceDetailModal
        └── services/         # api.js (fetch wrapper + auth)
```

---

## 🔑 Demo Credentials

```
username: admin   password: admin123
username: demo    password: demo123
```

---

## 🛣️ Roadmap

- [ ] Claude Vision API as primary OCR engine
- [ ] Supabase Auth (persistent user accounts)
- [ ] Indian numeral script support (०–९, ૦–૯, ௦–௯)
- [ ] PDF invoice support
- [ ] Async job queue (Celery + Redis)
- [ ] Docker Compose deployment
- [ ] Export to Excel / CSV

---

## 📄 License

MIT — built by **Suraj Antre**, June 2026.