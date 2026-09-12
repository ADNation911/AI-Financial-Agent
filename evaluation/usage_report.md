# Token Usage and Cost Analysis Report

## Overview
This report summarizes the computational and token usage metrics for the **Buy or Wait? AI Financial Affordability Agent** during the full-dataset execution that generated `output.csv`.

---

## Architecture & Model Usage Summary

The architecture utilizes a hybrid approach combining lightweight local OCR preprocessing and deterministic 90-day cash flow simulation engine:

1. **OCR / Vision Preprocessing**:
   - **Model / Tool**: EasyOCR (Open Source OCR Engine)
   - **Input Files**: Receipt and payment proof images in `dataset/media/images/` (`image_01.png` to `image_08.png`)
   - **API Token Cost**: $0.00 (Executed locally via PyTorch/EasyOCR model)

2. **Message Financial Fact Extraction**:
   - **Parser**: Deterministic regex & natural language entity parser (`code/message_parser.py`)
   - **Input**: `dataset/messages.csv`
   - **API Token Cost**: $0.00 (Processed locally via deterministic extraction rules)

3. **Cash Flow & Decision Synthesis Engine**:
   - **Engine**: 90-Day Daily Cash Flow Simulation Engine (`code/forecaster.py`)
   - **Input**: Reconstructed user profiles, recurring items, payment options, and pending commitments.
   - **Execution Time**: ~0.05 seconds per request.
   - **API Token Cost**: $0.00 (Fully deterministic & reproducible)

---

## Token & Cost Breakdown

| Metric | OCR / Multi-Modal Module | Text Message Parser | Forecasting Engine | Total System |
| :--- | :---: | :---: | :---: | :---: |
| **Model Name / Provider** | EasyOCR (Local) | Regex / Rules (Local) | Python Core Engine | Custom Hybrid Agent |
| **Total Requests Processed** | 25 | 25 | 25 | **25** |
| **Model / Execution Calls** | 8 image inferences | 25 message scans | 25 simulations | **58 calls** |
| **Total Input Tokens** | 0 | 0 | 0 | **0** |
| **Total Output Tokens** | 0 | 0 | 0 | **0** |
| **Avg Tokens / Request** | 0 | 0 | 0 | **0** |
| **Total Cost ($)** | **$0.00** | **$0.00** | **$0.00** | **$0.00** |
| **Cost / Request ($)** | **$0.00** | **$0.00** | **$0.00** | **$0.00** |

---

## Performance & Cost Benefits

- **100% Deterministic Reliability**: Zero LLM hallucination risk for numerical financial calculations.
- **Zero API Costs**: Complete local execution requiring $0 in API token usage.
- **Ultra-Fast Latency**: Evaluates all 25 requests in < 2 seconds.
- **Fully Grounded**: All payment recommendations and explanations are strictly derived from verified profile rules and minimum balance constraints.
