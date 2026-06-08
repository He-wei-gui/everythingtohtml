# Releasing everythingtohtml

Releases are published to [PyPI](https://pypi.org/project/everythingtohtml/)
automatically by the [`release.yml`](../.github/workflows/release.yml) workflow
whenever a `v*` tag is pushed. Publishing uses **PyPI Trusted Publishing**, so no
API token is ever stored in the repository.

## One-time setup (PyPI Trusted Publishing)

Do this once, before the first release.

1. Create the project owner account on [PyPI](https://pypi.org/).
2. Go to **PyPI → Your projects → Publishing** (or, for a brand-new project name,
   **Account settings → Publishing → Add a new pending publisher**).
3. Register a **GitHub** trusted publisher with:
   - **Owner**: `He-wei-gui`
   - **Repository**: `everythingtohtml`
   - **Workflow name**: `release.yml`
   - **Environment**: `pypi`
4. In the GitHub repo, create an **Environment** named `pypi`
   (**Settings → Environments → New environment**). Optionally add required
   reviewers so a human approves each publish.

That's it — no secrets to copy around.

## Cutting a release

1. Make sure `main` is green (CI passing).
2. Bump the version in
   [`src/everythingtohtml/__about__.py`](../src/everythingtohtml/__about__.py),
   following [SemVer](https://semver.org/).
3. Move the `## [Unreleased]` notes in [`CHANGELOG.md`](../CHANGELOG.md) under a
   new dated version heading, and update the comparison links at the bottom.
4. Commit:

   ```console
   git commit -am "Release vX.Y.Z"
   ```

5. Tag and push:

   ```console
   git tag -a vX.Y.Z -m "everythingtohtml X.Y.Z"
   git push origin main vX.Y.Z
   ```

6. The `release.yml` workflow builds the sdist + wheel, runs `twine check`, and
   publishes to PyPI. Watch the **Actions** tab.

7. (Optional) Create a GitHub Release from the tag and paste the changelog notes.

## Manual publish (fallback)

If you ever need to publish by hand:

```console
python -m pip install --upgrade build twine
python -m build
twine check dist/*
twine upload dist/*        # needs a PyPI API token configured locally
```
