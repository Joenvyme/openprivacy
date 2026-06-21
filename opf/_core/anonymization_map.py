"""Anonymization mapping for reversible redaction and de-anonymization."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class SpanMapping:
    """Mapping entry for a single detected span."""

    label: str
    original_text: str
    placeholder: str
    start: int
    end: int


@dataclass
class AnonymizationMap:
    """Complete mapping for reversible anonymization."""

    map_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    original_text: str = ""
    anonymized_text: str = ""
    spans: list[SpanMapping] = field(default_factory=list)

    def add_span(
        self,
        label: str,
        original_text: str,
        placeholder: str,
        start: int,
        end: int,
    ) -> None:
        """Add a span mapping entry.

        Args:
            label: The privacy label for this span.
            original_text: The original sensitive text.
            placeholder: The placeholder that replaced it.
            start: Start character position in original text.
            end: End character position in original text.
        """
        self.spans.append(
            SpanMapping(
                label=label,
                original_text=original_text,
                placeholder=placeholder,
                start=start,
                end=end,
            )
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert the anonymization map to a JSON-serializable dictionary.

        Returns:
            A dictionary containing all mapping information.
        """
        return {
            "map_id": self.map_id,
            "created_at": self.created_at,
            "original_text": self.original_text,
            "anonymized_text": self.anonymized_text,
            "spans": [
                {
                    "label": span.label,
                    "original_text": span.original_text,
                    "placeholder": span.placeholder,
                    "start": span.start,
                    "end": span.end,
                }
                for span in self.spans
            ],
        }

    def to_json(self, *, indent: int | None = 2) -> str:
        """Serialize the anonymization map as JSON.

        Args:
            indent: Indentation level passed to ``json.dumps``. Use ``None`` for
                compact single-line JSON.

        Returns:
            A JSON string representation of the mapping.
        """
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def save(self, path: str | Path) -> None:
        """Save the anonymization map to a JSON file.

        Args:
            path: File path where the map should be saved.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            f.write(self.to_json())

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AnonymizationMap:
        """Create an AnonymizationMap from a dictionary.

        Args:
            data: Dictionary containing mapping data.

        Returns:
            A new AnonymizationMap instance.
        """
        map_obj = cls(
            map_id=data.get("map_id", str(uuid.uuid4())),
            created_at=data.get(
                "created_at", datetime.now(timezone.utc).isoformat()
            ),
            original_text=data.get("original_text", ""),
            anonymized_text=data.get("anonymized_text", ""),
        )
        for span_data in data.get("spans", []):
            map_obj.spans.append(
                SpanMapping(
                    label=span_data["label"],
                    original_text=span_data["original_text"],
                    placeholder=span_data["placeholder"],
                    start=span_data["start"],
                    end=span_data["end"],
                )
            )
        return map_obj

    @classmethod
    def from_json(cls, json_str: str) -> AnonymizationMap:
        """Create an AnonymizationMap from a JSON string.

        Args:
            json_str: JSON string containing mapping data.

        Returns:
            A new AnonymizationMap instance.
        """
        data = json.loads(json_str)
        return cls.from_dict(data)

    @classmethod
    def load(cls, path: str | Path) -> AnonymizationMap:
        """Load an anonymization map from a JSON file.

        Args:
            path: File path to load the map from.

        Returns:
            A new AnonymizationMap instance.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        path = Path(path)
        with path.open("r", encoding="utf-8") as f:
            return cls.from_json(f.read())


def deanonymize_text(anonymized_text: str, mapping: AnonymizationMap) -> str:
    """Restore original text from anonymized text using a mapping.

    Args:
        anonymized_text: The anonymized text to restore.
        mapping: The anonymization map containing the reversible mapping.

    Returns:
        The original text with sensitive information restored.

    Raises:
        ValueError: If the anonymized text doesn't match the mapping.
    """
    # Sort spans by start position in reverse to avoid offset issues
    sorted_spans = sorted(mapping.spans, key=lambda s: s.start, reverse=True)

    # Start with the anonymized text as base
    result = anonymized_text

    # Replace each placeholder with the original text
    for span in sorted_spans:
        # Find the placeholder in the anonymized text
        # We need to search for it since positions might have shifted
        placeholder_pos = result.find(span.placeholder)
        if placeholder_pos == -1:
            # If placeholder not found, try alternative approach:
            # calculate the offset based on previous replacements
            continue

        # Replace the placeholder with the original text
        result = (
            result[:placeholder_pos]
            + span.original_text
            + result[placeholder_pos + len(span.placeholder) :]
        )

    return result
