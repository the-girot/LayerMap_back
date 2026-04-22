# run_tests_per_file.py
import subprocess
import sys
from pathlib import Path
from datetime import datetime

TEST_FILES = [
    # "tests/test_cache.py",
    "tests/test_contract.py",
    # "tests/test_errors.py",
    "tests/test_functional_enhanced.py",
    # "tests/test_health.py",
    "tests/test_integration.py",
    # "tests/test_mapping_tables_api.py",
    "tests/test_performance_api.py",
    # "tests/test_projects_api.py",
    # "tests/test_rpi_mappings_api.py",
    "tests/test_security_api.py",
    # "tests/test_sources_api.py",
    # "tests/test_validation.py",
]

OUTPUT_DIR = Path("test_results")
OUTPUT_DIR.mkdir(exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
summary_lines = []
summary_lines.append(f"Test run: {timestamp}\n")
summary_lines.append("=" * 60 + "\n")

for test_file in TEST_FILES:
    file_path = Path(test_file)
    if not file_path.exists():
        summary_lines.append(f"SKIP  {test_file} (file not found)\n")
        continue

    stem = file_path.stem
    out_file = OUTPUT_DIR / f"{stem}_{timestamp}.txt"

    print(f"Running {test_file} ...", end=" ", flush=True)

    result = subprocess.run(
        [
            sys.executable, "-m", "pytest",
            test_file,
            "-v",
            "--tb=short",
            "--no-header",
            f"--junit-xml={OUTPUT_DIR}/{stem}_{timestamp}.xml",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    output = result.stdout + result.stderr
    out_file.write_text(output, encoding="utf-8")

    # Вытащить итоговую строку (последняя непустая)
    lines = [l for l in result.stdout.splitlines() if l.strip()]
    summary_line = lines[-1] if lines else "(no output)"
    status = "PASS" if result.returncode == 0 else "FAIL"
    summary_lines.append(f"{status}  {test_file:<55} {summary_line}\n")

    print(f"{status} → {out_file.name}")

# Записать сводку
summary_file = OUTPUT_DIR / f"_summary_{timestamp}.txt"
summary_file.write_text("".join(summary_lines), encoding="utf-8")

print()
print("=" * 60)
print(f"Summary: {summary_file}")
print(f"Results dir: {OUTPUT_DIR}/")