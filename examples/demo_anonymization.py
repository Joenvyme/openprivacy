#!/usr/bin/env python3
"""Demo script for anonymization and deanonymization functionality."""

from pathlib import Path
import tempfile

from opf import anonymize, deanonymize
from opf._core.anonymization_map import AnonymizationMap


def demo_basic_usage():
    """Demonstrate basic anonymization and deanonymization."""
    print("=" * 60)
    print("DEMO: Basic Anonymization")
    print("=" * 60)
    
    # Original text with PII
    original_text = "Contact Alice at alice@example.com or call 555-1234."
    print(f"\nOriginal text:\n  {original_text}")
    
    # Anonymize
    anonymized_text, mapping = anonymize(original_text)
    print(f"\nAnonymized text:\n  {anonymized_text}")
    print(f"\nMapping ID: {mapping.map_id}")
    print(f"Number of spans detected: {len(mapping.spans)}")
    
    # Show detected spans
    if mapping.spans:
        print("\nDetected PII:")
        for span in mapping.spans:
            print(f"  - {span.label}: '{span.original_text}' -> '{span.placeholder}'")
    
    # Deanonymize
    restored_text = deanonymize(anonymized_text, mapping)
    print(f"\nRestored text:\n  {restored_text}")
    
    # Verify
    match = restored_text == original_text or restored_text == mapping.original_text
    print(f"\n✓ Restoration successful: {match}")
    print()


def demo_save_and_load():
    """Demonstrate saving and loading mapping files."""
    print("=" * 60)
    print("DEMO: Save and Load Mapping")
    print("=" * 60)
    
    original_text = "Bob works at bob@company.com, phone: +1-555-9876"
    print(f"\nOriginal text:\n  {original_text}")
    
    # Anonymize
    anonymized_text, mapping = anonymize(original_text)
    print(f"\nAnonymized text:\n  {anonymized_text}")
    
    # Save to temporary file
    with tempfile.TemporaryDirectory() as tmpdir:
        map_path = Path(tmpdir) / "demo_mapping.json"
        mapping.save(map_path)
        print(f"\nMapping saved to: {map_path}")
        
        # Load it back
        loaded_mapping = AnonymizationMap.load(map_path)
        print(f"Mapping loaded successfully (ID: {loaded_mapping.map_id})")
        
        # Deanonymize using loaded mapping
        restored_text = deanonymize(anonymized_text, loaded_mapping)
        print(f"\nRestored text:\n  {restored_text}")
    
    print()


def demo_multiple_pii():
    """Demonstrate handling multiple PII types."""
    print("=" * 60)
    print("DEMO: Multiple PII Types")
    print("=" * 60)
    
    text = """
    Employee Record:
    Name: Alice Johnson
    Email: alice.johnson@company.com
    Phone: +1-555-0123
    Address: 123 Main Street, Apt 4B
    Date of Birth: 1990-05-15
    """
    
    print(f"\nOriginal text:{text}")
    
    # Anonymize
    anonymized_text, mapping = anonymize(text)
    print(f"\nAnonymized text:{anonymized_text}")
    
    print(f"\nDetected {len(mapping.spans)} PII span(s):")
    for i, span in enumerate(mapping.spans, 1):
        print(f"  {i}. {span.label}: '{span.original_text}'")
    
    print()


def demo_no_pii():
    """Demonstrate behavior with text containing no PII."""
    print("=" * 60)
    print("DEMO: Text with No PII")
    print("=" * 60)
    
    text = "This is a simple sentence with no personal information."
    print(f"\nOriginal text:\n  {text}")
    
    anonymized_text, mapping = anonymize(text)
    print(f"\nAnonymized text:\n  {anonymized_text}")
    print(f"\nNumber of spans detected: {len(mapping.spans)}")
    
    if len(mapping.spans) == 0:
        print("✓ No PII detected - text unchanged")
    
    print()


def main():
    """Run all demo examples."""
    print("\n" + "=" * 60)
    print("OpenAI Privacy Filter - Anonymization Demo")
    print("=" * 60 + "\n")
    
    try:
        demo_basic_usage()
        demo_save_and_load()
        demo_multiple_pii()
        demo_no_pii()
        
        print("=" * 60)
        print("All demos completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
