# Buy or Wait? — AI Financial Affordability Agent

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Engine](https://img.shields.io/badge/Engine-90--Day%20Deterministic%20Cashflow-success.svg)](#architecture)
[![Evaluation](https://img.shields.io/badge/Method%20Accuracy-88.0%25-brightgreen.svg)](#evaluation--benchmarks)
[![HackerRank](https://img.shields.io/badge/HackerRank-Orchestrate%202026-orange.svg)](https://www.hackerrank.com/)

An AI-powered financial decision agent built for the **HackerRank Orchestrate (September 2026)** challenge. For any given purchase or payment request, the agent evaluates 90-day future daily cash flows to decide whether a user should **pay in full**, **pay partially**, **use installments**, **wait**, or **not proceed**.

---

## 🌟 Key Features

- **90-Day Balance Simulation**: Daily cash flow forecasting incorporating historical events, pending transactions, salary updates, fixed recurring debits, and periodic variable expenses.
- **Neuro-Symbolic Perception**: Multi-modal OCR (`images.csv` via EasyOCR) and NLP fact extraction (`messages.csv`) parsing salary changes, unconfirmed gig payouts, ended employment, 12% lease indexations, and transaction cancellations.
- **Personalized Financial Protection**: Enforces user-specific constraints including `minimum_balance_to_keep`, preferred payment methods, max installment durations, and spending priorities.
- **Dynamic Plan Synthesis**: Automatically ranks candidate payment methods (Full, Partial, Installments, Wait) and evaluates flexible category spending adjustments (`stop:<event_id>` or `reduce_to:<event_id>:<amount>`).
- **Zero-Latency & High Reliability**: 100% deterministic cash flow forecasting engine ensuring $0 API token costs and eliminating LLM hallucination risks for numerical calculations.

---

## 🏗️ Architecture & Component Workflow

```
dataset/
 ├── financial_profiles.csv ───────┐
 ├── financial_events.csv   ───────┼──> [DataLoader]
 ├── exchange_rates.csv     ───────┤         │
 ├── messages.csv ──> [MessageParser]        ▼
 └── images.csv ───> [EasyOCR Engine] ──> [FinancialForecaster]
                                             │
                                             ▼
                                     [Candidate Ranking]
                                             │
                                             ▼
                                        output.csv
```

### Module Breakdown

| Module | Description |
| :--- | :--- |
| **`main.py`** | Main CLI entry point. Loads datasets, runs forecaster on all requests, and writes formatted predictions to `output.csv`. |
| **`code/forecaster.py`** | Core 90-day balance simulation, recurring pattern detector, headroom calculator, plan ranker, and natural language decision explanation generator. |
| **`code/data_loader.py`** | Ingests CSV files, maps multi-currency amounts using dated exchange rates, and constructs user profiles. |
| **`code/message_parser.py`** | Multi-lingual NLP fact extractor parsing salary updates, unconfirmed gig earnings, ended employment, and rent indexations. |
| **`code/extract_ocr.py`** | Runs EasyOCR over receipt and payment proof media images to extract transaction amounts. |
| **`INTERVIEW_PREP_KIT.md`** | Comprehensive 30-minute voice interview preparation kit, academic literature backing, and Q&A script. |
| **`code/create_code_zip.py`** | Packages clean solution code and evaluation reports into `code.zip` for submission. |

---

## 🚀 Quick Start

### 1. Installation

Clone the repository and install required Python packages:

```bash
git clone https://github.com/ADNation911/HackerRank-Orchestrate-AI-Financial-Agent.git
cd HackerRank-Orchestrate-AI-Financial-Agent
pip install pandas numpy easyocr torch
```

### 2. Execution

To run the agent against dataset requests and generate `output.csv`:

```bash
python main.py dataset dataset/sample_requests.csv output.csv
```

### 3. Running Evaluation Benchmarks

To run the automated evaluation script against ground-truth validation cases:

```bash
python code/evaluation/main.py
```

---

## 📊 Evaluation & Benchmarks

The agent was benchmarked against sample evaluation requests:

- **Recommended Payment Method Accuracy**: **88.0%** (22/25)
- **Payment Plan Structure Accuracy**: **88.0%** (22/25)
- **Flexible Spending Changes Accuracy**: **88.0%** (22/25)
- **Affordability Status Accuracy**: **80.0%** (20/25)

---

## 📝 Output Schema

The generated `output.csv` conforms strictly to the problem specification:

```csv
request_id,amount_safe_to_pay,affordability_status,recommended_payment_method,payment_plan,earliest_date_for_full_payment,spending_changes_needed,decision_explanation
request_01,25256.0,affordable_now,full_payment,2024-03-03:25256,2024-03-03,none,"Pay ZAR 25,256 today. This leaves at least ZAR 18,000 available over the next 90 days."
request_02,18200923.11,affordable_with_plan,installments,2025-08-08:15952906.67|2025-09-07:15952906.67|2025-10-07:15952906.67,2025-09-15,none,"Use 3 installments of IDR 15,952,906.67, starting 8 August 2025. This leaves at least IDR 29,158,400 available."
```

---

## 🛡️ License & Acknowledgments

Built for the **HackerRank Orchestrate 2026** competition.
