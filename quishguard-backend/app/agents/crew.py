"""
agents/crew.py
──────────────
QuishGuard multi-agent crew orchestration.

Creates and runs a 3-agent pipeline:
  1. Forensic Agent — QR decode + OCR to extract URLs from images
  2. Investigator Agent — sandbox visit (Playwright) to detect phishing pages
  3. Threat Agent — VirusTotal + WHOIS to score and classify the URL

Key design decisions:
  - Agents are created PER-RUN (not at module level) so image-bound tools
    get the correct path for each request.
  - The crew runs synchronously via crew.kickoff(), but scan.py calls it
    inside run_in_executor() to avoid blocking FastAPI's event loop.
  - step_callback feeds each agent thought to ReasoningLogger for the
    live dashboard WebSocket stream.
"""

import os
import logging
from pathlib import Path

from crewai import Agent, Task, Crew, Process
from app.config import settings
from app.agents.tools import (
    create_image_tools,
    sandbox_investigation_tool,
    threat_intelligence_tool,
)
from app.services.reasoning_log import agent_logger

logger = logging.getLogger(__name__)

# Ensure Groq API key is available for CrewAI's LLM
os.environ["GROQ_API_KEY"] = settings.GROQ_API_KEY

# LLM identifier for CrewAI (uses litellm format)
GROQ_LLM = "groq/llama-3.3-70b-versatile"


class QuishGuardCrew:
    """
    Orchestrates the full QuishGuard agentic scan pipeline.

    Usage:
        crew = QuishGuardCrew(image_path="/path/to/uploaded.png")
        result = crew.run()  # returns dict with verdict + reasoning chain
    """

    def __init__(self, image_path: str):
        # Validate the image exists before doing any work
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        if not path.is_file():
            raise ValueError(f"Path is not a file: {image_path}")

        self.image_path = str(path.resolve())  # normalize to absolute path
        logger.info(f"QuishGuardCrew initialized with image: {self.image_path}")

        # Reset the logger so each scan gets a clean reasoning chain
        agent_logger.reset()

    def _create_agents(self):
        """
        Create agents with image-bound tools.
        Must be called per-run so each scan gets tools bound to its image.
        """
        # Create QR + OCR tools pre-bound to this scan's image
        qr_tool, ocr_tool = create_image_tools(self.image_path)

        forensic_agent = Agent(
            role='Forensic Image Specialist',
            goal='Extract hidden URLs from images and QR codes accurately',
            backstory=(
                'Expert in digital forensics and image analysis. '
                'You never miss a hidden link. You always try the QR extraction '
                'tool first, and if it fails, you use the OCR tool as a fallback.'
            ),
            tools=[qr_tool, ocr_tool],
            llm=GROQ_LLM,
            verbose=True,
            allow_delegation=False,
        )

        investigator_agent = Agent(
            role='Sandbox Web Investigator',
            goal='Safely explore URLs to find malicious redirects and phishing forms',
            backstory=(
                'Experienced in malware analysis. You identify "Quishing" landing '
                'pages by visiting URLs in a secure sandbox and analyzing the results.'
            ),
            tools=[sandbox_investigation_tool],
            llm=GROQ_LLM,
            verbose=True,
            allow_delegation=False,
        )

        threat_agent = Agent(
            role='Cyber Threat Architect',
            goal='Correlate all evidence to provide a final risk score and verdict',
            backstory=(
                'Senior Security Operations Lead. You correlate VirusTotal hits, '
                'domain age, redirect chains, and form detection to decide if a '
                'URL should be blocked or cleared.'
            ),
            tools=[threat_intelligence_tool],
            llm=GROQ_LLM,
            verbose=True,
            allow_delegation=False,
        )

        return forensic_agent, investigator_agent, threat_agent

    def _create_tasks(self, forensic_agent, investigator_agent, threat_agent):
        """Define the sequential task chain."""

        extraction_task = Task(
            description=(
                f"An image has been uploaded for phishing analysis. "
                f"The image file is already loaded into your tools. "
                f"Step 1: Use the qr_extraction_tool to decode any QR code. "
                f"Step 2: If no QR code is found, use the ocr_url_tool to find text URLs. "
                f"Report the extracted URL and the method used."
            ),
            expected_output=(
                "The extracted URL (if found) and which method succeeded (QR or OCR). "
                "If no URL was found, state that clearly."
            ),
            agent=forensic_agent,
        )

        investigation_task = Task(
            description=(
                "Take the URL extracted by the Forensic Agent and visit it using "
                "the sandbox_investigation_tool. Analyze the results for phishing "
                "indicators: redirect chains, login forms, suspicious page titles."
            ),
            expected_output=(
                "Detailed report: final destination URL, number of redirects, "
                "whether a login/credential form was detected, and the page title."
            ),
            agent=investigator_agent,
            context=[extraction_task],
        )

        verdict_task = Task(
            description=(
                "Using the URL from the investigation, check its reputation with "
                "the reputation_intelligence_tool. Combine ALL evidence from previous "
                "agents (redirects, login forms, VirusTotal hits, domain age) to "
                "calculate a risk score from 0 to 100 and deliver a final verdict."
            ),
            expected_output=(
                "A JSON-like summary with: risk_score (0-100), verdict ('phishing', "
                "'suspicious', or 'clean'), and a list of reasons supporting the verdict."
            ),
            agent=threat_agent,
            context=[extraction_task, investigation_task],
        )

        return [extraction_task, investigation_task, verdict_task]

    def _step_callback(self, step_output):
        """
        Called by CrewAI after every agent 'thought'.
        Routes the step to our ReasoningLogger.
        """
        agent_name = "Security Agent"
        if hasattr(step_output, 'agent'):
            agent_name = str(step_output.agent)
        agent_logger.add_step(agent_name, step_output)

    def run(self):
        """
        Execute the full crew pipeline.

        Returns:
            dict with keys:
              - verdict: the raw CrewAI output
              - reasoning_chain: list of step dicts from ReasoningLogger
        """
        logger.info(f"Starting QuishGuard crew for: {self.image_path}")

        forensic, investigator, threat = self._create_agents()
        tasks = self._create_tasks(forensic, investigator, threat)

        crew = Crew(
            agents=[forensic, investigator, threat],
            tasks=tasks,
            process=Process.sequential,
            step_callback=self._step_callback,
            verbose=True,
        )

        try:
            result = crew.kickoff()
        except Exception as e:
            logger.error(f"Crew execution failed: {e}", exc_info=True)
            return {
                "verdict": f"Crew execution error: {str(e)}",
                "reasoning_chain": agent_logger.get_final_log(),
                "success": False,
            }

        logger.info("QuishGuard crew completed successfully.")
        return {
            "verdict": str(result),
            "reasoning_chain": agent_logger.get_final_log(),
            "success": True,
        }