import psycopg2
from psycopg2 import Error
from db_config import get_db_connection, return_db_connection
from flask_bcrypt import Bcrypt
from flask import Flask

app = Flask(__name__)
bcrypt = Bcrypt(app)

def seed_database():
    db = get_db_connection()
    if not db:
        print("Error: Could not connect to PostgreSQL. Is it running?")
        return
    
    cursor = db.cursor()
    
    print("Clearing existing data...")
    # In PostgreSQL, CASCADE handles foreign key dependencies during truncation
    tables = ['feedback', 'assignments', 'service_requests', 'workers', 'customers', 'services', 'areas', 'cities', 'admins']
    cursor.execute(f"TRUNCATE TABLE {', '.join(tables)} RESTART IDENTITY CASCADE")

    print("Seeding Cities (Districts of Tamil Nadu)...")
    districts = [
        ('Ariyalur',), ('Chengalpattu',), ('Chennai',), ('Coimbatore',), ('Cuddalore',),
        ('Dharmapuri',), ('Dindigul',), ('Erode',), ('Kallakurichi',), ('Kanchipuram',),
        ('Kanyakumari',), ('Karur',), ('Krishnagiri',), ('Madurai',), ('Mayiladuthurai',),
        ('Nagapattinam',), ('Namakkal',), ('Nilgiris',), ('Perambalur',), ('Pudukkottai',),
        ('Ramanathapuram',), ('Ranipet',), ('Salem',), ('Sivaganga',), ('Tenkasi',),
        ('Thanjavur',), ('Theni',), ('Thoothukudi',), ('Tiruchirappalli',), ('Tirunelveli',),
        ('Tirupathur',), ('Tiruppur',), ('Tiruvallur',), ('Tiruvannamalai',), ('Tiruvarur',),
        ('Vellore',), ('Viluppuram',), ('Virudhunagar',)
    ]
    cursor.executemany("INSERT INTO cities (name) VALUES (%s)", districts)
    
    # Fetch IDs to map areas correctly
    cursor.execute("SELECT id, name FROM cities")
    city_map = {name: id for id, name in cursor.fetchall()}

    print("Seeding Areas (Towns/Cities for each District)...")
    area_mapping = {
        'Ariyalur': ['Ariyalur', 'Jayamkondam', 'Sendurai'],
        'Chengalpattu': ['Chengalpattu', 'Tambaram', 'Pallavaram', 'Maduranthakam'],
        'Chennai': ['Adyar', 'Velachery', 'T. Nagar', 'Anna Nagar', 'Mylapore', 'Ambattur'],
        'Coimbatore': ['Gandhipuram', 'RS Puram', 'Peelamedu', 'Pollachi', 'Mettupalayam'],
        'Cuddalore': ['Cuddalore', 'Chidambaram', 'Panruti', 'Neyveli', 'Virudhachalam'],
        'Dharmapuri': ['Dharmapuri', 'Harur', 'Pappireddipatti', 'Palacode'],
        'Dindigul': ['Dindigul', 'Palani', 'Kodaikanal', 'Oddanchatram'],
        'Erode': ['Erode', 'Bhavani', 'Gobichettipalayam', 'Sathyamangalam', 'Perundurai'],
        'Kallakurichi': ['Kallakurichi', 'Sankarapuram', 'Tirukkoilur', 'Ulundurpet'],
        'Kanchipuram': ['Kanchipuram', 'Sriperumbudur', 'Walajabad', 'Kundrathur'],
        'Kanyakumari': ['Nagercoil', 'Padmanabhapuram', 'Kuzhithurai', 'Colachel'],
        'Karur': ['Karur', 'Kulithalai', 'Aravakurichi', 'Krishnarayapuram'],
        'Krishnagiri': ['Krishnagiri', 'Hosur', 'Denkanikottai', 'Pochampalli'],
        'Madurai': ['K.K. Nagar', 'Tallakulam', 'Melur', 'Thirumangalam', 'Usilampatti'],
        'Mayiladuthurai': ['Mayiladuthurai', 'Sirkazhi', 'Tharangambadi', 'Kuthalam'],
        'Nagapattinam': ['Nagapattinam', 'Velankanni', 'Kilvelur', 'Thalaignayiru'],
        'Namakkal': ['Namakkal', 'Rasipuram', 'Tiruchengode', 'Paramathi-Velur'],
        'Nilgiris': ['Ooty', 'Coonoor', 'Gudalur', 'Kotagiri'],
        'Perambalur': ['Perambalur', 'Veppanthattai', 'Alathur', 'Kunnam'],
        'Pudukkottai': ['Pudukkottai', 'Aranthangi', 'Alangudi', 'Ponnamaravathi'],
        'Ramanathapuram': ['Ramanathapuram', 'Rameswaram', 'Paramakudi', 'Kamuthi'],
        'Ranipet': ['Ranipet', 'Arcot', 'Walajah', 'Arakkonam', 'Sholinghur'],
        'Salem': ['Salem City', 'Attur', 'Mettur', 'Omalur', 'Sangagiri'],
        'Sivaganga': ['Sivaganga', 'Karaikudi', 'Devakottai', 'Manamadurai'],
        'Tenkasi': ['Tenkasi', 'Sankarankovil', 'Kadayanallur', 'Sengottai'],
        'Thanjavur': ['Thanjavur', 'Kumbakonam', 'Pattukkottai', 'Thiruvaiyaru'],
        'Theni': ['Theni', 'Periyakulam', 'Bodinayakanur', 'Cumbum'],
        'Thoothukudi': ['Thoothukudi', 'Kovilpatti', 'Tiruchendur', 'Kayalpattinam'],
        'Tiruchirappalli': ['Trichy', 'Srirangam', 'Musiri', 'Lalgudi', 'Thuraiyur'],
        'Tirunelveli': ['Tirunelveli City', 'Palayamkottai', 'Ambasamudram', 'Nanguneri'],
        'Tirupathur': ['Tirupathur', 'Vaniyambadi', 'Ambur', 'Natrampalli'],
        'Tiruppur': ['Tiruppur City', 'Dharapuram', 'Kangeyam', 'Udumaipettai'],
        'Tiruvallur': ['Tiruvallur', 'Avadi', 'Poonamallee', 'Ponneri', 'Gummidipoondi'],
        'Tiruvannamalai': ['Tiruvannamalai', 'Arni', 'Chengam', 'Polur', 'Vandavasi'],
        'Tiruvarur': ['Tiruvarur', 'Mannargudi', 'Thiruthuraipoondi', 'Nannilam'],
        'Vellore': ['Vellore City', 'Gudiyatham', 'Katpadi', 'Pernambut'],
        'Viluppuram': ['Viluppuram', 'Tindivanam', 'Gingee', 'Vikravandi'],
        'Virudhunagar': ['Virudhunagar', 'Rajapalayam', 'Sivakasi', 'Aruppukkottai']
    }

    areas_to_insert = []
    for district, cities in area_mapping.items():
        d_id = city_map.get(district)
        if d_id:
            for city in cities:
                areas_to_insert.append((d_id, city))
    
    cursor.executemany("INSERT INTO areas (city_id, name) VALUES (%s, %s)", areas_to_insert)

    print("Seeding Services...")
    services = [
        ('Electrician', 'Expert electrical repairs and installations', 'bolt'),
        ('Plumber', 'Professional plumbing services and leak fixes', 'faucet'),
        ('Cleaner', 'Deep home cleaning and sanitization', 'broom'),
        ('AC Technician', 'AC service, repair, and installation', 'wind'),
        ('Carpenter', 'Furniture repair and custom woodwork', 'hammer'),
        ('Appliance Repair', 'Repair services for fridge, washing machine, etc.', 'plug')
    ]
    cursor.executemany("INSERT INTO services (name, description, icon_name) VALUES (%s, %s, %s)", services)
    
    # Map service IDs
    cursor.execute("SELECT id, name FROM services")
    service_map = {name: id for id, name in cursor.fetchall()}

    print("Seeding Admin...")
    admin_pw = bcrypt.generate_password_hash('admin123').decode('utf-8')
    cursor.execute("INSERT INTO admins (full_name, email, password) VALUES (%s, %s, %s)", 
                   ('System Admin', 'admin@urban.com', admin_pw))

    print("Seeding Customers...")
    cust_pw = bcrypt.generate_password_hash('customer123').decode('utf-8')
    customer_data = [
        ('Rajesh Kumar', 'rajesh@gmail.com', cust_pw, '9876543210', 'No 12, Gandhi Street', 'Chennai', 'Adyar'),
        ('Priya Dharshini', 'priya@gmail.com', cust_pw, '9876543211', 'Flat 4B, Velachery Main Rd', 'Chennai', 'Velachery'),
        ('Anand Mani', 'anand@gmail.com', cust_pw, '9876543212', 'Plot 55, North Street', 'Coimbatore', 'RS Puram')
    ]
    
    # Map area IDs
    cursor.execute("SELECT id, name FROM areas")
    area_map = {name: id for id, name in cursor.fetchall()}
    
    customers = []
    for c in customer_data:
        city_id = city_map.get(c[5])
        area_id = area_map.get(c[6])
        customers.append((c[0], c[1], c[2], c[3], c[4], city_id, area_id))
        
    cursor.executemany("""
        INSERT INTO customers (full_name, email, password, phone, address, city_id, area_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, customers)

    print("Seeding Workers...")
    work_pw = bcrypt.generate_password_hash('worker123').decode('utf-8')
    worker_data = [
        ('Suresh Electrician', 'suresh@worker.com', work_pw, '8877665544', 'Electrician', 'Chennai'),
        ('Mani Plumber', 'mani@worker.com', work_pw, '8877665545', 'Plumber', 'Chennai'),
        ('Karthik AC', 'karthik@worker.com', work_pw, '8877665546', 'AC Technician', 'Chennai'),
        ('Vijay Cleaner', 'vijay@worker.com', work_pw, '8877665547', 'Cleaner', 'Coimbatore'),
        ('Ramesh Carpenter', 'ramesh@worker.com', work_pw, '8877665548', 'Carpenter', 'Madurai')
    ]
    
    workers = []
    for w in worker_data:
        service_id = service_map.get(w[4])
        city_id = city_map.get(w[5])
        workers.append((w[0], w[1], w[2], w[3], service_id, city_id, 'Available'))
        
    cursor.executemany("""
        INSERT INTO workers (full_name, email, password, phone, service_id, city_id, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, workers)

    print("Seeding Sample Service Requests...")
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Map customer IDs
    cursor.execute("SELECT id, email FROM customers")
    customer_map = {email: id for id, email in cursor.fetchall()}
    
    request_data = [
        ('rajesh@gmail.com', 'Electrician', 'Chennai', 'Adyar', today, '09:00 AM - 12:00 PM', 'Fan is not working in the living room.'),
        ('priya@gmail.com', 'Plumber', 'Chennai', 'Velachery', today, '12:00 PM - 03:00 PM', 'Tap leakage in the kitchen.'),
        ('anand@gmail.com', 'AC Technician', 'Coimbatore', 'RS Puram', today, '03:00 PM - 06:00 PM', 'AC is not cooling, need urgent gas refill.')
    ]
    
    requests = []
    for r in request_data:
        cust_id = customer_map.get(r[0])
        serv_id = service_map.get(r[1])
        ct_id = city_map.get(r[2])
        ar_id = area_map.get(r[3])
        requests.append((cust_id, serv_id, ct_id, ar_id, r[4], r[5], r[6], 'Requested'))

    cursor.executemany("""
        INSERT INTO service_requests (customer_id, service_id, city_id, area_id, request_date, time_slot, description, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, requests)

    db.commit()
    cursor.close()
    return_db_connection(db)
    print("Database seeded successfully!")

if __name__ == "__main__":
    seed_database()
