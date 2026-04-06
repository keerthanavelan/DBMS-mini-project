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

--recent entries
SELECT * FROM expense
ORDER BY created_at DESC
LIMIT 5;


SELECT city_id, city_name FROM City WHERE city_name = :source OR city_name = :destination;

--flights between two cities
SELECT f.flight_id, f.flight_number, a.airline_name,
       cs.city_name AS source, cd.city_name AS destination,
       fs.departure_time, fs.arrival_time, fs.duration, fs.stops
FROM Flight f
JOIN Airline a ON f.airline_id = a.airline_id
JOIN Flight_Schedule fs ON f.flight_id = fs.flight_id
JOIN City cs ON fs.source_city_id = cs.city_id
JOIN City cd ON fs.destination_city_id = cd.city_id
WHERE cs.city_name = :source
  AND cd.city_name = :destination;

--insert user
INSERT INTO App_User
VALUES (user_seq.NEXTVAL, :name, :email, :password);

select * from app_user

--trip planning
INSERT INTO Trip
VALUES (trip_seq.NEXTVAL, :user_id, :source, :destination,
        TO_DATE(:departure_date,'DD/MM/YYYY'), TO_DATE(:return_date,'DD/MM/YYYY'), :budget);

SELECT * from city

select * from trip

--view user trips
SELECT t.trip_id, cs.city_name AS source, cd.city_name AS destination,
       t.departure_date, t.return_date, t.total_budget
FROM Trip t
JOIN City cs ON t.source_city_id = cs.city_id
JOIN City cd ON t.destination_city_id = cd.city_id
WHERE t.user_id = :user_id;

--add expense
INSERT INTO Expense
VALUES (
  expense_seq.NEXTVAL,
  :trip_id,
  :category,
  :amount,
  TO_DATE(:expense_date, 'DD/MM/YY'),
  :description
);

select * from expense
--view expenses of a trip
SELECT category, amount, expense_date, description
FROM Expense
WHERE trip_id = :trip_id
ORDER BY expense_date;

--total spent vs budget
SELECT t.total_budget,
       NVL(SUM(e.amount), 0) AS total_spent,
       (t.total_budget - NVL(SUM(e.amount), 0)) AS remaining_budget
FROM Trip t
LEFT JOIN Expense e ON t.trip_id = e.trip_id
WHERE t.trip_id = :trip_id
GROUP BY t.total_budget;

--expenses by category
SELECT category, SUM(amount) AS total
FROM Expense
WHERE trip_id = :trip_id
GROUP BY category;

--most expensive flights
SELECT f.flight_number, MAX(fr.price) AS max_price
FROM Flight f
JOIN Flight_Schedule fs ON f.flight_id = fs.flight_id
JOIN Fare fr ON fs.schedule_id = fr.schedule_id
GROUP BY f.flight_number
ORDER BY max_price DESC;

--popular routes? nvm its based on the app user trips 
SELECT cs.city_name AS source, cd.city_name AS destination, COUNT(*) AS trips
FROM Trip t
JOIN City cs ON t.source_city_id = cs.city_id
JOIN City cd ON t.destination_city_id = cd.city_id
GROUP BY cs.city_name, cd.city_name
ORDER BY trips DESC;

--filters for frontend
SELECT * FROM Fare
WHERE price BETWEEN :min_price AND :max_price;

--direct flights aka no stops
SELECT * FROM Flight_Schedule
WHERE stops = 'zero';

--flights within budget
SELECT fs.schedule_id, fr.price
FROM Flight_Schedule fs
JOIN Fare fr ON fs.schedule_id = fr.schedule_id
JOIN Trip t ON t.source_city_id = fs.source_city_id
WHERE fr.price <= t.total_budget;

--upcoming trips?
SELECT * FROM Trip
WHERE departure_date > SYSDATE
ORDER BY departure_date;

SELECT owner, table_name
FROM all_tables

select * from app_user