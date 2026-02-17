CREATE TABLE flights_raw (
    airline VARCHAR2(100),
    flight VARCHAR2(20),
    source_city VARCHAR2(100),
    departure_time VARCHAR2(50),
    stops VARCHAR2(50),
    arrival_time VARCHAR2(50),
    destination_city VARCHAR2(100),
    travel_class VARCHAR2(20),
    duration NUMBER,
    days_left NUMBER,
    price NUMBER
);
