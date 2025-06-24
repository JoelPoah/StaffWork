from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY","sk-2BhsRkf5K7CpVW5yg38IMLYviUm4OarHxZ-Uc8EEqjT3BlbkFJtvFLlwmfw7EPsBBpAFGXKHbKxtegkH-Jc5hlQY6yMA"))
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY",""))
import os

# Load your OpenAI API key from environment or hardcoded (NOT recommended for production)

app = FastAPI()

# Allow frontend access (adjust origin for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request schema
class ChatRequest(BaseModel):
    message: str
    documentContent: str

# Response schema
class ChatResponse(BaseModel):
    response: str

@app.post("/chat", response_model=ChatResponse)
async def chat_with_document(request: ChatRequest):
    prompt = f"{request.message}\n\nDocument:\n{request.documentContent[:4000]}"  # Truncate to avoid token overflow
    # prompt = f"{request.message}\n"
    print(prompt)
    try:
        response = client.chat.completions.create(model="gpt-3.5-turbo",  # Use "gpt-3.5-turbo" if on a budget
        messages=[
            {"role": "system", "content": "You are a critical academic writing assistant. Provide feedback clearly and analytically."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7)
        reply = response.choices[0].message.content
        print(reply)
        return {"response": reply}
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return {"response": "Failed to process the document. Please try again later."}


# uvicorn chatgpt:app --reload --host 0.0.0.0 --port 5001
