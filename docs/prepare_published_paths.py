"""Expose the published esp-sr layout so :project_file: checks pass here.

The RST files keep esp-sr component paths (include/<target>/..., model/...,
esp-tts/...). Those files live under components/ in this repo, or only exist
in the published component. This helper creates the published paths as
symlinks (or empty placeholders) at docs-build time.

When the same docs tree is built from an esp-sr checkout the published files
already exist, so this is a no-op.
"""

from __future__ import annotations

import os
from pathlib import Path

# published path (relative to repo root) -> source path in this repo, or None
PUBLISHED_TO_SOURCE: dict[str, str | None] = {
    "include/esp32s3/esp_aec.h": "components/esp_audio_processor/esp_aec.h",
    "include/esp32p4/esp_doa_capon_embedded.h": "components/esp_audio_processor/esp_doa_capon_embedded.h",
    "include/esp32p4/esp_gsc.h": "components/esp_audio_processor/esp_gsc.h",
    "test_apps/esp-sr-afe/main/test_afe.cpp": "tests/main/test_afe.cpp",
    "model/multinet_model/fst/commands_cn.txt": "components/model/multinet_model/fst/commands_cn.txt",
    "model/multinet_model/fst/commands_en.txt": "components/model/multinet_model/fst/commands_en.txt",
    "tool/multinet_pinyin.py": None,
    "esp-tts/samples/xiaoxin_speed1.wav": None,
    "esp-tts/samples/S2_xiaole_speed2.wav": None,
    "esp-tts/esp_tts_chinese/include/esp_tts.h": None,
}


def prepare_published_paths(repo_root: Path | None = None) -> None:
    root = Path(repo_root or Path(__file__).resolve().parent.parent)
    for published, source in PUBLISHED_TO_SOURCE.items():
        dest = root / published
        if dest.exists() or dest.is_symlink():
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        if source:
            src = root / source
            if src.exists():
                dest.symlink_to(Path(os.path.relpath(src, dest.parent)))
                continue
        dest.touch()


if __name__ == "__main__":
    prepare_published_paths()
