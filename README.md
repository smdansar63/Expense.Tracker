# 🪙 Personal Expense Tracking and Financial Analytics System

A full-stack, production-grade financial web application engineered for daily expense management, budget tracking, statistical financial analytics, and transaction auditing. Built as an academic Software Engineering and Financial Data Analytics capstone project.

---

## 🌟 Key System Capabilities

- **Fintech Dashboard**: Real-time KPI summaries (Total Expenses, Current Month Spending, Remaining Budget, Average Expense, Highest Expense, Top Spending Category, Transaction Counts) calculated directly from persistent MySQL records.
- **Interactive Visualizations (Chart.js)**:
  - Dynamic Category Breakdown Donut Chart
  - Last 6 Months Outflow Comparison Bar Chart
  - Current Month Daily Spending Trend Line Chart
  - Day-of-Week Spending Cluster Analysis Bar Chart
  - 6-Month Budget vs Actual Expenditure Analysis Chart
- **Data Analytics Engine (Pandas & NumPy)**: Mean, median, standard deviation, month-over-month rate of change, and category group aggregations.
- **Expense Management (CRUD)**: Add, view details modal, edit, delete with confirmation, live keyword search, category filtering, date-range filtering, multi-field sorting, and pagination.
- **Smart Budget Planning**: Set or update monthly budget allocations. Features real-time visual progress bars with **normal (<80%)**, **warning (80–100%)**, and **exceeded (>100%)** alerts.
- **Reporting & Ledger Export**: Filter transactions by period or category, live preview statement, print-ready PDF layout, and 1-click UTF-8 CSV ledger download.
- **Enterprise-Grade Authentication & Security**:
  - Secure password hashing using PBKDF2/SHA-256 (`werkzeug.security`).
  - Strict user data isolation with parameterized SQL queries (`WHERE user_id = %s`).
  - Time-limited, cryptographically signed password reset tokens (`itsdangerous`).
  - Session cookie protections (`HttpOnly`, `SameSite=Lax`).
- **Modern Fintech Aesthetics**: Soft indigo (`#4f46e5`), lavender, mint green, and dark slate color scheme with responsive sidebar navigation, micro-interactions, breadcrumb trails, and full light/dark mode support.
- **Academic Demo Dataset Seeder**: 1-click button in Profile to load 27+ realistic expenses and 3 months of historical budgets for instant college demonstration.

---

## 🛠️ Technology Stack

| Layer | Technologies Used |
| :--- | :--- |
| **Frontend** | HTML5, CSS3, JavaScript (ES6+), Tailwind CSS (Custom Fintech Palette), FontAwesome 6 |
| **Backend** | Python 3.10+ / 3.13, Flask 3.1 |
| **Database** | MySQL (5.0+ / 8.0+ / MariaDB) via `mysql-connector-python` |
| **Data Analytics** | Pandas, NumPy |
| **Charts & Graphs** | Chart.js 4.x |
| **Security & Auth** | Werkzeug Security, ItsDangerous, Flask Sessions |
| **Environment** | `python-dotenv` |

---

## 📁 Project Directory Structure

```
expense_tracker/
│
├── app.py                     # Main Flask application and REST routes
├── db.py                      # MySQL connection pool and database initialization
├── analytics_engine.py        # Pandas and NumPy financial data analytics engine
├── schema.sql                 # Complete MySQL schema and default category seeds
├── requirements.txt           # Python package dependencies
├── .env.example               # Environment variables template
├── .env                       # Local active environment configuration
├── test_app.py                # Automated 11-step integration test suite
├── README.md                  # Comprehensive documentation and project guide
│
├── templates/                 # Jinja2 HTML5 Templates
│   ├── base.html              # Master layout (sidebar, topbar, theme toggle, modals)
│   ├── index.html             # Landing page with hero, live preview, and features
│   ├── signup.html            # User registration with password confirmation
│   ├── login.html             # Secure login with remember-me option
│   ├── forgot_password.html   # Password recovery flow with development simulator
│   ├── reset_password.html    # Password reset with token validation
│   ├── dashboard.html         # Main dashboard with 7 KPIs & 3 Chart.js graphs
│   ├── expenses.html          # Transaction ledger with search, filters & pagination
│   ├── add_expense.html       # Add expense form with category picker
│   ├── edit_expense.html      # Edit expense form with validation
│   ├── analytics.html         # In-depth financial analytics & statistical distributions
│   ├── budgets.html           # Monthly budget allocation, progress & history
│   ├── reports.html           # Formal statement preview, print layout & CSV export
│   └── profile.html           # User preferences, dark mode, password change & demo seeder
│
└── static/
    ├── css/
    │   └── style.css          # Design system, glassmorphism, animations & print CSS
    ├── js/
    │   ├── main.js            # Theme toggle, safe back navigation, password eye, modals
    │   └── charts.js          # Interactive Chart.js initialization & dark mode syncing
    └── images/                # Asset storage directory
```

---

## 🚀 Step-by-Step Installation & Setup

### Prerequisites
1. **Python 3.10 or higher** installed.
2. **MySQL Server** or **WAMP / XAMPP / MariaDB** running locally on port `3306`.

### 1. Clone or Open the Workspace
```powershell
cd c:\Users\smdan\OneDrive\Desktop\expense_tracker
```

### 2. Install Python Dependencies
```powershell
pip install -r requirements.txt
```

### 3. Configure MySQL Connection (`.env`)
Create or edit `.env` with your local database credentials:
```env
SECRET_KEY=expense_tracker_fintech_super_secret_key_2026_academic
FLASK_ENV=development
FLASK_DEBUG=1
PORT=5000

DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=expense_tracker
```

### 4. Initialize Database & Seed Categories
The application automatically creates the database and all tables on startup. You can also run the initialization script directly:
```powershell
python db.py
```
*(Alternatively, you can import `schema.sql` via phpMyAdmin or MySQL CLI).*

### 5. Launch the Application
```powershell
python app.py
```
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 🧪 Testing Instructions

### Automated Integration Test Suite
To verify all 11 major features (Landing, Registration, Demo Data Seeding, Dashboard KPIs, Expense CRUD, Filtering, Pandas Analytics, Budgets, Reports & CSV Export, Profile & Theme, Session Logout):
```powershell
python test_app.py
```
All tests should pass with code `0`.

### Manual Testing Walkthrough

1. **Sign Up**:
   - Visit `http://127.0.0.1:5000/signup`.
   - Register a new account (e.g., `Priya Nair`, `priya@example.com`, `SecurePass123!`).
   - Confirm you are logged in and redirected to the personalized dashboard.
2. **Explore Empty State**:
   - New accounts display a clean empty-state greeting.
   - Click **"Load Sample Demo Data"** to automatically populate 27+ realistic transactions across all 7 categories and 3 months of historical budgets.
3. **Inspect Dashboard**:
   - Verify summary KPI cards: Current Month Spending, Remaining Budget, Average Expense, Highest Expense, Top Category.
   - Toggle the **Moon / Sun icon** in the top navigation header to test dark/light theme switching.
4. **Expense Management**:
   - Navigate to **Expenses** in the sidebar.
   - Search for a keyword like `Grocery` or `Swiggy`.
   - Filter by category (e.g., `Food & Dining`) and date range.
   - Click the **Eye icon** on any expense row to open the details modal.
   - Click the **Plus button** to add a new transaction and verify totals update immediately.
5. **Analytics**:
   - Navigate to **Analytics**.
   - Switch period tabs: *Today*, *This Week*, *This Month*, *This Year*, *All Time*, or enter a custom date range.
   - Check the **Category-Wise Statistical Breakdown** table generated using Pandas aggregation.
6. **Budgets**:
   - Navigate to **Monthly Budgets**.
   - Update the current month's budget to `₹50,000`.
   - Note the real-time progress bar color: Green (<80%), Amber (80-100%), Red (>100% with exact excess alert).
7. **Reports & CSV Export**:
   - Navigate to **Reports & Export**.
   - Click **"Download CSV Ledger"** to verify that a formatted `.csv` file downloads with proper date and amount columns.
   - Click **"Print Statement"** to inspect the clean, formal print stylesheet with signature blocks.
8. **Profile & Security**:
   - Navigate to **Profile & Settings**.
   - Update your display name or currency preference.
   - Test changing your password or logging out via the secure confirmation modal.

---

## 🎓 College Project Demonstration Script

When presenting this project to evaluators or professors:

1. **Problem Statement**:
   > *"Personal financial literacy and expense visibility are critical in modern financial planning. Traditional record-keeping is fragmented and lacks predictive insights. This project bridges software engineering with financial data analytics to deliver automated tracking, budget enforcement, and statistical distribution modeling."*
2. **System Architecture**:
   > *"The project follows an MVC-inspired modular architecture. The Flask backend utilizes parameterized SQL queries and Werkzeug cryptographic hashing to ensure multi-tenant security and zero data leakage. Data processing is handled on the server via Pandas and NumPy, which transform raw relational rows into time-series trends and grouped variance summaries before passing them to Chart.js for client-side rendering."*
3. **Key Technical Highlights**:
   - Multi-version MySQL compatibility (MySQL 5.0 up to 8.x and MariaDB).
   - Dynamic budget threshold alerts (Normal, 80% Warning, Exceeded Danger).
   - RFC 4180-compliant CSV generation and browser print stylesheets.
   - Full accessibility with breadcrumb hierarchy, safe fallback back-navigation, and responsive mobile-first drawer navigation.

---

## 🔒 Security & Database Integrity

- **SQL Injection Prevention**: All queries execute with parameterized tuple substitution (`%s`), never raw string formatting.
- **Password Protection**: Passwords are saved strictly as salted cryptographic hashes (`pbkdf2:sha256`).
- **Ownership Checks**: Every database operation queries `WHERE user_id = %s`, preventing IDOR (Insecure Direct Object Reference).
- **Session Security**: Session cookies have `HttpOnly` enabled to mitigate XSS attacks and `SameSite='Lax'` to protect against CSRF.
#   E x p e n s e _ T r a c k e r  
 #   E x p e n s e _ T r a c k e r  
 