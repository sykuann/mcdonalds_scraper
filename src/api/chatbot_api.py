from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.utils.local_llm import create_langgraph_workflow
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Initialize the graph
logger.info("Initializing LangGraph workflow...")
graph = create_langgraph_workflow()
logger.info("LangGraph workflow initialized successfully")

class Query(BaseModel):
    question: str

@app.post("/chat")
async def chat(query: Query):
    try:
        logger.info(f"Received query: {query.question}")
        state = {
            "messages": [{"role": "user", "content": query.question}],
            "sql_query": "",
            "sql_results": []
        }
        
        result = graph.invoke(state)
        response = result["messages"][-1]["content"]
        filtered_outlets = result.get("sql_results", [])
        
        logger.info(f"Generated response: {response}")
        logger.info(f"Found {len(filtered_outlets)} filtered outlets")
        
        return {
            "answer": response,
            "status": "success",
            "filtered_outlets": filtered_outlets
        }
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        return {
            "answer": f"Sorry, I encountered an error: {str(e)}",
            "status": "error",
            "filtered_outlets": []
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 