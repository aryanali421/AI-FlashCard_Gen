
import os
import json
import re
import html
import streamlit as st
import pandas as pd
from groq import Groq
from datetime import datetime

# =========================================================
# CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="MindForge | AI Learning Studio",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

MODEL = "openai/gpt-oss-120b"

# =========================================================
# API CONFIGURATION
# =========================================================

def get_api_key():
    key = os.getenv("GROQ_API_KEY", "")

    if not key:
        try:
            key = st.secrets.get("GROQ_API_KEY", "")
        except Exception:
            pass

    return key


def get_client():
    api_key = get_api_key()

    if not api_key:
        return None

    return Groq(api_key=api_key)


# =========================================================
# SESSION STATE
# =========================================================

DEFAULTS = {
    "page": "Dashboard",
    "difficulty": "Medium",
    "question_count": 5,
    "quiz": [],
    "quiz_answers": {},
    "quiz_submitted": False,
    "quiz_topic": "",
    "quiz_source": "",
    "flashcards": [],
    "flashcard_topic": "",
    "flashcard_index": 0,
    "flashcard_known": [],
    "flashcard_unknown": [],
    "chat_history": [],
    "quiz_history": [],
    "generation_count": 0,
    "show_answer": False,
    "last_generation_type": ""
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# DESIGN
# =========================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Space+Grotesk:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

.stApp {
    background: #0c0d12;
    color: #f2f2f5;
}

header[data-testid="stHeader"] {
    background: transparent;
}

section[data-testid="stSidebar"] {
    background: #11131b;
    border-right: 1px solid #252735;
}

section[data-testid="stSidebar"] * {
    color: #e8e9f0;
}

h1, h2, h3 {
    font-family: 'Space Grotesk', sans-serif;
}

.hero {
    padding: 32px;
    border-radius: 22px;
    background: linear-gradient(125deg, #191c2c, #252044, #172e35);
    border: 1px solid #34364d;
    margin-bottom: 25px;
}

.hero-tag {
    color: #b7a7ff;
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 2px;
    text-transform: uppercase;
}

.hero h1 {
    font-size: 42px;
    margin: 12px 0;
    color: #ffffff;
}

.hero p {
    color: #b7bbca;
    font-size: 15px;
    max-width: 650px;
}

.panel {
    background: #151721;
    border: 1px solid #292c3a;
    padding: 22px;
    border-radius: 17px;
    margin-bottom: 16px;
}

.metric {
    background: #171923;
    border: 1px solid #292c3a;
    border-radius: 15px;
    padding: 20px;
}

.metric-label {
    color: #969bad;
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.metric-value {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 29px;
    font-weight: 700;
    margin-top: 8px;
    color: #ffffff;
}

.metric-sub {
    font-size: 12px;
    color: #a5a9b8;
    margin-top: 5px;
}

.section-label {
    color: #a99aff;
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-bottom: 8px;
}

.question-card {
    background: #191c27;
    border: 1px solid #34384a;
    padding: 25px;
    border-radius: 17px;
    margin: 15px 0;
}

.flashcard {
    background: linear-gradient(140deg, #24213c, #1b2934);
    border: 1px solid #454267;
    border-radius: 22px;
    padding: 45px 30px;
    min-height: 250px;
    text-align: center;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.flashcard-label {
    color: #b7a7ff;
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 2px;
    margin-bottom: 20px;
}

.flashcard-content {
    color: white;
    font-size: 23px;
    font-weight: 700;
    line-height: 1.5;
}

.small-muted {
    color: #969bad;
    font-size: 13px;
}

div.stButton > button {
    border-radius: 10px;
    border: 1px solid #45415f;
    background: #28243e;
    color: white;
    font-weight: 700;
    min-height: 42px;
}

div.stButton > button:hover {
    border-color: #a99aff;
    color: white;
    background: #393254;
}

.stTextInput input, .stTextArea textarea,
.stSelectbox div[data-baseweb="select"] {
    background: #191c27;
    color: white;
    border-color: #34384a;
}

div[data-testid="stProgressBar"] > div > div {
    background: #a99aff;
}

hr {
    border-color: #292c3a;
}

footer {
    visibility: hidden;
}
</style>
""", unsafe_allow_html=True)


# =========================================================
# AI FUNCTIONS
# =========================================================

def ask_ai(system_prompt, user_prompt, temperature=0.4):
    client = get_client()

    if client is None:
        raise ValueError(
            "Groq API key not found. Configure GROQ_API_KEY in Streamlit secrets."
        )

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=temperature
    )

    return response.choices[0].message.content


def extract_json(response):
    response = response.strip()

    response = re.sub(
        r"^```(?:json)?\s*",
        "",
        response,
        flags=re.IGNORECASE
    )

    response = re.sub(r"\s*```$", "", response)

    try:
        return json.loads(response)
    except json.JSONDecodeError:
        match = re.search(r"(\{.*\}|\[.*\])", response, re.DOTALL)

        if match:
            return json.loads(match.group(1))

        raise ValueError("The AI returned an invalid response. Please try again.")


def generate_quiz(topic, source, difficulty, count):
    system_prompt = """
You are an expert academic assessment designer.

Create accurate, educational multiple-choice questions.

Return ONLY valid JSON in this exact format:

{
  "questions": [
    {
      "question": "Question text",
      "options": [
        "Option A",
        "Option B",
        "Option C",
        "Option D"
      ],
      "answer": "Exact correct option text",
      "explanation": "Clear explanation of why the answer is correct"
    }
  ]
}

Rules:
- Exactly the requested number of questions.
- Exactly four options per question.
- Only one correct answer per question.
- Questions must match the requested difficulty.
- Avoid repeated questions.
- Use plausible incorrect options.
- Keep explanations educational and clear.
- Do not include markdown or text outside JSON.
"""

    user_prompt = f"""
Create a {difficulty} difficulty quiz.

Topic:
{topic}

Study material:
{source if source.strip() else "Use reliable general academic knowledge."}

Number of questions:
{count}
"""

    result = extract_json(
        ask_ai(system_prompt, user_prompt, temperature=0.5)
    )

    questions = result.get("questions", [])

    if len(questions) != count:
        raise ValueError(
            f"Expected {count} questions, but received {len(questions)}."
        )

    for question in questions:
        if not isinstance(question.get("question"), str):
            raise ValueError("A question is missing its text.")

        if len(question.get("options", [])) != 4:
            raise ValueError("Every question must have four options.")

        if question.get("answer") not in question["options"]:
            raise ValueError("A question has an invalid correct answer.")

        if not question.get("explanation"):
            raise ValueError("A question is missing its explanation.")

    return questions


def generate_flashcards(topic, source, difficulty, count):
    system_prompt = """
You are an expert learning and memory specialist.

Generate concise, useful flashcards.

Return ONLY valid JSON:

{
  "cards": [
    {
      "front": "Question or concept",
      "back": "Answer or explanation"
    }
  ]
}

Rules:
- Generate exactly the requested number of cards.
- Keep each card focused on one concept.
- Answers must be accurate and understandable.
- Avoid duplicate cards.
- Match the requested difficulty.
- Make cards useful for active recall.
- Do not include markdown outside JSON.
"""

    user_prompt = f"""
Create flashcards about:

Topic:
{topic}

Study material:
{source if source.strip() else "Use reliable general academic knowledge."}

Difficulty:
{difficulty}

Number of flashcards:
{count}
"""

    result = extract_json(
        ask_ai(system_prompt, user_prompt, temperature=0.4)
    )

    cards = result.get("cards", [])

    if len(cards) != count:
        raise ValueError(
            f"Expected {count} flashcards, but received {len(cards)}."
        )

    for card in cards:
        if not card.get("front") or not card.get("back"):
            raise ValueError("A flashcard is missing its question or answer.")

    return cards


def ask_study_assistant(question, topic, source, history):
    system_prompt = f"""
You are MindForge's AI Study Assistant.

Help the learner understand concepts instead of merely memorizing answers.

Current topic: {topic or "Not specified"}

Study material:
{source or "No study material provided."}

Your responsibilities:
- Explain concepts step by step.
- Use simple language when appropriate.
- Give examples.
- Help identify misunderstandings.
- Ask useful follow-up questions.
- Never invent facts.
- Be concise but thorough.
"""

    messages = [
        {"role": "system", "content": system_prompt}
    ]

    for item in history[-10:]:
        messages.append(item)

    messages.append({
        "role": "user",
        "content": question
    })

    client = get_client()

    if client is None:
        raise ValueError("Groq API key not found.")

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.5
    )

    return response.choices[0].message.content


# =========================================================
# REUSABLE UI
# =========================================================

def metric_card(label, value, subtitle=""):
    st.markdown(
        f"""
        <div class="metric">
            <div class="metric-label">{html.escape(str(label))}</div>
            <div class="metric-value">{html.escape(str(value))}</div>
            <div class="metric-sub">{html.escape(str(subtitle))}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def section_heading(title, description=None):
    st.markdown(f"### {title}")

    if description:
        st.markdown(
            f'<p class="small-muted">{html.escape(description)}</p>',
            unsafe_allow_html=True
        )


def navigate(page):
    st.session_state.page = page


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:
    st.markdown("## 🧠 MindForge")
    st.caption("Your AI-powered learning studio")

    st.divider()

    pages = [
        "Dashboard",
        "Quiz Generator",
        "Flashcards",
        "AI Study Assistant",
        "Progress",
        "Settings"
    ]

    selected_page = st.radio(
        "NAVIGATION",
        pages,
        index=pages.index(st.session_state.page)
        if st.session_state.page in pages else 0
    )

    st.session_state.page = selected_page

    st.divider()

    st.markdown("#### Your learning space")
    st.caption("Generate. Practice. Understand. Improve.")

    st.markdown(
        f"""
        <div class="panel">
            <div class="small-muted">AI generations this session</div>
            <div class="metric-value">{st.session_state.generation_count}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# DASHBOARD
# =========================================================

if st.session_state.page == "Dashboard":

    st.markdown("""
    <div class="hero">
        <div class="hero-tag">AI Learning Studio</div>
        <h1>Learn smarter. Remember longer.</h1>
        <p>
        Turn your study material into interactive quizzes and flashcards.
        Understand difficult topics, test your knowledge, and track your progress.
        </p>
    </div>
    """, unsafe_allow_html=True)

    quiz_count = len(st.session_state.quiz_history)
    flashcard_count = len(st.session_state.flashcards)

    known_count = len(st.session_state.flashcard_known)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        metric_card("Quizzes completed", quiz_count)

    with col2:
        metric_card("Current flashcards", flashcard_count)

    with col3:
        metric_card("Cards mastered", known_count)

    with col4:
        metric_card("AI generations", st.session_state.generation_count)

    st.markdown("---")

    section_heading(
        "What would you like to do?",
        "Choose a learning activity to get started."
    )

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.markdown("### 📝 Generate a quiz")
            st.write(
                "Test your understanding with AI-generated questions "
                "and detailed explanations."
            )

            if st.button("Create a quiz →", use_container_width=True):
                navigate("Quiz Generator")
                st.rerun()

    with col2:
        with st.container(border=True):
            st.markdown("### 🗂️ Create flashcards")
            st.write(
                "Turn difficult topics and study notes into "
                "interactive revision cards."
            )

            if st.button("Create flashcards →", use_container_width=True):
                navigate("Flashcards")
                st.rerun()

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.markdown("### 💬 AI Study Assistant")
            st.write(
                "Ask questions, understand difficult concepts, "
                "and get explanations."
            )

            if st.button("Ask AI →", use_container_width=True):
                navigate("AI Study Assistant")
                st.rerun()

    with col2:
        with st.container(border=True):
            st.markdown("### 📊 Learning progress")
            st.write(
                "Review your quiz performance and flashcard progress."
            )

            if st.button("View progress →", use_container_width=True):
                navigate("Progress")
                st.rerun()

    st.markdown("---")

    section_heading("Recent quiz activity")

    if st.session_state.quiz_history:
        history_df = pd.DataFrame(
            st.session_state.quiz_history[-5:]
        )

        st.dataframe(
            history_df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Your completed quizzes will appear here.")


# =========================================================
# QUIZ GENERATOR
# =========================================================

elif st.session_state.page == "Quiz Generator":

    st.markdown("""
    <div class="hero">
        <div class="hero-tag">AI Assessment Lab</div>
        <h1>Build your next quiz.</h1>
        <p>Generate questions from your notes or any academic topic.</p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("quiz_form"):

        topic = st.text_input(
            "What do you want to study?",
            placeholder="e.g. Python loops, Newton's laws, cell biology"
        )

        source = st.text_area(
            "Paste your study material (optional)",
            placeholder="Paste notes, textbook extracts, or your own summaries...",
            height=150
        )

        col1, col2 = st.columns(2)

        with col1:
            difficulty = st.selectbox(
                "Difficulty",
                ["Easy", "Medium", "Hard"],
                index=["Easy", "Medium", "Hard"].index(
                    st.session_state.difficulty
                )
            )

        with col2:
            count = st.selectbox(
                "Number of questions",
                [5, 10, 15, 20],
                index=[5, 10, 15, 20].index(
                    st.session_state.question_count
                )
            )

        submitted = st.form_submit_button(
            "✨ Generate quiz",
            use_container_width=True
        )

    if submitted:
        if not topic.strip() and not source.strip():
            st.warning("Enter a topic or provide study material first.")

        else:
            try:
                with st.spinner("Creating your personalized quiz..."):

                    questions = generate_quiz(
                        topic,
                        source,
                        difficulty,
                        count
                    )

                st.session_state.quiz = questions
                st.session_state.quiz_answers = {}
                st.session_state.quiz_submitted = False
                st.session_state.quiz_topic = topic or "Study material"
                st.session_state.quiz_source = source
                st.session_state.generation_count += 1
                st.session_state.last_generation_type = "quiz"

                st.success("Your quiz is ready!")

            except Exception as e:
                st.error(f"Could not generate quiz: {e}")

    # Display generated quiz

    if st.session_state.quiz:

        st.divider()

        st.markdown(
            f"## Quiz: {st.session_state.quiz_topic}"
        )

        questions = st.session_state.quiz

        if not st.session_state.quiz_submitted:

            with st.form("answer_quiz"):

                selected_answers = {}

                for i, q in enumerate(questions):

                    st.markdown(
                        f"""
                        <div class="question-card">
                            <div class="section-label">
                                QUESTION {i + 1} OF {len(questions)}
                            </div>
                            <h4>{html.escape(q['question'])}</h4>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    selected_answers[i] = st.radio(
                        f"Choose your answer for question {i + 1}",
                        q["options"],
                        index=None,
                        key=f"quiz_answer_{i}",
                        label_visibility="collapsed"
                    )

                submitted_quiz = st.form_submit_button(
                    "Submit answers",
                    use_container_width=True
                )

            if submitted_quiz:

                unanswered = [
                    i for i, answer in selected_answers.items()
                    if answer is None
                ]

                if unanswered:
                    st.warning(
                        f"Please answer all questions. "
                        f"{len(unanswered)} remain unanswered."
                    )

                else:
                    st.session_state.quiz_answers = selected_answers
                    st.session_state.quiz_submitted = True
                    st.rerun()

        else:

            correct = 0

            for i, q in enumerate(questions):

                user_answer = st.session_state.quiz_answers.get(i)
                is_correct = user_answer == q["answer"]

                if is_correct:
                    correct += 1

                st.markdown(
                    f"### Question {i + 1}: {q['question']}"
                )

                if is_correct:
                    st.success(f"Your answer: {user_answer}")
                else:
                    st.error(f"Your answer: {user_answer}")
                    st.info(f"Correct answer: {q['answer']}")

                st.markdown(f"**Explanation:** {q['explanation']}")
                st.divider()

            percentage = round((correct / len(questions)) * 100)

            st.markdown("## Your results")

            col1, col2, col3 = st.columns(3)

            with col1:
                metric_card("Score", f"{correct}/{len(questions)}")

            with col2:
                metric_card("Accuracy", f"{percentage}%")

            with col3:
                metric_card(
                    "Incorrect",
                    len(questions) - correct
                )

            st.progress(percentage / 100)

            st.session_state.quiz_history.append({
                "Topic": st.session_state.quiz_topic,
                "Score": f"{correct}/{len(questions)}",
                "Accuracy": f"{percentage}%",
                "Date": datetime.now().strftime("%d %b %Y")
            })

            if st.button("Create another quiz", use_container_width=True):
                st.session_state.quiz = []
                st.session_state.quiz_answers = {}
                st.session_state.quiz_submitted = False
                st.rerun()


# =========================================================
# FLASHCARDS
# =========================================================

elif st.session_state.page == "Flashcards":

    st.markdown("""
    <div class="hero">
        <div class="hero-tag">Active Recall Studio</div>
        <h1>Make knowledge stick.</h1>
        <p>Generate flashcards and use active recall to strengthen your memory.</p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("flashcard_form"):

        topic = st.text_input(
            "Flashcard topic",
            placeholder="e.g. Data structures, organic chemistry"
        )

        source = st.text_area(
            "Study material (optional)",
            placeholder="Paste your notes here...",
            height=140
        )

        col1, col2 = st.columns(2)

        with col1:
            difficulty = st.selectbox(
                "Difficulty",
                ["Easy", "Medium", "Hard"],
                index=["Easy", "Medium", "Hard"].index(
                    st.session_state.difficulty
                ),
                key="flashcard_difficulty"
            )

        with col2:
            count = st.selectbox(
                "Number of cards",
                [5, 10, 15, 20, 30],
                index=1
            )

        generate = st.form_submit_button(
            "✨ Generate flashcards",
            use_container_width=True
        )

    if generate:

        if not topic.strip() and not source.strip():
            st.warning("Enter a topic or provide study material.")

        else:
            try:
                with st.spinner("Creating your flashcard deck..."):

                    cards = generate_flashcards(
                        topic,
                        source,
                        difficulty,
                        count
                    )

                st.session_state.flashcards = cards
                st.session_state.flashcard_topic = topic or "Study material"
                st.session_state.flashcard_index = 0
                st.session_state.flashcard_known = []
                st.session_state.flashcard_unknown = []
                st.session_state.show_answer = False
                st.session_state.generation_count += 1

                st.success("Your flashcard deck is ready!")

            except Exception as e:
                st.error(f"Could not create flashcards: {e}")

    # Flashcard learning interface

    cards = st.session_state.flashcards

    if cards:

        st.divider()

        st.markdown(f"## {st.session_state.flashcard_topic}")

        total = len(cards)
        index = st.session_state.flashcard_index

        if index >= total:
            index = 0
            st.session_state.flashcard_index = 0

        known = len(st.session_state.flashcard_known)
        unknown = len(st.session_state.flashcard_unknown)

        col1, col2, col3 = st.columns(3)

        with col1:
            metric_card("Total cards", total)

        with col2:
            metric_card("Known", known)

        with col3:
            metric_card("Need revision", unknown)

        st.progress((index + 1) / total)

        st.caption(f"Card {index + 1} of {total}")

        current_card = cards[index]

        content = (
            current_card["back"]
            if st.session_state.show_answer
            else current_card["front"]
        )

        label = (
            "ANSWER"
            if st.session_state.show_answer
            else "QUESTION"
        )

        st.markdown(
            f"""
            <div class="flashcard">
                <div class="flashcard-label">{label}</div>
                <div class="flashcard-content">
                    {html.escape(content)}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.write("")

        if not st.session_state.show_answer:

            if st.button(
                "Reveal answer",
                use_container_width=True
            ):
                st.session_state.show_answer = True
                st.rerun()

        else:

            col1, col2 = st.columns(2)

            with col1:
                if st.button(
                    "✕ Need revision",
                    use_container_width=True
                ):
                    if index not in st.session_state.flashcard_unknown:
                        st.session_state.flashcard_unknown.append(index)

                    if index in st.session_state.flashcard_known:
                        st.session_state.flashcard_known.remove(index)

                    st.session_state.flashcard_index = (index + 1) % total
                    st.session_state.show_answer = False
                    st.rerun()

            with col2:
                if st.button(
                    "✓ I know this",
                    use_container_width=True
                ):
                    if index not in st.session_state.flashcard_known:
                        st.session_state.flashcard_known.append(index)

                    if index in st.session_state.flashcard_unknown:
                        st.session_state.flashcard_unknown.remove(index)

                    st.session_state.flashcard_index = (index + 1) % total
                    st.session_state.show_answer = False
                    st.rerun()

        col1, col2 = st.columns(2)

        with col1:
            if st.button("← Previous card", use_container_width=True):
                st.session_state.flashcard_index = (index - 1) % total
                st.session_state.show_answer = False
                st.rerun()

        with col2:
            if st.button("Next card →", use_container_width=True):
                st.session_state.flashcard_index = (index + 1) % total
                st.session_state.show_answer = False
                st.rerun()

        st.divider()

        if known == total:
            st.success("You've marked every card as known!")

        if st.button("Restart flashcard review"):
            st.session_state.flashcard_index = 0
            st.session_state.flashcard_known = []
            st.session_state.flashcard_unknown = []
            st.session_state.show_answer = False
            st.rerun()


# =========================================================
# AI STUDY ASSISTANT
# =========================================================

elif st.session_state.page == "AI Study Assistant":

    st.markdown("""
    <div class="hero">
        <div class="hero-tag">Your Personal AI Tutor</div>
        <h1>Understand, don't just memorize.</h1>
        <p>Ask questions, explore concepts, and get explanations tailored to your learning needs.</p>
    </div>
    """, unsafe_allow_html=True)

    topic = st.text_input(
        "What are you currently studying?",
        placeholder="e.g. Calculus, machine learning, biology"
    )

    source = st.text_area(
        "Add your notes for context (optional)",
        height=100,
        placeholder="Paste relevant study material here..."
    )

    st.divider()

    for message in st.session_state.chat_history:

        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input(
        "Ask a question or tell me what you're struggling with..."
    )

    if prompt:

        st.session_state.chat_history.append({
            "role": "user",
            "content": prompt
        })

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):

            try:
                with st.spinner("Thinking..."):

                    response = ask_study_assistant(
                        prompt,
                        topic,
                        source,
                        st.session_state.chat_history[:-1]
                    )

                st.markdown(response)

                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response
                })

            except Exception as e:
                st.error(f"Assistant error: {e}")

    if st.button("Clear conversation"):
        st.session_state.chat_history = []
        st.rerun()


# =========================================================
# PROGRESS
# =========================================================

elif st.session_state.page == "Progress":

    st.markdown("""
    <div class="hero">
        <div class="hero-tag">Your Learning Analytics</div>
        <h1>Track your improvement.</h1>
        <p>See what you've practiced and where you can improve.</p>
    </div>
    """, unsafe_allow_html=True)

    history = st.session_state.quiz_history

    col1, col2, col3 = st.columns(3)

    with col1:
        metric_card("Quizzes completed", len(history))

    with col2:
        metric_card(
            "Flashcards known",
            len(st.session_state.flashcard_known)
        )

    with col3:
        metric_card(
            "Flashcards to revise",
            len(st.session_state.flashcard_unknown)
        )

    st.divider()

    section_heading("Quiz history")

    if history:

        df = pd.DataFrame(history)

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        accuracies = []

        for item in history:
            try:
                accuracies.append(
                    int(item["Accuracy"].replace("%", ""))
                )
            except (ValueError, KeyError):
                pass

        if accuracies:

            chart_df = pd.DataFrame({
                "Quiz": [
                    f"Quiz {i + 1}"
                    for i in range(len(accuracies))
                ],
                "Accuracy": accuracies
            })

            st.markdown("### Quiz accuracy")
            st.line_chart(
                chart_df.set_index("Quiz")
            )

    else:
        st.info("Complete a quiz to start building your learning history.")


# =========================================================
# SETTINGS
# =========================================================

elif st.session_state.page == "Settings":

    st.markdown("""
    <div class="hero">
        <div class="hero-tag">Personalization</div>
        <h1>Make MindForge yours.</h1>
        <p>Adjust how your AI learning tools generate study material.</p>
    </div>
    """, unsafe_allow_html=True)

    section_heading("Generation preferences")

    st.session_state.difficulty = st.selectbox(
        "Default difficulty",
        ["Easy", "Medium", "Hard"],
        index=["Easy", "Medium", "Hard"].index(
            st.session_state.difficulty
        )
    )

    st.session_state.question_count = st.selectbox(
        "Default quiz question count",
        [5, 10, 15, 20],
        index=[5, 10, 15, 20].index(
            st.session_state.question_count
        )
    )

    st.caption(
        "These preferences are used as the starting values "
        "when generating new quizzes."
    )

    st.divider()

    section_heading("Application information")

    st.markdown("""
    **MindForge**

    AI-powered quiz and flashcard generation.

    - AI model: Groq
    - Model: openai/gpt-oss-120b
    - Interface: Streamlit
    """)

    if st.button("Reset learning data", type="secondary"):

        st.session_state.quiz_history = []
        st.session_state.quiz = []
        st.session_state.quiz_answers = {}
        st.session_state.quiz_submitted = False
        st.session_state.flashcards = []
        st.session_state.flashcard_known = []
        st.session_state.flashcard_unknown = []
        st.session_state.chat_history = []

        st.success("Session learning data has been reset.")
