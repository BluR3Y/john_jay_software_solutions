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
