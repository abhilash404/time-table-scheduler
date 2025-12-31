from ortools.sat.python import cp_model

# Create the model
model = cp_model.CpModel()

# Decision variables
# x[t] = 1 if class is scheduled in time slot t
x = {
    0: model.NewBoolVar("class_in_slot_0"),
    1: model.NewBoolVar("class_in_slot_1")
}

# -------------------
# Hard Constraints
# -------------------

# Class must be scheduled in exactly one slot
model.Add(x[0] + x[1] == 1)

# -------------------
# Soft Constraint
# -------------------

# Prefer slot 0 (penalize slot 1)
model.Minimize(x[1])

# -------------------
# Solve
# -------------------

solver = cp_model.CpSolver()
status = solver.Solve(model)

# -------------------
# Output
# -------------------

if status == cp_model.OPTIMAL:
    for t in x:
        if solver.Value(x[t]) == 1:
            print(f"Class scheduled in slot {t}")
