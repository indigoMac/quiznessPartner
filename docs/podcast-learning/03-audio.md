# Stage 3: Audio

Turn a ready script into one audio file, stored outside the database, without holding the HTTP request open.

Speech for a 10 minute episode takes longer than a normal request and costs money. The POST that starts it returns immediately. The client polls until the file is ready.

## Data

Extend `episodes` in a migration.

| Column | Notes |
| --- | --- |
| `audio_status` | `none`, `generating`, `ready`, or `failed` |
| `audio_error` | Set only when audio failed |
| `duration_seconds` | Filled when the file is ready |
| `segment_timings` | JSON list aligned with `script`: start and end in seconds for each segment |

`status` from stage 2 stays the script status. Audio has its own status so a readable script survives a speech failure.

## Storage

Add a small storage interface with one implementation that writes under a configurable directory (`EPISODE_MEDIA_DIR`). The database stores the object key, not a filesystem path.

The backend container in `docker-compose.yml` has no file volume today, so a file written inside the container disappears on recreate. Mount `EPISODE_MEDIA_DIR` as a named volume in development. Swap the storage implementation for object storage before production. Do not add that provider in this stage.

## Work

- [x] Add `POST /api/v1/study-topics/{id}/episode/audio`. It requires `status == ready`. It sets `audio_status` to `generating` and returns the episode. A second request while `generating` returns the same episode and does not start another job.
- [x] Run synthesis in a background task. One voice per host. Concatenate the segment files in script order into one audio file. Record each segment's start and end in `segment_timings`.
- [x] On success, set `audio_status` to `ready` and store duration. On failure, set `audio_status` to `failed` and store `audio_error`. Leave the script intact.
- [x] Add `GET /api/v1/study-topics/{id}/episode/audio` that streams the file to the owner. Everyone else gets 404. Reject the request when audio is not ready.
- [x] If the process dies mid-job, the row can sit at `generating`. A retry POST is allowed when status is `failed`. Document that a stuck `generating` row is cleared by restarting generation only after a timeout you choose and record here (suggested: 15 minutes).
- [x] On the study page, a "Generate audio" button starts the job. Poll `GET` episode until `audio_status` is `ready` or `failed`. Show the error on failure.

## Tests

- [x] Unit test timing math from a sequence of fake segment durations.
- [x] API test with speech and storage mocked: POST returns `generating`, the task reaches `ready`, and the audio GET returns bytes only for the owner.
- [x] API test: calling POST while `generating` does not invoke speech twice.
- [x] API test: speech failure sets `audio_error` and leaves `status` as `ready`.

## Done when

A ready script can be turned into one audio file, the study page shows progress and failure, and the owner can fetch the bytes. Playback UI is stage 4.

## Stuck jobs

`audio_status` of `generating` stays in progress for 15 minutes from `updated_at`. A POST in that window returns the episode and does not start a second job. After 15 minutes, POST may start generation again. The row stores a claim token while the job runs, so a late finish from the abandoned job does not overwrite the newer one.

Speech uses Groq Orpheus (`canopylabs/orpheus-v1-english`): Host A is `autumn`, Host B is `austin`. Each request accepts at most 200 characters, so a segment is split on word boundaries, spoken in order, and concatenated before its timing is recorded. The stored object is one WAV for the whole episode.

## Leave for later

Word-level timestamps, multiple episodes, and a queue service. The background task is enough until a deploy needs work to survive process restarts without the timeout retry above.
