# Publishing AXIOM to PyPI

The distribution is named **`loki-axiom`** (the import package stays `axiom`, and the
CLI command stays `axiom`). Once published, anyone can:

```bash
pip install loki-axiom
axiom serve            # or: axiom analyze <path>
```

---

## 1. One-time: accounts + tokens

1. Create accounts: https://pypi.org/account/register/ and https://test.pypi.org/account/register/
2. Create an API token: PyPI → Account settings → **API tokens** → *Add API token*
   (scope it to the project after the first upload). Copy the `pypi-...` token.
3. Store it. Either a `~/.pypirc`:
   ```ini
   [pypi]
     username = __token__
     password = pypi-AgEIcHl...your-token...

   [testpypi]
     username = __token__
     password = pypi-AgEIcHl...your-testpypi-token...
   ```
   …or set env vars per upload:
   ```powershell
   $env:TWINE_USERNAME = "__token__"
   $env:TWINE_PASSWORD = "pypi-AgEIcHl...your-token..."
   ```

## 2. Build the distribution

```powershell
make build-wheel        # -> dist/loki_axiom-1.0.0-py3-none-any.whl + .tar.gz
```
(or `python -m build`). Check it: `twine check dist/loki_axiom-*`.

## 3. Test on TestPyPI first (recommended)

```powershell
make publish-test
# then verify in a clean venv:
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ loki-axiom
axiom version
```

## 4. Publish for real

```powershell
make publish            # twine upload dist/loki_axiom-*
```
Done. `pip install loki-axiom` now works for everyone.

## 5. Shipping updates

1. Bump `version` in `pyproject.toml` (PyPI refuses re-uploading the same version).
2. `make build-wheel && make publish`.
3. Tag the release: `git tag v1.0.1 && git push --tags`.

---

## Notes
- **Heavy optional deps** (`torch`, `chromadb`, `bcc`) are extras, not core — a plain
  `pip install loki-axiom` stays lightweight; users add `pip install "loki-axiom[ml]"` etc.
- The `axiom` **console command** comes from `[project.scripts]` — installs automatically.
- Migrations (`alembic/`) and bundled model (`gnn_v1.npz`) ship inside the wheel so
  `axiom serve` works after a bare `pip install`.
- For the **VS Code extension** on the Marketplace, that's a separate flow: `vsce publish`
  (needs an Azure DevOps publisher + token) — see SETUP.md §4.
