from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///nqizbali.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ─── Models ───────────────────────────────────────
class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    neighborhood = db.Column(db.String(100), nullable=False)
    qr_code = db.Column(db.String(50), unique=True, nullable=False)
    trash_ready = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(50), default='not_ready')
    lat = db.Column(db.Float, default=31.6258)
    lng = db.Column(db.Float, default=-8.0038)

class Collection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    collector_name = db.Column(db.String(100), nullable=False)
    collected_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='collected')
    violation_reason = db.Column(db.String(200), nullable=True)

# ─── Routes ───────────────────────────────────────
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

# ─── API ──────────────────────────────────────────
@app.route('/api/clients', methods=['GET'])
def get_clients():
    clients = Client.query.all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'address': c.address,
        'neighborhood': c.neighborhood,
        'qr_code': c.qr_code,
        'status': c.status,
        'trash_ready': c.trash_ready,
        'lat': c.lat,
        'lng': c.lng
    } for c in clients])

@app.route('/api/trash_ready/<int:client_id>', methods=['POST'])
def toggle_trash_ready(client_id):
    client = Client.query.get_or_404(client_id)
    client.trash_ready = not client.trash_ready
    client.status = 'ready' if client.trash_ready else 'not_ready'
    db.session.commit()
    return jsonify({'success': True, 'status': client.status})

@app.route('/api/collect/<int:client_id>', methods=['POST'])
def collect(client_id):
    client = Client.query.get_or_404(client_id)
    client.status = 'collected'
    client.trash_ready = False
    data = request.get_json()
    collection = Collection(
        client_id=client_id,
        collector_name=data.get('collector', 'Youssef B.'),
        status='collected'
    )
    db.session.add(collection)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/violation/<int:client_id>', methods=['POST'])
def report_violation(client_id):
    client = Client.query.get_or_404(client_id)
    client.status = 'violation'
    data = request.get_json()
    collection = Collection(
        client_id=client_id,
        collector_name=data.get('collector', 'Youssef B.'),
        status='violation',
        violation_reason=data.get('reason', '')
    )
    db.session.add(collection)
    db.session.commit()
    return jsonify({'success': True})

# ─── Seed Data ────────────────────────────────────
def seed_data():
    if Client.query.count() == 0:
        clients = [
            Client(name='Karima Fahim', address='Apt 7B', neighborhood='Massira II', qr_code='NQZ-MRK-0001', lat=31.6258, lng=-8.0038),
            Client(name='Ahmed Benali', address='Villa 12', neighborhood="M'hamid 6", qr_code='NQZ-MRK-0002', lat=31.6220, lng=-7.9972),
            Client(name='Fatima Ouali', address='Bloc C', neighborhood='Daoudiate', qr_code='NQZ-MRK-0003', lat=31.6285, lng=-8.0089),
            Client(name='Hassan Tazi', address='N°34', neighborhood='Massira I', qr_code='NQZ-MRK-0004', lat=31.6278, lng=-8.0075),
            Client(name='Nadia Chraibi', address='Appt 2A', neighborhood="M'hamid 7", qr_code='NQZ-MRK-0005', lat=31.6184, lng=-7.9910),
            Client(name='Omar Bakkali', address='Rue Al Farah', neighborhood='Daoudiate', qr_code='NQZ-MRK-0006', lat=31.6271, lng=-8.0062),
            Client(name='Zineb Mansouri', address='Appt 5', neighborhood='Massira III', qr_code='NQZ-MRK-0007', lat=31.6243, lng=-8.0010),
            Client(name='Rachid Idrissi', address='Villa 4', neighborhood="M'hamid 8", qr_code='NQZ-MRK-0008', lat=31.6198, lng=-7.9935),
            Client(name='Samira Bensouda', address='N°91', neighborhood='Massira II', qr_code='NQZ-MRK-0009', lat=31.6228, lng=-7.9985),
            Client(name='Karim Ouazzani', address='Appt 11B', neighborhood='Daoudiate', qr_code='NQZ-MRK-0010', lat=31.6205, lng=-7.9948),
        ]
        db.session.bulk_save_objects(clients)
        db.session.commit()
        print("✅ Sample data created!")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_data()
    app.run(debug=True, host='0.0.0.0')