import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# === Fixed Light Theme ===
background_color = "#87CEEB"
text_color = "#000000"

# === Header Styling ===
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

# === New Excel Export with Charts ===
def export_to_excel_with_charts(inputs_df, results_df, project_name="DMHR_Project"):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{project_name.replace(' ', '_')}_{timestamp}.xlsx"

    try:
        with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
            inputs_df.to_excel(writer, sheet_name="Inputs", index=False)
            results_df.to_excel(writer, sheet_name="Results", index=False)

            workbook = writer.book
            worksheet = writer.sheets["Results"]

            # Bar Chart
            chart1 = workbook.add_chart({'type': 'column'})
            chart1.add_series({
                'name':       'Fixed Cost',
                'categories': ['Results', 1, 0, len(results_df), 0],
                'values':     ['Results', 1, 1, len(results_df), 1],
                'fill':       {'color': '#1f77b4'}
            })
            chart1.add_series({
                'name':       'Variable Cost',
                'categories': ['Results', 1, 0, len(results_df), 0],
                'values':     ['Results', 1, 2, len(results_df), 2],
                'fill':       {'color': '#ff7f0e'}
            })
            chart1.set_title({'name': 'Fixed vs Variable Costs'})
            chart1.set_x_axis({'name': 'Machine'})
            chart1.set_y_axis({'name': 'Cost (₦)'})
            worksheet.insert_chart('E2', chart1)

            # Pie Chart
            chart2 = workbook.add_chart({'type': 'pie'})
            chart2.add_series({
                'name': 'Cost Distribution',
                'categories': ['Results', 0, 0, 0, 2],
                'values':     ['Results', 1, 1, 1, 2],
            })
            chart2.set_title({'name': 'Cost Share'})
            worksheet.insert_chart('E20', chart2)

        return filename

    except ImportError:
        st.warning("xlsxwriter is not installed. Exporting without charts.")
        results_df.to_excel(filename, index=False)
        return filename

# === App Logic ===
compare_mode = st.checkbox("🧮 Compare Multiple Machines", key="compare_mode")

if compare_mode:
    st.subheader("🔄 Multi-Machine Comparison Mode")
    machine_count = st.number_input("How many machines do you want to compare?", min_value=2, max_value=5, step=1)
    machine_inputs = []

    for i in range(int(machine_count)):
        with st.expander(f"🔧 Machine {i+1} Inputs", expanded=(i == 0)):
            Pm = st.number_input("Purchase Cost (₦)", key=f"Pm_{i}", min_value=0.0)
            Ls = st.number_input("Life Span (hours)", key=f"Ls_{i}", min_value=1.0)
            inflation_rate = st.number_input("Inflation Rate", key=f"inf_{i}", min_value=0.0, max_value=1.0)
            insurance_rate = st.number_input("Insurance Rate", key=f"ins_{i}", min_value=0.0, max_value=1.0)
            am = st.number_input("Area Occupied (m²)", key=f"am_{i}", min_value=0.0)
            Af = st.number_input("Total Factory Area (m²)", key=f"Af_{i}", min_value=0.0)
            Cb = st.number_input("Building Cost/Rent (₦)", key=f"Cb_{i}", min_value=0.0)
            Hf = st.number_input("Hours Used", key=f"Hf_{i}", min_value=1.0)
            Oc = st.number_input("Overhead Cost (₦)", key=f"Oc_{i}", min_value=0.0)
            tax_env_cost = st.number_input("Tax & Environmental Cost (₦)", key=f"tax_{i}", min_value=0.0)
            Pt_m = st.number_input("Energy Use (kWh)", key=f"Pt_{i}", min_value=0.0)
            Rt = st.number_input("Energy Cost per kWh (₦)", key=f"Rt_{i}", min_value=0.0)
            Sm = st.number_input("Scheduled Maintenance (₦)", key=f"Sm_{i}", min_value=0.0)
            Um = st.number_input("Unscheduled Maintenance (₦)", key=f"Um_{i}", min_value=0.0)
            labour_rate = st.number_input("Labour Cost per Hour (₦)", key=f"lr_{i}", min_value=0.0)
            project_name = st.text_input("Machine Name / Label", value=f"Machine_{i+1}", key=f"label_{i}")

            machine_inputs.append({
                "Pm": Pm, "Ls": Ls, "inflation_rate": inflation_rate, "insurance_rate": insurance_rate,
                "am": am, "Af": Af, "Cb": Cb, "Hf": Hf, "Oc": Oc, "tax_env_cost": tax_env_cost,
                "Pt_m": Pt_m, "Rt": Rt, "Sm": Sm, "Um": Um, "labour_rate": labour_rate,
                "project_name": project_name
            })

    if st.button("🔍 Compare All Machines"):
        results = []
        for m in machine_inputs:
            FC = calculate_fixed_costs(m["Pm"], m["Ls"], m["inflation_rate"], m["insurance_rate"],
                                       m["am"], m["Af"], m["Cb"], m["Hf"], m["Oc"], m["tax_env_cost"])
            VC = calculate_variable_costs(m["Pt_m"], m["Rt"], m["Sm"], m["Um"], m["labour_rate"], m["Hf"])
            DMHR = calculate_dmhr(FC, VC, m["Hf"])
            results.append({
                "Machine": m["project_name"],
                "Fixed Cost": round(FC, 2),
                "Variable Cost": round(VC, 2),
                "DMHR (₦/hr)": round(DMHR, 2)
            })

        inputs_df = pd.DataFrame(machine_inputs)
        results_df = pd.DataFrame(results)

        st.dataframe(results_df)
        st.bar_chart(results_df.set_index("Machine")[["Fixed Cost", "Variable Cost"]])
        st.line_chart(results_df.set_index("Machine")[["DMHR (₦/hr)"]])

        excel_file = export_to_excel_with_charts(inputs_df, results_df, project_name="DMHR_Comparison")
        with open(excel_file, "rb") as file:
            st.download_button("📥 Download Excel Report with Charts", file, file_name=excel_file)

else:
    with st.form(key="unique_single_form"):
        Pm = st.number_input("Machine purchase cost (₦)", min_value=0.0)
        Ls = st.number_input("Machine life span (hours)", min_value=1.0)
        inflation_rate = st.number_input("Inflation rate", min_value=0.0, max_value=1.0)
        insurance_rate = st.number_input("Insurance rate", min_value=0.0, max_value=1.0)
        am = st.number_input("Area occupied by machine (m²)", min_value=0.0)
        Af = st.number_input("Total factory area (m²)", min_value=0.0)
        Cb = st.number_input("Building cost or rent (₦)", min_value=0.0)
        Hf = st.number_input("Machine hours used (hours)", min_value=1.0)
        Oc = st.number_input("Total overhead cost (₦)", min_value=0.0)
        tax_env_cost = st.number_input("Tax & environmental cost (₦)", min_value=0.0)
        Pt_m = st.number_input("Machine energy consumption (kWh)", min_value=0.0)
        Rt = st.number_input("Energy rate per kWh (₦/kwh)", min_value=0.0)
        Sm = st.number_input("Scheduled maintenance cost (₦)", min_value=0.0)
        Um = st.number_input("Unscheduled maintenance cost (₦)", min_value=0.0)
        labour_rate = st.number_input("Labour cost per hour (₦/hr)", min_value=0.0)
        project_name = st.text_input("Project name for Excel report", value="DMHR_Project")

        submitted = st.form_submit_button("🧮 Calculate DMHR")

    if submitted:
        FC = calculate_fixed_costs(Pm, Ls, inflation_rate, insurance_rate, am, Af, Cb, Hf, Oc, tax_env_cost)
        VC = calculate_variable_costs(Pt_m, Rt, Sm, Um, labour_rate, Hf)
        DMHR = calculate_dmhr(FC, VC, Hf)

        inputs_df = pd.DataFrame([{
            "Pm": Pm, "Ls": Ls, "inflation_rate": inflation_rate, "insurance_rate": insurance_rate,
            "am": am, "Af": Af, "Cb": Cb, "Hf": Hf, "Oc": Oc, "tax_env_cost": tax_env_cost,
            "Pt_m": Pt_m, "Rt": Rt, "Sm": Sm, "Um": Um, "labour_rate": labour_rate
        }])

        results_df = pd.DataFrame([{
            "Machine": project_name,
            "Fixed Cost": round(FC, 2),
            "Variable Cost": round(VC, 2),
            "DMHR (₦/hr)": round(DMHR, 2)
        }])

        st.metric("💰 Fixed Costs (₦)", f"{FC:,.2f}")
        st.metric("🔧 Variable Costs (₦)", f"{VC:,.2f}")
        st.metric("📈 DMHR (₦/hr)", f"{DMHR:,.2f}")

        st.bar_chart(results_df.set_index("Machine")[["Fixed Cost", "Variable Cost"]])
        st.plotly_chart(
            px.pie(results_df.melt(id_vars=["Machine"], value_vars=["Fixed Cost", "Variable Cost"]),
                   values='value', names='variable', title='Fixed vs Variable Cost Share'),
            use_container_width=True
        )

        excel_file = export_to_excel_with_charts(inputs_df, results_df, project_name)
        with open(excel_file, "rb") as file:
            st.download_button("📥 Download Excel Report with Charts", file, file_name=excel_file)
