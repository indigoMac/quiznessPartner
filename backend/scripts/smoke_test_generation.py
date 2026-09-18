"""Generate a real quiz against the configured LLM provider.

The unit tests stub the HTTP client, so they prove the collection and top-up
logic but not that the provider accepts our request. This script closes that
gap: it makes real API calls and fails loudly if the provider rejects the
JSON schema or returns fewer questions than asked for.

Run it by hand or from a deploy pipeline, never as part of the normal test
run, because it costs money and needs network access. Run it as a module
from the backend directory so the package imports resolve:

    LLM_API_KEY=... python3 -m scripts.smoke_test_generation
    LLM_API_KEY=... python3 -m scripts.smoke_test_generation --questions 15
"""

import argparse
import logging

from env_loader import load_app_env

load_app_env()

from ai_utils import (  # noqa: E402
    QuizGenerationError,
    _llm_base_url,
    _llm_model,
    _response_format,
    generate_quiz_from_text,
)

SOURCE_TEXT = """
Photosynthesis is the process by which green plants, algae and some bacteria
convert light energy into chemical energy stored as glucose. It takes place in
the chloroplasts, organelles containing the green pigment chlorophyll that
absorbs light most strongly in the blue and red parts of the spectrum.

The process has two stages. The light-dependent reactions occur in the
thylakoid membranes, where absorbed light splits water molecules in a step
called photolysis, releasing oxygen as a by-product and producing the energy
carriers ATP and NADPH. The light-independent reactions, known as the Calvin
cycle, take place in the stroma, where the enzyme RuBisCO fixes carbon dioxide
and uses ATP and NADPH to build glucose.

Several factors limit the rate of photosynthesis, including light intensity,
carbon dioxide concentration and temperature. At low light the rate rises with
intensity, but beyond a saturation point another factor becomes limiting. Very
high temperatures reduce the rate because the enzymes involved denature.
"""


def _check(label: str, passed: bool, detail: str = "") -> bool:
    print(f"{'PASS' if passed else 'FAIL'}  {label}{f': {detail}' if detail else ''}")
    return passed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions", type=int, default=10)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )

    model = _llm_model()
    print(f"provider : {_llm_base_url()}")
    print(f"model    : {model}")
    print(f"schema   : {'strict' if _response_format(model) else 'not sent'}")
    print(f"asking   : {args.questions} questions\n")

    try:
        quiz = generate_quiz_from_text(
            SOURCE_TEXT, topic="Photosynthesis", num_questions=args.questions
        )
    except QuizGenerationError as exc:
        print(f"FAIL  generation raised: {exc}")
        return 1

    texts = [question["question"] for question in quiz.questions]
    results = [
        _check(
            "question count",
            len(quiz.questions) == args.questions,
            f"got {len(quiz.questions)} of {args.questions}",
        ),
        _check(
            "no duplicates",
            len(set(texts)) == len(texts),
            f"{len(set(texts))} unique of {len(texts)}",
        ),
        _check("title present", bool(quiz.title and quiz.title != "Untitled Quiz")),
        _check(
            "answers in range",
            all(
                0 <= question["correct_answer"] < len(question["options"])
                for question in quiz.questions
            ),
        ),
        _check(
            "four options each",
            all(len(question["options"]) == 4 for question in quiz.questions),
        ),
    ]

    print(f'\ntitle: "{quiz.title}"   topic: "{quiz.topic}"')
    if args.verbose:
        for index, question in enumerate(quiz.questions, start=1):
            answer = question["options"][question["correct_answer"]]
            print(f'  {index}. {question["question"]}  -> {answer}')

    passed = all(results)
    print("\nALL PASS" if passed else "\nFAILURES PRESENT")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
