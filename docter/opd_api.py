from flask import Flask, request, jsonify
import uuid

app = Flask(__name__)

# --- DATABASE (In-Memory for Basic Concept) ---
# Data Structure:
# doctors = {
#     "doc_1": { "name": "Dr. Smith", "slots": ["09:00", "10:00"], "capacity": 2, "schedule": {...} }
# }
doctors_db = {}

# --- PRIORITIES ---
# Lower Number = Higher Priority
PRIORITY_LEVELS = {
    "EMERGENCY": 1,      # Highest
    "PAID": 2,           # High
    "FOLLOW_UP": 3,      # Medium
    "WALK_IN": 4,        # Low
    "ONLINE": 4          # Low
}

def get_priority(p_type):
    return PRIORITY_LEVELS.get(p_type, 4)

# --- ALGORITHM: THE BUMPING LOGIC ---
def attempt_booking(doctor_id, time_slot, patient):
    """
    Tries to book a patient. If slot is full, checks if we can
    bump a lower priority patient to the next slot.
    """
    doctor = doctors_db.get(doctor_id)
    if not doctor: return False, "Doctor not found"

    # 1. Validate Slot
    if time_slot not in doctor['schedule']:
        return False, "Invalid time slot"

    slot_tokens = doctor['schedule'][time_slot]
    capacity = doctor['capacity']

    # CASE A: Slot has Empty Space
    if len(slot_tokens) < capacity:
        slot_tokens.append(patient)
        # Sort tokens by priority (Emergency at top)
        slot_tokens.sort(key=lambda x: get_priority(x['type']))
        return True, f"Booked for {time_slot}"

    # CASE B: Slot is Full -> Try to Bump
    else:
        # Get the person with the lowest priority (last in list)
        lowest_patient = slot_tokens[-1]

        # Check if incoming patient is more important than the lowest one
        if get_priority(patient['type']) < get_priority(lowest_patient['type']):

            # 1. Remove the low priority patient
            bumped_patient = slot_tokens.pop()

            # 2. Add the new high priority patient
            slot_tokens.append(patient)
            slot_tokens.sort(key=lambda x: get_priority(x['type']))

            # 3. Find the NEXT slot to move the bumped patient to
            all_slots = doctor['slots']
            try:
                current_index = all_slots.index(time_slot)
                if current_index + 1 < len(all_slots):
                    next_slot = all_slots[current_index + 1]

                    # RECURSIVE CALL: Try to book the bumped patient in the next slot
                    # We modify the message to track the change
                    success, msg = attempt_booking(doctor_id, next_slot, bumped_patient)
                    if success:
                        return True, f"Booked in {time_slot}. (Bumped {bumped_patient['name']} to {next_slot})"
                    else:
                         return True, f"Booked in {time_slot}. (Bumped {bumped_patient['name']} could not be reallocated and was dropped)"
                else:
                    return True, f"Booked in {time_slot}. (Bumped {bumped_patient['name']} dropped - End of Day)"
            except ValueError:
                pass

        return False, "Slot full and priority too low to bump"

# --- API ENDPOINTS ---

@app.route('/doctors', methods=['POST'])
def add_doctor():
    """Create a new doctor with slots"""
    data = request.json
    doc_id = str(uuid.uuid4())[:8]

    doctors_db[doc_id] = {
        "name": data['name'],
        "capacity": data['capacity'],
        "slots": data['slots'], # List like ["09:00", "10:00"]
        "schedule": {t: [] for t in data['slots']}
    }
    return jsonify({"id": doc_id, "message": "Doctor added"})

@app.route('/book', methods=['POST'])
def book_token():
    """Book a token with priority logic"""
    data = request.json
    patient = {
        "id": str(uuid.uuid4())[:8],
        "name": data['patient_name'],
        "type": data['type'] # EMERGENCY, PAID, WALK_IN
    }

    success, message = attempt_booking(data['doctor_id'], data['time_slot'], patient)

    if success:
        return jsonify({"status": "Success", "message": message})
    else:
        return jsonify({"status": "Failed", "message": message}), 400

@app.route('/cancel', methods=['POST'])
def cancel_token():
    """Cancel a booking"""
    data = request.json
    doctor = doctors_db.get(data['doctor_id'])
    if doctor and data['time_slot'] in doctor['schedule']:
        slot = doctor['schedule'][data['time_slot']]
        # Filter out the patient by name
        original_count = len(slot)
        doctor['schedule'][data['time_slot']] = [p for p in slot if p['name'] != data['patient_name']]

        if len(doctor['schedule'][data['time_slot']]) < original_count:
            return jsonify({"status": "Success", "message": "Cancelled successfully"})

    return jsonify({"status": "Failed", "message": "Booking not found"})

@app.route('/schedule/<doc_id>', methods=['GET'])
def get_schedule(doc_id):
    """View the doctor's full day"""
    return jsonify(doctors_db.get(doc_id, {}))

if __name__ == '__main__':
    app.run(port=5000, debug=True)