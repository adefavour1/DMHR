import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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

# === Improved Export Function ===
def export_to_excel(inputs_dict, FC, VC, DMHR, project_name="DMHR_Project"):
    import xlsxwriter

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{project_name.replace(' ', '_')}_{timestamp}.xlsx"

    writer = pd.ExcelWriter(filename, engine='xlsxwriter')

    # Inputs sheet
    inputs_df = pd.DataFrame(list(inputs_dict.items()), columns=["Parameter", "Value"])
    inputs_df.to_excel(writer, sheet_name="Inputs", index=False)

    # Results sheet
    results_df = pd.DataFrame({
        "Cost Type": ["Fixed Cost", "Variable Cost", "Total Cost", "DMHR"],
        "Amount (₦)": [round(FC, 2), round(VC, 2), round(FC + VC, 2), round(DMHR, 2)]
    })
    results_df.to_excel(writer, sheet_name="Results", index=False)

    # Charts
    bar_fig = go.Figure(data=[
        go.Bar(name='Costs', x=["Fixed Cost", "Variable Cost"], y=[FC, VC])
    ])
    bar_fig.update_layout(title="Fixed vs Variable Costs", yaxis_title="₦")

    pie_fig = go.Figure(data=[
        go.Pie(labels=["Fixed Costs", "Variable Costs"], values=[FC, VC])
    ])
    pie_fig.update_layout(title="Cost Share")

    bar_img = io.BytesIO()
    pie_img = io.BytesIO()
    bar_fig.write_image(bar_img, format="png")
    pie_fig.write_image(pie_img, format="png")
    bar_img.seek(0)
    pie_img.seek(0)

    workbook = writer.book
    worksheet = workbook.add_worksheet("Charts")
    worksheet.insert_image("B2", "bar_chart.png", {"image_data": bar_img})
    worksheet.insert_image("B20", "pie_chart.png", {"image_data": pie_img})

    writer._save()
    return filename

# === App Logic (Single Machine) ===
with st.form(key="unique_single_form"):
    st.markdown("### 🏗️ Fixed Cost Inputs")
    Pm = st.number_input("**Machine purchase cost (₦)**", min_value=0.0)
    Ls = st.number_input("**Machine life span (hours)**", min_value=1.0)
    inflation_rate = st.number_input("**Inflation rate (e.g. 0.05 for 5%)**", min_value=0.0, max_value=1.0)
    insurance_rate = st.number_input("**Insurance rate (e.g. 0.02 for 2%)**", min_value=0.0, max_value=1.0)
    am = st.number_input("**Area occupied by machine (m²)**", min_value=0.0)
    Af = st.number_input("**Total factory area (m²)**", min_value=0.0)
    Cb = st.number_input("**Building cost or rent (₦)**", min_value=0.0)
    Hf = st.number_input("**Machine hours used (hours)**", min_value=1.0)
    Oc = st.number_input("**Total overhead cost (₦)**", min_value=0.0)
    tax_env_cost = st.number_input("**Tax & environmental cost (₦)**", min_value=0.0)

    st.markdown("### ⚙️ Variable Cost Inputs")
    Pt_m = st.number_input("**Machine energy consumption (kWh)**", min_value=0.0)
    Rt = st.number_input("**Energy rate per kWh (₦/kwh)**", min_value=0.0)
    Sm = st.number_input("**Scheduled maintenance cost (₦)**", min_value=0.0)
    Um = st.number_input("**Unscheduled maintenance cost (₦)**", min_value=0.0)
    labour_rate = st.number_input("**Labour cost per hour (₦/hr)**", min_value=0.0)

    project_name = st.text_input("**Project name for Excel report**", value="DMHR_Project")
    submitted = st.form_submit_button("**🧮 Calculate DMHR**")

if submitted:
    FC = calculate_fixed_costs(Pm, Ls, inflation_rate, insurance_rate, am, Af, Cb, Hf, Oc, tax_env_cost)
    VC = calculate_variable_costs(Pt_m, Rt, Sm, Um, labour_rate, Hf)
    DMHR = calculate_dmhr(FC, VC, Hf)

    st.success("✅ Calculation Complete!")

    col1, col2, col3 = st.columns(3)
    col1.metric(label="💰 Fixed Costs (₦)", value=f"{FC:,.2f}")
    col2.metric(label="🔧 Variable Costs (₦)", value=f"{VC:,.2f}")
    col3.metric(label="📈 DMHR (₦/hr)", value=f"{DMHR:,.2f}")

    # Live charts in Streamlit
    cost_data = pd.DataFrame({
        "Amount (₦)": [FC, VC],
        "Cost Type": ["Fixed Costs", "Variable Costs"]
    })
    st.bar_chart(cost_data.set_index("Cost Type"))

    pie_data = pd.DataFrame({
        'Cost Type': ['Fixed Costs', 'Variable Costs'],
        'Amount': [FC, VC]
    })
    st.plotly_chart(
        px.pie(pie_data, values='Amount', names='Cost Type', title='Fixed vs Variable Cost Share'),
        use_container_width=True
    )

    # Prepare inputs for Excel
    inputs_dict = {
        "Purchase Cost (₦)": Pm,
        "Life Span (hrs)": Ls,
        "Inflation Rate": inflation_rate,
        "Insurance Rate": insurance_rate,
        "Area Occupied (m²)": am,
        "Total Factory Area (m²)": Af,
        "Building Cost (₦)": Cb,
        "Hours Used": Hf,
        "Overhead Cost (₦)": Oc,
        "Tax & Environmental Cost (₦)": tax_env_cost,
        "Energy Use (kWh)": Pt_m,
        "Energy Rate (₦/kWh)": Rt,
        "Scheduled Maintenance (₦)": Sm,
        "Unscheduled Maintenance (₦)": Um,
        "Labour Rate (₦/hr)": labour_rate
    }

    excel_file = export_to_excel(inputs_dict, FC, VC, DMHR, project_name)
    with open(excel_file, "rb") as file:
        st.download_button("📥 Download Full Excel Report", file, file_name=excel_file)
