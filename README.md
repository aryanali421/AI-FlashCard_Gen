# 🧠 MindForge – AI Quiz & Flashcard Generator

MindForge is an AI-powered learning application that transforms study topics and educational material into interactive quizzes and flashcards.

It helps students move beyond passive reading by encouraging active recall, self-assessment, and conceptual understanding.

Whether you're preparing for an examination, learning a new subject, or revising difficult concepts, MindForge provides AI-powered tools to make studying more interactive.

## ✨ Features

### 📝 AI Quiz Generator
- Generate multiple-choice quizzes from any academic topic.
- Create quizzes using pasted study notes or educational material.
- Choose between Easy, Medium, and Hard difficulty levels.
- Generate 5, 10, 15, or 20 questions.
- Receive instant feedback after submitting answers.
- View correct answers and detailed explanations.
- Calculate quiz scores and accuracy.

### 🗂️ AI Flashcard Generator
- Automatically generate flashcards from topics or study material.
- Choose the difficulty level and number of cards.
- Interactive flashcard interface with answer reveal.
- Mark cards as known or needing revision.
- Track flashcard learning progress.

### 💬 AI Study Assistant
- Ask questions about academic topics.
- Get explanations in simple, understandable language.
- Provide study notes for more contextual responses.
- Explore concepts through conversational AI assistance.

### 📊 Learning Progress
- Track completed quizzes.
- Review previous quiz scores.
- Monitor quiz accuracy.
- Track flashcards marked as known or needing revision.

### ⚙️ Customization
- Set a default quiz difficulty.
- Choose a default question count.
- Personalize generation preferences.

## 🛠️ Tech Stack

- **Python:** Core application logic.
- **Streamlit:** Interactive web application interface.
- **Groq API:** AI-powered content generation and tutoring.
- **Pandas:** Quiz history and progress data handling.
- **HTML and CSS:** Custom application styling.

## 🤖 AI Integration

MindForge integrates the Groq API to power three main capabilities:

1. **Quiz Generation:** Creates multiple-choice questions, answer options, correct answers, and explanations.
2. **Flashcard Generation:** Converts topics and study material into question-and-answer cards.
3. **AI Tutoring:** Provides conversational explanations and educational assistance.

The application uses the `openai/gpt-oss-120b` model through Groq.

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone YOUR_REPOSITORY_URL
cd mindforge
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure your API key

Create a `.streamlit` folder in the project directory and add a file named `secrets.toml`.

```toml
GROQ_API_KEY = "your_groq_api_key_here"
```

Alternatively, configure the `GROQ_API_KEY` environment variable.

### 4. Run the application

```bash
streamlit run app.py
```

## 🔐 Environment Variables

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | API key required to access Groq's AI models |

Never commit API keys or your `secrets.toml` file to a public repository.

## 📌 Current Limitations

- Learning progress is stored in Streamlit session state.
- Generated quizzes and flashcards are not permanently saved.
- User accounts and database-backed storage are not currently implemented.
- Quiz generation depends on access to the Groq API.

## 🎯 Project Objective

MindForge aims to make learning more engaging and effective by combining AI-generated educational content with interactive revision tools.

The goal is to help students test their knowledge, identify learning gaps, and strengthen their understanding through active recall.

## 👨‍💻 Author

**Aryan Ali**

---

*Built with Python, Streamlit, and Generative AI.*
