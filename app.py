from flask import Flask, render_template, request, redirect, session, url_for, flash
import pickle, os, re
from auth import register_user, verify_user, save_scan, get_history
from werkzeug.utils import secure_filename
from utils import preprocess_text
import joblib
from groq import Groq

client = Groq(
    api_key= "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",
)

model = joblib.load("model/spam_model.pkl")
vectorizer = joblib.load("vectorizer/vectorizer.pkl")


app = Flask(__name__)
app.secret_key = 'supersecretkey'

# model = pickle.load(open('model/spam_model.pkl', 'rb'))
# vectorizer = pickle.load(open('vectorizer/vectorizer.pkl', 'rb'))
authorized_domains = ['gmail.com', 'yahoo.com', 'outlook.com']

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def home():
    return redirect(url_for('dashboard')) if 'user_id' in session else redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        if register_user(request.form['username'], request.form['password']):
            flash('Signup successful! Please login.', 'success')
            return redirect(url_for('login'))
        flash('Username already exists.', 'danger')
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = verify_user(request.form['username'], request.form['password'])
        if user_id:
            session['user_id'], session['username'] = user_id, request.form['username']
            return redirect(url_for('dashboard'))
        flash('Invalid credentials.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    result, sender_status = None, None
    if request.method == 'POST':
        sender = request.form['sender']
        content = request.form['content']
        domain = sender.split('@')[-1].lower()
        sender_status = "Authorized ✅" if domain in authorized_domains else "Not Authorized ❌"

        processed = preprocess_text(content)

        chat_completion = client.chat.completions.create(
        messages=[
                {
                    "role": "user",
                    "content": f"You are a spam detection assistant. Analyze the following email content and respond strictly with 'yes' if it is spam or 'no' if it is not. Do not provide any explanation or additional text.\nEmail Content: {processed}"
                }
            ],
        model="llama-3.3-70b-versatile",
        stream=False,
        )

        prediction = chat_completion.choices[0].message.content
        result = "Spam 🚨" if prediction == "yes" else "Ham ✅"
        save_scan(session['user_id'], sender, content, result)

    history = get_history(session['user_id'])
    spam_count = sum(1 for x in history if x[2] == "Spam 🚨")
    ham_count = sum(1 for x in history if x[2] == "Ham ✅")

    return render_template("dashboard.html",
                           result=result,
                           sender_status=sender_status,
                           scan_user=history,
                           spam_count=spam_count,
                           ham_count=ham_count)

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    if not file or file.filename == '':
        flash("No file selected.", "warning")
        return redirect(url_for('dashboard'))

    path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
    file.save(path)

    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    match = re.search(r"From: .*<(.+?)>", content)
    sender = match.group(1) if match else "unknown@example.com"
    domain = sender.split('@')[-1].lower()
    sender_status = "Authorized ✅" if domain in authorized_domains else "Not Authorized ❌"

    processed = preprocess_text(content)
    prediction = model.predict(vectorizer.transform([processed]))[0]
    result = "Spam 🚨" if prediction == "spam" else "Ham ✅"
    save_scan(session['user_id'], sender, content, result)

    flash(f"{sender} → {result} ({sender_status})", "info")
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
