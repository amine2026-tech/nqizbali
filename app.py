from flask import (Flask, render_template, request, jsonify,
                   redirect, url_for, session)
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import hashlib, os, uuid, random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///nqizbali.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'nqizbali-dev-secret')

CMI_MERCHANT_ID  = os.environ.get('CMI_MERCHANT_ID',  'TEST_MERCHANT')
CMI_STORE_KEY    = os.environ.get('CMI_STORE_KEY',     'TEST_STORE_KEY')
CMI_BASE_URL     = os.environ.get('CMI_BASE_URL',
                   'https://testpayment.cmi.co.ma/fim/est3Dgate')
PRICE_PER_APT    = 60
ADMIN_PASSWORD   = os.environ.get('ADMIN_PASSWORD', 'nqizbali2026')

db = SQLAlchemy(app)

# ═══════════════════════════════════════════════════
#  MODELS
# ═══════════════════════════════════════════════════

class Syndic(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(120), nullable=False)
    phone         = db.Column(db.String(30),  nullable=False)
    email         = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    approved      = db.Column(db.Boolean, default=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    buildings     = db.relationship('Building', backref='syndic', lazy=True)

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)


class Building(db.Model):
    id                  = db.Column(db.Integer, primary_key=True)
    syndic_id           = db.Column(db.Integer, db.ForeignKey('syndic.id'), nullable=False)
    name                = db.Column(db.String(150), nullable=False)
    address             = db.Column(db.String(250), nullable=False)
    neighborhood        = db.Column(db.String(100), nullable=False)
    nb_apartments       = db.Column(db.Integer, nullable=False, default=1)
    lat                 = db.Column(db.Float, default=31.6258)
    lng                 = db.Column(db.Float, default=-8.0038)
    subscription_active = db.Column(db.Boolean, default=False)
    subscription_end    = db.Column(db.DateTime, nullable=True)
    clients             = db.relationship('Client', backref='building', lazy=True)
    payments            = db.relationship('Payment', backref='building', lazy=True)

    @property
    def monthly_total(self):
        return self.nb_apartments * PRICE_PER_APT

    @property
    def is_active(self):
        if not self.subscription_active:
            return False
        if self.subscription_end and datetime.utcnow() > self.subscription_end:
            return False
        return True


class Client(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    building_id  = db.Column(db.Integer, db.ForeignKey('building.id'), nullable=True)
    name         = db.Column(db.String(100), nullable=False)
    address      = db.Column(db.String(200), nullable=False)
    neighborhood = db.Column(db.String(100), nullable=False)
    qr_code      = db.Column(db.String(50), unique=True, nullable=False)
    trash_ready  = db.Column(db.Boolean, default=False)
    status       = db.Column(db.String(50), default='not_ready')
    lat          = db.Column(db.Float, default=31.6258)
    lng          = db.Column(db.Float, default=-8.0038)
    email        = db.Column(db.String(150), nullable=True)
    phone        = db.Column(db.String(30), nullable=True)
    otp_code     = db.Column(db.String(6), nullable=True)
    otp_expiry   = db.Column(db.DateTime, nullable=True)

    @property
    def subscription_active(self):
        if self.building:
            return self.building.is_active
        return False


class Collection(db.Model):
    id               = db.Column(db.Integer, primary_key=True)
    client_id        = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    collector_name   = db.Column(db.String(100), nullable=False)
    collected_at     = db.Column(db.DateTime, default=datetime.utcnow)
    status           = db.Column(db.String(50), default='collected')
    violation_reason = db.Column(db.String(200), nullable=True)


class Payment(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    building_id   = db.Column(db.Integer, db.ForeignKey('building.id'), nullable=False)
    syndic_id     = db.Column(db.Integer, db.ForeignKey('syndic.id'), nullable=False)
    ref           = db.Column(db.String(64), unique=True, nullable=False)
    amount_mad    = db.Column(db.Integer, nullable=False)
    nb_apartments = db.Column(db.Integer, nullable=False)
    status        = db.Column(db.String(30), default='pending')
    cmi_approval  = db.Column(db.String(30), nullable=True)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    paid_at       = db.Column(db.DateTime, nullable=True)
    syndic        = db.relationship('Syndic', backref='payments')


# ═══════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════

def syndic_login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'syndic_id' not in session:
            return redirect(url_for('syndic_login'))
        return f(*args, **kwargs)
    return decorated

def resident_login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'client_id' not in session:
            return redirect(url_for('resident_login'))
        return f(*args, **kwargs)
    return decorated

def cmi_build_form(payment, building, syndic):
    ok_url   = url_for('cmi_callback_ok',   _external=True)
    fail_url = url_for('cmi_callback_fail', _external=True)
    shop_url = url_for('syndic_dashboard',  _external=True)
    params = {
        'clientid':      CMI_MERCHANT_ID,
        'amount':        f'{payment.amount_mad:.2f}',
        'currency':      '504',
        'oid':           payment.ref,
        'okUrl':         ok_url,
        'failUrl':       fail_url,
        'shopurl':       shop_url,
        'callbackUrl':   url_for('cmi_webhook', _external=True),
        'TranType':      'PreAuth',
        'instalment':    '',
        'rnd':           payment.ref[-8:],
        'lang':          'en',
        'BillToName':    syndic.name,
        'BillToEmail':   syndic.email,
        'BillToCompany': building.name,
        'description':   f'NqiZbali — {building.name} — {building.nb_apartments} apts — {datetime.utcnow().strftime("%m/%Y")}',
        'storetype':     '3D_PAY_HOSTING',
        'hashAlgorithm': 'ver3',
    }
    hash_str = '|'.join([
        CMI_MERCHANT_ID, params['oid'], params['amount'], params['currency'],
        params['okUrl'], params['failUrl'], params['TranType'], params['instalment'],
        params['rnd'], params['storetype'], params['lang'], params['BillToName'],
        params['description'], CMI_STORE_KEY,
    ])
    params['HASH'] = hashlib.sha512(hash_str.encode()).hexdigest().upper()
    return params


# ═══════════════════════════════════════════════════
#  PUBLIC ROUTES
# ═══════════════════════════════════════════════════

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/collector')
def collector_view():
    return render_template('collector.html')


# ═══════════════════════════════════════════════════
#  RESIDENT AUTH
# ═══════════════════════════════════════════════════

@app.route('/client')
def client_view():
    if 'client_id' not in session:
        return redirect(url_for('resident_login'))
    return render_template('client.html')

@app.route('/resident/login', methods=['GET', 'POST'])
def resident_login():
    error = None
    if request.method == 'POST':
        qr_code = request.form.get('qr_code', '').strip().upper()
        phone   = request.form.get('phone', '').strip()
        client  = Client.query.filter_by(qr_code=qr_code).first()
        if not client:
            error = 'QR code not found. Check the sticker on your door.'
        else:
            # Save phone if first time
            if not client.phone:
                client.phone = phone
            # Generate OTP
            otp = str(random.randint(100000, 999999))
            client.otp_code   = otp
            client.otp_expiry = datetime.utcnow() + timedelta(minutes=5)
            db.session.commit()
            session['otp_client_id'] = client.id
            # In production: send SMS here
            # For now: store in session for display
            session['dev_otp'] = otp
            return redirect(url_for('resident_verify'))
    return render_template('resident_login.html', error=error)

@app.route('/resident/verify', methods=['GET', 'POST'])
def resident_verify():
    client_id = session.get('otp_client_id')
    if not client_id:
        return redirect(url_for('resident_login'))
    client  = Client.query.get(client_id)
    dev_otp = session.get('dev_otp')
    error   = None
    if request.method == 'POST':
        entered = request.form.get('otp', '').strip()
        if not client.otp_code or not client.otp_expiry:
            error = 'OTP expired. Please try again.'
        elif datetime.utcnow() > client.otp_expiry:
            error = 'OTP expired. Please request a new one.'
        elif entered != client.otp_code:
            error = 'Incorrect code. Please try again.'
        else:
            # Clear OTP
            client.otp_code   = None
            client.otp_expiry = None
            db.session.commit()
            session.pop('otp_client_id', None)
            session.pop('dev_otp', None)
            session['client_id']   = client.id
            session['client_name'] = client.name
            return redirect(url_for('client_view'))
    return render_template('resident_verify.html',
                           client=client, error=error, dev_otp=dev_otp)

@app.route('/resident/logout')
def resident_logout():
    session.pop('client_id', None)
    session.pop('client_name', None)
    return redirect(url_for('resident_login'))


# ═══════════════════════════════════════════════════
#  SYNDIC AUTH
# ═══════════════════════════════════════════════════

@app.route('/syndic/login', methods=['GET', 'POST'])
def syndic_login():
    error = None
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        pw    = request.form.get('password', '')
        s = Syndic.query.filter_by(email=email).first()
        if s and s.check_password(pw):
            if not s.approved:
                error = 'Your account is pending approval. Please contact NqiZbali admin.'
            else:
                session['syndic_id']   = s.id
                session['syndic_name'] = s.name
                return redirect(url_for('syndic_dashboard'))
        else:
            error = 'Incorrect email or password.'
    return render_template('syndic_login.html', error=error)

@app.route('/syndic/register', methods=['GET', 'POST'])
def syndic_register():
    error   = None
    success = False
    if request.method == 'POST':
        name  = request.form.get('name',  '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip().lower()
        pw    = request.form.get('password', '')
        if Syndic.query.filter_by(email=email).first():
            error = 'This email is already registered.'
        elif len(pw) < 6:
            error = 'Password must be at least 6 characters.'
        else:
            s = Syndic(name=name, phone=phone, email=email, approved=False)
            s.set_password(pw)
            db.session.add(s)
            db.session.commit()
            success = True
    return render_template('syndic_register.html', error=error, success=success)

@app.route('/syndic/logout')
def syndic_logout():
    session.clear()
    return redirect(url_for('syndic_login'))


# ═══════════════════════════════════════════════════
#  SYNDIC DASHBOARD
# ═══════════════════════════════════════════════════

@app.route('/syndic/dashboard')
@syndic_login_required
def syndic_dashboard():
    syndic    = Syndic.query.get(session['syndic_id'])
    buildings = Building.query.filter_by(syndic_id=syndic.id).all()
    for b in buildings:
        if b.subscription_active and b.subscription_end and datetime.utcnow() > b.subscription_end:
            b.subscription_active = False
            db.session.commit()
    return render_template('syndic_dashboard.html', syndic=syndic,
                           buildings=buildings, price_per_apt=PRICE_PER_APT)

@app.route('/syndic/building/add', methods=['GET', 'POST'])
@syndic_login_required
def syndic_add_building():
    error = None
    if request.method == 'POST':
        try:
            b = Building(
                syndic_id     = session['syndic_id'],
                name          = request.form['name'].strip(),
                address       = request.form['address'].strip(),
                neighborhood  = request.form['neighborhood'].strip(),
                nb_apartments = int(request.form['nb_apartments']),
                lat           = float(request.form.get('lat', 31.6258)),
                lng           = float(request.form.get('lng', -8.0038)),
            )
            db.session.add(b)
            db.session.commit()
            return redirect(url_for('syndic_dashboard'))
        except Exception as e:
            error = str(e)
    return render_template('syndic_add_building.html', error=error,
                           price_per_apt=PRICE_PER_APT)

@app.route('/syndic/building/<int:building_id>/pay')
@syndic_login_required
def syndic_pay(building_id):
    building = Building.query.get_or_404(building_id)
    syndic   = Syndic.query.get(session['syndic_id'])
    if building.syndic_id != syndic.id:
        return redirect(url_for('syndic_dashboard'))
    ref = f'NQZ-{building_id}-{uuid.uuid4().hex[:8].upper()}'
    payment = Payment(
        building_id   = building.id,
        syndic_id     = syndic.id,
        ref           = ref,
        amount_mad    = building.monthly_total,
        nb_apartments = building.nb_apartments,
        status        = 'pending',
    )
    db.session.add(payment)
    db.session.commit()
    cmi_params = cmi_build_form(payment, building, syndic)
    return render_template('syndic_pay.html', building=building,
                           syndic=syndic, payment=payment,
                           cmi_params=cmi_params, cmi_url=CMI_BASE_URL)


# ═══════════════════════════════════════════════════
#  CMI CALLBACKS
# ═══════════════════════════════════════════════════

@app.route('/cmi/ok', methods=['GET', 'POST'])
def cmi_callback_ok():
    oid      = request.values.get('oid', '')
    approval = request.values.get('AuthCode', '')
    _confirm_payment(oid, approval)
    payment  = Payment.query.filter_by(ref=oid).first()
    building = payment.building if payment else None
    return render_template('payment_success.html', building=building, approval=approval)

@app.route('/cmi/fail', methods=['GET', 'POST'])
def cmi_callback_fail():
    oid     = request.values.get('oid', '')
    payment = Payment.query.filter_by(ref=oid).first()
    if payment:
        payment.status = 'failed'
        db.session.commit()
    building = payment.building if payment else None
    return render_template('payment_cancel.html', building=building)

@app.route('/cmi/webhook', methods=['POST'])
def cmi_webhook():
    oid      = request.form.get('oid', '')
    response = request.form.get('Response', '')
    approval = request.form.get('AuthCode', '')
    if response == 'Approved':
        _confirm_payment(oid, approval)
    return 'OK'

def _confirm_payment(ref, approval_code=''):
    payment = Payment.query.filter_by(ref=ref).first()
    if not payment or payment.status == 'approved':
        return
    payment.status       = 'approved'
    payment.cmi_approval = approval_code
    payment.paid_at      = datetime.utcnow()
    building = Building.query.get(payment.building_id)
    if building:
        building.subscription_active = True
        building.subscription_end    = datetime.utcnow() + timedelta(days=30)
    db.session.commit()

@app.route('/dev/simulate-payment/<ref>', methods=['POST'])
def dev_simulate_payment(ref):
    if os.environ.get('FLASK_ENV') == 'production':
        return jsonify({'error': 'Not available in production'}), 403
    _confirm_payment(ref, approval_code='TEST-OK')
    return jsonify({'success': True})


# ═══════════════════════════════════════════════════
#  CLIENT / COLLECTOR API
# ═══════════════════════════════════════════════════

@app.route('/api/clients', methods=['GET'])
def get_clients():
    clients = Client.query.all()
    return jsonify([_client_dict(c) for c in clients])

@app.route('/api/client/me', methods=['GET'])
def get_my_client():
    client_id = session.get('client_id')
    if not client_id:
        return jsonify({'error': 'Not logged in'}), 401
    c = Client.query.get_or_404(client_id)
    return jsonify(_client_dict(c))

@app.route('/api/client/<int:client_id>', methods=['GET'])
def get_client(client_id):
    return jsonify(_client_dict(Client.query.get_or_404(client_id)))

def _client_dict(c):
    return {
        'id': c.id, 'name': c.name, 'address': c.address,
        'neighborhood': c.neighborhood, 'qr_code': c.qr_code,
        'status': c.status, 'trash_ready': c.trash_ready,
        'lat': c.lat, 'lng': c.lng,
        'subscription_active': c.subscription_active,
        'building_id': c.building_id,
    }

@app.route('/api/trash_ready/<int:client_id>', methods=['POST'])
def toggle_trash_ready(client_id):
    client = Client.query.get_or_404(client_id)
    if not client.subscription_active:
        return jsonify({'success': False, 'error': 'subscription_required',
                        'message': "Your building's subscription is not active."}), 403
    client.trash_ready = not client.trash_ready
    client.status      = 'ready' if client.trash_ready else 'not_ready'
    db.session.commit()
    return jsonify({'success': True, 'status': client.status})

@app.route('/api/collect/<int:client_id>', methods=['POST'])
def collect(client_id):
    client = Client.query.get_or_404(client_id)
    client.status = 'collected'
    client.trash_ready = False
    data = request.get_json() or {}
    db.session.add(Collection(client_id=client_id,
                              collector_name=data.get('collector', 'Collector'),
                              status='collected'))
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/violation/<int:client_id>', methods=['POST'])
def report_violation(client_id):
    client = Client.query.get_or_404(client_id)
    client.status = 'violation'
    data = request.get_json() or {}
    db.session.add(Collection(client_id=client_id,
                              collector_name=data.get('collector', 'Collector'),
                              status='violation',
                              violation_reason=data.get('reason', '')))
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/collections/<int:client_id>', methods=['GET'])
def get_collections(client_id):
    cols = Collection.query.filter_by(client_id=client_id)\
               .order_by(Collection.collected_at.desc()).limit(10).all()
    return jsonify([{
        'collector': c.collector_name,
        'date': c.collected_at.strftime('%d/%m/%Y %H:%M'),
        'status': c.status,
        'reason': c.violation_reason
    } for c in cols])


# ═══════════════════════════════════════════════════
#  ADMIN PANEL
# ═══════════════════════════════════════════════════

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
    syndics          = Syndic.query.order_by(Syndic.created_at.desc()).all()
    buildings        = Building.query.all()
    payments         = Payment.query.order_by(Payment.created_at.desc()).all()
    clients          = Client.query.all()
    total_revenue    = sum(p.amount_mad for p in payments if p.status == 'approved')
    active_buildings = sum(1 for b in buildings if b.is_active)
    pending_payments = sum(1 for p in payments if p.status == 'pending')
    pending_syndics  = sum(1 for s in syndics if not s.approved)
    return render_template('admin_dashboard.html',
        syndics=syndics, buildings=buildings, payments=payments,
        clients=clients, total_revenue=total_revenue,
        active_buildings=active_buildings,
        pending_payments=pending_payments,
        pending_syndics=pending_syndics)

@app.route('/admin/syndic/<int:syndic_id>/approve', methods=['POST'])
def admin_approve_syndic(syndic_id):
    if not session.get('admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    s = Syndic.query.get_or_404(syndic_id)
    s.approved = True
    db.session.commit()
    return jsonify({'success': True, 'name': s.name})

@app.route('/admin/syndic/<int:syndic_id>/reject', methods=['POST'])
def admin_reject_syndic(syndic_id):
    if not session.get('admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    s = Syndic.query.get_or_404(syndic_id)
    db.session.delete(s)
    db.session.commit()
    return jsonify({'success': True})


# ═══════════════════════════════════════════════════
#  SEED DATA
# ═══════════════════════════════════════════════════

def seed_data():
    if Syndic.query.count() == 0:
        s = Syndic(name='Mohammed Alami', phone='0661234567',
                   email='syndic@nqizbali.ma', approved=True)
        s.set_password('nqizbali2026')
        db.session.add(s)
        db.session.flush()
        b1 = Building(syndic_id=s.id, name='Residence Al Amal',
                      address='Rue Ibn Batouta', neighborhood='Massira II',
                      nb_apartments=8, lat=31.6258, lng=-8.0038)
        b2 = Building(syndic_id=s.id, name='Immeuble Atlas',
                      address='Avenue Mohammed VI', neighborhood="M'hamid 6",
                      nb_apartments=6, lat=31.6220, lng=-7.9972)
        db.session.add_all([b1, b2])
        db.session.flush()
        clients = [
            Client(building_id=b1.id, name='Karima Fahim',   address='Apt 7B',       neighborhood='Massira II',  qr_code='NQZ-MRK-0001', lat=31.6258, lng=-8.0038, phone='0661000001'),
            Client(building_id=b1.id, name='Ahmed Benali',   address='Apt 3A',       neighborhood='Massira II',  qr_code='NQZ-MRK-0002', lat=31.6255, lng=-8.0035, phone='0661000002'),
            Client(building_id=b1.id, name='Fatima Ouali',   address='Apt 1C',       neighborhood='Massira II',  qr_code='NQZ-MRK-0003', lat=31.6252, lng=-8.0032, phone='0661000003'),
            Client(building_id=b2.id, name='Hassan Tazi',    address='Apt 4',        neighborhood="M'hamid 6",   qr_code='NQZ-MRK-0004', lat=31.6220, lng=-7.9972, phone='0661000004'),
            Client(building_id=b2.id, name='Nadia Chraibi',  address='Apt 2A',       neighborhood="M'hamid 6",   qr_code='NQZ-MRK-0005', lat=31.6218, lng=-7.9968, phone='0661000005'),
            Client(building_id=None,  name='Omar Bakkali',   address='Rue Al Farah', neighborhood='Daoudiate',   qr_code='NQZ-MRK-0006', lat=31.6271, lng=-8.0062, phone='0661000006'),
            Client(building_id=None,  name='Zineb Mansouri', address='Appt 5',       neighborhood='Massira III', qr_code='NQZ-MRK-0007', lat=31.6243, lng=-8.0010, phone='0661000007'),
        ]
        db.session.add_all(clients)
        db.session.commit()
        print('✅ Demo data seeded — syndic@nqizbali.ma / nqizbali2026')


@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}


with app.app_context():
    db.create_all()
    seed_data()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
