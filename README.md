# Claude System Prompts

[![Sync Anthropic system prompts](https://github.com/congmnguyen/claude-system-prompts/actions/workflows/sync.yml/badge.svg)](https://github.com/congmnguyen/claude-system-prompts/actions/workflows/sync.yml)

A searchable GitHub mirror of the public Anthropic Claude system prompts page.

This repository tracks Anthropic Claude system prompts for Claude Opus, Claude Sonnet, and Claude Haiku,
split into one Markdown file per model so the prompts are easier to browse, diff, search, and link.

Official source: https://platform.claude.com/docs/en/release-notes/system-prompts
Last synced from the official docs: 2026-08-12 UTC

## Why This Repo Exists

- The Anthropic page is public, but a GitHub repo is easier to star, search, diff, fork, and reference.
- Each model has its own file at the repository root, which makes direct linking and history tracking simpler.
- A scheduled GitHub Action can refresh the repo automatically when Anthropic updates the source page.

## Included Claude Models


## Auto Sync

- Workflow file: `.github/workflows/sync.yml`
- Triggers: scheduled run plus manual `workflow_dispatch`
- Update command used by CI: `python3 scripts/import_system_prompts.py --remote`
- The workflow only commits when the imported output passes validation and contains no unresolved payload references.

## Manual Update

Recommended if you already have an exported copy of the Anthropic page:

```bash
python3 scripts/import_system_prompts.py --source-file /path/to/System\ Prompts.md
```

You can also try a live fetch from Anthropic:

```bash
python3 scripts/import_system_prompts.py --remote
```

The live fetch path is best-effort and only writes changes when the imported output passes validation.

## Notes

- Content in this repo is sourced from Anthropic's official public documentation.
- Anthropic may change the docs structure over time; if that happens, the import script may need adjustment.
- This repository is an unofficial mirror and index, not the canonical source.

Keywords: Anthropic Claude system prompts, Claude Opus system prompt, Claude Sonnet system prompt, Claude Haiku system prompt.
