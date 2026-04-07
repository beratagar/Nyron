"""Ana giriş — PySide6 arayüz (varsayılan)."""
import logging
import os
import sys
from pathlib import Path

from config import LOGGING

PROJECT_ROOT = Path(__file__).resolve().parent


def _configure_utf8_stdio() -> None:
    # run.bat uses chcp 65001; mirror that behavior for direct runs.
    try:
        os.environ.setdefault("PYTHONUTF8", "1")
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def _ensure_requirements() -> None:
    """Best-effort dependency install for direct `python main.py` runs.

    run.bat installs `requirements.txt` every time; direct runs often fail or behave oddly
    when a different Python install is used (missing packages).
    """
    req = PROJECT_ROOT / "requirements.txt"
    if not req.exists():
        return
    # Fast check: if core GUI deps import, assume we're ok.
    try:
        import PySide6  # noqa: F401
        import pandas  # noqa: F401
        import matplotlib  # noqa: F401

        return
    except Exception:
        pass
    try:
        import subprocess

        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q", "-r", str(req)],
            check=False,
            cwd=str(PROJECT_ROOT),
        )
    except Exception:
        # If pip is unavailable, continue; the import error will surface later.
        pass

# Ensure `python <anywhere>\main.py` behaves like running from project root (run.bat).
try:
    os.chdir(PROJECT_ROOT)
except OSError:
    pass

# Prefer local project modules over any globally installed ones.
root_s = str(PROJECT_ROOT)
if root_s not in sys.path:
    sys.path.insert(0, root_s)


def _resolve_in_project(path_like: str) -> Path:
    p = Path(path_like)
    return p if p.is_absolute() else (PROJECT_ROOT / p)


_log_file = _resolve_in_project(str(LOGGING.get("file", "logs/app.log")))
_log_file.parent.mkdir(parents=True, exist_ok=True)

_fmt = LOGGING.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Konsol çıktısı kullanıcı için okunabilir olmalı:
# - Varsayılan: WARNING+ (terminali şişirmesin)
# - Detay istenirse: NYRON_VERBOSE=1 ile INFO'a çek
_verbose = os.environ.get("NYRON_VERBOSE", "").strip().lower() in ("1", "true", "yes", "on")
_console_level = logging.INFO if _verbose else logging.WARNING

_file_level_name = str(LOGGING.get("level", "INFO")).upper()
_file_level = getattr(logging, _file_level_name, logging.INFO)

root_logger = logging.getLogger()
root_logger.setLevel(min(_file_level, _console_level))

file_h = logging.FileHandler(_log_file, encoding="utf-8")
file_h.setLevel(_file_level)
file_h.setFormatter(logging.Formatter(_fmt))

console_h = logging.StreamHandler(sys.stderr)
console_h.setLevel(_console_level)
console_h.setFormatter(logging.Formatter(_fmt))

# Aynı process içinde tekrar çalıştırma olursa handler birikmesini önle.
if not any(isinstance(h, logging.FileHandler) and getattr(h, "baseFilename", None) == str(_log_file) for h in root_logger.handlers):
    root_logger.addHandler(file_h)
if not any(isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler) for h in root_logger.handlers):
    root_logger.addHandler(console_h)

logger = logging.getLogger(__name__)

try:
    logger.info(
        "Entrypoint: file=%s cwd=%s exe=%s argv=%s",
        str(Path(__file__).resolve()),
        os.getcwd(),
        sys.executable,
        sys.argv,
    )
    logger.info("sys.path[0]=%s", sys.path[0] if sys.path else "")
except Exception:
    # Logging should never block startup.
    pass


if __name__ == "__main__":
    _configure_utf8_stdio()
    _ensure_requirements()

    import matplotlib

    matplotlib.use("qtagg", force=True)

    from config import APP

    logger.info("%s (PySide6) başlatılıyor", APP.get("name", "Nyron"))
    try:
        from qt_app.main_window import run_app

        run_app()
    except Exception as e:
        logger.critical("Kritik hata: %s", e, exc_info=True)
        sys.exit(1)
