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
    page_title="Obituary Analyzer — Useless Projects Hackathon",
    page_icon="🪦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;900&display=swap');
  
  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

  .hero-title {
    font-size: 4rem; font-weight: 900; text-align: center;
    background: linear-gradient(135deg, #e0e0e0, #ffffff);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin-bottom: 0;
  }
  .hero-tagline {
    text-align: center; font-size: 1.15rem; color: #999;
    font-style: italic; margin-top: 4px; margin-bottom: 8px;
  }
  .hero-sub {
    text-align: center; font-size: 1rem; color: #bbb; margin-bottom: 30px;
  }
  .section-title {
    font-size: 1.4rem; font-weight: 700; margin-top: 2rem; margin-bottom: 0.5rem;
    color: #e0e0e0;
  }
  .demo-banner {
    background: linear-gradient(135deg, #3a1a00, #5a2d00);
    border: 1px solid #ff8c00; border-radius: 8px;
    padding: 12px 18px; text-align: center;
    color: #ffcc80; font-weight: 600; margin-bottom: 18px;
  }
  .page-card {
    background: rgba(255,255,255,0.04); border-radius: 8px;
    padding: 10px 14px; margin-bottom: 6px;
    border-left: 4px solid #4CAF50;
  }
  .page-card-warn { border-left-color: #ff9800; }
  .insight-box {
    background: linear-gradient(135deg, rgba(255,75,75,0.1), rgba(255,150,0,0.05));
    border: 1px solid rgba(255,75,75,0.3); border-radius: 12px;
    padding: 24px 28px; text-align: center; margin: 20px 0;
  }
  .insight-text { font-size: 1.3rem; color: #f0f0f0; font-style: italic; }
  .final-msg {
    text-align: center; padding: 30px; margin-top: 20px;
    background: rgba(255,255,255,0.03); border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.08);
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
    st.markdown('<div class="hero-title">🪦 OBITUARY ANALYZER</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hero-tagline">"We scanned an entire newspaper just to tell you who died alphabetically."</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="hero-sub">Technically impressive. Completely unnecessary.</div>',
        unsafe_allow_html=True
    )

# ─────────────────────────────────────────────
#  STEP 1 — UPLOAD
# ─────────────────────────────────────────────
if st.session_state.step == 'upload':
    render_header()
    st.divider()

    col_upload, col_demo = st.columns([3, 1], gap="large")

    with col_upload:
        st.markdown("### 📰 Upload a Newspaper PDF")
        st.caption("The application will automatically scan every page and detect obituary/death-related sections.")

        uploaded = st.file_uploader(
            "Drop your newspaper PDF here", type=["pdf"], label_visibility="collapsed"
        )

        if uploaded:
            pdf_bytes = uploaded.read()
            total_pages, err = get_page_count(pdf_bytes)
            if err:
                st.error(err)
            elif total_pages == 0:
                st.error("⚠️ The uploaded newspaper appears to have no readable pages.")
            else:
                st.success(f"✓ Newspaper uploaded — **{total_pages} pages** detected")
                st.info(f"📋 Every page will be scanned automatically. No page selection needed!")

                if st.button("🔍 Analyze Entire Newspaper", type="primary", use_container_width=True):
                    st.session_state.pdf_bytes = pdf_bytes
                    st.session_state.total_pages = total_pages
                    st.session_state.is_demo = False
                    st.session_state.step = 'scanning'
                    st.rerun()

    with col_demo:
        st.markdown("### 🚀 Hackathon Demo Mode")
        st.caption("No PDF? WiFi failing? OCR broken? Use pre-loaded newspaper data to demo the full pipeline instantly.")
        st.markdown("---")
        if st.button("▶ Load Demo Newspaper", type="secondary", use_container_width=True):
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

    for page_num, img, direct_text in extract_all_pages(st.session_state.pdf_bytes):
        status_text.text(f"Scanning page {page_num}/{total}...")
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
        "Add missing entries with the ＋ row at the bottom."
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
    st.caption("We have successfully converted a newspaper into statistics that nobody asked for.")
    st.divider()

    # ── Scan summary ──
    st.markdown('<div class="section-title">📰 Newspaper Scan Summary</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Pages Scanned", total_pages)
    c2.metric("Pages with Death-related Content", relevant_count)
    c3.metric("Total Entries Detected", stats['total_people'])
    st.divider()

    # ── Key metrics ──
    st.markdown('<div class="section-title">📊 Key Statistics</div>', unsafe_allow_html=True)
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("👤 People Analyzed", stats['total_people'])
    m2.metric("📈 Average Age", stats['average_age'])
    m3.metric("📉 Median Age", stats['median_age'])
    m4.metric("⬇️ Youngest", stats['youngest'])
    m5.metric("⬆️ Oldest", stats['oldest'])
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

        st.markdown(
            f"### 🏆 Most Reported Age Group: **{stats['most_common_group']}** "
            f"({stats['most_common_group_count']} people)"
        )

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
    st.markdown('<div class="section-title">🔤 Alphabetical Obituary List</div>', unsafe_allow_html=True)

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

    # ── Useless statistics ──
    st.markdown('<div class="section-title">🎰 Completely Useless Statistics</div>', unsafe_allow_html=True)

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

    # ── Useless insight ──
    st.markdown(
        f'<div class="insight-box"><p class="insight-text">💡 {insight}</p></div>',
        unsafe_allow_html=True
    )
    st.divider()

    # ── Uselessness score ──
    st.markdown('<div class="section-title">🎯 Completely Unscientific Uselessness Score</div>', unsafe_allow_html=True)
    st.caption("Based on number of pages unnecessarily scanned, entries extracted, and statistics generated. Scientifically meaningless.")

    score_col, _ = st.columns([2, 3])
    with score_col:
        st.markdown(f"### {useless_score} / 100")
        st.progress(useless_score / 100)
        st.caption(
            f"USELESSNESS: {useless_score}%   |   USEFULNESS: {100 - useless_score}%  \n"
            f"You scanned {total_pages} pages to extract {stats['total_people']} entries and sort them alphabetically."
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
<h3>🎉 Congratulations!</h3>
<p>You have successfully converted an entire newspaper into statistics that nobody asked for.</p>
<br/>
<p><em>Was it useful?</em> <strong>Probably not.</strong></p>
<p><em>Was it technically impressive?</em> <strong>We hope so.</strong></p>
<br/>
<p style="color: #aaa; font-size: 0.9rem;">"We turned an entire newspaper into data. Nobody asked us to."</p>
</div>
    """, unsafe_allow_html=True)

    st.markdown("")
    if st.button("🔄 Analyze Another Newspaper", type="primary", on_click=reset_app):
        pass
