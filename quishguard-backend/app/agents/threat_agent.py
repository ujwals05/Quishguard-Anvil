from crewai import Agent
from app.agents.tools import threat_intelligence_tool

threat_agent = Agent(
    role="Threat Intelligence Specialist",
    goal="Analyze URL reputation and domain age to determine a risk score",
    backstory="""You are an expert in OSINT and threat intelligence. You correlate 
    data from VirusTotal and WHOIS records to determine if a domain was 
    registered recently for a phishing campaign.""",
    tools=[threat_intelligence_tool],
    verbose=True,
    allow_delegation=True # Can ask other agents for more evidence
)