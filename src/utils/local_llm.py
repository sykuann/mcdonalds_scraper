from typing import Dict, List, Any, TypedDict, Tuple
from langchain_community.llms import LlamaCpp
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain.chains import LLMChain
from langchain.schema import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor
import logging
import sqlite3
import time
import os
from datetime import datetime
from src.utils.sql_queries import FACILITY_QUERIES, get_outlets_with_facilities

# Set up logging to both file and console
def setup_logging():
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Create a timestamp for the log file name
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f'logs/local_llm_{timestamp}.log'
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            # File handler
            logging.FileHandler(log_file),
            # Console handler
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized. Log file: {log_file}")
    return logger

# Initialize logger
logger = setup_logging()

class ChatState(TypedDict):
    messages: List[Dict[str, str]]
    sql_query: str
    sql_results: List[Dict[str, Any]]

def format_context(results: List[Dict[str, Any]]) -> str:
    """Format SQL results into a context string."""
    logger.info("Formatting context for LLM...")
    
    if not results:
        return "No outlets found matching the criteria."
    
    context = "Here are the matching McDonald's outlets:\n\n"
    
    for i, outlet in enumerate(results, 1):
        logger.info(f"Processing outlet {i}: {outlet['name']}")
        
        # Log raw data
        logger.info(f"Outlet {i} raw data:")
        logger.info(f"Name: {outlet['name']}")
        logger.info(f"Address: {outlet['address']}")
        logger.info(f"Hours: {outlet['operating_hours']}")
        logger.info(f"Facilities: {outlet['facilities']}")
        
        # Truncate long strings
        name = outlet['name'][:100] if len(outlet['name']) > 100 else outlet['name']
        address = outlet['address'][:150] if len(outlet['address']) > 150 else outlet['address']
        hours = outlet['operating_hours'][:50] if len(outlet['operating_hours']) > 50 else outlet['operating_hours']
        facilities = outlet['facilities'][:200] if len(outlet['facilities']) > 200 else outlet['facilities']
        
        # Log truncated data
        logger.info(f"Outlet {i} truncated data:")
        logger.info(f"Name: {name}")
        logger.info(f"Address: {address}")
        logger.info(f"Hours: {hours}")
        logger.info(f"Facilities: {facilities}")
        
        context += f"Outlet {i}:\n"
        context += f"Name: {name}\n"
        context += f"Address: {address}\n"
        context += f"Hours: {hours}\n"
        context += f"Facilities: {facilities}\n\n"
    
    logger.info(f"Final formatted context ({len(context)} characters):")
    logger.info("-" * 80)
    logger.info(context)
    logger.info("-" * 80)
    
    return context

class LocalLLMChat:
    def __init__(self):
        """Initialize the LocalLLMChat instance."""
        self.llm = create_local_llm()
        self.workflow = create_langgraph_workflow()
        logger.info("LocalLLMChat initialized successfully")

    def determine_sql_query(self, question: str) -> str:
        """Determine the SQL query based on the question."""
        logger.info("Determining SQL query...")
        
        # Base query
        query = "SELECT Name, Address, Operating_Hours, Facilities FROM outlets WHERE 1=1"
        conditions = []
        
        # Check for facility-specific keywords
        for facility, sql_condition in FACILITY_QUERIES.items():
            if facility.lower() in question.lower():
                logger.info(f"Found facility keyword: {facility}")
                conditions.append(sql_condition)
        
        # Add conditions to query if any found
        if conditions:
            query += " AND " + " AND ".join(conditions)
        
        # Add limit to prevent context window overflow
        query += " LIMIT 10"
        
        logger.info(f"Final SQL query: {query}")
        return query

    def process_query(self, question: str) -> str:
        """Process a user query and return the response."""
        logger.info(f"Processing query: {question}")
        start_time = time.time()
        
        try:
            state = {
                "messages": [{"role": "user", "content": question}],
                "sql_query": "",
                "sql_results": []
            }
            
            result = self.workflow.invoke(state)
            response = result["messages"][-1]["content"]
            
            end_time = time.time()
            logger.info(f"Query processed in {end_time - start_time:.2f} seconds")
            
            return response
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return f"I apologize, but I encountered an error processing your query: {str(e)}"

def create_local_llm():
    """Initialize the local LLM."""
    logger.info("Initializing local LLM...")
    try:
        llm = LlamaCpp(
            model_path="models/llama-2-7b-chat.Q4_K_M.gguf",
            temperature=0.7,
            max_tokens=512,
            top_p=0.95,
            n_ctx=2048,
            n_threads=4,
            verbose=True
        )
        logger.info("Local LLM initialized successfully")
        return llm
    except Exception as e:
        logger.error(f"Error initializing local LLM: {e}")
        raise

def execute_sql_query(state: ChatState) -> ChatState:
    """Execute the determined SQL query."""
    sql_query = state.get("sql_query", "")
    logger.info(f"Executing SQL query: {sql_query}")
    
    results = []
    try:
        conn = sqlite3.connect("mcdonalds_outlets.db")
        cursor = conn.cursor()
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        conn.close()
        
        # Map the database columns to the expected format
        results = [{
            "name": row[0],  # Name
            "address": row[1],  # Address
            "operating_hours": row[2],  # Operating_Hours
            "facilities": row[3]  # Facilities
        } for row in rows]
        logger.info(f"Found {len(results)} matching outlets")
    except Exception as e:
        logger.error(f"Error executing SQL query: {e}")
    
    state["sql_results"] = results
    return state

def process_query(state: ChatState) -> ChatState:
    """Use LLM to generate a response based on SQL results."""
    logger.info("Starting LLM processing...")
    llm = create_local_llm()
    
    prompt_template = PromptTemplate(
        input_variables=["query", "context"],
        template="""
        You are a customer service assistant providing detailed information about McDonald's outlets in Malaysia.
        Use the provided context to answer the user's question. If no relevant information is found, state so.
        Keep your response concise and focused on the specific information requested.
        
        Context:
        {context}
        
        Question: {query}
        
        Answer:"""
    )
    
    chain = LLMChain(llm=llm, prompt=prompt_template)
    
    query = state["messages"][-1]["content"]
    context = format_context(state["sql_results"])
    
    try:
        logger.info("Running LLM chain...")
        response = chain.run({"query": query, "context": context})
        logger.info("Successfully generated response")
        state["messages"].append({"role": "assistant", "content": response})
    except Exception as e:
        logger.error(f"Error in LLM processing: {e}")
        state["messages"].append({
            "role": "assistant", 
            "content": "I apologize, but I encountered an error processing your query. Please try rephrasing it."
        })
    
    return state

def create_langgraph_workflow() -> StateGraph:
    """Create the LangGraph workflow."""
    logger.info("Creating LangGraph workflow...")
    workflow = StateGraph(ChatState)
    workflow.add_node("determine_sql_query", determine_sql_query)
    workflow.add_node("execute_sql_query", execute_sql_query)
    workflow.add_node("process_query", process_query)
    
    workflow.set_entry_point("determine_sql_query")
    workflow.add_edge("determine_sql_query", "execute_sql_query")
    workflow.add_edge("execute_sql_query", "process_query")
    
    logger.info("LangGraph workflow created successfully")
    return workflow.compile()

def determine_sql_query(state: ChatState) -> ChatState:
    """Determine the SQL query based on user input."""
    query = state["messages"][-1]["content"].lower()
    logger.info(f"Determining SQL query for: {query}")
    
    # Check for facility-specific keywords
    found_facilities = []
    for facility in FACILITY_QUERIES.keys():
        if facility.lower() in query:
            logger.info(f"Found facility keyword: {facility}")
            found_facilities.append(facility)
    
    if found_facilities:
        # If multiple facilities found, use the combined query function
        sql_query = get_outlets_with_facilities(found_facilities)
    else:
        # Default query if no specific facilities mentioned
        sql_query = "SELECT Name, Address, Operating_Hours, Facilities FROM outlets LIMIT 10"
    
    logger.info(f"Generated SQL query: {sql_query}")
    state["sql_query"] = sql_query
    return state

if __name__ == "__main__":
    logger.info("Starting local LLM system...")
    graph = create_langgraph_workflow()
    
    test_queries = [
        "Which outlets in KL operate 24 hours?"
        "Which outlet allows birthday parties?",
        "What are the opening hours?"
    ]
    
    for query in test_queries:
        logger.info(f"\nProcessing query: {query}")
        start_time = time.time()
        state = {"messages": [{"role": "user", "content": query}], "sql_query": "", "sql_results": []}
        result = graph.invoke(state)
        end_time = time.time()
        
        print(f"\nQuery: {query}")
        print(f"Response: {result['messages'][-1]['content']}")
        print(f"Processing time: {end_time - start_time:.2f} seconds")
        print("-" * 80)
        logger.info(f"Query processing completed in {end_time - start_time:.2f} seconds")
    
    logger.info("All queries processed successfully") 