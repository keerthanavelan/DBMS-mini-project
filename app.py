# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import oracledb
from datetime import datetime
import os
from dotenv import load_dotenv

oracledb.init_oracle_client(lib_dir=r"C:\oracle\instantclient_23_26\instantclient_23_0")
# ============================================================================
# CONFIGURATION
# ============================================================================

load_dotenv()

app = Flask(__name__)
CORS(app)

# Oracle Database Configuration
DB_CONFIG = {
    'user': os.getenv('DB_USER', 'FLIGHT_USER'),
    'password': os.getenv('DB_PASSWORD', 'flight123'),
    'dsn': os.getenv('DB_DSN', 'localhost:1521/XE')
}

# Initialize Oracle Client (optional - for thick mode)
# Uncomment if you need thick mode (e.g., for advanced features)
# oracledb.init_oracle_client(lib_dir=r"path/to/instantclient")

# ============================================================================
# DATABASE HELPERS
# ============================================================================

def get_db_connection():
    """Create and return a database connection"""
    try:
        connection = oracledb.connect(
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            dsn=DB_CONFIG['dsn']
        )
        return connection
    except oracledb.Error as error:
        print(f"Database connection error: {error}")
        return None

def execute_query(query, params=None, fetch_one=False, fetch_all=False, commit=False):
    """
    Execute a database query and return results.
    Returns standardized response: (success, data, error_message)
    """
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        if not connection:
            return False, None, "Database connection failed"
        
        cursor = connection.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if commit:
            connection.commit()
            return True, None, None
        elif fetch_one:
            result = cursor.fetchone()
            return True, result, None
        elif fetch_all:
            result = cursor.fetchall()
            return True, result, None
        else:
            return True, None, None
            
    except oracledb.Error as error:
        if commit and connection:
            connection.rollback()
        return False, None, str(error)
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def safe_float(value):
    """Safely convert value to float, return 0.0 if conversion fails"""
    if value is None:
        return 0.0
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def safe_int(value):
    """Safely convert value to int, return 0 if conversion fails"""
    if value is None:
        return 0
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0

def format_response(success, data=None, message=None, status_code=200):
    """
    Standardized API response formatter.
    Returns tuple (json_response, status_code)
    """
    response = {
        'success': success,
        'data': data if data is not None else ([] if not success else None),
        'message': message if message else ('Operation successful' if success else 'Operation failed')
    }
    return jsonify(response), status_code

# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.route('/api/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.json or {}
    name = data.get('name')
    email = data.get('email').strip()
    password = data.get('password').strip()
    
    # Validation
    if not all([name, email, password]):
        return format_response(False, message='All fields are required', status_code=400)
    
    if len(password) < 6:
        return format_response(False, message='Password must be at least 6 characters', status_code=400)
    
    # Check if user already exists
    check_query = "SELECT user_id FROM App_User WHERE email = :email"
    success, existing_user, error = execute_query(check_query, {'email': email}, fetch_one=True)
    
    if not success:
        return format_response(False, message=f'Database error: {error}', status_code=500)
    
    if existing_user:
        return format_response(False, message='Email already registered', status_code=400)
    
    # Insert new user
    insert_query = """
        INSERT INTO App_User (user_id, name, email, password)
        VALUES (user_seq.NEXTVAL, :name, :email, :password)
        RETURNING user_id INTO :user_id
    """
    
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        if not connection:
            return format_response(False, message='Database connection failed', status_code=500)
        
        cursor = connection.cursor()
        user_id = cursor.var(oracledb.NUMBER)
        
        cursor.execute(insert_query, {
            'name': name,
            'email': email,
            'password': password,
            'user_id': user_id
        })
        connection.commit()
        
        response_data = {
            'user_id': int(user_id.getvalue()[0]),
            'name': name,
            'email': email
        }
        
        return format_response(True, data=response_data, message='Registration successful')
        
    except oracledb.Error as error:
        if connection:
            connection.rollback()
        return format_response(False, message=f'Database error: {str(error)}', status_code=500)
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@app.route('/api/login', methods=['POST'])
def login():
    """Authenticate a user"""
    data = request.json or {}
    email = data.get('email')
    password = data.get('password')
    
    if not all([email, password]):
        return format_response(False, message='Email and password are required', status_code=400)
    
    query = """
        SELECT user_id, name, email 
        FROM App_User 
        WHERE email = :email AND password = :password
    """
    
    success, user, error = execute_query(query, {'email': email, 'password': password}, fetch_one=True)
    
    if not success:
        return format_response(False, message=f'Database error: {error}', status_code=500)
    
    if user:
        response_data = {
            'user_id': user[0],
            'name': user[1],
            'email': user[2]
        }
        return format_response(True, data=response_data, message='Login successful')
    else:
        return format_response(False, message='Invalid credentials', status_code=401)

# ============================================================================
# FLIGHT ENDPOINTS
# ============================================================================

@app.route('/api/flights/search', methods=['GET'])
def search_flights():
    """Search for flights based on criteria"""
    source = request.args.get('source')
    destination = request.args.get('destination')
    travel_class = request.args.get('travel_class')
    stops = request.args.get('stops')
    max_price = request.args.get('max_price')
    
    query = """
        SELECT 
            f.flight_number,
            a.airline_name,
            cs.city_name AS source,
            cd.city_name AS destination,
            fs.departure_time,
            fs.arrival_time,
            fs.duration,
            fs.stops,
            fr.travel_class,
            fr.days_left,
            fr.price
        FROM Flight f
        JOIN Airline a ON f.airline_id = a.airline_id
        JOIN Flight_Schedule fs ON f.flight_id = fs.flight_id
        JOIN City cs ON fs.source_city_id = cs.city_id
        JOIN City cd ON fs.destination_city_id = cd.city_id
        JOIN Fare fr ON fs.schedule_id = fr.schedule_id
        WHERE 1=1
    """
    
    params = {}
    
    if source:
        query += " AND cs.city_name = :source"
        params['source'] = source
    if destination:
        query += " AND cd.city_name = :destination"
        params['destination'] = destination
    if travel_class:
        query += " AND fr.travel_class = :travel_class"
        params['travel_class'] = travel_class
    if stops is not None:
        query += " AND fs.stops = :stops"
        params['stops'] = safe_int(stops)
    if max_price:
        query += " AND fr.price <= :max_price"
        params['max_price'] = safe_float(max_price)
    
    query += " ORDER BY fr.price"
    
    success, results, error = execute_query(query, params, fetch_all=True)
    
    if not success:
        return format_response(False, message=f'Database error: {error}', status_code=500)
    
    if not results:
        return format_response(True, data=[], message='No flights found')
    
    flights = []
    for row in results:
        flights.append({
            'flight_number': row[0],
            'airline_name': row[1],
            'source': row[2],
            'destination': row[3],
            'departure_time': row[4],
            'arrival_time': row[5],
            'duration': safe_int(row[6]),
            'stops': safe_int(row[7]),
            'travel_class': row[8],
            'days_left': safe_int(row[9]),
            'price': safe_float(row[10])
        })
    
    return format_response(True, data=flights, message=f'Found {len(flights)} flights')

@app.route('/api/flights/<flight_number>', methods=['GET'])
def get_flight_details(flight_number):
    """Get detailed information for a specific flight"""
    query = """
        SELECT 
            f.flight_number,
            a.airline_name,
            cs.city_name AS source,
            cd.city_name AS destination,
            fs.departure_time,
            fs.arrival_time,
            fs.duration,
            fs.stops,
            fr.travel_class,
            fr.days_left,
            fr.price
        FROM Flight f
        JOIN Airline a ON f.airline_id = a.airline_id
        JOIN Flight_Schedule fs ON f.flight_id = fs.flight_id
        JOIN City cs ON fs.source_city_id = cs.city_id
        JOIN City cd ON fs.destination_city_id = cd.city_id
        JOIN Fare fr ON fs.schedule_id = fr.schedule_id
        WHERE f.flight_number = :flight_number
        ORDER BY fr.price
    """
    
    success, results, error = execute_query(query, {'flight_number': flight_number}, fetch_all=True)
    
    if not success:
        return format_response(False, message=f'Database error: {error}', status_code=500)
    
    if not results:
        return format_response(False, message='Flight not found', status_code=404)
    
    # Group fares by schedule
    flight_info = {
        'flight_number': results[0][0],
        'airline_name': results[0][1],
        'source': results[0][2],
        'destination': results[0][3],
        'departure_time': results[0][4],
        'arrival_time': results[0][5],
        'duration': safe_int(results[0][6]),
        'stops': safe_int(results[0][7]),
        'fares': []
    }
    
    for row in results:
        flight_info['fares'].append({
            'travel_class': row[8],
            'days_left': safe_int(row[9]),
            'price': safe_float(row[10])
        })
    
    return format_response(True, data=flight_info, message='Flight details retrieved')

@app.route('/api/cities', methods=['GET'])
def get_cities():
    """Get all cities for dropdowns"""
    query = "SELECT city_name FROM City ORDER BY city_name"
    success, results, error = execute_query(query, fetch_all=True)
    
    if not success:
        return format_response(False, message=f'Database error: {error}', status_code=500)
    
    cities = [row[0] for row in results] if results else []
    return format_response(True, data=cities, message=f'Found {len(cities)} cities')

# ============================================================================
# TRIP ENDPOINTS
# ============================================================================

@app.route('/api/trips', methods=['GET'])
def get_trips():
    """Get all trips for a user"""
    user_id = request.args.get('user_id')
    
    if not user_id:
        return format_response(False, message='User ID required', status_code=400)
    
    query = """
        SELECT 
            t.trip_id,
            cs.city_name AS source,
            cd.city_name AS destination,
            TO_CHAR(t.departure_date, 'YYYY-MM-DD') AS departure_date,
            TO_CHAR(t.return_date, 'YYYY-MM-DD') AS return_date,
            t.total_budget
        FROM Trip t
        JOIN City cs ON t.source_city_id = cs.city_id
        JOIN City cd ON t.destination_city_id = cd.city_id
        WHERE t.user_id = :user_id
        ORDER BY t.departure_date DESC
    """
    
    success, results, error = execute_query(query, {'user_id': safe_int(user_id)}, fetch_all=True)
    
    if not success:
        return format_response(False, message=f'Database error: {error}', status_code=500)
    
    if not results:
        return format_response(True, data=[], message='No trips found')
    
    trips = []
    for row in results:
        trips.append({
            'trip_id': row[0],
            'source': row[1],
            'destination': row[2],
            'departure_date': row[3],
            'return_date': row[4],
            'total_budget': safe_float(row[5])
        })
    
    return format_response(True, data=trips, message=f'Found {len(trips)} trips')

@app.route('/api/trips/<int:trip_id>', methods=['GET'])
def get_trip_details(trip_id):
    """Get detailed information for a specific trip"""
    query = """
        SELECT 
            t.trip_id,
            t.user_id,
            cs.city_name AS source,
            cd.city_name AS destination,
            TO_CHAR(t.departure_date, 'YYYY-MM-DD') AS departure_date,
            TO_CHAR(t.return_date, 'YYYY-MM-DD') AS return_date,
            t.total_budget,
            u.name AS user_name,
            u.email AS user_email
        FROM Trip t
        JOIN City cs ON t.source_city_id = cs.city_id
        JOIN City cd ON t.destination_city_id = cd.city_id
        JOIN App_User u ON t.user_id = u.user_id
        WHERE t.trip_id = :trip_id
    """
    
    success, result, error = execute_query(query, {'trip_id': trip_id}, fetch_one=True)
    
    if not success:
        return format_response(False, message=f'Database error: {error}', status_code=500)
    
    if not result:
        return format_response(False, message='Trip not found', status_code=404)
    
    trip_data = {
        'trip_id': result[0],
        'user_id': result[1],
        'source': result[2],
        'destination': result[3],
        'departure_date': result[4],
        'return_date': result[5],
        'total_budget': safe_float(result[6]),
        'user_name': result[7],
        'user_email': result[8]
    }
    
    return format_response(True, data=trip_data, message='Trip details retrieved')

@app.route('/api/trips', methods=['POST'])
def create_trip():
    """Create a new trip"""
    data = request.json or {}
    user_id = data.get('user_id')
    source_city_name = data.get('source_city_name')
    destination_city_name = data.get('destination_city_name')
    departure_date = data.get('departure_date')
    return_date = data.get('return_date')
    total_budget = data.get('total_budget')
    
    if not all([user_id, source_city_name, destination_city_name, departure_date, total_budget]):
        return format_response(False, message='Missing required fields', status_code=400)
    
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        if not connection:
            return format_response(False, message='Database connection failed', status_code=500)
        
        cursor = connection.cursor()
        
        # Get or create source city
        source_query = "SELECT city_id FROM City WHERE city_name = :name"
        cursor.execute(source_query, {'name': source_city_name})
        source_city = cursor.fetchone()
        
        if not source_city:
            insert_city = "INSERT INTO City (city_id, city_name) VALUES (city_seq.NEXTVAL, :name) RETURNING city_id INTO :city_id"
            city_id = cursor.var(oracledb.NUMBER)
            cursor.execute(insert_city, {'name': source_city_name, 'city_id': city_id})
            source_city_id = int(city_id.getvalue())
        else:
            source_city_id = source_city[0]
        
        # Get or create destination city
        cursor.execute(source_query, {'name': destination_city_name})
        dest_city = cursor.fetchone()
        
        if not dest_city:
            insert_city = "INSERT INTO City (city_id, city_name) VALUES (city_seq.NEXTVAL, :name) RETURNING city_id INTO :city_id"
            city_id = cursor.var(oracledb.NUMBER)
            cursor.execute(insert_city, {'name': destination_city_name, 'city_id': city_id})
            dest_city_id = int(city_id.getvalue())
        else:
            dest_city_id = dest_city[0]
        
        # Create trip
        insert_trip = """
            INSERT INTO Trip (trip_id, user_id, source_city_id, destination_city_id, 
                             departure_date, return_date, total_budget)
            VALUES (trip_seq.NEXTVAL, :user_id, :source_city_id, :destination_city_id,
                    TO_DATE(:departure_date, 'YYYY-MM-DD'), 
                    TO_DATE(:return_date, 'YYYY-MM-DD'), 
                    :total_budget)
            RETURNING trip_id INTO :trip_id
        """
        
        trip_id = cursor.var(oracledb.NUMBER)
        cursor.execute(insert_trip, {
            'user_id': safe_int(user_id),
            'source_city_id': source_city_id,
            'destination_city_id': dest_city_id,
            'departure_date': departure_date,
            'return_date': return_date if return_date else departure_date,
            'total_budget': safe_float(total_budget),
            'trip_id': trip_id
        })
        
        connection.commit()
        
        response_data = {
            'trip_id': int(trip_id.getvalue()[0])
        }
        
        return format_response(True, data=response_data, message='Trip created successfully')
        
    except oracledb.Error as error:
        if connection:
            connection.rollback()
        return format_response(False, message=f'Database error: {str(error)}', status_code=500)
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@app.route('/api/trips/<int:trip_id>', methods=['PUT'])
def update_trip(trip_id):
    """Update an existing trip"""
    data = request.json or {}
    departure_date = data.get('departure_date')
    return_date = data.get('return_date')
    total_budget = data.get('total_budget')
    
    if not any([departure_date, return_date, total_budget]):
        return format_response(False, message='No fields to update', status_code=400)
    
    update_fields = []
    params = {'trip_id': trip_id}
    
    if departure_date:
        update_fields.append("departure_date = TO_DATE(:departure_date, 'YYYY-MM-DD')")
        params['departure_date'] = departure_date
    if return_date:
        update_fields.append("return_date = TO_DATE(:return_date, 'YYYY-MM-DD')")
        params['return_date'] = return_date
    if total_budget is not None:
        update_fields.append("total_budget = :total_budget")
        params['total_budget'] = safe_float(total_budget)
    
    update_query = f"""
        UPDATE Trip 
        SET {', '.join(update_fields)}
        WHERE trip_id = :trip_id
    """
    
    success, _, error = execute_query(update_query, params, commit=True)
    
    if not success:
        return format_response(False, message=f'Failed to update trip: {error}', status_code=500)
    
    return format_response(True, message='Trip updated successfully')

@app.route('/api/trips/<int:trip_id>', methods=['DELETE'])
def delete_trip(trip_id):
    """Delete a trip and its associated expenses"""
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        if not connection:
            return format_response(False, message='Database connection failed', status_code=500)
        
        cursor = connection.cursor()
        
        # Delete expenses first due to foreign key constraint
        cursor.execute("DELETE FROM Expense WHERE trip_id = :trip_id", {'trip_id': trip_id})
        
        # Delete the trip
        cursor.execute("DELETE FROM Trip WHERE trip_id = :trip_id", {'trip_id': trip_id})
        
        connection.commit()
        
        return format_response(True, message='Trip and associated expenses deleted successfully')
        
    except oracledb.Error as error:
        if connection:
            connection.rollback()
        return format_response(False, message=f'Database error: {str(error)}', status_code=500)
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@app.route('/api/trips/budget-summary', methods=['GET'])
def get_trip_budget_summary():
    """Get budget summary for a specific trip"""
    trip_id = request.args.get('trip_id')
    
    if not trip_id:
        return format_response(False, message='Trip ID required', status_code=400)
    
    query = """
        SELECT 
            t.total_budget,
            NVL(SUM(e.amount), 0) AS spent,
            (t.total_budget - NVL(SUM(e.amount), 0)) AS remaining
        FROM Trip t 
        LEFT JOIN Expense e ON t.trip_id = e.trip_id
        WHERE t.trip_id = :trip_id 
        GROUP BY t.total_budget
    """
    
    success, result, error = execute_query(query, {'trip_id': safe_int(trip_id)}, fetch_one=True)
    
    if not success:
        return format_response(False, message=f'Database error: {error}', status_code=500)
    
    if not result:
        return format_response(False, message='Trip not found', status_code=404)
    
    response_data = {
        'total_budget': safe_float(result[0]),
        'spent': safe_float(result[1]),
        'remaining': safe_float(result[2])
    }
    
    return format_response(True, data=response_data)

# ============================================================================
# EXPENSE ENDPOINTS
# ============================================================================

@app.route('/api/expenses', methods=['GET'])
def get_expenses():
    """Get all expenses for a trip"""
    trip_id = request.args.get('trip_id')
    
    if not trip_id:
        return format_response(False, message='Trip ID required', status_code=400)
    
    query = """
        SELECT 
            expense_id,
            category,
            amount,
            TO_CHAR(expense_date, 'YYYY-MM-DD') AS expense_date,
            description
        FROM Expense 
        WHERE trip_id = :trip_id 
        ORDER BY expense_date DESC
    """
    
    success, results, error = execute_query(query, {'trip_id': safe_int(trip_id)}, fetch_all=True)
    
    if not success:
        return format_response(False, message=f'Database error: {error}', status_code=500)
    
    if not results:
        return format_response(True, data=[], message='No expenses found')
    
    expenses = []
    for row in results:
        expenses.append({
            'expense_id': row[0],
            'category': row[1],
            'amount': safe_float(row[2]),
            'expense_date': row[3],
            'description': row[4]
        })
    
    return format_response(True, data=expenses, message=f'Found {len(expenses)} expenses')

@app.route('/api/expenses', methods=['POST'])
def add_expense():
    """Add a new expense"""
    data = request.json or {}
    trip_id = data.get('trip_id')
    category = data.get('category')
    amount = data.get('amount')
    expense_date = data.get('expense_date')
    description = data.get('description', '')
    
    if not all([trip_id, category, amount, expense_date]):
        return format_response(False, message='Missing required fields', status_code=400)
    
    insert_query = """
        INSERT INTO Expense (expense_id, trip_id, category, amount, expense_date, description)
        VALUES (expense_seq.NEXTVAL, :trip_id, :category, :amount, 
                TO_DATE(:expense_date, 'YYYY-MM-DD'), :description)
        RETURNING expense_id INTO :expense_id
    """
    
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        if not connection:
            return format_response(False, message='Database connection failed', status_code=500)
        
        cursor = connection.cursor()
        expense_id = cursor.var(oracledb.NUMBER)
        
        cursor.execute(insert_query, {
            'trip_id': safe_int(trip_id),
            'category': category,
            'amount': safe_float(amount),
            'expense_date': expense_date,
            'description': description,
            'expense_id': expense_id
        })
        
        connection.commit()
        
        response_data = {
            'expense_id': int(expense_id.getvalue()[0])
        }
        
        return format_response(True, data=response_data, message='Expense added successfully')
        
    except oracledb.Error as error:
        if connection:
            connection.rollback()
        return format_response(False, message=f'Database error: {str(error)}', status_code=500)
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@app.route('/api/expenses/<int:expense_id>', methods=['PUT'])
def update_expense(expense_id):
    """Update an existing expense"""
    data = request.json or {}
    category = data.get('category')
    amount = data.get('amount')
    expense_date = data.get('expense_date')
    description = data.get('description')
    
    if not any([category, amount, expense_date, description]):
        return format_response(False, message='No fields to update', status_code=400)
    
    update_fields = []
    params = {'expense_id': expense_id}
    
    if category:
        update_fields.append("category = :category")
        params['category'] = category
    if amount is not None:
        update_fields.append("amount = :amount")
        params['amount'] = safe_float(amount)
    if expense_date:
        update_fields.append("expense_date = TO_DATE(:expense_date, 'YYYY-MM-DD')")
        params['expense_date'] = expense_date
    if description is not None:
        update_fields.append("description = :description")
        params['description'] = description
    
    update_query = f"""
        UPDATE Expense 
        SET {', '.join(update_fields)}
        WHERE expense_id = :expense_id
    """
    
    success, _, error = execute_query(update_query, params, commit=True)
    
    if not success:
        return format_response(False, message=f'Failed to update expense: {error}', status_code=500)
    
    return format_response(True, message='Expense updated successfully')

@app.route('/api/expenses/<int:expense_id>', methods=['DELETE'])
def delete_expense(expense_id):
    """Delete an expense"""
    delete_query = "DELETE FROM Expense WHERE expense_id = :expense_id"
    success, _, error = execute_query(delete_query, {'expense_id': expense_id}, commit=True)
    
    if not success:
        return format_response(False, message=f'Failed to delete expense: {error}', status_code=500)
    
    return format_response(True, message='Expense deleted successfully')

# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@app.route('/api/analytics/timeline', methods=['GET'])
def get_expense_timeline():
    """Get expense timeline for a user"""
    user_id = request.args.get('user_id')
    
    if not user_id:
        return format_response(False, message='User ID required', status_code=400)
    
    query = """
        SELECT 
            TO_CHAR(e.expense_date, 'YYYY-MM-DD') AS expense_date,
            e.description,
            e.category,
            e.amount,
            cs.city_name AS source,
            cd.city_name AS destination
        FROM Expense e
        JOIN Trip t ON e.trip_id = t.trip_id
        JOIN City cs ON t.source_city_id = cs.city_id
        JOIN City cd ON t.destination_city_id = cd.city_id
        WHERE t.user_id = :user_id AND e.amount > 0
        ORDER BY e.expense_date DESC
    """
    
    success, results, error = execute_query(query, {'user_id': safe_int(user_id)}, fetch_all=True)
    
    if not success:
        return format_response(False, message=f'Database error: {error}', status_code=500)
    
    if not results:
        return format_response(True, data=[], message='No expense data found')
    
    timeline = []
    for row in results:
        timeline.append({
            'expense_date': row[0],
            'description': row[1],
            'category': row[2],
            'amount': safe_float(row[3]),
            'source': row[4],
            'destination': row[5]
        })
    
    return format_response(True, data=timeline, message=f'Found {len(timeline)} expense records')

@app.route('/api/analytics/category-breakdown', methods=['GET'])
def get_category_breakdown():
    """Get expense breakdown by category for a user"""
    user_id = request.args.get('user_id')
    
    if not user_id:
        return format_response(False, message='User ID required', status_code=400)
    
    query = """
        SELECT 
            e.category,
            SUM(e.amount) AS total_amount
        FROM Expense e
        JOIN Trip t ON e.trip_id = t.trip_id
        WHERE t.user_id = :user_id
        GROUP BY e.category
        ORDER BY total_amount DESC
    """
    
    success, results, error = execute_query(query, {'user_id': safe_int(user_id)}, fetch_all=True)
    
    if not success:
        return format_response(False, message=f'Database error: {error}', status_code=500)
    
    if not results:
        return format_response(True, data=[], message='No category data found')
    
    breakdown = []
    total_spent = 0
    
    for row in results:
        amount = safe_float(row[1])
        total_spent += amount
        breakdown.append({
            'category': row[0],
            'total_amount': amount
        })
    
    # Calculate percentages
    for item in breakdown:
        item['percentage'] = round((item['total_amount'] / total_spent * 100), 2) if total_spent > 0 else 0
    
    return format_response(True, data=breakdown, message=f'Found {len(breakdown)} categories')

@app.route('/api/analytics/monthly-spending', methods=['GET'])
def get_monthly_spending():
    """Get monthly spending pattern for a user"""
    user_id = request.args.get('user_id')
    
    if not user_id:
        return format_response(False, message='User ID required', status_code=400)
    
    query = """
        SELECT 
            TO_CHAR(e.expense_date, 'YYYY-MM') AS month,
            SUM(e.amount) AS total_spent,
            COUNT(e.expense_id) AS expense_count
        FROM Expense e
        JOIN Trip t ON e.trip_id = t.trip_id
        WHERE t.user_id = :user_id
        GROUP BY TO_CHAR(e.expense_date, 'YYYY-MM')
        ORDER BY month DESC
    """
    
    success, results, error = execute_query(query, {'user_id': safe_int(user_id)}, fetch_all=True)
    
    if not success:
        return format_response(False, message=f'Database error: {error}', status_code=500)
    
    if not results:
        return format_response(True, data=[], message='No spending data found')
    
    monthly_data = []
    for row in results:
        monthly_data.append({
            'month': row[0],
            'total_spent': safe_float(row[1]),
            'expense_count': safe_int(row[2])
        })
    
    return format_response(True, data=monthly_data, message=f'Found {len(monthly_data)} months of data')

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    # Test database connection
    connection = get_db_connection()
    db_status = "connected" if connection else "disconnected"
    if connection:
        connection.close()
    
    return format_response(True, data={
        'timestamp': datetime.now().isoformat(),
        'database': db_status,
        'status': 'healthy'
    }, message='Service is healthy')

# ============================================================================
# APPLICATION ENTRY POINT
# ============================================================================

@app.route('/')
def index():
    return jsonify({
        'name': 'Flight Booking and Trip Management API',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': [
            '/api/register',
            '/api/login',
            '/api/flights/search',
            '/api/flights/<flight_number>',
            '/api/cities',
            '/api/trips',
            '/api/trips/<trip_id>',
            '/api/expenses',
            '/api/analytics/timeline',
            '/api/analytics/category-breakdown',
            '/api/analytics/monthly-spending',
            '/api/health'
        ]
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)