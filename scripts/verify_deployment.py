#!/usr/bin/env python3
"""
verify_deployment.py — Kiểm tra tất cả điều kiện trước khi push lên GitHub.

Chạy: python scripts/verify_deployment.py
Nếu tất cả ✅ → safe to push.
"""
import sys
from pathlib import Path
from rich.console import Console
from rich.table   import Table

console = Console()
ROOT    = Path(__file__).parent.parent
PASS    = "[bold green]✅[/bold green]"
FAIL    = "[bold red]❌[/bold red]"

checks = []

def check(name: str, condition: bool, detail: str = ""):
    checks.append((name, condition, detail))

# ── File checks ───────────────────────────────────────────────────────────────

check("No chart_data.js",
      not (ROOT / "dashboard/js/chart_data.js").exists(),
      "Xóa file này: rm dashboard/js/chart_data.js")

check("No cstc_data.js",
      not (ROOT / "dashboard/js/cstc_data.js").exists(),
      "Xóa file này: rm dashboard/js/cstc_data.js")

check("No large export scripts",
      not any((ROOT / "dashboard" / f).exists()
               for f in ["export_data.py", "export_cstc.py"]),
      "Xóa: rm dashboard/export_data.py dashboard/export_cstc.py")

check("config.js exists",
      (ROOT / "dashboard/js/config.js").exists(),
      "Tạo file theo Session 6 TASK A")

check("SETUP_GITHUB.md exists",
      (ROOT / "SETUP_GITHUB.md").exists(),
      "Tạo file theo Session 6 TASK G")

check(".env.example exists",
      (ROOT / ".env.example").exists(),
      "Tạo file theo Session 6 TASK E")

check("No .env committed",
      not (ROOT / ".env").exists() or
      (ROOT / ".gitignore").read_text(encoding="utf-8").find(".env\n") >= 0,
      "Thêm .env vào .gitignore")

# ── .gitignore checks ─────────────────────────────────────────────────────────
gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8") if (ROOT / ".gitignore").exists() else ""

check("*.parquet in gitignore",  "*.parquet"        in gitignore,
      "Thêm '*.parquet' vào .gitignore")
check("*.json.gz in gitignore",  "*.json.gz"        in gitignore,
      "Thêm '*.json.gz' vào .gitignore")
check("data/static/ in gitignore","data/static/"    in gitignore,
      "Thêm 'data/static/' vào .gitignore")
check("*_data.js in gitignore",  "*_data.js"        in gitignore,
      "Thêm '*_data.js' vào .gitignore")

# ── GitHub Actions checks ─────────────────────────────────────────────────────
workflows_dir = ROOT / ".github/workflows"
check("build_history.yml exists",
      (workflows_dir / "build_history.yml").exists(), "")
check("daily_update.yml exists",
      (workflows_dir / "daily_update.yml").exists(), "")

# ── Config.js URL check ───────────────────────────────────────────────────────
config_js = (ROOT / "dashboard/js/config.js").read_text(encoding="utf-8") if (ROOT / "dashboard/js/config.js").exists() else ""
check("config.js has STATIC_BASE_URL",
      "STATIC_BASE_URL" in config_js, "")
check("config.js URL not placeholder",
      "YOUR_GITHUB_USERNAME" not in config_js,
      "Thay YOUR_GITHUB_USERNAME bằng username thực trong config.js")

# ── Size checks ───────────────────────────────────────────────────────────────
large_files = []
for f in ROOT.rglob("*"):
    if f.is_file() and f.stat().st_size > 50 * 1024 * 1024:  # > 50MB
        if ".git" not in str(f):
            large_files.append(f)
check("No files > 50MB in working tree",
      len(large_files) == 0,
      f"Large files: {[str(f.relative_to(ROOT)) for f in large_files]}")

# ── Print results ─────────────────────────────────────────────────────────────
table = Table(title="Deployment Verification", show_header=True)
table.add_column("Check",   style="cyan")
table.add_column("Status",  justify="center")
table.add_column("Action",  style="dim")

all_pass = True
for name, ok, detail in checks:
    table.add_row(name, PASS if ok else FAIL, detail if not ok else "")
    if not ok:
        all_pass = False

console.print(table)

if all_pass:
    console.print("\n[bold green]✅ Tất cả checks passed! Safe to push.[/bold green]")
    console.print("  git add . && git commit -m 'refactor: migrate to per-ticker architecture'")
    console.print("  git push origin main")
    sys.exit(0)
else:
    n_fail = sum(1 for _, ok, _ in checks if not ok)
    console.print(f"\n[bold red]❌ {n_fail} checks failed. Fix before pushing.[/bold red]")
    sys.exit(1)
