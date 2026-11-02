# Changelog

## [Unreleased]

### Fixed

- Use `defaultlib` in project examples because VHDL LS rejects the reserved `work` library name.
- Fail real-server smoke checks on configuration errors and warning notifications, which previously went unnoticed.

## [0.1.0] - 2026-11-02

### Added

- Native VHDL LS integration with pinned official downloads, project PATH discovery and explicit binary/settings overrides.
- VHDL Tree-sitter highlighting, outlines, indentation, brackets, text objects and four editing snippets.
- Real-server completion, navigation, rename and diagnostic regression checks with a VHDL-2008 blinker example.
