﻿----OLD --- Query returned successfully: 11007989 rows affected, 1590061 ms execution time.
-----Query returned successfully: 10778051 rows affected, 2680560 ms execution time.


CREATE TABLE v3_3.block_group_final_union as 

--EXPLAIN

SELECT * FROM v3_3.block_group_final_core

UNION

SELECT * FROM v3_3.block_group_final_water

UNION

SELECT * FROM v3_3.block_group_final_nwalt21_refined

UNION

SELECT * FROM v3_3.block_group_final_nwalt21_unrefined

UNION

SELECT * FROM v3_3.block_group_final_conservation;



------create indexes after table is created-------------------------------------------
---create index using geoid column
CREATE INDEX v3_3_block_group_final_union_geoid_idx ON v3_3.block_group_final_union (geoid);

---create index using geom column
CREATE INDEX v3_3_block_group_final_union_geom_idx ON v3_3.block_group_final_union USING gist (geom);





-----QAQC--------------------------------------------------
----create primary key
ALTER TABLE v3_3.block_group_final_union
  ADD CONSTRAINT block_group_final_union_pkey PRIMARY KEY(geoid);