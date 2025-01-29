# Echo - AI-Powered Story Generation

## Overview
What if we chronologically arrange textual narratives and train a model that can best predict the direction of its semantic narrative? Aka - can we make a model to predict future events?

## Features
- Feature 1
- Feature 2
- etc.

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
