
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, TextAreaField, FileField, SubmitField
from wtforms.validators import DataRequired
from werkzeug.utils import secure_filename
import random, os, uuid

app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///applications.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 15 * 1024 * 1024

# Flask-Mail config
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'thessaly.it.apps@gmail.com'
app.config['MAIL_PASSWORD'] = 'kclv qmdy mlcf lftr'
mail = Mail(app)

db = SQLAlchemy(app)
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    age = db.Column(db.Integer)
    description = db.Column(db.Text)
    filename = db.Column(db.String(300))

class ApplicationForm(FlaskForm):
    name = StringField('Όνομα', validators=[DataRequired()])
    age = IntegerField('Ηλικία', validators=[DataRequired()])
    description = TextAreaField('Περιγραφή', validators=[DataRequired()])
    file1 = FileField('Αρχείο 1', validators=[DataRequired()])
    file2 = FileField('Αρχείο 2', validators=[DataRequired()])
    file3 = FileField('Αρχείο 3', validators=[DataRequired()])
    submit = SubmitField('Υποβολή')

with app.app_context():
    db.create_all()
    
    
from flask import send_from_directory

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    

@app.route('/send_otp', methods=['GET', 'POST'])
def send_otp():
    if request.method == 'POST':
        email = request.form['email']
        otp = str(random.randint(100000, 999999))
        session['otp'] = otp
        session['email'] = email
        msg = Message('OTP Verification', sender='your_email@gmail.com', recipients=[email])
        msg.body = f'Your OTP is: {otp}'
        mail.send(msg)
        flash('OTP sent to your email.', 'info')
        return redirect(url_for('verify_otp'))
    return render_template('send_otp.html')

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        user_otp = request.form['otp']
        if user_otp == session.get('otp'):
            session['verified'] = True
            flash('Email verified successfully!', 'success')
            return redirect(url_for('form'))
        else:
            flash('Invalid OTP. Please try again.', 'danger')
    return render_template('verify_otp.html')

@app.route('/', methods=['GET', 'POST'])
def form():
    if not session.get('verified'):
        return redirect(url_for('send_otp'))
    form = ApplicationForm()
    error_message = None
    if form.validate_on_submit():
        files = [form.file1.data, form.file2.data, form.file3.data]
        total_size = 0
        filenames = []
        for file in files:
            if file and allowed_file(file.filename):
                file_size = len(file.read())
                total_size += file_size
                file.seek(0)
            else:
                error_message = 'Μη αποδεκτός τύπος αρχείου.'
                return render_template('form.html', form=form, error_message=error_message)
        if total_size > 15 * 1024 * 1024:
            error_message = 'Το συνολικό μέγεθος αρχείων ξεπερνά τα 15MB.'
            return render_template('form.html', form=form, error_message=error_message)
        for file in files:
            filename = secure_filename(f"{uuid.uuid4().hex}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            file.save(filepath)
            filenames.append(filename)
        new_app = Application(
            name=form.name.data,
            age=form.age.data,
            description=form.description.data,
            filename=', '.join(filenames)
        )
        db.session.add(new_app)
        db.session.commit()
        flash('Η αίτηση υποβλήθηκε επιτυχώς!', 'success')
        return redirect(url_for('form'))
    return render_template('form.html', form=form, error_message=error_message)

@app.route('/applications')
def applications():
    all_apps = Application.query.all()
    return render_template('applications.html', apps=all_apps)

if __name__ == '__main__':
    app.run(debug=True)
