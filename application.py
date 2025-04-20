import os
from flask import Flask, request, redirect, render_template, jsonify, send_file
import boto3
#from flask_mysqldb import MySQL
import mysql.connector
import mysql
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

# Configure MySQL
app.config['MYSQL_HOST'] = 'database-1.cjgkq0i0mjpn.us-west-2.rds.amazonaws.com'
app.config['MYSQL_USER'] = 'admin'
app.config['MYSQL_PASSWORD'] = '80176366Ps*'
app.config['MYSQL_DB'] = 'demodata'


try:
    connection = mysql.connector.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        database=app.config['MYSQL_DB']
    )
    
    if connection.is_connected():
        print(f"Connected to database {app.config['MYSQL_DB']} on {app.config['MYSQL_HOST']}")
        print(mysql.__file__)
except mysql.connector.Error as e:
    print(f"Error connecting to MySQL database: {e}")


#mysql = MySQL(app)
#print("Hellooooo")
# Configure S3
S3_BUCKET = os.environ.get("S3_BUCKET")
S3_KEY = os.environ.get("S3_KEY")
S3_SECRET = os.environ.get("S3_SECRET")

# Initialize boto3 S3 client
s3_client = boto3.client('s3', aws_access_key_id=S3_KEY, aws_secret_access_key=S3_SECRET)

#cursor = connection.cursor()
@app.route('/')
def index():
    #return 'Helloooooo'
    return render_template('landing.html')
    print("helloooo")
@app.route('/search', methods=['GET'])
def search():
    #if request.method == 'POST':
    phone_number = request.args.get('phone_number')
    print("Reached /search route")
    print(f"search for number:{phone_number}")
    #print("####################################################")
    if not phone_number:
        return render_template('search.html')
        #return jsonify({"error": "Phone number is required"}), 400
    try:
     with connection.cursor(dictionary=True) as cursor:
      cursor.execute("SELECT * FROM users WHERE phone_number = %s", (phone_number,))
      user = cursor.fetchone()
      print(f"quer:{user}")
      
    #print(f"{phone_number}")
      if user is None:
        #return jsonify({"error": "User not found"}), 404
         return render_template('search.html', error="User not found.")
    # Fetch the file from S3
      #file_key = user['pdf_url']
      file_key = user['pdf_url'].split('.com/')[1]
      print(f"File key from DB: {file_key}")
      try:
        s3_file = s3_client.get_object(Bucket=S3_BUCKET, Key=file_key)
        file_content = s3_file['Body'].read()
        file_url = s3_client.generate_presigned_url('get_object', Params={'Bucket': S3_BUCKET, 'Key': file_key}, ExpiresIn=3600)  # URL valid for 1 hour
        return render_template('search.html', user=user, file_url=file_url)
        #return jsonify({"error": "File not found in S3"}), 404
        #return render_template('search.html', error="File not found in S3.")
      except s3_client.exceptions.NoSuchKey:
        return render_template('search.html', error="File not found in S3.")
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
        return render_template('search.html', error="Database error occurred.")
      #return jsonify({
        #"name": user['name'],
        #"phone_number": user['phone_number'],
        #"file_url": file_url
    #})
    #return render_template('search.html', user=user, file_url=file_url) 
    #except mysql.connector.Error as e:
     #   return jsonify({"error": f"Database error: {e}"}), 500 
    #return render_template('search.html')

@app.route('/upload', methods=['GET','POST'])
def upload():
    if request.method == 'GET':
        return render_template('index.html')
    if 'file' not in request.files:
        return "No file part", 400

    file = request.files['file']
    name = request.form['name']
    ExamDate = request.form['ED']
    phone_number = request.form['phone_number']

    if file.filename == '':
        return "No selected file", 400

    # Upload PDF file to S3
    try:
        s3_file_key = f"uploads/{file.filename.replace(' ', '_')}"
        s3_client.upload_fileobj(file, S3_BUCKET, s3_file_key, ExtraArgs={'ACL': 'public-read'})

        # Get the public URL of the uploaded file
        pdf_url = f"https://{S3_BUCKET}.s3.amazonaws.com/{s3_file_key}"
        
        # Store the user data in the MySQL database
        
        #print(cursor)
        with connection.cursor() as cursor:
         cursor.execute('INSERT INTO users (name, phone_number, pdf_url, Examination_Date) VALUES (%s, %s, %s, %s)', (name, phone_number, pdf_url, ExamDate))
         connection.commit()

        return "File successfully uploaded and data stored", 200
    except Exception as e:
        return f"Error uploading file: {str(e)}", 500
application = app
if __name__ == '_main_':
    app.run(debug=True)