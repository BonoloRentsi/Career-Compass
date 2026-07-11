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
    - Colors/font come from .streamlit/config.toml (Streamlit's native
      theming system) rather than injected CSS targeting internal
      Streamlit classes, which breaks across Streamlit versions.
    - There are two "pages": a Home landing page (about the tool, sample
      screenshots, quotes, contact info, disclaimer) and the App itself
      (the questionnaire wizard + results). A ☰ Menu popover switches
      between them.
    - The questionnaire is a short multi-step wizard instead of one long
      scrolling form, so no single screen has more than ~10 questions.
    - Requires streamlit >= 1.28 (for st.container(border=True) and
      st.popover).
"""
import streamlit as st
from careers_data import ALL_SUBJECTS
from questionnaire import (RIASEC_ITEMS, BIG5_ITEMS, CONSTRAINT_QUESTIONS,
                            score_riasec, score_big5, all_riasec_questions, all_big5_questions)
from recommender import generate_training_data, CareerRecommender, student_from_answers

st.set_page_config(page_title="CareerCompass", page_icon="🧭", layout="wide")

GREEN = "#1E8A5F"
BLUE = "#0F4C81"
BLUE_DEEP = "#0A3A63"
INK_SOFT = "#5A6B78"
LINE = "#DDE6EA"
CARD_BG = "#FFFFFF"
PALE_BLUE = "#EAF2F8"

# Fill these in with your real details before deploying.
CONTACT_PHONE = "+27 00 000 0000"
CONTACT_EMAIL = "hello@careercompass.co.za"
# Optional: paths/URLs to real screenshots of the app in action.
# Leave as None to show a placeholder card instead.
SCREENSHOT_1 = "Screenshot 2026-06-11 163438.png"
SCREENSHOT_2 = None

# Minimal CSS: only imports a font and styles elements we create ourselves
# (safe — doesn't depend on Streamlit's internal DOM structure).
st.markdown(f"""
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
    .cc-serif {{ font-family: 'Fraunces', serif; }}
    .cc-hero {{
        background: linear-gradient(135deg, {BLUE} 0%, {BLUE_DEEP} 100%);
        border-radius: 16px;
        padding: 2.2rem 2rem;
        color: #FFFFFF;
        margin-bottom: 1.6rem;
    }}
    .cc-hero h1 {{
        font-family: 'Fraunces', serif;
        font-size: 2rem;
        font-weight: 700;
        margin: 0 0 0.3rem 0;
        color: #FFFFFF;
    }}
    .cc-hero p {{ margin: 0; color: #DCE7EE; font-size: 1rem; max-width: 34rem; }}
    .cc-eyebrow {{
        text-transform: uppercase; letter-spacing: 0.13em; font-size: 0.7rem;
        font-weight: 600; color: {GREEN}; margin-bottom: 0.5rem;
    }}
    .cc-badge {{
        display: inline-block; background: {PALE_BLUE}; color: {BLUE_DEEP};
        border-radius: 999px; padding: 0.2rem 0.75rem; font-size: 0.82rem;
        font-weight: 600; margin: 0.15rem 0.35rem 0.15rem 0;
    }}
    .cc-question {{ font-size: 0.95rem; color: #262730; margin-bottom: 0.2rem; }}
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_recommender():
    df = generate_training_data(n_per_career=45)
    rec = CareerRecommender()
    rec.fit(df)
    return rec


STEPS = ["Interests", "Personality", "Marks", "Situation", "Results"]

if "page" not in st.session_state:
    st.session_state.page = "home"
if "step" not in st.session_state:
    st.session_state.step = 0
if "answers" not in st.session_state:
    st.session_state.answers = {}
if "max_reached" not in st.session_state:
    st.session_state.max_reached = 0


def goto(i):
    st.session_state.step = i
    st.session_state.max_reached = max(st.session_state.max_reached, i)


def start_assessment():
    st.session_state.page = "app"
    st.session_state.step = 0
    st.session_state.max_reached = 0


def go_home():
    st.session_state.page = "home"


def hero():
    st.markdown("""
    <div class="cc-hero">
        <div class="cc-eyebrow">Career guidance, personalised</div>
        <h1>🧭 CareerCompass</h1>
        <p>Answer a few honest questions about your interests, personality, marks, and
        circumstances — we'll match you to career paths that genuinely fit, and explain why.</p>
    </div>
    """, unsafe_allow_html=True)


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


# ----------------------------------------------------------------------------
# Menu — simple popover nav, matches the "hamburger" in the wireframe
# ----------------------------------------------------------------------------
menu_l, menu_r = st.columns([6, 1])
with menu_r:
    with st.popover("☰ Menu", use_container_width=True):
        if st.button("🏠 Home", use_container_width=True):
            go_home()
            st.rerun()
        if st.button("🚀 Start assessment", use_container_width=True):
            start_assessment()
            st.rerun()

# ============================================================================
# HOME PAGE
# ============================================================================
if st.session_state.page == "home":
    hero()

    st.button("🚀 Start your journey", type="primary", use_container_width=True,
              on_click=start_assessment)

    st.write("")
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
                        f'<div style="height:180px; display:flex; align-items:center; '
                        f'justify-content:center; color:{INK_SOFT}; background:{PALE_BLUE}; '
                        f'border-radius:10px; font-size:0.9rem;">📸 Add a screenshot here</div>',
                        unsafe_allow_html=True
                    )
                st.caption(caption)

    st.write("")
    with st.container(border=True):
        st.markdown('<h3 class="cc-serif">What is CareerCompass?</h3>', unsafe_allow_html=True)
        st.write(
            "CareerCompass is a self-help tool that helps you explore career paths that fit "
            "who you are — not just your marks. It looks at your interests, your personality, "
            "your academic results, and your real-world circumstances (budget and time), then "
            "explains why each recommendation makes sense for you."
        )

    st.write("")
    conf_col1, conf_col2 = st.columns([1, 2])
    with conf_col1:
        st.markdown(f"""
        <svg viewBox="0 0 220 220" xmlns="http://www.w3.org/2000/svg">
            <circle cx="110" cy="95" r="55" fill="{PALE_BLUE}"/>
            <circle cx="110" cy="80" r="30" fill="{BLUE}"/>
            <rect x="80" y="108" width="60" height="55" rx="20" fill="{BLUE}"/>
            <text x="45" y="55" font-size="30" fill="{GREEN}" font-family="Fraunces, serif">?</text>
            <text x="150" y="45" font-size="24" fill="{BLUE_DEEP}" font-family="Fraunces, serif">?</text>
            <text x="35" y="130" font-size="22" fill="{BLUE_DEEP}" font-family="Fraunces, serif">?</text>
            <text x="165" y="140" font-size="28" fill="{GREEN}" font-family="Fraunces, serif">?</text>
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
                st.markdown(f'<div style="font-size:0.82rem; font-weight:600; color:{BLUE_DEEP}; margin-top:0.5rem;">'
                            f'— {author}</div>', unsafe_allow_html=True)

    st.write("")
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
# QUESTIONNAIRE / RESULTS APP
# ============================================================================
else:
    hero()

    # Top tab bar — click a completed step to jump back to it.
    tab_cols = st.columns(len(STEPS))
    for i, (col, name) in enumerate(zip(tab_cols, STEPS)):
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
                    st.markdown(f'<div class="cc-serif" style="font-size:1.15rem; font-weight:700; color:{BLUE_DEEP};">'
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
