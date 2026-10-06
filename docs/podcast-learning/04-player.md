# Stage 4: Player

Play the episode on the study page with the transcript and chapter list moving in step with the audio.

## Work

- [x] Add an audio player on `/study/:id` when `audio_status` is `ready`. Use the audio GET URL with the user's credentials. Support play, pause, and a seek bar.
- [x] Render the script under the player. Highlight the segment whose `segment_timings` range contains the current time. Scroll that segment into view.
- [x] Show a chapter list built from the first segment of each chapter. Choosing a chapter seeks to that segment's start time.
- [x] Keep the script readable when audio is `none` or `failed`, so stage 2 still works before anyone generates audio.
- [x] On a narrow viewport, the player stays usable: controls and the current segment fit without a horizontal scroll. Check a desktop width and a phone width.

## Tests

- [x] Frontend test: given timings, the highlighted segment changes when current time crosses a boundary.
- [x] Frontend test: choosing a chapter sets the audio time to that chapter's start.
- [x] Frontend test: a script with no audio still renders chapters and lines.

## Done when

You can press play on a generated episode, hear it, see the current line, and jump by chapter. The page still shows the script when audio has not been generated.

## Leave for later

Generated slides, diagrams, and word-by-word highlighting. Chapter and segment sync is the visual half of version 1.
