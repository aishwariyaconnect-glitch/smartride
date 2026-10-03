# SmartRide – Vehicle Rental System 🚗🏍🛵🚐

**SmartRide** is a full-stack, beginner-friendly online vehicle rental platform developed with **Python (Flask)**, **SQLite (SQLAlchemy)**, **HTML5/CSS3**, **JavaScript**, and **Bootstrap 5**.

---

## 🌟 Key Features

### 👤 Customer Features
1. **User Registration & Login**: Secure account creation with password hashing (`werkzeug.security`).
2. **Homepage & Search**: Interactive hero banner, vehicle category shortcuts (Cars, Bikes, Scooters, Vans), search by keyword, vehicle type, location, and max rate.
3. **Vehicle Details & Availability**: Real-time pickup & return datepicker with instant client-side and server-side availability check.
4. **Dynamic Price Calculator**: Automatic rental cost calculation based on selected rental duration (`Total Days × Daily Rate`).
5. **Conflict Overlap Prevention**: Prevents double-booking of vehicles during active rental dates.
6. **Booking Management ("My Bookings")**: Track rental requests with status badges (`Pending`, `Approved`, `Rejected`, `Cancelled`, `Completed`) and cancel eligible bookings.
7. **Printable Invoice Receipt**: View and print itemized rental booking receipts.

### 🛡 Admin Features
1. **Admin Control Dashboard**: Analytics showing Total Revenue (₹), Total Bookings, Vehicle Inventory Count, and Customer Count.
2. **Vehicle Inventory CRUD**: Add new vehicles, update specifications, upload image URLs, delete vehicles, and toggle instant availability (`Available` / `Unavailable`).
3. **Booking Approval System**: Review customer booking requests and approve, reject, cancel, or mark as completed.
4. **Customer Overview**: View registered users list and total revenue generated per customer.

---

## 🛠 Technology Stack

- **Frontend**: HTML5, CSS3, JavaScript (ES6+), Bootstrap 5, Bootstrap Icons.
- **Backend**: Python 3.x, Flask web framework.
- **Database**: SQLite3 with Flask-SQLAlchemy ORM.
- **Authentication**: Flask Sessions & Password Hashing.

---

## 🚀 How to Run locally on Windows using VS Code

### 1. Open Project in VS Code
Open VS Code, select **File -> Open Folder...** and navigate to:
`C:\Users\Aishwariya Lakshmi.V\.gemini\antigravity\scratch\smartride`

### 2. Install Required Dependencies
Open VS Code Terminal (`Ctrl + ~`) and run:
```bash
pip install -r requirements.txt
```

### 3. Launch Application
Run the main Flask application:
```bash
python app.py
```

### 4. Access in Browser
Open your browser and visit:
`http://127.0.0.1:5000`

---

## 🔑 Pre-seeded Demo Credentials

The system automatically initializes and seeds the database (`smartride.db`) on first launch with sample data and test accounts:

| Role | Email | Password |
| :--- | :--- | :--- |
| **Admin** | `admin@smartride.com` | `admin123` |
| **Customer** | `john@example.com` | `customer123` |

---

## 📊 Database Schema Summary

- **`User`**: `id`, `full_name`, `email` (unique), `phone`, `password_hash`, `role` ('customer' / 'admin'), `created_at`
- **`Vehicle`**: `id`, `name`, `vehicle_number` (unique), `brand`, `model`, `vehicle_type` ('Car', 'Bike', 'Scooter', 'Van'), `fuel_type`, `seating_capacity`, `price_per_day`, `location`, `description`, `image_url`, `is_available`, `created_at`
- **`Booking`**: `id`, `user_id` (FK), `vehicle_id` (FK), `pickup_date`, `return_date`, `total_days`, `total_price`, `status` ('Pending', 'Approved', 'Rejected', 'Cancelled', 'Completed'), `notes`, `created_at`

---

## 🎓 Viva Voce Q&A Preparation Tips

1. **Q: How does the application handle double-booking prevention?**
   - *Answer*: When a customer checks availability or submits a booking, the system queries the `Booking` table for any existing `Pending` or `Approved` rentals for that specific vehicle where `pickup_date <= selected_return_date AND return_date >= selected_pickup_date`. If an overlap is detected, booking is blocked.

2. **Q: How is user authentication maintained across pages?**
   - *Answer*: HTTP is stateless. Flask uses encrypted cookie-based **sessions** (`session['user_id']`, `session['user_role']`) to keep the user logged in across requests.

3. **Q: How are passwords stored securely in the database?**
   - *Answer*: Passwords are never stored in plaintext. We use `generate_password_hash` from `werkzeug.security` (PBKDF2 SHA-256) during registration and `check_password_hash` during login.

4. **Q: What architecture pattern does this application follow?**
   - *Answer*: It follows the **MVC (Model-View-Controller)** pattern. `models.py` represents the Data Layer (Model), Jinja2 HTML templates in `/templates` represent the View, and routes in `app.py` act as Controllers handling business logic.
