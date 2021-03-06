﻿

-------------  create the road buffer by couty --------------------------------------------------- 


-- Clip all lines (roads) by counties (here we assume counties geom are POLYGON or MULTIPOLYGONS)
-- NOTE: we are only keeping intersections that result in a LINESTRING or MULTILINESTRING because we don't
-- care about roads that just share a point
-- the dump is needed to expand a geometry collection into individual single MULT* parts
-- the below is fairly generic and will work for polys, etc. by just changing the where clause


-- Query returned successfully: one row affected, 545014 ms execution time.
-- Query returned successfully: one row affected, 148772 ms execution time.

create table test.roads_buff25_wyoming as 

SELECT clipped.atlas_name, ST_Buffer(ST_Union(ST_SnapToGrid(clipped_geom,0.0001)),25) as geom
FROM 
(SELECT counties.atlas_name, (ST_Dump(ST_Intersection(counties.wkb_geometry, roads.wkb_geometry))).geom As clipped_geom
FROM spatial.states_102003 as counties
INNER JOIN refine.region_roads_102003 as roads
ON ST_Intersects(counties.wkb_geometry, roads.wkb_geometry)
)  As clipped

WHERE ST_Dimension(clipped.clipped_geom) = 1 and clipped.atlas_name = 'Wyoming'
GROUP BY clipped.atlas_name;


ALTER TABLE test.clip_19073 ALTER COLUMN geom TYPE geometry(MultiLineString,102003) USING ST_SetSRID(geom,102003);


---------- erase layer by buffer -----------------------------------------------------------------------
/*
create table test.erase_19073 as 
SELECT ST_Difference(a.wkb_geometry, b.geom) as geom
FROM spatial.states_102003 as a, test.clip_19073 as b
WHERE a.wkb_geometry && b.geom AND a.atlas_name = '19073'
*/