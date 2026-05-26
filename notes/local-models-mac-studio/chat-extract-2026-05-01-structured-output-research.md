# Chat Extract: 2026-05-01 OSS Model Structured Output Research

This is the closest prior research chat found by local CCC/cloud-memory/session search. It is not a Mac Studio local-install discussion, but it is relevant because it covers open-source model behavior, Qwen/Kimi/gpt-oss routing, and structured-output reliability.

## Source Sessions

- Primary Claude session: `/Users/stefanvalentinovpetrov/.claude/projects/-Users-stefanvalentinovpetrov-marimo-test-key/1078006e-a623-4bae-a8ba-c907f2fd5362.jsonl`
- Cloud-memory observer session: `/Users/stefanvalentinovpetrov/.claude/projects/-Users-stefanvalentinovpetrov--claude-mem-observer-sessions/b3360a55-d004-4128-9478-7eae69d4199d.jsonl`

## User Intent Captured In That Chat

Two research tracks were launched:

1. Research Core42 Compass model availability, especially Qwen and Kimi model IDs, API base URL, authentication, OpenAI compatibility, structured output, JSON schema mode, and function/tool calling.
2. Research structured output libraries for open-source LLMs over OpenAI-compatible HTTP APIs, including native `response_format`, Outlines, PydanticAI, Instructor, and DSPy.

## Key Findings

Compass model availability:

- The research reported Qwen 3 14B, Qwen 3 embedding, Qwen 3 reranker, and Kimi K2.5 entries.
- It did not find Qwen 2.5 in that Compass model list.
- It found the relevant base URL as `https://api.core42.ai/openai/deployments` for Compass docs and also used `https://foundry.core.uaen.ai71services.ai/v1` in the notebook artifact.

Structured output approaches:

- Native server-side `response_format` with JSON schema was treated as the first option when the serving layer actually supports it.
- PydanticAI `NativeOutput` over an OpenAI-compatible provider was the recommended Python path when the server supports native schema output.
- Outlines was noted as supporting OpenAI-compatible endpoints, with constraint enforcement depending on the server/backend.
- Prompt-only JSON was considered unreliable for schemas.

The notebook artifact later tested these ideas in code:

- `structured_output_eval.py` runs a Marimo experiment against Qwen/gpt-oss style endpoints.
- It compares prompt-only JSON, native response format, strict schema conversion, and tool schema approaches.
- The notebook concluded that strict schema conversion was required for reliable gpt-oss structured output in the tested deployment.

## Practical Carryover To Local Models

For local models on a Mac Studio, use this as a testing principle:

- Do not assume "JSON mode" or `response_format` is real constrained decoding until a local endpoint proves it.
- Validate a local model with a small schema matrix before trusting it for tool or data extraction workflows.
- Prefer `response_format` or named tool schemas over prompt-only JSON when the local server supports them.
- If using LM Studio locally, point OpenAI-compatible clients at `http://localhost:1234/v1`.
- If using Ollama locally, validate the exact endpoint and model combination before relying on structured output.

## Related Local Artifacts

- `artifacts/structured_output_eval.py`
- `artifacts/marimo_test_key_pyproject.toml`

These artifacts were copied from `/Users/stefanvalentinovpetrov/marimo_test_key`.
