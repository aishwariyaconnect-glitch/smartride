import datetime
from models import db, User, Vehicle, Booking

def seed_database(app):
    with app.app_context():
        db.create_all()

        # Seed Admin User if not exists
        admin = User.query.filter_by(email='admin@smartride.com').first()
        if not admin:
            admin = User(
                full_name='System Admin',
                email='admin@smartride.com',
                phone='9876543210',
                role='admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)

        # Seed Demo Customer if not exists
        customer = User.query.filter_by(email='john@example.com').first()
        if not customer:
            customer = User(
                full_name='John Doe',
                email='john@example.com',
                phone='9123456789',
                role='customer'
            )
            customer.set_password('customer123')
            db.session.add(customer)

        db.session.commit()

        # Seed Vehicles if database table is empty
        if Vehicle.query.count() == 0:
            sample_vehicles = [
                # Cars
                Vehicle(
                    name='Toyota Etios',
                    vehicle_number='TN01AB1234',
                    brand='Toyota',
                    model='Etios Liva',
                    vehicle_type='Car',
                    fuel_type='Petrol',
                    seating_capacity=5,
                    price_per_day=1500.0,
                    location='Chennai Central',
                    description='Comfortable sedan with excellent mileage and spacious legroom. Perfect for city travel and family road trips.',
                    image_url='https://images.unsplash.com/photo-1549399542-7e3f8b79c341?auto=format&fit=crop&w=800&q=80',
                    is_available=True
                ),
                Vehicle(
                    name='Hyundai Creta',
                    vehicle_number='TN09XY5678',
                    brand='Hyundai',
                    model='Creta SX',
                    vehicle_type='Car',
                    fuel_type='Diesel',
                    seating_capacity=5,
                    price_per_day=2500.0,
                    location='Chennai Airport',
                    description='Premium SUV featuring panoramic sunroof, touch entertainment, and supreme highway driving comfort.',
                    image_url='https://images.unsplash.com/photo-1519641471654-76ce0107ad1b?auto=format&fit=crop&w=800&q=80',
                    is_available=True
                ),
                Vehicle(
                    name='Honda City',
                    vehicle_number='TN02CD3456',
                    brand='Honda',
                    model='City V',
                    vehicle_type='Car',
                    fuel_type='Petrol',
                    seating_capacity=5,
                    price_per_day=2000.0,
                    location='Coimbatore Town',
                    description='Executive sedan with automatic transmission, leather seating, and smooth power delivery.',
                    image_url='https://images.unsplash.com/photo-1552519507-da3b142c6e3d?auto=format&fit=crop&w=800&q=80',
                    is_available=True
                ),

                # Bikes
                Vehicle(
                    name='Royal Enfield Classic 350',
                    vehicle_number='TN02CD5678',
                    brand='Royal Enfield',
                    model='Classic 350',
                    vehicle_type='Bike',
                    fuel_type='Petrol',
                    seating_capacity=2,
                    price_per_day=700.0,
                    location='Chennai T.Nagar',
                    description='Iconic cruiser motorcycle with smooth thump, dual-channel ABS, and timeless retro aesthetic.',
                    image_url='https://images.unsplash.com/photo-1558981806-ec527fa84c39?auto=format&fit=crop&w=800&q=80',
                    is_available=True
                ),
                Vehicle(
                    name='Yamaha R15 V4',
                    vehicle_number='TN05EF1234',
                    brand='Yamaha',
                    model='R15 V4',
                    vehicle_type='Bike',
                    fuel_type='Petrol',
                    seating_capacity=2,
                    price_per_day=900.0,
                    location='Madurai City',
                    description='Track-ready sports bike equipped with quickshifter, traction control, and sharp aerodynamics.',
                    image_url='https://images.unsplash.com/photo-1568772585407-9361f9bf3a87?auto=format&fit=crop&w=800&q=80',
                    is_available=True
                ),
                Vehicle(
                    name='KTM Duke 390',
                    vehicle_number='TN07GH8901',
                    brand='KTM',
                    model='Duke 390',
                    vehicle_type='Bike',
                    fuel_type='Petrol',
                    seating_capacity=2,
                    price_per_day=1200.0,
                    location='Coimbatore Town',
                    description='High-performance naked streetfighter with explosive acceleration and TFT instrument console.',
                    image_url='https://images.unsplash.com/photo-1591637333184-19aa84b3e01f?auto=format&fit=crop&w=800&q=80',
                    is_available=True
                ),

                # Scooters
                Vehicle(
                    name='Honda Activa 6G',
                    vehicle_number='TN03EF9012',
                    brand='Honda',
                    model='Activa 6G',
                    vehicle_type='Scooter',
                    fuel_type='Petrol',
                    seating_capacity=2,
                    price_per_day=500.0,
                    location='Chennai Guindy',
                    description='India\'s favorite scooter with silent start technology, under-seat storage, and high fuel economy.',
                    image_url='https://images.unsplash.com/photo-1622185135505-2d795003994a?auto=format&fit=crop&w=800&q=80',
                    is_available=True
                ),
                Vehicle(
                    name='Ather 450X Electric',
                    vehicle_number='TN10EV7890',
                    brand='Ather',
                    model='450X Gen 3',
                    vehicle_type='Scooter',
                    fuel_type='Electric',
                    seating_capacity=2,
                    price_per_day=600.0,
                    location='Chennai Velachery',
                    description='Futuristic electric scooter featuring Google Maps navigation, Warp Mode, and 105km real-world range.',
                    image_url='https://images.unsplash.com/photo-1593941707882-a5bba14938c7?auto=format&fit=crop&w=800&q=80',
                    is_available=True
                ),

                # Vans
                Vehicle(
                    name='Force Traveller Luxury',
                    vehicle_number='TN04GH3456',
                    brand='Force',
                    model='Traveller 3350',
                    vehicle_type='Van',
                    fuel_type='Diesel',
                    seating_capacity=12,
                    price_per_day=3500.0,
                    location='Chennai Central',
                    description='Spacious 12-seater passenger van with reclining seats, dual AC vents, and high luggage capacity for group tours.',
                    image_url='https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?auto=format&fit=crop&w=800&q=80',
                    is_available=True
                ),
                Vehicle(
                    name='Maruti Eeco 7-Seater',
                    vehicle_number='TN08LM2345',
                    brand='Maruti',
                    model='Eeco Star',
                    vehicle_type='Van',
                    fuel_type='Petrol',
                    seating_capacity=7,
                    price_per_day=1800.0,
                    location='Salem Bus Stand',
                    description='Reliable multi-purpose van for affordable group transportation and family outings.',
                    image_url='https://images.unsplash.com/photo-1570125909232-eb263c188f7e?auto=format&fit=crop&w=800&q=80',
                    is_available=True
                )
            ]

            db.session.bulk_save_objects(sample_vehicles)
            db.session.commit()

        # Seed sample booking for demo user if none exists
        if Booking.query.count() == 0:
            first_vehicle = Vehicle.query.first()
            if customer and first_vehicle:
                today = datetime.date.today()
                pickup = today + datetime.timedelta(days=2)
                return_d = today + datetime.timedelta(days=5)
                days = (return_d - pickup).days
                total_cost = days * first_vehicle.price_per_day

                demo_booking = Booking(
                    user_id=customer.id,
                    vehicle_id=first_vehicle.id,
                    pickup_date=pickup,
                    return_date=return_d,
                    total_days=days,
                    total_price=total_cost,
                    status='Approved',
                    notes='Demo booking for presentation.'
                )
                db.session.add(demo_booking)
                db.session.commit()
