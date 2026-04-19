#!/usr/bin/env python3

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import subprocess
from collections import OrderedDict
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_URL = "https://platform.claude.com/docs/en/release-notes/system-prompts"
README_BADGE = "https://github.com/congmnguyen/claude-system-prompts/actions/workflows/sync.yml/badge.svg"
README_WORKFLOW_URL = "https://github.com/congmnguyen/claude-system-prompts/actions/workflows/sync.yml"


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def normalize_block(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u00a0", " ")
    lines = [line.rstrip() for line in text.splitlines()]
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines)


def resolve_reference(node, registry: dict[str, object]):
    if isinstance(node, str):
        match = re.fullmatch(r"\$L?([A-Za-z0-9]+)", node)
        if match:
            return registry.get(match.group(1), node)
    return node


def expand_string_references(text: str, registry: dict[str, object], seen: set[str]) -> str:
    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in registry or key in seen:
            return match.group(0)
        return render_inline(registry[key], registry, seen | {key})

    return re.sub(r"\$L?([A-Za-z0-9]+)", replace, text)


def render_inline(node, registry: dict[str, object], seen: set[str] | None = None) -> str:
    seen = seen or set()
    node = resolve_reference(node, registry)
    if node is None:
        return ""
    if isinstance(node, str):
        return expand_string_references(node, registry, seen)
    if isinstance(node, dict):
        return render_inline(node.get("children"), registry, seen)
    if isinstance(node, list):
        if len(node) == 4 and node[0] == "$" and isinstance(node[3], dict):
            tag = node[1]
            props = node[3]
            text = render_inline(props.get("children"), registry, seen)
            if tag == "strong":
                return f"**{text}**"
            if tag == "em":
                return f"*{text}*"
            if tag == "code":
                return f"`{text}`"
            return text
        return "".join(render_inline(item, registry, seen) for item in node)
    return ""


def extract_list_items(node, registry: dict[str, object]) -> list[str]:
    node = resolve_reference(node, registry)
    items: list[str] = []
    if isinstance(node, list):
        if len(node) == 4 and node[0] == "$" and node[1] == "li" and isinstance(node[3], dict):
            text = normalize_block(render_inline(node[3].get("children"), registry))
            if text:
                items.append(text)
            return items
        for item in node:
            items.extend(extract_list_items(item, registry))
    elif isinstance(node, dict):
        for value in node.values():
            items.extend(extract_list_items(value, registry))
    return items


def extract_blocks(node, registry: dict[str, object]) -> list[str]:
    node = resolve_reference(node, registry)
    blocks: list[str] = []
    if isinstance(node, dict):
        content_type = node.get("contentType")
        if content_type == "paragraph":
            text = normalize_block(render_inline(node.get("children"), registry))
            if text:
                blocks.append(text)
            return blocks
        if content_type == "list":
            for item in extract_list_items(node.get("children"), registry):
                blocks.append(f"- {item}")
            return blocks
        for value in node.values():
            blocks.extend(extract_blocks(value, registry))
        return blocks
    if isinstance(node, list):
        for item in node:
            blocks.extend(extract_blocks(item, registry))
    return blocks


def extract_json_fragments(html_text: str) -> list[str]:
    pattern = re.compile(r'self\.__next_f\.push\(\[1,"((?:\\.|[^"\\])*)"\]\)</script>')
    fragments: list[str] = []
    for match in pattern.finditer(html_text):
        fragments.append(json.loads(f'"{match.group(1)}"'))
    return fragments


def parse_payload_entries(fragments: list[str]) -> tuple[list[tuple[str, object]], dict[str, object]]:
    entries: list[tuple[str, object]] = []
    registry: dict[str, object] = {}
    for fragment in fragments:
        for line in fragment.splitlines():
            if ":" not in line:
                continue
            key, payload = line.split(":", 1)
            key = key.strip()
            payload = payload.strip()
            if not payload or payload[0] not in "[{\"":
                continue
            try:
                parsed = json.loads(payload)
            except json.JSONDecodeError:
                continue
            entries.append((key, parsed))
            registry[key] = parsed
    return entries, registry


def parse_html_skeleton(html_text: str) -> list[dict]:
    text = html.unescape(html_text)
    models: list[dict] = []
    heading_pattern = re.compile(r'<h2[^>]*>.*?<div[^>]*id="(claude-[^"]+)".*?<div>(Claude [^<]+)</div>.*?</h2>', re.S)
    headings = list(heading_pattern.finditer(text))
    for index, match in enumerate(headings):
        start = match.end()
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        chunk = text[start:end]
        dates = re.findall(r'<span class="font-semibold text-text-100 flex-1 font-ui">([^<]+)</span>', chunk)
        models.append({"slug": match.group(1), "name": match.group(2), "dates": dates})
    return models


def parse_remote_source() -> OrderedDict[str, dict]:
    html_text = subprocess.check_output(
        ["curl", "-L", "--silent", "-A", "Mozilla/5.0", SOURCE_URL],
        text=True,
    )
    fragments = extract_json_fragments(html_text)
    entries, registry = parse_payload_entries(fragments)
    skeleton = parse_html_skeleton(html_text)

    section_payloads: list[dict] = []
    for _, parsed in entries:
        found_sections: list[dict] = []

        def walk(node) -> None:
            if isinstance(node, dict):
                if isinstance(node.get("title"), str) and isinstance(node.get("children"), list):
                    blocks = extract_blocks(node["children"], registry)
                    if blocks:
                        found_sections.append({"title": node["title"], "blocks": blocks})
                    return
                for value in node.values():
                    walk(value)
            elif isinstance(node, list):
                for item in node:
                    walk(item)

        walk(parsed)
        section_payloads.extend(found_sections)

    models: OrderedDict[str, dict] = OrderedDict(
        (model["name"], {"slug": model["slug"], "sections": []}) for model in skeleton
    )

    def consume(expected_title: str, model_name: str) -> dict:
        nonlocal_section_index[0] += 1
        section = section_payloads[nonlocal_section_index[0] - 1]
        if section["title"] != expected_title:
            raise RuntimeError(
                f"Section mismatch while mapping {model_name}: "
                f"expected {expected_title!r}, got {section['title']!r}."
            )
        return {"title": section["title"], "body": "\n\n".join(section["blocks"]).strip()}

    nonlocal_section_index = [0]

    for model in skeleton:
        if model["dates"]:
            models[model["name"]]["sections"].append(consume(model["dates"][0], model["name"]))

    for model in skeleton:
        for expected_title in model["dates"][1:]:
            models[model["name"]]["sections"].append(consume(expected_title, model["name"]))

    if nonlocal_section_index[0] != len(section_payloads):
        raise RuntimeError("Unmapped sections remain after processing Anthropic page content.")

    return models


def parse_markdown_source(source_path: Path) -> OrderedDict[str, dict]:
    text = source_path.read_text(encoding="utf-8")
    heading_pattern = re.compile(r"^##\s+(.+?)\n", re.M)
    matches = list(heading_pattern.finditer(text))
    models: OrderedDict[str, dict] = OrderedDict()
    for index, match in enumerate(matches):
        name = match.group(1).strip()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        section_pattern = re.compile(
            r'^<section title="([^"]+)">\n\n?(.*?)(?=^<section title="|\Z)',
            re.M | re.S,
        )
        sections = []
        for section_match in section_pattern.finditer(body):
            sections.append(
                {
                    "title": section_match.group(1).strip(),
                    "body": section_match.group(2).strip(),
                }
            )
        if not sections and body:
            sections.append({"title": "", "body": body})
        models[name] = {"slug": slugify(name), "sections": sections}
    return models


def build_model_markdown(name: str, model: dict) -> str:
    lines = [f"# {name}", "", f"Source: {SOURCE_URL}#{model['slug']}"]
    for section in model["sections"]:
        lines.extend(["", f'<section title="{section["title"]}">', ""])
        lines.append(section["body"].strip())
    return normalize_block("\n".join(lines)) + "\n"


def build_readme(models: OrderedDict[str, dict]) -> str:
    synced_on = dt.datetime.now(dt.UTC).strftime("%Y-%m-%d")
    lines = [
        "# Claude System Prompts",
        "",
        f"[![Sync Anthropic system prompts]({README_BADGE})]({README_WORKFLOW_URL})",
        "",
        "A searchable GitHub mirror of the public Anthropic Claude system prompts page.",
        "",
        "This repository tracks Anthropic Claude system prompts for Claude Opus, Claude Sonnet, and Claude Haiku,",
        "split into one Markdown file per model so the prompts are easier to browse, diff, search, and link.",
        "",
        f"Official source: {SOURCE_URL}",
        f"Last synced from the official docs: {synced_on} UTC",
        "",
        "## Why This Repo Exists",
        "",
        "- The Anthropic page is public, but a GitHub repo is easier to star, search, diff, fork, and reference.",
        "- Each model has its own file at the repository root, which makes direct linking and history tracking simpler.",
        "- A scheduled GitHub Action can refresh the repo automatically when Anthropic updates the source page.",
        "",
        "## Included Claude Models",
        "",
    ]
    for name, model in models.items():
        latest = model["sections"][0]["title"] if model["sections"] else ""
        line = f"- [{name}]({model['slug']}.md)"
        if latest:
            line += f" - latest published section: {latest}"
        lines.append(line)
    lines.extend(
        [
            "",
            "## Auto Sync",
            "",
            "- Workflow file: `.github/workflows/sync.yml`",
            "- Triggers: scheduled run plus manual `workflow_dispatch`",
            "- Update command used by CI: `python3 scripts/import_system_prompts.py --remote`",
            "- The workflow only commits when the imported output passes validation and contains no unresolved payload references.",
            "",
            "## Manual Update",
            "",
            "Recommended if you already have an exported copy of the Anthropic page:",
            "",
            "```bash",
            "python3 scripts/import_system_prompts.py --source-file /path/to/System\\ Prompts.md",
            "```",
            "",
            "You can also try a live fetch from Anthropic:",
            "",
            "```bash",
            "python3 scripts/import_system_prompts.py --remote",
            "```",
            "",
            "The live fetch path is best-effort and only writes changes when the imported output passes validation.",
            "",
            "## Notes",
            "",
            "- Content in this repo is sourced from Anthropic's official public documentation.",
            "- Anthropic may change the docs structure over time; if that happens, the import script may need adjustment.",
            "- This repository is an unofficial mirror and index, not the canonical source.",
            "",
            "Keywords: Anthropic Claude system prompts, Claude Opus system prompt, Claude Sonnet system prompt, Claude Haiku system prompt.",
            "",
        ]
    )
    return "\n".join(lines)


def write_repo(models: OrderedDict[str, dict]) -> None:
    generated = set()
    for name, model in models.items():
        filename = f"{model['slug']}.md"
        (REPO_ROOT / filename).write_text(build_model_markdown(name, model), encoding="utf-8")
        generated.add(filename)

    for path in REPO_ROOT.glob("claude-*.md"):
        if path.name not in generated:
            path.unlink()

    (REPO_ROOT / "README.md").write_text(build_readme(models), encoding="utf-8")


def validate_models(models: OrderedDict[str, dict]) -> None:
    unresolved_pattern = re.compile(r"\$L?[A-Za-z0-9]+")
    for name, model in models.items():
        if not model["sections"]:
            raise RuntimeError(f"{name} has no parsed sections.")
        for section in model["sections"]:
            body = section["body"]
            if not body.strip():
                raise RuntimeError(f"{name} / {section['title']} is empty.")
            if unresolved_pattern.search(body):
                raise RuntimeError(
                    f"{name} / {section['title']} still contains unresolved payload references."
                )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import Anthropic Claude system prompts into this repository.")
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--remote", action="store_true", help="Fetch the live Anthropic docs page.")
    source_group.add_argument("--source-file", type=Path, help="Import from a local Markdown file.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.remote:
        models = parse_remote_source()
    else:
        models = parse_markdown_source(args.source_file)
    validate_models(models)
    write_repo(models)


if __name__ == "__main__":
    main()
