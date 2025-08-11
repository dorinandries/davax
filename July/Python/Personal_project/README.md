# 🧠 AI office mentors – Virtual assistant with 3 senior experts

An interactive prototype based on the OpenAI API, simulating a realistic mentorship experience within a team, with three virtual senior specialists in different roles.

## 🔍 Description

This application simulates an office room where the user can virtually approach three AI mentors, each representing a senior role in a technical team:

- 👨‍💻 **Person 1**: Senior .NET Developer (10 years of experience)
- 📊 **Person 2**: Senior Software Tester (9 years of experience)
- 🧪 **Person 3**: Senior Data Engineer (8 years of experience)

At the start of the application, the user sets up their profile: current role, experience level (junior/middle/senior), and years of experience. Then they can approach any of the three mentors to ask technical questions. The AI mentors answer based on the knowledge relevant to their specialization. If a question does not match their domain of expertise, they will redirect to the appropriate colleague.

## 🎯 Purpose

To simulate an interactive workspace for learning, mentoring and knowledge sharing, based on integration with OpenAI and advanced prompt engineering to generate realistic behaviors.

## ⚙️ Technologies

- 🧠 OpenAI API – for generating personalized AI responses  
- 🌐 React.js, ThreeJS – for the web interface  
- 🛢️ SQLite – for storing data and the questions asked to the mentors  
- 🧩 Prompt Engineering – for constructing the personalities of the three mentors  
- 🐍 Python – for backend management  

## 📦 Features

- [x] Selection of a **custom user profile** (role, level, experience)  
- [x] AI-generated responses in the style of an experienced domain expert  
- [x] Voice support (TTS and STT)  
- [x] Navigation toward any of the three people in the room 
- [x] Speed movement is faster when hold the _Shift_ key
- [x] Recommendation/redirection to the right person if the question doesn’t fit the domain
- [x] Ability to address questions to any mentor

## 🚀 Running instructions

1. **Configurations**

- Frontend
_Configure the `.env` file with the URL for the backend connection:_  
```env
VITE_API_URL='http://[link]'
```

- Backend
 _Configure the `.env` file with your OpenAI key and other settings:_  
```env
OPENAI_API_KEY=your_openai_api_key_here
JWT_SECRET=your_secret_jwt_key_here
JWT_ALGORITHM=your_jwt_algorithm_name_here
DEFAULT_EMAIL=your_default_email_here
DEFAULT_PWD=your_default_password_here
DATABASE_URL="sqlite:///your_file_name_here.db"
```

2. **Install dependencies and start the application:**

Run frontend project:
```bash
npm install
npm run dev
```

Run backend project:
```bash
python -m venv .venv
.venv\Scripts\activate 
uvicorn app:app --reload --port 8000
```

## 📌 Type of questions

- To the .NET Developer: "How can I optimize the performance of a REST API in .NET 6?"
- To the Data Engineer: "What strategy should I use for data sharing in Snowflake?"
- To the Software Tester: "How can I automate regression tests for a microservice?"

## 🧠 Prompt Engineering

Each AI mentor is configured with a custom prompt that includes:
- Name and role
- Years of experience
- Interaction style
- Expertise (clearly delineating what they know and what they DO NOT know)
- Guidelines for redirecting unsuitable questions

## 🛠 Future Developments

- [ ] Add avatar models for each mentor
- [ ] View conversation history
- [ ] Use previous questions from history to address them again to a mentor.