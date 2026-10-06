# Stage 2: Episode script

Generate a short two-speaker lesson from a study topic and show it as readable chapters. No audio in this stage.

## Data

Add an `episodes` table in a migration.

| Column | Notes |
| --- | --- |
| `id` | Primary key |
| `study_topic_id` | Foreign key, cascade delete, unique in version 1 |
| `user_id` | Owner, matches the study topic's user |
| `status` | `pending`, `ready`, or `failed` |
| `title` | Short episode title |
| `script` | JSON list of segments: `chapter`, `speaker` (`host_a` or `host_b`), `text` |
| `error_message` | Set only when `status` is `failed` |
| `created_at`, `updated_at` | Timestamps |

Store the script as JSON. On SQLite use the same JSON column approach as other non-portable types in this repo.

## Work

- [x] Add `POST /api/v1/study-topics/{id}/episode`. It loads the caller's topic, rejects a missing or empty `source_text` with 400, and creates or replaces the single episode.
- [x] Build the prompt in a new function next to the other generators in `backend/ai_utils.py`. Ask for JSON only: title plus segments. Ground it in the stored source. For long sources, select a spread of chunks with the existing `split_text` helper rather than pasting the whole document.
- [x] Validate the model output before saving: at least one chapter, both speakers present, no empty lines, and a segment count that lands near 8–12 minutes of speech (about 1,200–1,800 words). If validation fails, set `status` to `failed` and return the error. Do not save a partial script as ready.
- [x] Add `GET /api/v1/study-topics/{id}/episode` for the owner. Other users get 404.
- [x] Add a study page at `/study/:id` that shows the source title and, once ready, the script grouped by chapter. Host lines are visually distinct. A failed episode shows `error_message` and a retry button that calls the same POST.
- [x] Link each saved topic on the dashboard to `/study/:id`.

## Tests

- [x] Unit test the parser against a valid script, missing speakers, empty text, and non-JSON.
- [x] API test with the LLM mocked: ready episode persists and a second POST replaces it.
- [x] API test: topic with no source text returns 400.
- [x] Frontend test: chapters render host lines in order, and the failed state shows the error.

## Done when

Opening a saved topic generates a script, the page shows it by chapter, and a bad model response is visible as a failure with retry. No audio file is created.

## Leave for later

Playback, timestamps, and text-to-speech. The script JSON is the input to stage 3, so keep the segment shape stable.
