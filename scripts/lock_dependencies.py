"""Generate deployment requirements from package metadata and a universal lock."""
import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "ai-governance-control-plane"
EXTRA = "web"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    uv = shutil.which('uv')
    if uv is None:
        parser.error('Install uv to update or verify the deployment lock.')
    if not args.check:
        subprocess.run([uv, 'lock', '--directory', str(ROOT / 'deployment')], check=True)
    with tempfile.TemporaryDirectory() as directory:
        target = Path(directory) / 'requirements.txt'
        subprocess.run([uv, 'export', '--directory', str(ROOT / 'deployment'), '--locked',
                        '--no-header', '--no-hashes', '--no-emit-project', '--no-emit-package', PACKAGE,
                        '--output-file', str(target)], check=True, stdout=subprocess.DEVNULL)
        content = '# Generated from pyproject.toml and deployment/uv.lock. Run python scripts/lock_dependencies.py.\n'
        content += target.read_text() + '\n.' + ('['+EXTRA+']' if EXTRA else '') + '\n'
        output = ROOT / 'requirements.txt'
        if args.check:
            if not output.exists() or output.read_text() != content:
                raise SystemExit('Deployment requirements have drifted. Regenerate and review the lock.')
        else:
            output.write_text(content)


if __name__ == '__main__':
    main()
