# Minimal LiveKit Voice Agent

A small, server-side Python voice agent. It joins a LiveKit room, listens to
participant audio, detects speech and interruptions, transcribes speech, asks a
language model for a response, and returns generated speech to the room.

This project is an audio agent, not a video-chat application. It has no custom
browser UI: run the worker locally and use the LiveKit Agent Console to start a
browser-based session.

## What happens during a session

1. The LiveKit Agents worker connects to the configured LiveKit project and
   receives a room job.
2. `AgentSession` connects the audio pipeline to the room.
3. Silero VAD detects speech locally and helps the session identify turns and
   interruptions.
4. OpenAI transcription converts speech to text; an OpenAI language model
   generates a concise reply; OpenAI text-to-speech turns that reply into audio.
5. The generated audio is played back into the room. The agent also generates
   an initial spoken greeting when the session starts.

The pipeline is intentionally explicit rather than using a single real-time
speech model: each STT, LLM, and TTS stage can be understood and changed
independently. The tradeoff is that audio or transcript data is sent to OpenAI
for those stages, so review the providers' privacy terms before using real or
sensitive conversations.

## Why these choices?

- **LiveKit Agents and rooms:** LiveKit provides the WebRTC room transport and
  the Python framework for starting an agent session, routing audio, and
  coordinating the voice pipeline. The worker runs on your computer; the room
  and Agent Console are provided by LiveKit Cloud.
- **Silero VAD:** Voice activity detection helps identify when speech starts
  and ends and supports interruption handling. It runs locally, but it does not
  replace speech recognition or semantic turn understanding. It is included
  intentionally instead of relying on an implicit framework default: the
  pipeline's speech-detection component is explicit, reproducible, and easy to
  inspect or replace. Silero is a choice for this starter, not a LiveKit
  requirement.
- **OpenAI STT, LLM, and TTS:** One provider keeps the starter straightforward.
  The selected components are `gpt-4o-mini-transcribe`, `gpt-4o-mini`, and
  `gpt-4o-mini-tts` with the `alloy` voice. These are implementation defaults,
  not requirements; the plugins can be replaced with other supported providers
  and models.
- **`uv`:** It is a convenient Python project and environment manager. `uv sync`
  reads dependencies from `pyproject.toml` and creates/updates a local `.venv`;
  `uv run` runs a command in that project environment without requiring manual
  activation. Since this project does not include a lockfile, `uv` resolves
  compatible dependency versions rather than guaranteeing identical versions
  across installs. `uv` is not part of the agent or a LiveKit requirement;
  Python's built-in `venv` and `pip` can be used instead.
- **Billing acknowledgment:** Starting a worker or voice session may use
  billable LiveKit or OpenAI services. The app therefore refuses to start
  unless you explicitly opt in. This is a startup guard, not a spending limit
  or a guarantee of zero cost.

## Requirements

- Python 3.10 or newer
- Either [uv](https://docs.astral.sh/uv/) or Python's `venv` and `pip`
- A [LiveKit Cloud](https://cloud.livekit.io/) project with its server URL,
  API key, and API secret
- An OpenAI API key with access to the configured transcription, language, and
  speech models

LiveKit Cloud's developer sandbox does not make OpenAI API calls free. Check
both providers' current pricing and plan limits before enabling the agent.

## Configure credentials

Copy `.env.example` to `.env` and fill in `LIVEKIT_URL`, `LIVEKIT_API_KEY`,
`LIVEKIT_API_SECRET`, and `OPENAI_API_KEY`. Keep `.env` private; it is ignored
by git. The example deliberately leaves the billing acknowledgment blank, so
the app exits before starting its worker or connecting to a service.

Before opting in, consider setting provider-side usage limits and using a
dedicated OpenAI key. To enable the worker, set this in `.env`:

```dotenv
ENABLE_BILLABLE_VOICE_SESSIONS=I_ACCEPT_POTENTIAL_CHARGES
```

Only set this after reviewing the providers' pricing. Once enabled, running the
agent and starting sessions can incur charges. Removing or clearing this value
disables the worker again.

## Install and run with uv

From this directory:

```bash
uv sync
uv run python agent.py dev
```

`uv sync` installs the project dependencies from `pyproject.toml`. The
development command starts the local worker; use the Agent Console URL it
prints to start a session, allow microphone access, and talk to the agent.

### Run without uv

Create and activate a virtual environment, then install the agent's dependencies:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install "livekit-agents[openai]~=1.8" \
  "livekit-plugins-silero~=1.2" "python-dotenv>=1.0,<2"
python agent.py dev
```

## Safe local checks

You can check Python syntax without connecting to LiveKit or calling OpenAI:

```bash
python -m py_compile agent.py
```

The app's opt-in gate prevents worker startup unless the exact acknowledgment
value is present. It does not impose provider-side quotas, and it cannot prevent
charges after you deliberately enable and use the agent.
