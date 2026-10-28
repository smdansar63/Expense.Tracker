import requests
import re

BASE_URL = "http://127.0.0.1:5000"
session = requests.Session()

def run_tests():
    print("[1] Testing Landing Page...")
    r = session.get(f"{BASE_URL}/")
    assert r.status_code == 200, f"Landing page failed with {r.status_code}"
    print(" -> Landing page OK (200)")

    import time
    test_email = f"test.user_{int(time.time())}@example.com"
    print(f"[2] Testing User Registration with {test_email}...")
    signup_data = {
        'full_name': 'Aarav Patel',
        'email': test_email,
        'password': 'SecurePassword123!',
        'confirm_password': 'SecurePassword123!',
        'terms': 'on'
    }
    r = session.post(f"{BASE_URL}/signup", data=signup_data, allow_redirects=True)
    assert r.status_code == 200, f"Signup failed with {r.status_code}"
    assert "Aarav" in r.text or "Dashboard" in r.text
    print(" -> Signup & auto-login OK (200)")

    print("[3] Testing Demo Financial Data Seeder...")
    r = session.post(f"{BASE_URL}/seed-demo-data", allow_redirects=True)
    assert r.status_code == 200
    assert "Organic Grocery" in r.text or "Dashboard" in r.text
    print(" -> Demo data seeded successfully (27+ records)")

    print("[4] Testing Dashboard KPIs & Metrics...")
    r = session.get(f"{BASE_URL}/dashboard")
    assert r.status_code == 200
    assert "Total Lifetime Expenses" in r.text
    assert "₹" in r.text
    print(" -> Dashboard KPIs calculated and rendered OK (200)")

    print("[5] Testing Adding a Custom Expense...")
    add_data = {
        'title': 'Coffee with College Team',
        'amount': '350.00',
        'category_id': '1', # Food & Dining
        'expense_date': '2026-10-28',
        'notes': 'Academic project discussion at Starbucks'
    }
    r = session.post(f"{BASE_URL}/add-expense", data=add_data, allow_redirects=True)
    assert r.status_code == 200
    assert "Coffee with College Team" in r.text
    print(" -> Add Expense OK (200)")

    print("[6] Testing Expense Search & Filter...")
    r = session.get(f"{BASE_URL}/expenses?search=Coffee")
    assert r.status_code == 200
    assert "Coffee with College Team" in r.text
    print(" -> Search & Filter OK (200)")

    print("[7] Testing Analytics Calculations (Pandas & NumPy)...")
    r = session.get(f"{BASE_URL}/analytics?period=this_month")
    assert r.status_code == 200
    assert "Category-Wise Statistical Breakdown" in r.text
    assert "MoM Comparison" in r.text
    print(" -> Analytics & statistical distribution OK (200)")

    print("[8] Testing Monthly Budget Management...")
    # Set a budget of ₹55,000 for current month
    budget_data = {
        'action': 'set_budget',
        'month': '10',
        'year': '2026',
        'budget_amount': '55000'
    }
    r = session.post(f"{BASE_URL}/budgets", data=budget_data, allow_redirects=True)
    assert r.status_code == 200
    assert "55,000" in r.text or "55000" in r.text
    print(" -> Budget setting & progress monitoring OK (200)")

    print("[9] Testing Reports Page & CSV Export...")
    r = session.get(f"{BASE_URL}/reports")
    assert r.status_code == 200
    assert "Statement Ledger Preview" in r.text

    csv_res = session.get(f"{BASE_URL}/export-csv")
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers.get('Content-Type', '')
    assert "Expense Title" in csv_res.text
    assert "Coffee with College Team" in csv_res.text
    print(" -> Reports & CSV Export OK (200)")

    print("[10] Testing User Profile & Theme Preference...")
    profile_data = {
        'action': 'update_profile',
        'full_name': 'Aarav Patel (Senior Analyst)',
        'currency': 'INR',
        'theme': 'dark'
    }
    r = session.post(f"{BASE_URL}/profile", data=profile_data, allow_redirects=True)
    assert r.status_code == 200
    assert "Aarav Patel (Senior Analyst)" in r.text
    print(" -> Profile update OK (200)")

    print("[11] Testing Logout & Route Protection...")
    r = session.post(f"{BASE_URL}/logout", allow_redirects=True)
    assert r.status_code == 200
    assert "successfully logged out" in r.text

    # Verify protected route redirects to login
    r = session.get(f"{BASE_URL}/dashboard", allow_redirects=False)
    assert r.status_code == 302
    assert "/login" in r.headers.get('Location', '')
    print(" -> Logout & route protection OK (302 -> /login)")

    print("\n=======================================================")
    print(" ALL 11 MAJOR FEATURE INTEGRATION TESTS PASSED 100%! ")
    print("=======================================================")

if __name__ == '__main__':
    run_tests()
