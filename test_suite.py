import sys
import io

# Force UTF-8 output for Windows console testing
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import app as app_module
from models import db, User, Vehicle, Booking

app = app_module.app

def run_tests():
    with app.app_context():
        app_module.seed_database(app)
        print("1. Database Seed Verified:")
        print(f"   - Users: {User.query.count()}")
        print(f"   - Vehicles: {Vehicle.query.count()}")
        print(f"   - Bookings: {Booking.query.count()}")

        with app.test_client() as client:
            print("\n2. Testing Public Endpoints:")
            res = client.get('/')
            assert res.status_code == 200, "Homepage failed"
            print("   - Homepage (/): 200 OK")

            res = client.get('/vehicles')
            assert res.status_code == 200, "Vehicles list failed"
            print("   - Vehicles List (/vehicles): 200 OK")

            res = client.get('/vehicles/1')
            assert res.status_code == 200, "Vehicle detail failed"
            print("   - Vehicle Detail (/vehicles/1): 200 OK")

            print("\n3. Testing Customer Registration & Authentication:")
            reg_res = client.post('/register', data={
                'full_name': 'Test Alice',
                'email': 'alice@example.com',
                'phone': '9988776655',
                'password': 'password123',
                'confirm_password': 'password123'
            }, follow_redirects=True)
            assert reg_res.status_code == 200
            print("   - Customer Registration: Success")

            # Login as Alice
            login_res = client.post('/login', data={
                'email': 'alice@example.com',
                'password': 'password123'
            }, follow_redirects=True)
            assert login_res.status_code == 200
            print("   - Customer Login: Success")

            print("\n4. Testing Availability API & Price Calculation:")
            avail_res = client.post('/check-availability', data={
                'vehicle_id': 2,
                'pickup_date': '2026-11-01',
                'return_date': '2026-11-05'
            })
            json_data = avail_res.get_json()
            assert json_data['available'] == True
            assert json_data['days'] == 4
            print(f"   - Availability check response: {json_data['message']}")

            print("\n5. Testing Booking Submission:")
            book_res = client.post('/book/2', data={
                'pickup_date': '2026-11-01',
                'return_date': '2026-11-05',
                'notes': 'Need child safety seat'
            }, follow_redirects=True)
            assert book_res.status_code == 200
            print("   - Booking created successfully!")

            # Verify double-booking is blocked for overlapping dates
            avail_conflict = client.post('/check-availability', data={
                'vehicle_id': 2,
                'pickup_date': '2026-11-03',
                'return_date': '2026-11-07'
            })
            assert avail_conflict.get_json()['available'] == False
            print("   - Double-booking conflict check passed! (Blocked overlapping request)")

            print("\n6. Testing Admin Login & Booking Approval:")
            # Logout customer
            client.get('/logout')
            # Login Admin
            admin_login = client.post('/login', data={
                'email': 'admin@smartride.com',
                'password': 'admin123'
            }, follow_redirects=True)
            assert admin_login.status_code == 200
            print("   - Admin Login: Success")

            admin_dash = client.get('/admin/dashboard')
            assert admin_dash.status_code == 200
            print("   - Admin Dashboard (/admin/dashboard): 200 OK")

            # Approve the new booking (ID 2)
            approve_res = client.post('/admin/bookings/status/2/Approved', follow_redirects=True)
            assert approve_res.status_code == 200
            print("   - Admin Approved Booking #2")

            print("\n🎉 ALL UNIT & INTEGRATION TESTS PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    run_tests()
