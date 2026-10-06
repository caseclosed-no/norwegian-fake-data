"""Check installed wheel and sdist via uvx outside the source checkout.

Run after `uv build`: uv run python scripts/smoke_dist.py
"""

import json
import os
import shutil
import subprocess
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    uv = shutil.which("uv")
    if uv is None:
        raise SystemExit("uv is required for distribution smoke tests.")
    version = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    wheel = ROOT / "dist" / f"norwegian_fake_data-{version}-py3-none-any.whl"
    sdist = ROOT / "dist" / f"norwegian_fake_data-{version}.tar.gz"
    for artifact in (wheel, sdist):
        if not artifact.is_file():
            raise SystemExit(f"Missing {artifact}; run uv build first.")
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    env.pop("VIRTUAL_ENV", None)
    with tempfile.TemporaryDirectory(prefix="norwegian-fake-data-smoke-") as temporary:
        for artifact in (wheel, sdist):
            command = [uv, "tool", "run", "--from", str(artifact), "norwegian-fake-data"]

            def run(*args: str, base_command: tuple[str, ...] = tuple(command)) -> str:
                result = subprocess.run(
                    [*base_command, *args],
                    cwd=temporary,
                    env=env,
                    check=True,
                    text=True,
                    encoding="utf-8",
                    capture_output=True,
                )
                return result.stdout

            assert run("--version").strip() == version
            assert "Usage" in run("--help")
            phones = json.loads(run("phone", "--count", "5", "--unique", "--format", "json"))
            assert len({p["phone"] for p in phones}) == 5
            assert all(68050000 <= int(p["phone"].replace(" ", "")) <= 68059999 for p in phones)
            args = ("--age", "35", "--exact-age", "--as-of", "2026-10-06", "--format", "json")
            fnr = json.loads(run("fnr", *args))[0]
            assert fnr["birthday"] == "1991-10-06" and fnr["mode"] == "prop"
            assert run("plate", "--prefix", "QB", "--format", "plain").startswith("QB ")
            person = json.loads(run("person", *args, "--vehicle"))[0]
            assert person["plate"] and person["email"].endswith("@example.com")
            for subcommand in ("fnr", "person"):
                synthetic = json.loads(run(subcommand, *args, "--mode", "synthetic"))[0]
                assert 81 <= int(synthetic["fnr"][2:4]) <= 92
                try:
                    run(subcommand, *args, "--mode", "valid")
                except subprocess.CalledProcessError as exc:
                    assert exc.returncode == 2 and not exc.stdout
                else:
                    raise AssertionError(f"{subcommand} must reject valid FNR generation")
            print(f"Passed installed distribution checks: {artifact.name}")


if __name__ == "__main__":
    main()
