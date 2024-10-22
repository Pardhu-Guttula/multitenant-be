from flask import Flask, jsonify, request
import mysql.connector
from mysql.connector import Error
from flask_cors import CORS
import config
import pyodbc
from datetime import datetime
import json
app = Flask(__name__)

# Enable CORS for specific origins
CORS(app, resources={r"/*": {"origins": ["http://localhost:3000", "https://multitenant-fe-ckabezf7eab2cudb.eastus-01.azurewebsites.net"]}})

def get_db_connection(database_name):
    try:
        connection = pyodbc.connect(
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={config.MYSQL_HOST};"
            f"DATABASE={database_name};"
            f"UID={config.MYSQL_USER};"
            f"PWD={config.MYSQL_PASSWORD}"
        )
        print(f"Connected to {database_name} database")
        return connection
    except pyodbc.Error as e:
        print(f"Error connecting to SQL Server: {e}")
        return None

# Route to retrieve all users from the respective database based on the domain
@app.route('/login', methods=['POST'])
def login_user():
    data = request.json
    domain = data.get('domain')   # Get the domain entered by the user

    # Check if the domain is valid and map it to the correct database
    if domain == "brillio":
        db_name = "brillio"
    elif domain == "xyz":
        db_name = "xyz"
    elif domain == "abc":
        db_name = "abc"
    else:
        return jsonify({'error': 'Invalid domain'}), 400

    connection = get_db_connection(db_name)
    if connection:
        cursor = connection.cursor()
        try:
            # Query to find the user with the matching email and password
            query = "SELECT * FROM users WHERE email = ? AND password = ?"
            values = (data['email'], data['password'])
            cursor.execute(query, values)
            user = cursor.fetchone()

            if user:
                columns = [column[0] for column in cursor.description]
                user_dict = dict(zip(columns, user))  # Create a dictionary from columns and row values
                return jsonify(user_dict), 200  # Return user data if login is successful
            else:
                return jsonify({'error': 'Invalid credentials'}), 401  # Invalid login
        except Error as e:
            return jsonify({'error': str(e)}), 500
        finally:
            cursor.close()
            connection.close()
    return jsonify({'error': 'Database connection failed'}), 500

@app.route('/log-activity', methods=['POST'])
def log_activity():
    data = request.json
    required_fields = ['email', 'activity', 'timestamp']
    
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    # Extract domain from email
    domain = data['email'].split('@')[1].split('.')[0]
    db_name = domain

    # Additional fields with defaults
    additional_data = {
        'ip_address': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', 'Unknown'),
        'device_info': data.get('device_info', 'Unknown'),
        'session_id': data.get('session_id', 'Unknown'),
        'location': data.get('location', 'Unknown'),
        'outcome': data.get('outcome', 'Unknown'),
        'page': data.get('page', None),
        'time_spent': data.get('timeSpent', None),
        'navigation_type': data.get('navigation_type', None),
        'additional_info': json.dumps({
            k: v for k, v in data.items() 
            if k not in ['email', 'activity', 'timestamp', 'ip_address', 
                        'user_agent', 'device_info', 'session_id', 'location', 
                        'outcome', 'page', 'timeSpent', 'navigation_type']
        })
    }

    connection = get_db_connection(db_name)
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500

    cursor = connection.cursor()
    try:
        # Updated SQL query with additional fields
        insert_query = """
            INSERT INTO user_activities 
            (email, activity, timestamp, ip_address, user_agent, device_info, 
             session_id, location, outcome, page, time_spent, navigation_type, additional_info)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        values = (
            data['email'], data['activity'], data['timestamp'],
            additional_data['ip_address'], additional_data['user_agent'],
            additional_data['device_info'], additional_data['session_id'],
            additional_data['location'], additional_data['outcome'],
            additional_data['page'], additional_data['time_spent'],
            additional_data['navigation_type'], additional_data['additional_info']
        )
        
        cursor.execute(insert_query, values)
        connection.commit()
        return jsonify({"message": "Activity logged successfully"}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()
    return jsonify({'error': 'Database connection failed'}), 500

if __name__ == '__main__':
    app.run(debug=True)
