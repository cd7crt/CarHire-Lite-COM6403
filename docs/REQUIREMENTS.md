# CarHire Lite: Software Requirements Specification

**Version:** 1.0 (release candidate)
**Status:** Baselined for testing

This document is the **test basis** for CarHire Lite. Where the application's
behaviour differs from this specification, the specification is correct and the
application has a defect.

---

## 1. Purpose and scope

CarHire Lite is a small web application for a single car-hire branch.

- **Customers** browse cars, get a price quote, book a car, look up a booking and cancel it.
- **Branch staff** view all bookings and record when a car is picked up and returned.

**Out of scope for v1.0:** user accounts/login (including staff authentication),
online payment, e-mail notifications, multiple branches.

---

## 2. Functional requirements

| ID    | Requirement |
|-------|-------------|
| FR-01 | The system shall list all cars showing make, model, category, seats and daily rate, sorted by daily rate (cheapest first). |
| FR-02 | The system shall let a user search cars by **make**. The search is case-insensitive and matches part of the make (e.g. `merc` finds Mercedes-Benz). An empty search shows all cars. |
| FR-03 | The system shall produce a **price quote** for a car, driver age, pick-up date, return date and optional extras, following BR-04 to BR-07. |
| FR-04 | The system shall create a booking when all input is valid (BR-01 to BR-03, BR-12) and the car is available (BR-11). A new booking has status `CONFIRMED` and a unique reference in the format `CH-XXXXXX` (six upper-case hexadecimal characters). |
| FR-05 | The system shall let a customer view a booking by its reference, including the full price breakdown. |
| FR-06 | The system shall let a customer cancel a booking and shall show the refund amount (BR-08). |
| FR-07 | The system shall let staff record that a booked car has been picked up. |
| FR-08 | The system shall let staff record the actual return date of a car and shall calculate any late-return fee (BR-10). |
| FR-09 | The system shall show staff a list of all bookings, newest first. |
| FR-10 | Every function in FR-01 to FR-09 shall also be available through the JSON API (see `README.md`). |

---

## 3. Business rules

### BR-01 Driver age
The driver's age must be a whole number from **21 to 75 inclusive**.

### BR-02 Luxury cars
Cars in the `LUXURY` category may only be hired by drivers aged **25 or over**.

### BR-03 Rental dates
- The pick-up date must be **today or later**.
- The return date must be **after** the pick-up date.
- Rental length (in days) = return date − pick-up date, and must be **1 to 28 days inclusive**.
- Dates use the format `YYYY-MM-DD`.

### BR-04 Base price
Base price = car daily rate × rental length (days).

### BR-05 Long-rental discount
Applied to the **base price only** (not to surcharges or extras):

| Rental length | Discount |
|---------------|----------|
| 1 to 6 days   | 0%       |
| 7 to 13 days  | 10%      |
| 14 to 28 days | 20%      |

### BR-06 Young-driver surcharge
Drivers aged **21 to 24 inclusive** pay a surcharge of **£15.00 per day** of the rental.

### BR-07 Extras
Optional extras are charged **per day** and are not discounted:

| Extra                   | Price per day |
|-------------------------|---------------|
| Sat-nav / GPS           | £5.00         |
| Full insurance cover    | £12.00        |

**Total price** = base price − discount + young-driver surcharge + extras.
All money values are shown in pounds to **2 decimal places** (rounded half-up).

> **Worked example:** £40/day car, 7 days, driver aged 30, no extras.
> Base £280.00, discount £28.00, surcharge £0.00, extras £0.00, **total £252.00**.

### BR-08 Cancellation and refunds
All pick-ups happen at **10:00 on the pick-up date**. The refund depends on how
long before the pick-up time the booking is cancelled:

| Time before pick-up              | Refund        |
|----------------------------------|---------------|
| 48 hours or more                 | 100% of total |
| 24 hours or more, but under 48   | 50% of total  |
| Under 24 hours (or after pick-up time) | 0%      |

Only bookings with status `CONFIRMED` can be cancelled.

### BR-09 Booking status lifecycle
The only valid status changes are:

```
CONFIRMED ──pick up──▶ PICKED_UP ──return──▶ RETURNED
    │
    └──cancel──▶ CANCELLED
```

Any other change (for example, picking up a cancelled booking) must be rejected
with an error message, and the booking's status must not change.

### BR-10 Late-return fee
If the actual return date is **after** the agreed return date:

late fee = number of days late × car daily rate × **1.5**

Returning on time or early costs nothing extra, and there is no refund for early
returns. The actual return date cannot be before the pick-up date.

### BR-11 Availability
A car cannot have two bookings with status `CONFIRMED` or `PICKED_UP` whose rental
periods overlap. A rental period runs from the pick-up date up to (but not
including) the return date, so **back-to-back bookings are allowed**: a new booking
may start on the same day another booking for that car is returned.
Cancelled and returned bookings do not block a car.

### BR-12 Customer details
- **Name:** 2 to 50 characters (after removing leading/trailing spaces).
- **E-mail:** exactly one `@`, a non-empty part before it, a domain after it that
  contains at least one `.`, and no spaces anywhere (e.g. `jo@example.com`).
- **Driving licence number:** exactly **16** letters and/or digits; stored in
  upper case.

---

## 4. Non-functional requirements

| ID     | Category        | Requirement |
|--------|-----------------|-------------|
| NFR-01 | Performance     | 95% of API requests shall complete in under **500 ms** with **20 concurrent users** on a standard laptop. |
| NFR-02 | Security        | User input shall never change the meaning of a database query (no SQL injection). |
| NFR-03 | Reliability     | Invalid input shall never cause a server error (HTTP 500). The API returns HTTP 400 with error messages; web forms are shown again with messages. |
| NFR-04 | Usability       | When a form fails validation, every error is shown next to its field and the values already entered are kept. |
| NFR-05 | Maintainability | Source code shall pass a PEP 8 linter using the project settings in `setup.cfg` without errors, and no secrets shall be hard-coded in source code. |

---

## 5. User stories and acceptance criteria

**US-01 Browse and search cars**
*As a customer, I want to see the cars and their prices so that I can choose one.*
- **AC1:** Given the application has its sample data, when I open the home page, then I see all 8 cars sorted cheapest first.
- **AC2:** Given I am on the home page, when I search for `ford`, then only Ford cars are shown.

**US-02 Book a car**
*As a customer, I want to book a car online so that it is reserved for me.*
- **AC1:** Given valid details and an available car, when I submit the booking form, then I see a confirmation page with a booking reference, status `CONFIRMED` and the price breakdown.
- **AC2:** Given one or more invalid details, when I submit the form, then I see an error message for each problem and no booking is created.
- **AC3:** Given the car is already booked for overlapping dates, when I submit the form, then I am told the car is unavailable and no booking is created.

**US-03 Add extras**
*As a customer, I want to add extras so that I have what I need for my trip.*
- **AC1:** Given I tick Sat-nav / GPS for a 3-day rental, when I book, then the extras line in the price breakdown is £15.00.

**US-04 Cancel a booking**
*As a customer, I want to cancel my booking and know my refund.*
- **AC1:** Given a `CONFIRMED` booking whose pick-up is 3 days away, when I cancel it, then its status becomes `CANCELLED` and I am refunded 100% of the total.

**US-05 Record pick-up and return**
*As a member of staff, I want to record pick-ups and returns so that booking status and late fees are correct.*
- **AC1:** Given a `PICKED_UP` booking for a £40/day car due back on day D, when it is returned on day D + 2, then the late fee is £120.00 and the status is `RETURNED`.
- **AC2:** Given a `CANCELLED` booking, when I try to record a pick-up, then I see an error and the status stays `CANCELLED`.

---

## 6. Sample data

The database starts with these cars:

| ID | Make          | Model    | Category | Seats | Daily rate |
|----|---------------|----------|----------|-------|------------|
| 1  | Toyota        | Yaris    | ECONOMY  | 5     | £30        |
| 2  | Ford          | Fiesta   | ECONOMY  | 5     | £32        |
| 3  | Vauxhall      | Astra    | COMPACT  | 5     | £38        |
| 4  | Volkswagen    | Golf     | COMPACT  | 5     | £40        |
| 5  | Kia           | Sportage | SUV      | 5     | £62        |
| 6  | Nissan        | Qashqai  | SUV      | 5     | £65        |
| 7  | BMW           | 5 Series | LUXURY   | 5     | £120       |
| 8  | Mercedes-Benz | E-Class  | LUXURY   | 5     | £125       |
