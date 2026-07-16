"""
CareerCompass Questionnaire
============================
Short Likert-scale (1-5) quiz that operationalises the RIASEC interest
model and the Big Five personality traits, plus academic marks and
practical constraints. This is the layer a real web front-end would
collect from the user before calling the recommender.
"""

RIASEC_ITEMS = {
"R": ["I ENJOY FIXING OR BUILDING THINGS WITH MY HANDS.",
      "I'D RATHER WORK OUTDOORS OR WITH TOOLS/MACHINES THAN SIT AT A DESK ALL DAY."],

"I": ["I LIKE FIGURING OUT HOW THINGS WORK OR SOLVING PUZZLES.",
      "I ENJOY SCIENCE EXPERIMENTS OR RESEARCHING A TOPIC DEEPLY."],

"A": ["I ENJOY DRAWING, MUSIC, WRITING OR OTHER CREATIVE EXPRESSION.",
      "I LIKE COMING UP WITH ORIGINAL IDEAS RATHER THAN FOLLOWING A FIXED METHOD."],

"S": ["I ENJOY HELPING, TEACHING OR CARING FOR OTHER PEOPLE.",
      "I'D RATHER WORK IN A TEAM HELPING OTHERS THAN WORK ALONE."],

"E": ["I ENJOY LEADING A GROUP OR CONVINCING PEOPLE OF AN IDEA.",
      "I LIKE TAKING INITIATIVE AND STARTING NEW PROJECTS OR VENTURES."],

"C": ["I ENJOY ORGANISING INFORMATION, SCHEDULES OR RECORDS.",
      "I PREFER CLEAR RULES AND STRUCTURED TASKS OVER AMBIGUITY."],
}

BIG5_ITEMS = {
"openness": ["I ENJOY LEARNING ABOUT NEW AND UNUSUAL TOPICS.",
             "I LIKE TRYING NEW APPROACHES RATHER THAN STICKING TO ROUTINE."],

"conscientiousness": ["I PLAN AHEAD AND FOLLOW THROUGH ON TASKS.",
                      "I PAY CLOSE ATTENTION TO DETAIL AND ACCURACY."],

"extraversion": ["I FEEL ENERGISED BEING AROUND OTHER PEOPLE.",
                 "I SPEAK UP EASILY IN GROUP SETTINGS."],

"agreeableness": ["I TRY TO KEEP PEACE AND SUPPORT OTHERS' NEEDS.",
                  "I FIND IT EASY TO TRUST AND COOPERATE WITH PEOPLE."],

"neuroticism": ["I GET STRESSED EASILY UNDER PRESSURE.",
                "MY MOOD CHANGES QUICKLY WHEN THINGS GO WRONG."],
}

CONSTRAINT_QUESTIONS = {
"budget_level": {
    "question": "WHAT IS YOUR REALISTIC FUNDING ACCESS FOR FURTHER STUDY?",
    "options": {
        1: "VERY LIMITED — NEED FREE/LOW-COST ROUTES (TVET, LEARNERSHIPS, BURSARIES ONLY)",
        2: "MODERATE — NSFAS/LOAN OR PART-FUNDED IS WORKABLE",
        3: "GOOD — CAN ACCESS FULL UNIVERSITY FEES VIA BURSARY, LOAN OR FAMILY SUPPORT"
    }
},

"duration_pref": {
    "question": "HOW LONG ARE YOU WILLING/ABLE TO STUDY BEFORE EARNING AN INCOME?",
    "options": {
        1: "SHORT — UP TO 2 YEARS",
        2: "MEDIUM — 3 TO 4 YEARS",
        3: "LONG — 5+ YEARS"
    }
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
