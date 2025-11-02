# ---- Packages ----
library(dplyr)
library(readr)
library(stringr)
library(lubridate)
library(sf)
library(rnaturalearth)
library(rnaturalearthdata)

# ---- Load dataset ----
ghcn_canada <- read_csv("ghcn_canada.csv")

# ---- 1) Keep only stations starting with "CA" ----
ghcn_ca <- ghcn_canada %>%
  filter(str_starts(station, "CA"))

# ---- 2) Arrange by station and date; remove 'year' ----
ghcn_ca <- ghcn_ca %>%
  mutate(date = as_date(date)) %>%
  arrange(station, date) %>%
  select(-year)

# ---- 3) Assign city and province ----

# Get Canada provinces and populated places
prov_sf <- ne_states(country = "canada", returnclass = "sf") %>%
  st_make_valid()

places_sf <- ne_download(scale = 10, type = "populated_places",
                         category = "cultural", returnclass = "sf") %>%
  st_make_valid() %>%
  filter(ADM0NAME == "Canada")

# Convert to spatial points
stations_sf <- ghcn_ca %>%
  st_as_sf(coords = c("longitude", "latitude"), crs = 4326, remove = FALSE)

# Province overlay
stations_with_prov <- st_join(
  stations_sf,
  prov_sf %>% select(prov_name = name, prov_code = postal),
  join = st_within,
  left = TRUE
)

# Fill missing provinces by nearest
missing_prov_idx <- which(is.na(stations_with_prov$prov_name))
if (length(missing_prov_idx) > 0) {
  nearest_idx <- st_nearest_feature(stations_with_prov[missing_prov_idx, ], prov_sf)
  stations_with_prov$prov_name[missing_prov_idx] <- prov_sf$name[nearest_idx]
  stations_with_prov$prov_code[missing_prov_idx] <- prov_sf$postal[nearest_idx]
}

# Nearest city for every station
nearest_city_idx <- st_nearest_feature(stations_with_prov, places_sf)
stations_with_prov$city <- places_sf$NAME[nearest_city_idx]

# Combine province and code into one column (e.g., "Ontario (ON)")
stations_with_prov$city_province <- paste0(
  stations_with_prov$prov_name, " (", stations_with_prov$prov_code, ")"
)

# ---- Finalize & save ----
cleaned_data_with_city_filled <- stations_with_prov %>%
  st_drop_geometry() %>%
  select(station, date, observation, value,
         latitude, longitude, elevation, name,
         city, city_province)

write_csv(cleaned_data_with_city_filled, "cleaned_data_with_city_filled.csv")

cleaned_data_with_city_filled
