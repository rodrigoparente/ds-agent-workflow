---
name: data-catalog
description: Reference guide for data lake tables, PySpark loading snippets, standard cleaning and deduplication transformations, schemas, sample records, and table relationships. Consult when exploring data, defining data inputs in specs, or writing PySpark data loading code.
---

# Data Lake Catalog

This skill provides the index of available tables in the data lake, standard PySpark loading recipes, schemas, sample data, and entity relationships.

To keep this skill fast and scalable across dozens of large tables, detailed schemas (`printSchema()`), sample outputs (`show(truncate=False)`), and loading functions are stored in individual files under `assets/tables/`.

---

## 1. Table Directory

| Table Name | Description | Primary Key | Foreign / Join Keys | Details File |
|---|---|---|---|---|
| `lake.core.users` | Registered user profiles, account status, and timestamps | `user_id` | `country_code` | [assets/tables/users.md](assets/tables/users.md) |
| `lake.media.user_images` | User media assets, avatars, and approval statuses | `image_id` | `user_id` | [assets/tables/user_images.md](assets/tables/user_images.md) |

> **Consulting Table Details:** When a spec or task requires specific columns, data types, or standard deduplication/cleanup logic for a table, read its corresponding file in `assets/tables/<table_name>.md`.

---

## 2. Table Relationships & Recommended Joins

### `users` (1) ⟷ `user_images` (N)
- **Join Key:** `user_id`
- **Relationship:** One user may have zero or multiple images.
- **Common Pattern:** Joining active users with their primary avatar image:

```python
from pyspark.sql import functions as F

# Example: Get active users with their primary avatar
user_profiles_df = (
    users_df.filter(F.col("is_active") == True)
    .join(
        images_df.filter(F.col("is_primary") == True),
        on="user_id",
        how="left"
    )
    .select(
        users_df["user_id"],
        users_df["username"],
        users_df["email"],
        images_df["image_url"].alias("avatar_url")
    )
)
```

---

## 3. How to Use in Specs

When drafting a spec in `experiment-spec`:
1. Check the Table Directory above to find the relevant tables.
2. If column-level schemas, deduplication rules, or cleaning steps are needed, read the table's detail file in `assets/tables/<table_name>.md`.
3. In the spec's `## Data & Inputs` section, explicitly describe the data sources, deduplication, filters, and join logic agreed upon.
4. Once written into the spec, subsequent code implementation follows the spec directly.

---

## 4. Adding New Tables

To add your own tables to this catalog:
1. Copy [assets/tables/template.md](assets/tables/template.md) to `assets/tables/<your_table_name>.md`.
2. Fill in your table's PySpark loading recipe, `printSchema()`, and sample rows.
3. Add a row to the **Table Directory** table above.
