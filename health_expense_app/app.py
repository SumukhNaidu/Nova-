from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from functools import wraps
from analyzer import analyze_expenses, generate_charts, add_expense_record, get_user_name, USERS_PATH
from datetime import datetime
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = 'super_secret_health_key'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

@app.template_filter('inr')
def inr_format(value):
    try:
        value = float(value)
        num_str = str(int(value))
        if len(num_str) > 3:
            last_3 = num_str[-3:]
            other = num_str[:-3]
            other = ','.join([other[max(0, i-2):i] for i in range(len(other), 0, -2)][::-1])
            formatted = f"{other},{last_3}"
        else:
            formatted = num_str
        decimals = "{:.2f}".format(value).split('.')[-1]
        return f"{formatted}.{decimals}"
    except (ValueError, TypeError):
        return value

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if os.path.exists(USERS_PATH):
            users = pd.read_csv(USERS_PATH)
            user = users[(users['username'] == email) & (users['password'] == password)]
            if not user.empty:
                session['user_id'] = str(user.iloc[0]['user_id'])
                return redirect(url_for('dashboard'))
        error = 'Invalid credentials or user does not exist.'
    return render_template('login.html', error=error)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        users = pd.DataFrame(columns=['user_id', 'username', 'password', 'profile_name'])
        if os.path.exists(USERS_PATH):
            users = pd.read_csv(USERS_PATH)
            
        if email in users['username'].values:
            error = 'Email already registered.'
        else:
            new_id = str(len(users) + 1)
            new_user = pd.DataFrame([{'user_id': new_id, 'username': email, 'password': password, 'profile_name': name}])
            users = pd.concat([users, new_user], ignore_index=True)
            users.to_csv(USERS_PATH, index=False)
            session['user_id'] = new_id
            return redirect(url_for('dashboard'))
            
    return render_template('signup.html', error=error)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    user_id = session['user_id']
    chart_filename = generate_charts(user_id)
    analysis = analyze_expenses(user_id)
    patient_name = get_user_name(user_id)
    return render_template('dashboard.html', analysis=analysis, chart_filename=chart_filename, patient_name=patient_name)

@app.route('/add_expense', methods=['GET', 'POST'])
@login_required
def add_expense():
    user_id = session['user_id']
    if request.method == 'POST':
        date = request.form.get('expense-date', datetime.today().strftime('%Y-%m-%d'))
        category = request.form.get('category', 'Miscellaneous')
        amount = request.form.get('cost', 0)
        description = request.form.get('description', '')
        add_expense_record(user_id, date, category, amount, description)
        generate_charts(user_id)
        return redirect(url_for('history'))
        
    patient_name = get_user_name(user_id)
    return render_template('add_expense.html', patient_name=patient_name)

@app.route('/history')
@login_required
def history():
    user_id = session['user_id']
    analysis = analyze_expenses(user_id)
    expenses = analysis.get('recent_expenses', [])
    patient_name = get_user_name(user_id)
    return render_template('history.html', expenses=expenses, patient_name=patient_name, analysis=analysis)

@app.route('/api/chat', methods=['POST'])
@login_required
def api_chat():
    user_id = session.get('user_id')
    data = request.get_json()
    prompt = data.get('prompt', '')
    from analyzer import chat_with_patient
    response = chat_with_patient(user_id, prompt)
    return jsonify({"response": response})

@app.route('/advisor')
@login_required
def advisor():
    user_id = session['user_id']
    patient_name = get_user_name(user_id)
    return render_template('advisor.html', patient_name=patient_name)

@app.route('/insurance')
@login_required
def insurance():
    user_id = session['user_id']
    patient_name = get_user_name(user_id)
    from analyzer import analyze_expenses
    analysis = analyze_expenses(user_id)
    return render_template('insurance.html', patient_name=patient_name, analysis=analysis)

if __name__ == '__main__':
    app.run(debug=True, port=5000)

