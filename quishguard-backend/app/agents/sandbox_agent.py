from crewai import Agent
from app.agents.tools import sandbox_investigation_tool

sandbox_agent = Agent(
    role="Sandbox Investigator",
    goal="Safely browse URLs to identify redirects and credential-harvesting forms",
    backstory="""You operate in an isolated environment. You follow every redirect 
    to the final destination and look for 'Visual Phishing' indicators like 
    fake login screens or brand impersonation.""",
    tools=[sandbox_investigation_tool],
    verbose=True,
    allow_delegation=False
)