# 📦 Pack Manager

### AI-powered outbound packing verification

Pack Manager is an AI-assisted packing verification system that checks an open package against the customer's expected order **before the package is sealed**.

The system combines computer vision with deterministic verification logic to identify:

* ✅ Correct items
* ❌ Missing items
* ❌ Unexpected/extra items
* ❌ Wrong quantities
* ⚠️ Uncertain visual observations
* ⏳ Failed AI verification requiring human review

The final operational decision is either:

> **SEAL** — all required items were verified

or

> **STOP & FIX** — something is missing, incorrect, uncertain, or requires review

---

## 🎯 Problem

Packing mistakes are expensive.

A warehouse operator may accidentally:

* Pick the wrong SKU
* Forget an item
* Pick the wrong quantity
* Add an unexpected item
* Seal a package when the visual evidence is unclear

Traditional workflows often depend on manual checking immediately before shipment.

Pack Manager adds an AI-assisted verification step:

```text
Open package
     ↓
Take photo
     ↓
AI identifies visible products
     ↓
Compare against order
     ↓
Generate evidence
     ↓
SEAL / STOP & FIX
```

---

# 🧠 How It Works

Pack Manager follows a simple three-stage architecture:

```text
              ┌──────────────────┐
              │   Package Photo  │
              └────────┬─────────┘
                       ↓
              ┌──────────────────┐
              │ Vision Inspection│
              │      AI          │
              └────────┬─────────┘
                       ↓
              ┌──────────────────┐
              │   Observations   │
              │ SKU + quantity   │
              │ + evidence       │
              └────────┬─────────┘
                       ↓
              ┌──────────────────┐
              │ Deterministic    │
              │ Verification     │
              └────────┬─────────┘
                       ↓
          ┌────────────┴────────────┐
          ↓                         ↓
       VERIFIED                  UNCERTAIN
          ↓                         ↓
     ┌────┴────┐              STOP & FIX
     ↓         ↓
   MATCH     MISMATCH
     ↓         ↓
   SEAL    STOP & FIX
```

The AI is responsible for **visual observation**.

The application code is responsible for the **final verification decision**.

This separation prevents the vision model from independently deciding whether an order should ship.

---

# 🏗️ Architecture

```text
React Frontend
      │
      │ multipart request
      ↓
FastAPI Backend
      │
      ├── Order Parser
      │
      ├── Product Catalogue
      │
      ├── Vision Inspection
      │       └── OpenAI vision model
      │
      ├── Deterministic Verifier
      │
      ├── PostgreSQL / Supabase
      │
      └── Supabase Storage
```

### Main components

| Component     | Purpose                                     |
| ------------- | ------------------------------------------- |
| React + Vite  | Operator dashboard                          |
| FastAPI       | Backend API                                 |
| OpenAI Vision | Visual product observation                  |
| Pydantic      | Structured data validation                  |
| PostgreSQL    | Products, captures and verification results |
| Supabase      | Database and object storage                 |
| SQLAlchemy    | Database connectivity                       |
| RLS           | Tenant isolation                            |
| Python        | Verification and backend logic              |

---

# 🔍 Vision Layer

The vision model receives:

1. Package image
2. Authoritative product catalogue

The model is instructed to:

* Identify visible catalogue products
* Estimate observed quantities
* Provide visual evidence
* Mark observations as `observed` or `uncertain`
* Avoid inventing SKUs
* Avoid making the final packing decision

Example observation:

```json
{
  "sku": "CAP-BLU",
  "quantity": 1,
  "status": "observed",
  "evidence": "One blue baseball cap is clearly visible."
}
```

The vision layer does **not** decide `SEAL` or `STOP & FIX`.

---

# ⚖️ Deterministic Verification

After visual inspection, the backend compares expected and observed quantities by SKU.

Example:

```text
Expected:
TSHIRT-BLK: 2
CAP-BLU: 1

Observed:
TSHIRT-BLK: 2
CAP-BLU: 1
```

Result:

```text
SEAL
```

Another example:

```text
Expected:
TSHIRT-BLK: 2

Observed:
TSHIRT-BLK: 1
```

Result:

```text
STOP & FIX
```

The verifier handles:

* Missing products
* Extra products
* Wrong quantities
* Matching quantities
* Uncertain observations

---

# ⚠️ Uncertainty

Uncertainty is treated as a first-class verification state.

If the image does not provide enough evidence to confidently identify an item, Pack Manager does not force a positive conclusion.

Example:

```text
Verification status:
UNCERTAIN

Operational decision:
STOP & FIX

Reason:
Verification is uncertain and requires human review.
```

This allows the system to distinguish:

```text
❌ Verified mismatch
```

from:

```text
⚠️ Insufficient evidence
```

---

# ⏳ Fail-Open Behaviour

AI services can fail.

Pack Manager therefore saves the package capture before attempting visual verification.

If the vision call fails:

```text
Package capture
      ↓
Saved successfully
      ↓
Vision failure
      ↓
PENDING
      ↓
Human review
```

The package does not disappear from the system simply because an AI call failed.

---

# 🔐 Tenant Isolation

Pack Manager uses organization-scoped database records.

Every major table contains an `org_id`:

```text
organizations
products
pack_captures
verification_results
```

PostgreSQL Row Level Security is enabled and forced.

The application uses a restricted database role rather than relying on the privileged database administrator role.

The tenant context is applied before querying organization-scoped records.

Example:

```text
org_demo_alpha
    ↓
Alpha products only

org_demo_bravo
    ↓
Bravo products only
```

The isolation was tested using the restricted application database role.

---

# ☁️ Image Storage

Package images are stored in a private Supabase Storage bucket:

```text
pack-images/
└── <organization-id>/
    └── <unique-image-id>.jpg
```

The backend stores the image in object storage while also creating a package capture record.

Images are not stored as publicly accessible files.

---

# 🖥️ Dashboard

The operator dashboard provides:

* Organization
* Order ID
* Expected order lines
* Package image upload
* Verification action
* Final packing decision
* Expected vs observed quantities
* Verification status
* Visual evidence

Example:

```text
PACKING DECISION

SEAL

CAP-BLU
Expected and observed quantities match.

Evidence:
One blue baseball cap is clearly visible.

             1 / 1    PASS
```

---

# 🧪 Tested Scenarios

The system was tested against multiple packing conditions.

### 1. Correct package

```text
Expected:
TSHIRT-BLK:1
CAP-BLU:1
SOCK-RED:1

Observed:
TSHIRT-BLK:1
CAP-BLU:1
SOCK-RED:1

Decision:
SEAL
```

### 2. Extra item

```text
Expected:
TSHIRT-BLK:1
CAP-BLU:1

Observed:
TSHIRT-BLK:1
CAP-BLU:1
SOCK-RED:1

Decision:
STOP & FIX
```

### 3. Wrong quantity

```text
Expected:
TSHIRT-BLK:2

Observed:
TSHIRT-BLK:1

Decision:
STOP & FIX
```

### 4. Missing quantity

```text
Expected:
SOCK-RED:2

Observed:
SOCK-RED:1

Decision:
STOP & FIX
```

### 5. Uncertain visual evidence

A deliberately blurry/low-confidence package image was tested.

Result:

```text
Verification:
UNCERTAIN

Decision:
STOP & FIX
```

### 6. Vision failure

The vision model failure path was tested.

Result:

```text
Decision:
PENDING
```

while the package capture remained persisted for review.

---

# 📁 Project Structure

```text
cube-03-pack-manager/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── catalog/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── services/
│   │       ├── vision/
│   │       ├── verifier.py
│   │       ├── order_parser.py
│   │       ├── catalog_service.py
│   │       ├── persistence.py
│   │       └── storage.py
│   │
│   ├── fixtures/
│   ├── tests/
│   ├── data/
│   └── .env
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   └── App.css
│   └── package.json
│
├── data/
├── RULES.md
├── GITHUB-GUIDE.md
└── README.md
```

---

# 🚀 Local Setup

## Backend

```bash
cd backend

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

Create:

```text
backend/.env
```

with the required OpenAI, database and Supabase configuration.

Start the API:

```bash
uvicorn app.main:app --reload
```

API:

```text
http://127.0.0.1:8000
```

Health check:

```text
GET /health
```

---

## Frontend

```bash
cd frontend

npm install
npm run dev
```

Open the Vite development URL shown in the terminal.

---

# 📡 API

### `GET /health`

Returns:

```json
{
  "status": "ok",
  "service": "pack-manager"
}
```

### `POST /verify`

Multipart form fields:

```text
org_id
order_id
order_lines
image
```

Example:

```text
org_id=org_demo_alpha
order_id=ORD-001
order_lines=TSHIRT-BLK:1;CAP-BLU:1;SOCK-RED:1
image=<package photo>
```

The response contains:

* Capture ID
* Expected items
* Observed items
* Verification checks
* Verification status
* Decision
* Reason
* Evidence

---

# 🔒 Security Notes

The project uses:

* Organization-scoped database records
* PostgreSQL RLS
* Restricted application database role
* Private object storage
* Server-side API access to AI services
* Environment variables for credentials

Production deployment would additionally require authenticated user identity and deriving the organization from the authenticated session rather than trusting a client-provided `org_id`.

---

# 🎯 Design Principles

### AI observes. Code verifies.

The vision model should answer:

> “What can I actually see?”

The deterministic verifier answers:

> “Does what we observed satisfy the order?”

This makes the final operational decision auditable and predictable.

### Don't guess.

When visual evidence is insufficient:

```text
UNCERTAIN
```

not:

```text
probably correct
```

### Fail safely.

If verification cannot be completed:

```text
PENDING
```

rather than silently allowing the package to proceed.

---

# 🔮 Future Improvements

Potential next steps include:

* Reference images for visually similar SKUs
* Operator correction/override workflow
* Authenticated organization identity
* Signed image URLs with authorization checks
* Order management integration
* Barcode/QR verification
* Multi-image package inspection
* Historical accuracy dashboards
* Human-in-the-loop review queue
* Production deployment and monitoring

---

# 🏆 Hackathon Summary

Pack Manager turns a simple package photograph into an actionable packing decision:

```text
PHOTO
  ↓
VISION
  ↓
EVIDENCE
  ↓
DETERMINISTIC VERIFICATION
  ↓
SEAL / STOP & FIX
```

The goal is not to replace the warehouse operator.

The goal is to give the operator a reliable verification layer **before the box is sealed**.
