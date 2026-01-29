# OPD Token Allocation Engine

## Overview
This backend service manages OPD token allocation with support for **Elastic Capacity**. It does not simply reject patients when slots are full; instead, it prioritizes critical cases and dynamically reallocates lower-priority patients to future slots.

## 1. Prioritization Logic
The system assigns a numeric weight to patient types. Lower numbers indicate higher priority.
* **Level 1 (Highest):** EMERGENCY
* **Level 2:** PAID (Priority Booking)
* **Level 3:** FOLLOW_UP
* **Level 4 (Lowest):** WALK_IN / ONLINE

## 2. Dynamic Reallocation Algorithm
When a patient requests a slot that is already at **Max Capacity**:
1.  **Comparison:** The system compares the new patient's priority against the *lowest* priority patient currently in that slot.
2.  **The "Bump":** If the new patient has higher priority, the lowest-priority patient is removed (bumped).
3.  **Insertion:** The high-priority patient is added to the current slot.
4.  **Cascade:** The system automatically attempts to book the *bumped* patient into the **next available time slot**.

## 3. Edge Cases & Failure Handling
* **End of Day Overflow:** If a patient is bumped from the last slot of the day, they are unfortunately dropped (API returns a specific message).
* **Double Full:** If a bumped patient tries to move to the next slot, and that slot is *also* full of high-priority patients, the bump fails.
* **Cancellation:** Cancelling a token immediately frees up the slot for new bookings.

## 4. API Endpoints
* `POST /doctors`: Initialize a doctor with `name`, `capacity`, and `slots`.
* `POST /book`: Book a token. Requires `patient_name`, `type` (EMERGENCY/PAID/WALK_IN), and `time_slot`.
* `POST /cancel`: Cancel a booking.
* `GET /schedule/<doctor_id>`: View the current state of allocations.

## How to Run
1.  **Install Flask:** `pip install flask requests`
2.  **Start Server:** `python opd_api.py`
3.  **Run Simulation:** `python simulation.py`