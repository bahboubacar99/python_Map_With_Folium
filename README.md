# Map With python library "Folium"
In this project, we will map deaths caused by different diseases using Python's folium library. 
The project chosen in this rendering is the representation of tumour-related deaths by year and gender.
The data was downloaded from the CEPIdc Inserm website, which can be accessed via this [link](https://opendata-cepidc.inserm.fr/)
The **main.py** file contains the project programme in Python. Once executed, a file named death_by_tumour_map.html is created in the main.py file folder, which is a map web page.

## prerequisities : install and import these libraries

import csv
import folium
from folium import plugins
import pandas as pd
import geopandas as geo_pd
from shapely.geometry import shape
import json
from jenkspy import jenks_breaks

## Description of the main functions of the programme  
In the programme, different functions have been created to perform different operations.
read_gpkg(path):
This function reads a GeoPackage (GPKG) file containing geographical data for the departments of France.
It defines the EPSG:4326 Coordinate Reference System (CRS) for this data.
It filters out the overseas departments, keeping only those in metropolitan France.

#### read_death(path):
This function reads a CSV file containing statistics on tumour-related deaths, with each line representing   a death record by department, year and gender.
The function organises the data into a nested dictionary, with department codes as keys. 
Each department contains information on deaths per year, broken down by gender (male/female).
The function processes the records to group deaths by department, year and gender in a dictionary, taking into account missing data. 

### filter_death(death_data):
This function filters death data to exclude overseas departments (outre-mer), retaining only data for metropolitan France.
	
### merge_data(geodata, death):
This function merges geographical data (from the read_gpkg function) with death statistics (from the read_death function).
It joins the two datasets by department code (INSEE_DEP), adding death statistics (cause and annual data) to the geographical entities.

### select_data(death_geo_merge, selected_year, selected_sex):
This function extracts the death data to be mapped from the merged dataset for a specified year and sex (e.g., ‘Men’ or ‘Women’). It converts them into a GeoDataFrame ready for use in mapping.
	
### create_map(death_geo_merge, selected_year, selected_sex):
This function generates an interactive choropleth map using the folium library.
The map shows the number of deaths per department for the selected year and sex.
Different map backgrounds are added, and the map allows the use of drawing and full-screen tools.
A choropleth layer is added to the map, where the shading of each department corresponds to the number of deaths.
Tooltips display detailed information when you hover over a department on the map.
The resulting map is saved as an HTML file (death_by_tumour_map.html).
The geocode plugin is added to the map to allow the user to search for the department they want to see.    
Important: for the slected_year arguments, you must choose a year between 1990 and 2022, and for the selected_sex argument, you must choose either ‘Men’ or ‘Women’.

**Therefore, the user will be able to view the data they want by modifying the values of the selected_year and selected_sex arguments accordingly.** 
	
