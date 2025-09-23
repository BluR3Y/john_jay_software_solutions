from __future__ import annotations

def apply_aliases(df, colmap: dict[str, dict]) :
    alias_map = {}
    for raw, cfg in (colmap or {}).items():
        alias = cfg.get("alias")
        if alias:
            alias_map[raw] = alias
    if alias_map:
        df = df.rename(columns=alias_map)
    return df
