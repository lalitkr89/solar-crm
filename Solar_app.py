import streamlit as st

st.title("Solar Requirement Calculator")

customer = st.text_input("Customer Name")

bill = st.number_input("Monthly Electricity Bill (₹)")
unit_cost = st.number_input("Electricity Cost per unit (₹)", value=8)
roof = st.number_input("Roof Size (sqft)")

if st.button("Calculate"):

    units = bill / unit_cost
    required_kw = units / 120
    recommended_kw = round(required_kw)

    roof_capacity = roof / 100

    st.write("Units Consumption:", round(units,2),"units")
    st.write("Required Solar:", round(required_kw,2),"kW")

    if roof_capacity >= recommended_kw:

        st.success(f"Recommended System: {recommended_kw} kW")

    else:

        reduced = int(roof_capacity)
        required_roof = recommended_kw * 100

        st.warning(f"Recommended System: {reduced} kW")
        st.write("System reduced due to limited roof space.")
        st.write(f"For {recommended_kw} kW system you need approx {required_roof} sqft shadow free roof.")
        