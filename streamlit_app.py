"""
CareerCompass — Streamlit Web App
===================================
Quick-deploy front-end for the recommender built in
CareerCompass_Recommender.ipynb. Reuses careers_data.py, recommender.py
and questionnaire.py as-is.

Run locally:
    streamlit run streamlit_app.py

Deploy for free:
    Push this folder (streamlit_app.py, .streamlit/config.toml,
    careers_data.py, recommender.py, questionnaire.py, requirements.txt)
    to a GitHub repo and connect it at https://share.streamlit.io
    (Streamlit Community Cloud) or as a Hugging Face Space (Streamlit SDK).

Notes on this version:
    - Layout is modelled on the National Career Advice Portal
      (ncap.careerhelp.org.za): a white header lockup, a green site nav
      bar with a multicolour underline strip, a search/category strip,
      and a hero banner paired with stacked action blocks.
    - Colors/font come from .streamlit/config.toml (Streamlit's native
      theming system) plus a small block of CSS for elements we create
      ourselves (safe — doesn't depend on Streamlit's internal DOM).
    - Four "pages": Home, Assessment (the questionnaire wizard +
      results), and Contact. The site nav bar switches between them.
    - Requires streamlit >= 1.28 (for st.container(border=True)).
"""
import streamlit as st
from careers_data import ALL_SUBJECTS
from questionnaire import (RIASEC_ITEMS, BIG5_ITEMS, CONSTRAINT_QUESTIONS,
                            score_riasec, score_big5, all_riasec_questions, all_big5_questions)
from recommender import generate_training_data, CareerRecommender, student_from_answers

st.set_page_config(page_title="CareerCompass", page_icon="🧭", layout="wide")

# ------------------------------------------------------------------------
# Palette — modelled on the reference site: green nav, navy action blocks,
# peach search strip, teal "welcome" ribbon, multicolour underline strip.
# ------------------------------------------------------------------------
NAV_GREEN = "#2F7A4F"
NAV_GRAY_BG = "#EFEFEF"
NAV_TEXT = "#4A4A4A"
NAVY_DARK = "#26344A"
PEACH_BG = "#F4E8DA"
TEAL = "#4FB8AE"
INK = "#242423"
INK_SOFT = "#5A6B78"
LINE = "#DDE0E3"
PALE_BLUE = "#EAF2F8"
STRIP_COLORS = ["#2F7A4F", "#3B7FB5", "#D9822B", "#E8C93B"]

# Fill these in with your real details before deploying.
CONTACT_PHONE = "+27 00 000 0000"
CONTACT_EMAIL = "hello@careercompass.co.za"
# Optional: paths/URLs to real screenshots of the app in action.
SCREENSHOT_1 = None
SCREENSHOT_2 = None

st.markdown(f"""
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
    .cc-serif {{ font-family: 'Fraunces', serif; }}
    .cc-question {{ font-size: 0.95rem; color: #262730; margin-bottom: 0.2rem; }}
    /* Backstop against dark mode: some browsers/OSes force a dark
       Streamlit theme regardless of config.toml. Pin white/ink here too
       so header text never disappears against a black background. */
    .stApp, body, html {{
        background-color: #FFFFFF !important;
        color: {INK} !important;
    }}
    /* Force full-width layout — Streamlit's "wide" mode still caps
       .block-container at a max-width by default. */
    .block-container {{
        max-width: 100% !important;
        padding-left: 2.5rem !important;
        padding-right: 2.5rem !important;
        padding-top: 1.5rem !important;
    }}
    .cc-badge {{
        display: inline-block; background: {PALE_BLUE}; color: {NAVY_DARK};
        border-radius: 999px; padding: 0.2rem 0.75rem; font-size: 0.82rem;
        font-weight: 600; margin: 0.15rem 0.35rem 0.15rem 0;
    }}
    /* Header lockup */
    .cc-header-title {{
        text-align: center; text-transform: uppercase; letter-spacing: 0.04em;
        font-weight: 700; font-size: 1.15rem; color: {INK}; padding-top: 0.6rem;
    }}
    .cc-wordmark span {{ font-family: 'Fraunces', serif; font-weight: 700; font-size: 1.5rem; }}
    .cc-wordmark {{ text-align: right; }}
    .cc-tagline {{ text-align: right; font-size: 0.72rem; color: {INK_SOFT}; margin-top: -0.2rem; }}
    .cc-logo-caption {{ font-size: 0.72rem; color: {INK_SOFT}; line-height: 1.15; }}
    /* Multicolour underline strip below the nav bar */
    .cc-strip {{ display: flex; height: 5px; margin-bottom: 1.3rem; }}
    .cc-strip div {{ flex: 1; }}
    /* Search / category strip */
    .cc-searchbar {{
        background: {PEACH_BG}; border-radius: 10px; padding: 0.9rem 1.1rem;
        margin-bottom: 1.2rem;
    }}
    /* Hero welcome ribbon */
    .cc-hero-panel {{
        background: linear-gradient(135deg, {NAV_GREEN} 0%, {NAVY_DARK} 100%);
        border-radius: 12px; position: relative; height: 260px;
        display: flex; align-items: center; justify-content: center;
        overflow: hidden;
    }}
    .cc-hero-ribbon {{
        background: {TEAL}; color: #FFFFFF; font-weight: 700; font-size: 1.4rem;
        letter-spacing: 0.08em; padding: 0.9rem 3rem; text-align: center;
        transform: rotate(-2deg); box-shadow: 0 6px 14px rgba(0,0,0,0.15);
    }}
    /* Stacked navy action blocks */
    .cc-action-block {{
        background: {NAVY_DARK}; color: #FFFFFF; border-radius: 8px;
        padding: 0.95rem 1.1rem; margin-bottom: 0.65rem; text-align: center;
        font-weight: 600; letter-spacing: 0.04em; font-size: 0.92rem;
        border-bottom: 3px solid {TEAL};
    }}
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_recommender():
    df = generate_training_data(n_per_career=45)
    rec = CareerRecommender()
    rec.fit(df)
    return rec


STEPS = ["Interests", "Personality", "Marks", "Situation"]
NAV_ITEMS = ["Home", "Assessment", "Results", "Contact Us"]

if "page" not in st.session_state:
    st.session_state.page = "home"
if "step" not in st.session_state:
    st.session_state.step = 0
if "answers" not in st.session_state:
    st.session_state.answers = {}
if "max_reached" not in st.session_state:
    st.session_state.max_reached = 0
if "flash" not in st.session_state:
    st.session_state.flash = None


def goto(i):
    st.session_state.step = i
    st.session_state.max_reached = max(st.session_state.max_reached, i)


def has_complete_answers():
    a = st.session_state.answers
    required = {"riasec", "big5", "marks", "budget_level", "duration_pref"}
    return required.issubset(a.keys())


def rating_grid(questions, key_prefix):
    """Render questions as compact 1-5 number-input cards, three per row."""
    answers = {}
    cols = st.columns(3)
    for i, q in enumerate(questions):
        with cols[i % 3]:
            with st.container(border=True):
                st.markdown(f'<div class="cc-question">{q}</div>', unsafe_allow_html=True)
                answers[q] = st.number_input(
                    q, min_value=1, max_value=5, value=3, step=1,
                    key=f"{key_prefix}_{i}", label_visibility="collapsed"
                )
    st.caption("1 = not at all · 5 = a great deal")
    return answers


# ============================================================================
# HEADER — logo lockup left, page title centre, wordmark + tagline right
# ============================================================================
h_left, h_mid, h_right = st.columns([1, 2, 1])
with h_left:
    st.markdown(
        '<div style="font-size:2.2rem; line-height:1;">🎓</div>'
        '<div class="cc-logo-caption"><b>Career<br>Compass</b><br>self-help tool</div>',
        unsafe_allow_html=True
    )
with h_mid:
    st.markdown('<div class="cc-header-title">The Career Compass Portal</div>', unsafe_allow_html=True)
with h_right:
    st.markdown(
        '<div class="cc-wordmark" style="padding-right:1.2rem; margin-top:1.6rem;">'
        '<span style="color:#2F7A4F;">C</span><span style="color:#3B7FB5;">areer</span>'
        '<span style="color:#D9822B;">Com</span><span style="color:#E8C93B;">pass</span>'
        '</div>'
        '<div class="cc-tagline" style="padding-right:1.2rem;">Navigate your future. Choose your path.</div>',
        unsafe_allow_html=True
    )

st.write("")

# ============================================================================
# SCREENSHOTS — sit right below the header/logo lockup
# ============================================================================
shot_col1, shot_col2 = st.columns(2)
for shot_col, shot_path, caption in (
    (shot_col1, SCREENSHOT_1, "The questionnaire"),
    (shot_col2, SCREENSHOT_2, "Your results"),
):
    with shot_col:
        with st.container(border=True):
            if shot_path:
                st.image(shot_path, use_container_width=True)
            else:
                st.markdown(
                    f'<div style="height:160px; display:flex; align-items:center; '
                    f'justify-content:center; color:{INK_SOFT}; background:{PALE_BLUE}; '
                    f'border-radius:10px; font-size:0.9rem;">📸 Add a screenshot here</div>',
                    unsafe_allow_html=True
                )

st.write("")

# ============================================================================
# SITE NAV BAR — green active tab, gray inactive, multicolour underline
# ============================================================================
nav_cols = st.columns(len(NAV_ITEMS))
for i, (col, label) in enumerate(zip(nav_cols, NAV_ITEMS)):
    with col:
        target = ["home", "assessment", "results", "contact"][i]
        is_active = (st.session_state.page == target)
        btn_type = "primary" if is_active else "secondary"
        if st.button(label.upper(), key=f"nav_{i}", type=btn_type, use_container_width=True):
            if target == "results" and not has_complete_answers():
                st.session_state.flash = "Complete the assessment first to see your results."
                st.session_state.page = "assessment"
                st.session_state.step = max(st.session_state.step, 0)
            elif target == "results":
                st.session_state.page = "assessment"
                st.session_state.step = 4
            elif target == "assessment":
                st.session_state.page = "assessment"
            else:
                st.session_state.page = target
            st.rerun()

st.markdown(
    f'<div class="cc-strip">{"".join(f"<div style=\'background:{c};\'></div>" for c in STRIP_COLORS)}</div>',
    unsafe_allow_html=True
)

if st.session_state.flash:
    st.warning(st.session_state.flash)
    st.session_state.flash = None

# ============================================================================
# HOME PAGE
# ============================================================================
if st.session_state.page == "home":
    # ---- Category / search strip ----
    st.markdown('<div class="cc-searchbar">', unsafe_allow_html=True)
    s1, s2, s3 = st.columns([1.2, 3, 0.6])
    with s1:
        section_choice = st.selectbox("Jump to", ["Select a section"] + STEPS, label_visibility="collapsed")
    with s2:
        st.text_input("Search", placeholder="Search careers or subjects (coming soon)", label_visibility="collapsed")
    with s3:
        if st.button("🔍", use_container_width=True) and section_choice != "Select a section":
            st.session_state.page = "assessment"
            st.session_state.step = STEPS.index(section_choice)
            st.session_state.max_reached = max(st.session_state.max_reached, STEPS.index(section_choice))
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # ---- Description line ----
    st.markdown(
        f'<p style="text-align:center; color:{INK_SOFT}; max-width:50rem; margin:0 auto 1.4rem auto;">'
        'CareerCompass is an online self-help tool designed to facilitate informed career and '
        'study decisions. It looks at your interests, personality, academic results, and '
        'real-world circumstances, then explains why each recommendation makes sense for you.'
        '</p>',
        unsafe_allow_html=True
    )

    # ---- Hero banner + stacked action blocks ----
    hero_col, action_col = st.columns([2.3, 1])
    with hero_col:
        st.markdown(f"""
        <div class="cc-hero-panel">
            <div class="cc-hero-ribbon">WELCOME</div>
        </div>
        """, unsafe_allow_html=True)
    with action_col:
        if st.button("🎯  TAKE THE ASSESSMENT", key="act1", use_container_width=True):
            st.session_state.page = "assessment"
            st.session_state.step = 0
            st.rerun()
        if st.button("📊  MY RESULTS", key="act2", use_container_width=True):
            if has_complete_answers():
                st.session_state.page = "assessment"
                st.session_state.step = 4
            else:
                st.session_state.flash = "Complete the assessment first to see your results."
                st.session_state.page = "assessment"
                st.session_state.step = max(st.session_state.step, 0)
            st.rerun()
        if st.button("🧭  WHAT WE OFFER", key="act3", use_container_width=True):
            st.session_state.page = "contact"
            st.rerun()

    st.write("")
    conf_col1, conf_col2 = st.columns([1, 2])
    with conf_col1:
        st.markdown(f"""
        <svg viewBox="0 0 220 220" xmlns="http://www.w3.org/2000/svg">
            <circle cx="110" cy="95" r="55" fill="{PALE_BLUE}"/>
            <circle cx="110" cy="80" r="30" fill="{NAV_GREEN}"/>
            <rect x="80" y="108" width="60" height="55" rx="20" fill="{NAV_GREEN}"/>
            <text x="45" y="55" font-size="30" fill="{TEAL}" font-family="Fraunces, serif">?</text>
            <text x="150" y="45" font-size="24" fill="{NAVY_DARK}" font-family="Fraunces, serif">?</text>
            <text x="35" y="130" font-size="22" fill="{NAVY_DARK}" font-family="Fraunces, serif">?</text>
            <text x="165" y="140" font-size="28" fill="{TEAL}" font-family="Fraunces, serif">?</text>
        </svg>
        """, unsafe_allow_html=True)
    with conf_col2:
        st.markdown('<h3 class="cc-serif">Feeling unsure about which path to take?</h3>', unsafe_allow_html=True)
        st.write(
            "So many bright learners get stuck between subjects, marks, and a dozen well-meaning "
            "opinions. CareerCompass gives you one clear, personalised place to start."
        )

    st.write("")
    st.markdown('<h3 class="cc-serif">Words to carry with you</h3>', unsafe_allow_html=True)
    quotes = [
        ("It always seems impossible until it's done.", "Nelson Mandela"),
        ("You have to dream before your dreams can come true.", "A.P.J. Abdul Kalam"),
        ("Education is the passport to the future.", "Malcolm X"),
        ("Life is like riding a bicycle. To keep your balance, you must keep moving.", "Albert Einstein"),
    ]
    q_cols = st.columns(4)
    for q_col, (quote, author) in zip(q_cols, quotes):
        with q_col:
            with st.container(border=True):
                st.markdown(f'<div style="font-size:0.9rem; font-style:italic; color:{INK_SOFT};">"{quote}"</div>',
                            unsafe_allow_html=True)
                st.markdown(f'<div style="font-size:0.82rem; font-weight:600; color:{NAVY_DARK}; margin-top:0.5rem;">'
                            f'— {author}</div>', unsafe_allow_html=True)

# ============================================================================
# CONTACT PAGE
# ============================================================================
elif st.session_state.page == "contact":
    with st.container(border=True):
        st.markdown('<h3 class="cc-serif">Contact us</h3>', unsafe_allow_html=True)
        cc1, cc2 = st.columns(2)
        cc1.markdown(f"📞 **Phone**\n\n{CONTACT_PHONE}")
        cc2.markdown(f"✉️ **Email**\n\n{CONTACT_EMAIL}")

    st.write("")
    st.warning(
        "CareerCompass offers general self-help guidance only. It does not replace advice from "
        "a qualified career counsellor, teacher, or psychologist — please use it as a starting "
        "point for further conversation, not a final decision."
    )

# ============================================================================
# ASSESSMENT PAGE — questionnaire wizard + results
# ============================================================================
else:
    # ---- Step tab bar (Interests / Personality / Marks / Situation / Results) ----
    all_labels = STEPS + ["Results"]
    tab_cols = st.columns(len(all_labels))
    for i, (col, name) in enumerate(zip(tab_cols, all_labels)):
        with col:
            is_active = (i == st.session_state.step)
            is_unlocked = (i <= st.session_state.max_reached)
            is_done = (i < st.session_state.step)
            prefix = "● " if is_active else ("✓ " if is_done else "")
            label = f"{prefix}{i + 1}. {name}"
            btn_type = "primary" if is_active else "secondary"
            if st.button(label, key=f"tab_{i}", type=btn_type, disabled=not is_unlocked, use_container_width=True):
                st.session_state.step = i
                st.rerun()
    st.markdown(f'<div style="border-bottom:2px solid {LINE}; margin: -0.4rem 0 1.2rem 0;"></div>', unsafe_allow_html=True)

    if st.session_state.step == 0:
        # ---- Step 0: Interests ----
        st.markdown('<h3 class="cc-serif">1. Your interests</h3>', unsafe_allow_html=True)
        st.caption("How much do you enjoy each kind of activity?")
        with st.form("step_interests"):
            riasec_answers = rating_grid(all_riasec_questions(), "riasec")
            next_clicked = st.form_submit_button("Continue →", type="primary", use_container_width=True)
        if next_clicked:
            st.session_state.answers["riasec"] = riasec_answers
            goto(1)
            st.rerun()

    elif st.session_state.step == 1:
        # ---- Step 1: Personality ----
        st.markdown('<h3 class="cc-serif">2. Your personality</h3>', unsafe_allow_html=True)
        st.caption("Rate how well each statement describes you.")
        with st.form("step_personality"):
            big5_answers = rating_grid(all_big5_questions(), "big5")
            c1, c2 = st.columns([1, 3])
            back_clicked = c1.form_submit_button("← Back")
            next_clicked = c2.form_submit_button("Continue →", type="primary", use_container_width=True)
        if back_clicked:
            goto(0)
            st.rerun()
        if next_clicked:
            st.session_state.answers["big5"] = big5_answers
            goto(2)
            st.rerun()

    elif st.session_state.step == 2:
        # ---- Step 2: Marks ----
        st.markdown('<h3 class="cc-serif">3. Your academic marks (%)</h3>', unsafe_allow_html=True)
        st.caption("Enter your most recent percentage mark for each subject.")
        with st.form("step_marks"):
            marks = {}
            cols = st.columns(3)
            for i, subj in enumerate(sorted(ALL_SUBJECTS)):
                with cols[i % 3]:
                    marks[subj] = st.number_input(subj, 0, 100, 55, key=f"mark_{subj}")
            c1, c2 = st.columns([1, 3])
            back_clicked = c1.form_submit_button("← Back")
            next_clicked = c2.form_submit_button("Continue →", type="primary", use_container_width=True)
        if back_clicked:
            goto(1)
            st.rerun()
        if next_clicked:
            st.session_state.answers["marks"] = marks
            goto(3)
            st.rerun()

    elif st.session_state.step == 3:
        # ---- Step 3: Situation ----
        st.markdown('<h3 class="cc-serif">4. Your practical situation</h3>', unsafe_allow_html=True)
        st.caption("This helps us recommend paths that are realistic for you.")
        with st.form("step_situation"):
            budget_opts = CONSTRAINT_QUESTIONS["budget_level"]["options"]
            duration_opts = CONSTRAINT_QUESTIONS["duration_pref"]["options"]
            sit_col1, sit_col2 = st.columns(2)
            with sit_col1:
                with st.container(border=True):
                    budget_level = st.radio(CONSTRAINT_QUESTIONS["budget_level"]["question"],
                                             options=list(budget_opts.keys()), format_func=lambda k: budget_opts[k])
            with sit_col2:
                with st.container(border=True):
                    duration_pref = st.radio(CONSTRAINT_QUESTIONS["duration_pref"]["question"],
                                              options=list(duration_opts.keys()), format_func=lambda k: duration_opts[k])
            c1, c2 = st.columns([1, 3])
            back_clicked = c1.form_submit_button("← Back")
            next_clicked = c2.form_submit_button("See my results →", type="primary", use_container_width=True)
        if back_clicked:
            goto(2)
            st.rerun()
        if next_clicked:
            st.session_state.answers["budget_level"] = budget_level
            st.session_state.answers["duration_pref"] = duration_pref
            goto(4)
            st.rerun()

    else:
        # ---- Step 4: Results ----
        if not has_complete_answers():
            st.warning("Complete the assessment first to see your results.")
            if st.button("Start the assessment"):
                st.session_state.step = 0
                st.rerun()
        else:
            recommender = load_recommender()
            a = st.session_state.answers
            riasec_scores = score_riasec(a["riasec"])
            big5_scores = score_big5(a["big5"])
            student = student_from_answers(a["marks"], riasec_scores, big5_scores,
                                            a["budget_level"], a["duration_pref"])
            results = recommender.recommend(student, top_n=5)

            st.markdown('<h3 class="cc-serif">🎯 Your top career matches</h3>', unsafe_allow_html=True)
            st.caption("Ranked by overall fit across your interests, personality, marks, and circumstances.")

            for i, r in enumerate(results, 1):
                c = r["career_obj"]
                pct = r["final_score"] * 100
                with st.container(border=True):
                    col_title, col_score = st.columns([3, 1])
                    with col_title:
                        st.markdown(f'<div class="cc-serif" style="font-size:1.15rem; font-weight:700; color:{NAVY_DARK};">'
                                    f'{i}. {r["career"]}</div>', unsafe_allow_html=True)
                    with col_score:
                        st.metric("Match", f"{pct:.0f}%", label_visibility="collapsed")
                    st.progress(min(max(r["final_score"], 0.0), 1.0))

                    with st.expander("Why this fits, and what's next", expanded=(i == 1)):
                        st.write(r["explanation"])
                        st.markdown(f"**What it involves:** {c['description']}")
                        st.markdown(
                            f'<span class="cc-badge">{c["sector"]} · {c["seta"]}</span>'
                            f'<span class="cc-badge">{c["duration_years"]} years study</span>'
                            f'<span class="cc-badge">R{c["salary_entry"]:,}/yr entry</span>',
                            unsafe_allow_html=True
                        )
                        st.markdown("**Next steps:**")
                        for step in c["next_steps"]:
                            st.markdown(f"- {step}")

            st.write("")
            if st.button("↺ Start over"):
                st.session_state.step = 0
                st.session_state.answers = {}
                st.session_state.max_reached = 0
                st.rerun()
