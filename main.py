import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
from PIL import Image
import io
import json
import re
import time
import html as html_lib

# ── Load environment ──────────────────────────────────────────────────────────
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY", "").strip("'\"")

if not API_KEY:
    st.error("GOOGLE_API_KEY not found in .env file.")
    st.stop()

genai.configure(api_key=API_KEY)

# ── Page configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Detection Hub",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

  /* Dark background */
  .stApp { background: #0a0e1a; color: #e2e8f0; }
  .main .block-container { padding: 2rem 3rem; max-width: 1200px; }

  /* Hero header */
  .hero {
    background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
    border: 1px solid #334155;
    border-radius: 20px;
    padding: 2.5rem;
    margin-bottom: 2rem;
    text-align: center;
    position: relative;
    overflow: hidden;
  }
  .hero::before {
    content: '';
    position: absolute;
    top: -50%; left: -50%;
    width: 200%; height: 200%;
    background: radial-gradient(circle at 50% 50%, rgba(99,102,241,0.08) 0%, transparent 60%);
  }
  .hero-title {
    font-size: 2.8rem;
    font-weight: 700;
    background: linear-gradient(135deg, #818cf8, #c084fc, #38bdf8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
  }
  .hero-sub {
    color: #94a3b8;
    font-size: 1.05rem;
    margin-top: 0.5rem;
  }

  /* Feature cards */
  .feature-card {
    background: #111827;
    border: 1px solid #1f2937;
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    transition: border-color 0.2s;
  }
  .feature-card:hover { border-color: #4f46e5; }
  .feature-title {
    font-size: 1.3rem;
    font-weight: 600;
    color: #e2e8f0;
    margin-bottom: 0.3rem;
  }
  .feature-desc { color: #64748b; font-size: 0.9rem; }

  /* Result cards */
  .result-box {
    border-radius: 14px;
    padding: 1.5rem;
    margin-top: 1.2rem;
    border: 1px solid;
    animation: fadeIn 0.4s ease;
  }
  .result-real {
    background: rgba(16,185,129,0.08);
    border-color: #059669;
  }
  .result-fake {
    background: rgba(239,68,68,0.09);
    border-color: #dc2626;
  }
  .result-warning {
    background: rgba(245,158,11,0.08);
    border-color: #d97706;
  }
  .result-neutral {
    background: rgba(99,102,241,0.08);
    border-color: #4f46e5;
  }

  /* Verdict badge */
  .verdict-badge {
    display: inline-block;
    padding: 0.3rem 1rem;
    border-radius: 20px;
    font-weight: 700;
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 1rem;
  }
  .badge-real  { background: #059669; color: #fff; }
  .badge-fake  { background: #dc2626; color: #fff; }
  .badge-warn  { background: #d97706; color: #fff; }
  .badge-uncl  { background: #4f46e5; color: #fff; }

  /* Confidence bar */
  .conf-bar-wrap {
    background: #1f2937;
    border-radius: 8px;
    height: 10px;
    margin: 0.5rem 0 1rem;
    overflow: hidden;
  }
  .conf-bar { height: 100%; border-radius: 8px; transition: width 0.6s ease; }
  .conf-label { font-size: 0.8rem; color: #94a3b8; margin-bottom: 0.2rem; }

  /* Analysis text */
  .analysis-text {
    background: #0f172a;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    color: #cbd5e1;
    font-size: 0.92rem;
    line-height: 1.7;
    border-left: 3px solid #4f46e5;
    margin-top: 0.8rem;
  }

  /* Tabs */
  .stTabs [data-baseweb="tab-list"] {
    background: #111827;
    border-radius: 12px;
    padding: 0.4rem;
    gap: 0.3rem;
    border: 1px solid #1f2937;
  }
  .stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    color: #64748b;
    padding: 0.6rem 1.4rem;
    font-weight: 500;
  }
  .stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #4f46e5, #7c3aed) !important;
    color: #fff !important;
  }
  .stTabs [data-baseweb="tab-panel"] { padding-top: 1.5rem; }

  /* Upload zone */
  .stFileUploader > div {
    background: #111827 !important;
    border: 2px dashed #334155 !important;
    border-radius: 14px !important;
    color: #64748b !important;
  }
  .stFileUploader > div:hover { border-color: #6366f1 !important; }

  /* Buttons */
  .stButton > button {
    background: linear-gradient(135deg, #4f46e5, #7c3aed);
    color: white;
    border: none;
    border-radius: 10px;
    padding: 0.65rem 2rem;
    font-weight: 600;
    font-size: 0.95rem;
    width: 100%;
    transition: opacity 0.2s, transform 0.1s;
  }
  .stButton > button:hover { opacity: 0.9; transform: translateY(-1px); }
  .stButton > button:active { transform: translateY(0); }

  /* Text input */
  .stTextArea textarea, .stTextInput input {
    background: #111827 !important;
    border: 1px solid #334155 !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
  }
  .stTextArea textarea:focus, .stTextInput input:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 2px rgba(99,102,241,0.15) !important;
  }

  /* Spinner */
  .stSpinner > div { border-top-color: #6366f1 !important; }

  /* Divider */
  hr { border-color: #1f2937; }

  /* Scrollbar */
  ::-webkit-scrollbar { width: 6px; }
  ::-webkit-scrollbar-track { background: #0f172a; }
  ::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }

  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  /* Source chips for fake news */
  .source-chip {
    display: inline-block;
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 20px;
    padding: 0.2rem 0.8rem;
    font-size: 0.78rem;
    color: #94a3b8;
    margin: 0.2rem;
  }
  .source-chip a { color: #818cf8 !important; text-decoration: none; }
  .source-chip a:hover { color: #c084fc !important; }

  /* Info pills */
  .info-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background: #1e293b;
    border-radius: 6px;
    padding: 0.25rem 0.7rem;
    font-size: 0.8rem;
    color: #94a3b8;
    margin: 0.2rem 0.2rem 0 0;
  }
</style>
""", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <p class="hero-title">🔍 AI Detection Hub</p>
  <p class="hero-sub">Deepfake Detection &nbsp;·&nbsp; Handwriting Analysis &nbsp;·&nbsp; Fake News Verification</p>
</div>
""", unsafe_allow_html=True)

# ── Helper: load image bytes ───────────────────────────────────────────────────
def image_to_bytes(uploaded_file) -> bytes:
    return uploaded_file.read()

def pil_to_bytes(img: Image.Image, fmt="PNG") -> bytes:
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()

# ── Helper: extract JSON verdict from Gemini response ─────────────────────────
def parse_verdict(text: str) -> dict:
    """Attempt to pull a JSON block from the response."""
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return {}

# ── Helper: confidence bar HTML ───────────────────────────────────────────────
def confidence_bar(label: str, pct: int, color: str) -> str:
    return f"""
    <div class="conf-label">{label} — <strong>{pct}%</strong></div>
    <div class="conf-bar-wrap">
      <div class="conf-bar" style="width:{pct}%; background:{color};"></div>
    </div>
    """

# ─────────────────────────────────────────────────────────────────────────────
#  FEATURE 1 — DEEPFAKE IMAGE DETECTION
# ─────────────────────────────────────────────────────────────────────────────
def analyze_deepfake(image_bytes: bytes, mime_type: str) -> dict:
    model = genai.GenerativeModel("gemini-2.5-flash")
    prompt = """You are an expert forensic image analyst and deepfake detection AI.
Carefully examine every detail of this image and determine if it is:
- A REAL authentic photograph
- A DEEPFAKE (AI face-swap, GAN-generated face, diffusion-model-generated face)
- AI GENERATED (entirely synthetic image created by Stable Diffusion, DALL-E, Midjourney etc.)
- MANIPULATED (digitally edited/composited real photo)

Look for these telltale signs:
• Facial artifacts: asymmetry, blurring at hairline, ear inconsistency, eye glint anomalies
• Skin texture smoothness vs. natural pores
• Lighting inconsistencies (face vs. background)
• GAN/diffusion artifacts: checkerboard noise, spectral artifacts, mode collapse
• Background coherence (distortion near face edges is a key deepfake sign)
• Metadata cues from compression patterns
• Portrait-specific: Too-perfect symmetry is a red flag

Respond ONLY with this JSON (no markdown, no extra text):
{
  "verdict": "REAL" | "DEEPFAKE" | "AI_GENERATED" | "MANIPULATED" | "UNCERTAIN",
  "confidence": <integer 0-100>,
  "risk_level": "LOW" | "MEDIUM" | "HIGH",
  "summary": "<2-3 sentence plain-English explanation>",
  "indicators": ["<indicator 1>", "<indicator 2>", "<indicator 3>"],
  "forensic_notes": "<technical detail for experts>"
}"""
    response = model.generate_content(
        [{"mime_type": mime_type, "data": image_bytes}, prompt]
    )
    raw = response.text.strip()
    data = parse_verdict(raw)
    if not data:
        data = {
            "verdict": "UNCERTAIN",
            "confidence": 50,
            "risk_level": "MEDIUM",
            "summary": raw,
            "indicators": [],
            "forensic_notes": "",
        }
    return data


# ─────────────────────────────────────────────────────────────────────────────
#  FEATURE 2 — HANDWRITING / TEXT AI DETECTION
# ─────────────────────────────────────────────────────────────────────────────
def analyze_handwriting(image_bytes: bytes, mime_type: str) -> dict:
    model = genai.GenerativeModel("gemini-2.5-flash")
    prompt = """You are an expert handwriting analyst and AI-generated text detector.
Examine this image closely. It may contain:
- Authentic human handwriting (pen, pencil, cursive, print)
- AI-generated / computer-simulated handwriting (fonts mimicking handwriting, GAN-generated script)
- Machine-printed text (typed/laser-printed)
- A mix of human and AI-generated content
decide if the image is likely AI-generated/manipulated (deepfake) vs authentic.
Use strict forensic cues: face boundary mismatch, skin texture repetition, lighting/reflection mismatch, warped geometry, inconsistent shadows, unnatural background blending, repeated GAN-like patterns, and impossible details.
Analyze for these indicators of AI/synthetic origin:
• Excessive regularity — letter spacing, baseline, slant too consistent
• Lack of natural pressure variation (real handwriting shows thick/thin strokes)
• Perfect loops and curves devoid of natural tremor or hesitation
• Repeating patterns or glyphs that are identical (pixel-perfect repetition)
• Absence of ligature variation in cursive
• Font artifacts embedded in "handwriting" style
• Ink bleed, paper texture, pen drag — are they authentic?
• For printed text: is the question whether it was written by a human or AI assistant?
  If so, analyze writing style, vocabulary complexity, structural patterns, and typical AI tells
  (over-hedging, formulaic structure, suspiciously balanced paragraphs).

Respond ONLY with this JSON (no markdown, no extra text):
{
  "verdict": "HUMAN_HANDWRITTEN" | "AI_SIMULATED_HANDWRITING" | "MACHINE_PRINTED" | "AI_GENERATED_TEXT" | "MIXED" | "UNCERTAIN",
  "confidence": <integer 0-100>,
  "is_ai_origin": true | false,
  "summary": "<2-3 sentence plain-English explanation>",
  "indicators": ["<indicator 1>", "<indicator 2>", "<indicator 3>"],
  "legibility_score": <integer 0-100>,
  "style_notes": "<description of writing style and any anomalies>"
}"""
    response = model.generate_content(
        [{"mime_type": mime_type, "data": image_bytes}, prompt]
    )
    raw = response.text.strip()
    data = parse_verdict(raw)
    if not data:
        data = {
            "verdict": "UNCERTAIN",
            "confidence": 50,
            "is_ai_origin": False,
            "summary": raw,
            "indicators": [],
            "legibility_score": 50,
            "style_notes": "",
        }
    return data


# ─────────────────────────────────────────────────────────────────────────────
#  FEATURE 3 — FAKE NEWS DETECTION (image upload + Google Search grounding)
# ─────────────────────────────────────────────────────────────────────────────
def analyze_fake_news(image_bytes: bytes, mime_type: str) -> dict:
    """Extract text from a news image, then fact-check it with Gemini + Google Search."""
    model = genai.GenerativeModel("gemini-2.5-flash")
    prompt = """You are a professional fact-checker and investigative journalist.
First, carefully read all visible text in this image — it may be a screenshot of a news article,
a social media post, a headline, a WhatsApp forward, or a printed clipping.
decide if handwriting is likely AI-generated/synthetic vs naturally human-written.
Focus on telltale cues: repeated identical character shapes, overly uniform stroke width/pressure, unnaturally consistent slant, baseline and spacing regularity, copied ligature patterns, and digital render artifacts.
Then fact-check the main claim or headline using your knowledge and any search results available.

Evaluate the claim thoroughly:
1. Extract and identify the core claim or headline from the image
2. Search for corroborating or refuting evidence from credible sources
3. Check for known misinformation patterns
4. Assess plausibility given established facts
5. Identify any misleading framing, selective context, or outright fabrications

Respond ONLY with this JSON (no markdown, no extra text):
{
  "extracted_claim": "<the main claim or headline you read from the image>",
  "verdict": "TRUE" | "FALSE" | "MISLEADING" | "UNVERIFIED" | "PARTIALLY_TRUE",
  "confidence": <integer 0-100>,
  "summary": "<3-4 sentence plain-English verdict explanation>",
  "key_findings": ["<finding 1>", "<finding 2>", "<finding 3>"],
  "red_flags": ["<red flag 1>", "<red flag 2>"],
  "recommendation": "<what the reader should do or know>",
  "credibility_score": <integer 0-100 where 100 = fully credible>
}"""

    response = model.generate_content(
        [{"mime_type": mime_type, "data": image_bytes}, prompt]
    )
    raw = response.text.strip()
    data = parse_verdict(raw)
    if not data:
        data = {
            "extracted_claim": "",
            "verdict": "UNVERIFIED",
            "confidence": 40,
            "summary": raw,
            "key_findings": [],
            "red_flags": [],
            "recommendation": "Verify with multiple credible sources.",
            "credibility_score": 40,
        }
    return data


# ─────────────────────────────────────────────────────────────────────────────
#  TABS
# ─────────────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "🖼️  Deepfake Detector",
    "✍️  Handwriting Analyzer",
    "📰  Fake News Detector",
])

# ══════════════════════════════════════════════════════════════════════════════
#  TAB 1 — DEEPFAKE DETECTION
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("""
    <div class="feature-card">
      <div class="feature-title">🖼️ Deepfake & AI Image Detection</div>
      <div class="feature-desc">Upload any image — portrait, scene, document screenshot — and get a
      forensic analysis detecting GAN faces, diffusion-model art, face-swaps, and digital manipulation.</div>
    </div>
    """, unsafe_allow_html=True)

    col_up, col_res = st.columns([1, 1], gap="large")

    with col_up:
        uploaded = st.file_uploader(
            "Drop or browse an image",
            type=["jpg", "jpeg", "png", "webp", "bmp"],
            key="deepfake_upload",
            label_visibility="collapsed",
        )
        if uploaded:
            img = Image.open(io.BytesIO(uploaded.read()))
            uploaded.seek(0)
            w, h = img.size
            st.image(img, caption=f"{uploaded.name}  ·  {w}×{h}px", use_container_width=True)
            st.markdown(f"""
            <div style="display:flex; flex-wrap:wrap; gap:4px; margin-top:6px;">
              <span class="info-pill">📄 {uploaded.name}</span>
              <span class="info-pill">📐 {w}×{h}</span>
              <span class="info-pill">💾 {uploaded.size/1024:.1f} KB</span>
            </div>""", unsafe_allow_html=True)

        analyze_btn = st.button("🔍 Analyze Image", key="btn_deepfake", disabled=not uploaded)

    with col_res:
        if uploaded and analyze_btn:
            with st.spinner("Running forensic analysis…"):
                try:
                    uploaded.seek(0)
                    img_bytes = uploaded.read()
                    ext = uploaded.name.rsplit(".", 1)[-1].lower()
                    mime_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg",
                                "png": "image/png", "webp": "image/webp", "bmp": "image/bmp"}
                    mime = mime_map.get(ext, "image/jpeg")
                    result = analyze_deepfake(img_bytes, mime)
                except Exception as e:
                    st.error(f"Analysis failed: {e}")
                    st.stop()

            verdict = result.get("verdict", "UNCERTAIN")
            confidence = result.get("confidence", 50)
            risk = result.get("risk_level", "MEDIUM")
            summary = result.get("summary", "")
            indicators = result.get("indicators", [])
            forensic = result.get("forensic_notes", "")

            # Choose styling
            if verdict in ("REAL",):
                box_cls, badge_cls, bar_color = "result-real", "badge-real", "#10b981"
                icon = "✅"
            elif verdict in ("DEEPFAKE", "AI_GENERATED", "MANIPULATED"):
                box_cls, badge_cls, bar_color = "result-fake", "badge-fake", "#ef4444"
                icon = "🚨"
            else:
                box_cls, badge_cls, bar_color = "result-warning", "badge-warn", "#f59e0b"
                icon = "⚠️"

            risk_colors = {"LOW": "#10b981", "MEDIUM": "#f59e0b", "HIGH": "#ef4444"}
            safe_summary = html_lib.escape(summary)

            st.markdown(f"""
            <div class="result-box {box_cls}">
              <span class="verdict-badge {badge_cls}">{icon} {verdict.replace("_", " ")}</span>
              <br/>
              {confidence_bar("Detection Confidence", confidence, bar_color)}
              {confidence_bar("Manipulation Likelihood", {"LOW":25,"MEDIUM":60,"HIGH":95}.get(risk,50), risk_colors.get(risk,"#6366f1"))}
              <div class="analysis-text">{safe_summary}</div>
            </div>
            """, unsafe_allow_html=True)

            if indicators:
                st.markdown("**🧪 Detection Indicators**")
                for ind in indicators:
                    st.markdown(f"- {ind}")

            if forensic:
                with st.expander("🔬 Forensic Technical Notes"):
                    st.markdown(forensic)
        elif not uploaded:
            st.markdown("""
            <div style="text-align:center; padding:3rem 1rem; color:#334155;">
              <div style="font-size:3rem;">🖼️</div>
              <div style="margin-top:0.5rem; font-size:0.9rem;">Upload an image to begin analysis</div>
            </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 2 — HANDWRITING DETECTION
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("""
    <div class="feature-card">
      <div class="feature-title">✍️ Handwriting & AI Text Detection</div>
      <div class="feature-desc">Upload a photo or scan of handwritten notes, typed documents, or
      assignment pages. The AI will determine if the content is genuine human handwriting,
      AI-simulated script, machine-printed, or AI-generated written text.</div>
    </div>
    """, unsafe_allow_html=True)

    col_u2, col_r2 = st.columns([1, 1], gap="large")

    with col_u2:
        hw_upload = st.file_uploader(
            "Drop or browse a handwriting / document image",
            type=["jpg", "jpeg", "png", "webp", "bmp", "tiff"],
            key="hw_upload",
            label_visibility="collapsed",
        )
        if hw_upload:
            hw_img = Image.open(io.BytesIO(hw_upload.read()))
            hw_upload.seek(0)
            w2, h2 = hw_img.size
            st.image(hw_img, caption=f"{hw_upload.name}  ·  {w2}×{h2}px", use_container_width=True)
            st.markdown(f"""
            <div style="display:flex; flex-wrap:wrap; gap:4px; margin-top:6px;">
              <span class="info-pill">📄 {hw_upload.name}</span>
              <span class="info-pill">📐 {w2}×{h2}</span>
              <span class="info-pill">💾 {hw_upload.size/1024:.1f} KB</span>
            </div>""", unsafe_allow_html=True)

        hw_btn = st.button("✍️ Analyze Writing", key="btn_hw", disabled=not hw_upload)

    with col_r2:
        if hw_upload and hw_btn:
            with st.spinner("Examining writing patterns…"):
                try:
                    hw_upload.seek(0)
                    hw_bytes = hw_upload.read()
                    hw_ext = hw_upload.name.rsplit(".", 1)[-1].lower()
                    hw_mime_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg",
                                   "png": "image/png", "webp": "image/webp",
                                   "bmp": "image/bmp", "tiff": "image/tiff"}
                    hw_mime = hw_mime_map.get(hw_ext, "image/jpeg")
                    hw_result = analyze_handwriting(hw_bytes, hw_mime)
                except Exception as e:
                    st.error(f"Analysis failed: {e}")
                    st.stop()

            hw_verdict = hw_result.get("verdict", "UNCERTAIN")
            hw_conf = hw_result.get("confidence", 50)
            is_ai = hw_result.get("is_ai_origin", False)
            hw_sum = hw_result.get("summary", "")
            hw_inds = hw_result.get("indicators", [])
            legibility = hw_result.get("legibility_score", 50)
            style_notes = hw_result.get("style_notes", "")

            if hw_verdict == "HUMAN_HANDWRITTEN":
                hw_box, hw_badge, hw_color = "result-real", "badge-real", "#10b981"
                hw_icon = "✅"
            elif hw_verdict in ("AI_SIMULATED_HANDWRITING", "AI_GENERATED_TEXT"):
                hw_box, hw_badge, hw_color = "result-fake", "badge-fake", "#ef4444"
                hw_icon = "🤖"
            elif hw_verdict == "MACHINE_PRINTED":
                hw_box, hw_badge, hw_color = "result-neutral", "badge-uncl", "#6366f1"
                hw_icon = "🖨️"
            elif hw_verdict == "MIXED":
                hw_box, hw_badge, hw_color = "result-warning", "badge-warn", "#f59e0b"
                hw_icon = "⚠️"
            else:
                hw_box, hw_badge, hw_color = "result-warning", "badge-warn", "#f59e0b"
                hw_icon = "❓"

            ai_conf_bar = confidence_bar("AI Origin Probability", hw_conf if is_ai else 100 - hw_conf, "#ef4444")
            human_conf_bar = confidence_bar("Human Origin Probability", hw_conf if not is_ai else 100 - hw_conf, "#10b981")
            leg_bar = confidence_bar("Legibility Score", legibility, "#6366f1")
            safe_hw_sum = html_lib.escape(hw_sum)

            st.markdown(f"""
            <div class="result-box {hw_box}">
              <span class="verdict-badge {hw_badge}">{hw_icon} {hw_verdict.replace("_", " ")}</span>
              <br/>
              {ai_conf_bar}
              {human_conf_bar}
              {leg_bar}
              <div class="analysis-text">{safe_hw_sum}</div>
            </div>
            """, unsafe_allow_html=True)

            if hw_inds:
                st.markdown("**🧪 Writing Pattern Indicators**")
                for ind in hw_inds:
                    st.markdown(f"- {ind}")

            if style_notes:
                with st.expander("🖊️ Style Analysis Notes"):
                    st.markdown(style_notes)
        elif not hw_upload:
            st.markdown("""
            <div style="text-align:center; padding:3rem 1rem; color:#334155;">
              <div style="font-size:3rem;">✍️</div>
              <div style="margin-top:0.5rem; font-size:0.9rem;">Upload a handwriting or document image to begin</div>
            </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 3 — FAKE NEWS DETECTION
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("""
    <div class="feature-card">
      <div class="feature-title">📰 Fake News & Misinformation Detector</div>
      <div class="feature-desc">Upload a screenshot of a news article, social media post,
      WhatsApp forward, or printed clipping. The AI will read the text, search the web,
      and return a detailed fact-check verdict with key findings.</div>
    </div>
    """, unsafe_allow_html=True)

    fn_col1, fn_col2 = st.columns([1, 1], gap="large")

    with fn_col1:
        fn_upload = st.file_uploader(
            "Drop or browse a news screenshot or image",
            type=["jpg", "jpeg", "png", "webp", "bmp"],
            key="fn_upload",
            label_visibility="collapsed",
        )
        if fn_upload:
            fn_img = Image.open(io.BytesIO(fn_upload.read()))
            fn_upload.seek(0)
            fw, fh = fn_img.size
            st.image(fn_img, caption=f"{fn_upload.name}  ·  {fw}×{fh}px", use_container_width=True)
            st.markdown(f"""
            <div style="display:flex; flex-wrap:wrap; gap:4px; margin-top:6px;">
              <span class="info-pill">📄 {fn_upload.name}</span>
              <span class="info-pill">📐 {fw}×{fh}</span>
              <span class="info-pill">💾 {fn_upload.size/1024:.1f} KB</span>
            </div>""", unsafe_allow_html=True)

        fn_btn = st.button(
            "🔎 Fact-Check Now",
            key="btn_fn",
            disabled=not fn_upload,
        )

        st.markdown("<br/>", unsafe_allow_html=True)
        st.markdown("""
        <div style="background:#111827; border:1px solid #1f2937; border-radius:12px; padding:1rem;">
          <div style="font-size:0.82rem; color:#475569; font-weight:600; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:0.6rem;">How it works</div>
          <div style="font-size:0.85rem; color:#64748b; line-height:1.7;">
            📸 &nbsp;Upload any news screenshot or image<br/>
            🔍 &nbsp;AI reads and extracts the claim<br/>
            📚 &nbsp;Cross-references multiple credible sources<br/>
            📊 &nbsp;Returns a confidence-scored verdict
          </div>
        </div>""", unsafe_allow_html=True)

    with fn_col2:
        if fn_upload and fn_btn:
            with st.spinner("Reading image and fact-checking…"):
                try:
                    fn_upload.seek(0)
                    fn_bytes = fn_upload.read()
                    fn_ext = fn_upload.name.rsplit(".", 1)[-1].lower()
                    fn_mime_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg",
                                   "png": "image/png", "webp": "image/webp", "bmp": "image/bmp"}
                    fn_mime = fn_mime_map.get(fn_ext, "image/jpeg")
                    fn_result = analyze_fake_news(fn_bytes, fn_mime)
                except Exception as e:
                    st.error(f"Fact-check failed: {e}")
                    st.stop()

            fn_verdict      = fn_result.get("verdict", "UNVERIFIED")
            fn_conf         = fn_result.get("confidence", 50)
            fn_credibility  = fn_result.get("credibility_score", 50)
            fn_summary      = fn_result.get("summary", "")
            fn_findings     = fn_result.get("key_findings", [])
            fn_flags        = fn_result.get("red_flags", [])
            fn_rec          = fn_result.get("recommendation", "")
            fn_claim        = fn_result.get("extracted_claim", "")

            VERDICT_STYLE = {
                "TRUE":          ("result-real",    "badge-real",  "#10b981", "✅"),
                "PARTIALLY_TRUE":("result-warning",  "badge-warn",  "#f59e0b", "🟡"),
                "MISLEADING":    ("result-warning",  "badge-warn",  "#f59e0b", "⚠️"),
                "FALSE":         ("result-fake",     "badge-fake",  "#ef4444", "❌"),
                "UNVERIFIED":    ("result-neutral",  "badge-uncl",  "#6366f1", "❓"),
            }
            fn_box, fn_badge, fn_color, fn_icon = VERDICT_STYLE.get(
                fn_verdict, ("result-neutral", "badge-uncl", "#6366f1", "❓")
            )

            if fn_claim:
                st.markdown(f"""
                <div style="background:#1e293b; border-radius:10px; padding:0.7rem 1rem;
                     margin-bottom:0.8rem; border-left:3px solid #334155; font-size:0.85rem; color:#94a3b8;">
                  📋 <strong style="color:#cbd5e1;">Detected Claim:</strong> {html_lib.escape(fn_claim)}
                </div>""", unsafe_allow_html=True)

            safe_fn_summary = html_lib.escape(fn_summary)
            st.markdown(f"""
            <div class="result-box {fn_box}">
              <span class="verdict-badge {fn_badge}">{fn_icon} {fn_verdict.replace("_", " ")}</span>
              <br/>
              {confidence_bar("Fact-Check Confidence", fn_conf, fn_color)}
              {confidence_bar("Source Credibility", fn_credibility, "#818cf8")}
              <div class="analysis-text">{safe_fn_summary}</div>
            </div>
            """, unsafe_allow_html=True)

            if fn_findings:
                st.markdown("**🔑 Key Findings**")
                for f in fn_findings:
                    st.markdown(f"- {f}")

            if fn_flags:
                st.markdown("**🚩 Red Flags**")
                for flag in fn_flags:
                    st.markdown(f"- {flag}")

            if fn_rec:
                st.markdown(f"""
                <div style="background:#1e293b; border-radius:10px; padding:0.8rem 1rem;
                     margin-top:0.8rem; border-left:3px solid #818cf8; font-size:0.88rem; color:#94a3b8;">
                  💡 <strong style="color:#c084fc;">Recommendation:</strong> {html_lib.escape(fn_rec)}
                </div>""", unsafe_allow_html=True)

        elif not fn_upload:
            st.markdown("""
            <div style="text-align:center; padding:3rem 1rem; color:#334155;">
              <div style="font-size:3rem;">📰</div>
              <div style="margin-top:0.5rem; font-size:0.9rem;">Upload a news image on the left to fact-check</div>
            </div>""", unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("<hr/>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align:center; color:#334155; font-size:0.8rem; padding:1rem 0;">
  AI Detection Hub · For research and educational use only
</div>
""", unsafe_allow_html=True)
