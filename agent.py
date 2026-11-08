"""Minimal LiveKit voice agent; external services are disabled unless opted in."""

import os

from dotenv import load_dotenv

from livekit import agents
from livekit.agents import Agent, AgentServer, AgentSession
from livekit.plugins import openai, silero

load_dotenv()

_BILLING_ACK_ENV = "ENABLE_BILLABLE_VOICE_SESSIONS"
_BILLING_ACK_VALUE = "I_ACCEPT_POTENTIAL_CHARGES"


def require_billing_acknowledgment() -> None:
    """Fail closed before connecting to LiveKit or initializing paid providers."""
    if os.getenv(_BILLING_ACK_ENV) != _BILLING_ACK_VALUE:
        raise SystemExit(
            "Voice sessions are disabled by default to avoid unexpected charges. "
            f"After reviewing provider pricing, set {_BILLING_ACK_ENV}="
            f"{_BILLING_ACK_VALUE} to enable them."
        )


class VoiceAssistant(Agent):
    def __init__(self) -> None:
        # These instructions define the assistant's response style for each session.
        super().__init__(
            instructions=(
                "You are a helpful voice assistant. "
                "Keep replies concise and conversational."
            )
        )


server = AgentServer()


@server.rtc_session(agent_name="minimal-voice-agent")
async def entrypoint(ctx: agents.JobContext) -> None:
    # Keep this guard here as well as in main, so direct entrypoint calls are gated.
    require_billing_acknowledgment()

    # Silero handles speech detection locally; all OpenAI components may be billed.
    session = AgentSession(
        vad=silero.VAD.load(),
        stt=openai.STT(model="gpt-4o-mini-transcribe"),  # Speech-to-text.
        llm=openai.LLM(model="gpt-4o-mini"),  # Language-model reasoning.
        tts=openai.TTS(model="gpt-4o-mini-tts", voice="alloy"),  # Spoken reply.
    )
    # Starting the session joins the room and enables audio processing.
    await session.start(room=ctx.room, agent=VoiceAssistant())
    # Generate the first spoken turn after the room session is ready.
    await session.generate_reply(
        instructions="Greet the user and ask what they would like to build."
    )


if __name__ == "__main__":
    # The CLI starts a worker that connects to LiveKit; require explicit opt-in first.
    require_billing_acknowledgment()
    agents.cli.run_app(server)
