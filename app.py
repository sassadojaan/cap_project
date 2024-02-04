from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import date
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField, DateField, validators
from flask_wtf.file import FileField, FileAllowed, FileRequired
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mycaps.db'
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = '/home/sass/projekt/static/pics'
db = SQLAlchemy(app)

class Collectible(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    team = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(300))
    place_aquired = db.Column(db.String(150))
    cost = db.Column(db.Float, nullable=True)
    date_aquired = db.Column(db.Date, nullable=True)
    picture = db.Column(db.String)

class SubmitForm(FlaskForm):
    name = StringField('Nimi', validators=[validators.DataRequired()])
    team = StringField('Tiim')
    description = StringField('Kirjeldus')
    place_aquired = StringField('Hankimise koht')
    cost = FloatField('Hind')
    date_aquired = DateField('Hankimise kuupäev')
    picture = FileField('Pilt', validators=[FileRequired(), FileAllowed(['jpg', 'png'], 'Images only!')])
    submit = SubmitField('Salvesta')
    
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    form = SubmitForm()
    if form.validate_on_submit():
        # Process the form data and save the file
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
        new_entry = Collectible(name=name, team=team, description=description, place_aquired=place_aquired, cost=cost, date_aquired=date_aquired, picture=filename)
        db.session.add(new_entry)
        db.session.commit()

        return redirect(url_for('index'))  # Redirect after successful upload
    return render_template('upload.html', form=form)

@app.route('/all')
def all():
    all_collectibles = Collectible.query.all()
    return render_template('all.html', all_collectibles=all_collectibles)
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=8885,host='0.0.0.0')