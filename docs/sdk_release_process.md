# SDK Release Process Documentation

This document outlines the procedures for releasing the DTLPY SDK. It covers the standard sprint release cycle and the hotfix process for production issues.

## Prerequisites

- **Access**: GitHub Actions on `ddoe-platform/dtlpy`, PyPI (handled via workflow secrets).
- **Tools**:
    - `git`
    - `bumpversion` (Python package)
    - `python3`
- **Permissions**: You must have write access to `master` and the active sprint branch (e.g. `version/release48`).

## Branching model

The active sprint branch (e.g. `version/release48`) serves as the integration / release‑candidate branch.

- A new sprint branch is created off `master` at the start of each sprint via the `Start New Sprint` workflow. The same `version/release<N>` branch is created in `python-e2e-tests` and `piper-agent-runner`.
- All feature PRs are merged into the active sprint branch during the sprint.
- At the end of the sprint the branch is finalized and promoted to `master`.

---

## 1. Standard Sprint Release

This process tags the final release on the active sprint branch, promotes it to `master`, and publishes to PyPI.

### Step 0: Start of sprint — create the sprint branch (one time, at sprint kickoff)

> Skip this step if the sprint branch already exists.

1. Go to **Actions > Start New Sprint > Run workflow**.
2. Select branch: `master`.
3. Fill in the inputs:
    - `SPRINT_NUMBER`: The new sprint number (e.g. `49`). The workflow will create branch `version/release<SPRINT_NUMBER>`.
4. Run the workflow.

The workflow creates `version/release<N>` in `python-e2e-tests` and `piper-agent-runner` (from `master`), then creates it in `dtlpy` off `master`, runs `bumpversion minor` as its first commit, and pushes the branch with the new tag.

### Step 1: Finalize the sprint (create the release tag)

At the end of the sprint, after the last PR has been merged into the sprint branch:

1. Go to **Actions > Finalize Sprint > Run workflow**.
2. Select branch: the active sprint branch (e.g. `version/release48`).
3. Fill in the inputs:
    - `EXPECTED_VERSION`: The PyPI version expected after the patch bump (e.g. `1.125.3`).

   The workflow operates on the branch it is launched from (selected in step 2), so no branch input is needed.
4. Run the workflow.

What it does: checks that `version/release<N>` exists in `dtlpy`, `piper-agent-runner` and `python-e2e-tests`, checks out the sprint branch, runs `bumpversion patch`, validates that the resulting version matches `EXPECTED_VERSION`, pushes the new commit and tag, and opens the release PRs (see Step 2).

**Verification**: Check the `Tag — Build SDK & Bump Piper Agent Runner` workflow that was triggered by the new tag push (builds the wheel and Docker image, and bumps `piper-agent-runner` on the matching branch). Also verify the Piper Agent Runner workflows complete successfully.

### Step 2: Merge the release PRs

`finalize-sprint` opens (or reuses) one PR per repo:

| Repo | PR |
|---|---|
| `dtlpy` | `version/release<N>` → `master` |
| `piper-agent-runner` | `version/release<N>` → `master` |
| `python-e2e-tests` | `version/release<N>` → `main` |

Once the tag workflow is green (it also bumps `piper-agent-runner`'s release branch, which updates its open PR):

1. Ensure all checks pass on the three PRs.
2. Merge all three (merge commit preferred so `master`/`main` match the release branch HEAD exactly).

### Step 3: Deploy to Production

1. Go to **Actions > Release to Prod (PyPI + public GitHub) > Run workflow**.
2. Select branch: `master`.
3. Fill in the inputs:
    - `FIX_VERSION`: The version tagged in Step 1 (e.g. `1.125.3`).
4. Run the workflow.

> Note: This workflow must run from `master`. It validates that `FIX_VERSION` matches the version in the code, builds the wheel, syncs the release files to the public `github.com/dataloop-ai/dtlpy` repo (commit + `FIX_VERSION` tag), and uploads to PyPI.

### Step 4: Notification

Post a message in the release channel (Slack).

- **Template**: `sdk sprint <Sprint Number> release, version <Version Number>`
- **Example**: `SDK sprint 48 release, version 1.125.3`

---

## 2. Hotfix Release Process

Use this process when a critical fix is required on Production (`master`) outside of the standard sprint cycle.

> The hotfix process is performed manually.

### Step 1: Preparation

1. Request a Hotfix Version to be created in Jira (Point of Contact: Namma).
2. Identify the fix required.

### Step 2: Branching & Merging

1. Checkout `master` and pull the latest changes:
    ```bash
    git checkout master
    git pull origin master
    ```
2. Create a new hotfix branch from `master`.
    - **Naming convention**: `sdk-release-<sprint>-hf`
    - **Example**:
        ```bash
        git checkout -b sdk-release-48-hf
        ```
3. Cherry-pick only the specific fix commit(s) into the hotfix branch (avoid merging the entire sprint branch):
    ```bash
    # Example: cherry-pick a single fix commit from the sprint branch
    git cherry-pick <FIX_COMMIT_SHA>
    ```
    - If the fix spans multiple commits, cherry-pick them individually in order.
    - If the fix is not on the sprint branch yet, cherry-pick directly from the source branch/PR commit.
4. **Resolve Conflicts (Crucial)**:
    - If conflicts appear, resolve them minimally; keep production versions (e.g. `.bumpversion.cfg`, `setup.py`, `dtlpy/__init__.py`) aligned with `master`.

### Step 3: Apply Fix & Bump Version

1. Apply the necessary code fixes to the hotfix branch.
2. Bump the patch version on the hotfix branch:
    ```bash
    bumpversion patch
    ```
3. Push the branch and tags:
    ```bash
    git push --follow-tags
    ```

### Step 4: Merge & Deploy

1. Create a Pull Request from the hotfix branch to `master`.
    - **Check**: The PR should include the code fix **and** the version bump.
2. Merge the PR.
3. Run the Production Release workflow:
    - Go to **Actions > Release to Prod (PyPI + public GitHub) > Run workflow**.
    - Branch: `master`
    - `FIX_VERSION`: The new hotfix version (e.g. `1.125.4`).

### Step 5: Notification

Post a message in the release channel using `@here`.

- **Template**: `@here release SDK sprint <Sprint> HF : version <Version>`
- **Example**: `@here release SDK sprint 48 HF : version 1.125.4`

---

## 3. Workflow Reference & Troubleshooting

All workflows live in `.github/workflows/`; helper scripts live in `.github/scripts/`.

### Workflow: `start-new-sprint.yml`

- **Trigger**: Manual (from `master`).
- **Inputs**: `SPRINT_NUMBER` (e.g. `49`; the branch `version/release<SPRINT_NUMBER>` is created).
- **Function**: Creates `version/release<N>` in `python-e2e-tests` and `piper-agent-runner`, then creates it in `dtlpy` off `master`, runs `bumpversion minor`, and pushes the branch and the new tag.

### Workflow: `finalize-sprint.yml`

- **Trigger**: Manual (from the active sprint branch).
- **Inputs**: `EXPECTED_VERSION`. The sprint branch is taken from the branch the workflow is run on (`github.ref_name`).
- **Function**: Verifies `version/release<N>` exists in all three repos, runs `bumpversion patch` on the sprint branch, validates the resulting version against `EXPECTED_VERSION`, pushes the new commit + tag, and opens the release PRs in `dtlpy` and `piper-agent-runner` (→ `master`) and `python-e2e-tests` (→ `main`).

### Workflow: `release-to-prod.yml`

- **Trigger**: Manual (from `master`).
- **Inputs**: `FIX_VERSION`.
- **Function**:
    1. Validates it runs from `master` and that `FIX_VERSION` matches `.bumpversion.cfg`, `setup.py`, `pyproject.toml`, `dtlpy/__version__.py`, `docs/conf.py`.
    2. Builds the Python wheel and runs `twine check`.
    3. Syncs the release files to public `github.com/dataloop-ai/dtlpy`, commits `Release <FIX_VERSION>`, tags `<FIX_VERSION>` (fails if the tag already exists).
    4. Uploads to PyPI using `twine`.

### Auto workflows (informational)

- **`tag.yml`** — runs on every pushed tag. Builds the wheel, uploads it to GCS, builds and pushes the Docker image, and bumps `piper-agent-runner` on the matching branch (`version/release<N>` → `version/release<N>`, `master` → `master`).
- **`pr.yml`** — for PRs into `version/release<N>`, runs `python-e2e-tests` sanity from its `version/release<N>` branch (fails if missing); other PRs use `main`.
- **`push-sprint.yml`** — runs on pushes to `version/release*`; bumps the patch version on merge commits.

## Common Commands

If `bumpversion` fails locally, ensure you have a clean git state (no uncommitted files).

```bash
# Check status
git status

# Bump patch (1.0.1 -> 1.0.2)
bumpversion patch

# Bump minor (1.0.2 -> 1.1.0)
bumpversion minor
```
