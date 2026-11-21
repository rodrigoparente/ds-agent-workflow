# Table: `<source_or_table_name>`

**Description:** <Brief description of the table/dataset, grain, and business context>

## Loading & Preprocessing Recipe
Document the standard query or loading snippet (SQL, pandas, DuckDB, PySpark, etc.), deduplication, and type/filter defaults:

```sql
SELECT
    *
FROM <source_or_table_name>
-- 1. Deduplication or filtering
-- 2. Type casting or string cleaning
```

## Schema
```text
- id: string (not null)
- ...
```

## Sample Content
```text
+---+---+
|...|...|
+---+---+
```
