# Vibehuntr

A conversational agent that helps a group of friends plan an outing. Tell it what you feel like doing and where, and it finds real venues, works out when everyone is free, and lets the group vote on a plan together in real time.

Built on Google's [Agent Development Kit](https://google.github.io/adk-docs/) (ADK) and Gemini, with a React front end and a FastAPI back end.

## What it does

**Plans in plain language.** "Indian food in South Philly for four on Friday" becomes a Google Places search, a shortlist with links, and a follow-up question if anything is missing.

**Finds real places.** The agent searches Google Places and pulls venue details: address, hours, rating, price level and website.

**Finds a time that works.** Each person records their availability. A scheduling optimizer ranks time slots by how much of the group can make it.

**Lets the group decide together.** A planning session gives everyone a shared link. Participants vote on venues, comment, and build an itinerary. Changes reach every browser at once over WebSockets.

**Remembers the conversation.** A context manager tracks your name, location, recent searches and the venues the agent just listed. "That one" or "more details on the first" resolve without repeating yourself.

**Streams cleanly.** Responses stream token by token over Server-Sent Events. A duplicate detector catches and drops repeated content, a known failure mode of streamed LLM output.

**Previews links.** URLs in chat render as cards with title, image and favicon, fetched and cached server side.

## Architecture

```
React + Vite + Tailwind  ──HTTP / SSE / WebSocket──►  FastAPI
   (Firebase Hosting)                                  (Cloud Run)
                                                          │
                                         ┌────────────────┼────────────────┐
                                         ▼                ▼                ▼
                                   ADK agent         Planning          Link
                                  (Gemini Flash)     sessions,         previews
                                         │           votes,
                              ┌──────────┴───────┐   itinerary
                              ▼                  ▼        │
                       Event planning     Google Places   ▼
                       tools              tools         Firestore
```

The agent in [`app/agent.py`](app/agent.py) exposes 14 tools to the model:

| Area | Tools |
|---|---|
| People | `create_user`, `list_users`, `update_user_preferences`, `add_availability` |
| Groups | `create_group`, `list_groups`, `get_group_details` |
| Scheduling | `find_optimal_time` |
| Events | `create_event`, `finalize_event`, `list_events`, `submit_feedback` |
| Venues | `search_venues`, `get_venue_details` |

An optional retrieval tool answers questions from your own documents through Vertex AI Search with re-ranking. Set `USE_DOCUMENT_RETRIEVAL=true` to turn it on. It needs the full Google Cloud setup.

## Project layout

```
app/                    ADK agent and event-planning domain
  agent.py              agent definition, instructions, tool wiring
  event_planning/
    models/             users, groups, events, venues, itineraries, sessions
    services/           scheduling, recommendations, voting, itinerary, broadcast
    repositories/       Firestore and local JSON persistence
    context_manager.py  conversation memory
    duplicate_detector.py
backend/app/            FastAPI: chat, sessions, planning sessions, voting,
                        itinerary, comments, link previews, WebSocket
frontend/src/           React 19 + TypeScript chat and group-planning UI
tests/                  unit, integration, property-based (Hypothesis), load
deployment/terraform/   Google Cloud infrastructure
.cloudbuild/            PR checks, staging, and production pipelines
```

## Running it locally

You need [uv](https://docs.astral.sh/uv/), Node.js 18+, a Gemini API key, and a Google Places API key.

```sh
cp .env.example .env        # add GOOGLE_API_KEY and GOOGLE_PLACES_API_KEY
./start_app.sh              # installs dependencies, starts both servers, opens the browser
```

`./stop_app.sh` and `./restart_app.sh` do what they say. To run the pieces by hand:

```sh
make install
(cd frontend && npm install)
uv run uvicorn backend.app.main:app --reload --port 8000   # terminal 1
(cd frontend && npm run dev)                               # terminal 2, then open http://localhost:5173
```

See [`.env.example`](.env.example) for every setting, including session timeout, CORS origins, and link-preview limits.

## Tests and checks

About 800 tests cover the domain models, services, API, streaming, and duplicate detection. Property-based tests use Hypothesis to check invariants such as "a streamed response never repeats content it already sent."

```sh
make test     # unit and integration
uv run pytest tests/property
make lint     # codespell, ruff, mypy
```

## Deployment

The back end runs on Cloud Run and the front end on Firebase Hosting. Cloud Build runs checks on each pull request, deploys to staging on merge, and deploys to production through a separate pipeline. Terraform in `deployment/terraform/` provisions the Google Cloud resources. [`PRODUCTION_DEPLOYMENT.md`](PRODUCTION_DEPLOYMENT.md) has the full runbook, and `scripts/rollback-production.sh` reverts a bad release.

## How it was built

The repo started from Google's [agent-starter-pack](https://github.com/GoogleCloudPlatform/agent-starter-pack). Features were planned as specs in [`.kiro/specs/`](.kiro/specs/), each with requirements, a design, and a task list. Several specs document real debugging work: context retention across turns, and duplicated content in streamed responses.

---

Built by [Avniel Dravid](https://github.com/avdrav1) · [LinkedIn](https://www.linkedin.com/in/dravid)
