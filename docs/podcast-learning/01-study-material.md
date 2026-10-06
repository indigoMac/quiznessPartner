# Stage 1: Study material

Save a PDF, text file, pasted text, or public URL as a study topic before any quiz or episode exists.

Today a topic is only created as a side effect of saving a quiz (`_persist_generated_quiz` in `backend/main.py`). `list_user_study_topics` in `backend/db_utils.py` also drops topics that have zero quizzes, so an empty topic would never show up.

## Work

- [x] Add `POST /api/v1/study-topics` that accepts the same three inputs as quiz creation: a PDF or `.txt` upload, pasted text, or a URL.
- [x] Reuse `extract_text_from_pdf`, text decoding, and `fetch_url_text`. Return the existing 400 responses when the file type is wrong, the file is empty, or the URL cannot be fetched.
- [x] Create the `StudyTopic` with title, optional topic label, `source_text`, and `source_url`. Title comes from the requested topic, otherwise the page title, otherwise the filename.
- [x] Index the source with `_index_source_material`. An indexing failure is logged and does not fail the save, same as quiz creation.
- [x] Show topics that have source text and no quizzes. `can_practice` stays true when `source_text` or `topic` is present.
- [x] Add a "Save material" path on the create screen, separate from "Generate quiz". Generating a quiz from `/quiz/new` stays as it is.
- [x] List the new topic on the dashboard with its title and source, and no quiz rows yet.

## Tests

- [x] API test: PDF, text, and URL each create a topic owned by the logged-in user and return an id.
- [x] API test: another user cannot read that topic.
- [x] API test: empty extraction and a bad URL return 400 and create nothing.
- [x] `list_user_study_topics` includes a topic with no quizzes.
- [x] Frontend test: saving material does not navigate into a quiz.

## Done when

A logged-in user can save a PDF or URL, see it on the dashboard with no quiz, and the existing upload-to-quiz buttons still create a quiz.

## Leave for later

Episode records, scripts, audio, and a dedicated study page. Stage 5 is what adds "generate a test" from this saved topic. The dashboard only has to show the topic for now.
