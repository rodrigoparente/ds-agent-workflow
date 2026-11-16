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


def fetch_skill(
    skill_name: str, force: bool = False, target_root: Path | None = None
) -> bool:
    if target_root is None:
        target_root = Path(__file__).resolve().parent.parent / "skills"

    dest_dir = target_root / skill_name
    scripts_dir = dest_dir / "scripts"

    # If scripts exist and not force, no need to download
    if dest_dir.exists() and scripts_dir.exists() and not force:
        print(
            f"Skill '{skill_name}' is already installed at {dest_dir}. "
            "Use --force to re-download."
        )
        return True

    print(f"Downloading '{skill_name}' from {REPO_TARBALL}...")
    req = urllib.request.Request(
        REPO_TARBALL, headers={"User-Agent": "DS-Starter-Pack/1.0"}
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
    except Exception as e:
        print(f"Error downloading skills archive: {e}", file=sys.stderr)
        return False

    dest_dir.mkdir(parents=True, exist_ok=True)
    extracted_count = 0

    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
        prefix_to_strip = None
        for member in tar.getmembers():
            parts = member.name.split("/")
            if len(parts) > 2 and parts[1] == "skills" and parts[2] == skill_name:
                prefix_to_strip = "/".join(parts[:3]) + "/"
                break

        if not prefix_to_strip:
            print(
                f"Skill '{skill_name}' not found in Anthropic skills repository.",
                file=sys.stderr,
            )
            return False

        for member in tar.getmembers():
            if not member.name.startswith(prefix_to_strip):
                continue
            rel_path = member.name[len(prefix_to_strip) :]
            if not rel_path:
                continue

            target_path = dest_dir / rel_path
            if member.isdir():
                target_path.mkdir(parents=True, exist_ok=True)
            elif member.isreg():
                target_path.parent.mkdir(parents=True, exist_ok=True)
                with (
                    tar.extractfile(member) as src_file,
                    open(target_path, "wb") as dst_file,
                ):
                    dst_file.write(src_file.read())
                if member.mode & 0o111:
                    target_path.chmod(target_path.stat().st_mode | 0o111)
                extracted_count += 1

    print(f"Successfully installed '{skill_name}' to {dest_dir} ({extracted_count} files).")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Download skills from Anthropic repository."
    )
    parser.add_argument(
        "skill", help="Name of the skill to fetch (e.g., docx, pdf)"
    )
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
