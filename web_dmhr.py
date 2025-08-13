import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
from datetime import datetime
import io

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
    FC = amortized_cost + inflation_adjustment + insurance_cost + building_space_cost + overhead_cost + tax_env_cost
    return FC

def calculate_variable_costs(Pt_m, Rt, Sm, Um, labour_rate, Hf):
    energy_cost = Pt_m * Rt
    maintenance_cost = Sm + Um
    labour_cost = labour_rate * Hf
    VC = energy_cost + maintenance_cost + labour_cost
    return VC

def calculate_dmhr(FC, VC, Hf):
    return (FC + VC) / Hf

def export_to_excel_with_charts(inputs_df, results_df, charts, filename="DMHR_Report"):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_filename = f"{filename}_{timestamp}.xlsx"
    with pd.ExcelWriter(output_filename, engine='xlsxwriter') as writer:
        inputs_df.to_excel(writer, sheet_name="Inputs", index=False)
        results_df.to_excel(writer, sheet_name="Results", index=False)
        workbook = writer.book
        worksheet = workbook.add_worksheet("Charts")
        writer.sheets["Charts"] = worksheet
        for idx, (title, img_bytes) in enumerate(charts):
            worksheet.write(idx * 20, 0, title)
            worksheet.insert_image(idx * 20 + 1, 0, "", {"image_data": img_bytes})
    return output_filename

# === App Logic ===
compare_mode = st.checkbox("🧮 Compare Multiple Machines", key="compare_mode")

if compare_mode:
    st.subheader("🔄 Multi-Machine Comparison Mode")
    machine_count = st.number_input("How many machines do you want to compare?", min_value=2, max_value=5, step=1)
    machine_inputs = []

    for i in range(int(machine_count)):
        with st.expander(f"🔧 Machine {i+1} Inputs", expanded=(i == 0)):
            Pm = st.number_input("**Purchase Cost (₦)**", key=f"Pm_{i}", min_value=0.0, step=1000.0)
            Ls = st.number_input("**Life Span (hours)**", key=f"Ls_{i}", min_value=1.0, step=100.0)
            inflation_rate = st.number_input("**Inflation Rate (e.g. 0.05)**", key=f"inf_{i}", min_value=0.0, max_value=1.0, step=0.01)
            insurance_rate = st.number_input("**Insurance Rate (e.g. 0.02)**", key=f"ins_{i}", min_value=0.0, max_value=1.0, step=0.01)
            am = st.number_input("**Area Occupied (m²)**", key=f"am_{i}", min_value=0.0, step=1.0)
            Af = st.number_input("**Total Factory Area (m²)**", key=f"Af_{i}", min_value=1.0, step=10.0)
            Cb = st.number_input("**Building Cost/Rent (₦)**", key=f"Cb_{i}", min_value=0.0, step=1000.0)
            Hf = st.number_input("**Hours Used**", key=f"Hf_{i}", min_value=1.0, step=1.0)
            Oc = st.number_input("**Overhead Cost (₦)**", key=f"Oc_{i}", min_value=0.0, step=100.0)
            tax_env_cost = st.number_input("**Tax & Environmental Cost (₦)**", key=f"tax_{i}", min_value=0.0, step=100.0)
            Pt_m = st.number_input("**Energy Use (kWh)**", key=f"Pt_{i}", min_value=0.0, step=1.0)
            Rt = st.number_input("**Energy Cost per kWh (₦)**", key=f"Rt_{i}", min_value=0.0, step=1.0)
            Sm = st.number_input("**Scheduled Maintenance (₦)**", key=f"Sm_{i}", min_value=0.0, step=100.0)
            Um = st.number_input("**Unscheduled Maintenance (₦)**", key=f"Um_{i}", min_value=0.0, step=100.0)
            labour_rate = st.number_input("**Labour Cost per Hour (₦)**", key=f"lr_{i}", min_value=0.0, step=10.0)
            project_name = st.text_input("**Machine Name / Label**", value=f"Machine_{i+1}", key=f"label_{i}")

            machine_inputs.append({
                "Pm": Pm, "Ls": Ls, "inflation_rate": inflation_rate, "insurance_rate": insurance_rate,
                "am": am, "Af": Af, "Cb": Cb, "Hf": Hf, "Oc": Oc, "tax_env_cost": tax_env_cost,
                "Pt_m": Pt_m, "Rt": Rt, "Sm": Sm, "Um": Um, "labour_rate": labour_rate,
                "project_name": project_name
            })

    if st.button("🔍 Compare All Machines"):
        results = []
        inputs_df = pd.DataFrame(machine_inputs)
        charts = []

        for m in machine_inputs:
            FC = calculate_fixed_costs(**m)
            VC = calculate_variable_costs(m["Pt_m"], m["Rt"], m["Sm"], m["Um"], m["labour_rate"], m["Hf"])
            DMHR = calculate_dmhr(FC, VC, m["Hf"])
            results.append({
                "Machine": m["project_name"],
                "Fixed Cost": round(FC, 2),
                "Variable Cost": round(VC, 2),
                "DMHR (₦/hr)": round(DMHR, 2)
            })

        results_df = pd.DataFrame(results)

        # Charts
        fig_bar = px.bar(results_df, x="Machine", y=["Fixed Cost", "Variable Cost"], barmode="group")
        fig_dmhr = px.line(results_df, x="Machine", y="DMHR (₦/hr)", markers=True)

        buf_bar, buf_dmhr = io.BytesIO(), io.BytesIO()
        fig_bar.write_image(buf_bar, format="png")
        fig_dmhr.write_image(buf_dmhr, format="png")
        charts.append(("Cost Breakdown", buf_bar))
        charts.append(("DMHR Trend", buf_dmhr))

        # Export
        excel_file = export_to_excel_with_charts(inputs_df, results_df, charts, "DMHR_Comparison")
        with open(excel_file, "rb") as file:
            st.download_button("📥 Download Full Excel Report", file, file_name=excel_file)

        # Display
        st.dataframe(results_df)
        st.plotly_chart(fig_bar, use_container_width=True)
        st.plotly_chart(fig_dmhr, use_container_width=True)

else:
    with st.form(key="unique_single_form"):
        Pm = st.number_input("**Machine purchase cost (₦)**", min_value=0.0, step=1000.0)
        Ls = st.number_input("**Machine life span (hours)**", min_value=1.0, step=100.0)
        inflation_rate = st.number_input("**Inflation rate (e.g. 0.05)**", min_value=0.0, max_value=1.0, step=0.01)
        insurance_rate = st.number_input("**Insurance rate (e.g. 0.02)**", min_value=0.0, max_value=1.0, step=0.01)
        am = st.number_input("**Area occupied by machine (m²)**", min_value=0.0, step=1.0)
        Af = st.number_input("**Total factory area (m²)**", min_value=1.0, step=10.0)
        Cb = st.number_input("**Building cost or rent (₦)**", min_value=0.0, step=1000.0)
        Hf = st.number_input("**Machine hours used (hours)**", min_value=1.0, step=1.0)
        Oc = st.number_input("**Total overhead cost (₦)**", min_value=0.0, step=100.0)
        tax_env_cost = st.number_input("**Tax & environmental cost (₦)**", min_value=0.0, step=100.0)
        Pt_m = st.number_input("**Machine energy consumption (kWh)**", min_value=0.0, step=1.0)
        Rt = st.number_input("**Energy rate per kWh (₦)**", min_value=0.0, step=1.0)
        Sm = st.number_input("**Scheduled maintenance cost (₦)**", min_value=0.0, step=100.0)
        Um = st.number_input("**Unscheduled maintenance cost (₦)**", min_value=0.0, step=100.0)
        labour_rate = st.number_input("**Labour cost per hour (₦/hr)**", min_value=0.0, step=10.0)
        project_name = st.text_input("**Project name for Excel report**", value="", placeholder="Enter project name")
        submitted = st.form_submit_button("**🧮 Calculate DMHR**")

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
            "Fixed Cost": round(FC, 2),
            "Variable Cost": round(VC, 2),
            "DMHR (₦/hr)": round(DMHR, 2)
        }])

        # Charts
        fig_bar = px.bar(results_df.melt(var_name="Type", value_name="Amount"), x="Type", y="Amount")
        fig_pie = px.pie(results_df.melt(var_name="Type", value_name="Amount"), names="Type", values="Amount")

        buf_bar, buf_pie = io.BytesIO(), io.BytesIO()
        fig_bar.write_image(buf_bar, format="png")
        fig_pie.write_image(buf_pie, format="png")
        charts = [("Cost Breakdown", buf_bar), ("Cost Share", buf_pie)]

        excel_file = export_to_excel_with_charts(inputs_df, results_df, charts, project_name or "DMHR_Project")
        with open(excel_file, "rb") as file:
            st.download_button("📥 Download Full Excel Report", file, file_name=excel_file)

        st.metric("💰 Fixed Costs (₦)", f"{FC:,.2f}")
        st.metric("🔧 Variable Costs (₦)", f"{VC:,.2f}")
        st.metric("📈 DMHR (₦/hr)", f"{DMHR:,.2f}")
        st.plotly_chart(fig_bar, use_container_width=True)
        st.plotly_chart(fig_pie, use_container_width=True)
