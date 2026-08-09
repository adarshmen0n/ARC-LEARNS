# ARC LEARNS 🧠

### AI-Powered Personalized Learning Assistant

ARC LEARNS is a lightweight AI-powered learning platform that transforms uploaded study material into an interactive learning experience.

Instead of searching through a long PDF manually, students can upload their study material and use AI to:

- Learn topics through structured lessons
- Ask questions about the uploaded material
- Ask general questions using ARC 0
- Search the web for current information
- Generate quizzes from their study material
- Receive streamed AI responses

---

## 🚀 Features

### 📄 Study Material Upload

Upload study material and let ARC LEARNS process it automatically.

The system extracts the text, cleans it, divides it into meaningful chunks, creates embeddings, and stores them for semantic search.

---

### 👨‍🏫 AI Teacher

ARC LEARNS can teach topics from the uploaded study material.

Teaching lengths:

- Short
- Medium
- Long

Lessons are generated using the retrieved study material rather than relying purely on general model knowledge.

AI Teacher also supports streaming responses so the lesson can appear progressively.

---

### 💬 Ask AI

Ask questions about the uploaded study material.

ARC LEARNS retrieves the most relevant content using semantic search and uses that context to generate the answer.

This provides a Retrieval-Augmented Generation (RAG) workflow.

---

### 🌐 ARC 0

ARC 0 is the general-purpose AI assistant inside ARC LEARNS.

Unlike the AI Teacher, ARC 0 is not restricted to the uploaded PDF.

It can help with:

- General knowledge
- Programming
- Mathematics
- Technology
- Writing
- Current events
- Recent information
- General questions

ARC 0 also supports web search for current information.

---

### 🔎 Web Search

ARC 0 and supported AI requests can use web search when current information is required.

This allows ARC LEARNS to handle questions where model knowledge alone may not be sufficient.

---

### 📝 AI Quiz Generator

Generate multiple-choice quizzes from uploaded study material.

The quiz system supports:

- 1–50 questions
- Four options per question
- One correct answer
- Explanations
- JSON validation
- Duplicate-resistant question generation
- Study-material-based questions

---

### ⚡ Streaming AI

ARC LEARNS supports streaming responses for:

- AI Teacher
- ARC 0

Instead of waiting for the complete response, the frontend receives the response progressively.

---

# 🧠 How ARC LEARNS Works

```text
                STUDENT
                   │
                   ▼
              Upload PDF
                   │
                   ▼
          Document Extraction
                   │
                   ▼
             Text Cleaning
                   │
                   ▼
               Chunking
                   │
                   ▼
        Sentence Transformer
             Embeddings
                   │
                   ▼
             FAISS Vector DB
                   │
                   ▼
           Semantic Search
                   │
                   ▼
            Relevant Context
                   │
                   ▼
                RAG
                   │
                   ▼
             OpenRouter AI
                   │
          ┌────────┼────────┐
          ▼        ▼        ▼
      AI Teacher  Ask AI   Quiz
                   │
                   ▼
                Student