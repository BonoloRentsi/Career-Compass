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


@st.cache_resource
def load_recommender():
    df = generate_training_data(n_per_career=45)
    rec = CareerRecommender()
    rec.fit(df)
    return rec


st.title("🧭 CareerCompass")
st.caption("Personalised, explainable career guidance for South African youth.")

recommender = load_recommender()

with st.form("questionnaire"):
    st.subheader("1. Your interests")
    riasec_answers = {}
    for q in all_riasec_questions():
        riasec_answers[q] = st.slider(q, 1, 5, 3)

    st.subheader("2. Your personality")
    big5_answers = {}
    for q in all_big5_questions():
        big5_answers[q] = st.slider(q, 1, 5, 3)

    st.subheader("3. Your academic marks (%)")
    marks = {}
    cols = st.columns(2)
    for i, subj in enumerate(sorted(ALL_SUBJECTS)):
        with cols[i % 2]:
            marks[subj] = st.number_input(subj, 0, 100, 55)

    st.subheader("4. Your practical situation")
    budget_opts = CONSTRAINT_QUESTIONS["budget_level"]["options"]
    duration_opts = CONSTRAINT_QUESTIONS["duration_pref"]["options"]
    budget_level = st.radio(CONSTRAINT_QUESTIONS["budget_level"]["question"],
                             options=list(budget_opts.keys()), format_func=lambda k: budget_opts[k])
    duration_pref = st.radio(CONSTRAINT_QUESTIONS["duration_pref"]["question"],
                              options=list(duration_opts.keys()), format_func=lambda k: duration_opts[k])

    submitted = st.form_submit_button("Get my recommendations", type="primary")

if submitted:
    riasec_scores = score_riasec(riasec_answers)
    big5_scores = score_big5(big5_answers)
    student = student_from_answers(marks, riasec_scores, big5_scores, budget_level, duration_pref)
    results = recommender.recommend(student, top_n=5)

    st.header("🎯 Your Top Career Matches")
    for i, r in enumerate(results, 1):
        c = r["career_obj"]
        with st.expander(f"{i}. {r['career']} — {r['final_score']*100:.0f}% match", expanded=(i == 1)):
            st.write(r["explanation"])
            st.markdown(f"**What it involves:** {c['description']}")
            st.markdown(f"**Sector:** {c['sector']} ({c['seta']})  |  **Study length:** {c['duration_years']} years  "
                        f"|  **Est. entry salary:** R{c['salary_entry']:,}/year")
            st.markdown("**Next steps:**")
            for step in c["next_steps"]:
                st.markdown(f"- {step}")
