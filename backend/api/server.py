import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from agent.invoke import invoke_agent

load_dotenv()

app = FastAPI(title="Nsight Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    cuda_code: str
    user_question: str

@app.post("/analyze")
async def analyze_code(request: AnalyzeRequest):
    result = await invoke_agent(request.cuda_code, request.user_question)
    return result

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
