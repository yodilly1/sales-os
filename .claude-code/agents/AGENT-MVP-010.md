# AGENT-MVP-010 — `phase3/contract-generation`

**Branch Name:** `phase3/contract-generation`

**Role:** Add contract/agreement generation from Contract Builder templates.

**End Goal:** User can generate SaaS contracts with customer-specific terms.

---

## What Must Work When Done

1. User selects "Contract" as content type
2. User provides customer info and deal terms
3. Backend generates complete SaaS agreement including:
   - Order form with pricing
   - Master agreement terms
   - Data processing addendum reference
   - Signature blocks
4. User downloads contract as Markdown or DOCX
5. All customer details correctly substituted

---

## Source Code to Port

Read and adapt from Contract Builder:

```
C:\Users\leerg\OneDrive\Documents\Contract Builder\Swimm\Vayu Master SaaS Agreement - Swimm.md
C:\Users\leerg\OneDrive\Documents\Contract Builder\Swimm\Exhibit A - Data Processing Agreement.md
```

Key sections to template:
- Order form header (customer name, address, contact)
- Pricing table (year 1, year 2+, services included)
- General terms (12 sections)
- Signature blocks
- DPA exhibit reference

---

## Responsibilities

### Backend - Contract Template
1. Create `backend/app/services/content/templates/contract_template.md`
2. Use Jinja2-style variables for substitution
3. Include all standard sections from your Contract Builder

### Backend - Content Generator
1. Add `ContentType.CONTRACT` to constants
2. Add `_generate_contract()` method to ContentGenerator
3. Accept contract-specific inputs (customer info, pricing, term)
4. Render template with substituted values

### Backend - Models
1. Add `ContractInputs` schema:
   - customer_name, customer_address, customer_contact
   - effective_date, initial_term_months
   - year1_price, year2_price
   - services_included (list)
   - payment_terms

### Frontend
1. Add "Contract" option to content type selector
2. Add contract-specific input form
3. Show contract preview (rendered markdown)
4. Add download as .md and .docx options

---

## Files/Folders to Create/Modify

**New Files:**
- `/backend/app/services/content/templates/contract_template.md`
- `/backend/app/services/content/templates/dpa_template.md`

**Modify:**
- `/backend/app/core/constants.py` - add CONTRACT content type
- `/backend/app/services/content/generator.py` - add contract generation
- `/backend/app/models/content.py` - add ContractInputs schema
- `/frontend/app/content/page.tsx` - add contract form
- `/frontend/components/content/ContentTypeSelector.tsx` - add contract option

---

## Contract Input Schema

```python
class ContractInputs(BaseModel):
    # Customer info
    customer_name: str
    customer_address: Optional[str] = None
    customer_contact_name: str
    customer_contact_email: str

    # Deal terms
    effective_date: Optional[str] = None  # Defaults to blank for manual fill
    initial_term_months: int = 12

    # Pricing
    year1_price: float
    year2_price: float
    payment_terms: str = "Net 30 days from invoice date"

    # Services
    services_included: List[str] = [
        "Platform subscription",
        "Implementation and training",
        "Technical support",
        "Customer Success Manager"
    ]
```

---

## Test Script

```bash
# 1. Start system
docker-compose up --build -d
sleep 15

# 2. Generate contract
curl -X POST http://localhost:8000/api/v1/content/generate \
  -H "Content-Type: application/json" \
  -d '{
    "content_type": "contract",
    "contract_inputs": {
      "customer_name": "Acme Corporation",
      "customer_contact_name": "John Smith",
      "customer_contact_email": "john@acme.com",
      "year1_price": 14400,
      "year2_price": 30000,
      "initial_term_months": 12,
      "services_included": [
        "Platform subscription",
        "Salesforce integration",
        "NetSuite integration",
        "Implementation and training"
      ]
    }
  }'

# 3. Response should include:
# - contract_markdown (full contract text)
# - Has "Acme Corporation" substituted throughout
# - Has pricing table with $14,400 / $30,000

# 4. Verify substitutions worked
# No "{{customer_name}}" or similar placeholders remaining
```

---

## Dependencies

- AGENT-MVP-007 (Phase 2 orchestrator complete)

---

## Acceptance Criteria

- [ ] Contract template created with all standard sections
- [ ] Contract content type added to system
- [ ] Customer info correctly substituted
- [ ] Pricing table populated correctly
- [ ] Services list rendered correctly
- [ ] No placeholder variables in output
- [ ] Frontend has contract generation form
- [ ] Contract preview displays properly
- [ ] Can download as Markdown file
- [ ] Contract follows structure of your existing contracts
