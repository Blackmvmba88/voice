SHELL := /bin/bash
.PHONY: check evidence clean
check:
	@mkdir -p evidence
	@python -c 'import datetime,platform,sys;print("UTC:",datetime.datetime.now(datetime.timezone.utc).isoformat());print("Python:",sys.version);print("Platform:",platform.platform())' | tee evidence/environment.log
	@git rev-parse HEAD >> evidence/environment.log 2>/dev/null || true
	@set -o pipefail; python -m pytest -q --maxfail=1 --junitxml=evidence/junit.xml 2>&1 | tee evidence/pytest.log
	@set -o pipefail; python scripts/check_vocalframe_contract.py --strict --log evidence/contract.log
	@python -c 'import hashlib,pathlib,json; p=pathlib.Path("evidence"); files=sorted(x for x in p.iterdir() if x.is_file() and x.name!="sha256.json"); (p/"sha256.json").write_text(json.dumps({x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in files},indent=2)+"\\n")'
evidence: check
	@ls -lh evidence/
clean:
	rm -rf evidence .pytest_cache
