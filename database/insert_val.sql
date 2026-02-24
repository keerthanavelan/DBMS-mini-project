INSERT INTO Airline (airline_id, airline_name)
SELECT airline_seq.NEXTVAL, airline
FROM (SELECT DISTINCT airline FROM flights_raw);

INSERT INTO City (city_id, city_name)
SELECT city_seq.NEXTVAL, city_name
FROM (
    SELECT DISTINCT source_city AS city_name FROM flights_raw
    UNION
    SELECT DISTINCT destination_city FROM flights_raw
);

INSERT INTO Flight (flight_id, airline_id, flight_number)
SELECT flight_seq.NEXTVAL, a.airline_id, fr.flight
FROM (
    SELECT DISTINCT airline, flight FROM flights_raw
) fr
JOIN Airline a
ON fr.airline = a.airline_name;

INSERT INTO Flight_Schedule (
    schedule_id,
    flight_id,
    source_city_id,
    destination_city_id,
    departure_time,
    arrival_time,
    duration,
    stops
)
SELECT
    schedule_seq.NEXTVAL,
    x.flight_id,
    x.source_city_id,
    x.destination_city_id,
    x.departure_time,
    x.arrival_time,
    x.duration,
    x.stops
FROM (
    SELECT DISTINCT
        f.flight_id,
        cs.city_id AS source_city_id,
        cd.city_id AS destination_city_id,
        fr.departure_time,
        fr.arrival_time,
        fr.duration,
        fr.stops
    FROM flights_raw fr
    JOIN Flight f
        ON fr.flight = f.flight_number
    JOIN Airline a
        ON fr.airline = a.airline_name
       AND f.airline_id = a.airline_id
    JOIN City cs
        ON fr.source_city = cs.city_name
    JOIN City cd
        ON fr.destination_city = cd.city_name
) x;

INSERT INTO Fare (
    fare_id,
    schedule_id,
    travel_class,
    days_left,
    price
)
SELECT
    fare_seq.NEXTVAL,
    x.schedule_id,
    x.travel_class,
    x.days_left,
    x.price
FROM (
    SELECT DISTINCT
        fs.schedule_id,
        fr.travel_class,
        fr.days_left,
        fr.price
    FROM flights_raw fr
    JOIN Flight f
        ON fr.flight = f.flight_number
    JOIN Airline a
        ON fr.airline = a.airline_name
       AND f.airline_id = a.airline_id
    JOIN City cs
        ON fr.source_city = cs.city_name
    JOIN City cd
        ON fr.destination_city = cd.city_name
    JOIN Flight_Schedule fs
        ON fs.flight_id = f.flight_id
        AND fs.source_city_id = cs.city_id
        AND fs.destination_city_id = cd.city_id
        AND fs.departure_time = fr.departure_time
        AND fs.arrival_time = fr.arrival_time
        AND fs.duration = fr.duration
        AND fs.stops = fr.stops
) x;

SELECT COUNT(*) FROM FLIGHTS_RAW;
SELECT COUNT(*) FROM FARE;
SELECT COUNT(*) FROM Airline;
SELECT COUNT(*) FROM City;
SELECT COUNT(*) FROM Flight;
SELECT COUNT(*) FROM Flight_Schedule;


SELECT *
FROM FLIGHTS_RAW
WHERE ROWNUM <= 10;


--users (temporary data)
INSERT INTO App_User (user_id, name, email, password)
VALUES (user_seq.NEXTVAL, 'Keerthana', 'keerthana@gmail.com', 'demo123');

COMMIT;

SELECT * FROM App_User;

INSERT INTO Trip (
    trip_id,
    user_id,
    source_city_id,
    destination_city_id,
    departure_date,
    return_date,
    total_budget
)
VALUES (
    trip_seq.NEXTVAL,
    1,
    28,
    32,
    DATE '2024-05-01',
    DATE '2024-05-07',
    60000
);

SELECT * FROM Trip;

INSERT INTO Expense VALUES (
    expense_seq.NEXTVAL,
    1,
    'Flight',
    22000,
    SYSDATE,
    'Round trip airfare'
);

INSERT INTO Expense VALUES (
    expense_seq.NEXTVAL,
    1,
    'Hotel',
    18000,
    SYSDATE,
    '5 nights stay'
);

INSERT INTO Expense VALUES (
    expense_seq.NEXTVAL,
    1,
    'Food',
    6000,
    SYSDATE,
    'Dining expenses'
);

INSERT INTO Expense VALUES (
    expense_seq.NEXTVAL,
    1,
    'Transport',
    4000,
    SYSDATE,
    'Local commute'
);

COMMIT;


--logic demo code

--total spent
SELECT SUM(amount) AS total_spent
FROM Expense
WHERE trip_id = 1;

--budget vs spent
SELECT t.total_budget,
       NVL(SUM(e.amount),0) AS total_spent,
       t.total_budget - NVL(SUM(e.amount),0) AS remaining_balance
FROM Trip t
LEFT JOIN Expense e ON t.trip_id = e.trip_id
WHERE t.trip_id = 1
GROUP BY t.total_budget;

--expense breakdown
SELECT category, SUM(amount)
FROM Expense
WHERE trip_id = 1
GROUP BY category;