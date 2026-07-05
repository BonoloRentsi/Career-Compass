"""
CareerCompass — Streamlit Web App
===================================
Quick-deploy front-end for the recommender built in
CareerCompass_Recommender.ipynb. Reuses careers_data.py, recommender.py
and questionnaire.py as-is.
Run locally:
    streamlit run streamlit_app.py
Deploy for free:
    Push this folder (streamlit_app.py, careers_data.py, recommender.py,
    questionnaire.py, requirements.txt) to a GitHub repo and connect it at
    https://share.streamlit.io (Streamlit Community Cloud) or as a
    Hugging Face Space (Streamlit SDK).
"""
import streamlit as st
from careers_data import ALL_SUBJECTS
from questionnaire import (RIASEC_ITEMS, BIG5_ITEMS, CONSTRAINT_QUESTIONS,
                            score_riasec, score_big5, all_riasec_questions, all_big5_questions)
from recommender import generate_training_data, CareerRecommender, student_from_answers

st.set_page_config(page_title="CareerCompass", page_icon="🧭", layout="centered")

# ----------------------------------------------------------------------------
# Design system — palette, type, and component styling
# ----------------------------------------------------------------------------
# Deep navy + warm ochre ("compass needle") on a soft, warm-grey field.
# Fraunces (serif, characterful) for headings, Inter for body/UI text.
NAVY = "#1B3A4B"
NAVY_DEEP = "#122A38"
OCHRE = "#E0972D"
OCHRE_DARK = "#B5741A"
SAGE = "#4A7C59"
CANVAS = "#F6F4EF"
CARD = "#FFFFFF"
INK = "#242423"
INK_SOFT = "#5C6670"
LINE = "#E4E0D6"

st.markdown(f"""
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
        color: {INK};
    }}
    .stApp {{
        background-color: {CANVAS};
    }}
    /* Hide default Streamlit chrome for a cleaner, product-like feel */
    #MainMenu, footer {{visibility: hidden;}}

    h1, h2, h3 {{
        font-family: 'Fraunces', serif;
        color: {NAVY_DEEP};
        letter-spacing: -0.01em;
    }}

    /* ---- Hero header ---- */
    .cc-hero {{
        background: linear-gradient(135deg, {NAVY} 0%, {NAVY_DEEP} 100%);
        border-radius: 18px;
        padding: 2.6rem 2.2rem 2.2rem 2.2rem;
        margin-bottom: 1.8rem;
        color: #F4F2EC;
        position: relative;
        overflow: hidden;
    }}
    .cc-hero::after {{
        content: "";
        position: absolute;
        right: -60px; top: -60px;
        width: 220px; height: 220px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(224,151,45,0.35) 0%, rgba(224,151,45,0) 70%);
    }}
    .cc-hero h1 {{
        color: #FBF9F4;
        font-size: 2.3rem;
        font-weight: 700;
        margin: 0 0 0.35rem 0;
    }}
    .cc-hero p {{
        color: #C9D2D6;
        font-size: 1.02rem;
        margin: 0;
        max-width: 34rem;
    }}
    .cc-eyebrow {{
        text-transform: uppercase;
        letter-spacing: 0.14em;
        font-size: 0.72rem;
        font-weight: 600;
        color: {OCHRE};
        margin-bottom: 0.6rem;
    }}

    /* ---- Section step cards ---- */
    .cc-step-label {{
        display: flex;
        align-items: center;
        gap: 0.65rem;
        margin: 1.6rem 0 0.9rem 0;
    }}
    .cc-step-num {{
        display: flex;
        align-items: center;
        justify-content: center;
        width: 30px; height: 30px;
        border-radius: 8px;
        background: {NAVY};
        color: #FBF9F4;
        font-family: 'Fraunces', serif;
        font-weight: 600;
        font-size: 0.95rem;
        flex-shrink: 0;
    }}
    .cc-step-title {{
        font-family: 'Fraunces', serif;
        font-size: 1.25rem;
        font-weight: 600;
        color: {NAVY_DEEP};
    }}
    .cc-step-sub {{
        color: {INK_SOFT};
        font-size: 0.9rem;
        margin: -0.5rem 0 0.8rem 2.55rem;
    }}

    /* ---- Card container look for form blocks ---- */
    div[data-testid="stForm"] {{
        background: {CARD};
        border: 1px solid {LINE};
        border-radius: 16px;
        padding: 1.8rem 1.9rem;
    }}

    hr {{ border-color: {LINE}; }}

    /* ---- Sliders / inputs accent ---- */
    div[data-baseweb="slider"] > div > div > div > div {{
        background-color: {OCHRE} !important;
    }}
    .stSlider [data-baseweb="thumb"] {{
        border-color: {OCHRE_DARK} !important;
    }}
    div[data-testid="stNumberInput"] input {{
        border-radius: 8px;
    }}
    .stRadio label {{
        color: {INK};
    }}

    /* ---- Primary submit button ---- */
    button[kind="primaryFormSubmit"], button[kind="primary"] {{
        background-color: {OCHRE} !important;
        border: none !important;
        color: {NAVY_DEEP} !important;
        font-weight: 700 !important;
        border-radius: 10px !important;
        padding: 0.7rem 1.4rem !important;
    }}
    button[kind="primaryFormSubmit"]:hover, button[kind="primary"]:hover {{
        background-color: {OCHRE_DARK} !important;
        color: #FBF9F4 !important;
    }}

    /* ---- Results ---- */
    .cc-results-title {{
        font-family: 'Fraunces', serif;
        font-weight: 700;
        color: {NAVY_DEEP};
        font-size: 1.7rem;
        margin: 2rem 0 0.3rem 0;
    }}
    .cc-results-sub {{
        color: {INK_SOFT};
        margin-bottom: 1.2rem;
        font-size: 0.95rem;
    }}
    .cc-match-bar-track {{
        background: {LINE};
        border-radius: 999px;
        height: 8px;
        width: 100%;
        margin: 0.3rem 0 0.9rem 0;
        overflow: hidden;
    }}
    .cc-match-bar-fill {{
        height: 100%;
        border-radius: 999px;
        background: linear-gradient(90deg, {OCHRE} 0%, {SAGE} 100%);
    }}
    .cc-meta-row {{
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem 1.4rem;
        color: {INK_SOFT};
        font-size: 0.92rem;
        margin: 0.4rem 0 1rem 0;
    }}
    .cc-meta-row b {{ color: {INK}; }}
    div[data-testid="stExpander"] {{
        background: {CARD};
        border: 1px solid {LINE};
        border-radius: 14px;
        margin-bottom: 0.8rem;
    }}
    div[data-testid="stExpander"] summary {{
        font-family: 'Fraunces', serif;
        font-weight: 600;
        font-size: 1.05rem;
        color: {NAVY_DEEP};
    }}
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_recommender():
    df = generate_training_data(n_per_career=45)
    rec = CareerRecommender()
    rec.fit(df)
    return rec


# ----------------------------------------------------------------------------
# Hero
# ----------------------------------------------------------------------------
st.markdown("""
<div class="cc-hero">
    <div class="cc-eyebrow">Career guidance, personalised</div>
    <h1>🧭 CareerCompass</h1>
    <p>Answer a few honest questions about your interests, personality, marks, and
    circumstances — we'll match you to career paths that genuinely fit, and explain why.</p>
</div>
""", unsafe_allow_html=True)

recommender = load_recommender()


def step_header(number, title, subtitle):
    st.markdown(f"""
    <div class="cc-step-label">
        <div class="cc-step-num">{number}</div>
        <div class="cc-step-title">{title}</div>
    </div>
    <div class="cc-step-sub">{subtitle}</div>
    """, unsafe_allow_html=True)


with st.form("questionnaire"):
    step_header(1, "Your interests", "How much do you enjoy each kind of activity? 1 = not at all, 5 = a great deal.")
    riasec_answers = {}
    for q in all_riasec_questions():
        riasec_answers[q] = st.slider(q, 1, 5, 3)

    st.divider()
    step_header(2, "Your personality", "Rate how well each statement describes you.")
    big5_answers = {}
    for q in all_big5_questions():
        big5_answers[q] = st.slider(q, 1, 5, 3)

    st.divider()
    step_header(3, "Your academic marks (%)", "Enter your most recent percentage mark for each subject.")
    marks = {}
    cols = st.columns(2)
    for i, subj in enumerate(sorted(ALL_SUBJECTS)):
        with cols[i % 2]:
            marks[subj] = st.number_input(subj, 0, 100, 55)

    st.divider()
    step_header(4, "Your practical situation", "This helps us recommend paths that are realistic for you.")
    budget_opts = CONSTRAINT_QUESTIONS["budget_level"]["options"]
    duration_opts = CONSTRAINT_QUESTIONS["duration_pref"]["options"]
    budget_level = st.radio(CONSTRAINT_QUESTIONS["budget_level"]["question"],
                             options=list(budget_opts.keys()), format_func=lambda k: budget_opts[k])
    duration_pref = st.radio(CONSTRAINT_QUESTIONS["duration_pref"]["question"],
                              options=list(duration_opts.keys()), format_func=lambda k: duration_opts[k])

    st.write("")
    submitted = st.form_submit_button("Get my recommendations", type="primary", use_container_width=True)

if submitted:
    riasec_scores = score_riasec(riasec_answers)
    big5_scores = score_big5(big5_answers)
    student = student_from_answers(marks, riasec_scores, big5_scores, budget_level, duration_pref)
    results = recommender.recommend(student, top_n=5)

    st.markdown('<div class="cc-results-title">🎯 Your Top Career Matches</div>', unsafe_allow_html=True)
    st.markdown('<div class="cc-results-sub">Ranked by overall fit across your interests, personality, marks, and circumstances.</div>', unsafe_allow_html=True)

    for i, r in enumerate(results, 1):
        c = r["career_obj"]
        pct = r["final_score"] * 100
        with st.expander(f"{i}. {r['career']} — {pct:.0f}% match", expanded=(i == 1)):
            st.markdown(f"""
            <div class="cc-match-bar-track">
                <div class="cc-match-bar-fill" style="width:{pct:.0f}%;"></div>
            </div>
            """, unsafe_allow_html=True)
            st.write(r["explanation"])
            st.markdown(f"**What it involves:** {c['description']}")
            st.markdown(f"""
            <div class="cc-meta-row">
                <span><b>Sector:</b> {c['sector']} ({c['seta']})</span>
                <span><b>Study length:</b> {c['duration_years']} years</span>
                <span><b>Est. entry salary:</b> R{c['salary_entry']:,}/year</span>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("**Next steps:**")
            for step in c["next_steps"]:
                st.markdown(f"- {step}")
