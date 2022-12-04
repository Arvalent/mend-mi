from flask import Flask, request, flash, url_for, redirect, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.db'
app.config['SECRET_KEY'] = "random string"

db = SQLAlchemy(app)


class Users(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(100))
	visited_places_id = db.Column(db.String(50))
	addr = db.Column(db.String(200))
	pin = db.Column(db.String(10))

	def __init__(self, id, name, city, addr, pin):
		self.id = id
		self.name = name
		self.city = city
		self.addr = addr
		self.pin = pin


@app.route('/new/<int:student_id>', methods=['GET', 'POST'])
def new(student_id):
	if request.method == 'POST':
		if not request.json["name"] or not request.json["city"] or not request.json["addr"]:
			flash('Please enter all the fields', 'error')
		else:
			student = students(student_id, request.json["name"], request.json["city"], request.json["addr"], request.json["pin"])

			db.session.add(student)
			db.session.commit()
			flash('Record was successfully added')
			return {"ADDED": "OK"}
	results = students.query.filter_by(id=student_id).first()
	return {"id": results.id, "name": results.name}


if __name__ == '__main__':
	with app.app_context():
		db.create_all()
	app.run(debug=True)