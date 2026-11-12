"""The chat agent: a LangGraph graph served over AG-UI at `/agent` (see `agent.server`)."""

from dotenv import load_dotenv

# The agent's modules read os.environ when they are imported, so `.env` has to be loaded
# before any of them; the API's own settings read `.env` through pydantic-settings.
load_dotenv()
