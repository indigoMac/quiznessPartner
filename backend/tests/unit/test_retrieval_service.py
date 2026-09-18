from unittest.mock import MagicMock, patch

import pytest

from models.source_chunk import EMBEDDING_DIMENSIONS
from services.retrieval_service import (
    RETRIEVAL_CHUNK_SIZE,
    RetrievalError,
    chunk_source_text,
    embed_texts,
    index_study_topic,
    retrieval_enabled,
    search_study_topic,
)


def _vector(seed: float = 0.1):
    return [seed] * EMBEDDING_DIMENSIONS


def _embedding_response(*vectors):
    return MagicMock(
        data=[
            MagicMock(index=index, embedding=vector)
            for index, vector in enumerate(vectors)
        ]
    )


class TestChunking:
    def test_returns_nothing_for_blank_text(self):
        assert chunk_source_text("   ") == []
        assert chunk_source_text("") == []

    def test_keeps_short_text_as_one_passage(self):
        assert chunk_source_text("A short note about rivers.") == [
            "A short note about rivers."
        ]

    def test_splits_long_text_into_several_passages(self):
        text = "This sentence is part of a much longer document. " * 120
        chunks = chunk_source_text(text)

        assert len(chunks) > 1
        assert all(chunk.strip() for chunk in chunks)

    def test_passages_overlap_so_boundaries_are_not_lost(self):
        """A point split across a boundary must survive in at least one chunk."""
        text = "".join(
            f"Sentence number {index} of the source. " for index in range(400)
        )
        chunks = chunk_source_text(text)

        joined = sum(len(chunk) for chunk in chunks)
        assert joined > len(text.strip()), "expected repeated text between chunks"

    def test_passages_are_smaller_than_generation_chunks(self):
        from ai_utils import SOURCE_CHUNK_SIZE

        assert RETRIEVAL_CHUNK_SIZE < SOURCE_CHUNK_SIZE


class TestEmbedding:
    def test_no_texts_makes_no_api_call(self):
        with patch("services.retrieval_service.OpenAI") as mock_client:
            assert embed_texts([]) == []
        assert not mock_client.called

    @patch.dict("os.environ", {"EMBEDDING_API_KEY": "", "OPENAI_API_KEY": ""})
    def test_requires_an_api_key(self):
        with pytest.raises(RetrievalError, match="No embedding API key"):
            embed_texts(["some text"])

    @patch.dict("os.environ", {"EMBEDDING_API_KEY": "test-key"})
    @patch("services.retrieval_service.OpenAI")
    def test_returns_vectors_in_request_order(self, mock_openai_class):
        client = mock_openai_class.return_value
        # Deliberately out of order, as the API is permitted to return.
        client.embeddings.create.return_value = MagicMock(
            data=[
                MagicMock(index=1, embedding=_vector(0.2)),
                MagicMock(index=0, embedding=_vector(0.1)),
            ]
        )

        vectors = embed_texts(["first", "second"])

        assert vectors[0][0] == pytest.approx(0.1)
        assert vectors[1][0] == pytest.approx(0.2)

    @patch.dict("os.environ", {"EMBEDDING_API_KEY": "test-key"})
    @patch("services.retrieval_service.OpenAI")
    def test_rejects_a_model_with_the_wrong_dimensions(self, mock_openai_class):
        client = mock_openai_class.return_value
        client.embeddings.create.return_value = MagicMock(
            data=[MagicMock(index=0, embedding=[0.1, 0.2, 0.3])]
        )

        with pytest.raises(RetrievalError, match="dimensions"):
            embed_texts(["text"])

    @patch.dict("os.environ", {"EMBEDDING_API_KEY": "test-key"})
    @patch("services.retrieval_service.OpenAI")
    def test_batches_large_inputs(self, mock_openai_class):
        client = mock_openai_class.return_value
        client.embeddings.create.side_effect = lambda model, input: _embedding_response(
            *[_vector() for _ in input]
        )

        vectors = embed_texts([f"text {index}" for index in range(200)])

        assert len(vectors) == 200
        assert client.embeddings.create.call_count == 3

    @patch.dict("os.environ", {"EMBEDDING_API_KEY": "test-key"})
    @patch("services.retrieval_service.OpenAI")
    def test_wraps_provider_failures(self, mock_openai_class):
        client = mock_openai_class.return_value
        client.embeddings.create.side_effect = Exception("503")

        with pytest.raises(RetrievalError, match="Could not embed"):
            embed_texts(["text"])


class TestRetrievalFlag:
    @patch.dict("os.environ", {"RETRIEVAL_ENABLED": "true"})
    def test_enabled_by_truthy_values(self):
        assert retrieval_enabled() is True

    @patch.dict("os.environ", {"RETRIEVAL_ENABLED": "false"})
    def test_disabled_by_falsy_values(self):
        assert retrieval_enabled() is False

    @patch.dict("os.environ", {}, clear=True)
    def test_off_by_default(self):
        assert retrieval_enabled() is False


class TestIndexing:
    @patch("services.retrieval_service.embed_texts")
    def test_blank_source_stores_nothing(self, mock_embed):
        db = MagicMock()

        assert index_study_topic(db, 1, "   ") == 0
        assert not mock_embed.called
        db.commit.assert_called_once()

    @patch("services.retrieval_service.embed_texts")
    def test_stores_one_row_per_passage(self, mock_embed):
        mock_embed.side_effect = lambda chunks: [_vector() for _ in chunks]
        db = MagicMock()

        stored = index_study_topic(db, 7, "A note about rivers and mountains.")

        assert stored == 1
        rows = db.add_all.call_args.args[0]
        assert rows[0].study_topic_id == 7
        assert rows[0].chunk_index == 0
        assert len(rows[0].embedding) == EMBEDDING_DIMENSIONS

    @patch("services.retrieval_service.embed_texts")
    def test_reindexing_clears_the_previous_passages(self, mock_embed):
        mock_embed.side_effect = lambda chunks: [_vector() for _ in chunks]
        db = MagicMock()

        index_study_topic(db, 7, "Updated material.")

        assert db.execute.called, "expected a delete before inserting"

    @patch("services.retrieval_service.embed_texts")
    def test_does_not_store_anything_when_embedding_fails(self, mock_embed):
        mock_embed.side_effect = RetrievalError("provider down")
        db = MagicMock()

        with pytest.raises(RetrievalError):
            index_study_topic(db, 7, "A note about rivers.")

        assert not db.add_all.called


class TestSearch:
    def test_blank_query_makes_no_api_call(self):
        db = MagicMock()
        with patch("services.retrieval_service.embed_texts") as mock_embed:
            assert search_study_topic(db, 1, "  ") == []
        assert not mock_embed.called

    @patch("services.retrieval_service.embed_texts")
    def test_returns_passages_with_their_distance(self, mock_embed):
        mock_embed.return_value = [_vector()]
        db = MagicMock()
        chunk = MagicMock(chunk_index=3, content="Photosynthesis happens here.")
        db.execute.return_value.all.return_value = [(chunk, 0.12)]

        results = search_study_topic(db, 1, "where does photosynthesis happen")

        assert len(results) == 1
        assert results[0].chunk_index == 3
        assert results[0].content == "Photosynthesis happens here."
        assert results[0].distance == pytest.approx(0.12)
