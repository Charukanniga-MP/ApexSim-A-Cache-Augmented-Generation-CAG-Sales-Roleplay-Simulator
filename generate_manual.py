"""
Enterprise Manual Generator for ApexERP Suite v4.2
Generates a comprehensive 35,000+ token sales manual, regulatory terms,
pricing schedules, objection battlecards, and legal annexes to exceed
the Gemini 1.5 Flash 32,768-token context caching requirement.
"""

import os

HEADER = """================================================================================
CONFIDENTIAL & PROPRIETARY — INTERNAL SALES ENABLEMENT MANUAL & PRODUCT SPEC
COMPANY: APEX CLOUD ENTERPRISE SYSTEMS (ACES)
PRODUCT: ApexERP Suite v4.2
CLASSIFICATION: RESTRICTED — INTERNAL DISTRIBUTION ONLY (DO NOT SHARE WITH PROSPECTS)
VERSION: 2026.4
================================================================================

1. EXECUTIVE SUMMARY & PRODUCT MISSION
ApexERP Suite v4.2 is a cloud-native Enterprise Resource Planning and Operations management platform designed for mid-market supply chain, wholesale, retail distribution, and field service businesses. This document serves as the single source of truth for all sales executives, solution engineers, account executives (AEs), and customer success managers (CSMs). 

All commercial terms, contract structures, discount authorities, technical constraints, and objection-handling scripts outlined herein are legally binding on commercial proposals. No sales representative has the authority to make verbal or written commitments that contradict this manual.

--------------------------------------------------------------------------------
2. COMMERCIAL PRICING TIERS & CONTRACT STRUCTURES
--------------------------------------------------------------------------------

ApexERP Suite is offered under three standardized pricing tiers:

### TIER 1: APEXLAUNCH (STARTER PLAN)
- Target Audience: Small businesses with 1 to 10 users transitioning from spreadsheets or legacy desktop tools.
- Base Pricing: $49 per user / month.
- BILLING CADENCE: STRICTLY BILLED ANNUALLY ($588/user/year upfront).
  *** CRITICAL STRUCTURAL RULE ***: There is NO monthly billing option for the Starter Plan under any circumstances. Sales representatives caught offering or promising month-to-month billing on ApexLaunch will be subject to disciplinary action and commission forfeiture.
- User Limit: Hard ceiling of 10 seats. Organizations requiring an 11th seat MUST upgrade entirely to the ApexGrowth tier.
- Workspaces: Exactly 1 primary workspace included. Multi-entity or multi-subsidiary structures are NOT supported.
- API Access: ZERO API access. Webhooks and REST/GraphQL endpoints are hard-disabled.
- Data Storage: 50 GB pooled company storage. Additional storage: $0.50 per GB per month, billed annually in 50 GB blocks ($300/year per block).
- Support SLA: Standard community portal and asynchronous email support. Response time: Best-effort, guaranteed within 48 business hours. No phone or live chat support.
- Onboarding & Implementation: Self-guided onboarding with standard documentation and video tutorials. Optional Guided Setup package: $950 one-time fee.

### TIER 2: APEXGROWTH (PROFESSIONAL PLAN)
- Target Audience: Growing mid-market businesses with 5 to 50 users requiring workflow automation, custom reporting, and external integrations.
- Base Pricing:
  * Annual Commitment: $129 per user / month (billed annually at $1,548/user/year).
  * Month-to-Month Billing: $159 per user / month (billed monthly, requires 30-day notice for seat adjustments).
- Minimum Seat Requirement: Strictly 5 user seats minimum. Single or 2-seat deployments cannot purchase ApexGrowth.
- Workspaces: Up to 3 separate operational workspaces / subsidiaries included. Additional workspaces: $150/month each.
- API Access: Standard REST and Webhook API included, subject to rate limiting of 100 requests per minute and 50,000 calls per 24-hour cycle.
- Single Sign-On (SSO): NOT included by default. Available as a paid add-on at $50 per user / month (requires full-domain licensing).
- Data Storage: 250 GB pooled company storage. Additional storage: $0.40 per GB per month.
- MANDATORY ONBOARDING FEE: Exactly $2,500 one-time fee.
  *** CRITICAL STRUCTURAL RULE ***: The $2,500 Implementation & Onboarding fee is MANDATORY for all ApexGrowth contracts. Self-serve onboarding is prohibited. This fee covers database staging, master data cleansing (up to 25,000 records), and two 90-minute live administrator training sessions. Representatives CANNOT waive this fee.
- Support SLA: 99.5% uptime SLA. Priority ticket support during business hours (8:00 AM - 8:00 PM EST, Monday through Friday). Response time: within 4 business hours.

### TIER 3: APEXSCALE (ENTERPRISE PLAN)
- Target Audience: Scaled distributors, multi-warehouse logistics firms, and enterprise operations with 25+ users requiring dedicated resources and high availability.
- Base Pricing: $299 per user / month, billed annually ($3,588/user/year). Multi-year contract options available (2-year or 3-year term).
- Minimum Seat Requirement: Strictly 25 user seats minimum.
- Workspaces: Unlimited workspaces, multi-currency ledger, and global consolidation tools included.
- API Access: Dedicated high-throughput API endpoints with up to 1,000 requests per minute, custom webhooks, and private gRPC streams.
- Single Sign-On (SSO): Included at no additional cost (SAML 2.0, Okta, Azure AD / Microsoft Entra ID, Google Workspace).
- Data Storage: 2 TB high-speed pooled NVMe storage. Additional storage: $0.25 per GB per month.
- MANDATORY ONBOARDING FEE: Exactly $8,000 one-time fee (White-Glove Enterprise Implementation).
  * Covers complete legacy ERP migration, custom ETL pipeline setup, sandbox staging, custom role permissions modeling, and on-site or dedicated remote certification for staff.
- Support SLA: 99.99% uptime guarantee with financial penalty credit. 24/7/365 dedicated telephone and Slack/Teams emergency bridge. Response time: 1 hour for severity-1 outages. Dedicated named Customer Success Manager (CSM).

--------------------------------------------------------------------------------
3. STRUCTURAL TECHNICAL LIMITATIONS & NON-NEGOTIABLE OPERATIONAL RULES
--------------------------------------------------------------------------------

Every sales rep MUST memorize these operational realities. Prospects frequently ask about these areas, and competitor reps will try to trap you:

### RULE 1: ABSOLUTE LACK OF NATIVE PAYROLL
- ApexERP DOES NOT HAVE A NATIVE PAYROLL ENGINE.
- We do NOT calculate state/federal tax withholdings, do NOT issue W-2s or 1099s, and do NOT execute direct deposit disbursements.
- How payroll is actually handled: We require customers to maintain an active external payroll subscription with third-party providers (specifically Gusto, ADP Workforce Now, or Paychex).
- Connector Cost: Integrating with Gusto or ADP requires the "Apex Payroll Sync Connector", which carries an additional recurring charge of $4.00 per employee / month, plus a one-time API provisioning fee of $450.
- ROADMAP TRUTH: Native payroll is NOT on the product roadmap for the next 18 to 24 months. Representatives who claim "native payroll is coming in Q3 or Q4" are committing blatant sales fraud and will be terminated.

### RULE 2: DATA MIGRATION BOUNDARIES
- Sales reps often promise "complete turn-key data migration." The reality is strictly delimited:
- The standard $2,500 Growth implementation fee covers standard CSV/Excel template ingestion for:
  1. Chart of Accounts
  2. Customers & Vendor Master Directory (max 25,000 records)
  3. Product Catalog & Inventory SKU baseline (max 50,000 active SKUs)
  4. Open Accounts Receivable and Accounts Payable balances (summary level only)
- HISTORICAL TRANSACTIONS: We DO NOT migrate historical invoices, closed purchase orders, or detailed historical ledger journals from legacy software (QuickBooks Desktop, Sage, MAS90). Historical records must be archived in the customer's legacy system or migrated via custom Enterprise Statement of Work (SOW) starting at $12,000.

### RULE 3: CUSTOM SCRIPTS & USER CODE EXECUTION
- Unlike Salesforce (Apex/Visualforce) or NetSuite (SuiteScript), ApexERP is a closed multi-tenant SaaS architecture.
- We DO NOT support custom Python, JavaScript, or Lua execution within our application runtime.
- All business logic custom workflows must be built using our no-code visual trigger engine or handled externally via Webhooks and customer-hosted microservices.

### RULE 4: HARDWARE AND BARCODE SCANNING CONSTRAINTS
- ApexERP Warehouse Manager supports standard Zebra, Honeywell, and Datalogic handheld scanners that operate in HID Keyboard Emulation mode (USB or Bluetooth) or running Android 11+ with our Apex Mobile APK.
- We DO NOT support legacy Windows CE or Windows Mobile devices.
- Offline scanning is NOT supported: The warehouse mobile app requires continuous Wi-Fi (802.11ac minimum) or 5G connectivity. If the warehouse loses internet connectivity, pick-and-pack scanning halts immediately.

### RULE 5: AUTO-RENEWAL AND CANCELLATION POLICIES
- All annual contracts automatically renew for a successive 12-month period unless the customer provides written notice of non-renewal via certified email to cancellations@apexcloudsystems.internal at least SIXTY (60) DAYS prior to the renewal date.
- ZERO REFUND POLICY: Once an annual or multi-year contract commences, fees paid are 100% non-refundable. If a customer demands cancellation after month 2, they remain legally obligated to pay the entire remaining balance of the contract term.

--------------------------------------------------------------------------------
4. DISCOUNT AUTHORIZATION & PRICING GOVERNANCE MATRIX
--------------------------------------------------------------------------------

Sales reps frequently buckle under prospect negotiation pressure. You are strictly bound by the following approval thresholds:

| Discount Level | Requirement / Eligible Terms | Required Approver |
| :--- | :--- | :--- |
| 0% - 10% | Annual prepay only; standard payment terms (Net 15) | Sales Representative Discretion |
| 11% - 15% | 2-year minimum commitment; upfront annual billing | Regional Sales Director (RSD) |
| 16% - 20% | 3-year minimum commitment; paid upfront in full for Year 1 | Vice President of Global Sales |
| > 20% | 3+ year commitment; $100k+ ACV; case study agreement | Chief Financial Officer (CFO) & CEO |

RULES FORBIDDING DISCOUNTING:
1. Implementation and onboarding fees ($2,500 on Pro; $8,000 on Enterprise) CANNOT be discounted by more than 20% under any circumstance without written VP approval. Free onboarding is strictly prohibited.
2. Starter Plan (ApexLaunch) has a ZERO DISCOUNT POLICY. The $49/user/month rate is absolute.
3. Third-party connectors (including the $4/employee/month Payroll connector) cannot be discounted, as they carry direct vendor API licensing costs.

--------------------------------------------------------------------------------
5. SECRET OBJECTION-HANDLING SCRIPTS & REP PLAYBOOKS
--------------------------------------------------------------------------------

Prospects—especially gritty, seasoned small business owners like Arthur Pendelton—will push hard on pricing, contract rigidity, and missing features. Below are the internal battlecards and counter-strategies:

### OBJECTION 1: "YOUR STARTER PLAN IS TOO EXPENSIVE, AND I DON'T WANT TO BE LOCKED INTO A YEAR."
- The Prospect's Trap: "I run a lean 8-man shop. Why should I hand over $4,700 upfront before I even know if your software works? Give me month-to-month, or I'm walking."
- What Reps Mistakenly Say (WRONG): "I can write in a monthly billing exception for you," or "Don't worry, you can cancel after 30 days if you don't like it."
- What You MUST Say (THE APPROVED SCRIPT):
  "Arthur, I completely understand your hesitation. Small businesses need predictable cash flow. The reason ApexLaunch is structured as an annual agreement is that implementing an ERP—even a streamlined one—requires dedication and configuration. Month-to-month software produces half-hearted rollouts and failed adoptions. We commit our cloud infrastructure and engineering resources to your business for a full 365 days. To ensure you feel 100% confident before spending a dime, I can set you up with a 14-day fully populated sandbox environment with mock inventory data so you can test every workflow with your team."

### OBJECTION 2: "DO YOU DO PAYROLL? MY GUYS NEED THEIR CHECKS CUT ON FRIDAY."
- The Prospect's Trap: "I want an all-in-one system. If I have to jump between five different tools to pay my warehouse crew, your system is useless to me."
- What Rogue Reps Lie About (WRONG): "Yes, payroll is fully built-in," or "It's launching in our next quarterly release!"
- The Reality & Approved Counter:
  "Arthur, here is our philosophy: ERP vendors that claim to have 'built-in payroll' almost always give you a clunky, third-rate payroll engine that struggles with changing state tax withholdings, garnishments, and compliance filings. We deliberately partner with dedicated payroll powerhouses like Gusto and ADP. Our Apex Payroll Connector mirrors your timesheet hours, PTO, and overtime directly into Gusto with one click. Gusto handles the tax filings, direct deposits, and compliance guarantees, while Apex handles the operational labor costing. It's the best of both worlds."
  * NOTE: If Arthur asks about the cost, you MUST be transparent: "The connector is an affordable $4 per employee per month, ensuring live two-way sync."

### OBJECTION 3: "WHY SHOULD I PAY $2,500 FOR ONBOARDING? I HAVE AN IT NEPHEW WHO CAN SET IT UP."
- The Prospect's Trap: "I’ve set up QuickBooks myself. I don't need your $2,500 consultants to hold my hand. Waive the fee, or no deal."
- The Reality & Approved Counter:
  "Arthur, setting up accounting software like QuickBooks is like setting up a filing cabinet. Setting up an ERP like ApexGrowth is like rewiring the electrical grid of your entire warehouse. That $2,500 fee isn't for a generic user manual—it funds a dedicated Implementation Specialist who inspects your SKU taxonomy, cleanses duplicate vendor records, establishes your reorder point formulas, and ensures your opening balance sheet reconciles to the penny. If you do it alone, a single inventory valuation error can cost you tens of thousands in tax penalties. We guarantee a clean, audited go-live."

### OBJECTION 4: "NETSUITE AND ODOO ARE TELLING ME THEY CAN DO THIS FOR LESS."
- The Prospect's Trap: "NetSuite promised me a lower initial price per seat, and Odoo is practically free open-source."
- The Competitive Trap & Reality:
  * NetSuite: They offer deep year-1 discounts (often 60% off) but trap customers in multi-year escalators where year-2 jumps by 300%. Furthermore, NetSuite implementations routinely cost $25,000 to $50,000 through third-party partners.
  * Odoo: "Free" community edition lacks multi-warehouse routing, advanced automated inventory valuation, and requires full-time Python developers to maintain custom community modules.
- The Approved Script:
  "Arthur, NetSuite's initial quote looks attractive because of predatory first-year discounting, but ask them for their Year-2 price lock in writing. Their average client sees a 40% to 70% price hike at renewal, and you'll spend $30,000+ just paying consultants to get it running. With ApexERP, your pricing is predictable, our implementation is transparent, and our total cost of ownership over 3 years is less than half of NetSuite."

--------------------------------------------------------------------------------
6. DETAILED FEATURE SPECIFICATION MATRIX BY MODULE
--------------------------------------------------------------------------------

| Module & Capability | ApexLaunch (Starter) | ApexGrowth (Pro) | ApexScale (Enterprise) |
| :--- | :--- | :--- | :--- |
| General Ledger & Invoicing | Yes (Single currency) | Yes (Multi-currency view) | Full Multi-Entity Consolidation |
| Inventory Tracking (FIFO/LIFO/Avg) | Average Cost only | FIFO, LIFO, Weighted Avg | Lot & Serial Tracking, Matrix SKUs |
| Warehouse Bins & Locations | Up to 10 bin locations | Up to 100 locations | Unlimited Locations & Cross-Docking |
| Native Payroll Processing | NO (Requires Connector) | NO (Requires Connector) | NO (Requires Connector) |
| Payroll Connector Fee | $4/emp/mo + $450 setup | $4/emp/mo + $450 setup | Included in custom tier |
| Purchase Orders & Vendor Portal | Basic PO generation | Vendor portal included | Automated EDI 850/855/856/810 |
| REST API & Webhooks | Hard Disabled | 100 req/min | 1,000 req/min + Webhooks |
| Single Sign-On (SAML/Okta) | Disabled | $50/user/mo add-on | Included |
| Implementation / Onboarding | Optional $950 | Mandatory $2,500 | Mandatory $8,000 |
| Contract Commitment | 1 Year Minimum Upfront | 1 Year or Month-to-Month | 1, 2, or 3 Years Upfront |
| Cancellation Notice Period | 60 days before renewal | 60 days before renewal | 60 days before renewal |
| Refund Policy | 100% Non-refundable | 100% Non-refundable | 100% Non-refundable |

--------------------------------------------------------------------------------
7. AUDIT TRAIL, COMPLIANCE, AND SECURITY SPECIFICATIONS
--------------------------------------------------------------------------------
- SOC 2 Type II: Compliant across all tiers. Reports available under NDA only.
- HIPAA Compliance: Only supported on ApexScale (Enterprise) with signed Business Associate Agreement (BAA) and dedicated single-tenant VPC encryption.
- Disaster Recovery: RPO (Recovery Point Objective) = 15 minutes; RTO (Recovery Time Objective) = 2 hours for Enterprise; RTO = 24 hours for Starter/Growth.
- Primary Data Centers: Google Cloud Platform (us-central1, us-east4) with redundant multi-region snapshot storage.
"""

def generate_full_manual():
    output_path = os.path.join(os.path.dirname(__file__), "sales_manual.txt")
    
    sections = [HEADER]
    
    # Section 8: Master Services Agreement Clauses
    sections.append("\n--------------------------------------------------------------------------------")
    sections.append("8. MASTER SERVICES AGREEMENT (MSA) STANDARD LEGAL CLAUSES & CONTRACT TERMS")
    sections.append("--------------------------------------------------------------------------------\n")
    for i in range(1, 41):
        sections.append(f"""### CLAUSE {i:02d}: SECTION 8.{i} — STANDARD CONTRACTUAL STIPULATION
8.{i}.1 Term and Binding Commitment:
Each subscription under this Agreement shall commence on the Effective Date set forth in the Order Form and shall continue for the initial term of twelve (12) calendar months (the "Initial Term"). In no event shall customer have the right to terminate early for convenience without accelerating all unpaid monthly subscription fees for the remainder of the Initial Term as liquidated damages.

8.{i}.2 Payment Terms and Remittance Protocol:
Fees are strictly invoiced upfront in accordance with the billing frequency specified in the Order Form. All invoices are due Net fifteen (15) days from the date of invoice. Late payments shall incur finance charges at the rate of one and one-half percent (1.5%) per month or the highest rate permitted by applicable law, whichever is lower, calculated daily from the due date until paid in full. Customer shall reimburse Apex Cloud Enterprise Systems for all reasonable costs incurred in collecting past-due amounts, including legal counsel fees.

8.{i}.3 Data Ownership and Confidentiality Obligations:
Customer retains all right, title, and interest in and to Customer Data uploaded into ApexERP Suite v4.2. Apex Cloud Enterprise Systems shall hold all Customer Data in strict confidence, implementing administrative, physical, and technical safeguards compliant with NIST SP 800-53 Rev. 5 and SOC 2 Type II Trust Services Criteria. Under no circumstances shall Customer Data be transferred, sold, or shared with unauthorized commercial third parties.

8.{i}.4 Warranty Disclaimer and Limitation of Consequential Damages:
EXCEPT AS EXPRESSLY SET FORTH HEREIN, APEX CLOUD ENTERPRISE SYSTEMS DISCLAIMS ALL WARRANTIES, WHETHER STATUTORY, EXPRESS, OR IMPLIED, INCLUDING ANY IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, OR NON-INFRINGEMENT. IN NO EVENT SHALL APEX'S TOTAL AGGREGATE LIABILITY ARISING OUT OF OR RELATED TO THIS AGREEMENT EXCEED THE TOTAL FEES ACTUALLY PAID BY CUSTOMER HEREUNDER IN THE TWELVE (12) MONTHS PRECEDING THE CLAIM.
""")

    # Section 9: Detailed Warehouse and Supply Chain SOPs
    sections.append("\n--------------------------------------------------------------------------------")
    sections.append("9. STANDARD OPERATING PROCEDURES (SOPS) & SUPPLY CHAIN AUDIT DIRECTIVES")
    sections.append("--------------------------------------------------------------------------------\n")
    for i in range(1, 35):
        sections.append(f"""### SOP-{i:03d}: WAREHOUSE INVENTORY AUDIT PROTOCOL & BIN CONTROL {i}
Purpose:
To standardize physical stock counts, cycle counts, cross-docking schedules, and SKU reconciliations across multi-location distribution facilities utilizing ApexERP Suite Warehouse Management System.

Detailed Procedure:
1. Every physical storage bin location must be registered with a unique 12-character Code 128 barcode containing Zone, Aisle, Shelf, and Bin designators (e.g., Z01-A04-S02-B18).
2. Warehouse personnel must utilize authorized ruggedized scanners configured to HID Keyboard Emulation mode running Android 11 or higher. No Bluetooth tethering to unmanaged personal devices is permitted.
3. Cycle counts must be initiated daily at 06:00 EST and completed prior to receiving dock openings at 08:00 EST. Variances exceeding $250.00 in calculated value must trigger an automated escalation event to the Logistics Supervisor.
4. Goods Receipt Validation: Upon receipt of Bill of Lading (BOL) and Advance Shipping Notice (ASN), receiving clerks must inspect container seals, scan purchase order barcode, and verify received item quantity against PO line items. Discrepancies must be quarantined in the Inspection Holding Bin (HOLD-INSPECT-01).
5. Picking and Put-Away Optimization: ApexERP dynamically sequences wave picks based on bin distance travel algorithms (Travelling Salesperson heuristic). Pickers are directed along single-direction aisles to avoid warehouse aisle congestion.
""")

    # Section 10: Technical API Reference and Integration Architecture
    sections.append("\n--------------------------------------------------------------------------------")
    sections.append("10. TECHNICAL API INTEGRATION SPECIFICATIONS & SCHEMA DICTIONARY")
    sections.append("--------------------------------------------------------------------------------\n")
    for i in range(1, 35):
        sections.append(f"""### ENDPOINT SPECIFICATION /api/v4/integration/service_{i:02d}
Route: POST /api/v4/integration/service_{i:02d}/execute
Supported Plans: ApexGrowth (subject to 100 req/min rate limit), ApexScale (up to 1,000 req/min). HARD-DISABLED ON APEXLAUNCH.

Authentication:
Authorization: Bearer <JWT_TOKEN_SECRET>
Header: X-Apex-Workspace-Id: <UUIDv4>

Request Payload Schema:
{{
  "transaction_id": "tx_{i:04d}_abcdef123456",
  "source_system": "ERP_LEGACY_GATEWAY",
  "execution_timestamp": "2026-10-09T11:00:00Z",
  "payload": {{
    "entity_type": "PURCHASE_ORDER_RECORD",
    "batch_size": 250,
    "validation_ruleset": "STRICT_SOX_AUDIT",
    "idempotency_key": "idemp_{i:05d}_hash"
  }}
}}

Response Status Codes:
- 200 OK: Transaction processed and committed to PostgreSQL primary ledger.
- 400 Bad Request: Schema validation failure or missing mandatory header.
- 402 Payment Required: Organization is on ApexLaunch Starter Plan (API access disabled) or overage threshold breached.
- 429 Too Many Requests: Rate limit exceeded. Retry-After header provided in seconds.
- 500 Internal Server Error: Database transaction lock timeout; retry with exponential backoff.
""")

    # Section 11: Enterprise Compliance, SOC 2, HIPAA, and Tax Schedules
    sections.append("\n--------------------------------------------------------------------------------")
    sections.append("11. REGULATORY COMPLIANCE, 50-STATE SALES TAX SCHEDULES, AND AUDIT MANDATES")
    sections.append("--------------------------------------------------------------------------------\n")
    for i in range(1, 35):
        sections.append(f"""### COMPLIANCE SCHEDULE CS-{i:03d}: STATE JURISDICTION TAX ENGINE INTEGRATION
Overview:
ApexERP Suite v4.2 does not provide a native sales tax rate calculation engine for complex municipal special taxing districts. To achieve economic nexus compliance under the South Dakota v. Wayfair precedent, customers must license the Avalara AvaTax or Vertex Cloud connector.

Specific Regulatory Mandates:
1. Connector Licensing: Avalara integration is available as a premium add-on at $1,200/year plus $0.15 per calculated transaction line.
2. Tax Exemption Certificates: Certificate management is restricted to the ApexGrowth and ApexScale tiers. ApexLaunch accounts cannot store digital exemption certificates; exemptions must be recorded manually on each invoice.
3. Audit Log Retention: In compliance with IRS Publication 583 and Sarbanes-Oxley Section 404, all transactional journals, credit memos, tax overrides, and voided orders are immutably archived for a mandatory minimum period of seven (7) years in WORM (Write Once, Read Many) cloud storage.
""")

    full_text = "\n".join(sections)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_text)
    print(f"Generated {output_path} successfully!")
    print(f"Total Words: {len(full_text.split())}, Total Characters: {len(full_text)}")

if __name__ == "__main__":
    generate_full_manual()
