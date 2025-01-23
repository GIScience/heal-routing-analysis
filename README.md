# Mitigating heat stress by reducing solar exposure in pedestrian routing

Repository in addition to the [paper](#related-publications-1) of the same name. A routing-based network analysis to evaluate the routing algorithm used by the [HEAL project](https://www.geog.uni-heidelberg.de/gis/heal_en.html), providing a solar exposure-reducing routing service for pedestrians. The utilized routing engine is the [OpenRouteService](https://openrouteservice.org/) (ORS).

## Installation

Make sure you have [Docker](https://www.docker.com/) installed, as you will need to build a local ORS instance. Optional: for data exploration and visualization afterwards, you will additionally need [GDAL](https://gdal.org/en/stable/) 3.5 or higher, which is shipped per default with [QGIS](https://qgis.org/) 3.26.

### 1. Download this repository

```shell
git clone https://gitlab.heigit.org/giscience/heal/heal-routing
cd heal-routing
```

### 2. Setup new virtual environment and install poetry (package manager)

> There are two supported options to create new virtual environments, Mamba/Conda and Venv + Pip.
> We recommend using [Mamba](https://mamba.readthedocs.io/en/latest/index.html).

Using [Mamba](https://mamba.readthedocs.io/en/latest/index.html) (if using [Conda](https://docs.conda.io/en/latest/), replace `mamba` with `conda` below):

```shell
mamba env create --file environment.yaml
mamba activate heal-routing
```

Using venv and pip (built-in):

```shell
sudo apt install python3.9 # if not installed already
python3.9 -m venv .venv
source .venv/bin/activate
python3.9 -m pip install poetry
```

### 3. Install necessary dependencies and packages using Poetry

Poetry will detect and respect any existing virtual environment that has been externally activated and will install the dependencies into that environment with:

```shell
poetry install
```

In some rare cases, you need to run the command again after it fails with an error that the dependency `virtualenv` cannot be handled correctly. In our cases, this fixed the error.


**Optional**: To update the packages to their latest suitable versions (and the poetry.lock file), run:

```shell
poetry update
```

### 4. Configure local ORS instance using Docker

All necessary configuration files for this step are included in the repository. To pull the specified ORS build and create a local ORS instance as docker container, run:

```shell
docker compose -f ors/docker-compose.yml up -d
```

Now you can check if the local instance is ready to take on requests at http://localhost:8080/ors/v2/health. The following command does this automatically (need `jq` to be installed on system):

```shell
while [[ $(curl -s http://localhost:8080/ors/v2/health | jq -r '.status') != 'ready' ]]; do sleep 3; done; echo 'It is ready now!'
```

> **Notice:** Solar exposure data (found under `ors/files/`) is currently only available for Heidelberg for the days 170/190 (June 19 & July 9) and 120/240 (April 20 & August 28) of year 2023.

## Data acquisition

### Area of interest (AOI) file

You have two options how to provide the area you are interested in:

- Name of AOI. You can provide the geocode of the AOI which will be used to query the boundaries using the Nominatim API.
- AOI file. You can provide an AOI file containing the AOI boundaries in the `data/` folder. The file should be of type SHP, GPKG with one layer, or GeoJSON.

See [config file](#configuration-file-c-config) for more information.

### Population file

To acquire the population file needed to calculate origin points based on population density, follow these steps:

1. Navigate to the [Global Human Settlement Layer](https://ghsl.jrc.ec.europa.eu/download.php?ds=pop) (note the product name GHS-POP)
2. On the left side, select the desired parameters (epoch, resolution and CRS), e.g. 2020, 100 m, Mollweide
3. Select your tile of interest, e.g. R4_C19 for Germany
4. Unzip the downloaded TIF file and put it in the folder `data/`
5. Rename the file to `pop_file.tif` or change the [config file](#configuration-file-c-config) later on to reflect the name of the file

[Example file](https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_POP_GLOBE_R2023A/GHS_POP_E2020_GLOBE_R2023A_54009_100/V1-0/tiles/GHS_POP_E2020_GLOBE_R2023A_54009_100_V1_0_R4_C19.zip) (R4_C19) for Heidelberg, Germany

## Run the script

Run the program with:

**Example:**
```shell
python src/run.py -c config/config_sample.yaml
```

**Usage:**
```shell
python src/run.py -h
usage: run.py [-h] -c [-oc] [-dc] [-d]

HEAL routing analysis

options:
  -h, --help                show this help message and exit

required arguments:
  -c, --config              Filepath | Configuration file. Example: config/config_sample.yaml

optional arguments:
  -oc, --ors_config         Filepath | ORS configuration file. Default: config/conf/ors_config.yaml
  -dc, --developer_config   Filepath | Developer configuration file. Default: config/conf/developer_config.yaml
```

> **Notice:** we recommend using `config/config_test.yaml` as config file first to test the architecture and program before simulating many routes with `config/config_sample.yaml`, as this can take a long time (around 30 mins with an Intel Core i7-1260P and 32 GB RAM.)

### Configuration file: -c / --config

The configuration file is a yaml file which contains all customizable parameters of the program.
An example config file can be found under [config/config_sample.yaml](./config/config_sample.yaml):

```yaml
aoi_name: Heidelberg
sensitivity_factor: 1.0
day: 170
n_trips: 125
max_distance: 2000
min_distance: 300
solar_threshold_dict:
  low: 50
  high: 90
pop_file: pop_file.tif
poi_type_list:
- bus
- children
- elderly-people
- general
- kindergartens
- market
- offices_townhall
- open-space
- other
- places
- primary-care
- schools
- secondary-care
- small-shops
- supermarket
- trams_subway
osm_timestamp: '2023-05-12'
```

| Parameter | Description                                           |
|-----------|-------------------------------------------------------|
| aoi_name | Name of the AOI (geocode) or name of file of type shapefile, GeoPackage (one layer) or GeoJSON |
| sensitivity_factor | The factor and weight of solar exposure values in the routing algorithm (float value between 0.0 and 1.0). This represents the individual sensitivity to solar exposure from low (0.0) to very high (1.0). |
| day | The day of the solar exposure data. Depends on what is available, in this case int value between 90 and 180 in steps of 10. |
| n_trips | Count of trips per poi type (multiple routes per trip for every time available on HEAL) - take a look at the notice below |
| max_distance | The maximum distance around origin points where POIs should be used as destination points (in m) |
| min_distance | The minimum distance around origin points where POIs should be used as destination points (in m) |
| solar_threshold_dict | Classification of the solar exposure area values in three classes (dict with int values between 1 and 99) |
| pop_file | Name of the population file of type tif |
| poi_type_list | POIs that are considered as destination points (look into poi tags file) - take a look at the notice below |
| osm_timestamp | Timestamp for the query to OSM using the ohsome API |

> **Notice:** the total route count is calculated by `n_trips * len(poi_type_list) * 5`, so by using the config_file above you will get 10000 routes in total.

### Developer configuration file: -dc / --developer_config

The developer configuration file is a yaml file which contains additional parameters that usually do not require to be changed. Nevertheless, should you for example have data files other than those in the `ors/ors-docker/files/` folder, you can specify the column names here in the [config/conf/developer_config.yaml](./config/conf/developer_config.yaml) file. Additionally, you can change some other parameters if necessary to adapt the program to your needs.

```yaml
data_dir: ./data
out_dir: ./export
poi_dir: ./pois
poi_tags_file: poi_tags.json
time_of_day_dict:
  morning: 10 am
  noon: 1 pm
  afternoon: 4 pm
  evening: 7 pm
testenv: False
```

| Parameter | Description                                           |
|-----------|-------------------------------------------------------|
| data_dir | Folder containing necessary data. Should not be changed. |
| out_dir | Name of the folder containing the results. |
| poi_dir | Name of the folder where poi data is saved into. |
| poi_tags_file | Name of file containing all poi information. Used to query POIs and should not be changed. |
| time_of_day_dict | Dictionary containing the columns (times of day) of the solar exposure data as keys and the according values for the output files. If no change should happen, use the same values as keys. |
| testenv | Developing option: if true, uses a random.seed. Otherwise random routes for each script execution. |

**Attention:** we cannot guarantee the successful execution of the script for changes made in this configuration file!

### What the program does (with resulting file locations)

> **Notice:** the path `export/{day}/{sensitivity_factor}/`, where all results are written into, will be called `out_dir` for short from now on. `{}` denotes variables either found in the configuration files or created during execution of the program.

<details>
   <summary><b>Preparation</b></summary>
<br/>

1. **Cleanup** by deleting folders in `out_dir` and temporary data in `./data/` (save the results before executing the program again!)
2. Create **folder structure** with subfolders according to the type of data under `out_dir`
3. **Download POIs** from OSM using the ohsome API - these are destination points (B)

</details>

<details>
   <summary><b>Route generation</b></summary>
<br/>

4. Create **origin points** (A) by reading population data from TIF file and selecting random points in areas with high population density
5. **Query routes from A to B** with a buffer ring around A (min_distance to max_distance) and do validation checks
6. If the route is valid, **query additional solar exposure data** for all times of day with sensitivity_factor = 0.0 and write to file (`out_dir/exportdata/{default}_routes_sol_data.json`)
7. **Create segments** of these default routes and write their solar exposure data to file as well (`out_dir/exportdata/{default}_segments_sol_data.json`)
8. Use the A to B pair to **query the best alternative route for each time of day**, writing all additional four routes with their respective solar exposure data to files (`out_dir/exportdata/routes/{time_of_day}/`)

</details>

<details>
   <summary><b>Evaluation and statistical analysis</b></summary>
<br/>

9. **Evaluate** the routes by **creating statistics** based on the comparison of alternatives to default routes, reading the data of the written files (`out_dir/exportdata/route_level_statistics.feather`)
10. **Create segments** of routes and **rank** them based on geometry and solar thresholds (`out_dir/exportdata/segment_level_statistics.feather`) compared to the respective default route of the A to B pair
11. **Counts segments** for a usage frequency analysis for all times of day and all segments (`out_dir/aggregation/`)

</details>

## Run for multiple days of year and sensitivity factors

To compare the analysis for **multiple days**, we are providing multiple solar exposure data files (found in `ors/ors-docker/files/`). You can use the `run_multiple_days.sh` script to run the program multiple times, rebuilding the docker container each time with the according solar exposure values for each day. Parameters like selecting specific days and config files can be adapted in the script itself.

To make the script file executable and run it (this currently only works on Unix systems):

```shell
chmod +x ./run_multiple_days.sh
./run_multiple_days.sh
```

Similarly, **multiple sensitivity factors** can be modeled, which represent the individual sensitivity to solar exposure. This is done using the `run_multiple_sensitivities.sh` script and following similar steps.

In order to run the analysis for **multiple days with multiple sensitivity factors each**, another script `run_multiple.sh` is provided which combines both scripts.

> **Notice:** due to the possible long running time, you should check if the script works using a small number of routes beforehand (e.g. by using the [config/config_test.yaml](./config/config_test.yaml)). Afterwards, scale the [config file](#configuration-file-c-config) depending on your needs.

## Explore results in QGIS

1. Import the files *route_level_statistics.feather* and *segment_level_statistics.feather* in `out_dir/exportdata` into QGIS to explore them
2. Use the QML files in `data/mapdata/` to style both files using our custom styling recommendation
3. To compare specific solar exposure data for the segments and the respective rankings between the default and shade-optimized routes, follow this guide for the file *all_segments_ranking.feather*:
   - Set filter like `("route_type" = '{default}' OR "route_type" = '{optimized} route at 4pm') AND "trip_id" = 4`
   - In symbology, change value to the one you want to see (`ranking_{time_of_day}`)
   - Labeling rules are preset for morning values, to change choose other `sol_expo_{time_of_day}` values in the rules of the labels

Also, for the files in `out_dir/aggregation`, there is another styling recommendation in `data/mapdata/` to visualize the usage frequency of the segments.

## Additional analysis and generation of figures

Additionally to the QGIS data exploration, there are notebooks which analyze the data using an array of different figures. The usage is explained in the notebooks themselves, found under `src/notebooks/`.

The notebooks were used to create the statistical figures found in the paper. Maps in the paper were created with QGIS.

## Contribution

Any advice, proposal for improvement, or question is welcome on all communication channels!

If you want to contribute code, please use pre-commit by running:

```shell
pre-commit install
```

Using this, we can ensure that the code you provide suits our custom formatting rules before committing or creating a pull request.

## Help

- If you interrupt the execution and change the AOI, you have to delete the `data/pois` folder and the files `pop_file_clipped.tif` and `pop_file_clip_proj.tif` in the `data` folder.
- On Windows machines, call `git config --global core.autocrlf false` before cloning the repository to fix possible "End of Line Sequence" or "...bash/r" errors.
- If you encounter errors where selected points are not possible to route to and are written to error_log.txt, please provide the info (and file) via the issues section, we will look into that. Thank you!

## Authors

- Christina Ludwig
- Nikolaos Kolaxidis

## License

This project is licensed under the MIT License - see the [LICENSE file](./LICENSE) for details

## Related publications

[1] Kolaxidis, N., Ludwig, C., Knoblauch, S., Foshag, K., Fendrich, S., Lautenbach, S., and Zipf, A. (2025) Mitigating Heat Stress by Reducing Solar Exposure in Pedestrian Routing. Preprint. doi:[10.22541/au.173697534.46361284/v1](https://doi.org/10.22541/au.173697534.46361284/v1)

[2] Foshag, K., Fürle, J., Ludwig, C., Fallmann, J., Lautenbach, S., Rupp, S. et al. (2024) How to assess the needs of vulnerable population groups towards
heat-sensitive routing? An evidence-based and practical approach to reducing urban heat stress. Erdkunde, 78(1), 1–33. doi:10.3112/erdkunde.2024.01.01

[3] Ludwig, C., Hecht, R., Lautenbach, S., Schorcht, M., & Zipf, A. (2021) Mapping Public Urban Green Spaces Based on OpenStreetMap and Sentinel-2 Imagery Using Belief Functions. ISPRS International Journal of Geo-Information, 10(4), 251. doi:10.3390/ijgi10040251

[4] Ludwig, C., Lautenbach, S., Schömann, E.M. & Zipf, A. Comparison of Simulated Fast and Green Routes for Cyclists and Pedestrians. In: Janowicz,
K. & Verstegen, J.A. (Eds.) 11th International Conference on Geographic Information Science (GIScience 2021) - Part II. Vol. 208 of Leibniz
International Proceedings in Informatics (LIPIcs), 2021. Dagstuhl, Germany: Schloss Dagstuhl – Leibniz-Zentrum für Informatik, pp. 3:1–3:15.
URL https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.GIScience.2021.II.3

[5] Foshag, K., Aeschbach, N., Höfle, B., Winkler, R., Siegmund, A. & Aeschbach, W. (2020) Viability of public spaces in cities under increasing heat:
A transdisciplinary approach. Sustainable Cities and Society, 59, 102215. doi:10.1016/j.scs.2020.102215.
