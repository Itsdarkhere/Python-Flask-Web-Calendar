import json
import logging
import random
from datetime import datetime
from flask import Flask, abort
from flask_restful import Resource, Api, reqparse, inputs, marshal_with, fields
from flask_sqlalchemy import SQLAlchemy
from flask import Response
import sys

app = Flask(__name__)
api = Api(app)
parser = reqparse.RequestParser()
parser2 = reqparse.RequestParser()
db = SQLAlchemy(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dates.db'


parser.add_argument(
    'event',
    required=True,
    help="The event name is required!",
)
parser.add_argument(
    'date',
    required=True,
    type=inputs.date,
    help="The event date with the correct format is required! The correct format is YYYY-MM-DD!",
)
# Notice this is a new parser
parser2.add_argument(
    'start_time',
    type=inputs.date,
    help="The event date with the correct format is required! The correct format is YYYY-MM-DD!",
)
parser2.add_argument(
    'end_time',
    type=inputs.date,
    help="The event date with the correct format is required! The correct format is YYYY-MM-DD!",
)


class Mark(db.Model):
    __tablename__ = 'Mark'
    id = db.Column(db.Integer, primary_key=True)
    event = db.Column(db.String, nullable=False)
    date = db.Column(db.Date, nullable=False)


# This is used in the marshalling two define how to process each field
resource_fields = {
    'id':       fields.Integer,
    'event':    fields.String,
    'date':     fields.String
}


# Create random ints that are not in the db
def create_id():
    random_id = random.randint(1, 10000)
    if bool(Mark.query.filter_by(id=random_id).first()):
        create_id()
    else:
        return random_id


class HelloResource(Resource):
    @marshal_with(resource_fields)
    def get(self):
        return Mark.query.filter(Mark.date == str(datetime.today().strftime('%Y-%m-%d'))).all()


class EventResource(Resource):
    @marshal_with(resource_fields)
    def get(self):
        try:
            args = parser2.parse_args()
            return Mark.query.filter(args['start_time'] < Mark.date, Mark.date < args['end_time']).all()
        except Exception:
            return Mark.query.all()

    def post(self):
        args = parser.parse_args()

        event = args['event']
        response = {
            'message': 'The event has been added!',
            'event': event,
            'date': str(args['date'].strftime('%Y-%m-%d'))
        }

        # create and add new Mark
        new_mark = Mark(id=create_id(), event=event,
                        date=args['date'])
        db.session.add(new_mark)
        db.session.commit()

        return Response(response=json.dumps(response), status=200)


class SpecificEventResource(Resource):
    @marshal_with(resource_fields)
    def get(self, id):
        specific_event = Mark.query.filter(Mark.id == id).first()
        if specific_event is None:
            abort(404, 'The event doesn\'t exist!')
        return specific_event

    def delete(self, id):
        event_to_delete = Mark.query.filter(Mark.id == id).first()
        if event_to_delete is None:
            abort(404, 'The event doesn\'t exist!')
            db.session.query(Mark).delete()
            db.session.commit()
        else:
            response_json = {
                'message': 'The event has been deleted!'
            }

            return Response(response=json.dumps(response_json), status=200)


api.add_resource(EventResource, '/event')
api.add_resource(SpecificEventResource, '/event/<int:id>')
api.add_resource(HelloResource, '/event/today')

# do not change the way you run the program
if __name__ == '__main__':
    if len(sys.argv) > 1:
        arg_host, arg_port = sys.argv[1].split(':')
        app.run(host=arg_host, port=arg_port)
    else:
        db.create_all()
        app.run()

