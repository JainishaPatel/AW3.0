from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import requests  # For fetching weather data
import pandas as pd
import os
from datetime import datetime  # Import datetime module



app = Flask(__name__)
app.secret_key = 'supersecretkey123456'    # app.secret_key = 'YOUR_SECRET_KEY'

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/agricultureDB')
db = client['agricultureDB']
users = db['users']
contact_collection = db['contacts']  # Collection for storing contact info




# Home route
@app.route('/')
def home():
    return redirect(url_for('dashboard'))



# Signup route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        
        # Check if user exists
        existing_user = users.find_one({'username': username})
        if existing_user:
            return 'Username already exists! Try logging in.'
        
        existing_email = users.find_one({'email': email})
        if existing_email:
            return 'Gmail already exists! Try logging in.'
        
        users.insert_one({'username': username, 'email': email, 'password': hashed_password})
        return redirect(url_for('login'))
    return render_template('signup.html')



# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        user = users.find_one({'username': username, 'email': email})
        if user and check_password_hash(user['password'], password):
            session['username'] = username
            session['email'] = email
            return redirect(url_for('dashboard'))  # Redirect to dashboard after login
            
           
        return 'Invalid credentials! Please try again.'
    
    return render_template('login.html')



# Dashboard route
@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        return render_template('dashboard.html')
    return redirect(url_for('login'))




# Weather route
@app.route('/weather', methods=['GET', 'POST'])
def weather():
    weather_data = None
    if request.method == 'POST':
        city = request.form['city']
        # Replace YOUR_API_KEY with your actual weather API key
        api_key = "bfded00eb9ee818074bc2745de187c87"           # api_key = "YOUR_API_KEY"  https://openweathermap.org/api
        response = requests.get(f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric")  
        weather_data = response.json()
        
        if weather_data['cod'] != 200:
            return 'City not found! Please try again.'
        
        # Get the current date and time
        current_time = datetime.now().strftime("%d-%m-%y %H:%M")  # Format: DD-MM-YYYY HH:MM
        
        weather_data = {
            'city': weather_data['name'],
            'temp': weather_data['main']['temp'],
            'condition': weather_data['weather'][0]['description'],
            'humidity': weather_data['main']['humidity'],  # Humidity field
            'wind_speed': weather_data['wind']['speed'],    # Wind speed field
            'datetime': current_time,  # Add date and time
        }

    return render_template('weather.html', weather=weather_data)



# Crop prediction route
@app.route('/crop_prediction', methods=['GET', 'POST'])
def crop_prediction():
    prediction = None
    crop_data = pd.read_csv('crops.csv')  # Ensure you provide the correct path to your CSV

    if request.method == 'POST':
        city = request.form['city']
        weather_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid=bfded00eb9ee818074bc2745de187c87&units=metric"  # Replace with your API key
        response = requests.get(weather_url)
        weather_data = response.json()

        # Extract relevant weather data
        if weather_data and weather_data.get('main'):
            temperature = weather_data['main']['temp']
            humidity = weather_data['main']['humidity']

            # Filter crops based on temperature and humidity conditions
            prediction = crop_data[
                (crop_data['Ideal_Temperature_Min'] <= temperature) & 
                (crop_data['Ideal_Temperature_Max'] >= temperature) & 
                (crop_data['Ideal_Humidity_Min'] <= humidity)& 
                (crop_data['Ideal_Humidity_Max'] >= humidity)]

    return render_template('crop_prediction.html', prediction=prediction.to_dict(orient='records') if prediction is not None else None)



# about route
@app.route('/about')
def about():
    return render_template('about.html')



# multilanguage route
@app.route('/multilanguage')
def multilanguage():
    return render_template('multilanguage.html')



# contact route
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        
        # Store the contact information in MongoDB
        contact_info = {
            'name': name,
            'email': email,
            'message': message
        }
        
        contact_collection.insert_one(contact_info)  # Insert the contact info
        
        return redirect(url_for('dashboard'))  # Redirect to the dashboard after submission
    return render_template('contact.html') # Render contact page for GET requests



# Logout route
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))



if __name__ == '__main__':
    app.run(debug=True)
