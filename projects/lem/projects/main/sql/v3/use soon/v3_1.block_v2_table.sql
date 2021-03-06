﻿CREATE TABLE v3_1.block_v2_main AS 
 SELECT main.geoid,
    LEFT(main.geoid,12) as block_group,
    st_area(main.wkb_geometry) * 0.0001::double precision AS hectares,
    --neighbors.neighbor_list,
    nwalt.majority AS nwalt,
    nwalt_rc.majority AS nwalt_rc,
    biomes.majority AS biomes,
    st_x(st_transform(st_centroid(main.wkb_geometry), 4152)) AS lng,
    st_y(st_transform(st_centroid(main.wkb_geometry), 4152)) AS lat,
    main.wkb_geometry AS geom
  FROM v3_1.block main
   --------------------------------------------------------------------------------
   --- derive neighbors column-----------------------------------------------------
   --------------------------------------------------------------------------------
/*
     JOIN ( SELECT a.src_geoid,
            string_agg(a.nbr_geoid, ', '::text) AS neighbor_list
           FROM v3_1.block_neighbors a
          WHERE a.length <> 0::double precision
          GROUP BY a.src_geoid) neighbors ON main.geoid::text = neighbors.src_geoid
*/
    -------------------------------------------------------------------------------
    --- derive majority column-----------------------------------------------------
    -------------------------------------------------------------------------------
/*
     JOIN ( SELECT block_zonal_maj_rc_nwalt.geoid,
             block_zonal_maj_rc_nwalt.majority
            FROM 
             v3_1.block_zonal_maj_rc_nwalt
            WHERE NOT (block_zonal_maj_rc_nwalt.geoid IN ( SELECT block_zonal_maj_nwalt.geoid
                                                         FROM v3_1.block_zonal_maj_nwalt
                                                         WHERE block_zonal_maj_nwalt.majority = 11))
	   UNION
	  
	   SELECT block_zonal_maj_nwalt.geoid,
	    nwalt_lookup.grouped AS majority
	   FROM v3_1.block_zonal_maj_nwalt,
	    nwalt_lookup
	   WHERE block_zonal_maj_nwalt.majority = nwalt_lookup.initial AND block_zonal_maj_nwalt.majority = 11) AS hybrid ON hybrid.geoid = main.geoid::text
*/
    ---------------------------------------------------------------------------------
    --- QAQC constrain records to maintain Foreign Key constaints--------------------
    ---------------------------------------------------------------------------------    
/*
    JOIN (SELECT 
	  block_group.geoid
	FROM 
	  v3_1.block_group, 
	(SELECT 
	left(block.geoid,12) as grouped_geoid
	FROM 
	v3_1.block
	group by 
	left(block.geoid,12)) as blocks
	WHERE 
	  block_group.geoid = blocks.grouped_geoid) as qaqc ON qaqc.geoid = LEFT(main.geoid,12)
*/

    ---join nwalt dataset
    LEFT JOIN v3_1.block_zonal_maj_nwalt as nwalt ON main.geoid::text = nwalt.geoid

    ---join rc_nwalt dataset
    LEFT JOIN v3_1.block_zonal_maj_nwalt_rc as nwalt_rc ON main.geoid::text = nwalt_rc.geoid

    ---join biomes dataset
    LEFT JOIN v3_1.block_zonal_maj_biomes as biomes ON main.geoid::text = biomes.geoid;


---create index using geoid column
CREATE INDEX v3_1_block_v2_main_geoid_idx ON v3_1.block_v2_main (geoid);




