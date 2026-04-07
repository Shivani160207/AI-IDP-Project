from flask import Flask, render_template, request, redirect, session 
from flask_sqlalchemy import SQLAlchemy
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
import matplotlib.pyplot as plt
import os

from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy

# Training data
skills_data = [
    "python statistics machine learning pandas",
    "python deep learning tensorflow ai",
    "html css javascript react web",
    "javascript html css frontend",
    "machine learning python ai",
    "react javascript web development"
]

labels = [
    "data scientist",
    "ai engineer",
    "web developer",
    "web developer",
    "ai engineer",
    "web developer"
]
vectorizer = CountVectorizer()
X = vectorizer.fit_transform(skills_data)

model = MultinomialNB()
model.fit(X, labels)
app = Flask(__name__)

import os
basedir = os.path.abspath(os.path.dirname(__file__))

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'users.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

with app.app_context():
    db.create_all()
app.secret_key = "secret123"
@app.route('/')
def home():
    if 'user' not in session:
        return redirect('/login')
    return render_template('form.html')
@app.route('/login', methods=['GET','POST'])
def login():
    error = None

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username, password=password).first()

        if user:
            session['user'] = username
            return redirect('/')
        else:
            error = "Invalid username or password"

    return render_template('login.html', error=error)
    
@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()

        return redirect('/login')   # after signup go to login

    return render_template('signup.html')
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/login')
@app.route('/result', methods=['POST'])
def result():
    skills = [skill.strip().lower() for skill in request.form['skills'].split(',') if skill.strip()]
    skills_input = request.form['skills']
    goal_input = request.form.get('goal', '').strip().lower()

    X_input = vectorizer.transform([skills_input])
    predicted_goal = model.predict(X_input)[0]

    goal = goal_input if goal_input else predicted_goal
    if 'user' not in session:
        return redirect('/login')
    # Normalize goal
    if "data" in goal:
        goal = "data scientist"
    elif "web" in goal:
        goal = "web developer"
    elif "ai" in goal:
        goal = "ai engineer"

    skill_map = {
        "data scientist": ["python", "statistics", "machine learning", "pandas"],
        "web developer": ["html", "css", "javascript", "react"],
        "ai engineer": ["python", "machine learning", "deep learning", "tensorflow"]
    }

    course_map = {
        "python": ("Python for Beginners", "https://www.coursera.org/learn/python"),
        "statistics": ("Statistics for Data Science", "https://www.udemy.com/course/statistics-for-data-science"),
        "machine learning": ("Machine Learning by Andrew Ng", "https://www.coursera.org/learn/machine-learning"),
        "pandas": ("Data Analysis with Pandas", "https://www.coursera.org/projects/data-analysis-pandas")
    }

    # ✅ INITIALIZE EVERYTHING (VERY IMPORTANT)
    required_skills = []
    missing_skills = []
    recommended_courses = []
    recommendation = "Goal not recognized"

    if goal in skill_map:
        required_skills = skill_map[goal]

        missing_skills = [skill for skill in required_skills if skill not in skills]

        if missing_skills:
            recommendation = f"You need to learn: {', '.join(missing_skills)}"
        else:
            recommendation = "You are ready! Start building projects."

        recommended_courses = [course_map.get(skill, ("Course", "#")) for skill in missing_skills]


    learned_count = len(required_skills) - len(missing_skills)
    missing_count = len(missing_skills)

    labels = ['Learned Skills', 'Missing Skills']
    values = [learned_count, missing_count]
    colors = ['#22c55e', '#ef4444']

    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(8, 4.8))
    bars = ax.barh(labels, values, color=colors, height=0.55)

    ax.set_title("Skill Gap Analysis", fontsize=16, fontweight='bold', color='#352f73', pad=15)
    ax.set_xlabel("Number of Skills", fontsize=11, color='#4b5563')
    ax.set_xlim(0, max(len(required_skills), 1))
    ax.set_facecolor('#f8f7ff')
    fig.patch.set_facecolor('#ffffff')

    for bar, value in zip(bars, values):
        ax.text(
            bar.get_width() + 0.05,
            bar.get_y() + bar.get_height() / 2,
            str(value),
            va='center',
            fontsize=11,
            fontweight='bold',
            color='#1f2340'
        )

    for spine in ['top', 'right', 'left']:
        ax.spines[spine].set_visible(False)

    ax.tick_params(axis='y', labelsize=11, colors='#1f2340')
    ax.tick_params(axis='x', colors='#4b5563')
    plt.tight_layout()

    os.makedirs("static", exist_ok=True)
    graph_path = "static/graph.png"
    plt.savefig(graph_path, dpi=200, bbox_inches='tight')
    plt.close()

    return render_template('result.html',
                           rec=recommendation,
                           missing=missing_skills,
                           required=required_skills,
                           courses=recommended_courses,
                           graph=graph_path,
                           goal=goal)
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

