# Table: `lake.core.users`

**Description:** Central identity table containing registered user profiles, account statuses, and timestamps.

## Loading & Preprocessing Recipe
Deduplicates on `user_id` (keeping the latest `updated_at`) and standardizes emails, usernames, booleans, and timestamps:

```sql
WITH ranked AS (
    SELECT
        *,
        ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY updated_at DESC NULLS LAST) AS row_num
    FROM lake.core.users
)
SELECT
    user_id,
    TRIM(username) AS username,
    LOWER(TRIM(email)) AS email,
    status,
    COALESCE(is_active, FALSE) AS is_active,
    country_code,
    CAST(created_at AS TIMESTAMP) AS created_at,
    CAST(updated_at AS TIMESTAMP) AS updated_at
FROM ranked
WHERE row_num = 1
```

## Schema
```text
- user_id: string (not null)
- username: string (nullable)
- email: string (nullable)
- status: string (nullable)
- is_active: boolean (not null)
- country_code: string (nullable)
- created_at: timestamp (nullable)
- updated_at: timestamp (nullable)
```

## Sample Content
```text
+------------------------------------+------------+----------------------+--------+---------+------------+-------------------+-------------------+
|user_id                             |username    |email                 |status  |is_active|country_code|created_at         |updated_at         |
+------------------------------------+------------+----------------------+--------+---------+------------+-------------------+-------------------+
|u_91a03e12-4f21-4f10-9b42-1200fa9101|alex_rivers |alex.rivers@email.com |VERIFIED|true     |US          |2025-01-15 10:14:02|2026-02-10 14:22:18|
|u_bc8411d9-76e2-41a4-9271-8840cd4190|sam_chen    |sam.chen@domain.io    |VERIFIED|true     |CA          |2025-03-22 08:30:45|2025-11-04 09:12:00|
|u_e14022a1-11c5-4a55-b482-aa01827419|jordan_m    |jordan99@webmail.org  |PENDING |false    |UK          |2026-01-02 18:45:10|2026-01-02 18:45:10|
+------------------------------------+------------+----------------------+--------+---------+------------+-------------------+-------------------+
```
