# Local evidence runner

```bash
python -m pip install -e '.[dev]'
make check
make evidence
# optional: python -m pip install pre-commit && pre-commit install
```

`make check` runs all tests and the standalone contract smoke check. A failed
command returns nonzero even through `tee` (bash pipefail). Artifacts are kept
under ignored `evidence/`: JUnit XML, pytest log, contract log, environment
metadata and SHA-256 hashes. SHA-256 proves file integrity **only if its digest
is preserved elsewhere**; it is not a cryptographic signature.

No timing guarantee: runtime depends on the host and installed packages.
Pre-commit uses `tests/` (this repository does not have `tests/unit`).
The optional pre-commit hook runs only for matched paths and is not a substitute
for a clean-environment CI run.

GitHub Actions remains an independent verification mechanism. Do not change
runner image or merge policy without diagnosing the current provisioning failure.
