# DocChat

A RAG-based chatbot that lets you ask questions about your own documents and shows exactly which part of which file the answer came from.

You drop PDFs or PowerPoint files into a folder, it indexes them, and you can query across all of them from a simple Streamlit interface.

---

## Tech Stack

| Component | Library / Tool |
|---|---|
| UI | Streamlit |
| Document loading | PyMuPDF, python-pptx |
| OCR | EasyOCR |
| Text splitting | LangChain RecursiveCharacterTextSplitter |
| Embeddings | FastEmbed — `BAAI/bge-small-en-v1.5` (runs locally, no API needed) |
| Vector store | FAISS |
| LLM | Groq — `openai/gpt-oss-120b` |
| Orchestration | LangChain |

---

## Pipeline

### Indexing (runs on first launch or when you click Rebuild Index)

```
docs/ folder
    │
    ├── PDFs ──► PyMuPDF checks for text layer
    │               ├── Text found ──► extract directly
    │               └── No text ────► EasyOCR page by page
    │                                       │
    │                               result saved to ocr_cache.json
    │
    └── PPTX/PPT ──► python-pptx extracts text slide by slide
                      (image-only slides are skipped)

All text
    │
    ▼
RecursiveCharacterTextSplitter (chunk size: 500, overlap: 50)
    │
    ▼
FastEmbed — bge-small-en-v1.5 (runs locally, no API call)
    │
    ▼
FAISS index saved to faiss_index/ on disk
```

### Query (every time you ask a question)

```
User question
    │
    ▼
Embed with bge-small-en-v1.5
    │
    ▼
FAISS similarity search → top 3 chunks
    │
    ▼
Chunks + question formatted into prompt
    │
    ▼
Groq API (GPT-OSS 120B)
    │
    ▼
Answer displayed + Sources expander shows filename, page, and chunk text
```

---

## What it does

- Accepts `.pdf` and `.pptx` files
- Automatically detects whether a PDF has a text layer or is a scanned image
- Scanned PDFs go through OCR before indexing (see note below)
- Chunks and embeds all content locally using `bge-small-en-v1.5`
- Stores the vector index in FAISS, saved to disk so it only builds once
- At query time, retrieves the 3 most relevant chunks and sends them to Groq to generate an answer
- Every answer is followed by a Sources section showing the filename, page number, and the actual chunk that was used

New files can be added at any time — clicking Rebuild Index only processes what isn't already cached.

---

## Project Structure

```
.
├── docs/               # Drop your PDFs and PPTXs here
├── app.py              # Streamlit UI
├── rag.py              # Indexing, retrieval, and generation pipeline
├── ocr.py              # OCR detection and caching logic
├── ocr_cache.json      # Auto-generated — tracks which files have been processed
├── faiss_index/        # Auto-generated — the saved vector index
├── .env                # Your API key (not committed)
├── .env.example        # Template
└── requirements.txt
```

---

## How to Run

**1. Clone the repo and install dependencies**

```bash
git clone <repo-url>
cd docchat
pip install -r requirements.txt
```

**2. Set up your API key**

```bash
cp .env.example .env
```

Open `.env` and paste your Groq API key. Get one free at [console.groq.com](https://console.groq.com).

**3. Add your documents**

Drop any `.pdf` or `.pptx`  files into the `docs/` folder.

**4. Run the app**

```bash
streamlit run app.py
```

The first run builds the index automatically. If you add new files later, click **Rebuild Index** in the top-right corner of the UI — only the new files get processed, everything cached is skipped.

---

## A Note on OCR and Handwritten Text

The project includes an OCR pipeline for scanned PDFs. When a PDF has no text layer, it converts each page to an image and runs it through EasyOCR before indexing.

This works well for printed text in scanned documents. However, EasyOCR was not designed for handwriting and the output on handwritten notes is not reliable enough to be useful — it tends to misread strokes and produce garbled text. I explored a vision model approach (sending pages to a multimodal LLM for transcription) which gives significantly better results, but adds latency and API cost per page.

For now, handwritten PDFs are best converted using a phone scanning app like Microsoft Lens or Google Lens before adding them to `docs/`. Both do on-device handwriting OCR that produces a proper searchable PDF, which the pipeline handles cleanly.

---

## Known Limitations

- Handwritten notes require preprocessing before indexing (see above)
- Image-only slides in PPTX files are skipped — only text content is indexed
- The FAISS index is stored locally; there is no persistence across machines without copying the `faiss_index/` folder