import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io

from src.pdf_processor import extract_all_pages, get_page_count
from src.ocr import run_ocr
from src.cleaner import clean_ocr_text
from src.page_detector import score_page, is_relevant_page, LABEL_NOT_RELEVANT
from src.extractor import extract_obituaries
from src.duplicate_detector import find_duplicates
from src.analyzer import (
    calculate_statistics, generate_useless_insight,
    calculate_uselessness_score, assign_age_group, AGE_GROUPS
)
from src.utils import get_demo_data, DEMO_TOTAL_PAGES, DEMO_DETECTED_PAGES

# ─────────────────────────────────────────────
#  PAGE CONFIG & GLOBAL CSS
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="The Tombstone Tournament — Useless Projects Hackathon",
    page_icon="🪦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700;900&family=Inter:wght@300;400;500;600&display=swap');
  
  html, body, [class*="css"], .stMarkdown, .stText, p, span, div, h1, h2, h3, h4, h5, h6, label, .stMetric * { 
    font-family: 'Inter', sans-serif; 
    color: #000000 !important; 
  }

  .stButton button {
    background-color: #0f172a !important;
    border: 2px solid #0f172a !important;
    border-radius: 8px !important;
    transition: all 0.3s ease;
  }
  
  .stButton button:hover {
    background-color: #334155 !important;
    border-color: #334155 !important;
    transform: translateY(-2px);
  }

  .stButton button p, .stButton button span, .stButton button div {
    color: #ffffff !important;
    font-weight: 700 !important;
  }
  
  .stApp {
    background: linear-gradient(135deg, #e0c3fc 0%, #8ec5fc 100%) !important; /* Pleasant soft gradient */
    background-attachment: fixed !important;
  }

  h1, h2, h3 { font-family: 'Outfit', sans-serif; font-weight: 900; letter-spacing: -0.5px; }
  
  .hero-title {
    font-family: 'Outfit', sans-serif; font-weight: 900;
    font-size: 4.5rem; text-align: center;
    color: #000000 !important;
    margin-bottom: 0; line-height: 1.2;
  }

  .hero-tagline {
    text-align: center; font-size: 1.4rem; color: #334155;
    margin-top: 10px; font-weight: 600; letter-spacing: 0.5px;
  }
  
  .hero-sub {
    text-align: center; font-size: 1.1rem; color: #475569;
    margin-bottom: 40px; font-weight: 500;
  }

  .feature-box {
    background: rgba(255, 255, 255, 0.7);
    border: 2px solid rgba(255,255,255,0.8); 
    border-radius: 16px; padding: 24px; 
    text-align: center; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    backdrop-filter: blur(12px); box-shadow: 0 8px 32px rgba(0,0,0,0.1);
  }
  .feature-box:hover { transform: translateY(-4px); border-color: rgba(236, 72, 153, 0.5); box-shadow: 0 10px 30px rgba(236,72,153,0.3); }
  .feature-box h3 { font-size: 1.5rem; color: #0f172a; margin-bottom: 12px; font-weight: 700; }
  .feature-box p { font-size: 1rem; color: #1e293b; line-height: 1.6; font-weight: 500; }

  .section-title {
    font-family: 'Outfit', sans-serif;
    font-size: 1.6rem; font-weight: 700; margin-top: 2.5rem; margin-bottom: 1rem;
    color: #0f172a; border-bottom: 2px solid rgba(0,0,0,0.1); padding-bottom: 0.5rem;
  }
  
  .demo-banner {
    background: rgba(245, 158, 11, 0.1);
    border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 8px;
    padding: 12px 18px; text-align: center;
    color: #fbbf24; font-weight: 500; margin-bottom: 18px;
  }
  
  .page-card {
    background: rgba(255, 255, 255, 0.6); border-radius: 8px;
    padding: 12px 16px; margin-bottom: 8px;
    border: 1px solid rgba(255,255,255,0.8); border-left: 5px solid #ec4899;
    color: #0f172a; font-weight: 600;
  }
  .page-card-warn { border-left-color: #f59e0b; }
  
  .insight-box {
    background: rgba(255, 255, 255, 0.5);
    border: 2px dashed rgba(236, 72, 153, 0.4); border-radius: 12px;
    padding: 24px 28px; text-align: center; margin: 20px 0;
  }
  .insight-text { font-size: 1.2rem; color: #be185d; font-weight: 600; font-style: italic; }
  
  .final-msg {
    text-align: center; padding: 30px; margin-top: 20px;
    background: rgba(255, 255, 255, 0.7); border-radius: 16px;
    border: 1px solid rgba(255,255,255,0.8);
    color: #0f172a; box-shadow: 0 8px 32px rgba(0,0,0,0.1);
  }
  
  /* Premium Winner Box */
  .winner-container {
    text-align: center;
    padding: 45px 20px;
    margin: 24px 0;
    background: linear-gradient(135deg, rgba(251, 191, 36, 0.05), rgba(245, 158, 11, 0.15));
    border: 1px solid rgba(251, 191, 36, 0.4);
    border-radius: 20px;
    position: relative;
    overflow: hidden;
    backdrop-filter: blur(10px);
    box-shadow: 0 10px 40px rgba(245, 158, 11, 0.1), inset 0 0 20px rgba(251, 191, 36, 0.1);
  }
  .trophy-icon {
    font-size: 7rem;
    display: block;
    margin: 0 auto 15px auto;
    filter: drop-shadow(0 15px 25px rgba(245, 158, 11, 0.4));
    animation: float 4s ease-in-out infinite;
  }
  @keyframes float {
    0% { transform: translateY(0px); }
    50% { transform: translateY(-15px); }
    100% { transform: translateY(0px); }
  }
  .winner-title {
    font-size: 1.1rem;
    color: #fbbf24;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 8px;
    font-weight: 600;
  }
  .winner-text {
    font-size: 5.5rem;
    font-family: 'Outfit', sans-serif;
    font-weight: 900;
    color: #000000 !important;
    margin: 10px 0;
    line-height: 1.1;
  }
  .winner-sub {
    font-size: 1.1rem;
    color: #78350f;
    margin-top: 12px;
    font-weight: 600;
  }
  .popper-left, .popper-right {
    position: absolute;
    top: 50%;
    font-size: 4rem;
    animation: pop 0.5s infinite alternate;
  }
  .popper-left { left: 5%; transform: translateY(-50%) scaleX(-1); }
  .popper-right { right: 5%; transform: translateY(-50%); }
  @keyframes pop {
    0% { transform: translateY(-50%) scale(1) rotate(0deg); }
    100% { transform: translateY(-50%) scale(1.3) rotate(15deg); }
  }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  STATE MANAGEMENT
# ─────────────────────────────────────────────
STEPS = ['upload', 'scanning', 'review', 'dashboard']

def _init_state():
    defaults = {
        'step': 'upload',
        'pdf_bytes': None,
        'page_scores': [],       # list of {page, score, label, keyword_hits, age_patterns}
        'page_texts': {},        # {page_num: text}
        'selected_pages': [],    # page numbers the user wants to extract from
        'raw_entries': [],       # list of entry dicts before editing
        'final_df': None,
        'total_pages': 0,
        'is_demo': False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()

def reset_app():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    _init_state()

# ─────────────────────────────────────────────
#  SHARED HEADER
# ─────────────────────────────────────────────
def render_header():
    # Dynamic pleasant background colors for each page
    bg_colors = {
        'upload': 'linear-gradient(135deg, #e0c3fc 0%, #8ec5fc 100%)',
        'scanning': 'linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%)',
        'review': 'linear-gradient(135deg, #e0f2f1 0%, #80cbc4 100%)',
        'dashboard': 'linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%)'
    }
    current_bg = bg_colors.get(st.session_state.step, '#f8f9fa')
    st.markdown(f"<style>.stApp {{ background: {current_bg} !important; background-attachment: fixed !important; }}</style>", unsafe_allow_html=True)
    
    st.markdown('<div class="hero-title">ശവമത്സരം 🪦</div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="text-align: center; font-size: 2rem; font-family: \'Outfit\', sans-serif; font-weight: 800; color: #000000; margin-top: -5px; margin-bottom: 15px;">The Tombstone Tournament</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="hero-tagline">Advanced Document Processing and Insight Generation (Now with 10% more ghosts 👻)</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="hero-sub">AI-Powered Optical Character Recognition Pipeline 🔮</div>',
        unsafe_allow_html=True
    )

# ─────────────────────────────────────────────
#  STEP 1 — UPLOAD
# ─────────────────────────────────────────────
if st.session_state.step == 'upload':
    render_header()
    
    # Feature Boxes
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="feature-box"><h3>🔍 Precision OCR</h3><p>State-of-the-art text extraction from complex newspaper layouts to find the departed.</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="feature-box"><h3>⚡ High Performance</h3><p>Rapidly process hundreds of entries before you can say "Rest In Peace".</p></div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="feature-box"><h3>📊 Deep Analytics</h3><p>Automated demographic classification and morbid statistical reporting.</p></div>', unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    col_upload, col_demo = st.columns([1, 1], gap="large")

    with col_upload:
        st.markdown("<div style='background: rgba(255,255,255,0.7); padding: 24px; border-radius: 16px; border: 2px solid rgba(255,255,255,0.8); height: 100%; box-shadow: 0 8px 32px rgba(0,0,0,0.1); backdrop-filter: blur(10px);'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color: #0f172a; margin-top:0;'>Document Upload 📄</h3>", unsafe_allow_html=True)
        st.info("Upload a PDF document. The system will automatically classify and extract relevant data sections. 🧛", icon="🦇")

        uploaded = st.file_uploader(
            "Drop your newspaper PDF here", type=["pdf"], label_visibility="collapsed"
        )

        if uploaded:
            pdf_bytes = uploaded.read()
            total_pages, err = get_page_count(pdf_bytes)
            if err:
                st.error(err)
            elif total_pages == 0:
                st.error("⚠️ The uploaded document appears to be empty or unreadable.")
            else:
                st.success(f"✓ Document verified — {total_pages} pages detected.")
                st.info(f"System ready for full document analysis.")

                if st.button("Initialize Processing Pipeline", type="primary", use_container_width=True):
                    st.session_state.pdf_bytes = pdf_bytes
                    st.session_state.total_pages = total_pages
                    st.session_state.is_demo = False
                    st.session_state.step = 'scanning'
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with col_demo:
        st.markdown("<div style='background: rgba(255,255,255,0.7); padding: 24px; border-radius: 16px; border: 2px solid rgba(255,255,255,0.8); height: 100%; box-shadow: 0 8px 32px rgba(0,0,0,0.1); backdrop-filter: blur(10px);'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color: #0f172a; margin-top:0;'>Demo Environment ⚡</h3>", unsafe_allow_html=True)
        st.info("Evaluate system capabilities instantly using our pre-processed sample dataset. Skip the queue! ⚰️", icon="🔮")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Launch Interactive Demo", type="secondary", use_container_width=True):
            st.session_state.is_demo = True
            st.session_state.total_pages = DEMO_TOTAL_PAGES
            st.session_state.page_scores = [
                {"page": p["page"], "score": p["score"], "label": p["label"],
                 "keyword_hits": 12, "age_patterns": p["entries"], "name_patterns": p["entries"]}
                for p in DEMO_DETECTED_PAGES
            ]
            st.session_state.selected_pages = [p["page"] for p in DEMO_DETECTED_PAGES]
            st.session_state.raw_entries = get_demo_data().to_dict(orient='records')
            st.session_state.step = 'review'
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  STEP 2 — SCANNING ALL PAGES
# ─────────────────────────────────────────────
elif st.session_state.step == 'scanning':
    render_header()
    st.divider()

    total = st.session_state.total_pages
    st.markdown(f"### 🔎 Scanning Newspaper — {total} pages")

    progress_bar = st.progress(0)
    status_text = st.empty()
    page_results_container = st.container()

    page_scores = []
    page_texts = {}
    all_entries = []

    import random
    messages = [
        "Initializing OCR engine... 👁️",
        "Analyzing page structure... 📄",
        "Detecting layout components...",
        "Extracting relevant entities... 👻",
        "Normalizing tabular data...",
        "Applying regex validations... 💀",
        "Checking for ghosts in the machine... 🧛"
    ]

    for page_num, img, direct_text in extract_all_pages(st.session_state.pdf_bytes):
        msg = random.choice(messages)
        status_text.text(f"Scanning page {page_num}/{total}... {msg}")
        progress_bar.progress(page_num / total)

        # Use direct text if available, else OCR
        if direct_text and len(direct_text) > 50:
            text = direct_text
        elif img is not None:
            text = run_ocr(img)
        else:
            text = direct_text or ""

        cleaned = clean_ocr_text(text)
        page_texts[page_num] = cleaned

        score_result = score_page(cleaned)
        score_result['page'] = page_num
        page_scores.append(score_result)

    progress_bar.progress(1.0)
    status_text.text("✅ Scan complete! Identifying relevant pages...")

    # Store results
    st.session_state.page_scores = page_scores
    st.session_state.page_texts = page_texts

    # Filter relevant pages
    relevant = [p for p in page_scores if is_relevant_page(p)]
    st.session_state.selected_pages = [p['page'] for p in relevant]

    # Show results
    st.success(f"Scan complete! Found **{len(relevant)}** relevant page(s) out of {total}.")
    st.markdown("#### Detected Relevant Pages")
    st.caption("Uncheck a page if it was incorrectly classified.")

    new_selected = []
    for p in page_scores:
        if p['label'] == LABEL_NOT_RELEVANT:
            continue
        colour = "🟢" if p['score'] >= 70 else "🟡"
        label_text = f"{colour} **Page {p['page']}** — {p['label']} — {p['score']}% confidence"
        checked = st.checkbox(label_text, value=True, key=f"page_check_{p['page']}")
        if checked:
            new_selected.append(p['page'])
        st.caption(
            f"   Keywords: {p['keyword_hits']} hits · Age patterns: {p['age_patterns']} · Name patterns: {p['name_patterns']}"
        )

    if not page_scores or not any(p['label'] != LABEL_NOT_RELEVANT for p in page_scores):
        st.warning(
            "No obituary or death-related section was confidently detected.\n\n"
            "Possible reasons:\n"
            "- The newspaper uses a different format.\n"
            "- OCR quality is poor.\n"
            "- This edition may not contain obituary notices."
        )

    if new_selected:
        if st.button("📋 Extract Entries from Selected Pages", type="primary"):
            st.session_state.selected_pages = new_selected
            # Extract entries from selected pages
            entries = []
            for page_num in new_selected:
                text = page_texts.get(page_num, "")
                if text:
                    page_entries = extract_obituaries(text, page_num=page_num)
                    entries.extend(page_entries)

            if not entries:
                st.error(
                    "⚠️ No obituary entries were confidently detected on the selected pages.\n"
                    "Please check the page selection or try a clearer scan."
                )
            else:
                st.session_state.raw_entries = entries
                st.session_state.step = 'review'
                st.rerun()

    if st.button("← Start Over"):
        reset_app()
        st.rerun()

# ─────────────────────────────────────────────
#  STEP 3 — MANUAL REVIEW
# ─────────────────────────────────────────────
elif st.session_state.step == 'review':
    render_header()
    if st.session_state.is_demo:
        st.markdown(
            '<div class="demo-banner">⚠️ DEMO MODE — Using sample newspaper data</div>',
            unsafe_allow_html=True
        )
    st.divider()

    st.markdown("### 📋 Review Detected Entries")
    st.caption(
        "OCR is imperfect. Correct names, ages, or notice types. "
        "Remove incorrect rows using the row delete (🗑) on the left. "
        "Add missing souls with the ＋ row at the bottom. 🧟"
    )

    # Build display dataframe
    raw = st.session_state.raw_entries
    if isinstance(raw, list):
        df_raw = pd.DataFrame(raw)
    else:
        df_raw = raw.copy()

    # Ensure all columns are string-safe for the editor
    for col in ['Name', 'Age', 'Age_Source', 'Notice_Type', 'Location', 'Date']:
        if col in df_raw.columns:
            df_raw[col] = df_raw[col].astype(str)
    if 'Page' in df_raw.columns:
        df_raw['Page'] = df_raw['Page'].astype(str)
    if 'Confidence' in df_raw.columns:
        df_raw['Confidence'] = pd.to_numeric(df_raw['Confidence'], errors='coerce').fillna(0.5)

    # Highlight low-confidence entries
    low_conf = df_raw[df_raw.get('Confidence', pd.Series([1.0]*len(df_raw))) < 0.7] if 'Confidence' in df_raw.columns else pd.DataFrame()
    if not low_conf.empty:
        st.warning(f"⚠️ {len(low_conf)} entries have low confidence (< 70%). Please review them carefully.")

    # Duplicate detection
    raw_list = df_raw.to_dict(orient='records')
    dupes = find_duplicates(raw_list)
    if dupes:
        st.info(f"🔍 {len(dupes)} possible duplicate pair(s) detected. Review them below.")
        with st.expander("Show possible duplicates"):
            for i, j, sim in dupes:
                col1, col2, col3 = st.columns([3, 3, 1])
                e1, e2 = raw_list[i], raw_list[j]
                col1.write(f"**{e1['Name']}**, Age {e1['Age']}")
                col2.write(f"**{e2['Name']}**, Age {e2['Age']}")
                col3.write(f"{int(sim*100)}% similar")

    # Editable table
    notice_options = ["Obituary", "Death Notice", "Memorial", "Remembrance",
                      "Condolence", "Funeral Notice", "Tribute", "Unknown"]

    column_config = {
        "Name": st.column_config.TextColumn("Name", required=True),
        "Age": st.column_config.TextColumn("Age"),
        "Age_Source": st.column_config.SelectboxColumn(
            "Age Source", options=["direct", "calculated", "unknown"], default="direct"
        ),
        "Page": st.column_config.TextColumn("Page"),
        "Notice_Type": st.column_config.SelectboxColumn(
            "Notice Type", options=notice_options, default="Unknown"
        ),
        "Location": st.column_config.TextColumn("Location"),
        "Date": st.column_config.TextColumn("Date"),
        "Confidence": st.column_config.NumberColumn(
            "Confidence", min_value=0.0, max_value=1.0, format="%.2f"
        ),
    }

    edited_df = st.data_editor(
        df_raw,
        num_rows="dynamic",
        column_config=column_config,
        use_container_width=True,
        key="review_editor"
    )

    col_back, col_confirm = st.columns([1, 5])
    with col_back:
        if st.button("← Back"):
            st.session_state.step = 'scanning' if not st.session_state.is_demo else 'upload'
            st.rerun()
    with col_confirm:
        if st.button("✅ Confirm & Generate Dashboard", type="primary"):
            if edited_df.empty:
                st.error("No entries to analyze. Please add at least one entry.")
            else:
                st.session_state.final_df = edited_df
                st.session_state.step = 'dashboard'
                st.rerun()

# ─────────────────────────────────────────────
#  STEP 4 — DASHBOARD
# ─────────────────────────────────────────────
elif st.session_state.step == 'dashboard':
    df = st.session_state.final_df.copy()
    total_pages = st.session_state.total_pages
    relevant_count = len(st.session_state.selected_pages)
    is_demo = st.session_state.is_demo

    # ── Data prep ──
    # Sort alphabetically
    df['Name'] = df['Name'].astype(str)
    df['Age'] = df['Age'].astype(str)
    df = df.sort_values(by='Name', key=lambda c: c.str.lower()).reset_index(drop=True)
    df['Age_Group'] = df['Age'].apply(assign_age_group)

    stats = calculate_statistics(df, total_pages=total_pages, relevant_pages=relevant_count)
    useless_score = calculate_uselessness_score(df, total_pages)
    insight = generate_useless_insight(stats)

    # ── Header ──
    render_header()
    if is_demo:
        st.markdown(
            '<div class="demo-banner">⚠️ DEMO MODE — Using sample newspaper data</div>',
            unsafe_allow_html=True
        )
    st.markdown("## 🪦 ANALYSIS COMPLETE")
    st.caption("Document processing and statistical analysis completed successfully. 💀")
    st.divider()

    # ── Scan summary ──
    st.markdown('<div class="section-title">📰 Newspaper Scan Summary (Overview 👀)</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("📄 Total Pages Scanned 📚", f"{total_pages} Pages")
    c2.metric("☠️ Relevant Pages Found 🪦", f"{relevant_count} Pages")
    c3.metric("🧑‍🤝‍🧑 Total Entries Extracted 📊", f"{stats['total_people']} People")
    st.divider()

    # ── Key metrics ──
    st.markdown('<div class="section-title">📊 Key Statistics (The Details 🔍)</div>', unsafe_allow_html=True)
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("👤 Total People", f"{stats['total_people']} 🧑")
    m2.metric("📈 Average Age", f"{stats['average_age']} 🎂")
    m3.metric("📉 Median Age", f"{stats['median_age']} 📏")
    m4.metric("👶 Youngest", f"{stats['youngest']} Yrs")
    m5.metric("👴 Oldest", f"{stats['oldest']} Yrs")
    st.divider()

    # ── Grand Winner Announcement ──
    try:
        percentage = round((stats['most_common_group_count'] / stats['total_people']) * 100, 1) if stats['total_people'] > 0 else 0
    except Exception:
        percentage = 0

    winner_html = f"""
    <div class="winner-container" style="width: 100%; margin: 40px 0; padding: 60px 20px;">
        <div class="popper-left" style="font-size: 6rem;">🎉</div>
        <div class="trophy-icon" style="font-size: 8rem; margin-bottom: 20px;">🏆</div>
        <div class="winner-title" style="font-size: 1.5rem; color: #d97706; letter-spacing: 4px;">👑 CHAMPIONS OF THE AFTERLIFE 👑</div>
        <div class="winner-title" style="font-size: 1.2rem; color: #475569; margin-top: 10px;">The Primary Demographic Group Is...</div>
        <div class="winner-text" style="font-size: 7rem; margin: 20px 0; letter-spacing: -2px;">{stats['most_common_group']}</div>
        <div class="winner-sub" style="font-size: 1.8rem; color: #000; font-weight: 800;">{stats['most_common_group_count']} individuals recorded</div>
        <div class="winner-sub" style="font-size: 1.4rem; color: #dc2626; margin-top: 10px;">(That's {percentage}% of all entries!)</div>
        <div class="winner-sub" style="font-size: 1.2rem; color: #64748b; margin-top: 20px; font-style: italic;">✨ Statistically significant and completely unnecessary ✨</div>
        <div class="popper-right" style="font-size: 6rem;">🎉</div>
    </div>
    """
    st.markdown(winner_html, unsafe_allow_html=True)
    st.divider()

    # ── Age group chart + page breakdown ──
    col_chart, col_page = st.columns([3, 2], gap="large")

    with col_chart:
        st.markdown('<div class="section-title">📊 Age Group Distribution</div>', unsafe_allow_html=True)

        group_order = [g for g in AGE_GROUPS]
        group_counts = df['Age_Group'].value_counts().reindex(group_order, fill_value=0).reset_index()
        group_counts.columns = ['Age Group', 'Count']

        # Highlight the peak group
        max_count = group_counts['Count'].max()
        group_counts['Color'] = group_counts['Count'].apply(
            lambda c: '#ff4b4b' if c == max_count else '#5b8dee'
        )

        fig = px.bar(
            group_counts, x='Age Group', y='Count',
            text_auto=True, color='Color',
            color_discrete_map='identity',
        )
        fig.update_layout(
            showlegend=False, plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)', font_color='#ccc',
            xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.08)'),
            margin=dict(l=0, r=0, t=10, b=0)
        )
        st.plotly_chart(fig, use_container_width=True)



    with col_page:
        st.markdown('<div class="section-title">📄 Page-wise Entry Count</div>', unsafe_allow_html=True)
        page_breakdown = stats.get('page_breakdown', {})
        if page_breakdown:
            pb_df = pd.DataFrame(
                sorted(page_breakdown.items(), key=lambda x: -x[1]),
                columns=['Page', 'Entries']
            )
            pb_df['Page'] = pb_df['Page'].apply(lambda p: f"Page {p}")
            fig_p = px.bar(
                pb_df, x='Entries', y='Page', orientation='h',
                text_auto=True, color='Entries',
                color_continuous_scale='Reds'
            )
            fig_p.update_layout(
                showlegend=False, plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)', font_color='#ccc',
                coloraxis_showscale=False,
                margin=dict(l=0, r=0, t=10, b=0)
            )
            st.plotly_chart(fig_p, use_container_width=True)
        else:
            st.info("Page breakdown not available.")

    st.divider()

    # ── Alphabetical list with search/filter ──
    st.markdown("""<div class="section-title" style="font-size: 3rem; text-align: center; border-bottom: none; margin-bottom: 0;">👥 Today's Participants</div>""", unsafe_allow_html=True)
    st.markdown("""<p style="text-align: center; font-size: 1.2rem; font-weight: 500; color: #334155; margin-bottom: 2rem;">A comprehensive alphabetical registry of all individuals processed in the current session.</p>""", unsafe_allow_html=True)

    with st.expander("🔎 Search & Filter", expanded=False):
        f1, f2, f3, f4 = st.columns(4)
        search_name = f1.text_input("Search name", "")
        filter_group = f2.selectbox("Age Group", ["All"] + AGE_GROUPS)
        filter_page = f3.selectbox(
            "Page", ["All"] + sorted(df['Page'].unique().tolist()) if 'Page' in df.columns else ["All"]
        )
        filter_type = f4.selectbox(
            "Notice Type",
            ["All"] + (df['Notice_Type'].unique().tolist() if 'Notice_Type' in df.columns else [])
        )
        show_low_conf = st.checkbox("Show only low-confidence entries (< 70%)")

    display_df = df.copy()
    if search_name:
        display_df = display_df[display_df['Name'].str.contains(search_name, case=False, na=False)]
    if filter_group != "All":
        display_df = display_df[display_df['Age_Group'] == filter_group]
    if filter_page != "All" and 'Page' in display_df.columns:
        display_df = display_df[display_df['Page'].astype(str) == str(filter_page)]
    if filter_type != "All" and 'Notice_Type' in display_df.columns:
        display_df = display_df[display_df['Notice_Type'] == filter_type]
    if show_low_conf and 'Confidence' in display_df.columns:
        display_df = display_df[pd.to_numeric(display_df['Confidence'], errors='coerce') < 0.7]

    display_cols = [c for c in ['Name', 'Age', 'Age_Group', 'Page', 'Notice_Type', 'Confidence'] if c in display_df.columns]
    st.dataframe(display_df[display_cols], use_container_width=True, hide_index=True)
    st.caption(f"Showing {len(display_df)} of {len(df)} entries.")
    st.divider()

    # ── Advanced statistics ──
    st.markdown('<div class="section-title">🎰 Advanced Demographics</div>', unsafe_allow_html=True)

    u1, u2, u3, u4 = st.columns(4)
    u1.metric("🔠 Alphabetically First", stats.get('first_alpha', 'N/A'))
    u2.metric("🔡 Alphabetically Last", stats.get('last_alpha', 'N/A'))
    u3.metric("👴 People Above 80", stats.get('above_80', 0))
    u4.metric("🧑 People Below 60", stats.get('below_60', 0))

    u5, u6, u7, u8 = st.columns(4)
    u5.metric("📊 % Above 80", f"{stats.get('pct_above_80', 0)}%")
    u6.metric("🏆 Busiest Page", f"Page {stats.get('busiest_page', 'N/A')}")
    u7.metric("📋 Common Notice Type", stats.get('most_common_notice', 'N/A'))
    u8.metric("❓ Unknown Ages", stats.get('unknown_age_count', 0))
    st.divider()

    # ── Key Insight ──
    st.markdown(
        f'<div class="insight-box"><p class="insight-text">💡 {insight}</p></div>',
        unsafe_allow_html=True
    )
    st.divider()

    # ── Processing score ──
    st.markdown('<div class="section-title">🎯 Extraction Confidence Score</div>', unsafe_allow_html=True)
    st.caption("Calculated based on OCR fidelity and structural integrity of identified notices.")

    score_col, _ = st.columns([2, 3])
    with score_col:
        st.markdown(f"### {useless_score} / 100")
        st.progress(useless_score / 100)
        st.caption(
            f"CONFIDENCE: {useless_score}%   |   MARGIN OF ERROR: {100 - useless_score}%  \n"
            f"Processed {total_pages} pages to successfully extract {stats['total_people']} verified entities."
        )
    st.divider()

    # ── CSV Export ──
    st.markdown('<div class="section-title">⬇️ Export Data</div>', unsafe_allow_html=True)
    export_cols = [c for c in ['Name', 'Age', 'Age_Group', 'Page', 'Notice_Type', 'Location', 'Confidence'] if c in df.columns]
    csv_data = df[export_cols].to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download CSV",
        data=csv_data,
        file_name="obituary_analysis.csv",
        mime="text/csv",
    )
    st.divider()

    # ── Final message ──
    st.markdown("""
<div class="final-msg">
<h3>✅ Processing Complete ⚰️</h3>
<p>The document analysis pipeline has successfully concluded. All demographic data has been processed and buried safely in the database.</p>
</div>
    """, unsafe_allow_html=True)

    st.markdown("")
    if st.button("🔄 Analyze Another Newspaper", type="primary", on_click=reset_app):
        pass
