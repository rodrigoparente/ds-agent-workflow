#!/usr/bin/env python3
"""
Fetch an official skill from Anthropic's skills repository (github.com/anthropics/skills)
and install or update it in .agents/skills/<skill_name>.

Usage:
    uv run python .agents/tools/fetch_skill.py docx
    uv run python .agents/tools/fetch_skill.py pdf --force
"""

import argparse
import io
import sys
import tarfile
import urllib.request
from pathlib import Path

REPO_TARBALL = "https://codeload.github.com/anthropics/skills/tar.gz/main"


def _extract_skill_tarball(data: bytes, skill_name: str, dest_dir: Path) -> int:
    """Extract matching skill directory from tarball bytes and return extracted file count."""
    extracted_count = 0
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
        prefix = next(
            (
                "/".join(m.name.split("/")[:3]) + "/"
                for m in tar.getmembers()
                if len(m.name.split("/")) > 2
                and m.name.split("/")[1] == "skills"
                and m.name.split("/")[2] == skill_name
            ),
            None,
        )
        if not prefix:
            return -1

        for member in tar.getmembers():
            if not member.name.startswith(prefix):
                continue
            rel_path = member.name[len(prefix) :]
            if not rel_path:
                continue
            target_path = dest_dir / rel_path
            if member.isdir():
                target_path.mkdir(parents=True, exist_ok=True)
            elif member.isreg():
                target_path.parent.mkdir(parents=True, exist_ok=True)
                with tar.extractfile(member) as src_file, open(target_path, "wb") as dst_file:
                    dst_file.write(src_file.read())
                if member.mode & 0o111:
                    target_path.chmod(target_path.stat().st_mode | 0o111)
                extracted_count += 1
    return extracted_count


def fetch_skill(skill_name: str, force: bool = False, target_root: Path | None = None) -> bool:
    if target_root is None:
        target_root = Path(__file__).resolve().parent.parent / "skills"

    dest_dir = target_root / skill_name
    if dest_dir.exists() and (dest_dir / "scripts").exists() and not force:
        print(
            f"Skill '{skill_name}' is already installed at {dest_dir}. Use --force to re-download."
        )
        return True

    print(f"Downloading '{skill_name}' from {REPO_TARBALL}...")
    req = urllib.request.Request(REPO_TARBALL, headers={"User-Agent": "DS-Starter-Pack/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
    except Exception as e:
        print(f"Error downloading skills archive: {e}", file=sys.stderr)
        return False

    dest_dir.mkdir(parents=True, exist_ok=True)
    extracted_count = _extract_skill_tarball(data, skill_name, dest_dir)
    if extracted_count < 0:
        print(
            f"Skill '{skill_name}' not found in Anthropic skills repository.",
            file=sys.stderr,
        )
        return False

    print(f"Successfully installed '{skill_name}' to {dest_dir} ({extracted_count} files).")
    return True


def main():
    parser = argparse.ArgumentParser(description="Download skills from Anthropic repository.")
    parser.add_argument("skill", help="Name of the skill to fetch (e.g., docx, pdf)")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-download even if already present",
    )
    args = parser.parse_args()

    success = fetch_skill(args.skill, force=args.force)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
