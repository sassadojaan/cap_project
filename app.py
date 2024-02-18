from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import date
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField, DateField, validators, PasswordField, SelectField
from wtforms.validators import Email, ValidationError
from email_validator import validate_email
from flask_wtf.file import FileField, FileAllowed, FileRequired
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mycaps.db'
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = '/home/sass/projekt/static/pics'
db = SQLAlchemy(app)

migrate = Migrate(app,db)

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(40), nullable=False)
    password = db.Column(db.String(20), nullable=False)
    collections = db.relationship('Collection', backref='user', lazy=True) 
    
class UserReg(FlaskForm):
    name = StringField('Nimi', validators=[validators.DataRequired(), validators.Regexp('^[A-Za-z0-9_ ]+$')])
    username = StringField('Kasutajatunnus', validators=[validators.DataRequired(), validators.Length(min=6, max=20)])
    email = StringField('E-posti aadress', validators=[validators.DataRequired(), validators.Email()])
    password = PasswordField('Parool', validators=[validators.DataRequired(), validators.Length(min=8, max=20)])
    confirmpassword = PasswordField('Korda parooli', validators=[validators.EqualTo('password')])
    submit = SubmitField('Registreeri')
    
class UserLogin(FlaskForm):
    username = StringField('Kasutajatunnus', validators=[validators.DataRequired(), validators.Length(min=6, max=20)])
    password = PasswordField('Parool', validators=[validators.DataRequired(), validators.Length(min=8, max=20)])
    submit = SubmitField('Login')

def authenticate_user(username, password):
    user = Users.query.filter_by(username=username).first()
    if user and check_password_hash(user.password, password):
        # User authentication successful
        session['username'] = user.username
        session['name'] = user.name 
        session['user_id'] = user.id 
        return True
    else:
        session['message'] = 'Ebaõnnestunud login'
        return False

class Collection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  
    collectibles = db.relationship('Collectible', backref='collection', lazy=True)

class SubmitCollection(FlaskForm):
    name = StringField('Kollektsiooni nimi', validators=[validators.DataRequired()])
    submit = SubmitField('Salvesta')
        
class Collectible(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    team = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(300))
    place_aquired = db.Column(db.String(150))
    cost = db.Column(db.Float, nullable=True)
    date_aquired = db.Column(db.Date, nullable=True)
    picture = db.Column(db.String)
    collection_id = db.Column(db.Integer, db.ForeignKey('collection.id'), nullable=False)
    
class SubmitCollectible(FlaskForm):
    collection_id = SelectField('Kollektsioon', coerce=int)
    name = StringField('Nimi', validators=[validators.DataRequired()])
    team = StringField('Tiim')
    description = StringField('Kirjeldus')
    place_aquired = StringField('Hankimise koht')
    cost = FloatField('Hind')
    date_aquired = DateField('Hankimise kuupäev')
    picture = FileField('Pilt', validators=[FileRequired(), FileAllowed(['jpg', 'png'], 'Images only!')])
    submit = SubmitField('Salvesta')

class SubmitSearch(FlaskForm):
    user_id = SelectField('Kasutajatunnus', coerce=int)
    search_text = StringField('Otsing')
    submit = SubmitField('Otsi')
        
@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/')
def front():
    return render_template('front.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = UserReg()
    if form.validate_on_submit():
        # Process the form data and save the file
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = form.password.data
        hashed_password = generate_password_hash(password)
        new_entry = Users(name=name, username=username, email=email, password=hashed_password)
        db.session.add(new_entry)
        db.session.commit()
        
        return redirect(url_for('front'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = UserLogin()
    if form.validate_on_submit():
        # Process the form data and save the file
        username = form.username.data
        password = form.password.data
        
        login_success = authenticate_user(username, password)
        if login_success:
            return render_template('front.html')  # Render success template
        else:
            return render_template('login.html', form=form) 
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    session.clear()  
    return redirect(url_for('front'))

@app.route('/search', methods=['GET', 'POST'])
def search():
    form = SubmitSearch()
    users = Users.query.all()
    form.user_id.choices = [(user.id, user.name) for user in users]
    return render_template('search.html', form=form)

@app.route('/collection', methods=['GET', 'POST'])
def collection():
    form = SubmitCollection()
    user_id=session['user_id']
    user = Users.query.get(user_id)
    if form.validate_on_submit():
        name = form.name.data
        new_entry = Collection(name=name, user_id=user_id)
        db.session.add(new_entry)
        db.session.commit()
        session['message'] = 'Lisati kollektsioon ' + name
        return redirect(url_for('front'))
    return render_template('collection.html', form=form, user=user)    

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    form = SubmitCollectible()
    user_id = session.get('user_id')
    collections = Collection.query.filter_by(user_id=user_id).all()
    form.collection_id.choices = [(collection.id, collection.name) for collection in collections]
    if form.validate_on_submit():
        # Process the form data and save the file
        collection_id = form.collection_id.data
        name = form.name.data
        team = form.team.data
        description = form.description.data
        place_aquired = form.place_aquired.data
        cost = form.cost.data
        date_aquired = form.date_aquired.data
        picture = form.picture.data
        filename = secure_filename(picture.filename)
        picture.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Save the form data and filename to the database
        new_entry = Collectible(collection_id=collection_id, name=name, team=team, description=description, place_aquired=place_aquired, cost=cost, date_aquired=date_aquired, picture=filename)
        db.session.add(new_entry)
        db.session.commit()

        return redirect(url_for('front'))  # Redirect after successful upload , will add "Successfully uploaded!" html page
    return render_template('upload.html', form=form)

@app.route('/all/<int:collection_id>')
def all(collection_id):
    all_collectibles = Collectible.query.filter(Collectible.collection_id == collection_id).all()
    name_object = Collection.query.filter(Collection.id == collection_id).first()
    if name_object:
        name = name_object.name
    return render_template('all.html', all_collectibles=all_collectibles, name=name)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=8885,host='0.0.0.0')