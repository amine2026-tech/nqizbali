from flask import (Flask, render_template, request, jsonify,
                   redirect, url_for, session, flash)
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import hashlib, os, uuid

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///nqizbali.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'nqizbali-dev-secret')

# ── CMI Config (Moroccan gateway) ──────────────────────────────
CMI_MERCHANT_ID   = os.environ.get('CMI_MERCHANT_ID',  'TEST_MERCHANT')
CMI_STORE_KEY     = os.environ.get('CMI_STORE_KEY',     'TEST_STORE_KEY')
CMI_BASE_URL      = os.environ.get('CMI_BASE_URL',
                    'https://testpayment.cmi.co.ma/fim/est3Dgate')
PRICE_PER_APT     = 60

db = SQLAlchemy(app)

class Syndic(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(120), nullable=False)
    phone         = db.Column(db.String(30),  nullable=False)
    email         = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
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


def syndic_login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'syndic_id' not in session:
            return redirect(url_for('syndic_login'))
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


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/client')
def client_view():
    clients = Client.query.all()
    return render_template('client.html', clients=clients)

@app.route('/collector')
def collector_view():
    clients = Client.query.all()
    return render_template('collector.html', clients=clients)


@app.route('/syndic/login', methods=['GET', 'POST'])
def syndic_login():
    error = None
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        pw    = request.form.get('password', '')
        s = Syndic.query.filter_by(email=email).first()
        if s and s.check_password(pw):
            session['syndic_id']   = s.id
            session['syndic_name'] = s.name
            return redirect(url_for('syndic_dashboard'))
        error = 'Incorrect email or password.'
    return render_template('syndic_login.html', error=error)

@app.route('/syndic/register', methods=['GET', 'POST'])
def syndic_register():
    error = None
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
            s = Syndic(name=name, phone=phone, email=email)
            s.set_password(pw)
            db.session.add(s)
            db.session.commit()
            session['syndic_id']   = s.id
            session['syndic_name'] = s.name
            return redirect(url_for('syndic_dashboard'))
    return render_template('syndic_register.html', error=error)

@app.route('/syndic/logout')
def syndic_logout():
    session.clear()
    return redirect(url_for('syndic_login'))


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


@app.route('/api/clients', methods=['GET'])
def get_clients():
    clients = Client.query.all()
    return jsonify([_client_dict(c) for c in clients])

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


def seed_data():
    if Syndic.query.count() == 0:
        s = Syndic(name='Mohammed Alami', phone='0661234567', email='syndic@nqizbali.ma')
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
            Client(building_id=b1.id, name='Karima Fahim',   address='Apt 7B',  neighborhood='Massira II', qr_code='NQZ-MRK-0001', lat=31.6258, lng=-8.0038),
            Client(building_id=b1.id, name='Ahmed Benali',   address='Apt 3A',  neighborhood='Massira II', qr_code='NQZ-MRK-0002', lat=31.6255, lng=-8.0035),
            Client(building_id=b1.id, name='Fatima Ouali',   address='Apt 1C',  neighborhood='Massira II', qr_code='NQZ-MRK-0003', lat=31.6252, lng=-8.0032),
            Client(building_id=b2.id, name='Hassan Tazi',    address='Apt 4',   neighborhood="M'hamid 6",  qr_code='NQZ-MRK-0004', lat=31.6220, lng=-7.9972),
            Client(building_id=b2.id, name='Nadia Chraibi',  address='Apt 2A',  neighborhood="M'hamid 6",  qr_code='NQZ-MRK-0005', lat=31.6218, lng=-7.9968),
            Client(building_id=None,  name='Omar Bakkali',   address='Rue Al Farah', neighborhood='Daoudiate', qr_code='NQZ-MRK-0006', lat=31.6271, lng=-8.0062),
            Client(building_id=None,  name='Zineb Mansouri', address='Appt 5',  neighborhood='Massira III', qr_code='NQZ-MRK-0007', lat=31.6243, lng=-8.0010),
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
