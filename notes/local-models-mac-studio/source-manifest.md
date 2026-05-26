# Source Manifest

Prepared: 2026-05-26

## What Was Searched

CCC memory was queried first:

- `index_all_projects` failed because the CCC memory database reported `database disk image is malformed`.
- `recall_relevant` and `get_research_findings` returned no relevant local-model memories.
- The local Codex memory registry only surfaced unrelated Qwen/tool-call review memories, not a prior local-model-install chat.

Raw session logs were then searched directly:

- `/Users/stefanvalentinovpetrov/.codex/sessions`
- `/Users/stefanvalentinovpetrov/.claude/projects`
- `/Users/stefanvalentinovpetrov/.claude/projects/-Users-stefanvalentinovpetrov--claude-mem-observer-sessions`

The only strong local-model hit in local raw logs was the current request. The useful older adjacent research found was the 2026-05-01 `marimo_test_key` research around open-source models, Core42 Compass, Qwen/Kimi/gpt-oss, and structured output reliability.

## Found Chat Artifacts

Primary chat/session artifacts:

- `/Users/stefanvalentinovpetrov/.claude/projects/-Users-stefanvalentinovpetrov-marimo-test-key/1078006e-a623-4bae-a8ba-c907f2fd5362.jsonl`
- `/Users/stefanvalentinovpetrov/.claude/projects/-Users-stefanvalentinovpetrov--claude-mem-observer-sessions/b3360a55-d004-4128-9478-7eae69d4199d.jsonl`
- `/Users/stefanvalentinovpetrov/.claude/projects/-Users-stefanvalentinovpetrov--claude-mem-observer-sessions/7b91c119-2f40-434f-b855-0f240b67cbae.jsonl`

Markdown extraction:

- `chat-extract-2026-05-01-structured-output-research.md`

## Found Local Files

Source directory:

- `/Users/stefanvalentinovpetrov/marimo_test_key`

Copied artifacts:

- `artifacts/structured_output_eval.py`
- `artifacts/marimo_test_key_pyproject.toml`

Skipped artifacts:

- `uv.lock`: omitted because it is a large dependency lockfile and not a research document.
- `.venv/`: omitted because it is generated environment state.
- `wolfram_demo.py`: omitted because it is unrelated to the local-model recommendation.

## Destination Repository

Destination:

- `/Users/stefanvalentinovpetrov/GitHub/langgraph_experiments`

Reason:

- It is a personal GitHub repo: `https://github.com/petrovs12/langgraph_experiments.git`.
- It already had a `notes/` area.
- `cons71-ml-sandbox` was a GitHub ML sandbox candidate, but it had a large dirty worktree and belongs to `LocAI1`; committing there would risk mixing this documentation with unrelated changes.
- `superhive-ml` is GitLab, which the request explicitly excluded.

Repo state before this work:

- Branch: `main`
- HEAD: `c6f173024992c4b005a6539a4aa5e561eedcb840`
- Existing unrelated dirty files: `src/quickstart.py`, `notes/`, `sonar-project.properties`, `src/quickstart_llm.py`, `src/tools_list.py`

Only `notes/local-models-mac-studio/` should be staged for this commit.

## Mac Studio Access

Bonjour found the target:

```text
Mac Studio (3)._ssh._tcp.local can be reached at Mac-Studio-3.local.:22
```

SSH probe:

```bash
ssh -o BatchMode=yes -o ConnectTimeout=5 -o StrictHostKeyChecking=accept-new Mac-Studio-3.local 'hostname && pwd && uname -a'
```

Result:

```text
Permission denied (publickey,password,keyboard-interactive).
```

So the documentation was prepared and committed from `Stefans-MacBook-Pro-3.local`, not from inside the Mac Studio.
