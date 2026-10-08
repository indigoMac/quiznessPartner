# Stage 5: Quiz from the episode

After the episode, generate a quiz from the same study topic.

`POST /api/v1/study-topics/{id}/practice` already does this, and the dashboard and quiz page already call it through `practiceStudyTopic`. This stage is the entry point on the study page, not a new generator.

## Work

- [x] On `/study/:id`, add "Generate a test" once the topic has source text. It is available for a ready script even when audio has not been generated.
- [x] Call the existing practice endpoint with the study topic id, the chosen question count, and difficulty. Reuse the controls from `CreateQuiz` rather than inventing new ones.
- [x] On success, navigate to `/quiz/:id` for the new quiz.
- [x] Show the topic's existing quizzes on the study page, using the same summary fields the dashboard already renders.
- [x] Practice-again on the quiz page stays as it is.

## Tests

- [x] Frontend test: the button calls practice with the topic id and routes to the returned quiz.
- [x] Frontend test: the button stays disabled, with the API error visible, when the topic has no source.
- [x] API regression: practice still 404s for another user's topic and still creates questions from `source_text`.

## Done when

From a study topic you can read or hear the episode, generate a quiz, take it, and see that quiz listed back on the study topic.

## Leave for later

Questions that quote the episode script instead of the source text. The quiz stays grounded in `source_text`, which is what practice already uses.
