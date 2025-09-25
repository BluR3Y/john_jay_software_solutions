# Data Manager Starter Guide

This guide introduces the **data_manager** Python package: a
production-ready system for ingesting, compiling, comparing, and
exporting datasets from multiple sources (Excel spreadsheets, Access
databases, etc.) using a declarative JSON configuration.

------------------------------------------------------------------------

## 1. Installation

Ensure Python 3.10+ is installed.

``` bash
git clone <your_repo_url>
cd data_manager
pip install -e .
```

Dependencies include: - pandas (data manipulation) - openpyxl, xlrd
(Excel IO) - pyodbc (Access DB connectivity, Windows only) - jsonschema
(config validation)

------------------------------------------------------------------------

## 2. Configuration File

The engine is fully schema-driven. Configs are written in JSON. Example:

``` json
{
  "version": "1.1",
  "timezone": "America/New_York",
  "output": "${DATA_MANAGER_OUT}/data_manager_out",
  "schema": {
    "aliases": {
      "grant_id": { "type": "integer", "identifier": true },
      "title": { "type": "string" },
      "submission_date": {
        "type": "date",
        "date": { "format": "%Y-%m-%d" }
      },
      "status": {
        "type": "string",
        "enum": ["Active","Closed","Pending"]
      }
    }
  }
}
```

### Key sections

-   **schema.aliases**: Defines normalized fields across sources.
-   **sources**: Points to Excel/Access tables, mapping raw columns →
    aliases, optionally with transforms.
-   **compile**: Combines inputs into targets, with merge rules and
    filters.
-   **compare**: Defines dataset pairs to reconcile differences.
-   **export**: Outputs Excel workbooks with custom sheets, column
    mappings, and filters.

------------------------------------------------------------------------

## 3. Running the Package

After writing a config:

``` bash
DATA_MANAGER_OUT=./out data-manager run --config ./config.json
```

Steps executed:

1.  **Load sources**: Read Excel sheets / Access tables, normalize
    column names, apply transforms.
2.  **Compile**: Merge inputs into logical datasets using join keys +
    merge rules.
3.  **Compare**: Identify discrepancies across datasets, saving CSV
    reports.
4.  **Export**: Generate Excel workbooks with user-defined sheets and
    layouts.

------------------------------------------------------------------------

## 4. Filters

Filters are declarative objects applied at pre-filter, post-filter,
compare, or export stages.

Supported operators: - `==, !=, >, >=, <, <=` - `in, not_in` -
`is_null, not_null` - `between`

Example:

``` json
{
  "AND": [
    { "submission_date": { "op": "between", "start": "2020-01-01", "end": "2021-01-01" } },
    { "status": { "op": "==", "value": "Active" } }
  ]
}
```

------------------------------------------------------------------------

## 5. Transforms

Transforms clean or normalize columns before compilation.

Available built-ins: - **regex_replace**: Remove or rewrite patterns in
text - **cast**: Convert type (`integer`, `number`, `string`,
`boolean`) - **titlecase**: Convert strings to Title Case

Example:

``` json
"Grant_ID": {
  "alias": "grant_id",
  "transforms": [
    { "regex_replace": { "pattern": "^jjc-", "repl": "", "flags": "i" } },
    { "cast": { "to": "integer", "on_cast_error": "coerce_null" } }
  ]
}
```

------------------------------------------------------------------------

## 6. Merge Rules

Controls how conflicting values across sources are resolved.

Strategies: - `"first_non_null"`: take the first non-null value across
inputs - `"prefer_source"`: choose value from a preferred table, with
optional fallbacks

Example:

``` json
"merge_rules": {
  "title": { "strategy": "first_non_null", "priority": ["excel_1_sheet_1","excel_1_sheet_2"] },
  "status": { "strategy": "prefer_source", "prefer_source": "excel_1_sheet_1", "fallback": ["excel_1_sheet_2"] }
}
```

------------------------------------------------------------------------

## 7. Compare

Define pairs of compiled datasets to reconcile.

``` json
"compare": {
  "pairs": [
    {
      "left": "excel_grants",
      "right": "access_grants",
      "on": ["grant_id"],
      "filter": { "status": { "op": "==", "value": "Active" } },
      "save_name": "excel_vs_access_active"
    }
  ]
}
```

Result: CSV with rows showing mismatches.

------------------------------------------------------------------------

## 8. Export

Exports data into Excel workbooks.

``` json
"export": {
  "workbooks": [
    {
      "save_name": "compiled_export",
      "sheets": [
        {
          "name": "Active Grants",
          "from": "excel_grants",
          "filter": { "status": { "op": "==", "value": "Active" } },
          "columns": {
            "Grant ID": { "alias": "grant_id" },
            "Title": { "alias": "title" },
            "PI": { "alias": "primary_investigator", "transforms": [ { "titlecase": {} } ] }
          }
        }
      ]
    }
  ]
}
```

------------------------------------------------------------------------

## 9. Logging

By default, logs are printed to stdout. Adjust verbosity with:

``` bash
export DATA_MANAGER_LOG_LEVEL=DEBUG
```

------------------------------------------------------------------------

## 10. Best Practices

-   **Always validate configs**: CI can run `jsonschema` validation to
    catch typos.
-   **Use environment variables for paths** (`${DATA_MANAGER_OUT}`) for
    portability.
-   **Explicitly define identifiers** in schema to avoid mismatched
    joins.
-   **Keep transforms small**: better readability and debuggability.
-   **Save reports**: compare outputs are essential for audits.

------------------------------------------------------------------------

## 11. Roadmap & Extensions

Future ideas: - More built-in transforms (trim, lower, upper, normalize
whitespace) - Built-in deduplication strategies - Integration with cloud
storage (S3, GCS) - Visualization of compare reports

------------------------------------------------------------------------

## 12. Support

-   Raise issues on the repository.
-   Contact maintainer for enhancements.

------------------------------------------------------------------------

Happy data managing! 🚀

# Computed Columns in Exports

This section documents the **computed column** feature for `data_manager` exports. It allows you to define new columns in an export workbook based on algebraic or logical expressions that reference other columns.

---

## Overview

In addition to mapping existing aliases or setting fixed values, you can now define a column as a **computed expression**. Expressions are written as a small JSON-based Abstract Syntax Tree (AST).

Each expression evaluates vectorized with pandas for performance and safety. No Python code or `eval` is executed from configs.

---

## Defining a Computed Column

In your `export.workbooks[*].sheets[*].columns` block, you can use three forms:

- **Alias** (existing column):  
  ```json
  "Grant Title": { "alias": "title" }
  ```

- **Constant value**:  
  ```json
  "Fixed Rate": { "value": 0.05 }
  ```

- **Computed expression**:  
  ```json
  "Total With Fee": {
    "compute": ["add", {"col": "grant_amount"}, ["mul", {"col": "grant_amount"}, {"col": "overhead_rate"}]]
  }
  ```

If both `alias` and `compute` are defined, `compute` takes precedence. If `value` is provided, it overrides both.

---

## Expression Syntax

### General form

An expression node can be:

- A primitive value (`number`, `string`, `boolean`, or `null`)
- A column reference: `{ "col": "field_name" }`
- An operation: `{ "op": "add", "args": [ <expr>, <expr>, ... ] }`
- A shorthand array: `["add", <expr>, <expr>, ...]`

### Supported Operations

**Arithmetic**  
- `add`: sum of arguments  
- `sub`: subtract two arguments  
- `mul`: multiply arguments  
- `div`: divide two arguments  
- `pow`: exponentiation  
- `neg`: negate a value  
- `abs`: absolute value  
- `round`: round to N decimals

**Comparison**  
- `eq`, `neq`, `gt`, `gte`, `lt`, `lte`

**Boolean**  
- `and`, `or`, `not`

**Null handling**  
- `coalesce`: return the first non-null among arguments  
- `fillna`: replace null with a value

**Strings**  
- `concat`: concatenate strings  
- `len`: string length

**Dates**  
- `strftime`: format a datetime with given pattern  
- `datediff`: difference between two datetimes (units: `day`, `hour`, `minute`)

**Misc**  
- `clip`: clip values between min and max  
- `percent`: apply a percentage (e.g., amount × rate)  
- `if`: conditional (`["if", <cond>, <then>, <else>]`)

---

## Examples

### Arithmetic with constants

```json
"Double Plus Five": {
  "compute": ["add", ["mul", 2, {"col": "grant_amount"}], 5]
}
```

→ For each row: `(2 × grant_amount) + 5`

### Overhead calculation

```json
"Overhead Amount": {
  "compute": ["mul", {"col": "grant_amount"}, {"col": "overhead_rate"}]
}
```

### Conditional logic

```json
"Active?": {
  "compute": ["if", ["eq", {"col": "status"}, "Active"], "Yes", "No"]
}
```

### Date calculations

```json
"Days Open": {
  "compute": ["datediff", "day", {"col": "close_date"}, {"col": "submission_date"}]
}
```

### String formatting

```json
"Pretty Date": {
  "compute": ["strftime", "%Y-%m-%d", {"col": "submission_date"}]
}
```

---

## Best Practices

- **Keep expressions small**: Nest only what you need for clarity.  
- **Use schema types**: Cast source columns to the right type (`date`, `integer`, etc.) at ingest.  
- **Handle nulls explicitly**: Use `coalesce` or `fillna` if nulls are expected.  
- **Validate configs**: CI should run configs through `jsonschema` and test one row for expression sanity.  
- **Auditability**: Every computed column is reproducible from config; avoid external code injection.

---

## Error Handling

- If a referenced column does not exist, an error is raised at export.  
- If an operator is unknown or arguments are missing, `ExprError` is raised.  
- For datetime operations, invalid values are coerced to `NA` instead of crashing.

---

This feature makes it possible to calculate new values (totals, percentages, conditional flags) directly in your JSON configuration, without custom Python code.

# Enrichment Mechanism

The **enrich** block extends the `compile.targets` functionality by allowing you to *augment* a compiled dataset with values pulled from another dataset (dimension table). This is particularly useful when you need to bring in codes, IDs, or reference attributes based on a key like organization name.

---

## Basic Structure

An `enrich` block is defined inside a compile target:

```json
{
  "name": "access_grants_enriched",
  "key": ["grant_id"],
  "inputs": ["grants_table"],
  "enrich": [
    {
      "from": "excel_external_orgs",
      "left_on": "sponsor_1_name",
      "right_on": "external_org_name",
      "add": { "sponsor_1_code": "external_org_code" }
    }
  ]
}
```

- **from**: dataset (compiled target or raw table) to join against  
- **left_on**: column in the current dataset  
- **right_on**: column in the enrichment dataset  
- **add**: mapping of `{ new_column: source_column }`

---

## Match Options

By default, enrich uses an **exact match** between `left_on` and `right_on`.  
For real-world messy data, you can specify a `match` block:

```json
"match": {
  "strategy": ["exact", "normalized", "fuzzy"],
  "normalize": ["strip", "lower", "collapse_ws", "strip_punct"],
  "fuzzy": {
    "scorer": "token_sort_ratio",
    "threshold": 90,
    "top_k": 1,
    "block": "first_char"
  },
  "on_miss": "leave_null",
  "audit": true
}
```

### Keys

- **strategy**: order of matching attempts (`exact` → `normalized` → `fuzzy`)  
- **normalize**: canonicalization steps applied to both sides before comparison  
- **fuzzy**: configuration for approximate matching  
  - **scorer**: similarity algorithm (`ratio`, `partial_ratio`, `token_sort_ratio`, `token_set_ratio`)  
  - **threshold**: minimum score (0–100) to accept a match  
  - **top_k**: how many candidates to consider (default: 1)  
  - **block**: restrict fuzzy candidates by a heuristic (e.g. `first_char`)  
- **on_miss**: what to do if no match found  
  - `leave_null`: leave blank  
  - `keep_source`: preserve original text  
  - `fail`: stop with an error  
- **audit**: if true, adds columns like `<col>_match_to`, `<col>_match_score`, `<col>_match_method` for QA

---

## Example: Enriching Org Codes

Suppose you have:

- `access_grants` with `sponsor_1_name`
- `excel_external_orgs` with `external_org_name` + `external_org_code`

Config:

```json
{
  "name": "access_grants_enriched",
  "key": ["grant_id"],
  "inputs": ["grants_table"],
  "enrich": [
    {
      "from": "excel_external_orgs",
      "left_on": "sponsor_1_name",
      "right_on": "external_org_name",
      "add": { "sponsor_1_code": "external_org_code" },
      "match": {
        "strategy": ["exact", "normalized", "fuzzy"],
        "normalize": ["strip","lower","collapse_ws","strip_punct"],
        "fuzzy": { "scorer": "token_sort_ratio", "threshold": 90 },
        "on_miss": "leave_null",
        "audit": true
      }
    }
  ]
}
```

During compilation, `sponsor_1_name` will be matched to `external_org_name`. If an exact match is not found, normalized forms are compared. If still not found, a fuzzy match is attempted. If matched, the corresponding `external_org_code` is pulled in as `sponsor_1_code`.

---

## Best Practices

1. **Pre-normalize sources**: Apply transforms (trim, lowercase, strip punctuation) at ingest for cleaner matching.  
2. **Keep dimensions unique**: Ensure the enrichment dataset has unique keys (`right_on`) before joining.  
3. **Audit**: Always enable `audit` when testing; review low-confidence matches.  
4. **Overrides**: Maintain a curated mapping table for edge cases; apply it as a transform before enrich.  
5. **Fail fast for critical joins**: Use `on_miss: fail` when enrichment is mandatory.  
6. **Performance**: Blocking (`first_char`, `first2`) speeds up fuzzy matches when enrichment dataset is large.

---

## Outputs

When `audit: true`, enrichment adds metadata columns:

- `<col>_match_to` → the value in the enrichment dataset chosen  
- `<col>_match_score` → similarity score (0–100)  
- `<col>_match_method` → which strategy was used (`exact`, `normalized`, `fuzzy`, `miss`)

These can be exported into workbooks for quality assurance.

---

With enrichment, you can declaratively connect datasets by codes and names, while handling imperfect data safely and transparently.

# Modular Configuration Loader

The configuration loader in **data_manager** has been enhanced to support **modular, layered, and reusable configurations**. This feature helps keep configuration files clean, maintainable, and production-ready.

---

## 1. Features

### Includes
- Any JSON config can include other files with the `include` key.
- Supports file paths and glob patterns.
- Example:
  ```json
  {
    "include": [
      "./schema.json",
      "./filters.json",
      "./sources/*.json",
      "./compile/*.json"
    ]
  }
  ```

### $ref (Reusable References)
- Any config block can reference another value by path.
- Syntax: `{ "$ref": "filters.active_only" }`
- Useful for reusing filters, transforms, and expressions across multiple places.

### Variables and Interpolation
- Environment variables and config keys can be interpolated inside strings.
- Example:
  ```json
  "output": "${DATA_MANAGER_OUT}/exports"
  ```
  - `${DATA_MANAGER_OUT}` → expands to environment variable.
  - `${paths.base}` → expands to another key in config.

### Profiles
- Profiles allow environment-specific overrides (e.g., `dev`, `prod`).
- Located under `config/profiles/`.
- Example:
  ```json
  {
    "sources": [
      { "id": "excel_doc_1", "path": "${paths.base}/dev/grants.xlsx" }
    ]
  }
  ```
- Activated with:
  ```bash
  data-manager run --config ./config/base.json --profile dev
  ```

### Modular File Structure
Recommended structure:
```
config/
├─ base.json
├─ schema.json
├─ filters.json
├─ macros.json
├─ sources/
│  ├─ access.main.json
│  ├─ excel.main.json
│  └─ inline.main.json
├─ compile/
│  └─ compile.json
├─ compare/
│  └─ pairs.json
├─ export/
│  └─ workbooks.json
└─ profiles/
   ├─ dev.json
   └─ prod.json
```

### Deep Merge Rules
- Objects are deep-merged (later overrides earlier).
- Arrays are replaced by default (not concatenated).
- Optional extensions can allow `{ "$append": [...] }` or `{ "$remove": [...] }`.

---

## 2. Workflow

1. Load the entry file (`base.json`).
2. Expand all `include`s (glob-friendly).
3. Resolve `$ref` references to other config paths.
4. Interpolate `${}` variables from env or config.
5. Merge in selected `profile` (if provided).
6. Validate against schema and semantic rules.
7. Pass resolved config to the pipeline.

---

## 3. Benefits

- **Readability**: smaller, focused JSON files.
- **Reusability**: filters, transforms, and expressions are defined once.
- **Portability**: environment and profile support for dev/prod.
- **Safety**: strict validation and friendly error messages.
- **Scalability**: supports large, complex projects without monolithic configs.

---

## 4. Example Run

```bash
DATA_MANAGER_OUT=./out data-manager run --config ./config/base.json --profile prod
```

Loader will:
1. Expand includes (`schema.json`, `filters.json`, `sources/*.json`, etc.).
2. Resolve all `$ref` and `${}` variables.
3. Apply `prod` profile overrides.
4. Provide a single resolved config for execution.

---

## 5. Best Practices

- Keep configs modular (one file per concern).
- Always reference reusable filters/expressions instead of duplicating them.
- Use `AND`/`OR` with `$ref` to extend filters.
- Parameterize paths and environment-specific values with `${}`.
- Store secrets in a separate git-ignored file (`secrets.local.json`).
- Validate configs in CI/CD.

---

This loader makes large, complex configuration files **manageable, maintainable, and production-grade**.

# User-Defined Functions (UDFs) in data_manager

The **data_manager** package supports extending its functionality with **user-defined functions (UDFs)**.  
This feature makes it possible to handle more complex or custom dataset logic in a **production-quality, safe, and reusable way**.

---

## 1. UDF Types

UDFs can plug into different stages of the pipeline:

- **Transforms**: applied to a single column (at source ingestion).
- **Compute expressions**: custom operators used inside `compute` blocks (export time).
- **Enrich**: DataFrame-wide enrichments, including cross-schema joins or inference.

---

## 2. Local vs. Packaged UDFs

You have two ways to use UDFs:

### a) Local (manual registration)
- Define UDFs in your project folder.
- Import and register them in the plugin registry:

```python
from my_udfs import normalize_org_transform

TRANSFORM_PLUGINS = {
    "normalize_org": normalize_org_transform,
}
```

- No packaging or installation required if UDFs live in the same repo.

### b) Packaged (production-grade, reusable)
- Package UDFs in their own repo with a `pyproject.toml`.
- Expose them via **entry points** so they are auto-discovered.

Example `pyproject.toml`:

```toml
[project]
name = "dm-extra-udfs"
version = "0.1.0"
dependencies = ["pandas>=2.1"]

[project.entry-points."data_manager.transforms"]
normalize_org = "dm_extra_udfs.org:normalize_org_transform"

[project.entry-points."data_manager.expr_ops"]
weighted_sum = "dm_extra_udfs.ops:weighted_sum"

[project.entry-points."data_manager.enrich"]
infer_irb_status = "dm_extra_udfs.irb:infer_irb_status"
```

Install into the same environment as `data_manager`:

```bash
pip install -e ../dm-extra-udfs
```

---

## 3. Interfaces

Each UDF must conform to a predictable function signature:

- **Transform**  
  ```python
  def my_transform(series: pd.Series, params: dict) -> pd.Series:
      ...
  ```

- **Expression Operator**  
  ```python
  def my_op(df: pd.DataFrame, *args) -> pd.Series:
      ...
  ```

- **Enrich Function**  
  ```python
  def my_enrich(df: pd.DataFrame, params: dict) -> pd.DataFrame:
      ...
  ```

---

## 4. Config Usage

### Transform UDF
```json
"columns": {
  "Org (normalized)": {
    "alias": "organization_name",
    "transforms": [
      { "normalize_org": { "drop_suffixes": ["inc", "llc", "corp"] } }
    ]
  }
}
```

### Compute UDF (Expression Operator)
```json
"columns": {
  "Score": {
    "compute": ["weighted_sum", {"col": "pubs"}, 0.5]
  }
}
```

### Enrich UDF
```json
"compile": {
  "targets": [
    {
      "name": "grants_enriched",
      "key": ["grant_id"],
      "inputs": ["grants_table"],
      "enrich": [
        { "fn": "infer_irb_status", "params": { "fallback_days": 90 } }
      ]
    }
  ]
}
```

---

## 5. Multi-Schema Access

- **Transforms**: only see a single column.  
- **Compute**: can reference any column in the current dataset.  
- **Enrich**: can access multiple DataFrames (both raw and compiled), making it the right place for cross-schema logic.

---

## 6. Best Practices

- Keep transforms **simple and vectorized**.  
- Use compute expressions for **row-level formulas**.  
- Use enrich for **cross-dataset joins or inference**.  
- Never embed raw Python in configs — only reference UDFs by name.  
- Test UDFs with sample DataFrames.  
- Log plugin names and versions for auditability.  
- Install both `data_manager` and UDF packages into the **same environment**.

---

## 7. Example Workflow

**Repo structure**:
```
data_manager/           # core package
dm-extra-udfs/          # separate UDF package
```

**requirements.txt**:
```
data-manager @ git+https://github.com/you/data_manager.git@v1.2
dm-extra-udfs @ git+https://github.com/you/dm_extra_udfs.git@v0.1
```

**Install**:
```bash
pip install -r requirements.txt
```

Now, `data_manager` will auto-discover the UDFs from `dm-extra-udfs`.

---

This makes UDFs in **data_manager** flexible, reusable, and production-ready.