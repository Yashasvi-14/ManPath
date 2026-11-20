# ManPath
### An Explainable, AI-Powered Student Well-Being Companion

ManPath is a student well-being analytics platform that uses machine learning and explainable AI to help students understand patterns between their digital habits, academic routines, lifestyle choices, and predicted mental health scores.

It combines personalized assessments, ML-based predictions, SHAP explanations, historical analytics, hypothetical simulations, and a context-aware AI assistant in one platform.

> **Disclaimer:** ManPath is an educational and informational tool. Its predictions are estimates, not clinical assessments or mental health diagnoses. It does not replace professional medical advice.

---

## Features

### 1. Student Authentication
- Email and password registration and login.
- Google authentication.
- JWT-based access and refresh token management.
- Email verification.
- Protected user-specific resources.

### 2. ML-Powered Well-Being Prediction
- Predicts a mental health score from student lifestyle and social media usage attributes.
- Uses a trained Random Forest regression pipeline.
- Validates input features against the model's expected categories and values.

### 3. Explainable AI with SHAP
- Explains individual predictions using SHAP feature contributions.
- Shows how input features contribute to the model's prediction.
- Provides a baseline score for interpreting individual predictions.

### 4. Assessment History
- Stores completed assessments.
- Retrieves user-specific assessment history.
- Supports access to individual assessment records.

### 5. Personal Analytics
- Tracks predicted score history.
- Analyzes lifestyle and habit trends.
- Provides categorical distributions and historical comparisons.
- Generates descriptive insights from assessment data.

### 6. Context-Aware AI Assistant
- Integrates Google's Gemini API.
- Uses assessment history and analytics as contextual information.
- Supports persistent conversations and message history.
- Provides personalized responses based on available user data.

### 7. What-If Simulations
- Allows hypothetical changes to assessment inputs.
- Reuses the trained prediction pipeline to calculate simulated scores.
- Distinguishes hypothetical results from actual saved assessments.

---

## Technology Stack

| Layer | Technologies |
|---|---|
| Backend | Python, FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| Validation | Pydantic |
| Machine Learning | Scikit-learn, NumPy, Pandas |
| Explainability | SHAP |
| AI Integration | Google Gemini API |
| Authentication | JWT, Argon2, Google OAuth |
| Testing | Pytest |

---

## Architecture

```text
                         ManPath
                            |
              +-------------+-------------+
              |                           |
         Frontend                    FastAPI Backend
                                          |
                +-------------------------+----------------------+
                |              |              |                  |
           Authentication  Assessments    Predictions         Chat
                |              |              |                  |
                +--------------+--------------+------------------+
                                          |
                                  Service Layer
                                          |
                  +-----------------------+--------------------+
                  |                       |                    |
              PostgreSQL            ML Prediction         Gemini AI
                  |                  Pipeline              Service
             SQLAlchemy                  |
               Alembic              Random Forest
                                        |
                                    SHAP Explainer
                                          |
                                   Explainable Results
```

---

## Project Structure

```text
ManPath/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── analytics.py
│   │   │   ├── assessments.py
│   │   │   ├── auth.py
│   │   │   ├── chat.py
│   │   │   └── predictions.py
│   │   │
│   │   ├── core/
│   │   ├── llm/
│   │   ├── ml/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── services/
│   │
│   ├── migrations/
│   ├── tests/
│   ├── requirements.txt
│   ├── alembic.ini
│   └── .env.example
│
├── frontend/
│
├── ml/
│   ├── artifacts/
│   └── notebooks/
│
├── docs/
├── .gitignore
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.13+
- PostgreSQL
- Git
- Google Gemini API key
- Google OAuth Client ID (if using Google authentication)

### 1. Clone the repository

```bash
git clone https://github.com/Yashasvi-14/ManPath.git
cd ManPath
```

### 2. Set up the backend environment

```bash
cd backend

python -m venv .venv
```

Activate the virtual environment.

**Windows PowerShell:**

```powershell
.venv\Scripts\Activate.ps1
```

**Linux/macOS:**

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file inside the `backend/` directory using `.env.example` as a reference.

Configure the following variables:

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection URL |
| `FRONTEND_URL` | Frontend origin used for CORS |
| `JWT_SECRET_KEY` | Secure JWT signing secret |
| `JWT_ALGORITHM` | JWT signing algorithm |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token expiration |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `GEMINI_API_KEY` | Google Gemini API key |
| `GEMINI_MODEL` | Gemini model identifier |

Never commit your actual `.env` file or expose API credentials.

### 5. Set up the database

Create a PostgreSQL database named `manpath_db` or configure another database through `DATABASE_URL`.

Apply database migrations:

```bash
alembic upgrade head
```

### 6. Start the backend

```bash
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

### 7. Explore the API

FastAPI interactive documentation:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
http://127.0.0.1:8000/health
```

---

## API Modules

The backend exposes the following API modules:

| Module | Responsibilities |
|---|---|
| Authentication | Registration, login, Google authentication, token refresh, email verification and logout |
| Predictions | Mental health score prediction and hypothetical simulation |
| Assessments | Assessment history and individual assessment retrieval |
| Analytics | Personal analytics and historical trends |
| Chat | AI conversations, message history and conversation management |

For exact paths, request schemas, response models, and authentication requirements, refer to the FastAPI documentation at `/docs`.

---

## Machine Learning Pipeline

ManPath uses a trained Random Forest regression pipeline to estimate a student's mental health score from lifestyle and social media usage features.

The prediction pipeline:

1. Receives and validates assessment inputs.
2. Prepares the input features in the format expected by the trained model.
3. Applies the trained preprocessing and prediction pipeline.
4. Generates a predicted score.
5. Uses SHAP to calculate feature-level contributions.
6. Returns the prediction and explanation through the API.

The model artifacts are maintained under `ml/artifacts/`.

---

## Testing

Run the backend test suite from the `backend/` directory:

```bash
pytest
```

---

## Important Limitations

- Model predictions are estimates and depend on the training dataset and model performance.
- SHAP contributions explain model behavior, not clinical causation.
- Hypothetical simulations are not actual future predictions.
- AI-generated responses may be imperfect and should not be treated as professional medical advice.
- User data and authentication credentials must be handled securely.

---

## Project Status

**Backend:** Implemented and stabilized.

**Frontend:** Pending development and integration.

**Deployment:** Pending.

---

## Author

**Yashasvi Tekriwal**

B.Tech — Electrical Engineering, Delhi Technological University

GitHub: [@Yashasvi-14](https://github.com/Yashasvi-14)

---

*ManPath — Understand patterns. Build awareness. Make informed choices.*
