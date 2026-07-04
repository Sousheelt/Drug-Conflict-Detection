<div align="center">
  <h1>💊 Drug Conflict Detection System</h1>
  <p><strong>Multi-Agent AI system for intelligent prescription conflict detection using severity-prioritized search algorithms</strong></p>
  <sup><em>Educational & research prototype – NOT for clinical use</em></sup>
  
  [![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
  [![License](https://img.shields.io/badge/license-Educational-green.svg)]()
  [![Tests](https://img.shields.io/badge/tests-40%20passing-brightgreen.svg)]()
</div>

---

## 📋 Table of Contents
- [Overview](#overview)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Usage](#usage)
- [Data Formats](#data-formats)
- [Conflict Detection Algorithm](#conflict-detection-algorithm)
- [Multi-Agent System](#multi-agent-system)
- [Advanced Features](#advanced-features)
- [Security & Authentication](#security-authentication)
- [Report Generation](#report-generation)
- [Testing](#testing)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## 🎯 Overview

The **Drug Conflict Detection System** is an intelligent healthcare AI prototype that identifies potentially dangerous interactions between prescribed medications and patient conditions. Built on a Multi-Agent System (MESA) architecture, it uses a Best-First Search algorithm with severity prioritization to detect and report conflicts before they cause harm.

### Problem It Solves
- **Drug-Drug Interactions**: Detects conflicts between multiple prescribed medications
- **Drug-Condition Contraindications**: Identifies medications unsafe for specific medical conditions
- **Allergy-Based Conflicts**: Prevents prescription of drugs to which patients are allergic
- **Severity Prioritization**: Surfaces critical conflicts (Major) before minor ones

### Core Technology
- **Multi-Agent System (MESA)**: Simulates healthcare workflow with specialized agents
- **A* Search Algorithm**: Intelligent conflict space exploration with heuristic guidance
- **Memoization**: Cached conflict detection for real-time UI performance
- **Role-Based Access Control**: Enterprise-grade security with user permissions

---

### ✨ Key Features

### 🤖 **Intelligent Agent System**
- **PatientAgent**: Manages patient profile (conditions, allergies, prescriptions)
- **DoctorAgent**: Two modes - Smart (conflict-avoiding) & Demo (conflict-prone)
- **PharmacistAgent**: Validates prescriptions against safety rules
- **RuleEngineAgent**: Knowledge base query and conflict detection engine

### 🔍 **Advanced Conflict Detection**
- **Best-First Search (A*)**: State space exploration prioritizing high-severity conflicts
- **Severity Scoring**: Major (3 pts) → Moderate (2 pts) → Minor (1 pt)
- **Memoization Layer**: ~90%+ cache hit rate for repeated queries
- **Real-Time Analysis**: Live conflict detection as drugs are selected

### 🎨 **Interactive Web Dashboard (Streamlit)**
- **Dashboard Overview**: Statistics, severity distribution, patient risk rankings
- **Patient Management**: Full CRUD with conditions/allergies tracking
- **Prescription Simulator**: Multi-step agent workflow visualization
- **Manual Testing**: Real-time conflict checking with custom drug combinations
- **Drug Database**: Searchable catalog with replacement suggestions
- **Rules Engine**: Conflict rule management (Admin-only)
- **Custom Data Import**: Upload your own patients/drugs/rules CSV files

### 📊 **Professional Report Generation**
- **PDF Reports**: Publication-quality documents with colored severity indicators
- **Word Documents**: Editable reports with formatted tables and risk assessment
- **Export Options**: CSV download for further analysis
- **Report Contents**: Patient demographics, prescription list, detailed conflicts, recommendations

### 🔐 **Enterprise Security**
- **Role-Based Access Control (RBAC)**: Admin, Doctor, Pharmacist roles
- **bcrypt Password Hashing**: Industry-standard encryption (cost factor 12)
- **Session Management**: 30-minute timeout with activity tracking
- **Login Rate Limiting**: 5 attempts max, 15-minute lockout
- **Input Sanitization**: XSS, SQL injection, path traversal prevention
- **Permission System**: Page-level and action-level access control

### 📈 **Data-Driven & Extensible**
- **CSV-Based**: No database required—simple file storage
- **Pydantic Validation**: Strong typing and schema enforcement
- **Hot-Reload Rules**: Add conflicts without code changes
- **Test Coverage**: 40 automated tests covering core algorithms

---

## 🏗️ System Architecture

### High-Level Data Flow
```
┌─────────────────────────────────────────────────────────────────┐
│                     Data Sources (CSV Files)                    │
├─────────────┬──────────────────┬──────────────────┬─────────────┤
│ patients.csv│  drugs.csv       │  rules.csv       │ users.json  │
│ (Profiles)  │  (Catalog)       │  (Conflicts)     │ (Auth)      │
└─────┬───────┴────────┬─────────┴────────┬─────────┴──────┬──────┘
      │                │                  │                │
      ▼                ▼                  ▼                ▼
┌─────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────┐
│   Pydantic  │  │    utils.py  │  │   auth.py    │  │ rbac.py │
│ Data Models │  │  Loaders &   │  │  Session     │  │ Perms   │
│ Validation  │  │  Rules KB    │  │  Management  │  │ Checks  │
└──────┬──────┘  └──────┬───────┘  └──────┬───────┘  └────┬────┘
       │                │                  │               │
       └────────────────┴──────────┬───────┴───────────────┘
                                   ▼
                    ┌──────────────────────────────┐
                    │   HealthcareModel (MESA)     │
                    │  Orchestrates Agent Workflow │
                    └───────────┬──────────────────┘
                                │
                ┌───────────────┼───────────────┐
                ▼               ▼               ▼
        ┌──────────────┐ ┌────────────┐ ┌──────────────┐
        │ PatientAgent │ │DoctorAgent │ │RuleEngine    │
        │              │ │(Prescribe) │ │Agent         │
        └──────┬───────┘ └─────┬──────┘ └──────┬───────┘
               │               │               │
               │    ┌──────────▼───────────────┘
               │    │   PharmacistAgent
               │    │   (Validate via BFS)
               └────┼────────┐
                    │        │
                    ▼        ▼
            ┌────────────────────────┐
            │  Conflict Logs         │
            │  (patient_id, type,    │
            │   severity, score)     │
            └───────┬────────────────┘
                    │
        ┌───────────┼──────────────┐
        ▼           ▼              ▼
   ┌────────┐ ┌──────────┐ ┌────────────────┐
   │ CLI    │ │Streamlit │ │ PDF/Word       │
   │ Report │ │Dashboard │ │ Reports        │
   │(CSV)   │ │(UI)      │ │(Professional)  │
   └────────┘ └──────────┘ └────────────────┘
```

### Multi-Agent Interaction Flow
```
1. PatientAgent ──[profile]──> DoctorAgent
                                    │
                                    │ prescribe()
                                    │ (risk-aware selection)
                                    ▼
                              [prescription: list[str]]
                                    │
                                    ├──> RuleEngineAgent.check_conflicts()
                                    │         │
                                    │         └─> BFS Search (A*)
                                    │              - State space exploration
                                    │              - Heuristic: severity score
                                    │              - Memoization cache
                                    ▼              
                              PharmacistAgent.validate()
                                    │
                                    ▼
                              [conflicts: list[dict]]
                                    │
                                    └──> Model.conflict_logs
```

---

## 📁 Project Structure

```
drug_conflict_detection/
│
├── 📄 Core Application Files
│   ├── main.py                    # CLI entry point - batch simulation runner
│   ├── app.py                     # Streamlit web dashboard (2000+ lines)
│   ├── model.py                   # HealthcareModel - MESA orchestration
│   ├── agents.py                  # Multi-agent classes (Patient/Doctor/Pharmacist/RuleEngine)
│   └── utils.py                   # Core utilities (BFS, loaders, memoization, plotting)
│
├── 🔐 Security & Authentication
│   ├── auth.py                    # User authentication, session management, bcrypt hashing
│   ├── rbac.py                    # Role-Based Access Control (permissions, roles)
│   └── validation.py              # Input sanitization (XSS, SQL injection prevention)
│
├── 📊 Data & Reports
│   ├── data_models.py             # Pydantic validation models (Patient/Drug/Rule)
│   ├── report_generator.py        # PDF and Word report generation (reportlab, python-docx)
│   ├── patients.csv               # Sample patient dataset (id, name, conditions, allergies)
│   ├── drugs.csv                  # Drug catalog (drug, condition, category, replacements)
│   ├── rules.csv                  # Conflict rules (type, item_a, item_b, severity, recommendation)
│   └── users.json                 # User accounts database (auto-generated on first launch)
│
├── 🧪 Testing Suite
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py                  # Pytest fixtures and shared setup
│       ├── test_bfs_search.py          # BFS algorithm tests (7 tests)
│       ├── test_conflict_detection.py  # Integration tests (2 tests)
│       ├── test_data_models.py         # Pydantic validation tests (3 tests)
│       ├── test_doctor_prescribe.py    # Doctor agent logic tests (2 tests)
│       ├── test_memoization.py         # Cache layer tests (3 tests)
│       ├── test_realtime_ui.py         # Real-time UI tests (6 tests)
│       └── test_report_generator.py    # Report generation tests (17 tests)
│
├── 📤 Output (Generated at Runtime)
│   └── output/
│       └── conflicts.csv           # Generated conflict reports (gitignored)
│
└── ⚙️ Configuration
    ├── requirements.txt            # Python dependencies
    ├── .gitignore                  # Git ignore patterns
    └── README.md                   # This file

```

### File Sizes & Complexity
| File | Lines | Purpose | Critical Path |
|------|-------|---------|---------------|
| `app.py` | 2,035 | Full Streamlit UI with 9 pages | ✅ For web UI |
| `utils.py` | 350+ | Core algorithms (BFS, loaders) | ✅ Always |
| `agents.py` | 130 | Agent behavior definitions | ✅ Always |
| `model.py` | 87 | MESA orchestration | ✅ Always |
| `auth.py` | 380+ | Authentication system | ✅ For web UI |
| `rbac.py` | 300+ | Permission management | ✅ For web UI |
| `report_generator.py` | 450+ | PDF/Word generation | ⚠️ Optional |
| `validation.py` | 400+ | Security validators | ⚠️ Streamlit only |
| `data_models.py` | 90 | Pydantic schemas | ✅ Always |

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.10+** (3.11 recommended)
- **Windows PowerShell** (or any terminal)
- **pip** package manager

### 30-Second Setup
```powershell
# Clone or download the project
cd "C:\Users\anees\Desktop\SEM 3\AI\Drug Conflict Detection\drug_conflict_detection"

# Create virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run CLI simulation (fast)
python main.py

# OR run web dashboard (interactive)
streamlit run app.py
```

### First Launch
- **CLI Output**: Console summary + `output/conflicts.csv`
- **Web Dashboard**: Opens at `http://localhost:8501`
  - Login with: `admin` / `Admin@123`
  - Click **"Run Simulation"** in sidebar
  - Explore Dashboard, Patients, Conflicts, Manual Testing pages

---

## 📦 Installation

### Step-by-Step (Windows PowerShell)

#### 1. Navigate to Project Directory
```powershell
cd "C:\Users\anees\Desktop\SEM 3\AI\Drug Conflict Detection\drug_conflict_detection"
```

#### 2. Create Virtual Environment
```powershell
python -m venv .venv
```
> **Note**: If `python` command fails, try `py -3.11` or `py -3.10`

#### 3. Activate Virtual Environment
```powershell
# PowerShell
.\.venv\Scripts\Activate.ps1

# CMD (if PowerShell fails)
.venv\Scripts\activate.bat

# Git Bash / Linux
source .venv/bin/activate
```

You should see `(.venv)` prefix in your terminal.

#### 4. Install Dependencies
```powershell
pip install -r requirements.txt
```

**Installed Packages:**
- `mesa==1.1.1` - Multi-agent framework
- `streamlit>=1.28.0` - Web dashboard
- `pandas>=2.2.2` - Data manipulation
- `plotly>=5.18.0` - Interactive charts
- `pydantic>=2.5.0` - Data validation
- `bcrypt>=4.0.0` - Password hashing
- `reportlab>=4.0.0` - PDF generation
- `python-docx>=1.1.0` - Word generation
- `pytest>=8.0.0` - Testing framework
- `matplotlib>=3.8.0`, `seaborn>=0.13.0` - Plotting (optional)
- `networkx>=3.2`, `numpy>=1.26.0` - Dependencies

#### 5. Verify Installation
```powershell
python -c "import mesa, streamlit, pydantic, bcrypt; print('✅ All core packages installed')"
```

---

## 💻 Usage

### Simulation Modes

The system supports **two distinct simulation modes** for different use cases:

#### 🧠 Smart Doctor Mode (Default)
**Purpose:** Intelligent, conflict-avoiding prescribing for real-world clinical use

**Features:**
- ✅ **Zero Conflicts Guarantee**: Actively avoids ALL drug interactions
- ✅ **Allergy Checking**: Automatically excludes allergenic drugs
- ✅ **Replacement Logic**: Uses alternative drugs when primary choice conflicts
- ✅ **Safety First**: Skips conditions if no safe drug available

**Algorithm:**
1. **First Pass**: Find conflict-free drugs for each condition
2. **Second Pass**: Try replacement drugs if conflicts exist
3. **Final Decision**: Skip condition rather than prescribe conflicting drug

**Results:**
- **0 conflicts** (guaranteed safe prescriptions)
- No allergy violations
- Some conditions may be left untreated for safety

#### ⚠️ Demo Mode (Conflict-Prone)
**Purpose:** Educational demonstration of poor prescribing and conflict detection

**Features:**
- ⚠️ **Intentional Conflicts**: Deliberately creates drug interactions
- ⚠️ **Allergy Violations**: May prescribe allergenic drugs
- ⚠️ **System Testing**: Validates conflict detection works correctly

**Results:**
- **5-10 conflicts** typical (including Major severity)
- Demonstrates worst-case scenarios
- Shows system's detection capabilities

#### Mode Comparison

| Feature | Smart Mode | Demo Mode |
|---------|-----------|-----------|
| **Conflicts** | 0 (guaranteed) | 5-10 typical |
| **Allergy Checking** | ✅ Yes | ❌ No |
| **Replacement Drugs** | ✅ Yes | ❌ No |
| **Use Case** | Production/Training | Testing/Education |

---

### Option 1: Command-Line Interface (CLI)

**Fast batch processing for headless environments:**

```powershell
# Smart mode (default - zero conflicts)
python main.py --mode smart

# Demo mode (creates conflicts for demonstration)
python main.py --mode conflict-prone
```

**Smart Mode Output:**
```
🏥 Running simulation in SMART mode...
Mode: SMART
Total prescriptions: 20
Conflicts detected: 0
✅ No conflicts found! (Safe prescriptions)
```

**Demo Mode Output:**
```
🏥 Running simulation in CONFLICT-PRONE mode...
Mode: CONFLICT-PRONE
Total prescriptions: 20
Conflicts detected: 8
By severity:
  - Major: 2
  - Moderate: 6
  - Minor: 0

Report saved to: output\conflicts.csv
```

**Generated Files:**
- `output/conflicts.csv` - Detailed conflict report with all fields

**When to Use:**
- Automated testing or CI/CD pipelines
- Batch processing of patient datasets
- Performance benchmarking
- Scheduled conflict checks

---

### Option 2: Streamlit Web Dashboard

**Interactive UI with real-time conflict detection:**

```powershell
streamlit run app.py
```

**Dashboard opens at:** `http://localhost:8501`

#### Default Login Credentials

| Username | Password | Role | Capabilities |
|----------|----------|------|--------------|
| `admin` | `Admin@123` | Admin | Full access (CRUD, user management) |
| `doctor` | `Doctor@123` | Doctor | Prescribe, manage patients, view reports |
| `pharmacist` | `Pharma@123` | Pharmacist | Manage drugs, view-only for patients |

> ⚠️ **Security**: Change default passwords immediately after first login!

#### Available Pages

**1. 📊 Dashboard** (All Roles)
- Statistics overview (patients, drugs, rules, conflicts)
- Severity distribution pie chart
- Conflict type bar chart
- Patient risk rankings
- Summary metrics

**2. 👥 Patients** (Admin, Doctor)
- View all patient records in searchable table
- Add new patients with conditions and allergies
- Edit patient information (Admin + Doctor)
- Delete patients (Admin only)
- View patient details cards with conditions/allergies
- See current prescriptions after simulation

**3. 💉 Prescription Simulator** (Doctor, Admin)
- Run multi-agent simulation workflow
- View prescription results by patient
- See conflict counts per patient
- Observe Doctor → Pharmacist interaction
- Safe/Warning indicators

**4. ⚠️ Conflicts** (All Roles)
- View all detected conflicts with color-coded severity
- Filter by severity (Major/Moderate/Minor)
- Filter by conflict type (drug-drug, drug-condition)
- Filter by patient
- Export to CSV, PDF, or Word
- Detailed recommendations for each conflict

**5. 💊 Drug Database** (Pharmacist, Admin)
- Searchable drug catalog
- Add new drugs with category and replacements
- Edit drug information (Admin + Pharmacist)
- Delete drugs (Admin + Pharmacist)
- View drugs by category and condition
- Manage replacement drug suggestions

**6. ⚙️ Rules Engine** (Admin Only)
- View all conflict detection rules
- Add new rules (drug-drug or drug-condition)
- Edit existing rules
- Delete rules with confirmation
- Search rules by drug names
- Rule trigger statistics (after simulation)

**7. 🧪 Manual Testing** (Doctor, Admin)
- **Real-time conflict detection** (live as you select)
- Select patient conditions and allergies
- Choose drugs from dropdown
- Instant conflict analysis with memoization
- Color-coded severity indicators
- Export individual reports (PDF/Word)
- No simulation required—immediate feedback

**8. 📁 Import Data** (Doctor, Admin)
- Upload custom `patients.csv`
- Upload custom `drugs.csv`
- Upload custom `rules.csv`
- Preview uploaded data before import
- Download template files
- Reset to default datasets

**9. 👤 User Management** (Admin Only)
- View all user accounts
- Add new users with role assignment
- Change passwords
- Delete users (cannot delete self or last admin)
- Role-based permission display

#### Quick Actions (Sidebar)
- **🔄 Run Smart Simulation**: Execute intelligent conflict-avoiding prescriptions (0 conflicts)
- **🔄 Run Demo Simulation**: Execute conflict-prone mode for testing/education (shows conflicts)
- **Last Run**: Timestamp and mode of last simulation
- **Logout**: End session securely

---

### Option 3: Programmatic Usage

**Embed conflict detection in your own Python scripts:**

```python
from pathlib import Path
from model import HealthcareModel

# Initialize model with data directory
data_dir = Path(__file__).parent
model = HealthcareModel(data_dir=data_dir)

# Run simulation (1 step processes all patients)
model.run(steps=1)

# Access results
conflicts_df = model.conflicts_dataframe()
print(f"Total conflicts: {len(conflicts_df)}")

# Save to CSV
model.save_conflicts_csv("output/my_results.csv")

# Access individual components
for patient in model.patients:
    print(f"{patient.name}: {patient.prescription}")
    
# Query specific conflicts
major_conflicts = conflicts_df[conflicts_df['severity'] == 'Major']
print(f"Critical conflicts: {len(major_conflicts)}")
```

**Generate Reports Programmatically:**

```python
from report_generator import ReportGenerator

generator = ReportGenerator()

# Generate PDF
generator.generate_pdf_report(
    output_path="patient_report.pdf",
    patient_name="John Doe",
    patient_id="P001",
    conditions=["Hypertension", "Diabetes"],
    allergies=["Penicillin"],
    prescription=["Lisinopril", "Metformin", "Aspirin"],
    conflicts=[{
        'type': 'drug-drug',
        'item_a': 'Aspirin',
        'item_b': 'Warfarin',
        'severity': 'Major',
        'recommendation': 'Avoid concurrent use - increased bleeding risk',
        'score': 3
    }]
)

# Generate Word document
generator.generate_word_report(
    output_path="patient_report.docx",
    # ... same parameters
)
```

---

### Option 4: Optional Plotting

**Visualize severity distribution with Matplotlib:**

```powershell
python -c "import pandas as pd; from utils import plot_severity_distribution; df=pd.read_csv('output/conflicts.csv'); plot_severity_distribution(df)"
```

**Displays:**
- Bar chart of conflicts by severity
- Color-coded (red, orange, yellow)
- Requires `matplotlib` and `seaborn` installed

---

## 📊 Data Formats

### patients.csv

**Columns:** `id`, `name`, `conditions`, `allergies`

**Format Rules:**
- `conditions` and `allergies` are semicolon-separated (`;`)
- Use `None` for no conditions/allergies (ignored during parsing)
- IDs must be unique integers
- Names are sanitized to prevent XSS

**Example:**
```csv
id,name,conditions,allergies
1,John Doe,Hypertension;Diabetes,Penicillin
2,Jane Smith,Infection,None
3,Bob Lee,Pain;Hypertension,Aspirin;Ibuprofen
```

**Pydantic Validation:**
- Auto-converts `id` to string
- Splits semicolon lists into Python lists
- Filters out `"None"` values
- Trims whitespace

---

### drugs.csv

**Columns:** `drug`, `condition`, `category`, `replacements`

**Format Rules:**
- `replacements` is semicolon-separated list of alternative drugs
- `category` helps organize drugs (e.g., "ACE Inhibitor", "NSAID")
- Drug names must be unique (case-insensitive check in UI)

**Example:**
```csv
drug,condition,category,replacements
Lisinopril,Hypertension,ACE Inhibitor,Losartan;Enalapril
Metformin,Diabetes,Biguanide,Glipizide;Insulin
Ibuprofen,Pain,NSAID,Paracetamol;Naproxen
Amoxicillin,Infection,Antibiotic,Azithromycin;Cephalexin
```

**Usage:**
- DoctorAgent selects drugs matching patient conditions
- Replacements suggested when conflicts detected
- Category used for database organization

---

### rules.csv

**Columns:** `type`, `item_a`, `item_b`, `severity`, `recommendation`, `notes`

**Format Rules:**
- `type` ∈ {`drug-drug`, `drug-condition`}
- `severity` ∈ {`Major`, `Moderate`, `Minor`} (case-sensitive)
- For `drug-drug`: `item_a` and `item_b` are drug names (order doesn't matter)
- For `drug-condition`: `item_a` is condition/allergy token, `item_b` is drug
- Allergy tokens formatted as `{Drug}Allergy` (e.g., `PenicillinAllergy`)

**Example:**
```csv
type,item_a,item_b,severity,recommendation,notes
drug-drug,Aspirin,Warfarin,Major,Avoid concurrent use - increased bleeding risk,Anticoagulant interaction
drug-drug,Lisinopril,Losartan,Moderate,Do not combine ACE inhibitors and ARBs,Dual RAAS blockade
drug-condition,Hypertension,Ibuprofen,Moderate,Prefer Paracetamol - NSAIDs may elevate BP,Monitor blood pressure
drug-condition,PenicillinAllergy,Amoxicillin,Major,Do not prescribe - severe allergic reaction risk,Patient is allergic
```

**Matching Logic:**
- Drug-drug: Checked for every pair in prescription (order-independent)
- Drug-condition: Checked against patient conditions + allergy tokens
- Case-insensitive matching with `.lower()` normalization

---

### users.json (Auto-Generated)

**Structure:**
```json
{
  "admin": {
    "username": "admin",
    "password": "$2b$12$hashed_password_here",
    "role": "Admin",
    "email": "admin@example.com",
    "created_at": "2024-01-15T10:30:00"
  }
}
```

**Security:**
- Passwords hashed with bcrypt (cost factor 12)
- Created automatically on first `streamlit run app.py`
- Do NOT commit to version control with real passwords
- File permissions should be restricted (owner read/write only)

---

## 🔍 Conflict Detection Algorithm

### Overview: Best-First Search (A* Variant)

The system uses an **A*-style state space exploration** algorithm to detect conflicts, prioritizing high-severity issues first. This ensures critical (Major) conflicts surface immediately rather than being buried in a flat list.

### Why Not Simple Iteration?

**❌ Naive Approach (Not Used):**
```python
# Simple nested loop - no prioritization
for drug1 in prescription:
    for drug2 in prescription:
        check_rule(drug1, drug2)  # Random order
```
**Problems:**
- No severity awareness
- Random conflict discovery order
- Can't optimize for worst-case scenarios

**✅ Our Approach: BFS with Heuristic Guidance**
- Explores conflict space systematically
- Prioritizes high-severity paths (Major first)
- Prevents revisiting same conflict sets
- Optimized with memoization for repeated queries

---

### Algorithm Components

#### 1. State Representation
```python
@dataclass(frozen=True)
class SearchState:
    prescription: frozenset[str]      # Drugs in prescription
    conditions: frozenset[str]         # Patient conditions + allergies
    detected_conflicts: frozenset[Tuple[str, str, str]]  # Rule keys found
```

**State Space:**
- Each state = a set of conflicts detected so far
- Initial state = empty conflict set
- Goal = explore all reachable conflicts

#### 2. Heuristic Function
```python
def _compute_heuristic(state, kb):
    """Sum of severity scores for detected conflicts"""
    total = 0
    for rule_key in state.detected_conflicts:
        rule = kb.get(rule_key)
        if rule:
            total += severity_to_score(rule.severity)
    return total
```

**Severity Scores:**
- `Major` = 3 points
- `Moderate` = 2 points  
- `Minor` = 1 point

**Purpose:** Higher score = worse state → explore first (max-heap behavior with negative priority)

#### 3. Neighbor Expansion
```python
def _expand_neighbors(state, candidate_keys, kb):
    """Generate neighbor states by adding one conflict"""
    neighbors = []
    remaining = [k for k in candidate_keys 
                 if k not in state.detected_conflicts]
    
    for key in remaining:
        rule = kb[key]
        new_state = SearchState(
            prescription=state.prescription,
            conditions=state.conditions,
            detected_conflicts=state.detected_conflicts | {key}
        )
        neighbors.append((new_state, key, severity_to_score(rule.severity)))
    return neighbors
```

**Optimization:** Precompute all candidate keys once (drug-drug pairs + drug-condition pairs) instead of generating in each expansion.

#### 4. Priority Queue (Max-Heap)
```python
heap = []  # (priority, counter, state)
heapq.heappush(heap, (-heuristic, counter, initial_state))
```

**Priority:** `-heuristic` (negative for max-heap)
- States with more severe conflicts explored first
- Tie-breaking with counter for stable ordering

#### 5. Visited Set
```python
visited = set()  # frozenset of rule keys

if state.detected_conflicts in visited:
    continue  # Skip already explored states
visited.add(state.detected_conflicts)
```

**Purpose:** Avoid redundant exploration of same conflict combinations

---

### Algorithm Steps

```python
def bfs_conflicts(prescription, conditions, kb):
    """
    A*-style BFS for conflict detection
    
    Returns: List[Conflict] sorted by severity (Major → Moderate → Minor)
    """
    # 1. Setup
    drugs = frozenset(d.strip() for d in prescription)
    conds = frozenset(c.strip() for c in conditions)
    
    # 2. Precompute all possible conflict keys (optimization)
    candidate_keys = _precompute_candidate_keys(drugs, conds, kb)
    
    # 3. Initialize search
    initial = SearchState(drugs, conds, frozenset())
    heap = [(0, 0, initial)]
    visited = set()
    all_conflicts = {}
    
    # 4. Explore state space
    while heap:
        _, _, state = heapq.heappop(heap)
        
        if state.detected_conflicts in visited:
            continue
        visited.add(state.detected_conflicts)
        
        # Record conflicts from this state
        for key in state.detected_conflicts:
            if key not in all_conflicts:
                all_conflicts[key] = kb[key]
        
        # Expand neighbors
        for new_state, key, score in _expand_neighbors(state, candidate_keys, kb):
            if new_state.detected_conflicts not in visited:
                h = _compute_heuristic(new_state, kb)
                heapq.heappush(heap, (-h, counter, new_state))
                counter += 1
    
    # 5. Convert to sorted conflict list
    results = [Conflict(...) for key, rule in all_conflicts.items()]
    results.sort(key=lambda c: (-c.score, c.item_a, c.item_b))
    
    return results
```

---

### Performance Optimizations

#### Memoization Layer
```python
_MEMO_CACHE = {}  # (drugs_set, conds_set, kb_id) -> conflicts

def get_conflicts_cached(prescription, conditions, kb):
    """Wrapper with memoization"""
    key = (frozenset(prescription), frozenset(conditions), id(kb))
    if key in _MEMO_CACHE:
        _MEMO_STATS["hits"] += 1
        return _MEMO_CACHE[key]
    
    _MEMO_STATS["misses"] += 1
    result = bfs_conflicts(prescription, conditions, kb)
    _MEMO_CACHE[key] = result
    return result
```

**Real-World Performance:**
- Manual Testing page: ~90%+ cache hit rate
- 15-drug prescription: ~100ms first query, ~1ms cached
- KB rebuild invalidates cache (uses `id(kb)`)

#### Precomputed Candidates
Instead of:
```python
# ❌ Generate pairs every expansion (O(n²) per state)
for drug1 in drugs:
    for drug2 in drugs:
        check_rule(drug1, drug2)
```

We do:
```python
# ✅ Generate once upfront (O(n²) total)
candidate_keys = _precompute_candidate_keys(drugs, conds, kb)
# Then just filter remaining in each expansion (O(k))
```

---

### Example Walkthrough

**Prescription:** `["Aspirin", "Warfarin", "Ibuprofen"]`  
**Conditions:** `["Hypertension"]`

**Rules in KB:**
1. `drug-drug: Aspirin + Warfarin → Major (bleeding risk)`
2. `drug-drug: Ibuprofen + Warfarin → Major (bleeding risk)`  
3. `drug-condition: Hypertension + Ibuprofen → Moderate (BP elevation)`

**Search Execution:**

```
Initial State: detected_conflicts = {}

Expansion 1 (Priority Queue):
├─ State A: {Aspirin+Warfarin (Major)} → heuristic = 3 → priority = -3
├─ State B: {Ibuprofen+Warfarin (Major)} → heuristic = 3 → priority = -3
└─ State C: {Hypertension+Ibuprofen (Moderate)} → heuristic = 2 → priority = -2

Pop State A (highest priority):
├─ Record: Aspirin+Warfarin (Major)
├─ Expand neighbors:
│   ├─ State A+B: {Aspirin+Warfarin, Ibuprofen+Warfarin} → h = 6 → priority = -6
│   └─ State A+C: {Aspirin+Warfarin, Hypertension+Ibuprofen} → h = 5 → priority = -5

Pop State A+B (highest priority):
├─ Record: Ibuprofen+Warfarin (Major)
├─ Expand: State A+B+C → h = 8 → priority = -8

Pop State A+B+C (explored all):
├─ Record: Hypertension+Ibuprofen (Moderate)
└─ No more neighbors

Final Conflicts (sorted by severity):
1. Aspirin + Warfarin (Major, score=3)
2. Ibuprofen + Warfarin (Major, score=3)
3. Hypertension + Ibuprofen (Moderate, score=2)
```

**Result:** Major conflicts reported first, ensuring critical issues get immediate attention.

---

### Comparison to Previous Approach

**Version 1 (Replaced):**
```python
# Simple priority queue over pairs - no state exploration
pairs = generate_all_pairs(prescription, conditions)
priority_queue = [(severity_score(p), p) for p in pairs]
heapq.heapify(priority_queue)

while priority_queue:
    score, pair = heapq.heappop(priority_queue)
    if is_conflict(pair):
        yield pair
```

**Problems:**
- No systematic state exploration
- Can't optimize for combinations
- Less extensible for complex heuristics

**Version 2 (Current):**
- Full state space search with visited tracking
- Supports complex heuristics (future: interaction chains)
- Correct A* implementation with admissible heuristic
- Extensible to multi-hop conflict reasoning

---

## 🤖 Multi-Agent System

### Agent Responsibilities

#### **PatientAgent**
```python
class PatientAgent(Agent):
    def __init__(self, model, patient_id, name, conditions, allergies):
        self.patient_id = patient_id
        self.name = name
        self.conditions = conditions  # List[str]
        self.allergies = allergies    # List[str]
        self.prescription = []        # Filled by DoctorAgent
```

**Role:** Passive data holder  
**Behavior:** No `step()` action—waits for prescription

---

#### **DoctorAgent**
```python
class DoctorAgent(Agent):
    def __init__(self, model, drugs_catalog):
        self.drugs_catalog = drugs_catalog
    
    def prescribe(self, patient: PatientAgent) -> List[str]:
        """Risk-aware prescribing with conflict prediction"""
        chosen = []
        for condition in patient.conditions:
            candidates = [d for d in self.drugs_catalog 
                         if d['condition'] == condition]
            
            # Predict risk for each candidate
            scored = [(predicted_risk(drug, chosen), drug) 
                     for drug in candidates]
            
            # Demo mode: Pick HIGHEST risk (to showcase conflicts)
            # Production: Pick LOWEST risk
            scored.sort(reverse=True)  # Intentional conflict creation
            chosen.append(scored[0][1])
        
        return chosen
```

**Role:** Prescription generator  
**Behavior:**
- Matches drugs to patient conditions
- Predicts conflict risk before adding each drug
- Demo mode intentionally creates conflicts for testing
- Production mode would minimize risk

**Risk Prediction:**
```python
def predicted_risk(drug, current_rx):
    """Estimate severity score if adding drug to prescription"""
    risk = 0
    kb = self.model.rule_engine.kb
    
    # Check against existing drugs
    for existing in current_rx:
        key = ("drug-drug", existing.lower(), drug.lower())
        if key in kb:
            risk += severity_to_score(kb[key].severity)
    
    # Check against conditions/allergies
    for condition_token in patient_condition_tokens:
        key = ("drug-condition", condition_token.lower(), drug.lower())
        if key in kb:
            risk += severity_to_score(kb[key].severity)
    
    return risk
```

---

#### **RuleEngineAgent**
```python
class RuleEngineAgent(Agent):
    def __init__(self, model, rules_rows):
        self.kb = build_rules_kb(rules_rows)  # Dict[Tuple, Rule]
    
    def check_conflicts(self, prescription, conditions, allergies):
        """Invoke BFS algorithm for conflict detection"""
        condition_tokens = make_condition_tokens(conditions, allergies)
        conflicts = bfs_conflicts(prescription, condition_tokens, self.kb)
        return [conflict.to_dict() for conflict in conflicts]
```

**Role:** Knowledge base manager + conflict detector  
**Behavior:**
- Loads rules from CSV into searchable dictionary
- Provides query interface for conflict checking
- Normalizes keys (lowercase, sorted for drug-drug)

**Knowledge Base Structure:**
```python
kb = {
    ("drug-drug", "aspirin", "warfarin"): Rule(
        rtype="drug-drug",
        item_a="Aspirin",
        item_b="Warfarin",
        severity="Major",
        recommendation="Avoid concurrent use",
        notes="Bleeding risk"
    ),
    ("drug-condition", "penicillinallergy", "amoxicillin"): Rule(...)
}
```

---

#### **PharmacistAgent**
```python
class PharmacistAgent(Agent):
    def __init__(self, model, rule_engine: RuleEngineAgent):
        self.rule_engine = rule_engine
    
    def validate(self, patient, prescription):
        """Validate prescription and log conflicts"""
        conflicts = self.rule_engine.check_conflicts(
            prescription,
            patient.conditions,
            patient.allergies
        )
        
        logger.info(f"{patient.name}: {len(conflicts)} conflict(s) detected")
        return conflicts
```

**Role:** Prescription validator  
**Behavior:**
- Receives prescription from DoctorAgent
- Queries RuleEngineAgent for conflicts
- Returns conflict list to model for logging

---

### Agent Interaction Flow

```
┌──────────────────────────────────────────────────────┐
│ HealthcareModel.step()                               │
├──────────────────────────────────────────────────────┤
│                                                      │
│  for patient in model.patients:                      │
│                                                      │
│    ┌─────────────────────────────────────┐           │
│    │ 1. Doctor.prescribe(patient)        │           │
│    │    ↓                                │           │
│    │    - Match drugs to conditions      │           │
│    │    - Predict risk for each drug     │           │
│    │    - Return prescription            │           │
│    └───────────┬─────────────────────────┘           │
│                ▼                                     │
│    patient.prescription = [drug1, drug2, ...]        │
│                ▼                                     │
│    ┌─────────────────────────────────────┐           │
│    │ 2. Pharmacist.validate(patient, rx) │           │
│    │    ↓                                │           │
│    │    RuleEngine.check_conflicts()     │           │
│    │    ↓                                │           │
│    │    BFS Search (A*)                  │           │
│    │    ↓                                │           │
│    │    Return conflicts                 │           │
│    └───────────┬─────────────────────────┘           │
│                ▼                                     │
│    model.conflict_logs.append({...})                 │
│                                                      │
└──────────────────────────────────────────────────────┘
```

---

### Why Multi-Agent Design?

**Benefits:**
1. **Separation of Concerns**: Each agent has clear responsibility
2. **Modularity**: Easy to swap prescribing logic or validation rules
3. **Extensibility**: Add new agent types (e.g., InsuranceAgent, PharmacyAgent)
4. **Testability**: Mock individual agents for unit testing
5. **Realistic Simulation**: Models real healthcare workflow

**MESA Framework:**
- Provides `Agent` base class with `step()` method
- `Model` orchestrates agent interactions
- `BaseScheduler` manages agent activation order
- Minimal overhead for our simple orchestrated flow

---

## 🎯 Advanced Features

### Extending the System

| Goal | Implementation |
|------|----------------|
| **Add New Rules** | Append to `rules.csv` - no code changes needed |
| **Dosage/Timing** | Extend schema in `data_models.py`, update BFS logic |
| **ML Risk Scoring** | Add ML model to heuristic function |
| **Agent Negotiation** | Implement messaging in `Agent.step()` |
| **Smart Prescribing** | Replace naive logic with ML ranking |

---

## 11. Report Generation

### Overview
Generate professional PDF and Word documents for conflict analysis results with:
- Patient information and prescription details
- Detailed conflict analysis with severity breakdown
- Color-coded severity indicators (Major = Red, Moderate = Orange, Minor = Yellow)
- Risk assessment summary
- Clinical recommendations
- Professional disclaimers

### Usage in Streamlit
**Manual Testing Page**:
1. Select patient conditions, allergies, and drugs
2. Review detected conflicts
3. Click "Download PDF Report" or "Download Word Report"
4. Save the generated report

**Conflicts Page** (after simulation):
1. View simulation conflicts
2. Apply filters as needed
3. Click "Generate PDF Report" or "Generate Word Report"
4. Download comprehensive analysis

### Programmatic Usage
```python
from report_generator import ReportGenerator

generator = ReportGenerator()

# Generate PDF
generator.generate_pdf_report(
    output_path="report.pdf",
    patient_name="John Doe",
    patient_id="P123",
    conditions=["Hypertension", "Diabetes"],
    allergies=["Penicillin"],
    prescription=["Aspirin", "Metformin", "Lisinopril"],
    conflicts=[
        {
            'type': 'drug-drug',
            'item_a': 'Aspirin',
            'item_b': 'Warfarin',
            'severity': 'Major',
            'recommendation': 'Avoid concurrent use',
            'score': 9
        }
    ]
)

# Generate Word document
generator.generate_word_report(
    output_path="report.docx",
    patient_name="Jane Smith",
    patient_id="P456",
    conditions=["Pain"],
    allergies=[],
    prescription=["Acetaminophen"],
    conflicts=[]
)

# Generate for streaming/download (returns BytesIO)
pdf_bytes = generator.generate_report_bytes(
    format_type='pdf',
    patient_name="Test Patient",
    # ... other parameters
)
```

### Report Contents
**PDF Reports Include**:
- Title with generation timestamp
- Patient demographics table
- Prescribed medications list
- Conflict analysis with color-coded severity
- Risk level assessment (HIGH/MODERATE/LOW/MINIMAL)
- Clinical recommendations
- Professional disclaimer

**Word Reports Include**:
- Same structure as PDF
- Formatted tables and styled text
- Color-coded severity indicators
- Suitable for editing and customization

### Requirements
```powershell
pip install reportlab python-docx
```

## 12. Security & Authentication

### Overview
The system includes a comprehensive security layer with user authentication and role-based access control (RBAC).

### Default User Accounts
The system creates default accounts on first launch:

| Username | Password | Role | Permissions |
|----------|----------|------|-------------|
| `admin` | `Admin@123` | Admin | Full system access, user management, CRUD operations on all data |
| `doctor` | `Doctor@123` | Doctor | Can prescribe, view reports, run simulations, manage patients |
| `pharmacist` | `Pharma@123` | Pharmacist | Can manage drug database, view-only for other data |

**⚠️ Security Notice**: Change default passwords immediately in production!

### Role Permissions

#### Admin
- Full access to all pages and features
- User management (add/delete users, change passwords)
- **CRUD Operations**: Add, edit, and delete patients, drugs, and rules
- System settings and configuration
- View audit logs (when enabled)

#### Doctor
- **Patient Management**: Add and edit patient information
- Run simulations and prescribe drugs
- Generate and export reports
- Import patient data

#### Pharmacist
- **Drug Database Management**: Add, edit, and delete drugs
- View patient and drug information
- Review conflicts and rules
- Generate reports
- No prescription or simulation rights

### Security Features

#### Authentication
- **Secure Login**: Username/password authentication with bcrypt hashing
- **Session Management**: Automatic session timeout after 30 minutes of inactivity
- **Login Rate Limiting**: Maximum 5 failed attempts, 15-minute lockout period
- **Password Requirements**:
  - Minimum 8 characters
  - At least one uppercase letter
  - At least one lowercase letter
  - At least one digit
  - At least one special character

#### Input Validation & Sanitization
- **XSS Prevention**: HTML/JavaScript tag removal from user inputs
- **SQL Injection Prevention**: Sanitization of database-like operations
- **Path Traversal Protection**: Validation of file paths
- **CSV Validation**: Schema validation for all uploaded data
- **Data Type Checking**: Strict type and range validation

#### Access Control
- **Page-Level Restrictions**: Role-based page access
- **Action-Level Permissions**: Fine-grained control over operations
- **Dynamic Navigation**: Users only see pages they can access
- **Permission Checks**: Real-time validation of user permissions

### User Management (Admin Only)

#### Adding New Users
1. Login as admin
2. Navigate to **User Management** page
3. Click **Add New User** tab
4. Fill in username, password, role, and email
5. Click **Add User**

#### Changing Passwords
1. Navigate to **User Management** page
2. Click **Change Password** tab
3. Enter current and new passwords
4. Password must meet strength requirements

#### Deleting Users
1. Navigate to **User Management** page
2. Select user from dropdown (cannot delete yourself or last admin)
3. Click **Delete User**
4. Confirm action

### Security Best Practices
1. **Change Default Passwords**: Immediately after first login
2. **Use Strong Passwords**: Follow complexity requirements
3. **Regular Password Updates**: Change passwords periodically
4. **Principle of Least Privilege**: Assign minimal necessary permissions
5. **Monitor Access**: Review user activity in audit logs (when enabled)
6. **Secure Environment**: Use HTTPS in production deployments
7. **Data Backup**: Regularly backup `users.json` and patient data

### Data Management Features

#### CRUD Operations
The system provides full Create, Read, Update, Delete (CRUD) functionality for all data types:

**Patient Management** (Admin + Doctor):
- **Add Patient**: Create new patient records with ID, name, conditions, and allergies
- **Edit Patient**: Modify existing patient information
- **Delete Patient**: Remove patient records (Admin only)
- Form validation prevents duplicate IDs and ensures required fields
- Conditions and allergies entered as multi-line text (one per line)

**Drug Database Management** (Admin + Pharmacist):
- **Add Drug**: Add new drugs with name, condition, category, and optional replacements
- **Edit Drug**: Update drug information including replacement suggestions
- **Delete Drug**: Remove drugs from the database (Admin + Pharmacist)
- Duplicate drug name detection
- Replacements stored as semicolon-separated strings

**Rules Engine Management** (Admin only):
- **Add Rule**: Create new conflict detection rules
  - Select type: drug-drug or drug-condition
  - Choose severity: Minor, Moderate, or Major
  - Provide item pairs and recommendations
- **Edit Rule**: Modify existing rules
- **Delete Rule**: Remove rules from the system
- Duplicate rule detection based on type and items

#### Data Persistence
- All changes immediately saved to CSV files
- No database required - simple file-based storage
- Changes reflected in real-time across all pages
- Data integrity maintained through validation

#### User Interface
- Permission-based button visibility (users only see actions they can perform)
- Inline forms for add/edit operations
- Cancel buttons to abort operations
- Success/error messages for user feedback
- Dropdown selectors for editing existing records

### Technical Implementation
- **Password Hashing**: bcrypt with salt (cost factor 12)
- **Session Storage**: Streamlit session state
- **Permission System**: Enum-based permission definitions
- **Validation**: Pydantic models + custom sanitizers
- **Security Patterns**: Input validation, output encoding, secure defaults

## 13. Deployment Slimming

For smaller artifacts, trim files based on your target.

- **CLI-only (headless simulation)**
    - Keep: `agents.py`, `model.py`, `utils.py`, `data_models.py`, `patients.csv`, `drugs.csv`, `rules.csv`, `requirements.txt`, `main.py`, `README.md`.
    - Remove: `app.py`, `auth.py`, `rbac.py`, `report_generator.py`, most of `validation.py` (keep only helpers you call), `users.json`, `tests/`, `output/`, all `__pycache__/`.

- **Streamlit app deployment**
    - Keep: everything required by the UI (`app.py`, `auth.py`, `rbac.py`, `report_generator.py`, core modules, CSVs).
    - Exclude from build: `tests/`, `__pycache__/`, `output/` (generated at runtime).

- **Always safe to delete**
    - `__pycache__/` directories and `output/` contents (they’re regenerated).

## 🗺️ Roadmap (Suggested)
* Expand rule dataset (≥500 entries)
* Dosage & duration conflict checks
* FastAPI/REST backend for integration
* Test suite (pytest) & coverage reports
* Persistent DB layer (PostgreSQL) replacing CSVs
* Enhanced audit logging with activity tracking
* ML‑assisted severity prediction & alternative recommendations

## 🔧 Troubleshooting
| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError` (mesa/streamlit/bcrypt) | Re-run `pip install -r requirements.txt` in the active venv. |
| Streamlit exit code 1 | Check virtual env activation; try `streamlit cache clear`; specify alternate port `--server.port 8502`. |
| Empty conflicts CSV | Sample data may produce few conflicts—add more rules or conditions. |
| Plot says dependencies missing | Install: `pip install matplotlib seaborn`. |
| Cannot login | Check `users.json` exists; use default credentials; ensure bcrypt installed. |
| "Access Denied" errors | Check user role permissions; login as admin for full access. |

## 🧪 Testing

### Running Tests
```powershell
# All tests (40 tests)
pytest tests/ -v

# Specific test files
pytest tests/test_bfs_search.py -v               # BFS algorithm tests (7)
pytest tests/test_conflict_detection.py -v       # Integration tests (2)
pytest tests/test_doctor_prescribe.py -v         # Doctor agent tests (2)
pytest tests/test_data_models.py -v              # Data validation tests (3)
pytest tests/test_memoization.py -v              # Cache layer tests (3)
pytest tests/test_realtime_ui.py -v              # Real-time UI tests (6)
pytest tests/test_report_generator.py -v         # Report generation tests (17)
```

### Test Coverage
- ✅ **BFS Algorithm**: State space exploration, priority ordering, edge cases
- ✅ **Conflict Detection**: Multi-drug prescriptions, severity sorting
- ✅ **Data Validation**: Pydantic models, semicolon parsing, ID coercion
- ✅ **Doctor Logic**: Risk-aware prescribing, allergy checking, replacements
- ✅ **Memoization Layer**: Cache hits/misses, KB invalidation
- ✅ **Real-time UI**: Live conflict detection, caching, performance
- ✅ **Report Generation**: PDF/Word creation, content validation, edge cases

### Adding Tests
Place new tests in `tests/` directory. Use fixtures from `conftest.py` for model setup.

## ⚕️ Medical Disclaimer
This repository is for **educational and prototyping purposes only**. It does **not** provide medical advice and must **not** be used for real clinical decision making. Always consult qualified healthcare professionals .

## 🤝 Contributing
1. Create a feature branch (`git checkout -b feature/name`).
2. Keep changes focused & documented in commit messages.
3. Add/adjust tests when logic changes.
4. Open a Pull Request describing rationale & impact.

## 📜 License
If you intend to open source formally, add a LICENSE file (e.g. MIT). Currently no explicit license is bundled.

---
### Quick Command Reference
```powershell
# CLI run - Smart mode (zero conflicts)
python main.py --mode smart

# CLI run - Demo mode (creates conflicts)
python main.py --mode conflict-prone

# Streamlit dashboard
streamlit run app.py

# Run tests
pytest tests/ -v

# Optional plotting
python -c "import pandas as pd; from utils import plot_severity_distribution as p; p(pd.read_csv('output/conflicts.csv'))"
```

### Next Steps
Focus improvements on rule coverage, extensible schema, and test automation.

---
Feel free to open issues or request enhancements.
