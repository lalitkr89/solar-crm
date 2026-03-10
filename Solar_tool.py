print("===================================")
print("      SOLAR REQUIREMENT TOOL       ")
print("===================================\n")

customer = input("Customer Name: ")

bill = float(input("Monthly Electricity Bill (₹): "))
unit_cost = float(input("Electricity Cost per unit (₹): "))
roof = float(input("Roof Size (sqft): "))

# units consumed
units = bill / unit_cost

# required solar
required_kw = units / 120

# rounded recommended system
recommended_kw = round(required_kw)

# roof capacity
roof_capacity = roof / 100

print("\n===================================")
print("        SOLAR ANALYSIS RESULT      ")
print("===================================\n")

print("Customer:", customer)
print("Monthly Bill: ₹", bill)
print("Units Consumption:", round(units,2), "units\n")

print("Required Solar:", round(required_kw,2), "kW")

if roof_capacity >= recommended_kw:

    print("Recommended System:", recommended_kw, "kW")

else:

    print("Recommended System:", int(roof_capacity), "kW")

    required_roof = recommended_kw * 100

    print("Note: System size reduced due to limited roof space.")
    print("To install", recommended_kw, "kW system you need approx", required_roof, "sqft shadow free roof.")

print("\n===================================")