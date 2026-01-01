from ortools.sat.python import cp_model


# Input Data
batches = ["CST_5", "CSE_5"]

subjects = {
    "NET": {"type": "theory", "weekly_slots": 3, "code": "PT1"},
    "DBMS_LAB": {"type": "lab", "weekly_slots": 2, "code": "LAB1"},
    "compiler design": {"type": "theory", "weekly_slots": 3, "code": "PT2"},
    "RTS": {"type": "theory", "weekly_slots": 3, "code": "ET1"},
    "MC": {"type": "theory", "weekly_slots": 3, "code": "ET1"},
    "stats": {"type": "theory", "weekly_slots": 3, "code": "ET1"},
    "LUNCH": {"type": "break", "weekly_slots": 5, "code": "LUNCH"}
}

batch_subjects = {
    "CST_5": ["NET", "DBMS_LAB", "LUNCH", "RTS", "MC", "stats"],
    "CSE_5": ["NET", "compiler design", "LUNCH"]
}

faculty = {
    "Sarthak": ["NET", "compiler design"],
    "Anita": ["DBMS_LAB", "RTS"],
    "Rahul": ["compiler design", "MC"],
    "susmita": ["stats"],

    "LUNCH_CST_5": ["LUNCH"],
    "LUNCH_CSE_5": ["LUNCH"]
}

rooms = {
    "R658": {"type": "theory", "capacity": 90},
    "LAB1": {"type": "lab", "capacity": 30},
    "LUNCH_ROOM": {"type": "break", "capacity": 999}
}

slots_per_day = 8
days = 5
lunch_slot_offsets = [3, 4, 5, 6]
time_slots = list(range(slots_per_day * days))


# Model
model = cp_model.CpModel()

X = {}  # class placement
E = {}  # elective-code presence


# Decision Variables


for b in batches:
    for s in batch_subjects[b]:
        for f in faculty:
            if s not in faculty[f]:
                continue

            if s == "LUNCH" and not f.endswith(b):
                continue

            for r in rooms:
                if subjects[s]["type"] != rooms[r]["type"]:
                    continue

                for t in time_slots:
                    X[(b, s, f, r, t)] = model.NewBoolVar(
                        f"X_{b}_{s}_{f}_{r}_{t}"
                    )

# elective-code presence variables
for b in batches:
    for s in batch_subjects[b]:
        code = subjects[s]["code"]
        if code.startswith("ET"):
            for t in time_slots:
                E[(b, code, t)] = model.NewBoolVar(f"E_{b}_{code}_{t}")


# Constraints

# 1. Weekly slots per subject
for b in batches:
    for s in batch_subjects[b]:
        model.Add(
            sum(
                X[(bb, ss, f, r, t)]
                for (bb, ss, f, r, t) in X
                if bb == b and ss == s
            )
            == subjects[s]["weekly_slots"]
        )

# 2. Faculty clash
for f in faculty:
    for t in time_slots:
        model.Add(
            sum(
                X[(b, s, ff, r, tt)]
                for (b, s, ff, r, tt) in X
                if ff == f and tt == t
            )
            <= 1
        )

# 3. Lunch slot restriction
for (b, s, f, r, t), var in X.items():
    if s == "LUNCH" and (t % slots_per_day) not in lunch_slot_offsets:
        model.Add(var == 0)

# 4. Link electives to elective-code presence
for (b, s, f, r, t), var in X.items():
    code = subjects[s]["code"]
    if code.startswith("ET"):
        model.Add(var <= E[(b, code, t)])

# 5. At most ONE elective code per batch per slot
for b in batches:
    for t in time_slots:
        model.Add(
            sum(
                E[(bb, code, tt)]
                for (bb, code, tt) in E
                if bb == b and tt == t
            )
            <= 1
        )

# 6. Batch clash for NON-electives
for b in batches:
    for t in time_slots:
        model.Add(
            sum(
                X[(bb, s, f, r, tt)]
                for (bb, s, f, r, tt) in X
                if bb == b
                and tt == t
                and not subjects[s]["code"].startswith("ET")
            )
            <= 1
        )

# 7. Exactly one lunch per day per batch
for b in batches:
    for d in range(days):
        day_lunch_slots = [
            d * slots_per_day + s for s in lunch_slot_offsets
        ]

        model.Add(
            sum(
                X[(bb, s, f, r, t)]
                for (bb, s, f, r, t) in X
                if bb == b and s == "LUNCH" and t in day_lunch_slots
            )
            == 1
        )


# Solve

solver = cp_model.CpSolver()
status = solver.Solve(model)

print("Solver status:", solver.StatusName(status))

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    print("\n--- TIMETABLE ---")
    for (b, s, f, r, t), var in X.items():
        if solver.Value(var):
            print(
                f"Batch {b} | Subject {s} | Faculty {f} | Room {r} | Slot {t}"
            )
