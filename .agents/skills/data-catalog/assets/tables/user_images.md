# Table: `lake.media.user_images`

**Description:** Media assets associated with user profiles and uploads.

## PySpark Loading & Preprocessing Recipe
Filters out soft-deleted or unapproved images, casts dimensions, and normalizes URLs.

```python
from pyspark.sql import functions as F

# Filter deleted/unapproved media and normalize URLs & dimensions
images_df = (
    spark.read.table("lake.media.user_images")
    .filter((F.col("is_deleted") == False) & (F.col("moderation_status") == "APPROVED"))
    .withColumn("image_url", F.trim(F.col("image_url")))
    .withColumn("width_px", F.col("width_px").cast("integer"))
    .withColumn("height_px", F.col("height_px").cast("integer"))
    .withColumn("is_primary", F.coalesce(F.col("is_primary"), F.lit(False)))
    .withColumn("uploaded_at", F.to_timestamp(F.col("uploaded_at")))
)
```

## Schema (`printSchema()`)
```
root
 |-- image_id: string (nullable = false)
 |-- user_id: string (nullable = false)
 |-- image_url: string (nullable = true)
 |-- image_type: string (nullable = true)
 |-- width_px: integer (nullable = true)
 |-- height_px: integer (nullable = true)
 |-- is_primary: boolean (nullable = false)
 |-- moderation_status: string (nullable = true)
 |-- is_deleted: boolean (nullable = false)
 |-- uploaded_at: timestamp (nullable = true)
```

## Sample Content (`show(truncate=False)`)
```
+------------------------------------+------------------------------------+---------------------------------------------+----------+--------+---------+----------+-----------------+----------+-------------------+
|image_id                            |user_id                             |image_url                                    |image_type|width_px|height_px|is_primary|moderation_status|is_deleted|uploaded_at        |
+------------------------------------+------------------------------------+---------------------------------------------+----------+--------+---------+----------+-----------------+----------+-------------------+
|img_0102aa-99b8-410a-8501-11a28cb019|u_91a03e12-4f21-4f10-9b42-1200fa9101|https://cdn.example.com/media/alex_avatar.jpg |AVATAR    |1024    |1024     |true      |APPROVED         |false     |2025-01-15 10:20:00|
|img_0884cc-33d1-441f-a201-9011be1821|u_91a03e12-4f21-4f10-9b42-1200fa9101|https://cdn.example.com/media/alex_banner.png |BANNER    |1920    |1080     |false     |APPROVED         |false     |2025-02-01 16:04:12|
|img_7719bb-22e4-44b2-b112-aa7710cc88|u_bc8411d9-76e2-41a4-9271-8840cd4190|https://cdn.example.com/media/sam_profile.jpg|AVATAR    |800     |800      |true      |APPROVED         |false     |2025-03-22 08:35:10|
+------------------------------------+------------------------------------+---------------------------------------------+----------+--------+---------+----------+-----------------+----------+-------------------+
```
