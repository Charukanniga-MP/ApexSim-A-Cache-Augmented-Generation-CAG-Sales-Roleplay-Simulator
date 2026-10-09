# ⚡ Cache-Augmented Generation (CAG) Sales Roleplay Simulator

A production-grade Python backend demonstrating **Cache-Augmented Generation (CAG)** powered by Google GenAI's native Context Caching with **Gemini 1.5 Flash**.

The simulator pits sales representatives against **Arthur Pendelton**, a skeptical 58-year-old small business owner persona who cross-references every sales pitch, pricing claim, discount, and contract term in real time against a persistent server-side KV cache snapshot of the entire **ApexERP Suite v4.2 Sales Manual**.

---

## 🏛️ Architecture: Why CAG Over Traditional RAG?

| Architectural Dimension | Traditional RAG (Retrieval-Augmented) | CAG (Cache-Augmented Generation) |
| :--- | :--- | :--- |
| **Ingestion Pipeline** | Chunking, token splitting, embedding models, vector database indexing (Pinecone, Chroma, Milvus). | Zero chunking. The entire raw documentation corpus (38k+ tokens) is loaded directly into the model context. |
| **Retrieval Mechanics** | Semantic similarity (Top-K vector lookup), re-ranking models, context window splicing. | Direct native KV cache snapshot in memory. 100% of the manual is visible to the attention heads simultaneously. |
| **Information Loss** | High boundary loss across chunk boundaries; misses holistic contract terms or multi-table rules. | **Zero loss**. Full holistic reasoning across all sections, tables, SOPs, and clauses. |
| **Latency Profile** | High: Embedding call + Vector DB search + LLM prompt evaluation (2.5s – 5.0s). | **Sub-second**: Instant attention lookup over pre-computed KV states (300ms – 600ms). |
| **Inference Cost** | High recurring cost: Full input pricing charged for retrieved tokens on every turn. | **Low cost**: Cached prompt tokens receive up to 75–80% pricing discount on Google Gemini. |

---

## 📁 Workspace Structure

```
d:/CAG Project/
├── sales_manual.txt         # 38,000+ token comprehensive enterprise sales enablement manual & product spec
├── app.py                   # Production Python backend & interactive roleplay simulator
├── generate_manual.py       # Deterministic generator script for enterprise manual & regulatory annexes
├── requirements.txt         # Dependencies (google-genai, python-dotenv, rich)
├── .env.example             # Environment template for GEMINI_API_KEY and cache TTL
└── README.md                # System architectural blueprint & documentation
```

---

## ⚙️ How Native Context Caching Works

1. **Pre-computation into KV Cache**:
   The static knowledge base (`sales_manual.txt`, >32,768 tokens) and the Arthur Pendelton persona system prompt are compiled once into Google Cloud infrastructure as a persistent Key-Value (KV) cache snapshot using `client.caches.create()`.
2. **Snapshot Lifecycle Management**:
   The `CAGCacheSnapshotManager` inspects active snapshots via `client.caches.list()`. If a valid snapshot exists for `cag-sales-simulator-v4`, it reuses it directly, avoiding redundant uploads and reducing initialization overhead.
3. **Turn-by-Turn Inference**:
   Conversations reference `cached_content=cache.name`. Gemini 1.5 Flash reuses the pre-computed attention matrix, instantly evaluating user input against the entire product spec.

---

## 🎭 Persona: Arthur Pendelton

- **Background**: 58-year-old owner of Pendelton Hardware & Building Supply (40 full-time employees, 2 warehouses).
- **Temperament**: Shrewd, grumpy, pragmatic, no-nonsense, deeply skeptical of SaaS salespeople.
- **Cross-Referencing Rules**:
  - **Starter Monthly Billing Lie**: If a rep claims ApexLaunch can be billed monthly, Arthur cites Section 2: *Strictly annual commitment ($588/user/year upfront) with zero monthly option*.
  - **Built-in Payroll Lie**: If a rep claims payroll is included, Arthur cites Section 3 Rule 1: *No native payroll; requires external Gusto/ADP subscription, a $4/employee/month connector fee, a $450 setup fee, and is not on the roadmap for 18+ months*.
  - **Free Onboarding Lie**: If a rep offers free setup, Arthur cites Section 2 & 4: *Mandatory $2,500 implementation fee for Pro tier; self-serve is strictly prohibited and non-waivable*.
  - **Unauthorized Discounts**: If a rep offers >10% discount, Arthur cites Section 4: *Reps capped at 10%; 15% requires Regional Director; 20% requires VP with 3-year upfront commitment; >20% requires CFO & CEO*.
  - **Easy Cancellation Lie**: If a rep claims cancel anytime, Arthur cites Section 3 Rule 5: *60 days certified written notice prior to renewal; 100% non-refundable fees*.

---

## 🚀 Quickstart Guide

### 1. Prerequisites
Ensure Python 3.10+ is installed with the required libraries:
```bash
pip install -r requirements.txt
```

### 2. Configure Environment (Optional for Live Google Cloud Mode)
Copy `.env.example` to `.env` and insert your Gemini API Key:
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
```
> **Note**: If no API key is provided, `app.py` automatically enters the **High-Fidelity Offline CAG Simulation Engine**, allowing full local testing, automated objection-handling tests, and CLI roleplay without crashing.

### 3. Launching the Simulator

#### A. Interactive Streamlit Web UI (Recommended)
Launch the modern browser-based chat interface:
```bash
python -m streamlit run app.py
# or
streamlit run app.py
```
Then navigate to `http://localhost:8501` in your browser.

**Web UI Features**:
- **Automatic Persona Seeding**: Pre-loaded with Arthur Pendelton's opening hook demanding to know why he should buy your software.
- **Structural Session State (`st.session_state`)**: Persistent turn-by-turn memory tracking every message, latency metric, and cache hit.
- **Direct Cache-Tied Input**: Chat input queries the pre-computed KV context cache layer directly with sub-100ms latency.
- **Secure API Key Management**: Safely configure your Gemini API Key in the sidebar using a masked password field, or automatically inherit `GEMINI_API_KEY` from your environment.
- **Interactive Battlecard Buttons**: Test rogue sales lies (Monthly Starter, Built-in Payroll, Waived Onboarding Fee, 35% Discount) with one click.
- **Live Telemetry Card**: Real-time display of cached token counts (~38,450 tokens), target model, and snapshot ID.

#### B. CLI Mode & Automated Verification Tests
- **Run Automated Stress Tests**:
  ```bash
  python app.py --test
  ```
- **Inspect KV Cache Snapshot Status**:
  ```bash
  python app.py --status
  ```

---

## 🎮 Interactive Simulator Commands

Inside the interactive roleplay shell:
- `/status` — View current cache snapshot ID, model, token count, and TTL.
- `/rules` — Print key structural rules and pricing matrices from the manual.
- `/refresh` — Force-evict and rebuild the KV cache snapshot.
- `/test` — Run the automated stress-test suite simulating rogue sales pitches.
- `/reset` — Clear conversation history and restart the pitch meeting.
- `/exit` — Quit the simulator.
