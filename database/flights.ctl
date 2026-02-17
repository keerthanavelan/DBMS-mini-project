OPTIONS (SKIP=1)
LOAD DATA
INFILE 'clean_dataset_processed.csv'
INTO TABLE flights_raw
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
TRAILING NULLCOLS
(
 airline,
 flight,
 source_city,
 departure_time,
 stops,
 arrival_time,
 destination_city,
 travel_class,
 duration,
 days_left,
 price
)
