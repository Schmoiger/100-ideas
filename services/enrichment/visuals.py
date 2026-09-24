"""Visual asset generation and metaphorical prompt derivation engine with Imagen 3 and token governance."""

from __future__ import annotations

import hashlib
import struct
import time
import zlib
from pathlib import Path
from typing import Any

import yaml
from google.genai import types

from services.enrichment.models import VisualPrompt
from services.ingestion.models import IdeaRecord
from services.llm.client import get_genai_client, is_live_genai_available
from services.llm.governance import (
    check_fingerprint_match,
    compute_input_fingerprint,
    estimate_cost,
    estimate_token_count,
    get_governance,
)
from services.llm.telemetry import TokenTelemetry, record_telemetry_in_meta

# Editorial artistic styles for intentional visual variety
STYLES: list[str] = [
    "Swiss modernist graphic design, bold geometric silhouettes, subtle paper texture, duotone risograph",
    "Constructivist architectural schematics, stark axonometric perspective, precise linework, technical drafting",
    "Editorial linocut printmaking, woodblock relief, high-contrast monochrome with ochre accent",
    "Industrial brutalist product design, cast concrete and brushed brass mechanical gears, dramatic studio chiaroscuro",
    "Bauhaus abstract assemblage, balanced geometric primitives, primary tonal harmony, archival catalog aesthetic",
]

COMPOSITIONS: list[str] = [
    "Centered isometric composition with clean white negative space and asymmetric balance",
    "Close-up macro perspective focusing on interlocking analog components and mechanical friction",
    "Wide cinematic focal point framing an expansive architectural cross-section with subtle depth of field",
    "Dynamic diagonal rhythm illustrating kinetic energy and structural transition between states",
]

MOODS: list[str] = [
    "Cool gallery lighting, clinical clarity, measured precision, quiet intellectual authority",
    "High-contrast chiaroscuro, warm amber directional beam cutting through deep obsidian shadows",
    "Diffused overcast studio lighting, soft tactile shadows, muted archival parchment glow",
    "Dusk ambient glow with architectural silhouette contrast and razor-sharp specular highlights",
]

METAPHOR_MAP: dict[str, str] = {
    "constraint": "An hourglass neck transitioning into an expanding brass conduit",
    "loop": "A continuous Mobius strip carved from polished granite and steel",
    "verification": "A high-precision optical caliper gauging an intricate interlocking gear assembly",
    "governance": "An elevated architectural observation platform overlooking a clockwork train yard",
    "code": "A tactile letterpress printing block locking into an iron chase with micrometer precision",
    "agent": "An articulated brass drafting arm precisely tracing blueprints across a clean drafting board",
    "bottleneck": "A hydraulic valve manifold where narrow copper pipes widen into unobstructed chambers",
}


def derive_visual_prompt(
    idea: IdeaRecord,
    refinement: str | None = None,
) -> VisualPrompt:
    """Derive dynamic editorial prompt from core thesis and metaphorical concepts.

    Handles REQ-ENR-002: Specifies conceptual subject, composition, mood,
    and stylistic variety while actively avoiding AI art clichés.
    """
    # Deterministic style/composition selection based on idea ID hash
    hash_int: int = int(hashlib.sha256(f"{idea.id}:{idea.title}".encode()).hexdigest(), 16)
    style: str = STYLES[hash_int % len(STYLES)]
    composition: str = COMPOSITIONS[(hash_int // 10) % len(COMPOSITIONS)]
    mood: str = MOODS[(hash_int // 100) % len(MOODS)]

    # Select concept metaphor
    title_syn_lower: str = f"{idea.title} {idea.synopsis}".lower()
    metaphor: str = (
        "A kinetic physical balancing mechanism composed of brushed brass and dark basalt stone"
    )
    for key, candidate in METAPHOR_MAP.items():
        if key in title_syn_lower:
            metaphor = candidate
            break

    subject: str = f"A conceptual editorial metaphor representing '{idea.title}': {metaphor}."

    if refinement:
        subject += f" Refinement directive: {refinement.strip()}."

    negative_prompt: str = (
        "glowing circuit boards, matrix code rain, neon holograms, literal human faces, "
        "hyper-realistic CGI robots, cliché floating brain, distorted anatomy, blurry text, watermark"
    )

    full_prompt: str = (
        f"{subject} {composition}. Lighting: {mood}. Style: {style}. "
        "Award-winning editorial book illustration, high fidelity, 8k resolution, intentional graphic discipline."
    )

    return VisualPrompt(
        idea_id=idea.id,
        concept_metaphor=metaphor,
        subject=subject,
        composition=composition,
        mood_lighting=mood,
        style_direction=style,
        negative_prompt=negative_prompt,
        full_prompt=full_prompt,
    )


def create_editorial_png(seed_str: str, width: int = 800, height: int = 450) -> bytes:
    """Synthesise a valid, high-resolution PNG image binary with genuine PNG headers.

    Uses pure standard library zlib and struct to construct valid PNG chunks:
    IHDR, IDAT (deflated raw scanlines), and IEND.
    """
    digest: bytes = hashlib.sha256(seed_str.encode()).digest()
    r1, g1, b1 = digest[0] % 60 + 20, digest[1] % 60 + 20, digest[2] % 60 + 30  # Dark base
    r2, g2, b2 = digest[3] % 120 + 130, digest[4] % 100 + 100, digest[5] % 50 + 40  # Accent color
    r3, g3, b3 = 240, 238, 230  # Light background paper tone

    raw_data: bytearray = bytearray()
    for y in range(height):
        raw_data.append(0)  # Filter byte: None (0)
        norm_y: float = y / height
        for x in range(width):
            norm_x: float = x / width

            in_center: bool = 0.25 <= norm_x <= 0.75 and 0.25 <= norm_y <= 0.75
            is_diagonal: bool = abs(norm_x - norm_y) < 0.08

            if in_center and is_diagonal:
                raw_data.extend((r2, g2, b2))
            elif in_center:
                raw_data.extend((r1, g1, b1))
            elif is_diagonal:
                raw_data.extend((r2, g2, b2))
            else:
                raw_data.extend((r3, g3, b3))

    def make_chunk(chunk_type: bytes, data: bytes) -> bytes:
        chunk_len: bytes = struct.pack(">I", len(data))
        crc: int = zlib.crc32(chunk_type + data) & 0xFFFFFFFF
        return chunk_len + chunk_type + data + struct.pack(">I", crc)

    png_header: bytes = b"\x89PNG\r\n\x1a\n"
    ihdr_data: bytes = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    ihdr_chunk: bytes = make_chunk(b"IHDR", ihdr_data)

    compressed_idat: bytes = zlib.compress(bytes(raw_data), level=9)
    idat_chunk: bytes = make_chunk(b"IDAT", compressed_idat)
    iend_chunk: bytes = make_chunk(b"IEND", b"")

    return png_header + ihdr_chunk + idat_chunk + iend_chunk


def generate_visual_assets(
    idea: IdeaRecord,
    ideas_root: Path,
    refinement: str | None = None,
    force: bool = False,
    force_llm: bool = False,
    dry_run: bool = False,
    client: Any = None,
) -> tuple[Path, Path, bool]:
    """Derive prompt and produce illustration asset for an idea.

    Handles REQ-ENR-002, REQ-ENR-003, REQ-ENR-004 with live Imagen 3 / Gemini SDK and token guard rails.
    """
    idea_dir: Path = ideas_root / idea.id
    assets_dir: Path = idea_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    meta_file: Path = idea_dir / "meta.yaml"

    prompt_path: Path = assets_dir / "prompt.txt"
    image_path: Path = assets_dir / "illustration.png"

    prompt: VisualPrompt = derive_visual_prompt(idea, refinement=refinement)
    fingerprint = compute_input_fingerprint(
        model_name="imagen-3.0-generate-002",
        prompt_template=prompt.full_prompt,
    )

    if image_path.is_file() and prompt_path.is_file() and not force and not force_llm:
        if check_fingerprint_match(meta_file, fingerprint):
            return prompt_path, image_path, False
        if not force_llm:
            return prompt_path, image_path, False

    # Pre-flight governance check
    gov = get_governance()
    projected_tokens = estimate_token_count(prompt.full_prompt)
    projected_cost = gov.check_preflight(
        model="imagen-3.0-generate-002",
        projected_prompt_tokens=projected_tokens,
        projected_completion_tokens=0,
        idea_id=idea.id,
    )

    if dry_run:
        telemetry = TokenTelemetry(
            model="imagen-3.0 (dry-run)",
            fingerprint=fingerprint,
            prompt_tokens=projected_tokens,
            completion_tokens=0,
            total_tokens=projected_tokens,
            estimated_cost_usd=projected_cost,
        )
        record_telemetry_in_meta(meta_file, telemetry)
        return prompt_path, image_path, False

    # Persist prompt.txt
    temp_prompt: Path = assets_dir / ".prompt.txt.tmp"
    temp_prompt.write_text(prompt.to_text_payload(), encoding="utf-8")
    temp_prompt.replace(prompt_path)

    # Image generation: live Imagen 3 or deterministic fallback
    image_bytes: bytes | None = None
    live_available = is_live_genai_available() or client is not None
    used_model = "offline-mock"
    latency_ms = 0

    if live_available:
        try:
            active_client = client or get_genai_client()
            t0 = time.perf_counter()
            result = active_client.models.generate_images(
                model="imagen-3.0-generate-002",
                prompt=prompt.full_prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio="16:9",
                    output_mime_type="image/png",
                ),
            )
            latency_ms = int((time.perf_counter() - t0) * 1000)
            if result.generated_images:
                image_bytes = result.generated_images[0].image.image_bytes
                used_model = "imagen-3.0-generate-002"
        except Exception:
            image_bytes = None

    if image_bytes is None:
        image_bytes = create_editorial_png(
            seed_str=f"{idea.id}:{prompt.full_prompt}", width=800, height=450
        )

    # Record spend in accumulator
    actual_cost = estimate_cost(model=used_model, prompt_tokens=projected_tokens, num_images=1)
    gov.record_usage(prompt_tokens=projected_tokens, completion_tokens=0, cost_usd=actual_cost)

    temp_img: Path = assets_dir / ".illustration.png.tmp"
    temp_img.write_bytes(image_bytes)
    temp_img.replace(image_path)

    # Record telemetry
    telemetry = TokenTelemetry(
        model=used_model,
        fingerprint=fingerprint,
        prompt_tokens=projected_tokens,
        completion_tokens=0,
        total_tokens=projected_tokens,
        estimated_cost_usd=actual_cost,
        latency_ms=latency_ms,
    )
    record_telemetry_in_meta(meta_file, telemetry)

    # Update meta.yaml
    if meta_file.is_file():
        try:
            meta_data: Any = yaml.safe_load(meta_file.read_text(encoding="utf-8"))
            if isinstance(meta_data, dict):
                meta_data["illustration"] = "assets/illustration.png"
                meta_data["visual_prompt"] = "assets/prompt.txt"
                temp_meta: Path = idea_dir / ".meta.yaml.tmp"
                temp_meta.write_text(
                    yaml.safe_dump(meta_data, sort_keys=False, allow_unicode=True), encoding="utf-8"
                )
                temp_meta.replace(meta_file)
        except Exception:
            pass

    return prompt_path, image_path, True
