# ── Template context ───────────────────────────────
@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}


# ═══════════════════════════════════════════════════
#  ADMIN PANEL
# ═══════════════════════════════════════════════════

ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'nqizbali2026')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        error = 'Incorrect password.'
    return render_template('admin_login.html', error=error)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    syndics   = Syndic.query.all()
    buildings = Building.query.all()
    payments  = Payment.query.order_by(Payment.created_at.desc()).all()
    clients   = Client.query.all()

    total_revenue   = sum(p.amount_mad for p in payments if p.status == 'approved')
    active_buildings= sum(1 for b in buildings if b.is_active)
    pending_payments= sum(1 for p in payments if p.status == 'pending')

    return render_template('admin_dashboard.html',
        syndics=syndics,
        buildings=buildings,
        payments=payments,
        clients=clients,
        total_revenue=total_revenue,
        active_buildings=active_buildings,
        pending_payments=pending_payments,
    )
