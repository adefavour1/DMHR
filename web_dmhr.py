# web_dmhr.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io

st.set_page_config(page_title="DMHR Calculator", layout="wide")

# ----------------------------
# Styling (fixed light theme)
# ----------------------------
BACKGROUND = "#87CEEB"
TEXT = "#000000"
TITLE_COLOR = "#00008B"

st.markdown(
    f"""
    <style>
        .title-style {{
            text-align: center;
            color: {TITLE_COLOR};
            font-size: 42px;
            font-weight: bold;
            margin-bottom: 6px;
        }}
        .subtitle-style {{
            text-align: center;
            color: #444444;
            font-size: 16px;
            margin-bottom: 18px;
        }}
        .stApp {{
            background-color: {BACKGROUND};
            color: {TEXT};
        }}
    </style>
    <div class="title-style">🧮 Dynamic Machine Hour Rate (DMHR) Calculator</div>
    <div class="subtitle-style">Created by: Adedeji, Favour Busayo</div>
    <hr style='margin-top: 0'>
    """,
    unsafe_allow_html=True,
)

# ----------------------------
# Calculation functions
# ----------------------------
def calculate_fixed_costs(Pm, Ls, inflation_rate, insurance_rate, am, Af, Cb, Hf, Oc, tax_env_cost):
    # All denominators validated by input widgets (min_value >= 1 for Ls and Hf)
    amortized_cost = Pm / Ls
    inflation_adjustment = Pm * inflation_rate
    insurance_cost = Pm * insurance_rate
    building_space_cost = (am / Af) * Cb if Af != 0 else 0.0
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

# ----------------------------
# Export helpers (single + multi)
# ----------------------------
def save_plotly_fig_to_bytes(fig):
    """Return PNG bytes of a Plotly figure. Requires kaleido installed."""
    img_bytes = io.BytesIO()
    # fig.write_image requires kaleido
    fig.write_image(img_bytes, format="png", scale=2)
    img_bytes.seek(0)
    return img_bytes

def export_single_excel(inputs_dict, FC, VC, DMHR, project_name="DMHR_Project"):
    """Create an Excel file with Inputs, Results and Charts (images). Returns filename."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{project_name.replace(' ', '_')}_{timestamp}.xlsx"
    writer = pd.ExcelWriter(filename, engine="xlsxwriter")
    workbook = writer.book

    # Sheet 1: Inputs
    inputs_df = pd.DataFrame(list(inputs_dict.items()), columns=["Parameter", "Value"])
    inputs_df.to_excel(writer, sheet_name="Inputs", index=False)

    # Sheet 2: Results
    results_df = pd.DataFrame({
        "Cost Type": ["Fixed Cost", "Variable Cost", "Total Cost", "DMHR (₦/hr)"],
        "Amount (₦)": [round(FC, 2), round(VC, 2), round(FC + VC, 2), round(DMHR, 2)]
    })
    results_df.to_excel(writer, sheet_name="Results", index=False)

    # Create charts (Plotly)
    bar_fig = go.Figure(data=[go.Bar(x=["Fixed Cost", "Variable Cost"], y=[FC, VC], marker_color=["#1f77b4", "#ff7f0e"])])
    bar_fig.update_layout(title="Fixed vs Variable Costs", yaxis_title="₦")

    pie_fig = go.Figure(data=[go.Pie(labels=["Fixed Costs", "Variable Costs"], values=[FC, VC], hole=0.0)])
    pie_fig.update_layout(title="Cost Composition")

    # Save charts to bytes
    bar_img = save_plotly_fig_to_bytes(bar_fig)
    pie_img = save_plotly_fig_to_bytes(pie_fig)

    # Sheet 3: Charts (insert images)
    worksheet = workbook.add_worksheet("Charts")
    # Adjust column widths for aesthetics
    worksheet.set_column("A:A", 30)
    worksheet.set_column("B:B", 30)
    worksheet.insert_image("B2", "bar.png", {"image_data": bar_img})
    worksheet.insert_image("B30", "pie.png", {"image_data": pie_img})

    writer.close()
    return filename

def export_multi_excel(list_of_inputs, results_list, project_name="DMHR_Comparison"):
    """
    list_of_inputs: list of dicts (each machine's inputs)
    results_list: list of dicts with keys: Machine, Fixed Cost, Variable Cost, DMHR (₦/hr)
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{project_name.replace(' ', '_')}_comparison_{timestamp}.xlsx"
    writer = pd.ExcelWriter(filename, engine="xlsxwriter")
    workbook = writer.book

    # Sheet1: Inputs (all machines)
    inputs_df = pd.DataFrame(list_of_inputs)
    inputs_df.to_excel(writer, sheet_name="Inputs", index=False)

    # Sheet2: Results
    results_df = pd.DataFrame(results_list)
    results_df.to_excel(writer, sheet_name="Results", index=False)

    # Charts: grouped bar (Fixed & Variable), DMHR line
    machines = results_df["Machine"].astype(str).tolist()
    fixed_vals = results_df["Fixed Cost"].tolist()
    var_vals = results_df["Variable Cost"].tolist()
    dmhr_vals = results_df["DMHR (₦/hr)"].tolist()

    grouped_bar = go.Figure()
    grouped_bar.add_trace(go.Bar(x=machines, y=fixed_vals, name="Fixed Cost"))
    grouped_bar.add_trace(go.Bar(x=machines, y=var_vals, name="Variable Cost"))
    grouped_bar.update_layout(barmode="group", title="Fixed and Variable Costs per Machine", yaxis_title="₦")

    dmhr_line = go.Figure()
    dmhr_line.add_trace(go.Scatter(x=machines, y=dmhr_vals, mode="lines+markers", name="DMHR (₦/hr)"))
    dmhr_line.update_layout(title="DMHR per Machine", yaxis_title="₦/hr")

    # Save chart images
    bar_img = save_plotly_fig_to_bytes(grouped_bar)
    line_img = save_plotly_fig_to_bytes(dmhr_line)

    worksheet = workbook.add_worksheet("Charts")
    worksheet.set_column("A:A", 30)
    worksheet.insert_image("B2", "grouped_bar.png", {"image_data": bar_img})
    worksheet.insert_image("B30", "dmhr_line.png", {"image_data": line_img})

    writer.close()
    return filename

# ----------------------------
# App UI — Mode selection
# ----------------------------
st.sidebar.markdown("## Mode")
mode = st.sidebar.radio("Choose a mode", ("Single Machine", "Multi-Machine"))

if mode == "Multi-Machine":
    st.header("🔄 Multi-Machine Comparison Mode")

    col_top = st.columns([2, 1])
    machine_count = col_top[0].number_input("How many machines to compare?", min_value=2, max_value=6, value=2, step=1, key="mc_count")
    # We'll collect per-machine inputs in a list
    machine_inputs = []
    for i in range(int(machine_count)):
        with st.expander(f"Machine {i+1} inputs", expanded=(i==0)):
            st.subheader(f"Machine {i+1}")
            Pm = st.number_input("Purchase Cost (₦)", min_value=0.0, key=f"m{ i }_Pm")
            Ls = st.number_input("Life Span (hours)", min_value=1.0, key=f"m{ i }_Ls")
            inflation_rate = st.number_input("Inflation Rate (e.g. 0.05)", min_value=0.0, max_value=1.0, key=f"m{ i }_inf")
            insurance_rate = st.number_input("Insurance Rate (e.g. 0.02)", min_value=0.0, max_value=1.0, key=f"m{ i }_ins")
            am = st.number_input("Area Occupied (m²)", min_value=0.0, key=f"m{ i }_am")
            Af = st.number_input("Total Factory Area (m²)", min_value=1.0, key=f"m{ i }_Af")
            Cb = st.number_input("Building Cost/Rent (₦)", min_value=0.0, key=f"m{ i }_Cb")
            Hf = st.number_input("Hours Used (hrs)", min_value=1.0, key=f"m{ i }_Hf")
            Oc = st.number_input("Overhead Cost (₦)", min_value=0.0, key=f"m{ i }_Oc")
            tax_env_cost = st.number_input("Tax & Environmental Cost (₦)", min_value=0.0, key=f"m{ i }_tax")
            Pt_m = st.number_input("Energy Use (kWh)", min_value=0.0, key=f"m{ i }_Pt")
            Rt = st.number_input("Energy Rate (₦/kWh)", min_value=0.0, key=f"m{ i }_Rt")
            Sm = st.number_input("Scheduled Maintenance (₦)", min_value=0.0, key=f"m{ i }_Sm")
            Um = st.number_input("Unscheduled Maintenance (₦)", min_value=0.0, key=f"m{ i }_Um")
            labour_rate = st.number_input("Labour Rate (₦/hr)", min_value=0.0, key=f"m{ i }_lr")
            label = st.text_input("Machine label", value=f"Machine_{i+1}", key=f"m{ i }_label")

            machine_inputs.append({
                "Machine": label,
                "Pm": Pm, "Ls": Ls, "inflation_rate": inflation_rate, "insurance_rate": insurance_rate,
                "am": am, "Af": Af, "Cb": Cb, "Hf": Hf, "Oc": Oc, "tax_env_cost": tax_env_cost,
                "Pt_m": Pt_m, "Rt": Rt, "Sm": Sm, "Um": Um, "labour_rate": labour_rate
            })

    if st.button("🔍 Compare All Machines", key="compare_button"):
        # calculate results
        results = []
        for m in machine_inputs:
            FC = calculate_fixed_costs(
                m["Pm"], m["Ls"], m["inflation_rate"], m["insurance_rate"],
                m["am"], m["Af"], m["Cb"], m["Hf"], m["Oc"], m["tax_env_cost"]
            )
            VC = calculate_variable_costs(m["Pt_m"], m["Rt"], m["Sm"], m["Um"], m["labour_rate"], m["Hf"])
            DMHR = calculate_dmhr(FC, VC, m["Hf"])
            results.append({
                "Machine": m["Machine"],
                "Fixed Cost": round(FC, 2),
                "Variable Cost": round(VC, 2),
                "DMHR (₦/hr)": round(DMHR, 2),
                "Hours Used": m["Hf"],
                "Purchase Cost": m["Pm"],
                "Lifespan (hrs)": m["Ls"]
            })

        results_df = pd.DataFrame(results)
        st.subheader("📊 Comparison Results")
        st.dataframe(results_df)

        # Charts in app
        cols = st.columns(2)
        cols[0].write("### Fixed vs Variable (per Machine)")
        cols[0].plotly_chart(
            px.bar(results_df.melt(id_vars="Machine", value_vars=["Fixed Cost", "Variable Cost"]),
                   x="Machine", y="value", color="variable", barmode="group",
                   labels={"value":"₦", "variable":"Cost Type"}),
            use_container_width=True
        )
        cols[1].write("### DMHR (₦/hr) per Machine")
        cols[1].plotly_chart(px.line(results_df, x="Machine", y="DMHR (₦/hr)", markers=True), use_container_width=True)

        # Export to Excel (inputs + results + charts)
        # prepare inputs for export (preserve order and include machine label)
        inputs_for_export = []
        for m in machine_inputs:
            row = {"Machine": m["Machine"], **m}
            inputs_for_export.append(row)

        excel_file = export_multi_excel(inputs_for_export, results)
        with open(excel_file, "rb") as f:
            st.download_button("📥 Download Comparison Excel Report", f, file_name=excel_file)

else:
    st.header("Single Machine DMHR Calculator")
    with st.form(key="single_mode_form"):
        st.markdown("### 🏗️ Fixed Cost Inputs")
        Pm = st.number_input("Machine purchase cost (₦)", min_value=0.0, value=500000.0)
        Ls = st.number_input("Machine life span (hours)", min_value=1.0, value=20000.0)
        inflation_rate = st.number_input("Inflation rate (e.g. 0.05 for 5%)", min_value=0.0, max_value=1.0, value=0.05)
        insurance_rate = st.number_input("Insurance rate (e.g. 0.02 for 2%)", min_value=0.0, max_value=1.0, value=0.02)
        am = st.number_input("Area occupied by machine (m²)", min_value=0.0, value=50.0)
        Af = st.number_input("Total factory area (m²)", min_value=1.0, value=500.0)
        Cb = st.number_input("Building cost or rent (₦)", min_value=0.0, value=1000000.0)
        Hf = st.number_input("Machine hours used (hours)", min_value=1.0, value=1000.0)
        Oc = st.number_input("Total overhead cost (₦)", min_value=0.0, value=500000.0)
        tax_env_cost = st.number_input("Tax & environmental cost (₦)", min_value=0.0, value=50000.0)

        st.markdown("### ⚙️ Variable Cost Inputs")
        Pt_m = st.number_input("Machine energy consumption (kWh)", min_value=0.0, value=2000.0)
        Rt = st.number_input("Energy rate per kWh (₦/kwh)", min_value=0.0, value=50.0)
        Sm = st.number_input("Scheduled maintenance cost (₦)", min_value=0.0, value=100000.0)
        Um = st.number_input("Unscheduled maintenance cost (₦)", min_value=0.0, value=50000.0)
        labour_rate = st.number_input("Labour cost per hour (₦/hr)", min_value=0.0, value=1000.0)

        project_name = st.text_input("Project name for Excel report", value="DMHR_Project")
        submitted = st.form_submit_button("🧮 Calculate DMHR")

    if submitted:
        FC = calculate_fixed_costs(Pm, Ls, inflation_rate, insurance_rate, am, Af, Cb, Hf, Oc, tax_env_cost)
        VC = calculate_variable_costs(Pt_m, Rt, Sm, Um, labour_rate, Hf)
        DMHR = calculate_dmhr(FC, VC, Hf)

        st.success("✅ Calculation Complete!")
        c1, c2, c3 = st.columns(3)
        c1.metric("💰 Fixed Costs (₦)", f"{FC:,.2f}")
        c2.metric("🔧 Variable Costs (₦)", f"{VC:,.2f}")
        c3.metric("📈 DMHR (₦/hr)", f"{DMHR:,.2f}")

        # Display charts in app
        cost_data = pd.DataFrame({"Cost Type": ["Fixed Costs", "Variable Costs"], "Amount (₦)": [FC, VC]})
        st.plotly_chart(px.bar(cost_data, x="Cost Type", y="Amount (₦)", title="Fixed vs Variable Costs"), use_container_width=True)
        st.plotly_chart(px.pie(cost_data, names="Cost Type", values="Amount (₦)", title="Cost Composition"), use_container_width=True)

        # Prepare inputs for excel
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

        excel_file = export_single_excel(inputs_dict, FC, VC, DMHR, project_name)
        with open(excel_file, "rb") as f:
            st.download_button("📥 Download Full Excel Report", f, file_name=excel_file)
