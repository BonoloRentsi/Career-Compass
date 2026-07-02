"""
CareerCompass Questionnaire
============================
Short Likert-scale (1-5) quiz that operationalises the RIASEC interest
model and the Big Five personality traits, plus academic marks and
practical constraints. This is the layer a real web front-end would
collect from the user before calling the recommender.
"""

RIASEC_ITEMS = {
    "R": ["I enjoy fixing or building things with my hands.",
          "I'd rather work outdoors or with tools/machines than sit at a desk all day."],
    "I": ["I like figuring out how things work or solving puzzles.",
          "I enjoy science experiments or researching a topic deeply."],
    "A": ["I enjoy drawing, music, writing or other creative expression.",
          "I like coming up with original ideas rather than following a fixed method."],
    "S": ["I enjoy helping, teaching or caring for other people.",
          "I'd rather work in a team helping others than work alone."],
    "E": ["I enjoy leading a group or convincing people of an idea.",
          "I like taking initiative and starting new projects or ventures."],
    "C": ["I enjoy organising information, schedules or records.",
          "I prefer clear rules and structured tasks over ambiguity."],
}

BIG5_ITEMS = {
    "openness": ["I enjoy learning about new and unusual topics.",
                 "I like trying new approaches rather than sticking to routine."],
    "conscientiousness": ["I plan ahead and follow through on tasks.",
                           "I pay close attention to detail and accuracy."],
    "extraversion": ["I feel energised being around other people.",
                      "I speak up easily in group settings."],
    "agreeableness": ["I try to keep peace and support others' needs.",
                       "I find it easy to trust and cooperate with people."],
    "neuroticism": ["I get stressed easily under pressure.",
                     "My mood changes quickly when things go wrong."],
}

CONSTRAINT_QUESTIONS = {
    "budget_level": {
        "question": "What is your realistic funding access for further study?",
        "options": {1: "Very limited — need free/low-cost routes (TVET, learnerships, bursaries only)",
                    2: "Moderate — NSFAS/loan or part-funded is workable",
                    3: "Good — can access full university fees via bursary, loan or family support"}
    },
    "duration_pref": {
        "question": "How long are you willing/able to study before earning an income?",
        "options": {1: "Short — up to 2 years", 2: "Medium — 3 to 4 years", 3: "Long — 5+ years"}
    },
}


def likert_to_score(value):
    """Map a 1-5 Likert response to a 0-1 scale."""
    return (float(value) - 1) / 4.0


def score_riasec(answers):
    """answers: dict item_text -> 1-5 rating. Returns dict R..C -> 0-1."""
    scores = {}
    for dim, items in RIASEC_ITEMS.items():
        vals = [likert_to_score(answers[i]) for i in items if i in answers]
        scores[dim] = sum(vals) / len(vals) if vals else 0.5
    return scores


def score_big5(answers):
    scores = {}
    for trait, items in BIG5_ITEMS.items():
        vals = [likert_to_score(answers[i]) for i in items if i in answers]
        scores[trait] = sum(vals) / len(vals) if vals else 0.5
    return scores


def all_riasec_questions():
    return [q for items in RIASEC_ITEMS.values() for q in items]


def all_big5_questions():
    return [q for items in BIG5_ITEMS.values() for q in items]
