library(ggplot2)
library(maps)
library(rgdal)# R wrapper around GDAL/OGR
library(sp)
library(plyr)
# library(dplyr)
library(viridis)
library(scales)
require(RColorBrewer)
library(glue)
# library(ggpubr)
library(cowplot)
library(RPostgreSQL)
library(postGIStools)



library(rasterVis)

library(grid)
library(scales)
library(viridis)  # better colors for everyone
library(ggthemes) # theme_map()

user <- "mbougie"
host <- '144.92.235.105'
port <- '5432'
password <- 'Mend0ta!'

### Make the connection to database ######################################################################
con_synthesis <- dbConnect(PostgreSQL(), dbname = 'usxp_deliverables', user = user, host = host, port=port, password = password)




### Expansion:attach df to specific object in json #####################################################
bb = get_postgis_query(con_synthesis, "SELECT ST_Intersection(states.geom, bb.geom) as geom
                       FROM (SELECT st_transform(ST_MakeEnvelope(-111.144047, 36.585669, -79.748903, 48.760751, 4326),5070)as geom) as bb, spatial.states
                       WHERE ST_Intersects(states.geom, bb.geom) ",
                           geom_name = "geom")

bb.df <- fortify(bb)


### Expansion:attach df to specific object in json #####################################################
states = get_postgis_query(con_synthesis, "SELECT st_transform(geom,4326) as geom FROM spatial.states WHERE st_abbrev
                                           IN ('MT','MN','IA','ND','SD')",
                                                geom_name = "geom")

states.df <- fortify(states)


## Expansion:attach df to specific object in json #####################################################
region = get_postgis_query(con_synthesis, "SELECT st_transform(wkb_geometry,4326) as geom FROM waterfowl.tstorm_dissolved_5070",
                           geom_name = "geom")

region.df <- fortify(region)



### Expansion:attach df to specific object in json #####################################################
region = get_postgis_query(con_synthesis, "SELECT geom FROM waterfowl.waterfowl_wgs84",
                           geom_name = "geom")

region.df <- fortify(region)

# 
### Expansion:attach df to specific object in json #####################################################
states_large = get_postgis_query(con_synthesis, "SELECT st_transform(geom,4326) as geom FROM spatial.states",
                           geom_name = "geom")

states_large.df <- fortify(states_large)


### Expansion:attach df to specific object in json #####################################################
states = get_postgis_query(con_synthesis, "SELECT st_transform(geom,4326) as geom FROM spatial.states WHERE st_abbrev
                                           IN ('MT','IA','MN','ND','SD')",
                           geom_name = "geom")

states_region.df <- fortify(states)


################################################################
##### add the raster(s) datasets ###############################
################################################################

# fgdb = 'I:\\d_drive\\projects\\usxp\\series\\s35\\deliverables\\habitat_impacts\\milkweed\\data\\milkweed.gdb'
# mapa <- readOGR(dsn=fgdb,layer="milkweed_bs3km_region")
# 
# crs_wgs84 = CRS('+init=EPSG:4326')
# mapa <- spTransform(mapa, crs_wgs84)
# 
# #fortify() creates zany attributes so need to reattach the values from intial dataframe
# mapa.df <- fortify(mapa)
# 
# #creates a numeric index for each row in dataframe
# mapa@data$id <- rownames(mapa@data)
# 
# #merge the attributes of mapa@data to the fortified dataframe with id column
# mapa.df <- join(mapa.df, mapa@data, by="id")

#remove all rows with zero in it
##left side of the common is the row index and right side of the column is column index
# mapa.df = mapa.df[mapa.df$gridcode > 5000,]
# mapa.df$fill = cut(mapa.df$gridcode, breaks= c(0, 5000, 10000, 15000, 20000, 25000, 10000000))
# 
# table(mapa.df$fill)



####################################################################################################################
########raster stuff##############################################################################################
###############################################################################################################################


####good trick is to load a raster with null values and then replace nulls with a value (replaced null with zero in this case)
setwd('I:\\d_drive\\projects\\usxp\\series\\s35\\deliverables\\habitat_impacts\\waterfowl\\data\\tif')
r = raster('s35_waterfowl_bs3km.tif')

unique(r)

r[is.na(r)] <- 0

unique(r)

# ###repoject to wgs84
crs_wgs84 = CRS('+init=EPSG:4326')
r <- projectRaster(r, crs=crs_wgs84)

### convert the raster to SPDF
r_spdf <- as(r, "SpatialPixelsDataFrame")



###make the SPDF to a regular dataframe
r_df <- as.data.frame(r_spdf)


###convert value column to integer
r_df$value <- as.integer(r_df$value)

# ###remove all records with zero in it
# row_sub = apply(r_df, 1, function(row) all(row !=0 ))
# r_df <- r_df[row_sub,]

####add columns to the dataframe
colnames(r_df) <- c("value", "x", "y")


#### stats
## get the counts per bin
table(r_df$value)




##########################################################################
#### graphics############################################################
##########################################################################


ggplot() + 
  ### state boundary background ###########
### state boundary background ###########
geom_polygon(
  data=states_large.df,
  aes(x=long,y=lat,group=group),
  # fill='#D0D0D0') +
  fill='#D3D3D3') +
#   
  ### state boundary strokes ###########
geom_polygon(
  data=states_large.df,
  aes(y=lat, x=long, group=group),
  alpha=0,
  colour='grey',
  size=6
) +
  ### state boundary background ###########
  # geom_polygon(
  # data=states.df,
  # aes(x=long,y=lat,group=group),
  # # fill='#D0D0D0') +
  # fill='#808080') +

###focus datset
geom_tile(
  data=r_df,
  #### using alpha greatly increases the render time!!!!  --avoid if when possible
  # alpha=0.8,
  aes(x=x, y=y,fill=value)
) +

  ### state boundary background ###########
geom_polygon(
  data=region.df,
  aes(x=long,y=lat,group=group),
  fill='red') +
  
  
  ### state boundary background ###########
geom_polygon(
  data=states_region.df,
  aes(x=long,y=lat,group=group),
  # fill='#D0D0D0') +
  fill='#808080') +
  
  
  ### state boundary strokes ###########
geom_polygon(
  data=states_region.df,
  aes(y=lat, x=long, group=group),
  alpha=0,
  colour='white',
  size=2
) +


  # Equal scale cartesian coordinates 
# coord_equal() 
#   
# coord_map(project="polyconic")
coord_map(project="polyconic", xlim = c(-114,-90),ylim = c(39, 50)) +


  #### add title to map #######
labs(title = '',  
     caption = '0          5           10         15          20          25') + 
  
  
  
  theme(
    #### nulled attributes ##################
    axis.text.x = element_blank(),
    axis.title.x=element_blank(),
    axis.text.y = element_blank(),
    axis.title.y=element_blank(),
    axis.ticks = element_blank(),
    axis.line = element_blank(),
    
    panel.background = element_rect(fill = NA, color = NA),
    panel.grid.major = element_blank(),
    
    plot.background = element_rect(fill = NA, color = NA),
    plot.margin = unit(c(0, 0, 0, 0), "cm"),
    
    #### modified attributes ########################
    ##parameters for the map title
    plot.title = element_text(size= 55, vjust=-12.0, hjust=0.108, color = "#4e4d47"),
    ##shifts the entire legend (graphic AND labels)
    legend.text = element_text(color='white', size=0),
    
    legend.position = c(0.06, 0.06),   ####h,V
    plot.caption = element_text(size= 35, vjust=25, hjust=0.08, color = "#4e4d47")###title size/position/color
   
    
     # text = element_text(color = "#4e4d47", size=30)  ##these are the legend numeric values
  ) +


  ###this is modifying the specifics of INSIDE the legend (i.e. the legends components that make up the legend)
  ### create a discrete scale. These functions allow you to specify your own set of mappings from levels in the data to aesthetic values.
  
  scale_fill_gradient(
  # scale_fill_manual(
                    # values = brewer.pal(6, 'Oranges'),
                    values = c('red'),
                    ###legend labels
                    

                    #Legend type guide shows key (i.e., geoms) mapped onto values.
                    guide = guide_legend( title='Milkweeds Lost (stems(thousands)/10,000 acres)',
                                          title.theme = element_text(
                                            size = 32,
                                            color = "#4e4d47",
                                            vjust=0.0,
                                            angle = 0
                                          ),
                                          # legend bin dimensions
                                          keyheight = unit(8, units = "mm"),
                                          keywidth = unit(35, units = "mm"),
                                          
                                          # #legend elements position
                                          # label.position = "bottom",
                                          # title.position = 'top',
                                          
                                          #The desired number of rows of legends.
                                          nrow=1
                                          
                    )
  )
  
  
  

  # coord_equal() +
  # theme_map() +
  # theme(legend.position="bottom") +
  # theme(legend.key.width=unit(2, "cm"))



fileout = 'I:\\d_drive\\projects\\usxp\\series\\s35\\deliverables\\habitat_impacts\\waterfowl\\deliverables\\test.png'
ggsave(fileout, width = 34, height = 25, dpi = 500)
