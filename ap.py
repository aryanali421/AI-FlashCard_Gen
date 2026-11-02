import json
import os
import random

import streamlit as st
from groq import Groq

MODEL = "openai/gpt-oss-20b"

st.set_page_config(page_title="AI Quiz Generator", page_icon="🧠", layout="centered")


def get_api_key():
    key = os.getenv("GROQ_API_KEY", "")
    try:
        key = key or st.secrets.get("GROQ_API_KEY", "")
    except Exception:
        pass
    return key


def generate_questions(api_key, notes, difficulty, n):
    client = Groq(api_key=api_key)
    system = (
        "You write multiple-choice quiz questions from study notes. "
        "Use ONLY information from the notes. Return ONLY valid JSON in this shape: "
        '{"questions":[{"question":"...","options":["A","B","C","D"],'
        '"answer_index":0,"explanation":"..."}]}. '
        "Exactly 4 options per question, exactly one correct. "
        "Explanations: 1-2 sentences on why the answer is right."
    )
    user = (
        f"Difficulty: {difficulty}\n"
        f"Number of questions: {n}\n\n"
        f"NOTES:\n{notes}"
    )
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        response_format={"type": "json_object"},
        temperature=0.4,
    )
    data = json.loads(resp.choices[0].message.content)

    cleaned = []
    for q in data.get("questions", []):
        opts = q.get("options", [])
        idx = q.get("answer_index")
        if len(opts) != 4 or not isinstance(idx, int) or not 0 <= idx < 4:
            continue
        # shuffle so the correct answer isn't always in the same slot
        pairs = [(o, i == idx) for i, o in enumerate(opts)]
        random.shuffle(pairs)
        cleaned.append(
            {
                "question": q["question"],
                "options": [p[0] for p in pairs],
                "answer_index": next(i for i, p in enumerate(pairs) if p[1]),
                "explanation": q.get("explanation", ""),
            }
        )
    return cleaned


def reset_quiz_state():
    st.session_state.submitted = False
    st.session_state.card_i = 0
    st.session_state.card_flipped = False
    for k in list(st.session_state.keys()):
        if k.startswith("q_"):
            del st.session_state[k]


# ---------- state ----------
st.session_state.setdefault("questions", [])
st.session_state.setdefault("submitted", False)
st.session_state.setdefault("card_i", 0)
st.session_state.setdefault("card_flipped", False)

# ---------- sidebar ----------
with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("Groq API key", value=get_api_key(), type="password")
    difficulty = st.select_slider("Difficulty", ["Easy", "Medium", "Hard"], value="Medium")
    n_questions = st.slider("Number of questions", 3, 15, 5)

st.title("🧠 AI Quiz & Flashcard Generator")
notes = st.text_area("Paste your lesson notes", height=220)

if st.button("Generate quiz", type="primary"):
    if not api_key:
        st.error("Add your Groq API key in the sidebar.")
    elif len(notes.strip()) < 100:
        st.error("Notes are too short. Paste at least a few solid paragraphs.")
    else:
        with st.spinner("Generating..."):
            try:
                qs = generate_questions(api_key, notes, difficulty, n_questions)
                if not qs:
                    st.error("Model returned nothing usable. Try again.")
                else:
                    reset_quiz_state()
                    st.session_state.questions = qs
            except Exception as e:
                st.error(f"Generation failed: {e}")

questions = st.session_state.questions

if questions:
    quiz_tab, cards_tab = st.tabs(["📝 Quiz", "🃏 Flashcards"])

    # ---------- quiz ----------
    with quiz_tab:
        with st.form("quiz_form"):
            for i, q in enumerate(questions):
                st.markdown(f"**{i + 1}. {q['question']}**")
                st.radio(
                    "Choose one",
                    q["options"],
                    index=None,
                    key=f"q_{i}",
                    label_visibility="collapsed",
                    disabled=st.session_state.submitted,
                )
                st.divider()
            submitted = st.form_submit_button("Submit answers")
            if submitted:
                st.session_state.submitted = True

        if st.session_state.submitted:
            score = 0
            for i, q in enumerate(questions):
                picked = st.session_state.get(f"q_{i}")
                correct = q["options"][q["answer_index"]]
                if picked == correct:
                    score += 1
                    st.success(f"Q{i + 1}: Correct. {correct}")
                elif picked is None:
                    st.warning(f"Q{i + 1}: Skipped. Answer: {correct}")
                else:
                    st.error(f"Q{i + 1}: You said '{picked}'. Answer: {correct}")
                st.caption(q["explanation"])

            pct = round(score / len(questions) * 100)
            st.subheader(f"Score: {score}/{len(questions)} ({pct}%)")
            st.progress(pct / 100)

            if st.button("Retake quiz"):
                reset_quiz_state()
                st.rerun()

    # ---------- flashcards ----------
    with cards_tab:
        i = st.session_state.card_i
        q = questions[i]
        st.caption(f"Card {i + 1} of {len(questions)}")

        if st.session_state.card_flipped:
            st.success(f"**{q['options'][q['answer_index']]}**\n\n{q['explanation']}")
        else:
            st.info(f"**{q['question']}**")

        c1, c2, c3 = st.columns(3)
        if c1.button("⬅ Prev", disabled=i == 0):
            st.session_state.card_i -= 1
            st.session_state.card_flipped = False
            st.rerun()
        if c2.button("Flip"):
            st.session_state.card_flipped = not st.session_state.card_flipped
            st.rerun()
        if c3.button("Next ➡", disabled=i == len(questions) - 1):
            st.session_state.card_i += 1
            st.session_state.card_flipped = False
            st.rerun()
