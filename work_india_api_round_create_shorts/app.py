from flask import Flask, request, jsonify, abort
from flask_mysqldb import MySQL
import yaml
import hashlib
import jwt
import datetime
from datetime import datetime

from datetime import datetime
import pytz


 
app = Flask(__name__)

# Load database configuration
try:
    with open('db.yaml', 'r') as file:
        db_config = yaml.safe_load(file)

    app.config['MYSQL_HOST'] = db_config['mysql_host']
    app.config['MYSQL_USER'] = db_config['mysql_user']
    app.config['MYSQL_PASSWORD'] = db_config['mysql_password']
    app.config['MYSQL_DB'] = db_config['mysql_db']

    mysql = MySQL(app)

except yaml.YAMLError as e:
    print(f"Error loading YAML file: {e}")
    abort(500)  # Internal Server Error
except Exception as e:
    print(f"Error: {e}")
    abort(500)  # Internal Server Error

# Convert the ISO 8601 datetime string to a datetime object
def convert_datetime(iso_datetime_str):
    dt = datetime.strptime(iso_datetime_str, '%Y-%m-%dT%H:%M:%SZ')
    dt_utc = dt.replace(tzinfo=pytz.UTC)  # Ensure it's in UTC
    return dt_utc.strftime('%Y-%m-%d %H:%M:%S')

# JWT Secret Key
SECRET_KEY = 'your_secret_key'

@app.route('/api/signup', methods=['POST'])
def signup():
    if request.method == 'POST':
        userDetails = request.json
        username = userDetails['username']
        password = userDetails['password']
        email = userDetails['email']
        role = userDetails.get('role', 'user')  # Default to 'user' if not provided

        encrypted_pass = hashlib.md5(password.encode()).hexdigest()

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users(username, password, email, role) VALUES(%s, %s, %s, %s)",
                     (username, encrypted_pass, email, role))
        mysql.connection.commit()
        user_id = cur.lastrowid
        cur.close()

        return jsonify({"status": "Account successfully created", "status_code": 200, "user_id": user_id})

    return jsonify({"status": "Invalid method", "status_code": 405})

@app.route('/api/login', methods=['POST'])
def login():
    if request.method == 'POST':
        userDetails = request.json
        username = userDetails.get('username')
        password = userDetails.get('password')

        encrypted_pass = hashlib.md5(password.encode()).hexdigest()

        cur = mysql.connection.cursor()
        # Query adjusted to use 'username' and 'password', 'user_id' and 'role'
        cur.execute("SELECT user_id, role FROM users WHERE username = %s AND password = %s", (username, encrypted_pass))
        user = cur.fetchone()
        cur.close()

        if user:
            user_id, role = user
            token = jwt.encode({'user_id': user_id, 'role': role, 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)}, SECRET_KEY, algorithm='HS256')
            return jsonify({"status": "Login successful", "status_code": 200, "user_id": user_id, "access_token": token})
        
        return jsonify({"status": "Incorrect username/password provided. Please retry", "status_code": 401})

    return jsonify({"status": "Invalid method", "status_code": 405})


@app.route('/api/shorts/create', methods=['POST'])
def create_short():
    if request.method == 'POST':
        token = request.headers.get('Authorization').replace('Bearer ', '')
        try:
            decoded = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            user_id = decoded['user_id']
            role = decoded['role']
        except jwt.ExpiredSignatureError:
            return jsonify({"status": "Token has expired", "status_code": 401})
        except jwt.InvalidTokenError:
            return jsonify({"status": "Invalid token", "status_code": 401})

        if role != 'admin':
            return jsonify({"status": "Access forbidden", "status_code": 403})

        shortDetails = request.json
        category = shortDetails['category']
        title = shortDetails['title']
        author = shortDetails['author']
        publish_date = shortDetails['publish_date']
        content = shortDetails['content']
        actual_content_link = shortDetails['actual_content_link']
        image = shortDetails.get('image', '')
        upvote = shortDetails['votes']['upvote']
        downvote = shortDetails['votes']['downvote']

        # Convert the publish_date to MySQL-compatible format
        mysql_publish_date = convert_datetime(publish_date)

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO shorts (category, title, author, publish_date, content, actual_content_link, image, upvote, downvote) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                     (category, title, author, mysql_publish_date, content, actual_content_link, image, upvote, downvote))
        mysql.connection.commit()
        short_id = cur.lastrowid
        cur.close()

        return jsonify({"message": "Short added successfully", "short_id": short_id, "status_code": 200})

    return jsonify({"status": "Invalid method", "status_code": 405})

@app.route('/api/shorts/feed', methods=['GET'])
def get_feed():
    if request.method == 'GET':
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM shorts ORDER BY publish_date DESC, upvote DESC")
        shorts = cur.fetchall()
        cur.close()

        short_list = [{
            "short_id": short[0],
            "category": short[1],
            "title": short[2],
            "author": short[3],
            "publish_date": short[4].strftime('%Y-%m-%d %H:%M:%S') if short[4] else None,
            "content": short[5],
            "actual_content_link": short[6],
            "image": short[7],
            "votes": {
                "upvote": short[8],
                "downvote": short[9]
            }
        } for short in shorts]

        return jsonify(short_list)

    return jsonify({"status": "Invalid method", "status_code": 405})

@app.route('/api/shorts/filter', methods=['GET'])
def filter_shorts():
    if request.method == 'GET':
        token = request.headers.get('Authorization').replace('Bearer ', '')
        try:
            decoded = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({"status": "Token has expired", "status_code": 401})
        except jwt.InvalidTokenError:
            return jsonify({"status": "Invalid token", "status_code": 401})

        filters = request.args.get('filter', {})
        searches = request.args.get('search', {})

        query = "SELECT * FROM shorts WHERE 1=1"
        
        # Apply filters
        if 'category' in filters:
            query += " AND category = %s"
        if 'publish_date' in filters:
            query += " AND publish_date >= %s"
        if 'upvote' in filters:
            query += " AND upvote > %s"
        
        # Apply search parameters
        if 'title' in searches:
            query += " AND title LIKE %s"
        if 'keyword' in searches:
            query += " AND (title LIKE %s OR content LIKE %s)"
        if 'author' in searches:
            query += " AND author LIKE %s"

        params = []
        if 'category' in filters:
            params.append(filters['category'])
        if 'publish_date' in filters:
            # Convert date to MySQL DATETIME format
            publish_date = datetime.strptime(filters['publish_date'], '%Y-%m-%dT%H:%M:%SZ')
            params.append(publish_date.strftime('%Y-%m-%d %H:%M:%S'))
        if 'upvote' in filters:
            params.append(int(filters['upvote']))
        if 'title' in searches:
            params.append(f"%{searches['title']}%")
        if 'keyword' in searches:
            params.extend([f"%{searches['keyword']}%", f"%{searches['keyword']}%"])
        if 'author' in searches:
            params.append(f"%{searches['author']}%")

        cur = mysql.connection.cursor()
        cur.execute(query, params)
        shorts = cur.fetchall()
        cur.close()

        if not shorts:
            return jsonify({"status": "No short matches your search criteria", "status_code": 400})

        short_list = [{
            "short_id": short[0],
            "category": short[1],
            "title": short[2],
            "author": short[3],
            "publish_date": str(short[4]),
            "content": short[5],
            "actual_content_link": short[6],
            "image": short[7],
            "votes": {
                "upvote": short[8],
                "downvote": short[9]
            },
            "contains_title": 'title' in searches,
            "contains_content": 'keyword' in searches,
            "contains_author": 'author' in searches
        } for short in shorts]

        return jsonify(short_list)

    return jsonify({"status": "Invalid method", "status_code": 405})

if __name__ == '__main__':
    app.run(debug=True)
