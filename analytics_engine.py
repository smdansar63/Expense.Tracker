import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from decimal import Decimal

def format_currency_inr(number):
    """
    Formats a numeric value into Indian Rupee format (e.g., ₹1,25,000.00).
    """
    if number is None:
        return "₹0.00"
    try:
        val = float(number)
    except (ValueError, TypeError):
        return "₹0.00"
    
    is_negative = val < 0
    val = abs(val)
    parts = f"{val:.2f}".split('.')
    integer_part = parts[0]
    decimal_part = parts[1]
    
    if len(integer_part) > 3:
        last_three = integer_part[-3:]
        remaining = integer_part[:-3]
        # Group in 2s
        groups = []
        while len(remaining) > 2:
            groups.insert(0, remaining[-2:])
            remaining = remaining[:-2]
        if remaining:
            groups.insert(0, remaining)
        formatted_int = ",".join(groups) + "," + last_three
    else:
        formatted_int = integer_part
        
    res = f"₹{formatted_int}.{decimal_part}"
    return f"-{res}" if is_negative else res

def calculate_dashboard_metrics(user_id, cursor):
    """
    Calculates summary KPIs and chart datasets for the user's dashboard.
    Uses Pandas for aggregation and statistical analysis.
    """
    today = date.today()
    current_month = today.month
    current_year = today.year

    # 1. Fetch all user expenses
    cursor.execute("""
        SELECT e.id, e.title, e.amount, e.expense_date, e.notes, e.created_at,
               c.id as category_id, c.name as category_name, c.icon, c.color
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        WHERE e.user_id = %s
        ORDER BY e.expense_date DESC, e.created_at DESC
    """, (user_id,))
    rows = cursor.fetchall()

    # Column names
    columns = ['id', 'title', 'amount', 'expense_date', 'notes', 'created_at',
               'category_id', 'category_name', 'icon', 'color']
    
    if rows:
        df = pd.DataFrame(rows, columns=columns)
        df['amount'] = df['amount'].astype(float)
        df['expense_date'] = pd.to_datetime(df['expense_date'])
        df['year'] = df['expense_date'].dt.year
        df['month'] = df['expense_date'].dt.month
    else:
        df = pd.DataFrame(columns=columns)

    # Total expenses (all-time)
    total_expenses = float(df['amount'].sum()) if not df.empty else 0.0
    total_transactions = len(df)
    avg_expense = float(df['amount'].mean()) if not df.empty else 0.0
    max_expense = float(df['amount'].max()) if not df.empty else 0.0

    # Current month's spending
    current_month_df = df[(df['year'] == current_year) & (df['month'] == current_month)] if not df.empty else pd.DataFrame(columns=columns)
    month_spending = float(current_month_df['amount'].sum()) if not current_month_df.empty else 0.0

    # Top spending category (current month if has data, else all-time)
    top_category = "N/A"
    top_category_icon = "fa-tags"
    top_category_color = "#6366f1"
    active_cat_df = current_month_df if not current_month_df.empty else df
    if not active_cat_df.empty:
        cat_group = active_cat_df.groupby(['category_name', 'icon', 'color'])['amount'].sum().reset_index()
        if not cat_group.empty:
            top_row = cat_group.sort_values(by='amount', ascending=False).iloc[0]
            top_category = top_row['category_name']
            top_category_icon = top_row['icon']
            top_category_color = top_row['color']

    # Budget info for current month
    cursor.execute("""
        SELECT budget_amount FROM budgets 
        WHERE user_id = %s AND month = %s AND year = %s
    """, (user_id, current_month, current_year))
    budget_row = cursor.fetchone()
    monthly_budget = float(budget_row[0]) if budget_row else 0.0
    remaining_budget = monthly_budget - month_spending if monthly_budget > 0 else 0.0
    budget_usage_pct = (month_spending / monthly_budget * 100) if monthly_budget > 0 else 0.0

    # Recent transactions (latest 6)
    cursor.execute("""
        SELECT e.id, e.title, e.amount, e.expense_date, e.notes,
               c.name as category_name, c.icon, c.color
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        WHERE e.user_id = %s
        ORDER BY e.expense_date DESC, e.created_at DESC
        LIMIT 6
    """, (user_id,))
    recent_tx_rows = cursor.fetchall()
    recent_transactions = []
    for r in recent_tx_rows:
        recent_transactions.append({
            'id': r[0],
            'title': r[1],
            'amount': float(r[2]),
            'formatted_amount': format_currency_inr(r[2]),
            'date': r[3].strftime('%d/%m/%Y') if hasattr(r[3], 'strftime') else str(r[3]),
            'raw_date': str(r[3]),
            'notes': r[4] or '',
            'category_name': r[5],
            'category_icon': r[6],
            'category_color': r[7]
        })

    # Charts data preparation
    # 1. Category breakdown (Donut)
    category_chart = {
        'labels': [],
        'data': [],
        'colors': []
    }
    if not active_cat_df.empty:
        cat_summary = active_cat_df.groupby(['category_name', 'color'])['amount'].sum().reset_index()
        cat_summary = cat_summary.sort_values(by='amount', ascending=False)
        category_chart['labels'] = cat_summary['category_name'].tolist()
        category_chart['data'] = [round(float(x), 2) for x in cat_summary['amount'].tolist()]
        category_chart['colors'] = cat_summary['color'].tolist()

    # 2. Monthly spending trend (Last 6 Months)
    monthly_chart = {
        'labels': [],
        'data': []
    }
    # Generate labels for past 6 months
    past_months = []
    curr = datetime(current_year, current_month, 1)
    for i in range(5, -1, -1):
        # subtract months safely
        m = curr.month - i
        y = curr.year
        while m <= 0:
            m += 12
            y -= 1
        past_months.append((y, m))

    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    for y, m in past_months:
        label = f"{month_names[m-1]} '{str(y)[2:]}"
        monthly_chart['labels'].append(label)
        if not df.empty:
            m_sum = df[(df['year'] == y) & (df['month'] == m)]['amount'].sum()
            monthly_chart['data'].append(round(float(m_sum), 2))
        else:
            monthly_chart['data'].append(0.0)

    # 3. Daily Spending Trend (Current Month)
    daily_chart = {
        'labels': [],
        'data': []
    }
    if not current_month_df.empty:
        daily_grp = current_month_df.groupby(current_month_df['expense_date'].dt.strftime('%d %b'))['amount'].sum().reset_index()
        daily_chart['labels'] = daily_grp['expense_date'].tolist()
        daily_chart['data'] = [round(float(x), 2) for x in daily_grp['amount'].tolist()]

    return {
        'total_expenses': total_expenses,
        'formatted_total_expenses': format_currency_inr(total_expenses),
        'month_spending': month_spending,
        'formatted_month_spending': format_currency_inr(month_spending),
        'avg_expense': avg_expense,
        'formatted_avg_expense': format_currency_inr(avg_expense),
        'max_expense': max_expense,
        'formatted_max_expense': format_currency_inr(max_expense),
        'top_category': top_category,
        'top_category_icon': top_category_icon,
        'top_category_color': top_category_color,
        'total_transactions': total_transactions,
        'monthly_budget': monthly_budget,
        'formatted_monthly_budget': format_currency_inr(monthly_budget),
        'remaining_budget': remaining_budget,
        'formatted_remaining_budget': format_currency_inr(remaining_budget),
        'budget_usage_pct': round(budget_usage_pct, 1),
        'recent_transactions': recent_transactions,
        'category_chart': category_chart,
        'monthly_chart': monthly_chart,
        'daily_chart': daily_chart,
        'current_month_name': today.strftime('%B %Y')
    }

def get_detailed_analytics(user_id, period_filter='this_month', custom_start=None, custom_end=None, cursor=None):
    """
    Calculates detailed financial analytics, statistical distributions,
    and period comparisons using Pandas and NumPy.
    """
    today = date.today()
    start_date = None
    end_date = today

    # Determine date range based on period filter
    if period_filter == 'today':
        start_date = today
    elif period_filter == 'this_week':
        # Start of current week (Monday)
        start_date = today - timedelta(days=today.weekday())
    elif period_filter == 'this_month':
        start_date = date(today.year, today.month, 1)
    elif period_filter == 'this_year':
        start_date = date(today.year, 1, 1)
    elif period_filter == 'all_time':
        start_date = date(2000, 1, 1)
    elif period_filter == 'custom':
        if custom_start:
            try:
                start_date = datetime.strptime(custom_start, '%Y-%m-%d').date()
            except ValueError:
                start_date = date(today.year, today.month, 1)
        else:
            start_date = date(today.year, today.month, 1)
            
        if custom_end:
            try:
                end_date = datetime.strptime(custom_end, '%Y-%m-%d').date()
            except ValueError:
                end_date = today
    else:
        start_date = date(today.year, today.month, 1)

    # Fetch period expenses
    cursor.execute("""
        SELECT e.id, e.title, e.amount, e.expense_date, e.notes,
               c.id as category_id, c.name as category_name, c.icon, c.color
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        WHERE e.user_id = %s AND e.expense_date BETWEEN %s AND %s
        ORDER BY e.expense_date ASC
    """, (user_id, start_date, end_date))
    period_rows = cursor.fetchall()

    columns = ['id', 'title', 'amount', 'expense_date', 'notes',
               'category_id', 'category_name', 'icon', 'color']
    
    if period_rows:
        df = pd.DataFrame(period_rows, columns=columns)
        df['amount'] = df['amount'].astype(float)
        df['expense_date'] = pd.to_datetime(df['expense_date'])
    else:
        df = pd.DataFrame(columns=columns)

    # Summary statistics with Pandas & NumPy
    if not df.empty:
        total_expenditure = float(df['amount'].sum())
        transaction_count = len(df)
        avg_expense = float(df['amount'].mean())
        median_expense = float(df['amount'].median())
        max_expense = float(df['amount'].max())
        min_expense = float(df['amount'].min())
        std_expense = float(df['amount'].std()) if transaction_count > 1 else 0.0
        
        # Calculate daily average across the active days
        num_days = max(1, (end_date - start_date).days + 1)
        daily_average = total_expenditure / num_days
    else:
        total_expenditure = 0.0
        transaction_count = 0
        avg_expense = 0.0
        median_expense = 0.0
        max_expense = 0.0
        min_expense = 0.0
        std_expense = 0.0
        daily_average = 0.0

    # Category Breakdown aggregation
    category_breakdown = []
    category_chart_labels = []
    category_chart_data = []
    category_chart_colors = []
    most_expensive_category = "N/A"
    most_expensive_cat_amount = 0.0

    if not df.empty:
        cat_grouped = df.groupby(['category_id', 'category_name', 'icon', 'color']).agg(
            total_amount=('amount', 'sum'),
            tx_count=('amount', 'count'),
            avg_amount=('amount', 'mean')
        ).reset_index().sort_values(by='total_amount', ascending=False)

        for _, row in cat_grouped.iterrows():
            pct = (row['total_amount'] / total_expenditure * 100) if total_expenditure > 0 else 0
            category_breakdown.append({
                'name': row['category_name'],
                'icon': row['icon'],
                'color': row['color'],
                'total_amount': float(row['total_amount']),
                'formatted_amount': format_currency_inr(row['total_amount']),
                'count': int(row['tx_count']),
                'average': float(row['avg_amount']),
                'formatted_average': format_currency_inr(row['avg_amount']),
                'percentage': round(pct, 1)
            })
            category_chart_labels.append(row['category_name'])
            category_chart_data.append(round(float(row['total_amount']), 2))
            category_chart_colors.append(row['color'])

        if not cat_grouped.empty:
            most_expensive_category = cat_grouped.iloc[0]['category_name']
            most_expensive_cat_amount = float(cat_grouped.iloc[0]['total_amount'])

    # Day of Week Distribution (Monday - Sunday)
    dow_labels = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    dow_data = [0.0] * 7
    if not df.empty:
        dow_series = df.groupby(df['expense_date'].dt.day_name())['amount'].sum()
        for i, day in enumerate(dow_labels):
            if day in dow_series:
                dow_data[i] = round(float(dow_series[day]), 2)

    # Daily / Weekly Trend Time Series
    trend_labels = []
    trend_data = []
    if not df.empty:
        daily_series = df.groupby(df['expense_date'].dt.strftime('%d %b'))['amount'].sum().reset_index()
        trend_labels = daily_series['expense_date'].tolist()
        trend_data = [round(float(x), 2) for x in daily_series['amount'].tolist()]

    # Previous Month Comparison
    # Calculate previous calendar month spending
    prev_month_date = date(today.year, today.month, 1) - timedelta(days=1)
    prev_month_start = date(prev_month_date.year, prev_month_date.month, 1)
    prev_month_end = prev_month_date

    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0) FROM expenses
        WHERE user_id = %s AND expense_date BETWEEN %s AND %s
    """, (user_id, prev_month_start, prev_month_end))
    prev_month_total = float(cursor.fetchone()[0])

    # Current calendar month total
    curr_month_start = date(today.year, today.month, 1)
    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0) FROM expenses
        WHERE user_id = %s AND expense_date BETWEEN %s AND %s
    """, (user_id, curr_month_start, today))
    curr_month_total = float(cursor.fetchone()[0])

    # Percentage difference compared to previous month
    if prev_month_total > 0:
        mom_change_pct = ((curr_month_total - prev_month_total) / prev_month_total) * 100
    else:
        mom_change_pct = 100.0 if curr_month_total > 0 else 0.0

    return {
        'period_filter': period_filter,
        'start_date_str': start_date.strftime('%d/%m/%Y'),
        'end_date_str': end_date.strftime('%d/%m/%Y'),
        'raw_start': start_date.strftime('%Y-%m-%d'),
        'raw_end': end_date.strftime('%Y-%m-%d'),
        'total_expenditure': total_expenditure,
        'formatted_total': format_currency_inr(total_expenditure),
        'transaction_count': transaction_count,
        'avg_expense': avg_expense,
        'formatted_avg': format_currency_inr(avg_expense),
        'median_expense': median_expense,
        'formatted_median': format_currency_inr(median_expense),
        'max_expense': max_expense,
        'formatted_max': format_currency_inr(max_expense),
        'min_expense': min_expense,
        'formatted_min': format_currency_inr(min_expense),
        'std_expense': std_expense,
        'daily_average': daily_average,
        'formatted_daily_avg': format_currency_inr(daily_average),
        'most_expensive_category': most_expensive_category,
        'formatted_most_expensive_cat': format_currency_inr(most_expensive_cat_amount),
        'category_breakdown': category_breakdown,
        'category_chart': {
            'labels': category_chart_labels,
            'data': category_chart_data,
            'colors': category_chart_colors
        },
        'trend_chart': {
            'labels': trend_labels,
            'data': trend_data
        },
        'dow_chart': {
            'labels': dow_labels,
            'data': dow_data
        },
        'prev_month_total': prev_month_total,
        'formatted_prev_month': format_currency_inr(prev_month_total),
        'curr_month_total': curr_month_total,
        'formatted_curr_month': format_currency_inr(curr_month_total),
        'mom_change_pct': round(mom_change_pct, 1),
        'mom_is_increase': mom_change_pct > 0
    }

def get_budget_dashboard_data(user_id, month=None, year=None, cursor=None):
    """
    Computes budget analysis for a given month and historical 6-month comparisons.
    Handles warning states: normal (<80%), warning (80-100%), exceeded (>100%).
    """
    today = date.today()
    if not month:
        month = today.month
    if not year:
        year = today.year

    month = int(month)
    year = int(year)

    # 1. Fetch budget for this month
    cursor.execute("""
        SELECT budget_amount FROM budgets
        WHERE user_id = %s AND month = %s AND year = %s
    """, (user_id, month, year))
    row = cursor.fetchone()
    budget_amount = float(row[0]) if row else 0.0

    # 2. Fetch spending for this month
    start_d = date(year, month, 1)
    if month == 12:
        end_d = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_d = date(year, month + 1, 1) - timedelta(days=1)

    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0), COUNT(*) FROM expenses
        WHERE user_id = %s AND expense_date BETWEEN %s AND %s
    """, (user_id, start_d, end_d))
    spend_row = cursor.fetchone()
    total_spent = float(spend_row[0]) if spend_row else 0.0
    tx_count = int(spend_row[1]) if spend_row else 0

    remaining = budget_amount - total_spent
    usage_pct = (total_spent / budget_amount * 100) if budget_amount > 0 else 0.0

    # Determine alert status
    if budget_amount == 0:
        status = 'not_set'
        status_label = 'No Budget Configured'
        status_color = 'slate'
    elif total_spent > budget_amount:
        status = 'exceeded'
        status_label = f'Budget Exceeded by {format_currency_inr(total_spent - budget_amount)}'
        status_color = 'danger'
    elif usage_pct >= 80.0:
        status = 'warning'
        status_label = f'Warning: {round(usage_pct, 1)}% of Budget Utilized'
        status_color = 'warning'
    else:
        status = 'normal'
        status_label = 'Within Healthy Budget'
        status_color = 'success'

    # Historical 6-month comparison (Budgets vs Actual)
    hist_labels = []
    hist_budgets = []
    hist_spent = []
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    curr = datetime(year, month, 1)
    for i in range(5, -1, -1):
        m = curr.month - i
        y = curr.year
        while m <= 0:
            m += 12
            y -= 1
        label = f"{month_names[m-1]} {y}"
        hist_labels.append(label)

        # Budget query
        cursor.execute("SELECT budget_amount FROM budgets WHERE user_id = %s AND month = %s AND year = %s", (user_id, m, y))
        b_val = cursor.fetchone()
        hist_budgets.append(float(b_val[0]) if b_val else 0.0)

        # Spend query
        m_start = date(y, m, 1)
        if m == 12:
            m_end = date(y + 1, 1, 1) - timedelta(days=1)
        else:
            m_end = date(y, m + 1, 1) - timedelta(days=1)

        cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE user_id = %s AND expense_date BETWEEN %s AND %s", (user_id, m_start, m_end))
        s_val = cursor.fetchone()
        hist_spent.append(float(s_val[0]) if s_val else 0.0)

    # All user saved budgets list
    cursor.execute("""
        SELECT b.id, b.month, b.year, b.budget_amount,
               COALESCE((
                   SELECT SUM(e.amount) FROM expenses e 
                   WHERE e.user_id = b.user_id 
                   AND MONTH(e.expense_date) = b.month 
                   AND YEAR(e.expense_date) = b.year
               ), 0) as spent
        FROM budgets b
        WHERE b.user_id = %s
        ORDER BY b.year DESC, b.month DESC
    """, (user_id,))
    budget_history = []
    for r in cursor.fetchall():
        b_amt = float(r[3])
        s_amt = float(r[4])
        b_rem = b_amt - s_amt
        b_pct = (s_amt / b_amt * 100) if b_amt > 0 else 0
        budget_history.append({
            'id': r[0],
            'month': r[1],
            'month_name': month_names[r[1] - 1],
            'year': r[2],
            'budget_amount': b_amt,
            'formatted_budget': format_currency_inr(b_amt),
            'spent': s_amt,
            'formatted_spent': format_currency_inr(s_amt),
            'remaining': b_rem,
            'formatted_remaining': format_currency_inr(b_rem),
            'usage_pct': round(b_pct, 1),
            'is_exceeded': s_amt > b_amt
        })

    return {
        'selected_month': month,
        'selected_year': year,
        'month_name': month_names[month - 1],
        'budget_amount': budget_amount,
        'formatted_budget': format_currency_inr(budget_amount),
        'total_spent': total_spent,
        'formatted_spent': format_currency_inr(total_spent),
        'remaining': remaining,
        'formatted_remaining': format_currency_inr(remaining),
        'usage_pct': round(usage_pct, 1),
        'status': status,
        'status_label': status_label,
        'status_color': status_color,
        'tx_count': tx_count,
        'hist_chart': {
            'labels': hist_labels,
            'budgets': hist_budgets,
            'spent': hist_spent
        },
        'budget_history': budget_history
    }

def seed_sample_demo_data(user_id, cursor, conn):
    """
    Populates realistic academic demo financial data for the given user:
    - 3 months of diverse expenses (Food, Transport, Bills, Entertainment, Health, Shopping, Misc)
    - Budgets for current and past months
    """
    today = date.today()
    
    # 1. Clear existing expenses and budgets for this user to avoid conflicts
    cursor.execute("DELETE FROM expenses WHERE user_id = %s", (user_id,))
    cursor.execute("DELETE FROM budgets WHERE user_id = %s", (user_id,))

    # 2. Sample expenses template across the last 60 days
    sample_records = [
        # Recent current month expenses
        ("Organic Grocery Basket", 3250.00, 1, 1, "Weekly fruits, vegetables, and provisions"),
        ("Monthly High-Speed Fiber Internet", 1179.00, 3, 2, "Airtel Xstream Fiber broadband plan"),
        ("Weekend Dining at Olive Bistro", 2480.00, 1, 3, "Family dinner & beverages"),
        ("Petrol Refill for Car", 2500.00, 2, 4, "Indian Oil XP95 tank top-up"),
        ("Netflix & Spotify Subscription", 849.00, 4, 5, "Monthly entertainment auto-debit"),
        ("Electricity Bill Payment", 3840.00, 3, 6, "State Electricity Board bill payment"),
        ("Annual Health Checkup & Labs", 4500.00, 5, 8, "Apollo Diagnostics comprehensive panel"),
        ("Formal Shirts & Casual Wear", 4299.00, 6, 10, "Allen Solly sale weekend shopping"),
        ("Metro Smart Card Recharge", 500.00, 2, 12, "Delhi/Bangalore metro monthly commute"),
        ("Specialty Coffee & Bakery", 480.00, 1, 13, "Blue Tokai pour-over and croissant"),
        ("Prescription Medicines", 1250.00, 5, 15, "PharmEasy monthly health maintenance"),
        ("Cinema Tickets - IMAX 3D", 950.00, 4, 16, "PVR Cinemas weekend movie tickets"),
        ("Home Hardware & Repairs", 750.00, 7, 18, "Plumbing fixtures and tools"),
        ("Uber Airport Commute", 1120.00, 2, 19, "Cab ride from City Center to Airport"),
        ("Gourmet Pizza Dinner Delivery", 890.00, 1, 21, "Swiggy dinner order with friends"),
        ("Mobile Postpaid Family Plan", 1499.00, 3, 22, "Jio 5G family postpaid bill"),
        ("Wireless Noise-Canceling Earbuds", 4999.00, 6, 25, "OnePlus Buds Pro 2 from Amazon"),
        
        # Previous month expenses
        ("Supermarket Monthly Ration", 8400.00, 1, 32, "DMart grocery shopping"),
        ("Vehicle Servicing & Oil Change", 5600.00, 2, 35, "Authorised Hyundai service center"),
        ("LPG Gas Cylinder Refill", 950.00, 3, 38, "Indane 14.2kg domestic cylinder"),
        ("Dining Out - Barbeque Nation", 3100.00, 1, 40, "Celebration buffet dinner"),
        ("Dental Cleaning & Consultation", 1800.00, 5, 43, "Clove Dental clinic visit"),
        ("Amazon Prime Annual Renewal", 1499.00, 4, 46, "Annual membership renewal"),
        ("Gym Membership Quarterly", 4500.00, 5, 50, "Cult.fit quarterly fitness subscription"),
        ("Books & Online Tech Courses", 1650.00, 7, 52, "Data Engineering & Python course"),
        ("Casual Shoes & Sneaker Care", 3499.00, 6, 55, "Nike everyday sneakers"),
        ("Weekend Cab Travel", 820.00, 2, 58, "Ola city rides")
    ]

    for title, amount, cat_id, days_ago, notes in sample_records:
        exp_date = today - timedelta(days=days_ago)
        created_at = datetime.combine(exp_date, datetime.min.time()) + timedelta(hours=14, minutes=30)
        cursor.execute("""
            INSERT INTO expenses (user_id, title, amount, category_id, expense_date, notes, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (user_id, title, amount, cat_id, exp_date, notes, created_at))

    # 3. Insert realistic budgets
    # Current month budget: ₹45,000
    cursor.execute("""
        INSERT INTO budgets (user_id, month, year, budget_amount, created_at)
        VALUES (%s, %s, %s, %s, %s)
    """, (user_id, today.month, today.year, 45000.00, datetime.now()))

    # Previous month budget: ₹40,000
    prev_m_date = today - timedelta(days=35)
    cursor.execute("""
        INSERT INTO budgets (user_id, month, year, budget_amount, created_at)
        VALUES (%s, %s, %s, %s, %s)
    """, (user_id, prev_m_date.month, prev_m_date.year, 40000.00, datetime.now()))

    conn.commit()
    return True
