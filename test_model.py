import joblib
from utils import preprocess_text

# Load trained model and vectorizer
model = joblib.load("model/spam_model.pkl")
vectorizer = joblib.load("vectorizer/vectorizer.pkl")

# Sample test messages
test_messages = [
    "Congratulations! You have won a free ticket to Bahamas. Call now!",
    "Hi, are we still meeting for coffee today?",
    "FREE entry in 2 a weekly competition to win FA Cup final tkts. Text FA to 87121 to receive entry question(std txt rate)",
    "Your mobile number has won 1000000 pounds. To claim call 09061701461 now!",
    "I'll call you later when I'm free."
]

# Run prediction
for msg in test_messages:
    processed = preprocess_text(msg)
    vectorized = vectorizer.transform([processed])
    prediction = model.predict(vectorized)[0]
    label = "Spam ❌" if prediction == 1 else "Ham ✅"
    print(f"📧 Message: {msg}\n🔍 Result: {label}\n")
