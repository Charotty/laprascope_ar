# Continuous Integration & Deployment

## GitHub Actions Workflows

| Path | Purpose |
|------|---------|
| `.github/workflows/python-ci.yml` | Lint (black, isort) + `pytest` for backend on every push/PR |
| `.github/workflows/unity-ci.yml` | Unity Test Runner PlayMode tests on Ubuntu runners |

### python-ci.yml
```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'
      - run: pip install -r backend/requirements.txt
      - run: pip install black isort pytest
      - run: black --check backend
      - run: isort --check backend
      - run: pytest backend/tests -v
```

### unity-ci.yml
Uses [game-ci/unity-test-runner](https://github.com/game-ci/unity-test-runner) docker images.
Requires `UNITY_LICENSE` or personal return license activation token.

```
with:
  projectPath: unity_client
  unityVersion: 2022.3.17f1
```

Artifacts:
* `TestResults` XML (JUnit) uploaded for GitHub UI.

---

## Future CD
* Docker image build & push (see `docs/docker.md`).
* GitHub Pages or S3 hosting for WebGL build.
