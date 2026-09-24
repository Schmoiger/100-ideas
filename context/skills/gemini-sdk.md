---
name: gemini-sdk
description: Procedural guidance for google-genai Python SDK, structured outputs with Pydantic, Gemini context caching, Imagen 3, token telemetry, and burn guard rails.
globs: ["services/enrichment/**/*.py", "services/typesetting/**/*.py", "services/publishing/**/*.py", "**/gemini*.py"]
---

# Gemini SDK & Token Governance Skill

Procedural guidance and engineering discipline for integrating the official `google-genai` Python SDK into research synthesis, visual asset generation, book drafting, and channel syndication, combined with strict token burn guard rails and budget circuit breakers.

---

## 1. SDK Import & Client Initialisation

Always import from `google.genai` (never legacy `google.generativeai`):

```python
from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Secure resolution from .env without committing secrets
def get_genai_client(repo_root: Path | None = None) -> genai.Client:
    """Initialise official Google GenAI client with secure environment resolution."""
    if repo_root:
        env_file = repo_root / ".env"
        if env_file.is_file():
            load_dotenv(env_file)
    else:
        load_dotenv()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not configured.")

    return genai.Client(api_key=api_key)
```

---

## 2. Model Tiering & Responsibilities

Select models deliberately based on reasoning complexity, latency, and token economics:

| Role | Target Model | Purpose | Input Context |
|------|--------------|---------|---------------|
| **Research Synthesis** | `gemini-2.5-flash` | Extract empirical evidence, trade-offs, and citations from resources. | Linked whitepapers in `artefacts/content/resources/` |
| **Visual Prompting** | `gemini-2.5-flash` | Synthesise metaphorical prompts avoiding AI clichés. | Title, synopsis, and research notes |
| **Editorial Illustration** | `imagen-3.0-generate-002` | Generate publication-grade 16:9 and 3:2 PNG illustrations. | Derived metaphorical prompt |
| **Book Chapter Drafting** | `gemini-2.5-pro` | High-reasoning author voice synthesis (`author.md`). | Research notes + author persona + synopsis |
| **Syndication (Blog/Social)** | `gemini-2.5-flash` | Distil approved chapter manuscript into punchy blog post and LinkedIn takeaways. | Approved `book/chapter.md` |

---

## 3. Structured Outputs with Pydantic

Enforce deterministic schema compliance by binding Pydantic models directly to generation requests:

```python
from pydantic import BaseModel, Field

class EmpiricalResearchDossier(BaseModel):
    empirical_evidence: list[str] = Field(description="Concrete field observations and verified data points")
    economic_tradeoffs: list[str] = Field(description="Operational trade-offs and bottleneck dynamics")
    counterarguments: list[str] = Field(description="Known failure modes and boundary conditions")
    citations: list[str] = Field(description="Formal citations referencing resource library items")

def extract_research(client: genai.Client, prompt: str) -> EmpiricalResearchDossier:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=EmpiricalResearchDossier,
            temperature=0.2,
        ),
    )
    return response.parsed
```

---

## 4. Gemini Context Caching Architecture

Foundational whitepapers in `artefacts/content/resources/` (e.g. `new-devx-vision.md`) and author personas (`context/persona/author.md`) frequently exceed the 32,768 token caching threshold. Context caching reduces repeated token costs by up to 75% and improves generation latency:

```python
def create_resource_cache(
    client: genai.Client,
    model: str,
    contents: list[str],
    ttl: str = "3600s",
) -> str:
    """Create a reusable context cache for long-horizon documents."""
    cache = client.caches.create(
        model=model,
        config=types.CreateCachedContentConfig(
            contents=contents,
            ttl=ttl,
        ),
    )
    return cache.name

def generate_with_cache(
    client: genai.Client,
    model: str,
    prompt: str,
    cache_name: str,
) -> str:
    """Generate content referencing an established context cache."""
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            cached_content=cache_name,
            temperature=0.3,
        ),
    )
    return response.text
```

---

## 5. Editorial Illustration Generation (Imagen 3)

Generate crisp publication illustrations using `imagen-3.0-generate-002`:

```python
def generate_editorial_illustration(
    client: genai.Client,
    prompt: str,
    aspect_ratio: str = "16:9",
) -> bytes:
    """Generate editorial image binary using Imagen 3."""
    result = client.models.generate_images(
        model="imagen-3.0-generate-002",
        prompt=prompt,
        config=types.GenerateImagesConfig(
            number_of_images=1,
            aspect_ratio=aspect_ratio,
            output_mime_type="image/png",
        ),
    )
    return result.generated_images[0].image.image_bytes
```

---

## 6. Token Burn Guard Rails & Circuit Breakers

To guard against runaway expenditure, uncontrolled loops, and unexpected billing spikes during continuous execution, six non-negotiable guard rails are enforced:

1. **Pre-Flight Cost Estimator & Dry Run (`--dry-run`)**:
   - Calculate prompt tokens via `client.models.count_tokens` before dispatching.
   - Project USD spend based on published model pricing tiers.
2. **Hard Spend Circuit Breaker**:
   - `MAX_SESSION_SPEND_USD` (default `$2.00`) and `MAX_IDEA_TOKENS` (default `50,000` tokens).
   - If cumulative session spend exceeds the threshold, immediately raise `BudgetExhaustedError` and halt execution.
3. **Cryptographic Input Fingerprinting**:
   - Compute SHA-256 over `(model_name, prompt_template_hash, input_documents_hash)`.
   - If `meta.yaml` already records the identical fingerprint, bypass API generation (zero token spend) unless `--force-llm` is explicitly supplied.
4. **Context Window Clamping**:
   - Cap un-cached context at 12,000 tokens per call.
   - Long documents exceeding this threshold must route through context caching or structured summarisation.
5. **Strictly Sequential Concurrency**:
   - Batch operations must execute with `concurrency=1`. Parallel unmetered requests are strictly forbidden.
6. **Interactive Batch Confirmation**:
   - Commands touching multiple ideas or passing `--all` present an estimated token and cost summary, requiring explicit confirmation (`[y/N]`) unless `--yes` is passed.

---

## 7. Token Telemetry & Provenance Recording

Record full usage metrics in `meta.yaml` for every generation step:

```yaml
token_telemetry:
  model: "gemini-2.5-pro"
  fingerprint: "sha256:7f83b165..."
  prompt_tokens: 4210
  cached_tokens: 35000
  completion_tokens: 1820
  total_tokens: 41030
  estimated_cost_usd: 0.0078
  latency_ms: 1240
  timestamp: "2026-09-24T22:00:00Z"
```

---

## 8. Offline Fallback & Mock Execution

In environments lacking `GEMINI_API_KEY` (e.g. CI/CD test runners, sandboxed unit tests, local air-gapped workstations), the system must cleanly fall back to deterministic mock synthesis rather than failing with an unhandled exception.
