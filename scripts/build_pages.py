"""Build an explicit, minimal GitHub Pages artifact for SRTI."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / ".pages-artifact"
MODULE = "Sahel Region Threat Index (SRTI)"
PUBLIC_FILES = (
    Path("index.html"),
    Path(".nojekyll"),
    Path("assets/mc-mark.png"),
    Path("assets/srti.css"),
    Path("assets/srti.js"),
    Path("data/srti_latest.json"),
    Path("data/srti_history.json"),
    Path(MODULE) / "index.html",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build(output: Path = OUTPUT) -> Path:
    output = output.resolve()
    if output.parent != ROOT.resolve() or output.name != ".pages-artifact":
        raise ValueError("Pages output must be the repository .pages-artifact directory")
    if output.exists():
        shutil.rmtree(output)
    output.mkdir()

    manifest = {"files": {}}
    for relative in PUBLIC_FILES:
        source = ROOT / relative
        if not source.is_file():
            raise FileNotFoundError(f"Missing public file: {relative}")
        destination = output / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        manifest["files"][relative.as_posix()] = sha256(destination)

    clean_route = output / "srti" / "index.html"
    clean_route.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / MODULE / "index.html", clean_route)
    manifest["files"]["srti/index.html"] = sha256(clean_route)

    latest = json.loads((ROOT / "data/srti_latest.json").read_text(encoding="utf-8"))
    manifest["snapshot_fetched_at"] = latest.get("fetched_at")
    (output / "deployment-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return output


if __name__ == "__main__":
    built = build()
    print(f"[OK] Pages artifact: {built}")
