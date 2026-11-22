# Table: `lake.media.user_images`

**Description:** Media assets associated with user profiles and uploads.

## Loading & Preprocessing Recipe
Filters out soft-deleted or unapproved images, casts dimensions, and normalizes URLs:

```sql
SELECT
    image_id,
    user_id,
    TRIM(image_url) AS image_url,
    image_type,
    CAST(width_px AS INTEGER) AS width_px,
    CAST(height_px AS INTEGER) AS height_px,
    COALESCE(is_primary, FALSE) AS is_primary,
    moderation_status,
    is_deleted,
    CAST(uploaded_at AS TIMESTAMP) AS uploaded_at
FROM lake.media.user_images
WHERE is_deleted = FALSE
  AND moderation_status = 'APPROVED'
```

## Schema
```text
- image_id: string (not null)
- user_id: string (not null)
- image_url: string (nullable)
- image_type: string (nullable)
- width_px: integer (nullable)
- height_px: integer (nullable)
- is_primary: boolean (not null)
- moderation_status: string (nullable)
- is_deleted: boolean (not null)
- uploaded_at: timestamp (nullable)
```

## Sample Content
```text
+------------------------------------+------------------------------------+---------------------------------------------+----------+--------+---------+----------+-----------------+----------+-------------------+
|image_id                            |user_id                             |image_url                                    |image_type|width_px|height_px|is_primary|moderation_status|is_deleted|uploaded_at        |
+------------------------------------+------------------------------------+---------------------------------------------+----------+--------+---------+----------+-----------------+----------+-------------------+
|img_0102aa-99b8-410a-8501-11a28cb019|u_91a03e12-4f21-4f10-9b42-1200fa9101|https://cdn.example.com/media/alex_avatar.jpg |AVATAR    |1024    |1024     |true      |APPROVED         |false     |2025-01-15 10:20:00|
|img_0884cc-33d1-441f-a201-9011be1821|u_91a03e12-4f21-4f10-9b42-1200fa9101|https://cdn.example.com/media/alex_banner.png |BANNER    |1920    |1080     |false     |APPROVED         |false     |2025-02-01 16:04:12|
|img_7719bb-22e4-44b2-b112-aa7710cc88|u_bc8411d9-76e2-41a4-9271-8840cd4190|https://cdn.example.com/media/sam_profile.jpg|AVATAR    |800     |800      |true      |APPROVED         |false     |2025-03-22 08:35:10|
+------------------------------------+------------------------------------+---------------------------------------------+----------+--------+---------+----------+-----------------+----------+-------------------+
```
