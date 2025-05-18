from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:3001"}})
from flask_cors import CORS
import pandas as pd
import joblib
import ast
import os
from openai import OpenAI
import textwrap
import re
from datetime import datetime, timedelta
import urllib.parse
from collections import defaultdict

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure Ollama client
client = OpenAI(
    base_url='http://localhost:11434/v1',
    api_key='ollama'  # Required placeholder
)

# Load models and data
backend_path = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(backend_path, "model1", "model1.pkl")
encoder_path = os.path.join(backend_path, "model1", "label_encoder.pkl")

model = joblib.load(model_path)
le = joblib.load(encoder_path)

# Load datasets
data = pd.read_csv('data/Training-1.csv')
description = pd.read_csv('data/description.csv')
workout = pd.read_csv('data/Workout-1.csv')
diets = pd.read_csv('data/Diet-1.csv')
medicines = pd.read_csv('data/Medication-1.csv')
precautions = pd.read_csv('data/Precaution-1.csv')
medical_stores = pd.read_csv('data/clean_medical_stores_all_pincodes.csv')

# Load symptom synonyms
try:
    mapping_df = pd.read_csv('data/symptom_synonym_mappings.csv')
    SYMPTOM_SYNONYMS = defaultdict(list)
    for _, row in mapping_df.iterrows():
        SYMPTOM_SYNONYMS[row["General_Symptom"]].append(row["Specific_Symptom"])
except Exception as e:
    print(f"⚠️ Symptom synonyms not loaded: {e}")
    SYMPTOM_SYNONYMS = defaultdict(list)

def get_symptom_vector(user_input, symptom_columns):
    symptoms = [s.strip().lower() for s in user_input.split(',')]
    expanded_symptoms = set(symptoms)
    for sym in symptoms:
        expanded_symptoms.update(SYMPTOM_SYNONYMS.get(sym, []))
    return [1 if col in expanded_symptoms else 0 for col in symptom_columns]

def parse_diet_plan(diet_text):
    day_plans = {}
    current_day = None
    for line in diet_text.split('\n'):
        day_match = re.search(r'day\s*(\d+)', line.lower())
        if day_match:
            current_day = int(day_match.group(1))
            day_plans[current_day] = {'breakfast': '', 'lunch': '', 'dinner': ''}
        elif current_day:
            if 'breakfast' in line.lower():
                day_plans[current_day]['breakfast'] = line.split(':', 1)[-1].strip()
            elif 'lunch' in line.lower():
                day_plans[current_day]['lunch'] = line.split(':', 1)[-1].strip()
            elif 'dinner' in line.lower():
                day_plans[current_day]['dinner'] = line.split(':', 1)[-1].strip()
    return day_plans

def parse_workout_plan(workout_text):
    day_workouts = {}
    current_day = None
    for line in workout_text.split('\n'):
        day_match = re.search(r'day\s*(\d+)', line.lower())
        if day_match:
            current_day = int(day_match.group(1))
            day_workouts[current_day] = ''
        elif current_day and 'workout' in line.lower():
            day_workouts[current_day] = line.split(':', 1)[-1].strip()
    return day_workouts

def generate_ai_content(prompt, fallback_data, disease, content_type):
    try:
        response = client.chat.completions.create(
            model="llama3.2",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1500
        )
        content = response.choices[0].message.content
        return parse_diet_plan(content) if content_type == 'diet' else parse_workout_plan(content)
    except Exception as e:
        print(f"⚠️ AI {content_type} Generation Failed: {e}")
        return fallback_data[fallback_data['Disease'].str.lower() == disease.lower()].iloc[0][content_type]

def generate_gcal_url(title, description, start_time):
    start_str = start_time.strftime('%Y%m%dT%H%M%S')
    end_str = (start_time + timedelta(minutes=30)).strftime('%Y%m%dT%H%M%S')
    base_url = "https://calendar.google.com/calendar/u/0/r/eventedit?"
    params = {
        'text': title,
        'details': description,
        'dates': f"{start_str}/{end_str}",
        'ctz': 'Asia/Kolkata'
    }
    return base_url + urllib.parse.urlencode(params)

@app.route('/predict', methods=['POST'])
def predict():
    req_data = request.json
    symptoms = req_data['symptoms']
    pincode = req_data['pincode']

    # Generate symptom vector
    symptom_columns = list(data.columns[:-1])
    symptom_vector = get_symptom_vector(symptoms, symptom_columns)
    symptom_vector_df = pd.DataFrame([symptom_vector], columns=symptom_columns)

    # Predict disease
    predicted_label = model.predict(symptom_vector_df)[0]
    predicted_disease = le.inverse_transform([predicted_label])[0]

    # Get description
    desc_row = description[description['Disease'].str.lower() == predicted_disease.lower()]
    desc = desc_row['Description'].values[0] if not desc_row.empty else 'No description available'

    # Medications
    meds_df = medicines[medicines['Disease'].str.lower() == predicted_disease.lower()]
    medications = []
    if not meds_df.empty:
        try:
            medications = ast.literal_eval(meds_df.iloc[0]["Medication"])
        except:
            medications = [meds_df.iloc[0]["Medication"]]
    else:
        medications = ['Consult doctor']

    # Precautions
    prec = precautions[precautions['Disease'].str.lower() == predicted_disease.lower()]
    precautions_list = [prec.iloc[0][f'Precaution_{i}'] for i in range(1,5) if pd.notnull(prec.iloc[0].get(f'Precaution_{i}'))]

    # Generate AI content
    symptoms_list = [s.strip().lower() for s in symptoms.split(',')]
    
    diet_prompt = f"""Create a 7-day personalized diet plan for {predicted_disease} with symptoms: {', '.join(symptoms_list)}.
    Format EXACTLY like this:
    # Day 1
    - Breakfast: [meal details]
    - Lunch: [meal details]
    - Dinner: [meal details]
    ..."""
    
    workout_prompt = f"""Create a 7-day morning workout plan for {predicted_disease} with symptoms: {', '.join(symptoms_list)}.
    Format EXACTLY like this:
    # Day 1
    - Morning Workout: [exercise details]
    ..."""
    
    diet_plan = generate_ai_content(diet_prompt, diets, predicted_disease, 'diet')
    workout_plan = generate_ai_content(workout_prompt, workout, predicted_disease, 'workout')

    # Generate calendar links
    calendar_links = []
    today = datetime.now()
    for day in range(1, 8):
        current_date = today + timedelta(days=day-1)
        
        # Breakfast
        breakfast_time = current_date.replace(hour=8, minute=0)
        breakfast_desc = f"Breakfast: {diet_plan.get(day, {}).get('breakfast', '')}"
        calendar_links.append(generate_gcal_url(
            f"Day {day} Breakfast",
            f"{breakfast_desc}\nMedications: {', '.join(medications)}",
            breakfast_time
        ))
        
        # Workout
        workout_time = current_date.replace(hour=7, minute=0)
        workout_desc = f"Workout: {workout_plan.get(day, '')}"
        calendar_links.append(generate_gcal_url(
            f"Day {day} Workout",
            workout_desc,
            workout_time
        ))

    # Medical stores
    stores = medical_stores[medical_stores['Pincode'] == int(pincode)]
    pharmacies = stores[['Medical Store Name', 'Address']].head(3).to_dict('records')

    return jsonify({
        'disease': predicted_disease,
        'description': desc,
        'medications': medications,
        'precautions': precautions_list,
        'diet': diet_plan,
        'workout': workout_plan,
        'calendar_links': calendar_links,
        'pharmacies': pharmacies
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)