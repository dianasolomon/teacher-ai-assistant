"""
seed_demo_data.py
=================
Run this ONCE after starting your app at least once (so app.db exists):

    python seed_demo_data.py

It will:
  1. Create a student account  (id: demo_student  password: demo123)
  2. Create a teacher account  (id: demo_teacher  password: demo123)
  3. Add concepts for "Machine Learning" subject
  4. Add realistic doubt/feedback interactions (last 30 days)
  5. Add concept mastery scores
  6. Add mistake patterns
  7. Publish one assignment (from teacher)
  8. Log one assignment submission (from student)

After running, log in as demo_student / demo123 and check the dashboard!
"""

import os, sys, json, random
from datetime import datetime, timezone, timedelta

# Make sure we can import the project modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import (
    init_db, get_session,
    User, ConceptCatalog, ConceptMastery, MistakePattern, Interaction,
    Assignment, Question
)

# ── Config ──────────────────────────────────────────────────────────────────
STUDENT_ID   = "demo_student"
STUDENT_NAME = "Akshat Singh"
STUDENT_PASS = "demo123"

TEACHER_ID   = "demo_teacher"
TEACHER_NAME = "Prof. Sharma"
TEACHER_PASS = "demo123"

SUBJECT = "Machine Learning"

CONCEPTS = [
    "Linear Regression",
    "Decision Trees",
    "Neural Networks",
    "Support Vector Machines",
    "Overfitting & Regularization",
    "Gradient Descent",
    "K-Means Clustering",
    "Random Forests",
    "Backpropagation",
    "Bias-Variance Tradeoff",
]

# mastery scores (0.0 – 1.0) for each concept
MASTERY_SCORES = {
    "Linear Regression":           0.82,
    "Decision Trees":              0.75,
    "Neural Networks":             0.48,
    "Support Vector Machines":     0.35,
    "Overfitting & Regularization":0.61,
    "Gradient Descent":            0.29,
    "K-Means Clustering":          0.70,
    "Random Forests":              0.55,
    "Backpropagation":             0.22,
    "Bias-Variance Tradeoff":      0.67,
}

MISTAKE_PATTERNS = [
    ("Backpropagation",             "chain_rule_error",         5),
    ("Support Vector Machines",     "kernel_confusion",         4),
    ("Gradient Descent",            "learning_rate_selection",  3),
    ("Neural Networks",             "activation_function_mix",  3),
    ("Overfitting & Regularization","l1_vs_l2_confusion",       2),
]

DOUBT_INTERACTIONS = [
    # (days_ago, question, outcome, concept_name)
    (1,  "What is the difference between L1 and L2 regularization?",      "confused",    "Overfitting & Regularization"),
    (2,  "Can you explain gradient descent step by step?",                 "confused",    "Gradient Descent"),
    (3,  "How does backpropagation compute gradients?",                    "confused",    "Backpropagation"),
    (4,  "What is the kernel trick in SVM?",                               "confused",    "Support Vector Machines"),
    (5,  "Explain linear regression with a real-world example.",           "understood",  "Linear Regression"),
    (6,  "How do decision trees split on features?",                       "understood",  "Decision Trees"),
    (8,  "What is the bias-variance tradeoff?",                            "understood",  "Bias-Variance Tradeoff"),
    (9,  "How does K-Means clustering work?",                              "understood",  "K-Means Clustering"),
    (10, "What are activation functions and why do we need them?",         "confused",    "Neural Networks"),
    (12, "What is a random forest and how is it better than one tree?",    "understood",  "Random Forests"),
    (13, "Explain the chain rule and its role in backpropagation.",        "confused",    "Backpropagation"),
    (15, "How do I choose the right learning rate?",                       "confused",    "Gradient Descent"),
    (17, "What is overfitting and how do I detect it?",                    "understood",  "Overfitting & Regularization"),
    (18, "What is the difference between hard and soft margin SVM?",       "confused",    "Support Vector Machines"),
    (20, "How does a neural network learn weights?",                       "understood",  "Neural Networks"),
    (22, "What is the role of the loss function in gradient descent?",     "understood",  "Gradient Descent"),
    (24, "How does bagging work in random forests?",                       "understood",  "Random Forests"),
    (26, "Can you explain linear regression assumptions?",                 "understood",  "Linear Regression"),
    (28, "How do decision trees handle categorical features?",             "understood",  "Decision Trees"),
    (30, "What is the vanishing gradient problem?",                        "confused",    "Backpropagation"),
]

ASSIGNMENT_TITLE    = "Machine Learning Fundamentals - Quiz 1"
ASSIGNMENT_QUESTIONS = [
    {
        "question_text": "Explain the difference between supervised and unsupervised learning with one example each.",
        "rubric_text": "Award 2 marks for clear definition of supervised learning with example (e.g. classification). Award 2 marks for unsupervised learning with example (e.g. clustering). Award 1 mark for comparing the two.",
        "concept_ids_json": []
    },
    {
        "question_text": "Derive the gradient descent update rule for linear regression using Mean Squared Error loss.",
        "rubric_text": "Award 3 marks for correct MSE derivative. Award 2 marks for correct update rule. Deduct 1 mark for sign errors.",
        "concept_ids_json": []
    },
    {
        "question_text": "What is overfitting? List two techniques to prevent it.",
        "rubric_text": "Award 2 marks for correct definition. Award 1.5 marks each for valid techniques (e.g. regularization, dropout, cross-validation).",
        "concept_ids_json": []
    },
]

STUDENT_SUBMISSION = """
Q1: Supervised learning uses labelled data to train a model — e.g. email spam classification where emails are labelled spam/not-spam. Unsupervised learning finds hidden patterns in unlabelled data — e.g. K-Means clustering grouping customers by purchase behaviour without predefined labels.

Q2: For MSE = (1/n) * sum((y_pred - y)^2), the derivative w.r.t. weight w is (2/n) * sum((y_pred - y) * x). The gradient descent update rule is: w = w - alpha * (2/n) * sum((y_pred - y) * x), where alpha is the learning rate.

Q3: Overfitting is when a model learns the training data too well including its noise, causing poor generalisation to new data. Two techniques to prevent it: (1) L2 Regularization (Ridge) — adds a penalty term to the loss function to keep weights small. (2) Dropout — randomly deactivates neurons during training to prevent co-adaptation.
"""

# ── Helpers ──────────────────────────────────────────────────────────────────
def days_ago(n):
    return datetime.now(timezone.utc) - timedelta(days=n)

def upsert_user(db, user_id, name, role, password):
    user = db.get(User, user_id)
    if not user:
        user = User(id=user_id, name=name, role=role)
        user.set_password(password)
        db.add(user)
        print(f"  Created user: {user_id} ({role})")
    else:
        print(f"  User already exists: {user_id}")
    return user

def get_or_create_concept(db, subject, label):
    from sqlalchemy import select
    row = db.execute(
        select(ConceptCatalog).where(
            ConceptCatalog.subject == subject,
            ConceptCatalog.label == label
        )
    ).scalar_one_or_none()
    if not row:
        row = ConceptCatalog(subject=subject, label=label)
        db.add(row)
        db.flush()
    return row

# ── Main ─────────────────────────────────────────────────────────────────────
def seed():
    print("\n🌱 Seeding demo data…\n")
    init_db()
    db = get_session()
    try:
        # 1. Users
        print("👤 Creating users…")
        upsert_user(db, STUDENT_ID, STUDENT_NAME, "student", STUDENT_PASS)
        upsert_user(db, TEACHER_ID, TEACHER_NAME, "teacher", TEACHER_PASS)
        db.commit()

        # 2. Concept catalog
        print("\n📚 Creating concepts…")
        concept_map = {}  # label → ConceptCatalog
        for label in CONCEPTS:
            c = get_or_create_concept(db, SUBJECT, label)
            concept_map[label] = c
            print(f"  Concept: {label} (id={c.concept_id})")
        db.commit()

        # 3. Concept Mastery
        print("\n📊 Setting mastery scores…")
        from sqlalchemy import select
        for label, score in MASTERY_SCORES.items():
            concept = concept_map[label]
            existing = db.execute(
                select(ConceptMastery).where(
                    ConceptMastery.student_id == STUDENT_ID,
                    ConceptMastery.concept_id == concept.concept_id
                )
            ).scalar_one_or_none()
            if existing:
                existing.mastery = score
                existing.updated_at = days_ago(random.randint(0, 5))
            else:
                row = ConceptMastery(
                    student_id=STUDENT_ID,
                    subject=SUBJECT,
                    concept_id=concept.concept_id,
                    mastery=score,
                    updated_at=days_ago(random.randint(0, 5))
                )
                db.add(row)
            print(f"  {label}: {round(score*100)}%")
        db.commit()

        # 4. Mistake Patterns
        print("\n⚠️  Adding mistake patterns…")
        for concept_label, tag, count in MISTAKE_PATTERNS:
            concept = concept_map[concept_label]
            existing = db.execute(
                select(MistakePattern).where(
                    MistakePattern.student_id == STUDENT_ID,
                    MistakePattern.concept_id == concept.concept_id,
                    MistakePattern.mistake_tag == tag
                )
            ).scalar_one_or_none()
            if existing:
                existing.count = count
                existing.last_seen_at = days_ago(random.randint(0, 3))
            else:
                row = MistakePattern(
                    student_id=STUDENT_ID,
                    subject=SUBJECT,
                    concept_id=concept.concept_id,
                    mistake_tag=tag,
                    count=count,
                    last_seen_at=days_ago(random.randint(0, 3))
                )
                db.add(row)
            print(f"  {concept_label} → {tag} ({count}x)")
        db.commit()

        # 5. Interactions (doubt + feedback history)
        print("\n💬 Adding interaction history…")
        for days, question, outcome, concept_label in DOUBT_INTERACTIONS:
            concept = concept_map[concept_label]
            row = Interaction(
                student_id=STUDENT_ID,
                subject=SUBJECT,
                type="doubt",
                question_text=question,
                concepts_json=json.dumps([concept.concept_id]),
                outcome=outcome,
                created_at=days_ago(days)
            )
            db.add(row)
            print(f"  [{outcome:12s}] Day-{days:2d}: {question[:60]}…")
        db.commit()

        # 6. Assignment (published by teacher)
        print("\n📋 Publishing assignment…")
        existing_assign = db.execute(
            select(Assignment).where(Assignment.title == ASSIGNMENT_TITLE)
        ).scalar_one_or_none()

        if not existing_assign:
            assignment = Assignment(
                subject=SUBJECT,
                title=ASSIGNMENT_TITLE,
                created_at=days_ago(7)
            )
            db.add(assignment)
            db.flush()

            for q_data in ASSIGNMENT_QUESTIONS:
                q = Question(
                    assignment_id=assignment.assignment_id,
                    subject=SUBJECT,
                    question_text=q_data["question_text"],
                    rubric_text=q_data["rubric_text"],
                    concept_ids_json=json.dumps(q_data["concept_ids_json"]),
                    created_at=days_ago(7)
                )
                db.add(q)
            db.commit()
            print(f"  Assignment published: '{ASSIGNMENT_TITLE}' (id={assignment.assignment_id})")
        else:
            print(f"  Assignment already exists: '{ASSIGNMENT_TITLE}'")

        # 7. Log assignment submission interaction
        print("\n📤 Logging assignment submission…")
        submission_row = Interaction(
            student_id=STUDENT_ID,
            subject=SUBJECT,
            type="assignment",
            question_text=f"Submitted: {ASSIGNMENT_TITLE}",
            concepts_json=json.dumps([concept_map[c].concept_id for c in ["Linear Regression", "Gradient Descent", "Overfitting & Regularization"]]),
            outcome="answered",
            created_at=days_ago(2)
        )
        db.add(submission_row)
        db.commit()
        print(f"  Submission logged.")

        print("\n✅ Done! Demo data seeded successfully.\n")
        print("=" * 50)
        print(f"  Student login:  {STUDENT_ID} / {STUDENT_PASS}")
        print(f"  Teacher login:  {TEACHER_ID} / {TEACHER_PASS}")
        print("=" * 50)
        print("\nNow restart your Flask app and log in as demo_student to see the dashboard filled with data!\n")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        import traceback; traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
