# Pack Manager — System Architecture

## 1. System Architecture

Pack Manager uses a layered architecture that separates the user interface, API orchestration, AI perception, deterministic verification, persistence, and storage.

```text
                         ┌──────────────────────┐
                         │    React Frontend    │
                         │                      │
                         │ Order Input          │
                         │ Image Upload         │
                         │ Verification Result  │
                         └──────────┬───────────┘
                                    │
                              HTTP / Multipart
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │     FastAPI API      │
                         │                      │
                         │ Request validation   │
                         │ Capture creation     │
                         │ Workflow orchestration│
                         └──────┬───────┬───────┘
                                │       │
                    ┌───────────┘       └──────────────┐
                    ▼                                  ▼
          ┌───────────────────┐              ┌──────────────────┐
          │ PostgreSQL        │              │ Supabase Storage │
          │                   │              │                  │
          │ Organizations     │              │ Private package  │
          │ Products          │              │ images           │
          │ Captures          │              └──────────────────┘
          │ Results           │
          └─────────┬─────────┘
                    │
                    │ Catalogue
                    ▼
          ┌───────────────────────┐
          │    Vision Layer       │
          │                       │
          │ OpenAI Vision Model   │
          │ Catalogue-aware prompt│
          └───────────┬───────────┘
                      │
               Structured observations
                      │
                      ▼
          ┌───────────────────────┐
          │ Deterministic         │
          │ Verification Engine   │
          │                       │
          │ Expected vs Observed  │
          │ SKU + quantity checks │
          └───────────┬───────────┘
                      │
                      ▼
          ┌───────────────────────┐
          │ Operational Decision  │
          │                       │
          │ SEAL                  │
          │ STOP & FIX            │
          │ PENDING               │
          └───────────────────────┘
```

---

# 2. Components

## React Frontend

The frontend provides the operator interface.

Responsibilities:

* Select organization
* Enter order information
* Upload package image
* Submit verification
* Display verification status
* Display item-level checks
* Display visual evidence
* Surface uncertainty and pending states

The frontend does not perform the authoritative verification logic.

---

## FastAPI Backend

FastAPI is the main application orchestration layer.

Responsibilities:

* Receive multipart verification requests
* Persist the package capture
* Load the organization's catalogue
* Call the vision service
* Run deterministic verification
* Persist the verification result
* Return structured results to the frontend
* Handle model failures using the pending state

Main endpoint:

```text
POST /verify
```

Health endpoint:

```text
GET /health
```

---

## PostgreSQL

PostgreSQL stores application state.

Main tables:

```text
organizations
products
pack_captures
verification_results
```

### organizations

Represents a tenant.

```text
id
name
created_at
```

### products

Contains organization-specific catalogue information.

```text
id
org_id
sku
name
description
visual_attributes
reference_image_url
created_at
```

### pack_captures

Records that a package image was received.

```text
id
org_id
order_id
image_key
status
created_at
```

### verification_results

Stores the output of verification.

```text
id
org_id
capture_id
verdict
result
created_at
```

---

# 3. Tenant Isolation

Tenant isolation is implemented using PostgreSQL Row Level Security.

Each organization receives an organization context:

```text
app.current_org_id
```

Policies restrict rows to the current organization.

Conceptually:

```sql
org_id = current_org_id()
```

The application connects using a restricted database role rather than a superuser.

The system was tested with two demo organizations:

```text
org_demo_alpha
org_demo_bravo
```

The isolation test verifies that data belonging to one organization is not returned when the application is operating under the other organization's context.

This is important because tenant isolation is a security boundary rather than simply a frontend filter.

---

# 4. Image Storage

Package images are stored in a private Supabase Storage bucket.

The object path is organization-scoped:

```text
pack-images/
└── <org_id>/
    └── <unique-image-id>.jpg
```

Example:

```text
pack-images/org_demo_alpha/<uuid>.jpg
```

The API stores the resulting image key alongside the package capture.

The storage bucket is private rather than publicly accessible.

---

# 5. Data Flow

## Step 1 — Package submission

The operator submits:

```text
org_id
order_id
order_lines
package image
```

Example:

```text
TSHIRT-BLK:1;CAP-BLU:1;SOCK-RED:1
```

---

## Step 2 — Capture persistence

The backend first creates a capture record.

This is intentional.

The system should not lose the fact that a package was submitted simply because an external AI service later fails.

---

## Step 3 — Catalogue lookup

The backend loads products belonging to the current organization.

The catalogue contains information such as:

```text
SKU
Product name
Description
Visual attributes
```

The catalogue is authoritative for the current verification context.

---

## Step 4 — Vision analysis

The package image and catalogue context are sent to the vision layer.

The model receives instructions to:

* Identify only products supported by the catalogue
* Report observed quantities
* Provide visual evidence
* Mark ambiguous observations as uncertain
* Avoid inventing SKUs
* Avoid making the final packing decision

The output is structured rather than free-form.

Conceptually:

```json
{
  "items": [
    {
      "sku": "TSHIRT-BLK",
      "quantity": 1,
      "status": "observed",
      "evidence": "Black folded short-sleeve shirt visible in the package."
    }
  ],
  "image_quality": "observed"
}
```

---

# 6. Deterministic Verification

The vision model's output is passed to the verification engine.

The verifier creates two maps:

```text
Expected SKU → Quantity
Observed SKU → Quantity
```

It then compares the union of all SKUs.

For every SKU:

```text
expected_quantity == observed_quantity
```

results in:

```text
PASS
```

Different quantities produce:

```text
FAIL
```

An uncertain observation produces:

```text
UNCERTAIN
```

The verifier also identifies the reason for failures:

```text
Missing item
Unexpected extra item
Quantity mismatch
```

---

# 7. Decision Logic

The final decision is intentionally deterministic.

```text
                 ┌──────────────────┐
                 │ Run item checks  │
                 └────────┬─────────┘
                          │
                 ┌────────▼─────────┐
                 │ Any UNCERTAIN?   │
                 └──────┬─────┬─────┘
                        │Yes  │No
                        ▼     ▼
                 UNCERTAIN   ┌─────────────────┐
                             │ Any FAIL?       │
                             └──────┬────┬──────┘
                                    │Yes │No
                                    ▼    ▼
                              STOP & FIX SEAL
```

Operationally:

```text
UNCERTAIN → STOP & FIX / Human Review
FAIL      → STOP & FIX
PASS      → SEAL
```

The model does not directly choose `SEAL`.

---

# 8. Model / Agent Usage

The current implementation uses a vision model as a **perception component**, not as an autonomous decision-maker.

The model's responsibility is:

```text
Image → Structured observations
```

The application's responsibility is:

```text
Expected order + observations → Verification
```

This separation is deliberate.

A model may be good at recognizing visual information but is not the appropriate source of truth for deterministic business rules such as:

```text
Expected quantity = 2
Observed quantity = 1
```

That comparison belongs in application code.

---

# 9. Batch Model Usage

The system sends the package verification context to the vision model as a single structured verification request.

It does not make separate model calls for:

```text
SKU check
quantity check
missing check
extra check
```

Instead, the visual inspection is performed together and the resulting structured observation is reused by the deterministic verifier.

This reduces unnecessary model calls and keeps the workflow easier to reason about.

---

# 10. Uncertainty Handling

Uncertainty is explicitly represented in the schema.

```text
ObservationStatus:
    observed
    uncertain
```

And:

```text
CheckStatus:
    pass
    fail
    uncertain
```

This prevents the system from converting weak evidence into a false PASS.

For example, if two products are visually indistinguishable from the available image:

```text
Vision
  ↓
UNCERTAIN
  ↓
Verification
  ↓
Human review
```

The system therefore treats uncertainty as information rather than as an error to hide.

---

# 11. Fail-Open Design

External AI services can fail because of:

* Network problems
* Timeouts
* API errors
* Invalid model responses
* Temporary service failures

The backend handles this without losing the package capture.

The workflow is:

```text
Upload
  ↓
Save capture
  ↓
Vision call
  ↓
Failure
  ↓
Save PENDING result
  ↓
Operator review
```

This is preferable to silently dropping the package verification event.

---

# 12. Important Engineering Decisions

## Decision 1 — AI + deterministic verification

Instead of asking the model to make the complete decision, the model is used for perception and application code handles verification.

**Reason:**

* More deterministic
* Easier to test
* Easier to explain
* Easier to identify failure causes

---

## Decision 2 — Catalogue-driven vision

The vision prompt is constructed using the current organization's catalogue.

**Reason:**

The model should not be expected to remember arbitrary internal SKU identifiers.

The catalogue is the authoritative source for the products that can be recognized.

---

## Decision 3 — PostgreSQL RLS

Tenant isolation is enforced at the database layer.

**Reason:**

Frontend filtering is not a security boundary.

Database-level policies provide protection even if application queries are accidentally written too broadly.

---

## Decision 4 — Private image storage

Package images are stored in a private bucket.

**Reason:**

Packing images may contain operational information and should not be publicly accessible by default.

---

## Decision 5 — Capture before model execution

The capture is persisted before the external model call.

**Reason:**

An AI failure should not cause the system to lose the warehouse event.

---

## Decision 6 — Explicit uncertainty

The system supports:

```text
UNCERTAIN
PENDING
```

instead of forcing every case into PASS/FAIL.

**Reason:**

In a physical-world workflow, insufficient visual evidence should trigger review rather than an incorrect automated approval.

---

# 13. Verification Scenarios

The implementation was tested against:

| Scenario                 | Expected behavior     |
| ------------------------ | --------------------- |
| Correct package          | `SEAL`                |
| Missing item             | `STOP & FIX`          |
| Extra item               | `STOP & FIX`          |
| Wrong quantity           | `STOP & FIX`          |
| Multiple identical items | Quantity verification |
| Blurry / uncertain image | `UNCERTAIN` → review  |
| Vision failure           | `PENDING`             |
| Cross-tenant access test | Data isolated         |

---

# 14. Current Limitations

## Vision limitations

Recognition can be affected by:

* Occlusion
* Poor lighting
* Blur
* Similar-looking products
* Camera angle
* Packaging material covering products

## Authentication

The current hackathon demo uses an organization identifier supplied by the application.

A production system should derive tenant identity from an authenticated user/session.

## Human review

Uncertain cases are intentionally not automatically approved.

A production warehouse deployment would need an operator workflow for resolving these cases.

## Image retrieval

The current implementation focuses on secure image persistence and verification. A production system should expose authorized image retrieval through authenticated endpoints and short-lived signed URLs.

---

# 15. Architecture Summary

The central architecture can be summarized as:

```text
PERCEIVE
   │
   │ Vision model
   ▼
OBSERVE
   │
   │ Structured observations
   ▼
VERIFY
   │
   │ Deterministic comparison
   ▼
DECIDE
   │
   ├── SEAL
   ├── STOP & FIX
   └── PENDING / HUMAN REVIEW
```

The design deliberately keeps the AI component responsible for what it is good at — **visual perception** — while keeping the final packing verification **deterministic, explainable, and testable**.
