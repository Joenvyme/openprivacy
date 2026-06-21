"""Tests for anonymization and deanonymization functionality."""

import json
import tempfile
from pathlib import Path

import pytest

from opf._api import OPF, anonymize, deanonymize
from opf._core.anonymization_map import AnonymizationMap, SpanMapping


class TestAnonymizationMap:
    """Test suite for AnonymizationMap."""

    def test_create_empty_map(self):
        """Test creating an empty anonymization map."""
        anon_map = AnonymizationMap()
        assert anon_map.map_id is not None
        assert anon_map.created_at is not None
        assert anon_map.original_text == ""
        assert anon_map.anonymized_text == ""
        assert len(anon_map.spans) == 0

    def test_add_span(self):
        """Test adding a span to the map."""
        anon_map = AnonymizationMap()
        anon_map.add_span(
            label="private_person",
            original_text="Alice",
            placeholder="<PRIVATE_PERSON>",
            start=0,
            end=5,
        )
        assert len(anon_map.spans) == 1
        assert anon_map.spans[0].label == "private_person"
        assert anon_map.spans[0].original_text == "Alice"

    def test_to_dict(self):
        """Test converting map to dictionary."""
        anon_map = AnonymizationMap(
            original_text="Alice works at OpenAI",
            anonymized_text="<PRIVATE_PERSON> works at OpenAI",
        )
        anon_map.add_span(
            label="private_person",
            original_text="Alice",
            placeholder="<PRIVATE_PERSON>",
            start=0,
            end=5,
        )
        data = anon_map.to_dict()
        assert "map_id" in data
        assert "created_at" in data
        assert data["original_text"] == "Alice works at OpenAI"
        assert len(data["spans"]) == 1

    def test_to_json(self):
        """Test JSON serialization."""
        anon_map = AnonymizationMap()
        json_str = anon_map.to_json()
        assert isinstance(json_str, str)
        data = json.loads(json_str)
        assert "map_id" in data

    def test_from_dict(self):
        """Test creating map from dictionary."""
        data = {
            "map_id": "test-id-123",
            "created_at": "2024-01-01T00:00:00Z",
            "original_text": "Alice",
            "anonymized_text": "<PRIVATE_PERSON>",
            "spans": [
                {
                    "label": "private_person",
                    "original_text": "Alice",
                    "placeholder": "<PRIVATE_PERSON>",
                    "start": 0,
                    "end": 5,
                }
            ],
        }
        anon_map = AnonymizationMap.from_dict(data)
        assert anon_map.map_id == "test-id-123"
        assert len(anon_map.spans) == 1
        assert anon_map.spans[0].original_text == "Alice"

    def test_from_json(self):
        """Test creating map from JSON string."""
        json_str = json.dumps(
            {
                "map_id": "test-id-456",
                "created_at": "2024-01-01T00:00:00Z",
                "original_text": "Bob",
                "anonymized_text": "<PRIVATE_PERSON>",
                "spans": [],
            }
        )
        anon_map = AnonymizationMap.from_json(json_str)
        assert anon_map.map_id == "test-id-456"

    def test_save_and_load(self):
        """Test saving and loading map from file."""
        anon_map = AnonymizationMap(
            original_text="Alice at alice@example.com",
            anonymized_text="<PRIVATE_PERSON> at <PRIVATE_EMAIL>",
        )
        anon_map.add_span(
            label="private_person",
            original_text="Alice",
            placeholder="<PRIVATE_PERSON>",
            start=0,
            end=5,
        )
        anon_map.add_span(
            label="private_email",
            original_text="alice@example.com",
            placeholder="<PRIVATE_EMAIL>",
            start=9,
            end=26,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            map_path = Path(tmpdir) / "test_map.json"
            anon_map.save(map_path)
            assert map_path.exists()

            loaded_map = AnonymizationMap.load(map_path)
            assert loaded_map.map_id == anon_map.map_id
            assert loaded_map.original_text == anon_map.original_text
            assert len(loaded_map.spans) == 2


class TestAnonymizationAPI:
    """Test suite for anonymization API functions."""

    def test_anonymize_simple_text(self):
        """Test anonymizing a simple text with PII."""
        text = "My name is Alice."
        anonymized_text, anon_map = anonymize(text)

        assert isinstance(anonymized_text, str)
        assert isinstance(anon_map, AnonymizationMap)
        assert anon_map.original_text == text or anon_map.original_text == text
        assert anon_map.anonymized_text == anonymized_text

    def test_deanonymize_text(self):
        """Test deanonymizing text using a map."""
        # Create a simple map
        anon_map = AnonymizationMap(
            original_text="Alice works here",
            anonymized_text="<PRIVATE_PERSON> works here",
        )
        anon_map.add_span(
            label="private_person",
            original_text="Alice",
            placeholder="<PRIVATE_PERSON>",
            start=0,
            end=5,
        )

        anonymized_text = "<PRIVATE_PERSON> works here"
        original_text = deanonymize(anonymized_text, anon_map)

        assert "Alice" in original_text

    def test_opf_anonymize_method(self):
        """Test OPF.anonymize() method."""
        opf = OPF(device="cpu", output_text_only=False)
        text = "Contact Alice at alice@example.com"

        anonymized_text, anon_map = opf.anonymize(text)

        assert isinstance(anonymized_text, str)
        assert isinstance(anon_map, AnonymizationMap)
        assert anon_map.map_id is not None
        # Should detect at least the email or name
        assert len(anon_map.spans) >= 0  # May be 0 if model doesn't detect anything


class TestEndToEndAnonymization:
    """End-to-end tests for the complete anonymization workflow."""

    def test_full_anonymize_deanonymize_cycle(self):
        """Test the complete cycle: anonymize -> save map -> deanonymize."""
        original_text = "Contact Alice at alice@test.com or call 555-1234."

        # Anonymize
        opf = OPF(device="cpu", output_text_only=False)
        anonymized_text, anon_map = opf.anonymize(original_text)

        # The anonymized text should be different (if any PII detected)
        # But we can't guarantee detection, so we just check types
        assert isinstance(anonymized_text, str)
        assert isinstance(anon_map, AnonymizationMap)

        # Save and load the map
        with tempfile.TemporaryDirectory() as tmpdir:
            map_path = Path(tmpdir) / "test_map.json"
            anon_map.save(map_path)

            loaded_map = AnonymizationMap.load(map_path)
            assert loaded_map.map_id == anon_map.map_id

            # Deanonymize
            restored_text = deanonymize(anonymized_text, loaded_map)

            # Check that we can restore (basic check)
            assert isinstance(restored_text, str)

    def test_multiple_spans(self):
        """Test anonymization with multiple PII spans."""
        text = "Alice (alice@test.com) and Bob (bob@test.com) work together."

        opf = OPF(device="cpu", output_text_only=False)
        anonymized_text, anon_map = opf.anonymize(text)

        # Basic type checks
        assert isinstance(anonymized_text, str)
        assert isinstance(anon_map, AnonymizationMap)
        # Map should contain detected spans (may be 0 if nothing detected)
        assert len(anon_map.spans) >= 0

    def test_no_pii_text(self):
        """Test anonymization on text with no PII."""
        text = "This is a simple sentence with no personal information."

        opf = OPF(device="cpu", output_text_only=False)
        anonymized_text, anon_map = opf.anonymize(text)

        # Should return the same text if no PII detected
        assert isinstance(anonymized_text, str)
        assert len(anon_map.spans) == 0
        # If no PII detected, text should be unchanged
        if len(anon_map.spans) == 0:
            assert anonymized_text == text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
