# Local Models On Mac Studio M4 Max 36GB

Prepared: 2026-05-26

Target machine: Mac Studio with Apple M4 Max and 36GB unified memory.

## Recommendation

Install **Ollama first** and use **Qwen3 30B** as the main local model:

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama run qwen3:30b
```

Why this is the best first pick:

- `qwen3:30b` is a 30.5B-parameter MoE model in Q4_K_M quantization with a 19GB Ollama artifact. That leaves practical headroom inside 36GB unified memory for macOS, the runtime, context/KV cache, and normal desktop use.
- Qwen's current model notes position Qwen3 30B as a strong reasoning/instruction model despite using far fewer active parameters than its total parameter count.
- It is big enough to be materially better than 7B/8B class models, but still realistic on the base 36GB Mac Studio.

Install a second model for lower latency and coding/agent experiments:

```bash
ollama run gpt-oss:20b
```

`gpt-oss:20b` is a 14GB Ollama artifact. OpenAI's release notes say the 20B model is intended for local/on-device use and can run with 16GB memory. It is a good fast reasoning/tool-use fallback when Qwen3 30B feels too slow.

Install this smaller fallback if you want a model that stays comfortable while other apps are open:

```bash
ollama run qwen3:14b
```

## Optional Max-Quality Pick

Try `qwen3:32b` only if you are willing to keep context sizes moderate and avoid running several large apps at the same time:

```bash
ollama run qwen3:32b
```

It is a 32.8B dense model in Q4_K_M quantization with a 20GB Ollama artifact. It should fit, but the 36GB machine has less practical headroom than the raw model size suggests because the KV cache and runtime memory are not included in the model artifact size.

## Avoid On 36GB

Do not start with these as daily-driver local models on the 36GB machine:

- `gpt-oss:120b`: Ollama lists a 65GB artifact, and OpenAI says the model requires around 80GB memory.
- `qwen3:235b`: too large for this class of machine.
- 70B dense models at Q4: possible only with compromises on larger-memory Apple Silicon machines; not a good fit for this 36GB target.

## LM Studio

Install LM Studio if you want a GUI model browser, per-model load settings, and an OpenAI-compatible local server:

- LM Studio supports Apple Silicon Macs and recommends 16GB+ RAM.
- Its OpenAI-compatible endpoint is typically `http://localhost:1234/v1`.
- It supports Codex because it implements the `POST /v1/responses` endpoint.

For Codex local experiments, Ollama is the simpler first path:

```bash
codex --oss --local-provider ollama
```

For LM Studio:

```bash
codex --oss --local-provider lmstudio
```

## Smoke Test

After installing Ollama:

```bash
ollama run qwen3:30b "Give me a 5 bullet summary of what you are good at."
curl http://localhost:11434/api/chat \
  -d '{"model":"qwen3:30b","messages":[{"role":"user","content":"Reply with one short sentence."}]}'
```

If memory pressure is high, unload other models/apps or fall back to:

```bash
ollama run gpt-oss:20b
ollama run qwen3:14b
```

## Sources

- Apple Mac Studio specs: https://www.apple.com/mac-studio/specs/
- Ollama macOS install: https://ollama.com/download/mac
- Ollama `qwen3:30b`: https://ollama.com/library/qwen3:30b
- Ollama `qwen3:32b`: https://ollama.com/library/qwen3:32b
- Ollama `qwen3:14b`: https://ollama.com/library/qwen3:14b
- Ollama `gpt-oss:20b`: https://ollama.com/library/gpt-oss:20b
- Ollama `gpt-oss:120b`: https://ollama.com/library/gpt-oss:120b
- OpenAI gpt-oss release notes: https://openai.com/index/introducing-gpt-oss/
- LM Studio system requirements: https://lmstudio.ai/docs/app/system-requirements
- LM Studio OpenAI compatibility: https://lmstudio.ai/docs/developer/openai-compat
- MLX LM for Apple Silicon experiments: https://github.com/ml-explore/mlx-lm
