SELECT COUNT(*) FROM flights_raw;

SELECT * FROM flights_raw;

describe flights_raw

-- this should return 300153 then all rows are loaded properly
SELECT
    COUNT(*) AS total_rows,
    COUNT(airline) AS airline_not_null,
    COUNT(flight) AS flight_not_null,
    COUNT(source_city) AS source_not_null,
    COUNT(duration) AS duration_not_null,
    COUNT(price) AS price_not_null
FROM flights_raw;

SELECT MIN(duration), MAX(duration) FROM flights_raw;
SELECT MIN(price), MAX(price) FROM flights_raw;

-- in this i think other than the 'travel_class' the others return 6 (travel_class returns 2)
SELECT COUNT(DISTINCT airline) FROM flights_raw;
SELECT COUNT(DISTINCT source_city) FROM flights_raw;
SELECT COUNT(DISTINCT destination_city) FROM flights_raw;
SELECT COUNT(DISTINCT travel_class) FROM flights_raw;

--random check
SELECT * FROM flights_raw WHERE ROWNUM <= 10;

--check for duplicates in airline, flight, source_city, destination_city, departure_time
SELECT airline, flight, source_city, destination_city, departure_time,
       COUNT(*)
FROM flights_raw
GROUP BY airline, flight, source_city, destination_city, departure_time
HAVING COUNT(*) > 1;

--checking if duplicates differ in time, class and days_left
SELECT airline, flight, source_city, destination_city,
       departure_time, days_left, price, COUNT(*)
FROM flights_raw
GROUP BY airline, flight, source_city, destination_city,
         departure_time, days_left, price
HAVING COUNT(*) > 1;

--how many extra rows exist beyond the unique set.
SELECT SUM(cnt - 1) AS duplicate_rows
FROM (
    SELECT COUNT(*) AS cnt
    FROM flights_raw
    GROUP BY airline, flight, source_city, destination_city,
             departure_time, days_left, price
    HAVING COUNT(*) > 1
);


--checking for true full duplicates apparently (quoting chatgpt)
SELECT COUNT(*) - COUNT(DISTINCT
    airline || flight || source_city || destination_city ||
    departure_time || stops || arrival_time ||
    travel_class || duration || days_left || price
) AS exact_duplicates
FROM flights_raw;
