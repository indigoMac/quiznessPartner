# Stage 6: Limits and reliability

Put caps on episode size and cost, and make failures recoverable, before treating this as something users can run unsupervised.

Do this after the path from upload to quiz works. Earlier stages should use a generous dev cap so script quality is easy to judge.

## Caps

Record the numbers in settings, not in scattered checks.

| Limit | Starting value | Why |
| --- | --- | --- |
| Source characters stored for an episode | The existing source storage cap | Matches quiz generation |
| Script words | 1,800 | Keeps episodes at or under 15 minutes |
| Audio jobs per user per day | 3 on the free plan, align paid plans with `PaymentService.PLANS` | Speech is the costly call |
| Stuck `generating` audio | 15 minutes, then the retry POST may start again | Matches stage 3 |

## Work

- [ ] Reject script generation over the word cap inside the stage 2 validator if a response ignores the prompt.
- [ ] Before starting audio, check the daily job count for that user. Return 402 or 429 with a clear detail string when they are over the plan limit. Reuse the subscription lookup in `backend/services/payment_service.py`.
- [ ] Delete the stored audio object when an episode is replaced or its study topic is deleted.
- [ ] Surface script failure and audio failure as distinct messages on the study page, each with its own retry.
- [ ] Add a short note to the user-facing study page that generation can take a few minutes and that regenerating audio replaces the previous file.

## Tests

- [ ] Unit test: a script over the word cap is `failed` and is not marked ready.
- [ ] API test: the daily audio cap blocks a new job and allows it again under the cap.
- [ ] API test: replacing an episode removes the previous audio object via the storage interface.
- [ ] Frontend test: script failure and audio failure render different messages.

## Done when

A user over the cap gets a specific error, a failed script or failed audio file can be retried separately, and deleting or replacing an episode does not leave an audio file behind.

## Leave for later

Word documents, slides, scanned PDFs, and generated diagrams. Those are new ingestion and layout projects. They start only after this stage is done.
