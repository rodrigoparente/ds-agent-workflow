---
name: data-catalog
description: Reference guide for project data sources, tables, schemas, loading snippets, standard cleaning/deduplication rules, sample records, and relationships. Consult when exploring data, defining data inputs in specs, or writing data loading code.
---

# Data Catalog

> **Template Note:** The tables below (`lake.core.users`, `lake.media.user_images`) are **example placeholders**. Replace them with your project's actual tables, databases, or files using Section 3.

Index of project tables and datasets, loading recipes, schemas, sample rows, and entity relationships. Detailed schemas, sample rows, and loading snippets live in `assets/tables/<table_name>.md`.

---

## 1. Table Directory

| Table / Source | Description | Primary Key | Foreign / Join Keys | Details File |
|---|---|---|---|---|
| `lake.core.users` | Registered user profiles, account status, and timestamps | `user_id` | `country_code` | [assets/tables/users.md](assets/tables/users.md) |
| `lake.media.user_images` | User media assets, avatars, and approval statuses | `image_id` | `user_id` | [assets/tables/user_images.md](assets/tables/user_images.md) |

> Read `assets/tables/<table_name>.md` whenever a spec or task needs column types, schemas, or standard deduplication/cleanup rules.

---

## 2. Relationships & Common Joins

### `users` (1) ⟷ `user_images` (N)
- **Join Key:** `user_id` (one user may have zero or multiple images)
- **Pattern:** Filter active users (`is_active = TRUE`), left-join primary approved images (`is_primary = TRUE` and `is_deleted = FALSE` and `moderation_status = 'APPROVED'`) on `user_id`.

```sql
SELECT
    u.user_id,
    u.username,
    u.email,
    i.image_url AS avatar_url
FROM lake.core.users u
LEFT JOIN lake.media.user_images i
    ON u.user_id = i.user_id
    AND i.is_primary = TRUE
    AND i.is_deleted = FALSE
    AND i.moderation_status = 'APPROVED'
WHERE u.is_active = TRUE
```

---

## 3. Adding New Tables

1. Copy [assets/tables/template.md](assets/tables/template.md) to `assets/tables/<your_table_name>.md`.
2. Fill in the loading recipe (SQL, pandas, DuckDB, PySpark, etc.), schema, and sample rows.
3. Add a row to the **Table Directory** above.
