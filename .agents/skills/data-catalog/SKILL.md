---
name: data-catalog
description: Reference guide for data lake tables, PySpark loading snippets, standard cleaning and deduplication transformations, schemas, sample records, and table relationships. Consult when exploring data, defining data inputs in specs, or writing PySpark data loading code.
---

# Data Lake Catalog

Index of available data lake tables, PySpark loading recipes, schemas, sample data, and entity relationships. Detailed schemas (`printSchema()`), sample rows (`show(truncate=False)`), and loading functions live in `assets/tables/<table_name>.md`.

---

## 1. Table Directory

| Table Name | Description | Primary Key | Foreign / Join Keys | Details File |
|---|---|---|---|---|
| `lake.core.users` | Registered user profiles, account status, and timestamps | `user_id` | `country_code` | [assets/tables/users.md](assets/tables/users.md) |
| `lake.media.user_images` | User media assets, avatars, and approval statuses | `image_id` | `user_id` | [assets/tables/user_images.md](assets/tables/user_images.md) |

> Read `assets/tables/<table_name>.md` whenever a spec or task needs column types, schemas, or standard deduplication/cleanup rules.

---

## 2. Table Relationships & Recommended Joins

### `users` (1) ⟷ `user_images` (N)
- **Join Key:** `user_id` (one user may have zero or multiple images)
- **Common Pattern:** Joining active users with their primary avatar image:

```python
from pyspark.sql import functions as F

user_profiles_df = (
    users_df.filter(F.col("is_active") == True)
    .join(images_df.filter(F.col("is_primary") == True), on="user_id", how="left")
    .select(
        users_df["user_id"],
        users_df["username"],
        users_df["email"],
        images_df["image_url"].alias("avatar_url"),
    )
)
```

---

## 3. Adding New Tables

1. Copy [assets/tables/template.md](assets/tables/template.md) to `assets/tables/<your_table_name>.md`.
2. Fill in the PySpark loading recipe, `printSchema()`, and sample rows.
3. Add a row to the **Table Directory** above.
