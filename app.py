from flask import Flask, jsonify, request
import pyodbc
from flask_cors import CORS, cross_origin
import config

app = Flask(__name__)

# Enable CORS globally for your allowed origins
CORS(app, resources={r"/*": {"origins": "https://frontend-dfd9d6ehahgdazdk.eastus-01.azurewebsites.net"}})

# Route to check if the backend is running
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

# Route to handle user login with CORS enabled
@app.route('/login', methods=['POST', 'OPTIONS'])
@cross_origin(origin='https://frontend-dfd9d6ehahgdazdk.eastus-01.azurewebsites.net')
def login_user():
    # Handle the preflight OPTIONS request
    if request.method == 'OPTIONS':
        return jsonify({}), 200  # Respond to OPTIONS request with an empty 200 response

    data = request.json
    domain = data.get('domain')

    # Domain to database mapping
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
            query = "SELECT * FROM users WHERE email = ? AND password = ?"
            values = (data['email'], data['password'])
            cursor.execute(query, values)
            user = cursor.fetchone()

            if user:
                columns = [column[0] for column in cursor.description]
                user_dict = dict(zip(columns, user))
                return jsonify(user_dict), 200
            else:
                return jsonify({'error': 'Invalid credentials'}), 401
        except pyodbc.Error as e:
            return jsonify({'error': str(e)}), 500
        finally:
            cursor.close()
            connection.close()

    return jsonify({'error': 'Database connection failed'}), 500

if __name__ == '__main__':
    app.run(debug=True)
