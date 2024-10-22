from flask import Flask, jsonify, request
import mysql.connector
from mysql.connector import Error
from flask_cors import CORS, cross_origin
import config
import pyodbc
app = Flask(__name__)

# Enable CORS for all routes and allow specific origin (http://localhost:3000)
# CORS(app)
CORS(app, resources={r"/*": {"origins": "https://frontend-dfd9d6ehahgdazdk.eastus-01.azurewebsites.net"}})
# CORS(app, resources={r"/*": {"origins": ["http://localhost:3000","https://multitenant-fe-ckabezf7eab2cudb.eastus-01.azurewebsites.net"]}},
#      supports_credentials=True, 
#      allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Credentials"])

# cors = CORS(app, resource={
#     r"/*": {
#         "origins": "*"
#     }
# })
# app.config['CORS_HEADERS'] = 'Content-Type'
# # Function to establish a MySQL connection for a specific database
# def get_db_connection(database_name):
#     try:
#         connection = mysql.connector.connect(
#             host=config.MYSQL_HOST,
#             user=config.MYSQL_USER,
#             password=config.MYSQL_PASSWORD,
#             database=database_name  # Dynamically use the database name
#         )
#         if connection.is_connected():
#             print(f"Connected to {database_name} database")
#             return connection
#     except Error as e:
#         print(f"Error connecting to MySQL: {e}")
#         return None
@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Backend is successfully running!"}), 200
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
# @cross_origin(origin='https://multitenant-fe-ckabezf7eab2cudb.eastus-01.azurewebsites.net')  # Allow frontend domain
def login_user():
    # # Handle preflight OPTIONS request
    # if request.method == 'OPTIONS':
    #     return jsonify({}), 200

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

if __name__ == '__main__':
    app.run(debug=True)
