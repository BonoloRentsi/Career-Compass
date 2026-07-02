
# 🧭 CareerCompass — ML-Powered Career Guidance for South African Youth

**Problem:** Millions of SA children, matric leavers and unemployed youth lack access to
qualified career counsellors, leading to mismatched career choices, high dropout rates and
wasted potential.

**Solution:** CareerCompass collects a student's **academic marks**, **RIASEC interests**,
**Big Five personality traits**, and **practical constraints** (budget, study duration) through
a short questionnaire, then returns **personalised, explainable career recommendations** with
concrete next steps — mapped to South African subjects (NSC/APS), qualification pathways, and
SETA sectors.

## How this notebook is organised
1. **Career knowledge base** — 53 SA-relevant careers curated in the spirit of O\*NET (RIASEC +
   skill/personality profiles) and SETA sector taxonomies.
2. **Synthetic training data** — since no public, individually-labelled "student → ideal career"
   dataset exists for South Africa, we generate a realistic synthetic training set anchored to
   the career knowledge base (a standard technique when bootstrapping recommender systems).
3. **Hybrid recommendation model**:
   - *Content-based layer*: cosine similarity between the student's interest/personality vectors
     and each career's ideal profile, plus rule-based subject and budget/duration matching.
   - *ML layer*: a `RandomForestClassifier` learns to predict the most suitable **career sector**
     from a student's full profile, and its probabilities are blended in to re-rank results and
     to provide global feature-importance interpretability.
4. **Explanation engine** — turns every recommendation into a plain-English reason.
5. **Evaluation** — train/test accuracy, top-3 accuracy, feature importances.
6. **Interactive demo** — fill in the questionnaire and get live recommendations.
7. **Deployment notes** — how to turn this into the web app described in the brief.

> 📌 This notebook is fully self-contained — no external downloads required — so it runs
> end-to-end on Kaggle with **Settings → Internet: off** if needed.
