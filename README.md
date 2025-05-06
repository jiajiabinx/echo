# Echo - AI-Powered Story Generation

## Overview
What if we chronologically arrange textual narratives and train a model that can best predict the direction of its semantic narrative? Aka - can we make a model to predict future events?

## Video & Prototype
[Watch the demo video](https://www.loom.com/embed/adaaaf3ed7914ae690c54d4213e0909f?sid=5d0b8337-03c0-4437-831c-1be7300f4e2c)


## Technical Architecture
- Backend: FastAPI, PostgreSQL, SQLAlchemy
- AI Integration: Cohere multilingual-22-12, DeepSeek R1
- Vector Database: Pinecone


## Setup and Installation
### Prerequisites: Python 3.10, Poetry, PostgresSQL
### Environment Setup
1. Navigate to the backend directory:
```bash
cd backend
```
2. Create a virtual environment (optional but recommended):
```bash
python -m venv .venv
source .venv/bin/activate # On Windows use: .venv\Scripts\activate
```
3. Install required Python packages:
```bash
poetry install
```
### Database set-up
1. Have postgres installed on your machine
2. Initialize database
```bash
python app/databse.py
```
### Start the Backend Server
1. From the backend directory:
```bash
uvicorn app.main:app --reload
```
