# AI Proposal Generator

AI Proposal Generator is a FastAPI-based backend application that generates structured project proposals using a Large Language Model (LLM) and calculates estimated project costs.

The system combines:
- Dynamic prompt generation
- LLM-based proposal creation (via Ollama)
- Rule-based cost estimation
- Structured API responses

----------------------------------------
## Features

- Generate structured business proposals
- Executive Summary
- Technical Approach
- Implementation Timeline
- Risk Assessment
- Automatic cost estimation
- REST API with Swagger documentation
- Clean modular project structure

----------------------------------------
## Tech Stack

Backend:
- Python 3.10+
- FastAPI
- Pydantic
- Requests

LLM:
- Ollama (Local LLM Server)
- llama3 model

----------------------------------------
## Project Structure

proposal_generator/
│
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI entry point
│   ├── schemas.py           # Request & response models
│   ├── prompt_builder.py    # Prompt construction logic
│   ├── generator.py         # LLM communication logic
│   ├── cost_logic.py        # Cost calculation engine
│
├── prompts/
│   └── proposal_template.txt
│
├── requirements.txt
├── README.md

----------------------------------------
## Installation

1. Clone the repository:

git clone <your-repo-url>
cd proposal_generator

2. Create virtual environment (recommended):

python -m venv venv
venv\Scripts\activate    (Windows)
source venv/bin/activate (Mac/Linux)

3. Install dependencies:

pip install -r requirements.txt

----------------------------------------
## Setup Ollama

1. Install Ollama from:
https://ollama.com

2. Start Ollama server:

ollama serve

3. Pull the llama3 model:

ollama pull llama3

----------------------------------------
## Run the Application

From the project root folder:

uvicorn app.main:app --reload

Open in browser:

http://127.0.0.1:8000/docs

----------------------------------------
## API Endpoint

POST /generate-proposal

Request Body Example:

{
  "project_title": "AI Chatbot Platform",
  "industry": "Healthcare",
  "duration_months": 6,
  "expected_users": 5000,
  "tech_stack": ["FastAPI", "React", "PostgreSQL"]
}

Response:

{
  "executive_summary": "...",
  "technical_approach": "...",
  "timeline": "...",
  "estimated_cost": {
    "development_cost": 120000,
    "infrastructure_cost": 2500,
    "contingency": 12000,
    "total_estimated_cost": 134500
  },
  "risk_assessment": "..."
}

----------------------------------------
## Cost Calculation Logic

Base Development Cost:
20000 × duration_months

Infrastructure Cost:
expected_users × 0.5

Contingency:
10% of development cost

----------------------------------------
## Future Improvements

- Add database storage
- Add authentication
- Improve cost modeling logic
- Add frontend UI
- Add PDF export functionality
- Deploy to cloud (AWS / Azure / GCP)

----------------------------------------
## Author

AI Proposal Generator Backend Project
Built using FastAPI + Ollama