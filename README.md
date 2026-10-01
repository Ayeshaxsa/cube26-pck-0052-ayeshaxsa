# Pack Manager — AI Packing Verification Agent

> **AI observes. Deterministic logic verifies. Operators decide before the package leaves the warehouse.**

Pack Manager is an AI-powered outbound packing verification system that checks whether the contents of a package match the customer's order **before the package is sealed**.

The system combines computer vision with deterministic verification logic to identify:

* Missing items
* Wrong items
* Unexpected extra items
* Quantity mismatches
* Visually uncertain items

The final operational decision is:

* **SEAL** — all required items and quantities are verified.
* **STOP & FIX** — a packing issue is detected.
* **PENDING REVIEW** — automated verification could not be completed and requires operator review.

---

## Problem Understanding

In an outbound warehouse workflow, a package can be incorrectly sealed because of:

* A missing product
* The wrong product being packed
* Incorrect quantities
* An unexpected extra item
* Visually ambiguous evidence
* Automated verification failures

A useful packing verification system therefore cannot simply ask an AI model:

> "Is this package correct?"

Instead, the system needs to separate **visual observation** from **business verification**.

Pack Manager follows this principle:

```text
Package Image
     ↓
AI Vision Observation
     ↓
Deterministic Order Verification
     ↓
Evidence + Verification Status
     ↓
Operational Decision
```

This makes the final decision explainable and avoids relying on the vision model to perform business-critical quantity and order logic.

---

## Solution Overview

Pack Manager follows a **Perceive → Verify → Act** architecture.

### 1. Perceive

A vision model receives:

* The package image
* The organization's product catalogue
* Product descriptions and visual attributes

The model identifies products visible in the package and returns structured observations.

For each observed product, the system records:

```text
SKU
Observed quantity
Observation status
Visual evidence
```

The model is explicitly instructed not to invent products or make the final order decision.

### 2. Verify

The backend compares the AI observations against the customer's expected order.

The verification engine performs deterministic checks for every SKU:

```text
Expected quantity
        vs
Observed quantity
```

It identifies:

* PASS
* FAIL
* UNCERTAIN

Examples:

```text
Expected: TSHIRT-BLK × 2
Observed: TSHIRT-BLK × 2
→ PASS
```

```text
Expected: CAP-BLU × 1
Observed: CAP-BLU × 0
→ FAIL — Missing item
```

```text
Expected: CAP-BLU × 1
Observed: SOCK-RED × 1
→ FAIL — Wrong/unexpected item
```

### 3. Act

The verification result is converted into an operational decision:

```text
All checks pass
    ↓
SEAL
```

```text
Any verification failure
    ↓
STOP & FIX
```

```text
Insufficient/uncertain evidence
    ↓
UNCERTAIN
    ↓
STOP & FIX / Human Review
```

If the AI service fails or times out, the capture is still persisted and the result is marked as pending rather than silently losing the packing attempt.

---

# Architecture

```text
┌──────────────────────────┐
│      React Dashboard     │
│                          │
│ Order + Image Upload     │
│ Verification Results     │
└────────────┬─────────────┘
             │
             │ multipart request
             ▼
┌──────────────────────────┐
│       FastAPI API        │
│                          │
│ Capture + Orchestration  │
└────────────┬─────────────┘
             │
             ├──────────────► PostgreSQL
             │                Orders / Products /
             │                Captures / Results
             │
             ├──────────────► Supabase Storage
             │                Package Images
             │
             ▼
┌──────────────────────────┐
│     Vision Layer         │
│                          │
│ OpenAI Vision Model      │
│ Catalogue-aware prompt   │
└────────────┬─────────────┘
             │
             │ structured observations
             ▼
┌──────────────────────────┐
│ Deterministic Verifier   │
│                          │
│ Expected vs Observed     │
│ Quantity + SKU checks    │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│ Operational Decision     │
│                          │
│ SEAL / STOP & FIX /      │
│ PENDING                  │
└──────────────────────────┘
```

For the detailed technical architecture, see [`ARCHITECTURE.md`](ARCHITECTURE.md).

---

# Key Engineering Decisions

## AI observes, code verifies

The vision model is responsible for visual perception.

It does **not** decide whether the order is correct.

The backend performs the actual comparison between expected and observed quantities.

This keeps business-critical verification deterministic and explainable.

## Uncertainty is first-class

The system does not force a confident answer when the image does not provide enough evidence.

An observation can be:

```text
observed
```

or

```text
uncertain
```

An uncertain verification is surfaced to the operator instead of being silently treated as a successful match.

## Fail-open processing

If the vision service fails, times out, or returns an unusable response:

1. The package capture has already been persisted.
2. The verification result is recorded as pending.
3. The operator can review the package instead of losing the verification attempt.

This prevents an external model failure from silently dropping warehouse events.

## Tenant isolation

The backend uses PostgreSQL Row Level Security (RLS).

Data is scoped using an organization context:

```text
org_demo_alpha
org_demo_bravo
```

Application database access uses a restricted database role rather than a superuser connection.

This prevents application queries from freely reading another organization's catalogue, captures, or verification results.

## Authoritative catalogue

The vision prompt is generated from the organization's catalogue stored in PostgreSQL.

The model is not expected to remember SKU information or invent products.

---

# Project Structure

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
│   ├── requirements.txt
│   └── .env
│
├── frontend/
│   └── src/
│
├── data/
│
├── README.md
├── ARCHITECTURE.md
├── RULES.md
└── GITHUB-GUIDE.md
```

---

# Setup

## Requirements

* Python 3.11+
* Node.js
* PostgreSQL / Supabase
* OpenAI API key

---

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

with the required environment variables:

```env
OPENAI_API_KEY=your_openai_key
OPENAI_VISION_MODEL=your_vision_model

DATABASE_URL=your_postgresql_connection_string

SUPABASE_URL=your_supabase_project_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

Do not commit `.env` or any API keys.

Start the API:

```bash
uvicorn app.main:app --reload
```

The API should be available at:

```text
http://127.0.0.1:8000
```

Health check:

```text
GET /health
```

---

# Frontend

```bash
cd frontend
npm install
npm run dev
```

Open the Vite URL shown by the terminal.

The frontend allows the operator to:

1. Select the organization.
2. Enter an order.
3. Upload the package image.
4. Run verification.
5. Inspect the decision and supporting evidence.

---

# Usage

A typical verification request contains:

```text
Organization
Order ID
Order lines
Package image
```

Example order:

```text
TSHIRT-BLK:1;CAP-BLU:1;SOCK-RED:1
```

The system then:

```text
1. Saves the package capture
2. Loads the organization's catalogue
3. Sends the package image + catalogue context to the vision model
4. Receives structured observations
5. Compares observations with the order
6. Generates checks
7. Produces an operational decision
8. Displays the result and evidence
```

---

# Example Results

### Correct package

```text
TSHIRT-BLK    1 / 1    PASS
CAP-BLU       1 / 1    PASS
SOCK-RED      1 / 1    PASS

Decision: SEAL
```

### Missing item

```text
TSHIRT-BLK    1 / 1    PASS
CAP-BLU       0 / 1    FAIL

Decision: STOP & FIX
```

### Unexpected item

```text
Expected:
CAP-BLU × 1

Observed:
SOCK-RED × 1

Decision: STOP & FIX
```

### Uncertain image

When visual evidence is insufficient:

```text
Verification: UNCERTAIN

Decision: STOP & FIX
Reason: Human review required.
```

The system intentionally avoids turning weak visual evidence into a confident PASS.

---

# Reliability

The implementation was tested against several packing scenarios:

* Correct package
* Missing item
* Extra item
* Wrong quantity
* Multiple items
* Uncertain/blurry image
* Vision/model failure
* Cross-organization database isolation

The verification engine itself is deterministic once structured observations have been produced.

---

# Assumptions

* The product catalogue contains the products that can be packed.
* SKU identifiers are the authoritative product identifiers.
* Package images provide enough visual information for the vision model to identify products.
* The order lines supplied to the API represent the expected contents of the package.
* Human operators remain responsible for resolving uncertain cases.

---

# Limitations

### Product recognition

Vision accuracy depends on image quality, camera angle, lighting, occlusion, and how visually distinguishable products are.

### Quantity counting

Highly overlapping or partially hidden products may be difficult to count reliably.

### Demo authentication

The current demo uses an organization identifier supplied by the application rather than a full production authentication/authorization system.

A production deployment would derive the organization from the authenticated user's session.

### Human review

The system deliberately allows uncertain and pending outcomes. It is designed as a verification aid rather than a replacement for every warehouse decision.

### Storage security

Package images are stored in a private Supabase Storage bucket. The current application primarily uses storage for persistence; a production implementation would add fully authenticated image retrieval with authorization checks and signed URLs.

---

# Demo

Live demo:

**https://cube26-pck-0052-ayeshaxsa.vercel.app/**

Repository:

**https://github.com/Cube-Build-A-Thon/cube-03-pack-manager**

Demo video:

**https://drive.google.com/file/d/1F4H0JkwpKJuZE7oNiKrZMAwAdo4gNyAS/view?usp=sharing**

The recommended demo flow is:

```text
Correct package
      ↓
SEAL

Incorrect package
      ↓
STOP & FIX

Unclear evidence
      ↓
UNCERTAIN / Human Review

Model failure
      ↓
PENDING
```

---

# Design Principle

The core design principle is:

> **AI observes. Deterministic logic verifies. Humans handle uncertainty.**

The goal is not to make the AI sound confident.

The goal is to make the packing decision **traceable, explainable, and operationally useful**.