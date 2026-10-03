from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='customer', nullable=False) # 'customer' or 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to bookings
    bookings = db.relationship('Booking', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'

    def __repr__(self):
        return f'<User {self.email} ({self.role})>'

class Vehicle(db.Model):
    __tablename__ = 'vehicles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    vehicle_number = db.Column(db.String(30), unique=True, nullable=False)
    brand = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(50), nullable=False)
    vehicle_type = db.Column(db.String(20), nullable=False) # 'Car', 'Bike', 'Scooter', 'Van'
    fuel_type = db.Column(db.String(30), default='Petrol') # 'Petrol', 'Diesel', 'Electric'
    seating_capacity = db.Column(db.Integer, default=5)
    price_per_day = db.Column(db.Float, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to bookings
    bookings = db.relationship('Booking', backref='vehicle', lazy=True, cascade='all, delete-orphan')

    def is_available_for_dates(self, start_date, end_date, exclude_booking_id=None):
        """Check if vehicle is available between start_date and end_date (inclusive overlap check)"""
        if not self.is_available:
            return False

        # Query overlapping active bookings
        query = Booking.query.filter(
            Booking.vehicle_id == self.id,
            Booking.status.in_(['Pending', 'Approved']),
            Booking.pickup_date <= end_date,
            Booking.return_date >= start_date
        )

        if exclude_booking_id:
            query = query.filter(Booking.id != exclude_booking_id)

        overlapping = query.first()
        return overlapping is None

    def __repr__(self):
        return f'<Vehicle {self.name} ({self.vehicle_number})>'

class Booking(db.Model):
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=False)
    pickup_date = db.Column(db.Date, nullable=False)
    return_date = db.Column(db.Date, nullable=False)
    total_days = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='Pending', nullable=False) # 'Pending', 'Approved', 'Rejected', 'Cancelled', 'Completed'
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Booking #{self.id} User:{self.user_id} Vehicle:{self.vehicle_id} Status:{self.status}>'
