# from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage
from langchain_core.rate_limiters import InMemoryRateLimiter
from .tools import tools
from datetime import datetime
from os import environ
from dotenv import load_dotenv

load_dotenv()

rate_limiter = InMemoryRateLimiter(
    requests_per_second=0.2, 
)

api_key = environ.get("GOOGLE_API_KEY")
# gemini_llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-lite", rate_limiter=rate_limiter, api_key=api_key, temperature=0.5) #.bind_tools(tools)

llm = ChatOllama(
    model="llama3.2",  # or "phi3:mini", "gemma2:2b", etc.
    temperature=0.5,
    base_url="http://localhost:11434",  # Ollama's default port
    num_ctx=4096,  # Context window size
    top_k=10,
    top_p=0.95,
)
gemini_llm = llm.bind_tools(tools)

system_message = SystemMessage(content=f"Today's date is {datetime.today()}. You are an AI assistant tasked with being an expenses tracker for users. Your name is Reddington. You have a friendly, helpful, playful, and respectful tone.\n\nIMPORTANT TOOL CALLING GUIDELINES:\n1. Prefer making SINGLE, comprehensive tool calls rather than multiple separate calls\n2. If you need multiple pieces of information, consider whether you can achieve your goal with ONE tool call or by processing results sequentially\n3. NEVER call multiple tools at once - always prefer one tool call, wait for the result, then decide if another is needed\n4. When possible, use category-aggregating tools (like get_expenses_by_category) instead of multiple individual queries")
messages = [system_message]
