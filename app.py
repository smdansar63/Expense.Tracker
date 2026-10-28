import os
import io
import csv
from datetime import datetime, date, timedelta
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, jsonify, Response, send_file
)
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
from dotenv import load_dotenv

from db import get_db_connection, init_db
from analytics_engine import (
    calculate_dashboard_metrics,
    get_detailed_analytics,
    get_budget_dashboard_data,
    seed_sample_demo_data,
    format_currency_inr
)

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default_fintech_secure_key_12345')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# Password reset serializer
serializer = URLSafeTimedSerializer(app.secret_key)

# Ensure database tables exist at startup
with app.app_context():
    init_db()

# --------------------------------------------------------------------
# Jinja Template Filters & Context Processors
# --------------------------------------------------------------------
@app.template_filter('inr')
def inr_filter(value):
    return format_currency_inr(value)

@app.template_filter('indian_date')
def indian_date_filter(value):
    if not value:
        return ""
    if isinstance(value, (datetime, date)):
        return value.strftime('%d/%m/%Y')
    try:
        dt = datetime.strptime(str(value), '%Y-%m-%d')
        return dt.strftime('%d/%m/%Y')
    except Exception:
        return str(value)

@app.context_processor
def inject_global_data():
    today = date.today()
    user_theme = session.get('theme', 'light')
    user_currency = session.get('currency', 'INR')
    return {
        'now': datetime.now(),
        'today_date': today,
        'current_year': today.year,
        'user_theme': user_theme,
        'user_currency': user_currency
    }

# --------------------------------------------------------------------
# Authentication Decorator
# --------------------------------------------------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login', next=request.path))
        return f(*args, **kwargs)
    return decorated_function

# --------------------------------------------------------------------
# 1. Landing & Authentication Routes
# --------------------------------------------------------------------
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        terms = request.form.get('terms')

        # Form Validations
        errors = []
        if not full_name or len(full_name) < 2:
            errors.append("Full Name must be at least 2 characters.")
        if not email or '@' not in email or '.' not in email:
            errors.append("Please provide a valid email address.")
        if not password or len(password) < 6:
            errors.append("Password must be at least 6 characters long.")
        if password != confirm_password:
            errors.append("Passwords do not match.")
        if not terms:
            errors.append("You must agree to the Terms of Service and Privacy Policy.")

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('signup.html', full_name=full_name, email=email)

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # Check duplicate email
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                flash("An account with this email address already exists. Please log in.", "warning")
                cursor.close()
                conn.close()
                return render_template('signup.html', full_name=full_name, email=email)

            # Hash password and insert user
            pwd_hash = generate_password_hash(password)
            now = datetime.now()
            cursor.execute("""
                INSERT INTO users (full_name, email, password_hash, currency, theme, created_at)
                VALUES (%s, %s, %s, 'INR', 'light', %s)
            """, (full_name, email, pwd_hash, now))
            new_user_id = cursor.lastrowid

            # Set session
            session.permanent = True
            session['user_id'] = new_user_id
            session['user_name'] = full_name
            session['user_email'] = email
            session['theme'] = 'light'
            session['currency'] = 'INR'

            flash(f"Welcome to Personal Expense Tracker, {full_name}! Your account has been created.", "success")
            cursor.close()
            conn.close()
            return redirect(url_for('dashboard'))
        except Exception as e:
            conn.close()
            flash(f"Registration error: {str(e)}", "danger")
            return render_template('signup.html', full_name=full_name, email=email)

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember')

        if not email or not password:
            flash("Please enter both your email address and password.", "danger")
            return render_template('login.html', email=email)

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, full_name, email, password_hash, currency, theme FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()

            # Verify password using constant time check
            if user and check_password_hash(user[3], password):
                session.permanent = bool(remember)
                session['user_id'] = user[0]
                session['user_name'] = user[1]
                session['user_email'] = user[2]
                session['currency'] = user[4] or 'INR'
                session['theme'] = user[5] or 'light'

                flash(f"Welcome back, {user[1]}!", "success")
                next_url = request.args.get('next')
                if next_url and next_url.startswith('/'):
                    return redirect(next_url)
                return redirect(url_for('dashboard'))
            else:
                flash("Invalid email or password. Please verify your credentials and try again.", "danger")
                return render_template('login.html', email=email)
        except Exception as e:
            conn.close()
            flash(f"Login error: {str(e)}", "danger")
            return render_template('login.html', email=email)

    return render_template('login.html')

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    flash("You have been successfully logged out. Have a great day!", "info")
    return redirect(url_for('index'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    simulated_reset_url = None
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        if not email:
            flash("Please enter your registered email address.", "danger")
            return render_template('forgot_password.html')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, full_name FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if user:
            token = serializer.dumps(email, salt='password-reset-salt')
            expires_at = datetime.now() + timedelta(hours=1)
            cursor.execute("""
                INSERT INTO password_resets (user_id, token, expires_at, created_at)
                VALUES (%s, %s, %s, %s)
            """, (user[0], token, expires_at, datetime.now()))
            
            simulated_reset_url = url_for('reset_password', token=token, _external=True)
            flash("Password reset instructions have been generated.", "info")
        else:
            flash("If that email is registered in our system, reset instructions have been generated.", "info")
            
        cursor.close()
        conn.close()
        return render_template('forgot_password.html', simulated_reset_url=simulated_reset_url, submitted_email=email)

    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=3600)
    except (SignatureExpired, BadTimeSignature):
        flash("The password reset link is invalid or has expired. Please request a new one.", "danger")
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not password or len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return render_template('reset_password.html', token=token)
        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template('reset_password.html', token=token)

        conn = get_db_connection()
        cursor = conn.cursor()
        new_hash = generate_password_hash(password)
        cursor.execute("UPDATE users SET password_hash = %s WHERE email = %s", (new_hash, email))
        cursor.execute("DELETE FROM password_resets WHERE token = %s", (token,))
        cursor.close()
        conn.close()

        flash("Your password has been successfully updated. You may now log in with your new password.", "success")
        return redirect(url_for('login'))

    return render_template('reset_password.html', token=token)

# --------------------------------------------------------------------
# 2. Dashboard
# --------------------------------------------------------------------
@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    
    metrics = calculate_dashboard_metrics(user_id, cursor)
    
    cursor.close()
    conn.close()
    return render_template('dashboard.html', metrics=metrics)

# --------------------------------------------------------------------
# 3. Expense Management (CRUD)
# --------------------------------------------------------------------
@app.route('/expenses')
@login_required
def expenses():
    user_id = session['user_id']
    search = request.args.get('search', '').strip()
    category_id = request.args.get('category', '').strip()
    start_date = request.args.get('start_date', '').strip()
    end_date = request.args.get('end_date', '').strip()
    sort_by = request.args.get('sort_by', 'date_desc')
    page = int(request.args.get('page', 1))
    per_page = 10

    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch all categories for filter dropdown
    cursor.execute("SELECT id, name, icon, color FROM categories ORDER BY name ASC")
    categories = [{'id': r[0], 'name': r[1], 'icon': r[2], 'color': r[3]} for r in cursor.fetchall()]

    # Build filtered query with parameters
    where_clauses = ["e.user_id = %s"]
    params = [user_id]

    if search:
        where_clauses.append("(e.title LIKE %s OR e.notes LIKE %s)")
        params.extend([f"%{search}%", f"%{search}%"])

    if category_id and category_id.isdigit():
        where_clauses.append("e.category_id = %s")
        params.append(int(category_id))

    if start_date:
        where_clauses.append("e.expense_date >= %s")
        params.append(start_date)

    if end_date:
        where_clauses.append("e.expense_date <= %s")
        params.append(end_date)

    where_sql = " AND ".join(where_clauses)

    # Count total matching records for pagination
    cursor.execute(f"SELECT COUNT(*) FROM expenses e WHERE {where_sql}", tuple(params))
    total_records = cursor.fetchone()[0]

    # Calculate total sum of filtered records
    cursor.execute(f"SELECT COALESCE(SUM(e.amount), 0) FROM expenses e WHERE {where_sql}", tuple(params))
    filtered_total = float(cursor.fetchone()[0])

    # Sorting
    order_map = {
        'date_desc': 'e.expense_date DESC, e.created_at DESC',
        'date_asc': 'e.expense_date ASC, e.created_at ASC',
        'amount_desc': 'e.amount DESC',
        'amount_asc': 'e.amount ASC',
        'title_asc': 'e.title ASC',
        'category_asc': 'c.name ASC'
    }
    order_sql = order_map.get(sort_by, 'e.expense_date DESC, e.created_at DESC')

    # Pagination calculation
    total_pages = max(1, (total_records + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    offset = (page - 1) * per_page

    # Fetch page records
    query = f"""
        SELECT e.id, e.title, e.amount, e.expense_date, e.notes, e.created_at,
               c.id as category_id, c.name as category_name, c.icon, c.color
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        WHERE {where_sql}
        ORDER BY {order_sql}
        LIMIT %s OFFSET %s
    """
    cursor.execute(query, tuple(params + [per_page, offset]))
    expense_rows = cursor.fetchall()

    expense_list = []
    for r in expense_rows:
        expense_list.append({
            'id': r[0],
            'title': r[1],
            'amount': float(r[2]),
            'formatted_amount': format_currency_inr(r[2]),
            'expense_date': r[3],
            'formatted_date': r[3].strftime('%d/%m/%Y') if hasattr(r[3], 'strftime') else str(r[3]),
            'notes': r[4] or '',
            'created_at': r[5],
            'category_id': r[6],
            'category_name': r[7],
            'category_icon': r[8],
            'category_color': r[9]
        })

    cursor.close()
    conn.close()

    return render_template(
        'expenses.html',
        expenses=expense_list,
        categories=categories,
        total_records=total_records,
        filtered_total=filtered_total,
        formatted_filtered_total=format_currency_inr(filtered_total),
        page=page,
        total_pages=total_pages,
        per_page=per_page,
        search=search,
        selected_category=category_id,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by
    )

@app.route('/add-expense', methods=['GET', 'POST'])
@login_required
def add_expense():
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        amount_raw = request.form.get('amount', '').strip()
        category_id = request.form.get('category_id', '').strip()
        expense_date_raw = request.form.get('expense_date', '').strip()
        notes = request.form.get('notes', '').strip()

        errors = []
        if not title:
            errors.append("Expense title is required.")
        
        try:
            amount = float(amount_raw)
            if amount <= 0:
                errors.append("Amount must be greater than zero.")
        except (ValueError, TypeError):
            errors.append("Please enter a valid positive numerical amount.")

        if not category_id or not category_id.isdigit():
            errors.append("Please select a valid expense category.")

        try:
            expense_date = datetime.strptime(expense_date_raw, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            errors.append("Please select a valid date in YYYY-MM-DD format.")

        if errors:
            for err in errors:
                flash(err, 'danger')
            cursor.execute("SELECT id, name, icon, color FROM categories ORDER BY name ASC")
            categories = [{'id': r[0], 'name': r[1], 'icon': r[2], 'color': r[3]} for r in cursor.fetchall()]
            cursor.close()
            conn.close()
            return render_template('add_expense.html', categories=categories, form=request.form)

        # Insert new expense
        now = datetime.now()
        cursor.execute("""
            INSERT INTO expenses (user_id, title, amount, category_id, expense_date, notes, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (user_id, title, amount, int(category_id), expense_date, notes, now))

        flash(f"Expense '{title}' of {format_currency_inr(amount)} recorded successfully!", "success")
        cursor.close()
        conn.close()
        return redirect(url_for('expenses'))

    cursor.execute("SELECT id, name, icon, color FROM categories ORDER BY name ASC")
    categories = [{'id': r[0], 'name': r[1], 'icon': r[2], 'color': r[3]} for r in cursor.fetchall()]
    cursor.close()
    conn.close()

    return render_template('add_expense.html', categories=categories, today_str=date.today().strftime('%Y-%m-%d'))

@app.route('/edit-expense/<int:expense_id>', methods=['GET', 'POST'])
@login_required
def edit_expense(expense_id):
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()

    # Ensure ownership
    cursor.execute("""
        SELECT id, title, amount, category_id, expense_date, notes
        FROM expenses
        WHERE id = %s AND user_id = %s
    """, (expense_id, user_id))
    expense_row = cursor.fetchone()

    if not expense_row:
        flash("Expense not found or unauthorized access.", "danger")
        cursor.close()
        conn.close()
        return redirect(url_for('expenses'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        amount_raw = request.form.get('amount', '').strip()
        category_id = request.form.get('category_id', '').strip()
        expense_date_raw = request.form.get('expense_date', '').strip()
        notes = request.form.get('notes', '').strip()

        errors = []
        if not title:
            errors.append("Expense title is required.")
        
        try:
            amount = float(amount_raw)
            if amount <= 0:
                errors.append("Amount must be greater than zero.")
        except (ValueError, TypeError):
            errors.append("Please enter a valid positive numerical amount.")

        if not category_id or not category_id.isdigit():
            errors.append("Please select a valid expense category.")

        try:
            expense_date = datetime.strptime(expense_date_raw, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            errors.append("Please select a valid date.")

        if errors:
            for err in errors:
                flash(err, 'danger')
            cursor.execute("SELECT id, name, icon, color FROM categories ORDER BY name ASC")
            categories = [{'id': r[0], 'name': r[1], 'icon': r[2], 'color': r[3]} for r in cursor.fetchall()]
            cursor.close()
            conn.close()
            return render_template('edit_expense.html', expense=expense_row, categories=categories)

        # Update expense
        cursor.execute("""
            UPDATE expenses
            SET title = %s, amount = %s, category_id = %s, expense_date = %s, notes = %s
            WHERE id = %s AND user_id = %s
        """, (title, amount, int(category_id), expense_date, notes, expense_id, user_id))

        flash(f"Expense '{title}' updated successfully!", "success")
        cursor.close()
        conn.close()
        return redirect(url_for('expenses'))

    cursor.execute("SELECT id, name, icon, color FROM categories ORDER BY name ASC")
    categories = [{'id': r[0], 'name': r[1], 'icon': r[2], 'color': r[3]} for r in cursor.fetchall()]
    
    expense_data = {
        'id': expense_row[0],
        'title': expense_row[1],
        'amount': float(expense_row[2]),
        'category_id': expense_row[3],
        'expense_date': expense_row[4].strftime('%Y-%m-%d') if hasattr(expense_row[4], 'strftime') else str(expense_row[4]),
        'notes': expense_row[5] or ''
    }

    cursor.close()
    conn.close()
    return render_template('edit_expense.html', expense=expense_data, categories=categories)

@app.route('/delete-expense/<int:expense_id>', methods=['POST'])
@login_required
def delete_expense(expense_id):
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()

    # Verify ownership before delete
    cursor.execute("SELECT title FROM expenses WHERE id = %s AND user_id = %s", (expense_id, user_id))
    row = cursor.fetchone()
    if row:
        title = row[0]
        cursor.execute("DELETE FROM expenses WHERE id = %s AND user_id = %s", (expense_id, user_id))
        flash(f"Expense '{title}' has been deleted.", "info")
    else:
        flash("Record not found or unauthorized.", "danger")

    cursor.close()
    conn.close()
    return redirect(request.referrer or url_for('expenses'))

@app.route('/api/expense/<int:expense_id>')
@login_required
def api_expense_details(expense_id):
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.id, e.title, e.amount, e.expense_date, e.notes, e.created_at,
               c.name as category_name, c.icon, c.color
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        WHERE e.id = %s AND e.user_id = %s
    """, (expense_id, user_id))
    r = cursor.fetchone()
    cursor.close()
    conn.close()

    if not r:
        return jsonify({'error': 'Not found'}), 404

    return jsonify({
        'id': r[0],
        'title': r[1],
        'amount': float(r[2]),
        'formatted_amount': format_currency_inr(r[2]),
        'expense_date': r[3].strftime('%d/%m/%Y') if hasattr(r[3], 'strftime') else str(r[3]),
        'notes': r[4] or 'No additional notes provided.',
        'created_at': r[5].strftime('%d/%m/%Y %I:%M %p') if hasattr(r[5], 'strftime') else str(r[5]),
        'category_name': r[6],
        'category_icon': r[7],
        'category_color': r[8]
    })

# --------------------------------------------------------------------
# 4. Analytics & Financial Reports
# --------------------------------------------------------------------
@app.route('/analytics')
@login_required
def analytics():
    user_id = session['user_id']
    period_filter = request.args.get('period', 'this_month')
    custom_start = request.args.get('start_date')
    custom_end = request.args.get('end_date')

    conn = get_db_connection()
    cursor = conn.cursor()

    report = get_detailed_analytics(
        user_id,
        period_filter=period_filter,
        custom_start=custom_start,
        custom_end=custom_end,
        cursor=cursor
    )

    cursor.close()
    conn.close()
    return render_template('analytics.html', report=report)

# --------------------------------------------------------------------
# 5. Monthly Budget Management
# --------------------------------------------------------------------
@app.route('/budgets', methods=['GET', 'POST'])
@login_required
def budgets():
    user_id = session['user_id']
    today = date.today()
    month = request.args.get('month', today.month)
    year = request.args.get('year', today.year)

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'set_budget':
            b_month = int(request.form.get('month', today.month))
            b_year = int(request.form.get('year', today.year))
            amount_raw = request.form.get('budget_amount', '').strip()

            try:
                budget_amount = float(amount_raw)
                if budget_amount <= 0:
                    flash("Budget amount must be greater than zero.", "danger")
                    cursor.close()
                    conn.close()
                    return redirect(url_for('budgets', month=b_month, year=b_year))
            except (ValueError, TypeError):
                flash("Please enter a valid numeric budget amount.", "danger")
                cursor.close()
                conn.close()
                return redirect(url_for('budgets', month=b_month, year=b_year))

            # Upsert budget record
            cursor.execute("""
                INSERT INTO budgets (user_id, month, year, budget_amount, created_at)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE budget_amount = VALUES(budget_amount)
            """, (user_id, b_month, b_year, budget_amount, datetime.now()))

            flash(f"Monthly budget for {b_month}/{b_year} successfully set to {format_currency_inr(budget_amount)}!", "success")
            cursor.close()
            conn.close()
            return redirect(url_for('budgets', month=b_month, year=b_year))

        elif action == 'delete_budget':
            b_id = request.form.get('budget_id')
            if b_id:
                cursor.execute("DELETE FROM budgets WHERE id = %s AND user_id = %s", (b_id, user_id))
                flash("Budget plan deleted successfully.", "info")
            cursor.close()
            conn.close()
            return redirect(url_for('budgets'))

    data = get_budget_dashboard_data(user_id, month=month, year=year, cursor=cursor)

    cursor.close()
    conn.close()
    return render_template('budgets.html', data=data)

# --------------------------------------------------------------------
# 6. Reports & CSV Export
# --------------------------------------------------------------------
@app.route('/reports')
@login_required
def reports():
    user_id = session['user_id']
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    category_id = request.args.get('category', '')

    today = date.today()
    if not start_date:
        start_date = date(today.year, today.month, 1).strftime('%Y-%m-%d')
    if not end_date:
        end_date = today.strftime('%Y-%m-%d')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, name FROM categories ORDER BY name ASC")
    categories = [{'id': r[0], 'name': r[1]} for r in cursor.fetchall()]

    where_clauses = ["e.user_id = %s", "e.expense_date BETWEEN %s AND %s"]
    params = [user_id, start_date, end_date]

    if category_id and category_id.isdigit():
        where_clauses.append("e.category_id = %s")
        params.append(int(category_id))

    where_sql = " AND ".join(where_clauses)

    cursor.execute(f"""
        SELECT e.id, e.title, e.amount, e.expense_date, e.notes,
               c.name as category_name, c.icon, c.color
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        WHERE {where_sql}
        ORDER BY e.expense_date DESC
    """, tuple(params))
    records = []
    total_sum = 0.0
    for r in cursor.fetchall():
        amt = float(r[2])
        total_sum += amt
        records.append({
            'id': r[0],
            'title': r[1],
            'amount': amt,
            'formatted_amount': format_currency_inr(amt),
            'date': r[3].strftime('%d/%m/%Y') if hasattr(r[3], 'strftime') else str(r[3]),
            'raw_date': str(r[3]),
            'notes': r[4] or '',
            'category_name': r[5],
            'category_icon': r[6],
            'category_color': r[7]
        })

    cursor.close()
    conn.close()

    return render_template(
        'reports.html',
        records=records,
        total_sum=total_sum,
        formatted_total=format_currency_inr(total_sum),
        categories=categories,
        start_date=start_date,
        end_date=end_date,
        selected_category=category_id,
        record_count=len(records)
    )

@app.route('/export-csv')
@login_required
def export_csv():
    user_id = session['user_id']
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    category_id = request.args.get('category')

    conn = get_db_connection()
    cursor = conn.cursor()

    where_clauses = ["e.user_id = %s"]
    params = [user_id]

    if start_date:
        where_clauses.append("e.expense_date >= %s")
        params.append(start_date)
    if end_date:
        where_clauses.append("e.expense_date <= %s")
        params.append(end_date)
    if category_id and category_id.isdigit():
        where_clauses.append("e.category_id = %s")
        params.append(int(category_id))

    where_sql = " AND ".join(where_clauses)

    cursor.execute(f"""
        SELECT e.expense_date, e.title, c.name as category_name, e.amount, e.notes, e.created_at
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        WHERE {where_sql}
        ORDER BY e.expense_date ASC
    """, tuple(params))
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    # Generate CSV stream
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Expense Date (DD/MM/YYYY)", "Expense Title", "Category", "Amount (INR)", "Notes", "Recorded At"])

    for r in rows:
        d_str = r[0].strftime('%d/%m/%Y') if hasattr(r[0], 'strftime') else str(r[0])
        c_str = r[5].strftime('%d/%m/%Y %H:%M:%S') if hasattr(r[5], 'strftime') else str(r[5])
        writer.writerow([d_str, r[1], r[2], f"{float(r[3]):.2f}", r[4] or '', c_str])

    output.seek(0)
    filename = f"Expense_Report_{date.today().strftime('%Y%m%d')}.csv"
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# --------------------------------------------------------------------
# 7. Profile & Settings
# --------------------------------------------------------------------
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'update_profile':
            full_name = request.form.get('full_name', '').strip()
            theme = request.form.get('theme', 'light')
            currency = request.form.get('currency', 'INR')

            if not full_name or len(full_name) < 2:
                flash("Full name must be at least 2 characters.", "danger")
            else:
                cursor.execute("""
                    UPDATE users SET full_name = %s, theme = %s, currency = %s
                    WHERE id = %s
                """, (full_name, theme, currency, user_id))
                session['user_name'] = full_name
                session['theme'] = theme
                session['currency'] = currency
                flash("Your profile preferences have been successfully updated.", "success")

        elif action == 'change_password':
            current_pwd = request.form.get('current_password', '')
            new_pwd = request.form.get('new_password', '')
            confirm_pwd = request.form.get('confirm_password', '')

            cursor.execute("SELECT password_hash FROM users WHERE id = %s", (user_id,))
            pwd_hash = cursor.fetchone()[0]

            if not check_password_hash(pwd_hash, current_pwd):
                flash("Current password entered is incorrect.", "danger")
            elif not new_pwd or len(new_pwd) < 6:
                flash("New password must be at least 6 characters long.", "danger")
            elif new_pwd != confirm_pwd:
                flash("New passwords do not match.", "danger")
            else:
                new_hash = generate_password_hash(new_pwd)
                cursor.execute("UPDATE users SET password_hash = %s WHERE id = %s", (new_hash, user_id))
                flash("Your password has been changed successfully.", "success")

    # Fetch user info & statistics
    cursor.execute("SELECT id, full_name, email, currency, theme, created_at FROM users WHERE id = %s", (user_id,))
    user_data = cursor.fetchone()

    cursor.execute("SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM expenses WHERE user_id = %s", (user_id,))
    stat_row = cursor.fetchone()
    total_tx = stat_row[0]
    total_spent = float(stat_row[1])

    user_info = {
        'id': user_data[0],
        'full_name': user_data[1],
        'email': user_data[2],
        'currency': user_data[3] or 'INR',
        'theme': user_data[4] or 'light',
        'created_at': user_data[5].strftime('%d %B %Y') if hasattr(user_data[5], 'strftime') else str(user_data[5]),
        'total_transactions': total_tx,
        'total_spent': total_spent,
        'formatted_total_spent': format_currency_inr(total_spent)
    }

    cursor.close()
    conn.close()
    return render_template('profile.html', user=user_info)

@app.route('/seed-demo-data', methods=['POST'])
@login_required
def seed_demo_data():
    """Academic helper route: seeds 27+ realistic sample expenses and budgets for demo."""
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    seed_sample_demo_data(user_id, cursor, conn)
    cursor.close()
    conn.close()
    flash("Realistic academic demonstration financial data has been loaded into your account!", "success")
    return redirect(url_for('dashboard'))

# --------------------------------------------------------------------
# 8. Error Handlers
# --------------------------------------------------------------------
@app.errorhandler(404)
def page_not_found(e):
    return render_template('base.html', error_code=404, error_message="Page Not Found"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('base.html', error_code=500, error_message="Internal Server Error"), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', '1') == '1'
    print(f"Personal Expense Tracker starting at http://127.0.0.1:{port} (Debug={debug})")
    app.run(host='127.0.0.1', port=port, debug=debug)
