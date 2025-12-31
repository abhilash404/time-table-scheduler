from ortools.sat.python import cp_model

# -----------------------
# Input Data
# -----------------------

batches = ["CST_T", "CSE_5"]

subjects = {
    "NET": {"type": "theory", "weekly_slots": 3},
    "DBMS_LAB": {"type": "lab", "weekly_slots": 2},
    "compiler design": {"type": "theory", "weekly_slots": 3}
}

batch_subjects = {
    "CST_T": ["NET", "DBMS_LAB"],
    "CSE_5": ["NET", "compiler design"]
}

faculty = {
    "Sarthak": ["NET","compiler design"],
    "Anita": ["DBMS_LAB"],
    "Rahul": ["compiler design"]
}

rooms = {
    "R658": {"type": "theory", "capacity": 90},
    "LAB1": {"type": "lab", "capacity": 30}
}

# 40 slots
time_slots = list(range(40))

# -----------------------
# Model
# -----------------------

model = cp_model.CpModel()

X = {}

# -----------------------
# Decision Variables
# -----------------------

for b in batches:
    for s in batch_subjects[b]:
        for f in faculty:
            if s not in faculty[f]:
                continue

            for r in rooms:
                if subjects[s]["type"] != rooms[r]["type"]:
                    continue

                for t in time_slots:
                    X[(b, s, f, r, t)] = model.NewBoolVar(
                        f"X_{b}_{s}_{f}_{r}_{t}"
                    )

# -----------------------
# Constraints
# -----------------------

# 1. Subject weekly slots per batch
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

# 2. Batch clash
for b in batches:
    for t in time_slots:
        model.Add(
            sum(
                X[(bb, s, f, r, tt)]
                for (bb, s, f, r, tt) in X
                if bb == b and tt == t
            )
            <= 1
        )

# 3. Faculty clash
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

# -----------------------
# Solve
# -----------------------

solver = cp_model.CpSolver()
status = solver.Solve(model)

print("Solver status:", solver.StatusName(status))

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    for (b, s, f, r, t), var in X.items():
        if solver.Value(var) == 1:
            print(
                f"Batch {b} | Subject {s} | Faculty {f} | Room {r} | Slot {t}"
            )
