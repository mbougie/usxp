﻿------Query returned successfully with no result in 160975 ms.

CREATE TABLE v3_3.block_group_main AS
SELECT
    main.objectid, 
    main.geoid,
    LEFT(main.geoid,12) as tract,
    st_area(main.wkb_geometry) * 0.0001::double precision AS hectares,
    neighbors.neighbor_list,
    nwalt.majority AS nwalt,
    nwalt_rc.majority AS nwalt_rc,
    biomes.majority AS biomes,
    st_x(st_transform(st_centroid(main.wkb_geometry), 4152)) AS lng,
    st_y(st_transform(st_centroid(main.wkb_geometry), 4152)) AS lat,
    main.wkb_geometry AS geom
FROM v3_core.block_group AS main

-----join nbrlist table
LEFT JOIN v3_3.block_group_nbrlist as neighbors ON main.geoid = neighbors.geoid

---join nwalt table
LEFT JOIN v3_core.block_group_zonal_maj_nwalt_60m as nwalt ON main.geoid = nwalt.geoid

---join rc_nwalt table
LEFT JOIN v3_core.block_group_zonal_maj_nwalt_rc_v2_60m as nwalt_rc ON main.geoid = nwalt_rc.geoid

---join biomes table
LEFT JOIN v3_core.block_group_zonal_maj_biomes_60m as biomes ON main.geoid = biomes.geoid;



------create indexes after table is created-------------------------------------------
---create index using geoid column
CREATE INDEX v3_3_block_group_main_geoid_idx ON v3_3.block_group_main (geoid);

---create index using geom column
CREATE INDEX v3_3_block_group_main_geom_idx ON v3_3.block_group_main USING gist (geom);