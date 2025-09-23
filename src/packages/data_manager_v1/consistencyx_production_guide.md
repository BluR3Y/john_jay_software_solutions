
# ConsistencyX — Production Guide (v0.1.0)

This guide explains how to deploy and operate **ConsistencyX** in production: installation, configuration, execution (CLI & API), performance tuning, extensibility, testing, and troubleshooting. It is aligned with the scaffold you downloaded (`consistencyx-0.1.0.zip`).

---

## 1) Overview

**ConsistencyX** is a **config‑driven** data consistency and compilation engine. It:
- Reads from multiple sources via **adapters** (Excel, Access; easily extensible).
- Normalizes data (aliasing, typing) and runs **declarative transforms** (mutations).
- **Validates** against a canonical schema.
- **Compiles** multiple inputs into unified targets with merge rules.
- **Compares** artifacts and writes **reports**.
- Writes **snapshots** (Parquet preferred; CSV fallback) for reproducibility.

### Design principles
- **Declarative policy, imperative engine**: the JSON config describes *what*, the package decides *how*.
- **Separation of concerns**: sources vs. schema vs. compilation vs. comparison.
- **Deterministic**: same config + same inputs → same outputs; easy to test and audit.
- **Pluggable**: adapters, transforms, validators are easy to extend.

---

## 2) Install & System Requirements

```bash
# inside the unzipped project directory
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e .[excel,access,parquet]
```

- **Python**: 3.9+
- **Excel**: `openpyxl` is installed by the `[excel]` extra.
- **Access** (Windows): `pyodbc` plus the **Microsoft Access ODBC driver** (64‑bit or 32‑bit to match Python).
- **Access** (macOS/Linux): Consider using your own DB manager shim (e.g., UCanAccess via `jaydebeapi`) and inject it (see §7).

> **Tip:** If Parquet support is unavailable, snapshots and some reports fall back to CSV automatically.

---

## 3) Folder Structure (key files)

```
consistencyx/
  adapters/           # Excel/Access built-ins + shims for your managers
  compare/            # keyed diffs + report writer
  compile/            # keyed merge + snapshots
  io/                 # loader (AdapterRegistry) and writer utils
  normalize/          # alias + typing
  transform/          # column/row transforms and registry
  validate/           # basic validation rules
  runner.py           # programmatic API
  cli.py              # CLI entry point: `consistencyx run ...`
examples/
  example_config.json
```

---

## 4) Configuration — Schema & Semantics

The engine expects a single JSON file. Minimal top‑level keys:

```jsonc
{
  "config_version": 1,
  "schema": { "aliases": { /* canonical fields & rules */ } },
  "sources": [ /* or 'files' for backward-compat */ ],
  "compile":  { "targets": [ /* compiled models */ ] },
  "compare":  { "pairs": [ /* diffs to run */ ] },
  "output":   { "snapshots": { }, "reports": { } }
}
```

### 4.1 `schema.aliases` — Canonical fields & validation
Each key is a canonical column name seen by the engine after aliasing.

```json
"schema": {
  "aliases": {
    "grant_id": { "type": "number", "identifier": true, "not_null": true },
    "title":    { "type": "string", "not_null": true },
    "status":   { "type": "string", "allowed_values": ["Active","Closed","Pending"] },
    "submission_date": { "type": "date", "date": { "format": "%m/%d/%Y" } }
  }
}
```

Supported `type` values: `string`, `number`, `integer`, `date`, `bool`  
Supported validation hints: `identifier`, `not_null`, `allowed_values`

> **Order of operations:** alias → column transforms → **type coercion** → row transforms → **validation**.

### 4.2 `sources` — Where to read & how to map raw → canonical
Each source describes a file/DB, the `tables` to read, and per‑table details.

```json
"sources": [
  {
    "id": "excel1",
    "type": "excel",
    "path": "path/to/workbook.xlsx",
    "tables": [{
      "name": "Sheet1",
      "table_id": "excel1_sheet1",
      "columns": {
        "Title":          { "alias": "title" },
        "GrantStatus":    { "alias": "status" },
        "SubmissionDate": { "alias": "submission_date" }
      },
      "transforms": {
        "columns": {
          "title":           [ { "strip": {} }, { "titlecase": {} } ],
          "status":          [ { "strip": {} }, { "map": { "Closed Out": "Closed" } } ],
          "submission_date": [ { "parse_date": { "format": "%m/%d/%Y" } } ]
        },
        "row": [
          { "drop_if_null": { "cols": ["grant_id"] } },
          { "dedupe_on": { "cols": ["grant_id","submission_date"], "keep": "first" } }
        ]
      }
    }]
  },
  {
    "id": "access1",
    "type": "access",
    "path": "path/to/database.accdb",
    "tables": [{
      "name": "grants",
      "table_id": "grants_table",
      "columns": {
        "Title":          { "alias": "title" },
        "GrantStatus":    { "alias": "status" },
        "SubmissionDate": { "alias": "submission_date" }
      }
    }]
  }
]
```

Notes:
- `type` can be inferred from `path` when omitted.
- Per‑source options (e.g., `usecols`, `columns_select`, `where`) are passed through to adapters/shims.
- `table_id` is the **stable handle** referenced elsewhere (compile/compare).

### 4.3 `compile.targets` — Build unified models
A target merges multiple inputs into a canonical model.

```json
"compile": {
  "targets": [
    {
      "name": "grants_compiled",
      "key": ["grant_id"],
      "inputs": ["excel1_sheet1", "grants_table"],
      "merge_rules": {
        "title": "first_non_null",
        "submission_date": "max",
        "status": "prefer_enum_order:Active,Pending,Closed"
      },
      "post_transforms": {
        "columns": {
          "duration_days": [ { "compute": { "expr": "days_between(end_date, start_date)" } } ]
        }
      }
    }
  ]
}
```

**Precedence:** In v0.1.0 effective precedence is the **order of `inputs`**. The first input has highest priority when `first_non_null` is used. (A `precedence` field is accepted but *not yet* applied.)

Supported merge rules: `first_non_null`, `max`, `min`, `prefer_enum_order:<v1,v2,...>`

### 4.4 `compare.pairs` — Diffs
```json
"compare": {
  "pairs": [{
    "left":  "grants_compiled",
    "right": "grants_compiled",
    "on":    ["grant_id"],
    "output": { "path": "./reports/grants_diff.xlsx", "format": "excel" }
  }]
}
```
> v0.1.0 compares artifacts **within the same run**. To diff snapshots across runs, load the two snapshots manually (small helper script recommended).

### 4.5 `output`
```json
"output": {
  "snapshots": { "path": "./snapshots", "format": "parquet" },
  "reports":   { "path": "./reports" }
}
```

- Snapshots prefer **Parquet** (`pyarrow`); otherwise **CSV** fallback.
- Reports prefer **Excel** (`openpyxl`); otherwise CSV bundle.

---

## 5) Execution

### 5.1 CLI
```bash
consistencyx run path/to/config.json \
  [--no-snapshots] [--no-reports] \
  [--inject-wbm] [--inject-dbm]
```
- `--inject-wbm`: if your `workbook_manager` is importable, the loader uses it for Excel.
- `--inject-dbm`: if your `db_manager` is importable, the loader uses it for Access.

### 5.2 Programmatic API
```python
from consistencyx.runner import run_with_config
from consistencyx.io.loader import AdapterRegistry

cfg = {...}  # or json.load(...)

result = run_with_config(
    cfg,
    registry_kwargs={"workbook_manager": my_wbm, "db_manager": my_dbm},
    write_snapshots=True,
    write_reports=True,
)

compiled = result["compiled"]     # dict[str, DataFrame]
findings = result["findings"]     # dict[table_id, list[dict]]
diffs    = result["diffs"]        # dict[name, diff-struct]
ts       = result["timestamp"]
```

---

## 6) Transforms (Mutations)

Transforms are **declarative**. Engine applies them in a fixed order to ensure determinism.

**Order:** alias → `transforms.columns` → type coercion → `transforms.row` → validation → compile → `post_transforms.columns`

### 6.1 Column transforms (selected)
- `strip`, `lower`, `upper`, `titlecase`
- `replace` / `regex_replace`
- `map` (supports wildcards: `"Active*": "Active"`)
- `parse_date`
- `cast` (`number`, `integer`, `bool`, `string`)
- `fillna`
- `currency_to_number`
- `coalesce` (use other columns if current is null)
- `concat` (join columns with a separator)
- `compute` (small expression engine with helpers `days_between`, `today()`, `now()`, and access to other columns)
- `udf` (call into your Python function: `module`, `func`, `kwargs`)

Example:
```json
"columns": {
  "status": [ { "strip": {} }, { "map": { "Closed Out": "Closed" } } ],
  "amount": [ { "currency_to_number": {} }, { "fillna": { "value": 0 } } ],
  "duration": [ { "compute": { "expr": "days_between(end_date, start_date)" } } ]
}
```

### 6.2 Row transforms
- `drop_if_null` → `{ "cols": ["grant_id"] }`
- `filter` → `{ "expr": "status == 'Active' and amount > 0" }` (pandas `query` syntax)
- `dedupe_on` → `{ "cols": ["grant_id","submission_date"], "keep": "first" }`

---

## 7) Adapters & Manager Injection

### Built-ins
- **Excel** via `pandas.read_excel` (raw strings; typing later).
- **Access** via ODBC (`pyodbc`) on Windows.

### Inject your managers
If you already have `workbook_manager` and `db_manager`, inject them:
```python
from consistencyx.io.loader import AdapterRegistry
registry = AdapterRegistry(workbook_manager=wbm, db_manager=dbm)
tables = load_sources(cfg, registry)
```

Or use the CLI flags `--inject-wbm` / `--inject-dbm`.

> The adapters are **thin shims**—IO only. All business logic remains in ConsistencyX.

---

## 8) Validation, Snapshots, and Reports

- **Validation** is recorded per input table (missing required fields, enum violations, duplicate identifiers).
- **Snapshots** are written for each compiled target with a timestamp suffix.
- **Diff reports**: Excel with sheets **added**, **removed**, and **chg_<column>** per changed column (CSV fallback).

---

## 9) Performance & Reliability

- **Selective reads**: use `usecols` (Excel) / `columns_select` + `where` (Access) to avoid scanning entire tables.
- **Typing later**: adapters return strings where possible; heavy parsing happens once, centrally.
- **Memory**: plan for DataFrame sizes in the GB range if needed. (v0.1.0 loads eagerly; chunked pipelines are a roadmap item.)
- **Determinism**: prefer explicit `inputs` order to control precedence.
- **Idempotence**: re-running with the same config and inputs should produce identical outputs (timestamps aside).
- **Observability**: wrap runner invocation with your logger (timings, row counts, validation counts, diff counts).

---

## 10) Security & Compliance

- Keep secrets **out of config**; use environment variables or your managers for credentials.
- Avoid logging sensitive values. Log **counts**, not field contents, where possible.
- Maintain a **retention policy** for snapshots and reports (rotate or archive).

---

## 11) Extensibility

- **Transform**: add new operations by registering functions in `transform/registry.py` with `@register("op_name")`.
- **Row ops**: register with `@register_row("op_name")`.
- **Validators**: extend `validate/rules.py` with new checks and return standardized findings.
- **Adapters**: add new source types and register via `AdapterRegistry(extra_factories=...)`.

---

## 12) Testing Strategy

- **Unit tests** for transforms and validators with small DataFrames.
- **Golden tests**: store expected compiled outputs and diffs as Parquet/CSV and compare.
- **Smoke tests** for adapters (Excel/Access connectivity, sheet/table presence).

Example with `pytest`:
```python
def test_first_non_null_merge():
    # build tiny inputs and assert merged results
    ...
```

CI: run tests on Linux; for Access integration, rely on injected `db_manager` that mocks the ODBC layer.

---

## 13) Troubleshooting

- **ODBC driver not found**: Ensure the *Microsoft Access ODBC* driver matches Python bitness (64‑bit vs 32‑bit).
- **Date parsing returns NaT**: Verify `schema.aliases.<field>.date.format` matches the raw format (e.g., `"%m/%d/%Y"`).
- **Empty diffs**: Remember v0.1.0 compares targets **within the same run** unless you manually load previous snapshots.
- **Excel writer errors**: Ensure `openpyxl` is installed; otherwise the system writes CSV fallbacks.

---

## 14) Roadmap / Non‑goals in v0.1.0

- Apply `precedence` array at compile time (currently order of `inputs` governs precedence).
- Automatic **snapshot diffing across runs** (helper planned).
- Chunked/streaming reads & joins for very large datasets.
- Rich HTML report with validation summaries and hyperlinks.

---

## 15) FAQ

**Q: Does “mutate” still exist?**  
A: Yes. Use `transforms.columns` / `transforms.row` and `post_transforms.columns` with a deterministic order of execution.

**Q: Can I write back to Access/Excel?**  
A: Out of scope for the core runner. Use your managers or custom writers to persist cleaned data intentionally.

**Q: How do I prefer one source over another?**  
A: Place the preferred source **earlier** in `inputs`. For rule `first_non_null`, earlier inputs win.

---

## 16) Minimal End‑to‑End Example

```bash
# 1) Put workbook.xlsx and database.accdb under examples/data/
# 2) Adjust paths in examples/example_config.json
consistencyx run examples/example_config.json --inject-wbm --inject-dbm
# Outputs:
# - snapshots/<target>_<timestamp>.parquet (or .csv)
# - reports/diff_<left>_vs_<right>.xlsx (or CSVs)
```

---

## 17) Versioning & Upgrades

- Config includes `"config_version": 1` for migration control.
- On breaking changes, bump the config version and provide a migration script.

---

**That’s it.** Use this guide as your internal runbook and onboarding doc. For any API surface changes you make, extend the relevant sections here.
