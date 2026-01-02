# MicroLearn

**The missing link between the addictive nature of short-form social video and the structure of formal education.**

MicroLearn is an AI-powered platform that transforms the chaotic ocean of content found on YouTube Shorts, Reels, and TikTok into structured, interactive curriculums. Instead of getting lost in a random algorithmic feed, you simply type in a complex topic like 'Generative AI' and our AI instantly builds a personalized roadmap. It then aggregates and curates the perfect 60-second explainers from the open web for each step, allowing you to master complex concepts in 5-minute bursts.

**It's Duolingo for the open internet:** harnessing the high-dopamine engagement of social media to drive actual learning outcomes.

## Project Structure

```
microlearn-app/           <-- Root folder (Git lives here)
│
├── .gitignore            <-- Security guard (Ignores .env)
├── README.md             <-- Project documentation
│
├── backend/              <-- Python FastAPI backend
│   ├── main.py
│   ├── requirements.txt  <-- For Render deployment
│   ├── .env              <-- (IGNORED by git)
│   └── venv/             <-- (IGNORED by git)
│
└── frontend/             <-- React/Vite frontend
    ├── package.json
    ├── vite.config.js
    ├── src/
    └── node_modules/     <-- (IGNORED by git)
```

## Features

- 🤖 **AI-Powered Curriculum Generation**: Instantly create personalized learning paths for any complex topic
- 📱 **Short-Form Video Aggregation**: Curates 60-second explainers from YouTube Shorts, Reels, and TikTok
- 🎯 **Structured Learning**: Transform chaotic feeds into organized, progressive curriculums
- ⚡ **5-Minute Learning Bursts**: Master complex concepts in bite-sized, high-engagement sessions
- 🧠 **Dopamine-Driven Learning**: Leverage the addictive nature of social media for educational outcomes

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend Setup

```bash
cd frontend
npm install
```

### Environment Variables

Create a `.env` file in the `backend/` directory with your API keys and configuration (this file is ignored by git for security).

## Development

Start the backend server:
```bash
cd backend
python main.py
```

Start the frontend development server:
```bash
cd frontend
npm run dev
```

## Deployment

The backend is configured for deployment on Render using `requirements.txt`. The frontend can be deployed to any static hosting service (Vercel, Netlify, etc.).

