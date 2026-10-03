import os
import re
from datetime import datetime, date
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from models import db, User, Vehicle, Booking
from seed_data import seed_database

app = Flask(__name__)
app.config['SECRET_KEY'] = 'smartride-secret-key-viva-2026-secure'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///smartride.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Helper Decorators for Access Control
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Admin login required.', 'danger')
            return redirect(url_for('login'))
        if session.get('user_role') != 'admin':
            flash('Access denied! Admin privileges required.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def customer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to perform this action.', 'warning')
            return redirect(url_for('login'))
        if session.get('user_role') != 'customer':
            flash('Admin users cannot place rental bookings. Please log in as a customer.', 'warning')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Context processor for Jinja2 templates
@app.context_processor
def inject_now():
    return {'now': datetime.utcnow(), 'today_date': date.today().isoformat()}

# --- PUBLIC & CUSTOMER ROUTES ---

@app.route('/')
def index():
    featured_vehicles = Vehicle.query.filter_by(is_available=True).order_by(Vehicle.id.desc()).limit(6).all()
    categories = [
        {'name': 'Cars', 'icon': 'bi-car-front-fill', 'count': Vehicle.query.filter_by(vehicle_type='Car').count(), 'type': 'Car'},
        {'name': 'Bikes', 'icon': 'bi-bicycle', 'count': Vehicle.query.filter_by(vehicle_type='Bike').count(), 'type': 'Bike'},
        {'name': 'Scooters', 'icon': 'bi-scooter', 'count': Vehicle.query.filter_by(vehicle_type='Scooter').count(), 'type': 'Scooter'},
        {'name': 'Vans', 'icon': 'bi-truck-front-fill', 'count': Vehicle.query.filter_by(vehicle_type='Van').count(), 'type': 'Van'}
    ]
    return render_template('index.html', featured_vehicles=featured_vehicles, categories=categories)

@app.route('/vehicles')
def vehicle_list():
    query_param = request.args.get('q', '').strip()
    type_param = request.args.get('type', '').strip()
    location_param = request.args.get('location', '').strip()
    max_price_param = request.args.get('max_price', '').strip()

    vehicles_query = Vehicle.query

    if query_param:
        vehicles_query = vehicles_query.filter(
            (Vehicle.name.ilike(f'%{query_param}%')) |
            (Vehicle.brand.ilike(f'%{query_param}%')) |
            (Vehicle.model.ilike(f'%{query_param}%')) |
            (Vehicle.location.ilike(f'%{query_param}%'))
        )

    if type_param:
        vehicles_query = vehicles_query.filter(Vehicle.vehicle_type == type_param)

    if location_param:
        vehicles_query = vehicles_query.filter(Vehicle.location.ilike(f'%{location_param}%'))

    if max_price_param:
        try:
            max_p = float(max_price_param)
            vehicles_query = vehicles_query.filter(Vehicle.price_per_day <= max_p)
        except ValueError:
            pass

    vehicles = vehicles_query.order_by(Vehicle.is_available.desc(), Vehicle.name.asc()).all()
    
    locations = db.session.query(Vehicle.location).distinct().all()
    unique_locations = sorted([loc[0] for loc in locations if loc[0]])

    return render_template(
        'vehicles/list.html', 
        vehicles=vehicles, 
        selected_type=type_param,
        selected_location=location_param,
        max_price=max_price_param,
        search_query=query_param,
        unique_locations=unique_locations
    )

@app.route('/vehicles/<int:vehicle_id>')
def vehicle_detail(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    return render_template('vehicles/detail.html', vehicle=vehicle)

@app.route('/check-availability', methods=['POST'])
def check_availability():
    vehicle_id = request.form.get('vehicle_id')
    pickup_str = request.form.get('pickup_date')
    return_str = request.form.get('return_date')

    if not vehicle_id or not pickup_str or not return_str:
        return jsonify({'available': False, 'message': 'Missing dates or vehicle information.'})

    try:
        pickup_d = datetime.strptime(pickup_str, '%Y-%m-%d').date()
        return_d = datetime.strptime(return_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'available': False, 'message': 'Invalid date format.'})

    if pickup_d < date.today():
        return jsonify({'available': False, 'message': 'Pickup date cannot be in the past.'})

    if return_d <= pickup_d:
        return jsonify({'available': False, 'message': 'Return date must be after pickup date.'})

    vehicle = Vehicle.query.get(vehicle_id)
    if not vehicle:
        return jsonify({'available': False, 'message': 'Vehicle not found.'})

    is_avail = vehicle.is_available_for_dates(pickup_d, return_d)
    days = (return_d - pickup_d).days
    total_cost = days * vehicle.price_per_day

    if is_avail:
        return jsonify({
            'available': True,
            'days': days,
            'price_per_day': vehicle.price_per_day,
            'total_cost': total_cost,
            'message': f'Vehicle is available for {days} day(s)! Total: ₹{total_cost:,.2f}'
        })
    else:
        return jsonify({
            'available': False,
            'message': 'Sorry, vehicle is already booked for the selected date range.'
        })

@app.route('/book/<int:vehicle_id>', methods=['POST'])
@login_required
@customer_required
def book_vehicle(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)

    pickup_str = request.form.get('pickup_date')
    return_str = request.form.get('return_date')
    notes = request.form.get('notes', '').strip()

    if not pickup_str or not return_str:
        flash('Please select both pickup and return dates.', 'danger')
        return redirect(url_for('vehicle_detail', vehicle_id=vehicle_id))

    try:
        pickup_d = datetime.strptime(pickup_str, '%Y-%m-%d').date()
        return_d = datetime.strptime(return_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid date format submitted.', 'danger')
        return redirect(url_for('vehicle_detail', vehicle_id=vehicle_id))

    if pickup_d < date.today():
        flash('Pickup date cannot be in the past.', 'danger')
        return redirect(url_for('vehicle_detail', vehicle_id=vehicle_id))

    if return_d <= pickup_d:
        flash('Return date must be at least one day after pickup date.', 'danger')
        return redirect(url_for('vehicle_detail', vehicle_id=vehicle_id))

    # Double-booking check
    if not vehicle.is_available_for_dates(pickup_d, return_d):
        flash('This vehicle is not available for the selected dates. Please choose another date range.', 'danger')
        return redirect(url_for('vehicle_detail', vehicle_id=vehicle_id))

    total_days = (return_d - pickup_d).days
    total_price = total_days * vehicle.price_per_day

    new_booking = Booking(
        user_id=session['user_id'],
        vehicle_id=vehicle.id,
        pickup_date=pickup_d,
        return_date=return_d,
        total_days=total_days,
        total_price=total_price,
        status='Pending',
        notes=notes
    )

    db.session.add(new_booking)
    db.session.commit()

    flash('Booking request submitted successfully! Pending admin approval.', 'success')
    return redirect(url_for('booking_confirmation', booking_id=new_booking.id))

@app.route('/booking/confirmation/<int:booking_id>')
@login_required
def booking_confirmation(booking_id):
    booking = Booking.query.get_or_404(booking_id)

    # Security check: users can only view their own bookings unless admin
    if booking.user_id != session['user_id'] and session.get('user_role') != 'admin':
        flash('Unauthorized access to booking details.', 'danger')
        return redirect(url_for('my_bookings'))

    return render_template('customer/booking_confirmation.html', booking=booking)

@app.route('/my-bookings')
@login_required
@customer_required
def my_bookings():
    user_id = session['user_id']
    bookings = Booking.query.filter_by(user_id=user_id).order_by(Booking.created_at.desc()).all()
    return render_template('customer/dashboard.html', bookings=bookings)

@app.route('/cancel-booking/<int:booking_id>', methods=['POST'])
@login_required
@customer_required
def cancel_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)

    if booking.user_id != session['user_id']:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('my_bookings'))

    if booking.status not in ['Pending', 'Approved']:
        flash('Only Pending or Approved upcoming bookings can be cancelled.', 'warning')
        return redirect(url_for('my_bookings'))

    if booking.pickup_date <= date.today() and booking.status == 'Approved':
        flash('Cannot cancel rental on or after the pickup date.', 'danger')
        return redirect(url_for('my_bookings'))

    booking.status = 'Cancelled'
    db.session.commit()

    flash(f'Booking #{booking.id} has been cancelled.', 'info')
    return redirect(url_for('my_bookings'))

@app.route('/profile')
@login_required
def profile():
    user = User.query.get(session['user_id'])
    bookings_count = Booking.query.filter_by(user_id=user.id).count()
    return render_template('customer/profile.html', user=user, bookings_count=bookings_count)


# --- AUTHENTICATION ROUTES ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validations
        if not full_name or not email or not phone or not password or not confirm_password:
            flash('All fields are required.', 'danger')
            return render_template('auth/register.html', full_name=full_name, email=email, phone=phone)

        if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email):
            flash('Please enter a valid email address.', 'danger')
            return render_template('auth/register.html', full_name=full_name, email=email, phone=phone)

        if len(phone) < 10 or not phone.isdigit():
            flash('Please enter a valid 10-digit phone number.', 'danger')
            return render_template('auth/register.html', full_name=full_name, email=email, phone=phone)

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('auth/register.html', full_name=full_name, email=email, phone=phone)

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register.html', full_name=full_name, email=email, phone=phone)

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('An account with this email already exists. Please login.', 'warning')
            return render_template('auth/register.html', full_name=full_name, email=email, phone=phone)

        new_user = User(
            full_name=full_name,
            email=email,
            phone=phone,
            role='customer'
        )
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please login to continue.', 'success')
        return redirect(url_for('login'))

    return render_template('auth/register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        if session.get('user_role') == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please enter both email and password.', 'danger')
            return render_template('auth/login.html', email=email)

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['user_name'] = user.full_name
            session['user_role'] = user.role
            session['user_email'] = user.email

            flash(f'Welcome back, {user.full_name}!', 'success')
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)

            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')
            return render_template('auth/login.html', email=email)

    return render_template('auth/login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out safely.', 'info')
    return redirect(url_for('index'))


# --- ADMIN ROUTES ---

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    total_vehicles = Vehicle.query.count()
    total_customers = User.query.filter_by(role='customer').count()
    total_bookings = Booking.query.count()
    
    # Calculate revenue from Approved & Completed bookings
    approved_bookings = Booking.query.filter(Booking.status.in_(['Approved', 'Completed'])).all()
    total_revenue = sum(b.total_price for b in approved_bookings)

    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(5).all()
    pending_count = Booking.query.filter_by(status='Pending').count()

    return render_template(
        'admin/dashboard.html',
        total_vehicles=total_vehicles,
        total_customers=total_customers,
        total_bookings=total_bookings,
        total_revenue=total_revenue,
        recent_bookings=recent_bookings,
        pending_count=pending_count
    )

@app.route('/admin/vehicles')
@admin_required
def admin_vehicles():
    vehicles = Vehicle.query.order_by(Vehicle.id.desc()).all()
    return render_template('admin/vehicles.html', vehicles=vehicles)

@app.route('/admin/vehicles/add', methods=['POST'])
@admin_required
def admin_add_vehicle():
    name = request.form.get('name', '').strip()
    vehicle_number = request.form.get('vehicle_number', '').strip().upper()
    brand = request.form.get('brand', '').strip()
    model = request.form.get('model', '').strip()
    vehicle_type = request.form.get('vehicle_type', '').strip()
    fuel_type = request.form.get('fuel_type', 'Petrol').strip()
    seating_capacity = request.form.get('seating_capacity', 5, type=int)
    price_per_day = request.form.get('price_per_day', type=float)
    location = request.form.get('location', '').strip()
    description = request.form.get('description', '').strip()
    image_url = request.form.get('image_url', '').strip()

    if not name or not vehicle_number or not brand or not vehicle_type or not price_per_day or not location:
        flash('Please fill in all required vehicle fields.', 'danger')
        return redirect(url_for('admin_vehicles'))

    existing = Vehicle.query.filter_by(vehicle_number=vehicle_number).first()
    if existing:
        flash(f'Vehicle with number {vehicle_number} already exists.', 'warning')
        return redirect(url_for('admin_vehicles'))

    if not image_url:
        image_url = 'https://images.unsplash.com/photo-1549399542-7e3f8b79c341?auto=format&fit=crop&w=800&q=80'

    new_v = Vehicle(
        name=name,
        vehicle_number=vehicle_number,
        brand=brand,
        model=model,
        vehicle_type=vehicle_type,
        fuel_type=fuel_type,
        seating_capacity=seating_capacity,
        price_per_day=price_per_day,
        location=location,
        description=description,
        image_url=image_url,
        is_available=True
    )

    db.session.add(new_v)
    db.session.commit()

    flash(f'Vehicle "{name}" added successfully.', 'success')
    return redirect(url_for('admin_vehicles'))

@app.route('/admin/vehicles/edit/<int:vehicle_id>', methods=['POST'])
@admin_required
def admin_edit_vehicle(vehicle_id):
    v = Vehicle.query.get_or_404(vehicle_id)

    v.name = request.form.get('name', v.name).strip()
    v.brand = request.form.get('brand', v.brand).strip()
    v.model = request.form.get('model', v.model).strip()
    v.vehicle_type = request.form.get('vehicle_type', v.vehicle_type).strip()
    v.fuel_type = request.form.get('fuel_type', v.fuel_type).strip()
    v.seating_capacity = request.form.get('seating_capacity', v.seating_capacity, type=int)
    v.price_per_day = request.form.get('price_per_day', v.price_per_day, type=float)
    v.location = request.form.get('location', v.location).strip()
    v.description = request.form.get('description', v.description).strip()
    if request.form.get('image_url'):
        v.image_url = request.form.get('image_url').strip()

    db.session.commit()
    flash(f'Vehicle "{v.name}" updated successfully.', 'success')
    return redirect(url_for('admin_vehicles'))

@app.route('/admin/vehicles/toggle/<int:vehicle_id>', methods=['POST'])
@admin_required
def admin_toggle_vehicle(vehicle_id):
    v = Vehicle.query.get_or_404(vehicle_id)
    v.is_available = not v.is_available
    db.session.commit()
    status_str = "Available" if v.is_available else "Unavailable"
    flash(f'Vehicle "{v.name}" status changed to {status_str}.', 'info')
    return redirect(url_for('admin_vehicles'))

@app.route('/admin/vehicles/delete/<int:vehicle_id>', methods=['POST'])
@admin_required
def admin_delete_vehicle(vehicle_id):
    v = Vehicle.query.get_or_404(vehicle_id)
    name = v.name
    db.session.delete(v)
    db.session.commit()
    flash(f'Vehicle "{name}" deleted successfully.', 'info')
    return redirect(url_for('admin_vehicles'))

@app.route('/admin/bookings')
@admin_required
def admin_bookings():
    status_filter = request.args.get('status', '').strip()
    query = Booking.query

    if status_filter:
        query = query.filter_by(status=status_filter)

    bookings = query.order_by(Booking.created_at.desc()).all()
    return render_template('admin/bookings.html', bookings=bookings, current_filter=status_filter)

@app.route('/admin/bookings/status/<int:booking_id>/<string:new_status>', methods=['POST'])
@admin_required
def update_booking_status(booking_id, new_status):
    valid_statuses = ['Pending', 'Approved', 'Rejected', 'Cancelled', 'Completed']
    if new_status not in valid_statuses:
        flash('Invalid booking status.', 'danger')
        return redirect(url_for('admin_bookings'))

    booking = Booking.query.get_or_404(booking_id)
    booking.status = new_status
    db.session.commit()

    flash(f'Booking #{booking.id} status updated to {new_status}.', 'success')
    return redirect(url_for('admin_bookings'))

@app.route('/admin/customers')
@admin_required
def admin_customers():
    customers = User.query.filter_by(role='customer').order_by(User.created_at.desc()).all()
    
    # Calculate stats per customer
    customer_stats = []
    for c in customers:
        b_list = Booking.query.filter_by(user_id=c.id).all()
        spent = sum(b.total_price for b in b_list if b.status in ['Approved', 'Completed'])
        customer_stats.append({
            'user': c,
            'booking_count': len(b_list),
            'total_spent': spent
        })

    return render_template('admin/customers.html', customer_stats=customer_stats)


# --- INITIALIZATION & RUN ---

if __name__ == '__main__':
    with app.app_context():
        seed_database(app)
    app.run(debug=True, port=5000)
