# Claude System Prompts

[![Sync Anthropic system prompts](https://github.com/congmnguyen/claude-system-prompts/actions/workflows/sync.yml/badge.svg)](https://github.com/congmnguyen/claude-system-prompts/actions/workflows/sync.yml)

Anthropic Claude system prompts for Opus, Sonnet, and Haiku, organized by model with Git history and easy diffs.

This repo turns Anthropic's public system prompts page into a GitHub-friendly tracker:
- one Markdown file per Claude model
- Git history for prompt changes over time
- easy file-level diffs, blame, forks, bookmarks, and sharing

## Why Star This Repo?

- You want Anthropic Claude system prompts in a format that is easier to search and diff than the docs page.
- You want one stable link per model, such as `claude-opus-4-7.md` or `claude-sonnet-4-6.md`.
- You want to track prompt changes over time with normal GitHub tools instead of manually checking the docs UI.
- You want a lightweight index for Claude Opus, Claude Sonnet, and Claude Haiku system prompts in one place.

## Claude Models

| Model | Latest section | File |
| --- | --- | --- |
| Claude Opus 4.7 | April 16, 2026 | [claude-opus-4-7.md](claude-opus-4-7.md) |
| Claude Sonnet 4.6 | February 17, 2026 | [claude-sonnet-4-6.md](claude-sonnet-4-6.md) |
| Claude Opus 4.6 | February 5, 2026 | [claude-opus-4-6.md](claude-opus-4-6.md) |
| Claude Opus 4.5 | January 18, 2026 | [claude-opus-4-5.md](claude-opus-4-5.md) |
| Claude Haiku 4.5 | January 18, 2026 | [claude-haiku-4-5.md](claude-haiku-4-5.md) |
| Claude Sonnet 4.5 | January 18, 2026 | [claude-sonnet-4-5.md](claude-sonnet-4-5.md) |
| Claude Opus 4.1 | August 5, 2025 | [claude-opus-4-1.md](claude-opus-4-1.md) |
| Claude Opus 4 | August 5, 2025 | [claude-opus-4.md](claude-opus-4.md) |
| Claude Sonnet 4 | August 5, 2025 | [claude-sonnet-4.md](claude-sonnet-4.md) |
| Claude Sonnet 3.7 | Feb 24th, 2025 | [claude-sonnet-3-7.md](claude-sonnet-3-7.md) |
| Claude Sonnet 3.5 | Nov 22nd, 2024 | [claude-sonnet-3-5.md](claude-sonnet-3-5.md) |
| Claude Haiku 3.5 | Oct 22, 2024 | [claude-haiku-3-5.md](claude-haiku-3-5.md) |
| Claude Opus 3 | July 12th, 2024 | [claude-opus-3.md](claude-opus-3.md) |
| Claude Haiku 3 | July 12th, 2024 | [claude-haiku-3.md](claude-haiku-3.md) |

## What This Repo Adds

- Root-level model files instead of one long docs page
- Git commits you can watch or subscribe to
- a simple [CHANGELOG.md](CHANGELOG.md) for major imported snapshots
- an import script for rebuilding the repo from a local export or a best-effort live fetch

## How To Diff Prompt Updates

On GitHub:
- open any model file and use file history
- compare commits to see exactly what changed in a prompt
- watch the repo to get notified when new snapshots land

Locally:

```bash
git log -- claude-opus-4-7.md
git diff HEAD~1 HEAD -- claude-opus-4-7.md
```

## Update Workflow

Recommended, stable path if you already exported the Anthropic page:

```bash
python3 scripts/import_system_prompts.py --source-file /path/to/System\ Prompts.md
```

Best-effort live fetch from Anthropic:

```bash
python3 scripts/import_system_prompts.py --remote
```

The scheduled GitHub Action only commits when the imported output passes validation.

## Notes

- This repository is an unofficial GitHub mirror and tracker of Anthropic's public documentation.
- Anthropic may change the docs structure over time, which can require importer updates.
- If you care about prompt diffs, prompt tracking, or Claude system prompt history, watching this repo is more useful than using it once.

Keywords: Anthropic Claude system prompts, Claude Opus system prompt, Claude Sonnet system prompt, Claude Haiku system prompt, Claude prompt diffs, Claude prompt history.
