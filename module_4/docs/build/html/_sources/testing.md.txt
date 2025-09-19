# Testing Guide

This project uses **pytest** with custom **markers** to group tests and **coverage** to enforce 100% test coverage.

> **Run tests from the project root**: `module_4/` (not from `docs/`).

## Quick Start

```powershell
# run everything with coverage (enforces 100%)
pytest --cov=src --cov-report=term-missing --cov-fail-under=100
