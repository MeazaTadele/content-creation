"""FLUX image models on Cloudflare Workers AI (reference sheet and keyframes)."""
from __future__ import annotations

import base64
import os

from .. import media
from ..calls import CallResult, FatalError
from . import http
from .base import ImageProvider

HINT = "Save your Cloudflare account ID as CLOUDFLARE_ACCOUNT_ID and a Workers AI token as CLOUDFLARE_API_TOKEN."
# FLUX.2 klein 4B accepts reference images; FLUX.1 schnell is text-only.
DEFAULT_MODEL = "@cf/black-forest-labs/flux-2-klein-4b"


class CloudflareFlux(ImageProvider):
    name, licence = "cloudflare-flux", "FLUX.2 klein 4B: Apache 2.0; FLUX.1 schnell: Apache 2.0"

    def __init__(self):
        self.model = os.environ.get("CLOUDFLARE_IMAGE_MODEL", DEFAULT_MODEL)

    def check_ready(self):
        http.require_env("CLOUDFLARE_ACCOUNT_ID", HINT)
        http.require_env("CLOUDFLARE_API_TOKEN", HINT)

    def generate(self, prompt, negative, seed, width, height, refs, out_png, tmp_dir):
        acct = http.require_env("CLOUDFLARE_ACCOUNT_ID", HINT)
        token = http.require_env("CLOUDFLARE_API_TOKEN", HINT)
        url = f"https://api.cloudflare.com/client/v4/accounts/{acct}/ai/run/{self.model}"
        headers = {"Authorization": f"Bearer {token}"}
        if "flux-2" in self.model:
            # FLUX.2 models take multipart form data, with optional reference images
            fields = {"prompt": (None, prompt), "width": (None, str(width)), "height": (None, str(height)),
                      "seed": (None, str(seed))}
            for i, ref in enumerate(refs[:4]):
                fields[f"input_image_{i}"] = (ref.name, ref.read_bytes(), "image/png")
            r = http.post(url, headers=headers, files=fields)
        else:
            r = http.post(url, headers=headers, json={"prompt": prompt, "seed": seed, "steps": 4})
        j = r.json()
        img_b64 = (j.get("result") or {}).get("image")
        if not img_b64:
            raise FatalError(f"Cloudflare returned no image: {str(j)[:300]}")
        raw = tmp_dir / (out_png.stem + ".src")
        raw.write_bytes(base64.b64decode(img_b64))
        try:
            # whatever size came back, crop to exactly the size this keyframe needs
            media.run(["-i", str(raw), "-vf",
                       f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}",
                       "-frames:v", "1", str(out_png)])
        finally:
            raw.unlink(missing_ok=True)
        return CallResult(out_png, {"images": 1, "pixels": width * height}, self.model)
