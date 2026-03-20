# capsec audit GitHub Action

Static capability audit for Rust crates. Detects ambient authority (filesystem, network, environment, process, FFI) calls in your code.

## Usage

```yaml
name: Capability Audit
on: [pull_request]

permissions:
  contents: read
  security-events: write   # Required for SARIF upload
  pull-requests: write     # Required for PR review comments

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
      - uses: capsec/audit-action@v1
        with:
          fail-on: high
```

## Inputs

| Input | Default | Description |
|-------|---------|-------------|
| `version` | `latest` | cargo-capsec version to install |
| `fail-on` | `high` | Risk threshold: `low`, `medium`, `high`, `critical` |
| `baseline` | `.capsec-baseline.json` | Path to baseline file (empty to disable) |
| `diff` | `auto` | Only fail on new findings. `auto` enables on PRs. |
| `format` | `sarif` | Output format: `text`, `json`, `sarif` |
| `upload-sarif` | `true` | Upload SARIF to GitHub Code Scanning |
| `comment-on-pr` | `true` | Post inline PR review comments via reviewdog |
| `working-directory` | `.` | Path to Cargo workspace root |
| `token` | `${{ github.token }}` | GitHub token |
| `install-from` | `crates-io` | Install method: `crates-io` or `git` |
| `git-repo` | `https://github.com/bordumb/capsec` | Git URL when `install-from` is `git` |

## Outputs

| Output | Description |
|--------|-------------|
| `sarif-file` | Path to generated SARIF file |
| `finding-count` | Number of findings |
| `exit-code` | `0` = pass, `1` = findings exceed threshold, `2` = runtime error |

## Examples

### Minimal (fail on high-risk findings)

```yaml
- uses: capsec/audit-action@v1
```

### With baseline diffing (only fail on new findings)

```yaml
- uses: capsec/audit-action@v1
  with:
    fail-on: high
    baseline: .capsec-baseline.json
    diff: 'true'
```

### Install from git (before crates.io publish)

```yaml
- uses: capsec/audit-action@v1
  with:
    install-from: git
    git-repo: https://github.com/bordumb/capsec
```

### Monorepo with custom working directory

```yaml
- uses: capsec/audit-action@v1
  with:
    working-directory: ./rust-workspace
```

### SARIF only (no PR comments)

```yaml
- uses: capsec/audit-action@v1
  with:
    comment-on-pr: 'false'
```

## How it works

1. Installs `cargo-capsec` (from crates.io or git)
2. Runs `cargo capsec audit --format sarif --fail-on <threshold>`
3. Uploads SARIF to GitHub Code Scanning (appears in Security tab)
4. Posts inline review comments on PR diffs via reviewdog
5. Fails the check if new findings exceed the threshold

## Permissions

| Permission | Required for |
|-----------|-------------|
| `security-events: write` | SARIF upload to Code Scanning |
| `pull-requests: write` | Inline PR review comments |
| `contents: read` | Reading source code |

## License

Apache 2.0
