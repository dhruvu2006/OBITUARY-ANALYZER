# 🪦 Obituary Analyzer

> **"We turned an entire newspaper into statistics. Nobody asked us to."**
>
> *Technically impressive. Completely unnecessary.*

---

## Problem

Newspapers contain obituary sections. Nobody needs an automated system to scan an entire newspaper, detect those sections automatically, alphabetically sort the people mentioned, and generate completely unnecessary statistics about age distributions.

We built one anyway.

## Solution

Upload a full newspaper PDF. The application automatically scans **every single page**, scores each page for obituary/death-related content using keyword analysis, age-pattern detection and name-pattern recognition, then extracts structured information and presents it in a professional dashboard with charts, useless statistics, and a "Completely Unscientific Uselessness Score."

---

## Features

- **Automatic Full-Newspaper Scanning** — No manual page sele+ction. Every page is scanned.
- **Obituary Page Detection** — Multi-factor relevance scoring (0–100%) per page.
- **Page Classification** — OBITUARY / DEATH NOTICES / MEMORIAL / NOT RELEVANT.
- **Direct PDF Text Extraction** — Fast path for digital newspapers.
- **OCR Fallback** — Tesseract OCR for scanned newspaper images.
- **Name & Age Extraction** — Rule-based extraction with confidence scoring.
- **Birth/Death Year Calculation** — `1942–2026` → Age ≈ 84 (marked as Calculated).
- **Notice Type Classification** — Obituary / Death Notice / Memorial / Condolence / etc.
- **Manual Review Table** — Editable before final analysis.
- **Duplicate Detection** — Flags similar name/age pairs.
- **Alphabetical Sorting** — Case-insensitive, title-prefix aware.
- **Age Group Analysis** — 0-18 / 19-40 / 41-60 / 61-80 / 81-100 / 101+ / Unknown.
- **Interactive Charts** — Plotly bar charts for age groups and page-wise breakdown.
- **Search & Filter** — By name, age group, page, notice type, confidence.
- **Useless Statistics** — Average, median, youngest, oldest, alphabetically first, % above 80, and more.
- **Useless Insight Generator** — Humorous insights based on actual data.
- **Uselessness Score** — A completely unscientific metric.
- **CSV Export** — Download the full dataset.
- **Demo Mode** — Instant demo without a real PDF (great for hackathon presentations).
- **Error Handling** — Graceful fallbacks at every stage.

---

## Architecture

```
PDF Upload
   ↓
Page Extraction (PyMuPDF)
   ↓
Direct Text Extraction ──→ (if sparse) ──→ OCR (Tesseract)
   ↓
Text Cleaning
   ↓
Obituary Page Detection (keyword scoring + age/name pattern analysis)
   ↓
User Reviews Detected Pages (can deselect)
   ↓
Entry Extraction (name, age, notice type, confidence)
   ↓
Duplicate Detection
   ↓
User Reviews & Corrects Entries
   ↓
Pandas DataFrame
   ↓
Alphabetical Sort + Age Grouping + Statistics
   ↓
Dashboard (charts, metrics, useless stats, export)
```

**Module breakdown:**
| Module | Responsibility |
|---|---|
| `src/pdf_processor.py` | Extract pages; direct text + image rendering |
| `src/ocr.py` | Tesseract OCR with image preprocessing |
| `src/cleaner.py` | Normalize raw text |
| `src/page_detector.py` | Multi-factor obituary relevance scoring |
| `src/extractor.py` | Name, age, notice type, confidence extraction |
| `src/duplicate_detector.py` | Flag similar entries |
| `src/analyzer.py` | Statistics, insights, uselessness score |
| `src/utils.py` | Demo data |
| `app.py` | Streamlit UI — 4-step flow |

---

## Tech Stack

- **Python 3.10+**
- **Streamlit** — Web application
- **PyMuPDF** (`fitz`) — PDF page extraction
- **Tesseract OCR** (`pytesseract`) — Optical Character Recognition
- **Pillow** — Image preprocessing
- **Pandas** — Data manipulation
- **Plotly** — Interactive charts

---

## Installation

### 1. Install Tesseract OCR

**Windows:**
1. Download from the [UB-Mannheim repository](https://github.com/UB-Mannheim/tesseract/wiki).
2. Install (e.g. `C:\Program Files\Tesseract-OCR\`).
3. The application auto-detects this path — no manual configuration needed.

**Mac:**
```bash
brew install tesseract
```

**Linux (Ubuntu):**
```bash
sudo apt-get install tesseract-ocr
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

---

## Running

```bash
python -m streamlit run app.py
```

or (if `streamlit` is on PATH):

```bash
streamlit run app.py
```

---

## Hackathon Concept

Built for a **"Useless Projects" hackathon**. The joke is that we apply serious engineering — PDF rendering, OCR, NLP-style keyword scoring, confidence scoring, deduplication, Pandas analysis — to a problem that has absolutely no practical application. The technology is real. The utility is fictional.

---

## Future Scope

- **Malayalam / Tamil / Hindi** newspaper support (multilingual Tesseract models)
- **Improved NLP extraction** using a local LLM
- **Automatic layout understanding** (column detection, header recognition)
- **Historical comparison** across multiple newspaper editions
- **Better duplicate resolution** with fuzzy clustering
- **Trend analysis** over time
- **Automatic format detection** per newspaper publisher
