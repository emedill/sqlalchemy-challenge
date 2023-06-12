# Import the dependencies.
from flask import Flask, jsonify
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
import datetime as dt


#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(autoload_with=engine)

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################
climate_app = Flask(__name__)



#################################################
# Flask Routes
#################################################
@climate_app.route("/")
def home():
    print("Server received request for 'Home' page...")
    return (
        f"Welcome to the Climate App's home page!"
        f" The following are the Available Routes:<br/>"
        f" /api/v1.0/precipitation <br/>"
        f" /api/v1.0/stations <br/>"
        f" /api/v1.0/tobs <br/>"
        f" /api/v1.0/<start> <br/>"
        f" /api/v1.0/<start>/<end> <br/>"
    )


@climate_app.route("/api/v1.0/precipitation")
def precipitation():
    # Convert the query results from your precipitation analysis to a dictionary using date as the key and prcp as the value.
    recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    recent_date_value = recent_date[0]  
    previous_year = dt.datetime.strptime(recent_date_value, "%Y-%m-%d") - dt.timedelta(days=365)
    precipitation_data = session.query(Measurement.date, Measurement.prcp).\
        filter(Measurement.date >= previous_year).\
        order_by(Measurement.date).all()
    
    #Return the JSON representation of your dictionary.
    precipitation_dict = {date: prcp for date, prcp in precipitation_data}
    return jsonify(precipitation_dict)


@climate_app.route("/api/v1.0/stations")
def stations():
    #Return a JSON list of stations from the dataset.
    station_results = session.query(Station.station).all()
    station = [row[0] for row in station_results]
    return jsonify(station)   


@climate_app.route("/api/v1.0/tobs")
def tobs():
    #Query the dates and temperature observations of the most-active station for the previous year of data.
    active_stations = session.query(Measurement.station, func.count(Measurement.station)).\
        group_by(Measurement.station).\
        order_by(func.count(Measurement.station).desc()).all()
    
    most_active_station = active_stations[0][0] 

    active_station_recent_date = session.query(Measurement.date).\
        filter(Measurement.station == most_active_station).\
        order_by(desc(Measurement.date)).first()
    
    most_recent_station_date = dt.datetime.strptime(active_station_recent_date[0], "%Y-%m-%d").date()

    # Calculate the date one year from the last date in data set.
    active_station_previous_year = most_recent_station_date - dt.timedelta(days = 365)

    # Query the last 12 months of temperature observation data for this station
    previous_year_temp_data = session.query(Measurement.tobs).\
        filter(Measurement.station == most_active_station, Measurement.date >= active_station_previous_year).\
        order_by(Measurement.date).all()

    # Get the temperature values
    temperatures = [temp[0] for temp in previous_year_temp_data]

    # Return a JSON list of temperature observations for the previous year.
    return jsonify(temperatures)


@climate_app.route("/api/v1.0/<start>")
def start(start):
    temperature_data = session.query(func.min(Measurement.tobs), func.max(Measurement.tobs), func.avg(Measurement.tobs)).\
    filter(Measurement.date >= start).all()
    
    # Calculate TMIN, TAVG, and TMAX for all the dates greater than or equal to the start date.
    if temperature_data:
        tmin, tavg, tmax = temperature_data[0]
        response_data = {
            'start_date': start,
            'end_date': None,
            'tmin': tmin,
            'tavg': tavg,
            'tmax': tmax
        }

        # Return the response as JSON
        return jsonify(response_data)


@climate_app.route("/api/v1.0/<start>/<end>")
def start_end(start, end):
    temperature_data = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
        filter(Measurement.date >= start, Measurement.date <= end).all()
    
    # Calculate TMIN, TAVG, and TMAX for the dates from the start date to the end date, inclusive.
    if temperature_data:
        tmin, tavg, tmax = temperature_data[0]
        response_data = {
            'start_date': start,
            'end_date': end,
            'tmin': tmin,
            'tavg': tavg,
            'tmax': tmax
        }

        # Return the response as JSON
        return jsonify(response_data)
    

if __name__ == '__main__':
    climate_app.run(debug=True)