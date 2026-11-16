# Table: `<catalog>.<schema>.<table>`

**Description:** <Brief description of the table, entity, and business context>

## PySpark Loading & Preprocessing Recipe
```python
from pyspark.sql import functions as F

<table>_df = (
    spark.read.table("<catalog>.<schema>.<table>")
    # 1. Deduplication or filtering
    # 2. Type casting or string cleaning
)
```

## Schema (`printSchema()`)
```
root
 |-- id: string (nullable = false)
 |-- ...
```

## Sample Content (`show(truncate=False)`)
```
+---+---+
|...|...|
+---+---+
```
