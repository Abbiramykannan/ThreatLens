import pandas as pd
import nltk
import re
import string
import joblib
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Download NLTK resources
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('wordnet')

# ✅ Read and filter only valid rows
valid_rows = []
with open('Spam.csv', 'r', encoding='latin-1', errors='ignore') as file:
    for line in file:
        if line.count(',') >= 1:  # Expect at least 1 comma for "file,message"
            valid_rows.append(line)

# Save valid rows to a temporary cleaned CSV
with open('clean_spam.csv', 'w', encoding='latin-1') as clean_file:
    clean_file.writelines(valid_rows)

# Now safely load it
df = pd.read_csv('clean_spam.csv', names=['file', 'message'], usecols=[0, 1])
print("✅ Cleaned dataset loaded with shape:", df.shape)

# Label spam = 1, ham = 0
df['label'] = df['file'].apply(lambda x: 1 if 'spam' in str(x).lower() else 0)

# Email cleaning
def clean_email_body(text):
    text = re.sub(r"^(From:|To:|Subject:|Date:|Message-ID:|X-.*|MIME-Version:|Content-.*)", "", str(text), flags=re.MULTILINE)
    text = re.sub(r"\s+", " ", text).strip()
    return text

df['clean_message'] = df['message'].apply(clean_email_body)

# Preprocessing: stopwords + lemmatization
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

def preprocess(text):
    tokens = nltk.word_tokenize(text.lower())
    tokens = [t for t in tokens if t not in stop_words and t not in string.punctuation]
    lemmatized = [lemmatizer.lemmatize(t) for t in tokens]
    return " ".join(lemmatized)

df['clean_message'] = df['clean_message'].apply(preprocess)

# Train/test split
X = df['clean_message']
y = df['label']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Pipeline
pipeline = Pipeline([
    ('tfidf', TfidfVectorizer(max_features=3000)),
    ('clf', MultinomialNB())
])

# Train
pipeline.fit(X_train, y_train)

# Evaluate
accuracy = accuracy_score(y_test, pipeline.predict(X_test))
print(f"🎯 Model Accuracy: {accuracy:.4f}")

# Save model
joblib.dump(pipeline, 'spam_model.pkl')
print("✅ Model saved as spam_model.pkl")



df = pd.read_csv('Spam.csv')
print(df)