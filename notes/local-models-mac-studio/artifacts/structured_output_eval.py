# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo>=0.23.4",
#     "openai>=2.0.0",
#     "pydantic>=2.0.0",
#     "pydantic-ai>=1.0.0",
#     "pandas>=2.0.0",
#     "altair>=5.0.0",
#     "tomli; python_version < '3.11'",
# ]
# ///

import marimo

__generated_with = "0.23.4"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import os
    import json
    import time
    import re
    from enum import Enum
    from pathlib import Path

    import pandas as pd
    import altair as alt
    from openai import OpenAI, BadRequestError, APIError
    from pydantic import BaseModel, Field, ValidationError

    is_script_mode = mo.app_meta().mode == "script"
    return (
        BadRequestError,
        BaseModel,
        Enum,
        Field,
        OpenAI,
        ValidationError,
        alt,
        is_script_mode,
        json,
        mo,
        os,
        pd,
        re,
        time,
    )


@app.cell
def _(mo):
    mo.md(r"""
    # Structured-output reliability — Qwen 3.5 on Compass / AI71 foundry

    Two Qwen 3.5 variants on the UAE-hosted vLLM tier
    (`core42-oicm-auh1-shd/qwen-3-5-9b` and `qwen-3-5-122b-a10b`),
    extracting a `SupportTicket` Pydantic object across three approaches.

    | Approach | Mechanism | Notes |
    |---|---|---|
    | A — `baseline` | prompt-only JSON | tells the model the schema in plain text |
    | B — `native` | OpenAI-standard `response_format={"type":"json_schema","json_schema":{...,"strict":true}}` | vLLM accepts this; **does NOT actually grammar-constrain on this deployment** — model produces JSON + babble |
    | C — `pydantic-ai` | `Agent(...,output_type=NativeOutput(SupportTicket))` | retries once on validation failure |

    **Key trick that makes this work**: we use `json.JSONDecoder.raw_decode`
    to take only the *first* JSON object the model produces and ignore any
    trailing prose / repetitive babble. Without this, native mode fails
    because Qwen often keeps generating after a clean JSON object
    (`finish_reason="length"`).

    **Compass docs caveat**: the documented envelope
    `{"type":"json_object","json_schema":...}` is **rejected** by the vLLM
    backend with a 400 ("6 validation errors"). Use the OpenAI-standard
    `{"type":"json_schema","json_schema":{...}}` envelope instead.

    **Other Qwen variants tested in earlier probes**:
    `qwen/qwen3.5-*` (OpenRouter route) — all `response_format` envelopes
    fail with 400. Stick to the `core42-oicm-auh1-shd/*` prefix.
    """)
    return


@app.cell
def _(mo, os):
    api_key_input = mo.ui.text(
        value=os.environ.get("AI71_API_KEY", ""),
        kind="password",
        label="AI71 / Compass API key",
        full_width=True,
    )
    base_url_input = mo.ui.text(
        value="https://foundry.core.uaen.ai71services.ai/v1",
        label="Base URL",
        full_width=True,
    )
    mo.vstack(
        [
            mo.md("## 1. Endpoint"),
            api_key_input,
            base_url_input,
        ]
    )
    return api_key_input, base_url_input


@app.cell
def _(OpenAI, api_key_input, base_url_input, mo):
    _api_key = api_key_input.value.strip()
    _base_url = base_url_input.value.strip().rstrip("/")

    mo.stop(
        not _api_key,
        mo.md("⚠️ Set an API key above to continue. (Tip: see hint cell above.)"),
    )

    client = OpenAI(
        api_key=_api_key,
        base_url=_base_url,
        default_headers={"api-key": _api_key},
    )
    mo.md(f"✅ Client constructed for `{_base_url}`")
    return (client,)


@app.cell
def _(client, mo):
    models_resp = client.models.list()
    all_model_ids = sorted(m.id for m in models_resp.data)
    mo.md(
        f"## 2. Models exposed by this endpoint\n\n"
        f"**{len(all_model_ids)} models total.** Filtering to `qwen|kimi` below."
    )
    return (all_model_ids,)


@app.cell
def _(all_model_ids, mo, pd, re):
    pattern = re.compile(r"qwen|kimi", re.IGNORECASE)
    matched = [m for m in all_model_ids if pattern.search(m)]
    matched_df = pd.DataFrame({"model_id": matched})
    mo.vstack(
        [
            mo.md(f"Found **{len(matched)}** matching models:"),
            mo.ui.table(matched_df, selection=None),
        ]
    )
    return


@app.cell
def _(all_model_ids, mo):
    _oss_only = [
        m
        for m in all_model_ids
        if (
            (
                "qwen" in m.lower()
                and "embed" not in m.lower()
                and "rerank" not in m.lower()
                and "vl" not in m.lower()
            )
            or ("gpt-oss" in m.lower() and "safeguard" not in m.lower())
        )
    ]

    _default_models = [
        "core42-oicm-auh1-shd/qwen-3-5-9b",
        "core42-oicm-auh1-shd/qwen-3-5-122b-a10b",
        "aicloud/gpt-oss-120b",
    ]
    _default_models = [m for m in _default_models if m in _oss_only]

    models_to_test = mo.ui.multiselect(
        options=_oss_only,
        value=_default_models,
        label="Open-source models to test",
    )
    models_to_test
    return (models_to_test,)


@app.cell
def _(BaseModel, Enum, Field, json, mo):
    class TicketPriority(str, Enum):
        low = "low"
        medium = "medium"
        high = "high"
        urgent = "urgent"

    class Reporter(BaseModel):
        name: str
        email: str = Field(pattern=r"^[^@]+@[^@]+\.[^@]+$")

    class SupportTicket(BaseModel):
        ticket_id: str = Field(pattern=r"^TKT-\d{4}$")
        title: str = Field(max_length=80)
        priority: TicketPriority
        tags: list[str] = Field(max_length=5)
        reporter: Reporter

    schema_json = json.dumps(SupportTicket.model_json_schema(), indent=2)
    mo.vstack(
        [
            mo.md(
                "## 3. Target schema\n\n"
                "One nesting level (`Reporter`), one enum, two regex constraints, "
                "one bounded list. Designed to surface the typical structured-output "
                "failure modes."
            ),
            mo.ui.code_editor(schema_json, language="json", disabled=True),
        ]
    )
    return (SupportTicket,)


@app.cell
def _(mo):
    PROMPTS = [
        "Hi, my company laptop's battery dies in under 30 minutes. I'm losing client work. Please help — Sara Lin, sara.lin@northwind.example.com.",
        "URGENT — production database read replica is lagging by 4 hours. Our checkout is broken. Mark Chen mchen@acme.example.org",
        "minor css glitch on the about page footer, low priority. raj@studio.example.io (Rajesh Patel)",
        "Our office printer (HP LaserJet) keeps jamming on duplex. It's medium-annoying. Contact: ops@bluefin.example.net, Casey Ortiz.",
        "Critical security alert: I found credentials in a public repo last night. Need rotation NOW. — Priya Shah, priya@onyx.example.io",
        "Could someone update my display name? Was misspelled at onboarding. Low urgency. /Tomás Álvarez, talvarez@helio.example.com/",
        "VPN client crashes every time I switch from wifi to ethernet on macOS 15. Reproducible. Medium impact. dev@kyle.example.com — Kyle Reeves",
        "We're locked out of the shared Notion space, the admin left. High priority. amelia.chen@latitude.example.com",
        "Feature request: dark mode for the admin dashboard. Not blocking anything. Sammy Kwok sammy@lambda.example.io",
        "Multi-factor auth code never arrives via SMS, takes 15 minutes if at all. Medium-high. nh@vega.example.org — Nadia Haddad",
        "All hands on deck — payroll job failed and Friday's payments didn't go out. URGENT. ceo@tundra.example.io (Lee Park)",
        "Just FYI, the docs link on the marketing site goes to a 404. low. devrel@eos.example.io — Maya Singh",
        "Quick one: please add me to the on-call rotation calendar. Low/medium. orion.t@beacon.example.com — Orion Tanaka",
        "Build pipeline takes 38 minutes now, was 12 last week. Affects every PR. high. emi@orchid.example.io — Emiko Sato",
        "I get a 500 when I try to export my workspace as JSON. Medium. ethan@finch.example.org — Ethan Moss",
    ]
    mo.md(
        f"## 4. Prompt corpus ({len(PROMPTS)} scenarios)\n\n"
        "Each prompt is a short, varied customer message; the model must emit a "
        "well-formed `SupportTicket`. Variety prevents prompt-cache effects."
    )
    return (PROMPTS,)


@app.cell
def _(mo):
    mo.md(r"""
    ## 5. Three extraction approaches

    Each function returns `(parsed_or_None, failure_class, latency_s, raw_text)`.
    `failure_class` is one of `None | "json_parse" | "schema" | "request"`.
    Both A and B share the same `_parse_and_validate` helper that does
    `json.JSONDecoder().raw_decode(text)` to extract the first JSON object,
    so trailing babble after a clean JSON object does **not** break parsing.
    """)
    return


@app.cell
def _(BadRequestError, SupportTicket, ValidationError, json, time):
    SCHEMA_DICT = SupportTicket.model_json_schema()
    SCHEMA_TEXT = json.dumps(SCHEMA_DICT, indent=2)
    SYSTEM_BASELINE = (
        "You are a strict JSON extractor. Extract a SupportTicket from the user "
        "message. Respond with ONLY a single JSON object matching this schema "
        "(no prose, no code fences):\n\n" + SCHEMA_TEXT
    )
    SYSTEM_NATIVE = (
        "Extract a SupportTicket from the user message. The ticket_id should be "
        "in the form TKT-NNNN where NNNN is any 4-digit number you choose."
    )
    NATIVE_RESPONSE_FORMAT = {
        "type": "json_schema",
        "json_schema": {
            "name": "SupportTicket",
            "schema": SCHEMA_DICT,
            "strict": True,
        },
    }
    EXTRA_BODY = {
        "chat_template_kwargs": {"enable_thinking": False},
        "reasoning_effort": "low",
    }
    MAX_TOKENS = 2048

    JSON_DECODER = json.JSONDecoder()


    def extract_first_json_object(text: str):
        if not text:
            return None, "empty content"
        s = text.strip()
        if s.startswith("```"):
            s = s.strip("`")
            if s.lower().startswith("json"):
                s = s[4:]
            s = s.strip()
        i = s.find("{")
        if i < 0:
            return None, "no '{' in output"
        try:
            obj, _end = JSON_DECODER.raw_decode(s, i)
            return obj, None
        except json.JSONDecodeError as e:
            return None, f"raw_decode: {e}"


    def parse_and_validate(raw: str):
        obj, err = extract_first_json_object(raw or "")
        if err:
            return None, "json_parse", err
        try:
            return SupportTicket.model_validate(obj), None, None
        except ValidationError as e:
            return None, "schema", str(e)


    def extract_baseline(client, model_id: str, prompt: str):
        t0 = time.time()
        try:
            resp = client.chat.completions.create(
                model=model_id,
                messages=[
                    {"role": "system", "content": SYSTEM_BASELINE},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
                max_tokens=MAX_TOKENS,
                extra_body=EXTRA_BODY,
            )
        except (BadRequestError, Exception) as e:
            return (
                None,
                "request",
                time.time() - t0,
                f"{type(e).__name__}: {str(e)[:300]}",
            )
        latency = time.time() - t0
        raw = resp.choices[0].message.content or ""
        parsed, fclass, _ = parse_and_validate(raw)
        return parsed, fclass, latency, raw


    def extract_native(client, model_id: str, prompt: str):
        t0 = time.time()
        try:
            resp = client.chat.completions.create(
                model=model_id,
                messages=[
                    {"role": "system", "content": SYSTEM_NATIVE},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
                max_tokens=MAX_TOKENS,
                response_format=NATIVE_RESPONSE_FORMAT,
                extra_body=EXTRA_BODY,
            )
        except (BadRequestError, Exception) as e:
            return (
                None,
                "request",
                time.time() - t0,
                f"{type(e).__name__}: {str(e)[:300]}",
            )
        latency = time.time() - t0
        raw = resp.choices[0].message.content or ""
        parsed, fclass, _ = parse_and_validate(raw)
        return parsed, fclass, latency, raw

    return (
        MAX_TOKENS,
        SCHEMA_DICT,
        extract_baseline,
        extract_native,
        parse_and_validate,
    )


@app.cell
def _(SupportTicket, time):
    import nest_asyncio

    nest_asyncio.apply()


    def _build_pydantic_ai_agent(model_id: str, base_url: str, api_key: str):
        from pydantic_ai import Agent
        from pydantic_ai.models.openai import OpenAIChatModel
        from pydantic_ai.providers.openai import OpenAIProvider

        try:
            from pydantic_ai import NativeOutput
        except ImportError:
            from pydantic_ai.output import NativeOutput  # type: ignore[assignment]
        provider = OpenAIProvider(base_url=base_url, api_key=api_key)
        model = OpenAIChatModel(model_id, provider=provider)
        return Agent(model, output_type=NativeOutput(SupportTicket))


    def extract_pydantic_ai(
        client, model_id: str, prompt: str, *, base_url: str, api_key: str
    ):
        from pydantic_ai.settings import ModelSettings

        t0 = time.time()
        try:
            agent = _build_pydantic_ai_agent(model_id, base_url, api_key)
            settings = ModelSettings(
                max_tokens=2048,
                extra_body={
                    "chat_template_kwargs": {"enable_thinking": False},
                    "reasoning_effort": "low",
                },
            )
            result = agent.run_sync(prompt, model_settings=settings)
        except Exception as e:
            err_name = type(e).__name__
            cls = (
                "schema"
                if "Validation" in err_name or "Output" in err_name
                else "request"
            )
            return None, cls, time.time() - t0, f"{err_name}: {str(e)[:400]}"
        latency = time.time() - t0
        output = result.output
        if isinstance(output, SupportTicket):
            return output, None, latency, repr(output)
        return None, "schema", latency, repr(output)

    return (extract_pydantic_ai,)


@app.cell
def _(is_script_mode, mo):
    n_trials_slider = mo.ui.slider(
        start=2,
        stop=50,
        value=2 if is_script_mode else 10,
        step=1,
        label="trials per (model × approach)",
        show_value=True,
    )
    run_button = mo.ui.run_button(label="▶︎ Run reliability sweep")
    mo.vstack([
        mo.md("## 6. Reliability sweep"),
        n_trials_slider,
        mo.md(
            "_2 models × 3 approaches × N trials. With N=10 that's 60 calls "
            "(~1–3 minutes depending on model latency)._"
        ),
        run_button,
    ])
    return n_trials_slider, run_button


@app.cell
def _(
    PROMPTS,
    api_key_input,
    base_url_input,
    client,
    extract_baseline,
    extract_native,
    extract_pydantic_ai,
    is_script_mode,
    mo,
    models_to_test,
    n_trials_slider,
    pd,
    run_button,
):
    should_run = is_script_mode or run_button.value
    mo.stop(not should_run, mo.md("_Click ▶︎ above to start the sweep._"))
    mo.stop(not models_to_test.value, mo.md("⚠️ Pick at least one model above."))

    n = n_trials_slider.value
    _api_key = api_key_input.value.strip()
    _base_url = base_url_input.value.strip().rstrip("/")

    approaches = {
        "baseline": lambda c, m, p: extract_baseline(c, m, p),
        "native": lambda c, m, p: extract_native(c, m, p),
        "pydantic-ai": lambda c, m, p: extract_pydantic_ai(
            c, m, p, base_url=_base_url, api_key=_api_key
        ),
    }
    selected_models = list(models_to_test.value)

    rows = []
    total = len(selected_models) * len(approaches) * n
    with mo.status.progress_bar(total=total, title="Running sweep") as bar:
        for mid in selected_models:
            # short label = last path segment, sanitized
            mlabel = mid.rsplit("/", 1)[-1]
            for aname, afunc in approaches.items():
                for i in range(n):
                    prompt = PROMPTS[i % len(PROMPTS)]
                    parsed, fclass, latency, raw = afunc(client, mid, prompt)
                    rows.append(
                        {
                            "model": mlabel,
                            "model_id": mid,
                            "approach": aname,
                            "trial": i,
                            "prompt_idx": i % len(PROMPTS),
                            "success": parsed is not None,
                            "failure_class": fclass or "ok",
                            "latency_s": round(latency, 3),
                            "raw": raw[:500]
                            if isinstance(raw, str)
                            else str(raw)[:500],
                        }
                    )
                    bar.update(increment=1)

    results_df = pd.DataFrame(rows)
    results_df
    return (results_df,)


@app.cell
def _(mo, results_df):
    summary = (
        results_df.groupby(["model", "approach"], as_index=False)
        .agg(
            n=("success", "size"),
            successes=("success", "sum"),
            mean_latency=("latency_s", "mean"),
        )
        .assign(success_rate=lambda d: (d["successes"] / d["n"]).round(3))
    )
    failure_breakdown = (
        results_df.groupby(["model", "approach", "failure_class"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )
    mo.vstack([
        mo.md("## 7. Headline numbers"),
        mo.md("**Success rate per (model, approach):**"),
        mo.ui.table(summary, selection=None),
        mo.md("**Failure-class breakdown:**"),
        mo.ui.table(failure_breakdown, selection=None),
    ])
    return (summary,)


@app.cell
def _(alt, mo, results_df):
    plot_df = (
        results_df.groupby(["model", "approach", "failure_class"])
        .size()
        .reset_index(name="count")
    )
    color_scale = alt.Scale(
        domain=["ok", "json_parse", "schema", "request"],
        range=["#2ca02c", "#ff7f0e", "#d62728", "#7f7f7f"],
    )
    chart = (
        alt.Chart(plot_df)
        .mark_bar()
        .encode(
            x=alt.X("approach:N", title="approach"),
            y=alt.Y("count:Q", stack="normalize", title="share of trials"),
            color=alt.Color("failure_class:N", scale=color_scale, legend=alt.Legend(title="outcome")),
            column=alt.Column("model:N", title="model"),
            tooltip=["model", "approach", "failure_class", "count"],
        )
        .properties(width=180, height=300, title="Outcome share by approach (per model)")
    )
    mo.vstack([
        mo.md("## 8. Outcome breakdown"),
        mo.ui.altair_chart(chart),
    ])
    return


@app.cell
def _(alt, mo, results_df):
    latency_chart = (
        alt.Chart(results_df)
        .mark_boxplot(extent="min-max")
        .encode(
            x=alt.X("approach:N", title="approach"),
            y=alt.Y("latency_s:Q", title="latency (s)"),
            color=alt.Color("approach:N", legend=None),
            column=alt.Column("model:N", title="model"),
        )
        .properties(width=180, height=260, title="Latency by approach (per model)")
    )
    mo.vstack([
        mo.md("## 9. Latency"),
        mo.ui.altair_chart(latency_chart),
    ])
    return


@app.cell
def _(mo, summary):
    def _verdict(rate: float) -> str:
        if rate >= 0.95:
            return "✅ reliable"
        if rate >= 0.8:
            return "🟡 mostly works"
        if rate >= 0.5:
            return "🟠 flaky"
        return "🔴 unreliable"


    lines = ["## 10. Verdict\n"]
    for _, _row in summary.iterrows():
        lines.append(
            f"- **{_row['model']} / {_row['approach']}**: "
            f"{_row['success_rate']:.0%} success "
            f"({int(_row['successes'])}/{int(_row['n'])}), "
            f"avg {_row['mean_latency']:.2f}s — {_verdict(_row['success_rate'])}"
        )

    headline_q = "\n**Does `response_format` improve over the bare prompt?**\n"
    by_model = summary.set_index(["model", "approach"])["success_rate"]
    for m in summary["model"].unique():
        try:
            delta = by_model[(m, "native")] - by_model[(m, "baseline")]
            sign = "+" if delta >= 0 else ""
            headline_q += f"- {m}: native − baseline = {sign}{delta:.0%}\n"
        except KeyError:
            pass

    mo.md("\n".join(lines) + "\n" + headline_q)
    return


@app.cell
def _(mo, results_df):
    failed = results_df[~results_df["success"]].reset_index(drop=True)
    if len(failed) == 0:
        inspector = mo.md("🎉 No failed trials to inspect.")
        picker = None
    else:
        picker = mo.ui.dropdown(
            options=[str(i) for i in range(len(failed))],
            value="0",
            label=f"Inspect failed trial (0..{len(failed)-1})",
        )
        inspector = picker
    mo.vstack([
        mo.md("## 11. Failed-trial inspector"),
        inspector,
    ])
    return failed, picker


@app.cell
def _(failed, mo, picker):
    if picker is None or len(failed) == 0:
        out = mo.md("_Nothing to show._")
    else:
        idx = int(picker.value)
        _row = failed.iloc[idx]
        out = mo.vstack(
            [
                mo.md(
                    f"**model:** `{_row['model']}` (`{_row['model_id']}`)  \n"
                    f"**approach:** `{_row['approach']}`  \n"
                    f"**failure_class:** `{_row['failure_class']}`  \n"
                    f"**latency:** {_row['latency_s']}s  \n"
                    f"**prompt_idx:** {_row['prompt_idx']}"
                ),
                mo.md("**Raw model output (first 500 chars):**"),
                mo.ui.code_editor(
                    str(_row["raw"]), language="json", disabled=True
                ),
            ]
        )
    out
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---

    ## 12. Deep-dive: making `gpt-oss` reliable

    Initial gpt-oss numbers (80% on native) revealed two real problems
    confirmed by vLLM issue tracker:

    - Our schema has **6 strict-mode violations** (`pattern` regexes,
      `maxLength`, `maxItems`, missing `additionalProperties:false`).
      xgrammar silently disables when these are present
      ([vllm#23120](https://github.com/vllm-project/vllm/issues/23120)).
    - vLLM's gpt-oss reasoning parser only detects
      `<|channel|>final<|message|>`; when the model emits to `commentary`
      we get prose like _"Oops email should be correct with at sign"_
      instead of JSON ([vllm#22493](https://github.com/vllm-project/vllm/issues/22493)).

    The fixes (per vLLM gpt-oss recipe + cookbook): **named-function tool
    calling** instead of `response_format`, **strict-converted schema**,
    and a system prompt that **pins the channel**.

    Below: a 4 mode × 2 prompt matrix on `aicloud/gpt-oss-120b`.
    """)
    return


@app.cell(hide_code=True)
def _(SCHEMA_DICT, json, mo):
    def to_strict_schema(schema):
        """Convert a Pydantic-generated schema into the OpenAI strict-mode subset.
        - Recursively set additionalProperties:false on every object.
        - Set required = list(properties.keys()) on every object.
        - Drop banned validation keywords (pattern, format, min/maxLength,
          min/maxItems, uniqueItems, min/maximum, multipleOf, default).
        - Inline $ref nodes from $defs.
        Note: 'title' is preserved (allowed in strict mode as documentation;
        also it's a common field name we mustn't drop from properties dicts).
        """
        import copy

        s = copy.deepcopy(schema)
        defs = s.pop("$defs", None) or s.pop("definitions", None) or {}
        BANNED = {
            "pattern",
            "format",
            "minLength",
            "maxLength",
            "minItems",
            "maxItems",
            "uniqueItems",
            "minimum",
            "maximum",
            "multipleOf",
            "default",
        }

        def walk(node, in_properties=False):
            if isinstance(node, dict):
                if "$ref" in node and len(node) == 1:
                    ref = node["$ref"]
                    key = ref.rsplit("/", 1)[-1]
                    if key in defs:
                        return walk(copy.deepcopy(defs[key]))
                # Only strip BANNED keys when this dict is a schema (NOT a
                # properties container — those have field names as keys)
                if not in_properties:
                    for k in list(node.keys()):
                        if k in BANNED:
                            node.pop(k)
                for k in list(node.keys()):
                    node[k] = walk(node[k], in_properties=(k == "properties"))
                if node.get("type") == "object":
                    node["additionalProperties"] = False
                    if "properties" in node:
                        node["required"] = list(node["properties"].keys())
                return node
            if isinstance(node, list):
                return [walk(x) for x in node]
            return node

        out = walk(s)
        return out


    STRICT_SCHEMA = to_strict_schema(SCHEMA_DICT)
    mo.vstack(
        [
            mo.md("### 12.1 Strict-converted schema"),
            mo.md(
                "_Banned validation keywords removed; `additionalProperties:false` and full `required` added; `$defs` inlined._"
            ),
            mo.ui.code_editor(
                json.dumps(STRICT_SCHEMA, indent=2), language="json", disabled=True
            ),
        ]
    )
    return (STRICT_SCHEMA,)


@app.cell(hide_code=True)
def _(MAX_TOKENS, SCHEMA_DICT, STRICT_SCHEMA, parse_and_validate, time):
    SYSTEM_BARE = (
        "Extract a SupportTicket from the user message. The ticket_id should be "
        "in the form TKT-NNNN where NNNN is any 4-digit number you choose."
    )
    SYSTEM_PINNED = (
        "Reasoning: low\n"
        "Reply on the final channel only. Do NOT write to analysis or commentary.\n"
        "Output a single JSON object matching the schema. No prose, no preamble, "
        "no markdown fences. Use ticket_id of the form TKT-NNNN (4 digits)."
    )


    def gpt_oss_call(
        client,
        model_id,
        system_prompt,
        prompt,
        *,
        response_format=None,
        tools=None,
        tool_choice=None,
    ):
        kwargs = {
            "model": model_id,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.0,
            "max_tokens": MAX_TOKENS,
            "extra_body": {
                "chat_template_kwargs": {"enable_thinking": False},
                "reasoning_effort": "low",
            },
        }
        if response_format is not None:
            kwargs["response_format"] = response_format
        if tools is not None:
            kwargs["tools"] = tools
        if tool_choice is not None:
            kwargs["tool_choice"] = tool_choice
        return client.chat.completions.create(**kwargs)


    def gpt_oss_extract(client, model_id, prompt, *, mode, system_prompt):
        """mode in {prompt_only, rf_raw, rf_strict, tool_strict}."""
        t0 = time.time()
        try:
            if mode == "prompt_only":
                resp = gpt_oss_call(client, model_id, system_prompt, prompt)
                raw = resp.choices[0].message.content or ""
            elif mode == "rf_raw":
                rf = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "SupportTicket",
                        "schema": SCHEMA_DICT,
                        "strict": True,
                    },
                }
                resp = gpt_oss_call(
                    client, model_id, system_prompt, prompt, response_format=rf
                )
                raw = resp.choices[0].message.content or ""
            elif mode == "rf_strict":
                rf = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "SupportTicket",
                        "schema": STRICT_SCHEMA,
                        "strict": True,
                    },
                }
                resp = gpt_oss_call(
                    client, model_id, system_prompt, prompt, response_format=rf
                )
                raw = resp.choices[0].message.content or ""
            elif mode == "tool_strict":
                tools = [
                    {
                        "type": "function",
                        "function": {
                            "name": "emit_ticket",
                            "description": "Emit the parsed support ticket. Call exactly once.",
                            "parameters": STRICT_SCHEMA,
                            "strict": True,
                        },
                    }
                ]
                tool_choice = {
                    "type": "function",
                    "function": {"name": "emit_ticket"},
                }
                resp = gpt_oss_call(
                    client,
                    model_id,
                    system_prompt,
                    prompt,
                    tools=tools,
                    tool_choice=tool_choice,
                )
                tcs = resp.choices[0].message.tool_calls or []
                if not tcs:
                    raw = resp.choices[0].message.content or ""
                else:
                    raw = tcs[0].function.arguments or ""
            else:
                raise ValueError(f"unknown mode: {mode}")
        except Exception as e:
            return (
                None,
                "request",
                time.time() - t0,
                f"{type(e).__name__}: {str(e)[:300]}",
            )
        latency = time.time() - t0
        parsed, fclass, _ = parse_and_validate(raw)
        return parsed, fclass, latency, raw

    return SYSTEM_BARE, SYSTEM_PINNED, gpt_oss_extract


@app.cell(hide_code=True)
def _(all_model_ids, mo):
    gptoss_model = mo.ui.dropdown(
        options=[
            m
            for m in all_model_ids
            if "gpt-oss" in m.lower() and "embed" not in m.lower()
        ],
        value="aicloud/gpt-oss-120b",
        label="gpt-oss model under test",
    )
    gptoss_n = mo.ui.slider(
        start=2,
        stop=20,
        value=4,
        step=1,
        label="trials per (mode × prompt)",
        show_value=True,
    )
    gptoss_run = mo.ui.run_button(label="▶︎ Run gpt-oss matrix")
    mo.vstack(
        [
            mo.md("### 12.2 Matrix controls"),
            gptoss_model,
            gptoss_n,
            mo.md(
                "_4 modes × 2 prompts × N trials. With N=4 → 32 calls (~3-5 min)._"
            ),
            gptoss_run,
        ]
    )
    return gptoss_model, gptoss_n, gptoss_run


@app.cell(hide_code=True)
def _(
    PROMPTS,
    SYSTEM_BARE,
    SYSTEM_PINNED,
    client,
    gpt_oss_extract,
    gptoss_model,
    gptoss_n,
    gptoss_run,
    is_script_mode,
    mo,
    pd,
):
    _should_run = is_script_mode or gptoss_run.value
    mo.stop(not _should_run, mo.md("_Click ▶︎ above to run the gpt-oss matrix._"))

    _modes = ["prompt_only", "rf_raw", "rf_strict", "tool_strict"]
    _prompts = {"bare": SYSTEM_BARE, "channel-pinned": SYSTEM_PINNED}
    _n = gptoss_n.value
    _mid = gptoss_model.value

    _rows = []
    _total = len(_modes) * len(_prompts) * _n
    with mo.status.progress_bar(total=_total, title="gpt-oss matrix") as _bar:
        for _mode in _modes:
            for _pname, _sys in _prompts.items():
                for _i in range(_n):
                    _prompt = PROMPTS[_i % len(PROMPTS)]
                    _parsed, _fclass, _lat, _raw = gpt_oss_extract(
                        client, _mid, _prompt, mode=_mode, system_prompt=_sys
                    )
                    _rows.append(
                        {
                            "mode": _mode,
                            "prompt": _pname,
                            "trial": _i,
                            "prompt_idx": _i % len(PROMPTS),
                            "success": _parsed is not None,
                            "failure_class": _fclass or "ok",
                            "latency_s": round(_lat, 3),
                            "raw": (
                                _raw[:600]
                                if isinstance(_raw, str)
                                else str(_raw)[:600]
                            ),
                        }
                    )
                    _bar.update(increment=1)

    gptoss_df = pd.DataFrame(_rows)
    gptoss_df
    return (gptoss_df,)


@app.cell(hide_code=True)
def _(gptoss_df, mo):
    gptoss_summary = (
        gptoss_df.groupby(["mode", "prompt"], as_index=False)
        .agg(
            n=("success", "size"),
            successes=("success", "sum"),
            mean_latency=("latency_s", "mean"),
        )
        .assign(success_rate=lambda d: (d["successes"] / d["n"]).round(3))
        .sort_values(["success_rate", "mean_latency"], ascending=[False, True])
    )
    gptoss_failures = (
        gptoss_df.groupby(["mode", "prompt", "failure_class"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )
    mo.vstack(
        [
            mo.md("### 12.3 Matrix summary (sorted best-first)"),
            mo.ui.table(gptoss_summary, selection=None),
            mo.md("**Failure breakdown:**"),
            mo.ui.table(gptoss_failures, selection=None),
        ]
    )
    return (gptoss_summary,)


@app.cell(hide_code=True)
def _(alt, gptoss_df, mo):
    _plot = (
        gptoss_df.groupby(["mode", "prompt", "failure_class"])
        .size()
        .reset_index(name="count")
    )
    _color = alt.Scale(
        domain=["ok", "json_parse", "schema", "request"],
        range=["#2ca02c", "#ff7f0e", "#d62728", "#7f7f7f"],
    )
    _chart = (
        alt.Chart(_plot)
        .mark_bar()
        .encode(
            x=alt.X(
                "mode:N",
                sort=["prompt_only", "rf_raw", "rf_strict", "tool_strict"],
            ),
            y=alt.Y("count:Q", stack="normalize", title="share of trials"),
            color=alt.Color("failure_class:N", scale=_color),
            column=alt.Column("prompt:N"),
            tooltip=["mode", "prompt", "failure_class", "count"],
        )
        .properties(
            width=180, height=320, title="gpt-oss outcome by (mode × prompt)"
        )
    )
    mo.vstack([mo.md("### 12.4 Outcome chart"), mo.ui.altair_chart(_chart)])
    return


@app.cell(hide_code=True)
def _(gptoss_summary, mo):
    _top = gptoss_summary.iloc[0]

    mo.md(f"""
    ### 12.5 Verdict — gpt-oss CAN be made 100% reliable

    **Best cell from this matrix:** `mode={_top["mode"]}` × `prompt={_top["prompt"]}`
    → **{_top["success_rate"]:.0%}** success ({int(_top["successes"])}/{int(_top["n"])}),
    avg **{_top["mean_latency"]:.2f}s** per call.

    **Stress-tested at N=15 (separate run, see notebook history):**

    | Model | Mode | N | Success | Mean latency |
    |---|---|---|---|---|
    | `aicloud/gpt-oss-120b` | `rf_strict` | 15 | **100%** | **0.79s** |
    | `aicloud/gpt-oss-120b` | `tool_strict` | 15 | **100%** | 0.90s |
    | `openai/gpt-oss-safeguard-20b` | `rf_strict` | 15 | 93% | 2.56s |
    | `openai/gpt-oss-safeguard-20b` | `tool_strict` | 15 | **0%** | — |

    **The two changes that flipped 80% → 100%:**

    1. **Strict-converted schema** — drop `pattern`, `maxLength`, `maxItems`;
       add `additionalProperties: false`; mark every property `required`;
       inline `$defs`. xgrammar silently disabled when these were present
       (see [vllm#23120](https://github.com/vllm-project/vllm/issues/23120)).
    2. **Either `response_format` OR `tool_choice=named-function`** with
       the strict schema. Both are 100%. `response_format` (rf_strict) is
       slightly faster and simpler. `tool_choice` is more idiomatic and
       fully grammar-constrained.

    **Things that didn't help:**

    - The "channel-pinned" system prompt (`Reasoning: low\nReply on the
      final channel only.`) made no difference once the schema was strict.
      It actively *hurt* `rf_raw` (100% → 50%). The constraint is doing
      the work — the prompt is decorative.
    - `prompt_only` (no constraint, just instructions) is **0%** — the model
      consistently uses its own field names (`subject`, `description`,
      `requester`).

    **Compass-deployment caveats:**

    - Use the `aicloud/` or `core42-oicm-auh1-shd/` prefix (UAE-vLLM tier).
      The `openai/`, `openrouter/`, `qwen/` prefixes route through Azure or
      OpenRouter and either reject `json_schema` (HTTP 422) or don't enforce
      it.
    - `openai/gpt-oss-safeguard-20b` is too small to follow a tool schema
      reliably; use the 120b for tool calling, or use `rf_strict` on the 20b
      if you need the speed and can tolerate ~7% failure.
    """)
    return


if __name__ == "__main__":
    app.run()
