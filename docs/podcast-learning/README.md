# Podcast learning

Turn uploaded material into a short episode you can read and hear, then take a quiz on the same source.

Work the stages in order. Each one is usable on its own. Do not start a stage until the previous stage's acceptance checks pass.

| Stage | Doc | What you can do when it is done |
| --- | --- | --- |
| 1 | [Study material](01-study-material.md) | Save a PDF, text, or URL without generating a quiz |
| 2 | [Episode script](02-episode-script.md) | Read a two-speaker lesson grounded in that material |
| 3 | [Audio](03-audio.md) | Generate and store spoken audio for the script |
| 4 | [Player](04-player.md) | Listen while the transcript and chapters follow along |
| 5 | [Quiz](05-quiz-from-episode.md) | Generate a test from the same study topic after the episode |
| 6 | [Limits](06-limits-and-reliability.md) | Cap length and cost, retry failures, and gate by plan |

## Product decisions

These are fixed for this plan. Change them in this file before building, not halfway through a stage.

- One study topic is one source. Version 1 has one episode per topic. Regenerating replaces that episode.
- Hosts are two fixed speakers. Target length is 8–12 minutes. Hard cap is 15 minutes.
- Accepted sources stay what the app already accepts: PDF, `.txt`, pasted text, and a public URL (including a PDF URL). Word files, slides, images, and scanned papers are out of scope.
- The visual half of version 1 is the script: chapters and a transcript that tracks playback. Generated slides and diagrams are out of scope.
- The quiz reuses the existing study-topic practice flow. Do not build a second quiz generator.
- A person can read the script before any audio is generated. Audio is a separate, explicit action because text-to-speech is the expensive step.

## What already exists

Use these. Do not rebuild them.

- `POST /api/v1/upload-document` extracts PDF and text files in `backend/main.py`.
- `POST /api/v1/generate-quiz-from-url` fetches a public page or PDF in `backend/url_utils.py`.
- `POST /api/v1/generate-quiz` generates from pasted text.
- `StudyTopic` (`backend/models/study_topic.py`) stores `source_text`, `source_url`, title, and topic. It is created inside `_persist_generated_quiz` only when a quiz is saved.
- `SourceChunk` plus `backend/services/retrieval_service.py` embed that text for later lookup. Indexing is optional and must not fail the user's main request.
- `POST /api/v1/study-topics/{id}/practice` already writes a new quiz from a topic's stored source.
- The dashboard lists topics in `frontend/src/pages/Dashboard.tsx`, but `list_user_study_topics` hides a topic that has no quizzes.

## Rules for every stage

- Schema changes go through an Alembic migration. Tests run on SQLite, so new columns need a SQLite-safe type, the same way `SourceChunk.embedding` does.
- LLM and speech calls are mocked in unit tests. One scripted integration test may call the real provider behind an env flag, matching `backend/scripts/smoke_test_generation.py`.
- Errors from generation reach the UI as a message. Do not swallow them or substitute a generic success path.
- Keep quiz generation working. Uploading a file from `/quiz/new` must still create a quiz when the user asks for one.
