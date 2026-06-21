# Changelog

All notable changes to OpenAI Privacy Filter will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Reversible Anonymization** : New anonymization system with mapping-based restoration capability
  - `anonymize()` function that returns anonymized text and reversible mapping
  - `deanonymize()` function to restore original text from anonymized version
  - `AnonymizationMap` class for managing reversible PII mappings
  - `SpanMapping` class for storing individual span information
  - JSON serialization/deserialization for anonymization maps
  - CLI commands: `opf anonymize` and `opf deanonymize`
  - Comprehensive documentation in `ANONYMIZATION.md`
  - Technical design document in `TECHNICAL_DESIGN_ANONYMIZATION.md`
  - Full test suite in `tests/test_anonymization.py`
  - Demo script in `examples/demo_anonymization.py`
  
- **API Extensions**
  - `OPF.anonymize()` method for reversible anonymization
  - `anonymization_map` field in `RedactionResult` (optional, backward compatible)
  - Module-level `anonymize()` and `deanonymize()` functions

- **Security Features**
  - UUID-based mapping identification
  - ISO 8601 timestamps for audit trails
  - Comprehensive security guidelines in documentation

### Changed

- Updated `README.md` with anonymization examples
- Extended CLI help text to include anonymization commands

### Security

- ⚠️ **Important**: Anonymization map files contain original sensitive data and must be stored securely
- See `ANONYMIZATION.md` for security best practices

## Notes

This is the initial changelog. Previous versions did not maintain a formal changelog.

For detailed information about the anonymization feature, see:
- [ANONYMIZATION.md](ANONYMIZATION.md) - User guide
- [TECHNICAL_DESIGN_ANONYMIZATION.md](TECHNICAL_DESIGN_ANONYMIZATION.md) - Technical details
- [examples/README_ANONYMIZATION.md](examples/README_ANONYMIZATION.md) - Examples
