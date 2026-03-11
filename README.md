# AI Skill Gap Generator 🚀

> An intelligent platform that analyzes your skills, GitHub activity, and goals to generate personalized learning paths and identify skill gaps.

![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-181818?style=for-the-badge&logo=supabase&logoColor=3ECF8E)
![License](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)

## ✨ Features

- **6-Step Learning Wizard**: A structured, interactive setup to understand your background, skills, and goals.
- **GitHub Profile Analysis**: Integrates with GitHub to analyze your public repositories and contributions.
- **Interactive AI Chat**: Real-time assistance to guide your learning journey and answer technical questions.
- **Personalized Learning Paths**: Generates custom roadmaps to bridge your skill gaps.

## 💻 Tech Stack

| Layer | Technology |
| --- | --- |
| **Frontend** | React, Vite |
| **Backend** | Python, Flask |
| **Database & Auth** | Supabase |
| **AI / ML** | LLMs for path generation |

## 📸 Screenshots

> **Note:** To add actual screenshots, place your image files in a `docs/` or `assets/` folder and replace the placeholder URLs below.

<details>
<summary>Click to view screenshots</summary>

![Dashboard Placeholder](https://via.placeholder.com/800x450.png?text=Dashboard+Screenshot)
*Dashboard Overview*

![Wizard Placeholder](https://via.placeholder.com/800x450.png?text=6-Step+Wizard+Screenshot)
*6-Step Setup Wizard*

</details>

## 🚀 Local Setup Instructions

Follow these steps to get the project running locally.

### 1. Clone the repository
```bash
git clone https://github.com/your-username/ai-skill-gap-generator.git
cd ai-skill-gap-generator
```

### 2. Set up the Backend (Flask)
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows use: `venv\Scripts\activate`
pip install -r requirements.txt
```

### 3. Set up the Frontend (React)
```bash
cd ../frontend
npm install
```

### 4. Configure Environment Variables
Copy the `.env.example` files in both the frontend and backend directories and rename them to `.env`. Fill in the required values (see the reference table below).

### 5. Run the Application
You will need to open two separate terminal windows:

**Backend:**
```bash
cd backend
source venv/bin/activate  # Or Windows equivalent
python app.py  # or flask run
```

**Frontend:**
```bash
cd frontend
npm run dev
```

## ⚙️ Environment Variables Reference

### Backend (`backend/.env`)
| Variable | Description |
| --- | --- |
| `FLASK_ENV` | Environment context (e.g., `development`) |
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_KEY` | Your Supabase Anon/Service Key |
| `GITHUB_TOKEN` | GitHub Personal Access Token for profile analysis |
| `OPENAI_API_KEY` | API Key for AI features (or Groq/Anthropic depending on LLM used) |

### Frontend (`frontend/.env`)
| Variable | Description |
| --- | --- |
| `VITE_API_BASE_URL` | URL of the local Flask backend (e.g., `http://127.0.0.1:5000`) |
| `VITE_SUPABASE_URL` | Your Supabase project URL |
| `VITE_SUPABASE_ANON_KEY` | Your Supabase Anon Key |

## 🌍 Deployment Guide

### Frontend (Vercel)
1. Push your code to a GitHub repository.
2. Go to [Vercel](https://vercel.com/) and create a new project.
3. Import your repository.
4. Set the Framework Preset to **Vite**.
5. Set the Root Directory to `frontend`.
6. Add all Frontend Environment Variables in Vercel settings.
7. Click **Deploy**.

### Backend (Render)
1. Go to [Render](https://render.com/) and create a new **Web Service**.
2. Connect your GitHub repository.
3. Set the Root Directory to `backend`.
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `gunicorn app:app` *(Note: Ensure `gunicorn` is added to your `requirements.txt`)*
6. Add all Backend Environment Variables in Render settings.
7. Click **Create Web Service**.

## ⚠️ Known Limitations

- **GitHub API Limits:** Unauthenticated requests or free tier tokens might hit rate limits during deep profile analysis.
- **AI Processing Latency:** Generating comprehensive learning paths relies on third-party LLM APIs, which can occasionally take a few seconds to stream the full response.
- **Mobile Experience:** The 6-step wizard and dashboard are best experienced on a desktop browser.

## 📄 License

This project is licensed under the [MIT License](LICENSE).
