# AI Detection Hub

AI Detection Hub is a split-stack application for image-based analysis:

- **Deepfake / AI image detection**
- **Handwriting authenticity analysis**
- **Fake news screenshot fact-checking**

The app uses:

- **Backend:** FastAPI (Python)
- **Frontend:** React + Vite
- **Model SDK:** `google-genai`
- **Prompt source:** `prompts.json` (shared prompt config)

---

## Project structure

```
icat3.0/
├── backend/
│   └── app.py
├── frontend/
│   ├── src/
│   └── package.json
├── prompts.json
├── requirements.txt
└── main.py
```

---

## Prerequisites

- Python 3.10+
- Node.js 18+
- A Gemini API key

---

## Environment setup

Create a `.env` file in the project root:

```env
GOOGLE_API_KEY=your_api_key_here
# Optional
GEMINI_MODEL=gemini-2.5-flash
```

---

## Backend setup and run

From project root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Backend URL:

- `http://localhost:8000`
- Health check: `http://localhost:8000/api/health`

### Alternative backend command (from backend folder)

```bash
cd backend
source ../.venv/bin/activate
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

> Note: `python app.py` does not start a server by itself.

---

## Frontend setup and run

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend URL:

- `http://localhost:5173`

If backend is hosted elsewhere, create `frontend/.env`:

```env
VITE_API_BASE=http://localhost:8000
```

---

## API endpoints

All endpoints accept `multipart/form-data` with file field name: `image`.

- `POST /api/analyze/deepfake`
- `POST /api/analyze/handwriting`
- `POST /api/analyze/fake-news`

Example with `curl`:

```bash
curl -X POST "http://localhost:8000/api/analyze/deepfake" \
	-F "image=@/path/to/image.jpg"
```

---

## Prompts configuration

`prompts.json` stores the model prompts for all analyzers:

- `deepfake`
- `handwriting`
- `fake_news`

Update prompt text there without changing backend code.

---

## Troubleshooting

- **`GOOGLE_API_KEY not found`**
	- Ensure `.env` exists in project root and contains `GOOGLE_API_KEY`.

- **Frontend cannot reach backend**
	- Confirm backend is running on port `8000`.
	- Set `VITE_API_BASE` in `frontend/.env` if needed.

- **Import issues for Gemini SDK**
	- Use `google-genai` (not `google-generativeai`).
	- Reinstall deps: `pip install -r requirements.txt`
