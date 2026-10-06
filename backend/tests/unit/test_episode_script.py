"""Tests for turning model output into an episode script."""

import json
from unittest.mock import patch

import pytest

from ai_utils import (
    EpisodeGenerationError,
    generate_episode_script,
    parse_episode_script,
)


def _spoken(word: str, count: int) -> str:
    return " ".join([word] * count)


def _script(
    title: str = "How cells divide", *, host_b: str = "host_b", host_b_text=None
):
    if host_b_text is None:
        host_b_text = _spoken("divide", 700)
    return {
        "title": title,
        "segments": [
            {
                "chapter": "Mitosis",
                "speaker": "host_a",
                "text": _spoken("cells", 700),
            },
            {
                "chapter": "Mitosis",
                "speaker": host_b,
                "text": host_b_text,
            },
        ],
    }


def test_parse_episode_script_accepts_a_two_host_lesson():
    script = parse_episode_script(json.dumps(_script()))

    assert script.title == "How cells divide"
    assert [segment["speaker"] for segment in script.segments] == [
        "host_a",
        "host_b",
    ]
    assert script.segments[0]["chapter"] == "Mitosis"
    assert script.segments[0]["text"].startswith("cells")


def test_parse_episode_script_requires_both_speakers():
    payload = _script()
    payload["segments"][1]["speaker"] = "host_a"

    with pytest.raises(EpisodeGenerationError, match="both speakers"):
        parse_episode_script(json.dumps(payload))


def test_parse_episode_script_rejects_empty_text():
    payload = _script(host_b_text="  ")

    with pytest.raises(EpisodeGenerationError, match="empty line"):
        parse_episode_script(json.dumps(payload))


def test_parse_episode_script_rejects_non_json():
    with pytest.raises(EpisodeGenerationError, match="JSON"):
        parse_episode_script("this is not json")


@patch("ai_utils._chat_completion")
def test_generate_episode_script_uses_a_spread_of_the_source(mock_completion):
    mock_completion.return_value = json.dumps(_script())
    source = ". ".join(f"Sentence {index} about rivers" for index in range(2000))

    generate_episode_script(source, topic="Rivers")

    prompt = mock_completion.call_args.args[0]
    assert mock_completion.call_args.kwargs["constrain_to_quiz_schema"] is False
    assert mock_completion.call_args.kwargs["reasoning_effort"] == "low"
    assert mock_completion.call_args.kwargs["response_schema"]["required"] == [
        "title",
        "segments",
    ]
    assert "Rivers" in prompt
    assert len(prompt) < len(source)
    assert "Sentence 0 about rivers" in prompt
    assert "Sentence 1999 about rivers" in prompt
    assert mock_completion.call_count == 1


@patch("ai_utils._chat_completion")
def test_generate_episode_script_rewrites_a_short_draft(mock_completion):
    short = {
        "title": "Too short",
        "segments": [
            {"chapter": "Opening", "speaker": "host_a", "text": "Plants use light."},
            {"chapter": "Opening", "speaker": "host_b", "text": "They release oxygen."},
        ],
    }
    mock_completion.side_effect = [json.dumps(short), json.dumps(_script())]

    script = generate_episode_script("Plants use light to make sugar.", topic="Plants")

    assert script.title == "How cells divide"
    assert mock_completion.call_count == 2


@patch("ai_utils._chat_completion")
def test_generate_episode_script_does_not_rewrite_a_long_draft(mock_completion):
    line = " ".join(["cells"] * 1000)
    long_script = {
        "title": "Too long",
        "segments": [
            {"chapter": "Mitosis", "speaker": "host_a", "text": line},
            {"chapter": "Mitosis", "speaker": "host_b", "text": line},
        ],
    }
    mock_completion.return_value = json.dumps(long_script)

    with pytest.raises(EpisodeGenerationError, match="1200 and 1800"):
        generate_episode_script("Cells divide by mitosis.")

    assert mock_completion.call_count == 1


@patch("ai_utils._chat_completion")
def test_generate_episode_script_does_not_rewrite_invalid_json(mock_completion):
    mock_completion.return_value = "this is not json"

    with pytest.raises(EpisodeGenerationError, match="JSON"):
        generate_episode_script("Plants use light to make sugar.")

    assert mock_completion.call_count == 1
