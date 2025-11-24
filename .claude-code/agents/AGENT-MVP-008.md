# AGENT-MVP-008 — `phase3/financial-models`

**Branch Name:** `phase3/financial-models`

**Role:** Port Proposal Builder's financial ROI models into content generation.

**End Goal:** Generated proposals include real financial calculations (DSO, labor savings, ROI, payback).

---

## What Must Work When Done

1. User generates a proposal from `/content` page
2. User provides financial inputs (ARR, current DSO, hours spent, etc.)
3. Backend calculates:
   - Working capital improvement
   - Labor cost savings
   - Revenue leakage prevention
   - ROI multiple
   - Payback period
4. Generated proposal includes financial analysis section
5. Numbers are calculated, not hardcoded

---

## Source Code to Port

Read and adapt from Proposal Builder:

```
C:\Users\leerg\OneDrive\Documents\Proposal Builder\_scripts\generate_proposal.py
C:\Users\leerg\OneDrive\Documents\Proposal Builder\OptiMove_Proposal\index.html (for output format)
```

Key calculations to port:
- **DSO/Working Capital**: `(current_dso - target_dso) * (arr * affected_pct) / 365 * interest_rate`
- **Labor Savings**: `hours_saved_monthly * 12 * hourly_rate`
- **Revenue Leakage**: `(error_rate_current - error_rate_target) * arr`
- **ROI**: `total_savings / contract_cost`
- **Payback**: `contract_cost / (total_savings / 12)`

---

## Responsibilities

### Backend - Financial Models
1. Create `backend/app/services/content/financial_models.py`
2. Implement calculators:
   - `calculate_dso_savings()`
   - `calculate_labor_savings()`
   - `calculate_revenue_leakage_savings()`
   - `calculate_roi()`
   - `calculate_payback_months()`

### Backend - Content Generator
1. Update `backend/app/services/content/generator.py`
2. Accept financial inputs in `ContentGenerationRequest`
3. Call financial calculators for proposal type
4. Include financial summary in generated proposal

### Backend - Models
1. Update `backend/app/models/content.py`
2. Add `FinancialInputs` schema
3. Add `FinancialAnalysis` to proposal output

### Frontend
1. Add financial input fields to content form (for proposals)
2. Display financial analysis in generated proposal
3. Show ROI chart/visualization

---

## Files/Folders to Create/Modify

**New Files:**
- `/backend/app/services/content/financial_models.py`

**Modify:**
- `/backend/app/services/content/generator.py` - integrate financial models
- `/backend/app/models/content.py` - add financial schemas
- `/frontend/app/content/page.tsx` - add financial inputs
- `/frontend/components/content/ContentPreview.tsx` - show financial analysis

---

## Financial Input Schema

```python
class FinancialInputs(BaseModel):
    # Company info
    arr: float  # Annual recurring revenue

    # DSO model
    current_dso: Optional[float] = None  # Current days sales outstanding
    target_dso: Optional[float] = None   # Target DSO
    affected_revenue_pct: Optional[float] = None  # % of revenue affected
    interest_rate: Optional[float] = 0.05  # Cost of capital

    # Labor model
    hours_saved_monthly: Optional[float] = None
    hourly_rate: Optional[float] = 50.0  # Fully loaded hourly rate

    # Revenue leakage model
    current_error_rate: Optional[float] = None  # e.g., 0.01 for 1%
    target_error_rate: Optional[float] = None   # e.g., 0.001 for 0.1%

    # Pricing
    monthly_price: float
    contract_term_months: int = 12
```

---

## Test Script

```bash
# 1. Start system
docker-compose up --build -d
sleep 15

# 2. Generate proposal with financial inputs
curl -X POST http://localhost:8000/api/v1/content/generate \
  -H "Content-Type: application/json" \
  -d '{
    "content_type": "proposal",
    "goal": "Business case for billing automation",
    "product_info": {"name": "Vayu", "description": "Revenue ops platform"},
    "audience": {"role": "CFO", "industry": "SaaS"},
    "financial_inputs": {
      "arr": 50000000,
      "current_dso": 45,
      "target_dso": 30,
      "affected_revenue_pct": 0.20,
      "hours_saved_monthly": 80,
      "hourly_rate": 50,
      "monthly_price": 5000,
      "contract_term_months": 24
    }
  }'

# 3. Response should include:
# - financial_analysis.working_capital_savings
# - financial_analysis.labor_savings
# - financial_analysis.total_annual_savings
# - financial_analysis.roi_multiple
# - financial_analysis.payback_months

# 4. Verify calculations are reasonable
# Working capital: (45-30) * (50M * 0.20) / 365 * 0.05 = ~$41k
# Labor savings: 80 * 12 * 50 = $48k
```

---

## Dependencies

- AGENT-MVP-007 (Phase 2 orchestrator complete)

---

## Acceptance Criteria

- [ ] Financial models calculate correctly
- [ ] Proposal generation accepts financial inputs
- [ ] Generated proposal includes financial analysis section
- [ ] ROI and payback period calculated
- [ ] Numbers change when inputs change (not hardcoded)
- [ ] Frontend has financial input fields
- [ ] Financial analysis displays in proposal preview
- [ ] Works without financial inputs (graceful fallback)
