CREATE TABLE Airline (
    airline_id NUMBER PRIMARY KEY,
    airline_name VARCHAR2(100) UNIQUE
);
CREATE TABLE City (
    city_id NUMBER PRIMARY KEY,
    city_name VARCHAR2(100) UNIQUE
);
CREATE TABLE Flight (
    flight_id NUMBER PRIMARY KEY,
    airline_id NUMBER,
    flight_number VARCHAR2(20),
    CONSTRAINT fk_flight_airline
        FOREIGN KEY (airline_id)
        REFERENCES Airline(airline_id)
);
CREATE TABLE Flight_Schedule (
    schedule_id NUMBER PRIMARY KEY,
    flight_id NUMBER,
    source_city_id NUMBER,
    destination_city_id NUMBER,
    departure_time VARCHAR2(50),
    arrival_time VARCHAR2(50),
    duration NUMBER,
    stops VARCHAR2(50),
    CONSTRAINT fk_schedule_flight
        FOREIGN KEY (flight_id)
        REFERENCES Flight(flight_id),
    CONSTRAINT fk_schedule_source
        FOREIGN KEY (source_city_id)
        REFERENCES City(city_id),
    CONSTRAINT fk_schedule_destination
        FOREIGN KEY (destination_city_id)
        REFERENCES City(city_id)
);
CREATE TABLE Fare (
    fare_id NUMBER PRIMARY KEY,
    schedule_id NUMBER,
    travel_class VARCHAR2(20),
    days_left NUMBER,
    price NUMBER,
    CONSTRAINT fk_fare_schedule
        FOREIGN KEY (schedule_id)
        REFERENCES Flight_Schedule(schedule_id)
);
CREATE TABLE App_User (
    user_id NUMBER PRIMARY KEY,
    name VARCHAR2(100),
    email VARCHAR2(150) UNIQUE,
    password VARCHAR2(200)
);
CREATE TABLE Trip (
    trip_id NUMBER PRIMARY KEY,
    user_id NUMBER,
    source_city_id NUMBER,
    destination_city_id NUMBER,
    departure_date DATE,
    return_date DATE,
    total_budget NUMBER,
    CONSTRAINT fk_trip_user
        FOREIGN KEY (user_id)
        REFERENCES App_User(user_id),
    CONSTRAINT fk_trip_source
        FOREIGN KEY (source_city_id)
        REFERENCES City(city_id),
    CONSTRAINT fk_trip_destination
        FOREIGN KEY (destination_city_id)
        REFERENCES City(city_id)
);
CREATE TABLE Expense (
    expense_id NUMBER PRIMARY KEY,
    trip_id NUMBER,
    category VARCHAR2(50),
    amount NUMBER,
    expense_date DATE,
    description VARCHAR2(200),
    CONSTRAINT fk_expense_trip
        FOREIGN KEY (trip_id)
        REFERENCES Trip(trip_id)
);
CREATE SEQUENCE airline_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE city_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE flight_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE schedule_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE fare_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE user_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE trip_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE expense_seq START WITH 1 INCREMENT BY 1;