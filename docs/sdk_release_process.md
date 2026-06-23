# SDK Release Process Documentation

This document outlines the procedures for releasing the DTLPY SDK. It covers the standard sprint release cycle and the hotfix process for production issues.

## Prerequisites

- **Access**: Bitbucket Pipelines, GitHub Repository (`dataloop-ai/dtlpy`), PyPI (handled via pipeline credentials).
- **Tools**:
    - `git`
    - `bumpversion` (Python package)
    - `python3`
- **Permissions**: You must have write access to `master` and the active sprint branch (e.g. `version/sprint48`).

## Branching model

The active sprint branch (e.g. `version/sprint48`) serves as the integration / release‑candidate branch.

- A new sprint branch is created off `master` at the start of each sprint via the `start-new-sprint` custom pipeline.
- All feature PRs are merged into the active sprint branch during the sprint.
- At the end of the sprint the branch is finalized and promoted to `master`.

---

## 1. Standard Sprint Release

This process tags the final release on the active sprint branch, promotes it to `master`, and publishes to PyPI.

### Step 0: Start of sprint — create the sprint branch (one time, at sprint kickoff)

> Skip this step if the sprint branch already exists.

1. Go to **Pipelines > Run Pipeline**.
2. Select branch: `master`.
3. Select pipeline: `custom: start-new-sprint`.
4. Fill in the variables:
    - `SPRINT_NUMBER`: The new sprint number (e.g. `49`). The pipeline will create branch `version/sprint<SPRINT_NUMBER>`.
5. Run the pipeline.

The pipeline creates the new branch off `master`, runs `bumpversion minor` as its first commit, and pushes the branch with the new tag.

### Step 1: Finalize the sprint (create the release tag)

At the end of the sprint, after the last PR has been merged into the sprint branch:

1. Go to **Pipelines > Run Pipeline**.
2. Select branch: the active sprint branch (e.g. `version/sprint48`).
3. Select pipeline: `custom: finalize-sprint`.
4. Fill in the variables:
    - `EXPECTED_VERSION`: The PyPI version expected after the patch bump (e.g. `1.125.3`).

   The pipeline operates on the branch it is launched from (selected in step 2), so no branch variable is needed.
5. Run the pipeline.

What it does: checks out the sprint branch, runs `bumpversion patch`, validates that the resulting version matches `EXPECTED_VERSION`, and pushes the new commit and tag.

**Verification**: Check the tag pipeline that was triggered by the new tag push (builds the wheel, Docker image, and updates `dataloop-infra`). Also verify the Piper Agent Runner pipelines complete successfully.

### Step 2: Merge sprint branch to `master`

Once the sprint branch is finalized and the tag pipeline is green:

1. Create a Pull Request from the active sprint branch into `master`.
2. Ensure all checks pass.
3. Merge (fast‑forward preferred so `master` matches the sprint branch HEAD exactly).

### Step 3: Deploy to Production

1. Go to **Pipelines > Run Pipeline**.
2. Select branch: `master`.
3. Select pipeline: `custom: release-to-prod`.
4. Fill in the variables:
    - `FIX_VERSION`: The version tagged in Step 1 (e.g. `1.125.3`).
5. Run the pipeline.

> Note: This pipeline syncs code to GitHub, creates tags, builds the wheel, and uploads to PyPI.

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
3. Run the Production Release Pipeline:
    - Go to **Pipelines > Run Pipeline**.
    - Branch: `master`
    - Pipeline: `custom: release-to-prod`
    - `FIX_VERSION`: The new hotfix version (e.g. `1.125.4`).

### Step 5: Notification

Post a message in the release channel using `@here`.

- **Template**: `@here release SDK sprint <Sprint> HF : version <Version>`
- **Example**: `@here release SDK sprint 48 HF : version 1.125.4`

---

## 3. Pipeline Reference & Troubleshooting

### Pipeline: `start-new-sprint`

- **Trigger**: Manual (from `master`).
- **Inputs**: `SPRINT_NUMBER` (e.g. `49`; the branch `version/sprint<SPRINT_NUMBER>` is created).
- **Function**: Creates the new sprint branch off `master`, runs `bumpversion minor`, pushes the branch and the new tag.

### Pipeline: `finalize-sprint`

- **Trigger**: Manual (from the active sprint branch).
- **Inputs**: `EXPECTED_VERSION`. The sprint branch is taken from the branch the pipeline is run on (`$BITBUCKET_BRANCH`).
- **Function**: Checks out the sprint branch, runs `bumpversion patch`, validates the resulting version against `EXPECTED_VERSION`, and pushes the new commit + tag.

### Pipeline: `release-to-prod`

- **Trigger**: Manual (from `master`).
- **Inputs**: `FIX_VERSION`.
- **Function**:
    1. Syncs Bitbucket repo to GitHub.
    2. Creates Git tags.
    3. Builds the Python wheel (`bdist_wheel`).
    4. Uploads to PyPI using `twine`.

### Auto pipelines (informational)

- **`tags: "*"`** — runs on every pushed tag. Builds the wheel, uploads it to GCS, builds and pushes the Docker image, and updates `dataloop-infra`.
- **`pull-requests: "**"`** — runs the `python-e2e-tests` sanity suite for every PR.

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
