from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, AIMessage
from .tools import tools
from datetime import datetime

gemini_llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.5).bind_tools(tools)
system_message = SystemMessage(content=f"Today's date is {datetime.today()} You are an AI assistant tasked with being and expenses tracker for users. Your name is Reddington. You have a friendly, helpful, playful, and respectful tone.")
llm_message = AIMessage(content="Hello, I'm Reddington. I will assist you with recording your expenses. How can I help you today?")
messages = [system_message, llm_message]
