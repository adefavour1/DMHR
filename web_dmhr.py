import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# === Fixed Light Theme ===
background_color = "#87CEEB"
text_color = "#000000"

st.markdown(f"""
    <style>
        .title-style {{
            text-align: center;
            color: #00008B;
            font-size: 42px;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .subtitle-style {{
            text-align: center;
            color: #444444;
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 30px;
        }}
        .stApp {{
            background-color: {background_color};
            color: {text_color};
        }}
    </style>
    <div class="title-style">🧮 Dynamic Machine Hour Rate (DMHR) Calculator</div>
    <div class="subtitle-style">Created by: Adedeji, Favour Busayo</div>
    <hr style='margin-top: 0'>
""", unsafe_allow_html=True)

# === Calculation Functions ===
def calculate_fixed_costs(Pm, Ls, inflation_rate, insurance_rate, am, Af, Cb, Hf, Oc, tax_env_cost):
    amortized_cost = Pm / Ls
    inflation_adjustment = Pm * inflation_rate
    insurance_cost = Pm * insurance_rate
    building_space_cost = (am / Af) * Cb
    overhead_cost = (Hf / Ls) * Oc
    return amortized_cost + inflation_adjustment + insurance_cost + building_space_cost + overhead_cost + tax_env_cost

def calculate_variable_costs(Pt_m, Rt, Sm, Um, labour_rate, Hf):
    energy_cost = Pt_m * Rt
    maintenance_cost = Sm + Um
    labour_cost = labour_rate * Hf
    return energy_cost + maintenance_cost + labour_cost

def calculate_dmhr(FC, VC, Hf):
    return (FC + VC) / Hf

# === Excel Export with Descriptive Names ===
def export_to_excel_with_charts(inputs_dict, results_df, project_name="DMHR_Project"):
    import xlsxwriter

    param_labels = {
        "Pm": "Machine Purchase Cost (₦)",
        "Ls": "Machine Life Span (hours)",
        "inflation_rate": "Inflation Rate",
        "insurance_rate": "Insurance Rate",
        "am": "Area Occupied by Machine (m²)",
        "Af": "Total Factory Area (m²)",
        "Cb": "Building Cost or Rent (₦)",
        "Hf": "Machine Hours Used (hours)",
        "Oc": "Overhead Cost (₦)",
        "tax_env_cost": "Tax & Environmental Cost (₦)",
        "Pt_m": "Energy Use (kWh)",
        "Rt": "Energy Cost per kWh (₦)",
        "Sm": "Scheduled Maintenance (₦)",
        "Um": "Unscheduled Maintenance (₦)",
        "labour_rate": "Labour Cost per Hour (₦)"
    }

    inputs_df = pd.DataFrame([
        {"Parameter": param_labels.get(k, k), "Value": v}
        for k, v in inputs_dict.items()
    ])

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{project_name.replace(' ', '_')}_{timestamp}.xlsx"

    with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
        inputs_df.to_excel(writer, sheet_name="Inputs", index=False)
        results_df.to_excel(writer, sheet_name="Results", index=False)

        workbook = writer.book
        worksheet = writer.sheets["Results"]

        chart1 = workbook.add_chart({'type': 'column'})
        chart1.add_series({
            'name': 'Fixed Cost',
            'categories': ['Results', 1, 0, len(results_df), 0],
            'values': ['Results', 1, 1, len(results_df), 1],
            'fill': {'color': '#1f77b4'}
        })
        chart1.add_series({
            'name': 'Variable Cost',
            'categories': ['Results', 1, 0, len(results_df), 0],
            'values': ['Results', 1, 2, len(results_df), 2],
            'fill': {'color': '#ff7f0e'}
        })
        chart1.set_title({'name': 'Fixed vs Variable Costs'})
        worksheet.insert_chart('E2', chart1)

        chart2 = workbook.add_chart({'type': 'pie'})
        chart2.add_series({
            'name': 'Cost Distribution',
            'categories': ['Results', 0, 1, 0, 2],
            'values': ['Results', 1, 1, 1, 2],
        })
        chart2.set_title({'name': 'Cost Share'})
        worksheet.insert_chart('E20', chart2)

    return filename

# === App Logic ===
with st.form(key="single_machine_form"):
    st.markdown("### 🏗️ **Fixed Cost Inputs**")
    Pm = st.number_input("**Machine Purchase Cost (₦)**", min_value=0.0)
    Ls = st.number_input("**Machine Life Span (hours)**", min_value=1.0)
    inflation_rate = st.number_input("**Inflation Rate (e.g. 0.05)**", min_value=0.0, max_value=1.0)
    insurance_rate = st.number_input("**Insurance Rate (e.g. 0.02)**", min_value=0.0, max_value=1.0)
    am = st.number_input("**Area Occupied by Machine (m²)**", min_value=0.0)
    Af = st.number_input("**Total Factory Area (m²)**", min_value=0.0)
    Cb = st.number_input("**Building Cost or Rent (₦)**", min_value=0.0)
    Hf = st.number_input("**Machine Hours Used (hours)**", min_value=1.0)
    Oc = st.number_input("**Overhead Cost (₦)**", min_value=0.0)
    tax_env_cost = st.number_input("**Tax & Environmental Cost (₦)**", min_value=0.0)

    st.markdown("### ⚙️ **Variable Cost Inputs**")
    Pt_m = st.number_input("**Energy Use (kWh)**", min_value=0.0)
    Rt = st.number_input("**Energy Cost per kWh (₦)**", min_value=0.0)
    Sm = st.number_input("**Scheduled Maintenance (₦)**", min_value=0.0)
    Um = st.number_input("**Unscheduled Maintenance (₦)**", min_value=0.0)
    labour_rate = st.number_input("**Labour Cost per Hour (₦)**", min_value=0.0)

    project_name = st.text_input("**Project Name for Excel Report**", value="DMHR_Project")
    submitted = st.form_submit_button("**🧮 Calculate DMHR**")

if submitted:
    FC = calculate_fixed_costs(Pm, Ls, inflation_rate, insurance_rate, am, Af, Cb, Hf, Oc, tax_env_cost)
    VC = calculate_variable_costs(Pt_m, Rt, Sm, Um, labour_rate, Hf)
    DMHR = calculate_dmhr(FC, VC, Hf)

    st.success("✅ Calculation Complete!")

    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Fixed Costs (₦)", f"{FC:,.2f}")
    col2.metric("🛠️ Variable Costs (₦)", f"{VC:,.2f}")
    col3.metric("📊 DMHR (₦/hr)", f"{DMHR:,.2f}")

    # Display charts in Streamlit
    cost_data = pd.DataFrame({
        "Cost Type": ["Fixed Costs", "Variable Costs"],
        "Amount": [FC, VC]
    })
    st.subheader("📊 Cost Breakdown (Bar Chart)")
    st.bar_chart(cost_data.set_index("Cost Type"))

    pie_data = pd.DataFrame({
        'Cost Type': ['Fixed Costs', 'Variable Costs'],
        'Amount': [FC, VC]
    })
    st.subheader("🥧 Cost Breakdown (Pie Chart)")
    st.plotly_chart(px.pie(pie_data, values='Amount', names='Cost Type', title='Fixed vs Variable Cost Share'), use_container_width=True)

    # Prepare data for Excel export
    inputs_dict = {
        "Pm": Pm, "Ls": Ls, "inflation_rate": inflation_rate, "insurance_rate": insurance_rate,
        "am": am, "Af": Af, "Cb": Cb, "Hf": Hf, "Oc": Oc, "tax_env_cost": tax_env_cost,
        "Pt_m": Pt_m, "Rt": Rt, "Sm": Sm, "Um": Um, "labour_rate": labour_rate
    }
    results_df = pd.DataFrame({
        "Machine": [project_name],
        "Fixed Cost": [round(FC, 2)],
        "Variable Cost": [round(VC, 2)],
        "DMHR (₦/hr)": [round(DMHR, 2)]
    })

    excel_file = export_to_excel_with_charts(inputs_dict, results_df, project_name)
    with open(excel_file, "rb") as file:
        st.download_button("📥 Download Full Excel Report", file, file_name=excel_file)
