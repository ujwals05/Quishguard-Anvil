from crewai import Agent
from app.agents.tools import qr_extraction_tool, ocr_tool

qr_agent = Agent(
    role="Forensic Image Analyst",
    goal="Identify and extract URLs from QR codes or text within images",
    backstory="""You are a specialist in digital forensics. Your job is to take raw 
    image files and find the embedded URLs that attackers use for quishing. You are 
    meticulous and check for both QR codes and human-readable text.""",
    tools=[qr_extraction_tool, ocr_tool],
    verbose=True,
    allow_delegation=False
)