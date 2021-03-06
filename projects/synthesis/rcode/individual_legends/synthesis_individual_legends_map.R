#################### temp #######################################################

createMap <- function(df, obj, figure_params, title){
  
  #### get datasets######################
  
  state.df <- readOGR(dsn = "H:\\new_data_8_18_19\\e_drive\\data\\general\\sf", layer = "states")
  
  
  
  
  ### dimensions of the legend bins ###
  keywidth = figure_params$keywidth
  keyheight = figure_params$keyheight
  
  ### gap between legend bins ###
  gap = figure_params$gap
  
  
  ### get the spatial dtaframe that is stored in the object
  mapa <- df
  
  
  
  
  ########################################################################
  ##### modify dataframes #####################################
  ########################################################################
  
  #fortify() creates zany attributes so need to reattach the values from intial dataframe
  mapa.df <- fortify(mapa)
  
  #creates a numeric index for each row in dataframe
  mapa@data$id <- rownames(mapa@data)
  
  #merge the attributes of mapa@data to the fortified dataframe with id column
  mapa.df <- join(mapa.df, mapa@data, by="id")
  
  
  
  hist(mapa.df$current_field, 100)
  
  ###create new fill column with cut values returned from getFillValues() function
  # mapa.df$fill = getFillValues()
  
  
  
  
  
  
  #####create bin_breaks ################################################
  breaks_coef = obj$bin_params$coef
  breaks_lower_count = obj$bin_params$lower$count
  breaks_coef = obj$bin_params$coef
  kernel = obj$bin_params$kernel
  
  
  createScaledVector <- function(kernel, count, inf, upper_lower) {
    i = 1
    temp_vector <- c(kernel)
    while(i < count){
      print('-----temp_vector----------')
      print(temp_vector)
      x = temp_vector[i] * obj$bin_params$coef
      print('--------------x--------------')
      print(x)
      print('--------------i--------------')
      print(i)
      if((i == (count-1)) & (inf=='true') & (upper_lower==-1) ){
        temp_vector <- c(temp_vector, -1e300)
      }
      else if((i == (count-1)) & (inf=='true') & (upper_lower==1) ){
        temp_vector <- c(temp_vector, 1e300)
      }
      else{
        temp_vector <- c(temp_vector, x)
      }
      i = i + 1
    }
    return(temp_vector)
  }
  
  vector_low = createScaledVector((-1*kernel), obj$bin_params$lower$count, obj$bin_params$lower$inf, upper_lower=-1)
  vector_high = createScaledVector((1*kernel), obj$bin_params$upper$count, obj$bin_params$upper$inf, upper_lower=1)
  
  bin_breaks <-c(sort(vector_low), c(0), vector_high)
  print(bin_breaks)
  
  ##### create bin_breaks(end) ################################################
  
  
  ##### arguments for the labels #########################
  # replace lower infinity
  labels = replace(bin_breaks, bin_breaks==-1e+300, paste(obj$bin_params$coef*(nth(bin_breaks, 2)), "+", sep=""))
  print(labels)
  # replace upper infinity
  labels = replace(labels, labels==1e+300, paste(obj$bin_params$coef*(nth(bin_breaks, -2)), "+", sep=""))
  print(labels)
  
  
  
  mapa.df$fill = cut(mapa.df$current_field, breaks= bin_breaks)
  table(mapa.df$fill)
  
  
  #####create stuff for the legend here (abstract this into a fct soon)
  ####get the raw breaks in legend
  # raw_breaks = bin_breaks
  print('bin_breaks')
  
  
  
  ##### arguments for the graphics #########################
  number_of_breaks = length(bin_breaks)
  print('----------number_of_breaks--------------')
  print(number_of_breaks)
  
  legend_length = (keywidth * (number_of_breaks)) + (gap*(number_of_breaks-4))
  print('---------legend_length-----------')
  print(legend_length)
  
  ####get the location of where the legend start postion is
  start_legend = (1 - (legend_length))/2
  print('===================start_legend=============================')
  print(start_legend)
  
  
  
  
  
  
  
  ###get the number of labels
  number_of_labels = length(labels)
  print('---------number_of_labels-----------')
  print(number_of_labels)
  
  
  
  
  
  
  
  
  
  
  ###get the number of gaps between the labels 
  gap_count = number_of_labels-1
  print('---------gap_count-----------')
  print(gap_count) 
  
  ###get the total label length
  label_length = keywidth * gap_count
  print('--------label_length-----------')
  print(label_length)
  
  
  ### add keywidth plus a full gap (need to account for gap on both sides?!?)
  # start_label = start_legend + keywidth + gap
  start_label = start_legend
  print('---------------start_label------------------')
  print(start_label)
  
  
  
  
  
  
  
  
  
  
  
  ####################################################################
  
  
  
  #### function to get legend range vector for color pallette that is derived from breaks vector in json
  
  getLegendRange <- function(breaks){
    v <- 1:10
    print(v)
    print(breaks)
    print('-------------------------')
    
    
    
    print(sum(breaks < 0))
    ### for negative values
    total = 5 - (sum(breaks < 0))
    print(total)
    if(total != 0){v <- head(v, -total)}
    print(total)
    print(v)
    
    
    
    
    #### for postive values
    total = 5 - (sum(breaks > 0))
    if(total != 0){v <- v[!v %in% 1:total]}
    
    print('-------------------------')
    print(v)
  }
  
  
  legendLabelCreator <- function(start_label, number_of_breaks, labels){
    
    ###declare the empty list that will hold all the ggplot objects
    ggplot_object_list <- list()
    
    
    # ###### how much the location changes each iteration
    # multiplier = keywidth + gap
    # ####the limit defines the distance the 
    # limit = start_label + (multiplier * (number_of_breaks-2))
    # print('limit:-----------')
    # print(limit)
    
    i = 1
    while (i <= number_of_labels) {
      print('start_label---------------')
      print(start_label)
      
      ####create the grob-object
      ggplot_object = annotation_custom(grobTree(textGrob(labels[i], x=start_label, y= -0.06, just="left", rot = -45,gp=gpar(col="#4e4d47", fontsize=45, fontface="bold"))))
      
      ####append the grob-object to the ggplot_object_list
      ggplot_object_list <- append(ggplot_object_list, list(ggplot_object))
      
      ### add the keywidth and gap (acount for both sides of the key) to the location value to move foward with next bin
      start_label = start_label + keywidth + gap
      
      i = i + 1
      
    }
    return(ggplot_object_list)
    
  }
  
  
  
  
  
  
  ########################################################################
  ##### create graphic ###################################################
  ########################################################################
  
  d = ggplot() +
    
    ### state grey background ###########
  geom_polygon(
    data=state.df,
    aes(y=lat, x=long, group=group),
    fill='#cccccc'
  ) +
    
    
    ### county choropleth map ###########
  geom_polygon(
    data=mapa.df,
    ###Aesthetic tells ggplot which variables are being mapped to the x axis, y axis,
    ###(and often other attributes of the graph, such as the color fill).
    ###Intuitively, the aesthetic can be thought of as what you are graphing.
    
    ###y-axis of graph referencing lat column
    ###x-axis of graph referencing long column
    ###group tells ggplot that the data has explicit groups
    ###fill color of features referencing fill column. Fill color is initially arbitrary (changing the color of fill will be addressed later in code)
    aes(y=lat, x=long, group=group, fill = fill),
    colour = '#cccccc',
    size = 0.5
  ) +
    
    
    
    ### state boundary strokes ###########
  geom_polygon(
    data=state.df,
    aes(y=lat, x=long, group=group),
    alpha=0,
    colour='white',
    size=0.5
  ) +
    
    
    
    # Equal scale cartesian coordinates
    ####NOTE: besure to set clip to off or the grob annotation is clipped by the dimensions of the panel
    coord_equal(clip = 'off') +
    
    #### add title to map #######
  labs(title = title) +
    
    
    
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
      # panel.margin=unit(-10, "cm"),
      
      
      
      
      
      
      plot.background = element_rect(fill = NA, color = NA),
      
      ###extend bottom margin of plot to accomidate legend and grob annotation
      plot.margin = unit(c(0, 0, 2, 0), "cm"),
      
      #### modified attributes ########################
      plot.title = element_text(size= 45, vjust=-12.0, hjust=0.10, color = "#4e4d47"),
      legend.text = element_text(color='white', size=0),
      legend.margin=margin(t = -0.1, unit='cm'),
      
      ###sets legend to 0,0 versus center of map???
      legend.justification = c(0,0),
      
      legend.position = c(start_legend, -0.05),   ####(horizontal, vertical)
      
      ###spacing between legend number_of_breaks
      legend.spacing.x = unit(gap, 'npc')
      
    ) +
    
    scale_fill_manual(values = rev(brewer.pal(10, figure_params$palette)[getLegendRange(bin_breaks)]),
                      
                      
                      
                      #Legend type guide shows key (i.e., geoms) mapped onto values.
                      guide = guide_legend( title='',
                                            title.theme = element_text(
                                              size = 0,
                                              color = "#4e4d47",
                                              vjust=0.0,
                                              angle = 0
                                            ),
                                            # legend bin dimensions
                                            keyheight = unit(keyheight, units = "npc"),
                                            # keywidth = unit(1.9*keywidth, units = "npc"),
                                            keywidth = unit(2.70*keywidth, units = "npc"),
                                            # keywidth = unit(4.05*keywidth, units = "npc"),
                                            
                                            #legend elements position
                                            label.position = "bottom",
                                            title.position = 'top',
                                            
                                            #The desired number of rows of legends.
                                            nrow=1
                      )
    )
  
  
  # a = stri_unescape_unicode(gsub("\\U","\\u",mapa@data$legend_title, fixed=TRUE))
  
  a=expression(paste("4"^"th"))
  print(a)
  # a = stri_unescape_unicode(gsub("\\U","\\u","Emissions (Gg CO\u2082)", fixed=TRUE))
  legend_title <- annotation_custom(grobTree(textGrob(a, x = start_legend, y = 0.025, just="left", rot = 0,gp=gpar(col="#4e4d47", fontsize=45, fontface="bold"))))
  legendlabels <- legendLabelCreator(start_label = start_label, number_of_breaks = number_of_breaks, labels = labels)
  
  
  
  
  #### add annotation to map object ###################################################
  ggplot_obj = d + legend_title + legendlabels
  return(ggplot_obj)
  
} 

############################## end temp #############################################################

