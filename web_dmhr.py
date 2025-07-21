import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# === Optional: Password Protection Using secrets.toml ===
#if "authenticated" not in st.session_state:
 #   st.session_state["authenticated"] = False

#if not st.session_state["authenticated"]:
 #   try:
 #       PASSWORD = st.secrets["auth"]["password"]
  #  except KeyError:
   #     st.error("Password not set. Please configure secrets.")
    #    st.stop()

    #password_input = st.text_input("\U0001f510 Enter access password:", type="password")
    #if password_input == PASSWORD:
     #   st.session_state["authenticated"] = True
       # st.success("Access granted. Welcome!")
        #st.rerun()
    #else:
     #   st.warning("Please enter the correct password to access the app.")
       # st.stop()

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
    <div class="title-style">\U0001f9ee Dynamic Machine Hour Rate (DMHR) Calculator</div>
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

def export_to_excel(FC, VC, DMHR, project_name="DMHR_Project"):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{project_name.replace(' ', '_')}_{timestamp}.xlsx"
    data = {
        "Cost Type": ["Fixed Cost", "Variable Cost", "DMHR"],
        "Amount (₦)": [round(FC, 2), round(VC, 2), round(DMHR, 2)]
    }
    df = pd.DataFrame(data)
    df.to_excel(filename, index=False)
    return filename

def export_multi_machine_to_excel(results, project_name="DMHR_Comparison"):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{project_name.replace(' ', '_')}_comparison_{timestamp}.xlsx"
    df = pd.DataFrame(results)
    df.to_excel(filename, index=False)
    return filename

# === App Logic ===
compare_mode = st.checkbox("\U0001f9ee Compare Multiple Machines", key="compare_mode")

if compare_mode:
    st.subheader("\U0001f501 Multi-Machine Comparison Mode")
    machine_count = st.number_input("How many machines do you want to compare?", min_value=2, max_value=5, step=1)
    machine_inputs = []

    for i in range(int(machine_count)):
        with st.expander(f"\U0001f527 Machine {i+1} Inputs", expanded=(i == 0)):
            st.markdown("### \U0001f3d7\ufe0f Fixed Costs")
            Pm = st.number_input("**Purchase Cost (₦)**", key=f"Pm_{i}", min_value=0.0)
            Ls = st.number_input("**Life Span (hours)**", key=f"Ls_{i}", min_value=0.0)
            inflation_rate = st.number_input("**Inflation Rate (e.g. 0.05)**", key=f"inf_{i}", min_value=0.0, max_value=1.0)
            insurance_rate = st.number_input("**Insurance Rate (e.g. 0.02)**", key=f"ins_{i}", min_value=0.0, max_value=1.0)
            am = st.number_input("**Area Occupied (m²)**", key=f"am_{i}", min_value=0.0)
            Af = st.number_input("**Total Factory Area (m²)**", key=f"Af_{i}", min_value=0.0)
            Cb = st.number_input("**Building Cost/Rent (₦)**", key=f"Cb_{i}", min_value=0.0)
            Hf = st.number_input("**Hours Used**", key=f"Hf_{i}", min_value=0.0)
            Oc = st.number_input("**Overhead Cost (₦)**", key=f"Oc_{i}", min_value=0.0)
            tax_env_cost = st.number_input("**Tax & Environmental Cost (₦)**", key=f"tax_{i}", min_value=0.0)

            st.markdown("### \u2699\ufe0f Variable Costs")
            Pt_m = st.number_input("**Energy Use (kWh)**", key=f"Pt_{i}", min_value=0.0)
            Rt = st.number_input("**Energy Cost per kWh (₦)**", key=f"Rt_{i}", min_value=0.0)
            Sm = st.number_input("**Scheduled Maintenance (₦)**", key=f"Sm_{i}", min_value=0.0)
            Um = st.number_input("**Unscheduled Maintenance (₦)**", key=f"Um_{i}", min_value=0.0)
            labour_rate = st.number_input("**Labour Cost per Hour (₦)**", key=f"lr_{i}", min_value=0.0)
            project_name = st.text_input("**Machine Name / Label**", value=f"Machine_{i+1}", key=f"label_{i}")

            machine_inputs.append({
                "Pm": Pm, "Ls": Ls, "inflation_rate": inflation_rate, "insurance_rate": insurance_rate,
                "am": am, "Af": Af, "Cb": Cb, "Hf": Hf, "Oc": Oc, "tax_env_cost": tax_env_cost,
                "Pt_m": Pt_m, "Rt": Rt, "Sm": Sm, "Um": Um, "labour_rate": labour_rate,
                "project_name": project_name
            })

    if st.button("\U0001f50d Compare All Machines"):
        results = []
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

        df = pd.DataFrame(results)
        tab1, tab2, tab3 = st.tabs(["\U0001f4ca Charts", "\U0001f4e5 Download", "\U0001f9fe Summary"])

        with tab1:
            st.dataframe(df)
            st.bar_chart(df.set_index("Machine")[["Fixed Cost", "Variable Cost"]])
            st.line_chart(df.set_index("Machine")[["DMHR (₦/hr)"]])

        with tab2:
            comparison_excel = export_multi_machine_to_excel(results)
            with open(comparison_excel, "rb") as file:
                st.download_button("\U0001f4e5 Download Comparison Excel Report", file, file_name=comparison_excel)

        with tab3:
            st.success("\u2705 Comparison complete. See breakdown above.")

else:
    with st.form(key="unique_single_form"):
        st.markdown("### \U0001f3d7\ufe0f Fixed Cost Inputs")
        Pm = st.number_input("**Machine purchase cost (₦)**", min_value=0.0)
        Ls = st.number_input("**Machine life span (hours)**", min_value=0.0)
        inflation_rate = st.number_input("**Inflation rate (e.g. 0.05 for 5%)**", min_value=0.0, max_value=1.0)
        insurance_rate = st.number_input("**Insurance rate (e.g. 0.02 for 2%)**", min_value=0.0, max_value=1.0)
        am = st.number_input("**Area occupied by machine (m²)**", min_value=0.0)
        Af = st.number_input("**Total factory area (m²)**", min_value=0.0)
        Cb = st.number_input("**Building cost or rent (₦)**", min_value=0.0)
        Hf = st.number_input("**Machine hours used (hours)**", min_value=0.0)
        Oc = st.number_input("**Total overhead cost (₦)**", min_value=0.0)
        tax_env_cost = st.number_input("**Tax & environmental cost (₦)**", min_value=0.0)

        st.markdown("### \u2699\ufe0f Variable Cost Inputs")
        Pt_m = st.number_input("**Machine energy consumption (kWh)**", min_value=0.0)
        Rt = st.number_input("**Energy rate per kWh (₦/kwh)**", min_value=0.0)
        Sm = st.number_input("**Scheduled maintenance cost (₦)**", min_value=0.0)
        Um = st.number_input("**Unscheduled maintenance cost (₦)**", min_value=0.0)
        labour_rate = st.number_input("**Labour cost per hour (₦/hr)**", min_value=0.0)

        project_name = st.text_input("**Project name for Excel report**", value="DMHR_Project")
        submitted = st.form_submit_button("**\U0001f9ee Calculate DMHR**")

    if submitted:
        FC = calculate_fixed_costs(Pm, Ls, inflation_rate, insurance_rate, am, Af, Cb, Hf, Oc, tax_env_cost)
        VC = calculate_variable_costs(Pt_m, Rt, Sm, Um, labour_rate, Hf)
        DMHR = calculate_dmhr(FC, VC, Hf)

        st.success("\u2705 Calculation Complete!")
        col1, col2, col3 = st.columns(3)
        col1.metric(label="\U0001f4b0 Fixed Costs (₦)", value=f"{FC:,.2f}")
        col2.metric(label="\U0001f527 Variable Costs (₦)", value=f"{VC:,.2f}")
        col3.metric(label="\U0001f4c8 DMHR (₦/hr)", value=f"{DMHR:,.2f}")

        excel_file = export_to_excel(FC, VC, DMHR, project_name)
        with open(excel_file, "rb") as file:
            st.download_button("\U0001f4e5 Download Excel Report", file, file_name=excel_file)

        tab1, tab2, tab3 = st.tabs(["\U0001f4ca Bar Chart", "\U0001f967 Pie Chart", "\U0001f9fe Summary"])

        with tab1:
            cost_data = pd.DataFrame({
                "Amount (₦)": [FC, VC],
                "Cost Type": ["Fixed Costs", "Variable Costs"]
            })
            st.bar_chart(cost_data.set_index("Cost Type"))

        with tab2:
            pie_data = pd.DataFrame({
                'Cost Type': ['Fixed Costs', 'Variable Costs'],
                'Amount': [FC, VC]
            })
            st.plotly_chart(
                px.pie(pie_data, values='Amount', names='Cost Type',
                       title='Fixed vs Variable Cost Share'),
                use_container_width=True
            )

        with tab3:
            st.markdown(f"""
            **Project:** `{project_name}`  
            **Date:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`  
            **Machine Usage:** `{Hf:.2f} hours`

            ### Breakdown:
            - **Fixed Costs:** ₦{FC:,.2f}
            - **Variable Costs:** ₦{VC:,.2f}
            - **Total Cost:** ₦{FC + VC:,.2f}
            - **DMHR (₦/hr):** ₦{DMHR:,.2f}
            
            ### Interpretation:
            The **Dynamic Machine Hour Rate (DMHR)** represents the real operational cost of using this machine for each hour it is in service. It combines both capital (fixed) and operational (variable) costs and helps determine:
            - Pricing decisions
            - Machine efficiency
            - Cost planning for future projects
            """)
