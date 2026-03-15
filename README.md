# 🎤 Gemi The Robo — AI Voice Developer Assistant

**Gemi The Robo** is a voice-enabled AI agent that allows users to interact with databases using **natural language speech**.
Instead of writing queries manually, users can simply **ask questions using voice**, and the system interprets the request, retrieves relevant information from the database, and responds with a spoken answer.

This project demonstrates how **AI agents, voice interaction, and database tools** can work together to create a more intuitive developer experience.

---

# 🚀 Hackathon Category

**Live Agents — Real-Time Interaction**

The project demonstrates a real-time conversational AI system capable of:

* Natural **voice interaction**
* **Interruptible conversations**
* Intelligent **database query interpretation**
* AI-powered response generation
* Integration with **Google Cloud infrastructure**

---

# 🧠 Key Features

## Voice-First Interaction

Users can interact with the system using natural speech rather than typing commands.

The browser captures speech input and converts it into text for processing by the AI agent.

---

## AI-Driven Understanding

The AI agent interprets user intent and determines which database operation should be performed.

The system supports natural language questions such as requesting records, counting entries, or retrieving structured information.

---

## Intelligent Database Tools

The system integrates with MongoDB to perform operations such as:

* Listing available databases
* Retrieving collections
* Fetching documents
* Counting records
* Searching data

These operations are exposed through structured **AI agent tools**.

---

## Spoken Responses

After retrieving and processing the requested information, the AI assistant responds using **speech synthesis**, creating a conversational experience.

---

## Interruptible Interaction

Users can interrupt the AI response at any time using the interface controls, ensuring smooth real-time interaction.

---

# 🏗 System Architecture Overview

The system follows a layered architecture where voice input is processed by the browser, interpreted by the AI backend, and executed through database tools.

```
User
 │
 │ Voice Input
 ▼
Browser Interface
(Speech Recognition)
 │
 ▼
FastAPI Backend
 │
 │ AI Processing
 ▼
Gemini AI
 │
 │ Tool Invocation
 ▼
Agent Tool Layer
 │
 ▼
Database Tool Layer
 │
 ▼
MongoDB Database
 │
 ▼
AI Response Generated
 │
 ▼
Speech Synthesis
 │
 ▼
User Receives Spoken Answer
```

---

# 📂 Project Structure

```
project-root
│
├── backend
│   └── app.py
│
├── frontend
│   └── index.html
│
├── tools
│   ├── agent_tools.py
│   └── mongo_tools.py
│
├── requirements.txt
├── README.md
└── .env.example
```

---

# ⚙️ Installation

Clone the repository:

```
git clone <repository-url>
cd project-folder
```

Install dependencies:

```
pip install -r requirements.txt
```

Create a `.env` file with the required environment variables:

```
GEMINI_API_KEY=your_api_key
MONGO_URI=your_database_connection_string
```

Start the application:

```
uvicorn backend.app:app --reload
```

Open the application in your browser:

```
http://127.0.0.1:8000
```

---

# ☁️ Deployment

The application can be deployed using **Google Cloud Run**.

Deployment workflow:

1. Build a container image
2. Push the image to Google Container Registry
3. Deploy the container to Cloud Run
4. Configure environment variables securely in the cloud environment

This allows the AI agent to run as a scalable cloud service.

---

# 🔐 Security

Sensitive configuration values such as API keys and database credentials are not stored in the repository.

Security practices used in this project:

* `.env` files for local development
* `.gitignore` to prevent credential exposure
* Cloud environment variables for deployment

---

# 🛠 Technology Stack

Backend

* Python
* FastAPI
* MongoDB
* Google Gemini AI

Frontend

* HTML
* JavaScript
* Web Speech API

Infrastructure

* Google Cloud Run
* Containerized deployment

---

# 🎯 Project Goal

The goal of this project is to demonstrate how **AI agents combined with voice interfaces** can simplify developer workflows by enabling natural language interaction with technical systems such as databases.

---

# 👨‍💻 Author

**Yash Salve**

GitHub Profile
https://github.com/YashSalve695
