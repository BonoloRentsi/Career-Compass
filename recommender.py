"""
CareerCompass Recommender Engine
=================================
Hybrid architecture:
  1. CONTENT-BASED layer: cosine similarity between a student's RIASEC
     interest vector / personality vector and each career's ideal profile,
     plus a rule-based academic-subject match and a practical-constraints
     filter (budget, study duration).
  2. ML layer: a RandomForestClassifier trained on simulated student
     profiles (labelled by the content-based scorer acting as a weak
     supervisor, a common "distillation" pattern used when real labelled
     outcome data isn't available) predicts a probability distribution
     over career SECTORS. Sector probabilities are then used to re-rank
     and boost the content-based career scores, and the model's
     feature_importances_ give a global interpretability view.
  3. EXPLANATION layer: turns the numeric match into a plain-English
     reason string per recommendation.

This keeps the system interpretable (every recommendation can be traced
back to specific RIASEC dimensions, subjects and personality traits)
while still being "ML-powered" via the supervised sector classifier.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, top_k_accuracy_score
from sklearn.metrics.pairwise import cosine_similarity

from careers_data import CAREERS, RIASEC_KEYS, BIG5_KEYS, ALL_SUBJECTS

RNG = np.random.default_rng(42)


# ----------------------------------------------------------------------
# 1. SYNTHETIC STUDENT PROFILE GENERATION (for training the ML layer)
# ----------------------------------------------------------------------
def _sample_student(career_bias=None):
    """
    Sample one synthetic student. If career_bias is given (a career dict),
    the profile is generated *around* that career's ideal profile with
    noise, so the dataset contains a realistic mixture of "good fits" for
    every career alongside pure-random students. This avoids a purely
    self-referential labelling loop and gives the classifier real signal
    to learn from.
    """
    if career_bias is not None and RNG.random() < 0.7:
        riasec = {k: float(np.clip(career_bias["riasec"][k] + RNG.normal(0, 0.18), 0, 1))
                  for k in RIASEC_KEYS}
        personality = {k: float(np.clip(career_bias["personality"][k] + RNG.normal(0, 0.15), 0, 1))
                       for k in BIG5_KEYS}
        subjects = {}
        for s in ALL_SUBJECTS:
            base = career_bias["subjects"].get(s, 45)
            subjects[s] = float(np.clip(RNG.normal(base + 5, 15), 20, 100))
        budget_level = int(np.clip(career_bias["budget_level"] + RNG.integers(-1, 2), 1, 3))
    else:
        riasec = {k: float(RNG.uniform(0.1, 0.95)) for k in RIASEC_KEYS}
        personality = {k: float(RNG.uniform(0.15, 0.9)) for k in BIG5_KEYS}
        subjects = {s: float(np.clip(RNG.normal(55, 18), 20, 100)) for s in ALL_SUBJECTS}
        budget_level = int(RNG.integers(1, 4))

    duration_pref = int(RNG.integers(1, 4))  # 1=short(<=2y) 2=medium(3-4y) 3=long(5y+)
    location = RNG.choice(["urban", "peri-urban", "rural"])

    return dict(riasec=riasec, personality=personality, subjects=subjects,
                budget_level=budget_level, duration_pref=duration_pref, location=location)


def generate_training_data(n_per_career=40):
    rows = []
    for career in CAREERS:
        for _ in range(n_per_career):
            s = _sample_student(career_bias=career)
            rows.append({**_flatten_student(s), "career": career["name"], "sector": career["sector"]})
    # add pure-random ("undecided") students, labelled by best content-based match
    for _ in range(int(n_per_career * len(CAREERS) * 0.15)):
        s = _sample_student(career_bias=None)
        best = max(CAREERS, key=lambda c: _content_score(s, c)["total"])
        rows.append({**_flatten_student(s), "career": best["name"], "sector": best["sector"]})
    df = pd.DataFrame(rows)
    return df.sample(frac=1, random_state=42).reset_index(drop=True)


def _flatten_student(s):
    flat = {}
    for k in RIASEC_KEYS:
        flat[f"riasec_{k}"] = s["riasec"][k]
    for k in BIG5_KEYS:
        flat[f"big5_{k}"] = s["personality"][k]
    for subj in ALL_SUBJECTS:
        flat[f"subj_{subj}"] = s["subjects"][subj]
    flat["budget_level"] = s["budget_level"]
    flat["duration_pref"] = s["duration_pref"]
    flat["location"] = s["location"]
    return flat


FEATURE_COLS = (
    [f"riasec_{k}" for k in RIASEC_KEYS] +
    [f"big5_{k}" for k in BIG5_KEYS] +
    [f"subj_{s}" for s in ALL_SUBJECTS] +
    ["budget_level", "duration_pref"]
)


# ----------------------------------------------------------------------
# 2. CONTENT-BASED SCORING (interpretable layer, also used to label data)
# ----------------------------------------------------------------------
def _content_score(student, career):
    riasec_vec = np.array([student["riasec"][k] for k in RIASEC_KEYS]).reshape(1, -1)
    career_riasec_vec = np.array([career["riasec"][k] for k in RIASEC_KEYS]).reshape(1, -1)
    riasec_sim = float(cosine_similarity(riasec_vec, career_riasec_vec)[0, 0])

    pers_vec = np.array([student["personality"][k] for k in BIG5_KEYS]).reshape(1, -1)
    career_pers_vec = np.array([career["personality"][k] for k in BIG5_KEYS]).reshape(1, -1)
    pers_sim = float(cosine_similarity(pers_vec, career_pers_vec)[0, 0])

    # subject match: fraction of required subjects met at/above the minimum
    req = career["subjects"]
    if req:
        met = [1.0 if student["subjects"].get(subj, 0) >= min_mark else
               max(0.0, student["subjects"].get(subj, 0) / min_mark)
               for subj, min_mark in req.items()]
        subject_score = float(np.mean(met))
    else:
        subject_score = 0.8  # no hard subject requirement

    # constraint match: budget affordability + duration alignment
    budget_ok = 1.0 if student["budget_level"] >= career["budget_level"] else 0.4
    dur_bucket = 1 if career["duration_years"] <= 2 else (2 if career["duration_years"] <= 4 else 3)
    duration_ok = 1.0 if student["duration_pref"] == dur_bucket else (0.6 if abs(student["duration_pref"] - dur_bucket) == 1 else 0.3)
    constraint_score = 0.5 * budget_ok + 0.5 * duration_ok

    total = 0.40 * riasec_sim + 0.20 * pers_sim + 0.30 * subject_score + 0.10 * constraint_score
    return dict(total=total, riasec_sim=riasec_sim, pers_sim=pers_sim,
                subject_score=subject_score, constraint_score=constraint_score)


# ----------------------------------------------------------------------
# 3. ML MODEL (sector classifier)
# ----------------------------------------------------------------------
class CareerRecommender:
    def __init__(self):
        self.model = RandomForestClassifier(
            n_estimators=300, max_depth=14, min_samples_leaf=2,
            random_state=42, n_jobs=-1, class_weight="balanced"
        )
        self.le_sector = LabelEncoder()
        self.train_report = {}

    def fit(self, df):
        X = df[FEATURE_COLS].copy()
        y_sector = self.le_sector.fit_transform(df["sector"])
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_sector, test_size=0.2, random_state=42, stratify=y_sector
        )
        self.model.fit(X_train, y_train)
        y_pred = self.model.predict(X_test)
        proba = self.model.predict_proba(X_test)
        acc = accuracy_score(y_test, y_pred)
        present_labels = np.unique(y_train)
        top3 = top_k_accuracy_score(y_test, proba, k=3, labels=present_labels)
        self.train_report = dict(
            n_train=len(X_train), n_test=len(X_test),
            n_classes=len(self.le_sector.classes_),
            accuracy=acc, top3_accuracy=top3
        )
        return self.train_report

    def feature_importances(self, top_n=15):
        importances = pd.Series(self.model.feature_importances_, index=FEATURE_COLS)
        return importances.sort_values(ascending=False).head(top_n)

    def _sector_probabilities(self, student):
        x = pd.DataFrame([_flatten_student(student)])[FEATURE_COLS]
        proba = self.model.predict_proba(x)[0]
        return dict(zip(self.le_sector.classes_, proba))

    def recommend(self, student, top_n=5, apply_constraints=True):
        sector_proba = self._sector_probabilities(student)
        results = []
        for career in CAREERS:
            content = _content_score(student, career)
            ml_boost = sector_proba.get(career["sector"], 0.0)
            # blend: content-based score is primary (interpretable, precise to the
            # individual career) with the ML sector-probability as a re-ranking boost
            final_score = 0.75 * content["total"] + 0.25 * ml_boost
            results.append({
                "career": career["name"], "sector": career["sector"], "career_obj": career,
                "final_score": final_score, "ml_sector_confidence": ml_boost, **content
            })
        results.sort(key=lambda r: r["final_score"], reverse=True)

        if apply_constraints:
            affordable = [r for r in results if student["budget_level"] >= r["career_obj"]["budget_level"] - 1]
            ranked = affordable if len(affordable) >= top_n else results
        else:
            ranked = results

        top = ranked[:top_n]
        for r in top:
            r["explanation"] = _explain(student, r)
        return top


# ----------------------------------------------------------------------
# 4. EXPLANATION GENERATOR
# ----------------------------------------------------------------------
def _explain(student, result):
    career = result["career_obj"]
    reasons = []

    # top matching RIASEC dimension(s)
    diffs = {k: student["riasec"][k] * career["riasec"][k] for k in RIASEC_KEYS}
    top_dim = max(diffs, key=diffs.get)
    dim_names = dict(R="hands-on/practical work", I="investigating and analytical problem-solving",
                      A="creative and artistic expression", S="helping and working with people",
                      E="leading, persuading and enterprising activity", C="organised, detail-oriented work")
    if diffs[top_dim] > 0.3:
        reasons.append(f"Your interest profile strongly matches {dim_names[top_dim]}, "
                        f"which is central to this career (interest fit: {result['riasec_sim']*100:.0f}%).")

    # subjects
    req = career["subjects"]
    if req:
        met = [s for s, m in req.items() if student["subjects"].get(s, 0) >= m]
        short = [s for s, m in req.items() if student["subjects"].get(s, 0) < m]
        if met:
            reasons.append(f"You meet the marks needed in {', '.join(met)}.")
        if short:
            gap = ", ".join(f"{s} (need {m}%, currently {student['subjects'].get(s,0):.0f}%)"
                             for s, m in req.items() if s in short)
            reasons.append(f"You'll need to raise: {gap}.")
    else:
        reasons.append("This career has no strict subject cut-offs, widening access.")

    # personality
    if result["pers_sim"] > 0.85:
        reasons.append("Your personality traits closely align with people who thrive in this role.")

    # constraints
    if student["budget_level"] < career["budget_level"]:
        reasons.append("Note: this path is typically costlier — look into NSFAS, SETA or sector bursaries below.")
    else:
        reasons.append("This path fits within your indicated budget/funding access.")

    return " ".join(reasons)


def student_from_answers(academic_marks, riasec_scores, personality_scores, budget_level, duration_pref, location="urban"):
    """Convenience constructor turning raw questionnaire answers into the
    student-profile dict the recommender expects."""
    subjects = {s: float(academic_marks.get(s, 45)) for s in ALL_SUBJECTS}
    riasec = {k: float(riasec_scores.get(k, 0.5)) for k in RIASEC_KEYS}
    personality = {k: float(personality_scores.get(k, 0.5)) for k in BIG5_KEYS}
    return dict(riasec=riasec, personality=personality, subjects=subjects,
                budget_level=int(budget_level), duration_pref=int(duration_pref), location=location)


if __name__ == "__main__":
    print("Generating synthetic training data...")
    df = generate_training_data(n_per_career=40)
    print(df.shape)

    rec = CareerRecommender()
    report = rec.fit(df)
    print("Train report:", report)

    print("\nTop feature importances:")
    print(rec.feature_importances(10))

    demo_student = student_from_answers(
        academic_marks={"Mathematics": 78, "Physical Sciences": 74, "Life Sciences": 70, "English": 65},
        riasec_scores={"R": 0.3, "I": 0.9, "A": 0.2, "S": 0.6, "E": 0.3, "C": 0.5},
        personality_scores={"openness": 0.6, "conscientiousness": 0.85, "extraversion": 0.4,
                             "agreeableness": 0.6, "neuroticism": 0.2},
        budget_level=2, duration_pref=2
    )
    recs = rec.recommend(demo_student, top_n=5)
    print("\nDemo recommendations:")
    for r in recs:
        print(f"- {r['career']} (score={r['final_score']:.2f}, sector={r['sector']})")
        print(f"    {r['explanation']}")
