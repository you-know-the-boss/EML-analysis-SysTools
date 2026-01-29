import requests
import time

BASE_URL = "http://127.0.0.1:5000"

def log(step, message):
    print(f"\n[{step}] {message}")

def print_schedule(doc_name, doc_id):
    res = requests.get(f"{BASE_URL}/schedule/{doc_id}").json()
    print(f"\n--- Schedule for {doc_name} ---")
    for time, patients in res['schedule'].items():
        print(f"⏰ {time} | Capacity: {len(patients)}/{res['capacity']}")
        for p in patients:
            print(f"   - {p['name']} ({p['type']})")

# --- START SIMULATION ---
print("🏥 STARTING OPD SIMULATION (3 DOCTORS)...")

# 1. SETUP 3 DOCTORS
doctors = []
doc_data = [
    {"name": "Dr. Smith (Cardio)", "capacity": 2, "slots": ["09:00", "10:00"]},
    {"name": "Dr. Jones (Ortho)", "capacity": 2, "slots": ["09:00", "10:00"]},
    {"name": "Dr. Strange (Neuro)", "capacity": 1, "slots": ["09:00", "10:00"]} # Small capacity to test limits
]

for d in doc_data:
    res = requests.post(f"{BASE_URL}/doctors", json=d).json()
    doctors.append({"name": d['name'], "id": res['id']})
    print(f"Created {d['name']}")

cardio_id = doctors[0]['id'] # Dr. Smith

# 2. FILL UP SLOTS (Standard Patients)
log("STEP 1", "Filling Dr. Smith's 09:00 slot with Walk-in patients")
requests.post(f"{BASE_URL}/book", json={"doctor_id": cardio_id, "time_slot": "09:00", "patient_name": "Alice", "type": "WALK_IN"})
requests.post(f"{BASE_URL}/book", json={"doctor_id": cardio_id, "time_slot": "09:00", "patient_name": "Bob", "type": "WALK_IN"})
print_schedule("Dr. Smith", cardio_id)

# 3. EMERGENCY INSERTION (The "Bumping" Logic)
log("STEP 2", "Emergency Patient 'EVE' arrives at 09:00 (Slot is full!)")
res = requests.post(f"{BASE_URL}/book", json={"doctor_id": cardio_id, "time_slot": "09:00", "patient_name": "EVE", "type": "EMERGENCY"}).json()
print(f"👉 API Response: {res['message']}")

log("STEP 3", "Checking Schedule (Bob should be moved to 10:00)")
print_schedule("Dr. Smith", cardio_id)

# 4. CANCELLATION
log("STEP 4", "Alice cancels her appointment")
requests.post(f"{BASE_URL}/cancel", json={"doctor_id": cardio_id, "time_slot": "09:00", "patient_name": "Alice"})
print_schedule("Dr. Smith", cardio_id)

# 5. PAID PRIORITY (Different Doctor)
neuro_id = doctors[2]['id'] # Dr. Strange (Capacity 1)
log("STEP 5", "Dr. Strange: Paid Patient vs Walk-in")
requests.post(f"{BASE_URL}/book", json={"doctor_id": neuro_id, "time_slot": "09:00", "patient_name": "John (Walk-in)", "type": "WALK_IN"})
# Now Paid patient comes
res = requests.post(f"{BASE_URL}/book", json={"doctor_id": neuro_id, "time_slot": "09:00", "patient_name": "Richie (Paid)", "type": "PAID"}).json()
print(f"👉 API Response: {res['message']}")
print_schedule("Dr. Strange", neuro_id)

print("\n✅ Simulation Complete.")