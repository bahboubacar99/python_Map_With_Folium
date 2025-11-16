import csv

import folium
from folium import plugins

import pandas as pd
import geopandas as geo_pd
from shapely.geometry import shape
import json
from jenkspy import jenks_breaks


def read_gpkg(path):
    """
    -read the gpkg file and define its CRS 
    -filter the file to keep only the departments of France metropolitan 
    """
    geodata = geo_pd.read_file(path)
    geodata.crs = 'EPSG:4326'
    outremer = ['971', '972', '973', '974', '976']
    geodata = geodata[~geodata['INSEE_DEP'].isin(outremer)]
    
    return geodata

def read_death(path):
    """
    - Function that takes the relative path as a parameter.
    - reads the csv file containing the actual number of deaths caused by the tumour.
    - browses each line and creates a sub-dictionary with the code_dept as the key
    - inside which there is a years_deces key which also contains subdirectories for each year. 
    - sub-dictionary for each year and which have as keys the sexes
    - to which are the corresponding number of deaths.
     """
   
    death = {}
    with open(path, encoding="utf-8", mode="r") as f:
        reader = csv.DictReader(f, delimiter=";")
        for die in reader :
                           
            try:
                if die["departement_de_domicile"] not in death:                    
                    death[die["departement_de_domicile"]] = { "home_department": die["departement_de_domicile"],
                                                             "initial_cause_of_cause" : die["cause_initiale_de_deces"],
                                                             "death_year": {int(die["annee_de_deces"]):{die["sexe"] : int(die["effectif_de_deces"])}}}
            
                else:
                    year = int(die["annee_de_deces"])
                    if year not in death[die["departement_de_domicile"]]["death_year"]:
                        death[die["departement_de_domicile"]]["death_year"][year]={
                            die["sexe"] : int(die["effectif_de_deces"]), 
                        }         
                    else:
                        sex = die["sexe"]
                        death[die["departement_de_domicile"]]["death_year"][year][sex] = int(die["effectif_de_deces"])
                        
            except KeyError as e :
                print(f"Données incomplètes pour {die}, clé manquante : {e}")
    return death

def filter_death(death_data):
    """
    - function to filter death data by department in order to 
    - exclude outre-mer departments as their data is incomplete
    """
    outremer = ['971', '972', '973', '974', '976']  
    
    filtered_data = {key: value for key, value in death_data.items() if key not in outremer}
    
    return filtered_data


def merge_data(geodata, death):
    """
    - Takes as parameters a dicionary containing the death data
    - and the dataframe containing spatial information. 
    - joins the two sets of data by department code.
    """
    data_merge = geodata[['NOM', 'INSEE_DEP', 'geometry']].dropna().to_json()
    # Convert JSON string to Python dictionary
    data_merge = json.loads(data_merge)  
    for feature in data_merge['features']:        
        dept_code = feature['properties']['INSEE_DEP']
        if dept_code in death:
            feature['properties']["initial_cause_of_cause"] = death[dept_code]["initial_cause_of_cause"]
            feature['properties']['death_year'] = death[dept_code]["death_year"]
        else:
            print(f"Département {dept_code} non trouvé dans les données de décès.")
    return data_merge

def select_data(death_geo_merge, selected_year, selected_sex):
    """
    -Function to obtain death data which will be map according to year and sex.
    -param death_geo_merge: Dictionary containing death data by department.
    -param year: The year selected (for example, 2020).
    -param sex: The sex selected (for example, ‘Male’ or ‘Female’).
    -return: death data selected.
    """
    data_select = {
        feature['properties']['INSEE_DEP'] : {
            'dept_name' : feature['properties'].get('NOM', 'Non spécifiée'),
            'death_number': feature['properties']['death_year'].get(selected_year, {}).get(selected_sex, 0),
            'initial_cause_of_death': feature['properties'].get('initial_cause_of_death', 'Non spécifiée'),
            'geometry': feature['geometry']  
        }
        for feature in death_geo_merge['features']
    }
    #convert dictionary to dataframe
    data_select_df = pd.DataFrame.from_dict(data_select, orient='index')    
    data_select_df['INSEE_DEP'] = data_select_df.index
    data_select_df = data_select_df[['INSEE_DEP','dept_name', 'initial_cause_of_death', 'death_number','geometry']]
    
    #convert geometry column to wkt format
    data_select_df["geometry"] = data_select_df["geometry"].apply(lambda x: shape(x).wkt if x else None)
    
    #convert data_select_df to geodataframe
    data_select_df["geometry"] = geo_pd.GeoSeries.from_wkt(data_select_df["geometry"])  
    data_select_Geodf = geo_pd.GeoDataFrame(data_select_df, geometry='geometry', crs="EPSG:4326")
    
    return data_select_Geodf

def create_map (death_geo_merge, selected_year, selected_sex):
    """
    -function that creates a web map
    -it takes as parameters the fussionner data, and a sex either "Hommes" or "Femmes".
    -applies the select_data function to the fussionner data. 
    -creates a chloropete map with the selected data.    
    """
    
    # Define map area    
    map1 = folium.Map([46.50, 2.34], tiles='cartodbpositron',  control_scale=True, zoom_start=6,)
  
    
    # Create full screen
    plugins.Fullscreen(position='bottomright').add_to(map1)
    draw = plugins.Draw(export=True)# add draw tools to map
    draw.add_to(map1)
    
    # Prepare used data to map by extracting with function select_data
    dataMaped = select_data(death_geo_merge, selected_year, selected_sex)
    
    # Create tiles (background)
    tiles = ['cartodbpositron', 'openstreetmap','stamenwatercolor']
    
    for tile in tiles:
        folium.TileLayer(tile).add_to(map1)
        
    # Create choropleth map
    choropleth = folium.Choropleth(
        geo_data = dataMaped, # geodataframe
        name = 'choropleth', # Map type
        data = dataMaped, 
        columns = ['INSEE_DEP', 'death_number'], # features
        key_on = "feature.properties.INSEE_DEP", 
        fill_color = 'YlOrRd', # color type
        use_jenks=True,
        fill_opacity = 0.7,
        line_opacity = 0.5,
        legend_name = f"Décès des {selected_sex} liés aux tumeurs en {selected_year}",
        highlight = True # Diplay name
    ).add_to(map1)
    
    folium.LayerControl().add_to(map1)
    #add et geocodage option to search a departement
    folium.plugins.Geocoder().add_to(map1)
    
    choropleth.geojson.add_child(
        folium.features.GeoJsonTooltip(
            fields= ['INSEE_DEP', 'dept_name', 'death_number'], 
            aliases=["<b>Code département:</b>",
                     "<b>Nom du département :</b>",
                     f"<b>Décès des {selected_sex} en {str(selected_year)}:</b>"],
            labels=True,
            localize=True,
            sticky=False,
            style="""
                background-color: #F0EFEF;
                border: 2px solid black;
                border-radius: 3px;
                box-shadow: 3px;
                font-size: 14px;
                padding: 5px;
            """,
            max_width=800,
            
            ).add_to(map1)
    )   
          
    map1.save('death_by_tumeur_map.html')
    
def main ():    
    geodata = read_gpkg("./data/departement_reparer.gpkg")
    death_tumor= read_death("./data/deces_cause_tumeur.csv")
    death_tumor_filter = filter_death(death_tumor)
    death_geo_merge = merge_data(geodata, death_tumor_filter)
    
    #for the seccond argument of create_map function choice number between (1990 to 2022)
    #and for the last argument put ("Hommes" or "Femmes" )
    create_map(death_geo_merge, 2015, 'Hommes')

main()
