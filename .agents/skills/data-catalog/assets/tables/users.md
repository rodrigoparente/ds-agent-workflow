# Table: `lake.core.users`

**Description:** Central identity table containing registered user profiles, account statuses, and timestamps.

## PySpark Loading & Preprocessing Recipe
Applies deduplication on `user_id` (retaining the most recently updated record) and standardizes string fields and timestamps.

```python
from pyspark.sql import functions as F
from pyspark.sql.window import Window

# 1. Deduplication: keep the latest record per user_id
user_window = Window.partitionBy("user_id").orderBy(F.col("updated_at").desc_nulls_last())

# 2. Load, deduplicate, and standardize types
users_df = (
    spark.read.table("lake.core.users")
    .withColumn("row_num", F.row_number().over(user_window))
    .filter(F.col("row_num") == 1)
    .drop("row_num")
    .withColumn("email", F.lower(F.trim(F.col("email"))))
    .withColumn("username", F.trim(F.col("username")))
    .withColumn("created_at", F.to_timestamp(F.col("created_at")))
    .withColumn("is_active", F.coalesce(F.col("is_active"), F.lit(False)))
)
```

## Schema (`printSchema()`)
```
root
 |-- user_id: string (nullable = false)
 |-- username: string (nullable = true)
 |-- email: string (nullable = true)
 |-- status: string (nullable = true)
 |-- is_active: boolean (nullable = false)
 |-- country_code: string (nullable = true)
 |-- created_at: timestamp (nullable = true)
 |-- updated_at: timestamp (nullable = true)
```

## Sample Content (`show(truncate=False)`)
```
+------------------------------------+------------+----------------------+--------+---------+------------+-------------------+-------------------+
|user_id                             |username    |email                 |status  |is_active|country_code|created_at         |updated_at         |
+------------------------------------+------------+----------------------+--------+---------+------------+-------------------+-------------------+
|u_91a03e12-4f21-4f10-9b42-1200fa9101|alex_rivers |alex.rivers@email.com |VERIFIED|true     |US          |2025-01-15 10:14:02|2026-02-10 14:22:18|
|u_bc8411d9-76e2-41a4-9271-8840cd4190|sam_chen    |sam.chen@domain.io    |VERIFIED|true     |CA          |2025-03-22 08:30:45|2025-11-04 09:12:00|
|u_e14022a1-11c5-4a55-b482-aa01827419|jordan_m    |jordan99@webmail.org  |PENDING |false    |UK          |2026-01-02 18:45:10|2026-01-02 18:45:10|
+------------------------------------+------------+----------------------+--------+---------+------------+-------------------+-------------------+
```
