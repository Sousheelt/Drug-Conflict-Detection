"""
Streamlit Web Interface for Drug Conflict Detection System
"""
import streamlit as st
import pandas as pd
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import time

from model import HealthcareModel
from agents import PatientAgent
from utils import load_patients, load_drugs, load_rules, build_rules_kb, get_conflicts_cached
from auth import (
    initialize_session_state as init_auth_session,
    is_authenticated, authenticate_user, logout_user, get_current_user,
    create_default_users
)
from rbac import (
    get_user_role, has_permission, can_access_page, get_accessible_pages,
    require_permission, get_role_badge_html,
    Permission, Role, is_admin
)
from validation import sanitize_string

# Page configuration
st.set_page_config(
    page_title="Drug Conflict Detection System",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize authentication session state
init_auth_session()

# Initialize session state (must be before theme logic)
if 'model' not in st.session_state:
    st.session_state.model = None
if 'conflicts_df' not in st.session_state:
    st.session_state.conflicts_df = None
if 'simulation_run' not in st.session_state:
    st.session_state.simulation_run = False
if 'simulation_mode' not in st.session_state:
    st.session_state.simulation_mode = 'smart'
if 'custom_data_uploaded' not in st.session_state:
    st.session_state.custom_data_uploaded = False
if 'custom_patients' not in st.session_state:
    st.session_state.custom_patients = None
if 'custom_drugs' not in st.session_state:
    st.session_state.custom_drugs = None
if 'custom_rules' not in st.session_state:
    st.session_state.custom_rules = None
if 'cached_kb' not in st.session_state:
    st.session_state.cached_kb = None

# Apply light theme CSS
st.markdown("""
<style>
/* Light Theme */
.main-header {
    font-size: 2.5rem;
    font-weight: bold;
    color: #1f77b4;
    text-align: center;
    margin-bottom: 2rem;
}

.metric-card {
    background: linear-gradient(135deg, #f0f2f6 0%, #e8eaf0 100%);
    padding: 1.5rem;
    border-radius: 0.8rem;
    text-align: center;
    border: 1px solid #d0d2d6;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    transition: transform 0.2s, box-shadow 0.2s;
}

.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(31, 119, 180, 0.2);
}

.conflict-major {
    background-color: #ffebee;
    padding: 1rem;
    border-left: 4px solid #f44336;
    border-radius: 0.5rem;
    margin: 0.5rem 0;
}

.conflict-moderate {
    background-color: #fff3e0;
    padding: 1rem;
    border-left: 4px solid #ff9800;
    border-radius: 0.5rem;
    margin: 0.5rem 0;
}

.conflict-minor {
    background-color: #fff9c4;
    padding: 1rem;
    border-left: 4px solid #fbc02d;
    border-radius: 0.5rem;
    margin: 0.5rem 0;
}

/* Button hover effects */
.stButton button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
    transition: all 0.3s;
}

/* File Uploader */
[data-testid="stFileUploader"]:hover {
    border-color: #1f77b4;
    background-color: rgba(31, 119, 180, 0.05);
}

/* Animations */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

.element-container {
    animation: fadeIn 0.3s ease-out;
}
</style>
""", unsafe_allow_html=True)

# Helper functions
def load_data():
    """Load CSV data files"""
    # Use custom data if uploaded, otherwise use default files
    if st.session_state.custom_data_uploaded:
        base_dir = Path(__file__).parent
        
        # Load custom or default data
        if st.session_state.custom_patients is not None:
            patients = st.session_state.custom_patients
        else:
            patients = load_patients(base_dir / "patients.csv")
        
        if st.session_state.custom_drugs is not None:
            drugs = st.session_state.custom_drugs
        else:
            drugs = load_drugs(base_dir / "drugs.csv")
        
        if st.session_state.custom_rules is not None:
            rules = st.session_state.custom_rules
        else:
            rules = load_rules(base_dir / "rules.csv")
        
        return patients, drugs, rules
    else:
        base_dir = Path(__file__).parent
        patients = load_patients(base_dir / "patients.csv")
        drugs = load_drugs(base_dir / "drugs.csv")
        rules = load_rules(base_dir / "rules.csv")
        return patients, drugs, rules

def save_uploaded_file(uploaded_file, file_type):
    """Process and save uploaded CSV file to session state"""
    try:
        # Read the uploaded file
        df = pd.read_csv(uploaded_file)
        
        # Convert DataFrame to list of dictionaries
        data = df.to_dict('records')
        
        # Process based on file type
        if file_type == "patients":
            # Process conditions and allergies fields
            for record in data:
                if 'conditions' in record and isinstance(record['conditions'], str):
                    record['conditions'] = record['conditions'].split(';')
                if 'allergies' in record and isinstance(record['allergies'], str):
                    record['allergies'] = record['allergies'].split(';')
            st.session_state.custom_patients = data
            
        elif file_type == "drugs":
            st.session_state.custom_drugs = data
            
        elif file_type == "rules":
            st.session_state.custom_rules = data
        
        st.session_state.custom_data_uploaded = True
        return True, f"{file_type.capitalize()} data uploaded successfully!"
    
    except Exception as e:
        return False, f"Error uploading {file_type}: {str(e)}"

def run_simulation(mode: str = "smart"):
    """Run the drug conflict detection simulation
    
    Args:
        mode: "smart" for conflict-avoiding or "conflict-prone" for demonstration
    """
    base_dir = Path(__file__).parent
    
    # Save custom data to temporary CSV files if uploaded
    if st.session_state.custom_data_uploaded:
        temp_dir = base_dir / "temp_data"
        temp_dir.mkdir(exist_ok=True)
        
        # Save custom data to temp files
        if st.session_state.custom_patients is not None:
            temp_patients = pd.DataFrame(st.session_state.custom_patients)
            # Convert lists back to semicolon-separated strings
            if 'conditions' in temp_patients.columns:
                temp_patients['conditions'] = temp_patients['conditions'].apply(
                    lambda x: ';'.join(x) if isinstance(x, list) else x
                )
            if 'allergies' in temp_patients.columns:
                temp_patients['allergies'] = temp_patients['allergies'].apply(
                    lambda x: ';'.join(x) if isinstance(x, list) else x
                )
            temp_patients.to_csv(temp_dir / "patients.csv", index=False)
        else:
            # Copy default file
            import shutil
            shutil.copy(base_dir / "patients.csv", temp_dir / "patients.csv")
        
        if st.session_state.custom_drugs is not None:
            pd.DataFrame(st.session_state.custom_drugs).to_csv(temp_dir / "drugs.csv", index=False)
        else:
            import shutil
            shutil.copy(base_dir / "drugs.csv", temp_dir / "drugs.csv")
        
        if st.session_state.custom_rules is not None:
            pd.DataFrame(st.session_state.custom_rules).to_csv(temp_dir / "rules.csv", index=False)
        else:
            import shutil
            shutil.copy(base_dir / "rules.csv", temp_dir / "rules.csv")
        
        # Run model with temp data and specified mode
        model = HealthcareModel(data_dir=temp_dir, doctor_mode=mode)
    else:
        # Run model with default data and specified mode
        model = HealthcareModel(data_dir=base_dir, doctor_mode=mode)
    
    model.run(steps=1)
    
    st.session_state.model = model
    st.session_state.conflicts_df = model.conflicts_dataframe()
    st.session_state.simulation_run = True
    st.session_state.simulation_mode = mode
    st.session_state.last_run = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def get_severity_color(severity):
    """Return color based on severity"""
    colors = {
        'Major': '#f44336',
        'Moderate': '#ff9800',
        'Minor': '#fbc02d'
    }
    return colors.get(severity, '#757575')

# ============= LOGIN PAGE =============
if not is_authenticated():
    st.markdown('<div class="main-header">💊 Drug Conflict Detection System</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.subheader("🔐 Login")
        st.info("Please login to access the system")
        
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submit = st.form_submit_button("Login", use_container_width=True, type="primary")
            
            if submit:
                if not username or not password:
                    st.error("Please enter both username and password")
                else:
                    success, error_msg = authenticate_user(username, password)
                    
                    if success:
                        st.success(f"Welcome, {username}!")
                        st.rerun()
                    else:
                        st.error(f"❌ {error_msg}")
        
        # Show default credentials
        st.divider()
        with st.expander("ℹ️ Default Credentials"):
            st.markdown("""
            **Admin Account:**
            - Username: `admin`
            - Password: `Admin@123`
            - Full system access
            
            **Doctor Account:**
            - Username: `doctor`
            - Password: `Doctor@123`
            - Can prescribe and view reports
            
            **Pharmacist Account:**
            - Username: `pharmacist`
            - Password: `Pharma@123`
            - View-only with report access
            """)
    
    st.stop()

# User is authenticated - show main interface
user = get_current_user()

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/pill.png", width=80)
    st.title("🏥 Navigation")
    
    # User info section
    st.markdown("### 👤 User Info")
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"**{user.username}**")
    with col2:
        st.markdown(get_role_badge_html(get_user_role()), unsafe_allow_html=True)
    
    if st.button("🚪 Logout", use_container_width=True):
        logout_user()
        st.rerun()
    
    st.divider()
    
    # Get accessible pages for current role
    all_pages = ["Dashboard", "Patients", "Prescription Simulator", "Conflicts", "Drug Database", "Rules Engine", "Manual Testing", "Import Data"]
    accessible_pages = []
    
    for pg in all_pages:
        if can_access_page(pg, get_user_role()):
            accessible_pages.append(pg)
    
    # Add special pages for admin
    if is_admin():
        accessible_pages.append("User Management")
    
    page = st.radio(
        "Select Page:",
        accessible_pages
    )
    
    st.divider()
    
    # Quick Actions
    st.subheader("Quick Actions")
    
    # Only show run simulation if user has permission
    if has_permission(Permission.RUN_SIMULATION):
        st.markdown("**🧠 Smart Doctor Mode**")
        st.caption("Avoids conflicts, uses replacements")
        if st.button("🔄 Run Smart Simulation", use_container_width=True, type="primary"):
            with st.spinner("Running smart simulation..."):
                run_simulation(mode="smart")
            st.success("✅ Smart Simulation completed!")
            st.rerun()
        
        st.markdown("**⚠️ Demo Mode (Conflict-Prone)**")
        st.caption("Intentionally creates conflicts")
        if st.button("🔄 Run Demo Simulation", use_container_width=True, type="secondary"):
            with st.spinner("Running demo simulation..."):
                run_simulation(mode="conflict-prone")
            st.success("⚠️ Demo Simulation completed!")
            st.rerun()
    
    if st.session_state.simulation_run:
        mode_label = "🧠 Smart" if st.session_state.get('simulation_mode', 'smart') == "smart" else "⚠️ Demo"
        st.info(f"Last run: {st.session_state.last_run}\nMode: {mode_label}")

# Main content area
st.markdown('<div class="main-header">💊 Drug Conflict Detection System</div>', unsafe_allow_html=True)

# ============= DASHBOARD PAGE =============
if page == "Dashboard":
    st.header("📊 Dashboard Overview")
    
    # Load basic data
    patients_data, drugs_data, rules_data = load_data()
    
    # Top metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Patients", len(patients_data))
    
    with col2:
        st.metric("Available Drugs", len(drugs_data))
    
    with col3:
        st.metric("Active Rules", len(rules_data))
    
    with col4:
        if st.session_state.simulation_run:
            st.metric("Conflicts Detected", len(st.session_state.conflicts_df))
        else:
            st.metric("Conflicts Detected", "Run simulation")
    
    st.divider()
    
    # Simulation results
    if st.session_state.simulation_run and st.session_state.conflicts_df is not None:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📈 Conflict Analysis")
            
            df = st.session_state.conflicts_df
            if len(df) > 0:
                # Severity distribution
                sev_counts = df['severity'].value_counts()
                
                fig = px.pie(
                    values=sev_counts.values,
                    names=sev_counts.index,
                    title="Conflicts by Severity",
                    color=sev_counts.index,
                    color_discrete_map={'Major': '#f44336', 'Moderate': '#ff9800', 'Minor': '#fbc02d'},
                    hole=0.3  # Make it a donut chart
                )
                fig.update_traces(
                    textposition='inside',
                    textinfo='percent+label',
                    hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Conflict type distribution
                type_counts = df['type'].value_counts()
                fig2 = px.bar(
                    x=type_counts.index,
                    y=type_counts.values,
                    title="Conflicts by Type",
                    labels={'x': 'Conflict Type', 'y': 'Count'},
                    color=type_counts.values,
                    color_continuous_scale='Blues',
                    text=type_counts.values
                )
                fig2.update_traces(
                    textposition='outside',
                    hovertemplate='<b>%{x}</b><br>Count: %{y}<extra></extra>'
                )
                fig2.update_layout(
                    xaxis_title="Conflict Type",
                    yaxis_title="Number of Conflicts",
                    showlegend=False
                )
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.success("✅ No conflicts detected! All prescriptions are safe.")
        
        with col2:
            st.subheader("📋 Summary Statistics")
            
            if len(df) > 0:
                st.metric("Total Conflicts", len(df))
                
                st.write("**By Severity:**")
                for sev in ['Major', 'Moderate', 'Minor']:
                    count = len(df[df['severity'] == sev])
                    if count > 0:
                        st.markdown(f"- **{sev}**: {count}")
                
                st.write("**By Type:**")
                for ctype in df['type'].unique():
                    count = len(df[df['type'] == ctype])
                    st.markdown(f"- {ctype}: {count}")
                
                # Patient risk ranking
                st.write("**Patients at Risk:**")
                patient_conflicts = df.groupby('patient_name').size().sort_values(ascending=False)
                for patient, count in patient_conflicts.items():
                    st.markdown(f"- {patient}: {count} conflict(s)")
            else:
                st.info("No conflicts to display")
    else:
        st.info("👆 Click 'Run Simulation' in the sidebar to see results")

# ============= PATIENTS PAGE =============
elif page == "Patients":
    st.header("👥 Patient Management")
    
    patients_data, _, _ = load_data()
    
    # Action buttons (only for Admin and Doctor)
    if has_permission(Permission.ADD_PATIENT) or has_permission(Permission.EDIT_PATIENT):
        col1, col2, col3 = st.columns([1, 1, 4])
        
        with col1:
            if has_permission(Permission.ADD_PATIENT):
                if st.button("➕ Add Patient", type="primary"):
                    st.session_state.show_add_patient = True
        
        with col2:
            if has_permission(Permission.EDIT_PATIENT):
                if st.button("✏️ Edit Patient"):
                    st.session_state.show_edit_patient = True
        
        st.divider()
    
    # Add Patient Form
    if st.session_state.get('show_add_patient', False):
        with st.form("add_patient_form"):
            st.subheader("Add New Patient")
            
            col1, col2 = st.columns(2)
            with col1:
                new_id = st.number_input("Patient ID", min_value=1, step=1, value=len(patients_data) + 1)
                new_name = st.text_input("Name", placeholder="John Doe")
            
            with col2:
                new_conditions = st.text_area("Conditions (one per line)", placeholder="Hypertension\nDiabetes")
                new_allergies = st.text_area("Allergies (one per line)", placeholder="Penicillin\nSulfa drugs")
            
            col_submit, col_cancel = st.columns([1, 5])
            with col_submit:
                submit = st.form_submit_button("Add Patient", type="primary")
            with col_cancel:
                cancel = st.form_submit_button("Cancel")
            
            if submit:
                if not new_name:
                    st.error("Patient name is required")
                else:
                    # Check for duplicate ID
                    if any(p['id'] == new_id for p in patients_data):
                        st.error(f"Patient ID {new_id} already exists")
                    else:
                        # Process conditions and allergies
                        conditions_list = [c.strip() for c in new_conditions.split('\n') if c.strip()]
                        allergies_list = [a.strip() for a in new_allergies.split('\n') if a.strip()]
                        
                        if not conditions_list:
                            conditions_list = ['None']
                        if not allergies_list:
                            allergies_list = ['None']
                        
                        # Add to patients data
                        new_patient = {
                            'id': new_id,
                            'name': sanitize_string(new_name),
                            'conditions': ';'.join(conditions_list),
                            'allergies': ';'.join(allergies_list)
                        }
                        
                        # Save to CSV
                        patients_df_save = pd.DataFrame(patients_data + [new_patient])
                        patients_df_save.to_csv('patients.csv', index=False)
                        
                        st.success(f"✅ Patient '{new_name}' added successfully!")
                        time.sleep(2)
                        st.session_state.show_add_patient = False
                        st.rerun()
            
            if cancel:
                st.session_state.show_add_patient = False
                st.rerun()
        
        st.divider()
    
    # Edit Patient Form
    if st.session_state.get('show_edit_patient', False):
        st.subheader("Edit Patient")
        
        patient_options = {f"{p['name']} (ID: {p['id']})": p for p in patients_data}
        
        # Initialize selected patient in session state if not set
        if 'selected_patient_for_edit' not in st.session_state:
            st.session_state.selected_patient_for_edit = list(patient_options.keys())[0]
        
        selected_patient_key = st.selectbox("Select Patient to Edit", 
                                           list(patient_options.keys()),
                                           key="patient_selector")
        selected_patient = patient_options[selected_patient_key]
        
        with st.form("edit_patient_form"):
            col1, col2 = st.columns(2)
            with col1:
                edit_id = st.number_input("Patient ID", value=int(selected_patient['id']), disabled=True, step=1)
                edit_name = st.text_input("Name", value=selected_patient['name'])
            
            with col2:
                # Convert list back to text for editing
                current_conditions = selected_patient.get('conditions', [])
                if isinstance(current_conditions, list):
                    conditions_text = '\n'.join(current_conditions)
                else:
                    conditions_text = str(current_conditions).replace(';', '\n')
                
                current_allergies = selected_patient.get('allergies', [])
                if isinstance(current_allergies, list):
                    allergies_text = '\n'.join(current_allergies)
                else:
                    allergies_text = str(current_allergies).replace(';', '\n')
                
                edit_conditions = st.text_area("Conditions (one per line)", value=conditions_text)
                edit_allergies = st.text_area("Allergies (one per line)", value=allergies_text)
            
            col_submit, col_delete, col_cancel = st.columns([1, 1, 4])
            with col_submit:
                submit = st.form_submit_button("Save Changes", type="primary")
            with col_delete:
                if has_permission(Permission.DELETE_PATIENT):
                    # Check if delete confirmation is pending
                    if st.session_state.get('confirm_delete_patient') == selected_patient['id']:
                        confirm_delete = st.form_submit_button("⚠️ CONFIRM DELETE", type="secondary")
                    else:
                        delete = st.form_submit_button("🗑️ Delete", type="secondary")
                        confirm_delete = False
                else:
                    delete = False
                    confirm_delete = False
            with col_cancel:
                cancel = st.form_submit_button("Cancel")
            
            if submit:
                if not edit_name:
                    st.error("Patient name is required")
                else:
                    # Process conditions and allergies
                    conditions_list = [c.strip() for c in edit_conditions.split('\n') if c.strip()]
                    allergies_list = [a.strip() for a in edit_allergies.split('\n') if a.strip()]
                    
                    if not conditions_list:
                        conditions_list = ['None']
                    if not allergies_list:
                        allergies_list = ['None']
                    
                    # Update patient data
                    for p in patients_data:
                        if p['id'] == selected_patient['id']:
                            p['name'] = sanitize_string(edit_name)
                            p['conditions'] = ';'.join(conditions_list)
                            p['allergies'] = ';'.join(allergies_list)
                            break
                    
                    # Save to CSV
                    patients_df_save = pd.DataFrame(patients_data)
                    patients_df_save.to_csv('patients.csv', index=False)
                    
                    st.success(f"✅ Patient '{edit_name}' updated successfully!")
                    time.sleep(2)
                    st.session_state.show_edit_patient = False
                    st.rerun()
            
            # Handle delete button click - show confirmation
            if 'delete' in locals() and delete and has_permission(Permission.DELETE_PATIENT):
                st.session_state.confirm_delete_patient = selected_patient['id']
                st.warning(f"⚠️ You are about to delete patient '{selected_patient['name']}' (ID: {selected_patient['id']}). Click 'CONFIRM DELETE' to proceed. This action cannot be undone!")
                time.sleep(2)
                st.rerun()
            
            # Handle confirm delete button click - actually delete
            if 'confirm_delete' in locals() and confirm_delete and has_permission(Permission.DELETE_PATIENT):
                # Remove patient
                patients_data = [p for p in patients_data if p['id'] != selected_patient['id']]
                
                # Save to CSV
                patients_df_save = pd.DataFrame(patients_data)
                patients_df_save.to_csv('patients.csv', index=False)
                
                # Clear confirmation state
                if 'confirm_delete_patient' in st.session_state:
                    del st.session_state.confirm_delete_patient
                
                st.success(f"✅ Patient '{selected_patient['name']}' has been permanently deleted.")
                time.sleep(2)
                st.session_state.show_edit_patient = False
                st.rerun()
            
            if cancel:
                # Clear any pending delete confirmation
                if 'confirm_delete_patient' in st.session_state:
                    del st.session_state.confirm_delete_patient
                st.session_state.show_edit_patient = False
                st.rerun()
        
        st.divider()
    
    # Display patients table
    st.subheader("Patient Records")
    
    # Convert to DataFrame for display
    patients_df = pd.DataFrame(patients_data)
    
    # Format lists for display
    if not patients_df.empty:
        patients_df['conditions'] = patients_df['conditions'].apply(lambda x: ', '.join(x) if isinstance(x, list) else x)
        patients_df['allergies'] = patients_df['allergies'].apply(lambda x: ', '.join(x) if isinstance(x, list) and x != ['None'] else 'None')
    
    st.dataframe(patients_df, use_container_width=True, height=400)
    
    st.divider()
    
    # Patient details cards
    st.subheader("Patient Details")
    
    for patient in patients_data:
        with st.expander(f"👤 {patient['name']} (ID: {patient['id']})"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Conditions:**")
                conditions = patient.get('conditions', [])
                # Handle different data types for conditions
                if isinstance(conditions, list):
                    conditions = [str(c) for c in conditions if c]
                elif conditions and str(conditions).lower() not in ['none', 'nan']:
                    conditions = [str(conditions)]
                else:
                    conditions = []
                
                if conditions:
                    for cond in conditions:
                        st.markdown(f"- {cond}")
                else:
                    st.write("None")
            
            with col2:
                st.write("**Allergies:**")
                allergies = patient.get('allergies', [])
                # Handle different data types and filter out None, 'None', and NaN values
                if isinstance(allergies, list):
                    allergies = [str(a) for a in allergies if a and str(a).lower() not in ['none', 'nan']]
                elif allergies and str(allergies).lower() not in ['none', 'nan']:
                    allergies = [str(allergies)]
                else:
                    allergies = []
                
                if allergies:
                    for allergy in allergies:
                        st.markdown(f"- {allergy}")
                else:
                    st.write("None")
            
            # Show prescription if simulation has run
            if st.session_state.model:
                patient_obj = next((p for p in st.session_state.model.patients if p.patient_id == str(patient['id'])), None)
                if patient_obj and patient_obj.prescription:
                    st.write("**Current Prescription:**")
                    for drug in patient_obj.prescription:
                        st.markdown(f"- 💊 {drug}")

# ============= PRESCRIPTION SIMULATOR PAGE =============
elif page == "Prescription Simulator":
    st.header("💉 Prescription Simulation")
    
    if not st.session_state.simulation_run:
        st.warning("No simulation has been run yet. Click 'Run Simulation' in the sidebar.")
    else:
        model = st.session_state.model
        
        st.subheader("Prescription Results")
        
        for patient in model.patients:
            with st.expander(f"👤 {patient.name}", expanded=True):
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.write("**Patient Profile:**")
                    st.write(f"- ID: {patient.patient_id}")
                    st.write(f"- Conditions: {', '.join(patient.conditions) if isinstance(patient.conditions, list) else patient.conditions}")
                    allergies = patient.allergies if isinstance(patient.allergies, list) else [patient.allergies]
                    # Convert all items to strings to handle any float/NaN values
                    allergies = [str(a) for a in allergies if a and str(a).lower() not in ['none', 'nan']]
                    st.write(f"- Allergies: {', '.join(allergies) if allergies else 'None'}")
                
                with col2:
                    st.write("**Prescribed Drugs:**")
                    if patient.prescription:
                        for drug in patient.prescription:
                            st.markdown(f"💊 **{drug}**")
                    else:
                        st.write("No prescription")
                
                with col3:
                    # Count conflicts for this patient
                    if st.session_state.conflicts_df is not None:
                        patient_conflicts = st.session_state.conflicts_df[
                            st.session_state.conflicts_df['patient_id'] == patient.patient_id
                        ]
                        conflict_count = len(patient_conflicts)
                        
                        if conflict_count > 0:
                            st.error(f"⚠️ {conflict_count} conflict(s)")
                        else:
                            st.success("✅ Safe")

# ============= CONFLICTS PAGE =============
elif page == "Conflicts":
    st.header("⚠️ Conflict Detection Results")
    
    if not st.session_state.simulation_run:
        st.warning("No simulation has been run yet. Click 'Run Simulation' in the sidebar.")
    else:
        df = st.session_state.conflicts_df
        
        if len(df) == 0:
            st.success("✅ No conflicts detected! All prescriptions are safe.")
        else:
            # Filters
            col1, col2, col3 = st.columns(3)
            
            with col1:
                severity_filter = st.multiselect(
                    "Filter by Severity:",
                    options=df['severity'].unique(),
                    default=None,
                    placeholder="All severities"
                )
            
            with col2:
                type_filter = st.multiselect(
                    "Filter by Type:",
                    options=df['type'].unique(),
                    default=None,
                    placeholder="All types"
                )
            
            with col3:
                patient_filter = st.multiselect(
                    "Filter by Patient:",
                    options=df['patient_name'].unique(),
                    default=None,
                    placeholder="All patients"
                )
            
            # Apply filters - if empty, show all
            filtered_df = df.copy()
            if severity_filter:
                filtered_df = filtered_df[filtered_df['severity'].isin(severity_filter)]
            if type_filter:
                filtered_df = filtered_df[filtered_df['type'].isin(type_filter)]
            if patient_filter:
                filtered_df = filtered_df[filtered_df['patient_name'].isin(patient_filter)]
            
            st.divider()
            
            # Display filtered conflicts
            st.subheader(f"Showing {len(filtered_df)} conflict(s)")
            
            for idx, row in filtered_df.iterrows():
                severity_class = f"conflict-{row['severity'].lower()}"
                
                with st.container():
                    st.markdown(f'<div class="{severity_class}">', unsafe_allow_html=True)
                    
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.write(f"**Patient:** {row['patient_name']}")
                        st.write(f"**Type:** {row['type']}")
                        st.write(f"**Conflict:** {row['item_a']} ↔️ {row['item_b']}")
                    
                    with col2:
                        st.write(f"**Prescription:** {row['prescription']}")
                        st.write(f"**Recommendation:** {row['recommendation']}")
                    
                    with col3:
                        st.write(f"**Severity:** {row['severity']}")
                        st.write(f"**Score:** {row['score']}")
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    st.divider()
            
            # Export buttons
            st.subheader("📥 Export Options")
            
            col_e1, col_e2, col_e3 = st.columns(3)
            
            with col_e1:
                st.download_button(
                    label="📊 Download CSV",
                    data=filtered_df.to_csv(index=False),
                    file_name=f"conflicts_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col_e2:
                if st.button("📕 Generate PDF Report", use_container_width=True):
                    try:
                        from report_generator import ReportGenerator
                        
                        # Generate summary report with all conflicts
                        if len(filtered_df) > 0:
                            # Create a summary report for all patients
                            unique_patients = filtered_df['patient_name'].unique()
                            
                            if len(unique_patients) == 1:
                                # Single patient - use their details
                                first_row = filtered_df.iloc[0]
                                patient_name = first_row['patient_name']
                                patient_id = str(first_row['patient_id'])
                                prescription = first_row['prescription'].split(';') if ';' in first_row['prescription'] else first_row['prescription'].split(', ')
                            else:
                                # Multiple patients - create summary
                                patient_name = f"Simulation Summary ({len(unique_patients)} patients)"
                                patient_id = f"SIM-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                                prescription = []
                            
                            # Prepare conflicts list with patient names
                            conflicts_list = []
                            for _, row in filtered_df.iterrows():
                                conflict_dict = {
                                    'type': row['type'],
                                    'item_a': row['item_a'],
                                    'item_b': row['item_b'],
                                    'severity': row['severity'],
                                    'recommendation': row['recommendation'],
                                    'score': row['score']
                                }
                                # Add patient name to recommendation for multi-patient reports
                                if len(unique_patients) > 1:
                                    conflict_dict['recommendation'] = f"[{row['patient_name']}] {conflict_dict['recommendation']}"
                                conflicts_list.append(conflict_dict)
                            
                            generator = ReportGenerator()
                            pdf_bytes = generator.generate_report_bytes(
                                format_type='pdf',
                                patient_name=patient_name,
                                patient_id=patient_id,
                                conditions=[],
                                allergies=[],
                                prescription=prescription,
                                conflicts=conflicts_list
                            )
                            
                            filename = f"conflicts_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                            st.download_button(
                                label="💾 Save PDF",
                                data=pdf_bytes,
                                file_name=filename,
                                mime="application/pdf",
                                use_container_width=True,
                                key="pdf_download_conflicts"
                            )
                            st.success("✅ PDF report ready!")
                        
                    except ImportError:
                        st.error("📦 Install reportlab: `pip install reportlab`")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
            
            with col_e3:
                if st.button("📘 Generate Word Report", use_container_width=True):
                    try:
                        from report_generator import ReportGenerator
                        
                        if len(filtered_df) > 0:
                            # Create a summary report for all patients
                            unique_patients = filtered_df['patient_name'].unique()
                            
                            if len(unique_patients) == 1:
                                # Single patient - use their details
                                first_row = filtered_df.iloc[0]
                                patient_name = first_row['patient_name']
                                patient_id = str(first_row['patient_id'])
                                prescription = first_row['prescription'].split(';') if ';' in first_row['prescription'] else first_row['prescription'].split(', ')
                            else:
                                # Multiple patients - create summary
                                patient_name = f"Simulation Summary ({len(unique_patients)} patients)"
                                patient_id = f"SIM-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                                prescription = []
                            
                            # Prepare conflicts list with patient names
                            conflicts_list = []
                            for _, row in filtered_df.iterrows():
                                conflict_dict = {
                                    'type': row['type'],
                                    'item_a': row['item_a'],
                                    'item_b': row['item_b'],
                                    'severity': row['severity'],
                                    'recommendation': row['recommendation'],
                                    'score': row['score']
                                }
                                # Add patient name to recommendation for multi-patient reports
                                if len(unique_patients) > 1:
                                    conflict_dict['recommendation'] = f"[{row['patient_name']}] {conflict_dict['recommendation']}"
                                conflicts_list.append(conflict_dict)
                            
                            generator = ReportGenerator()
                            word_bytes = generator.generate_report_bytes(
                                format_type='word',
                                patient_name=patient_name,
                                patient_id=patient_id,
                                conditions=[],
                                allergies=[],
                                prescription=prescription,
                                conflicts=conflicts_list
                            )
                            
                            filename = f"conflicts_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
                            st.download_button(
                                label="💾 Save Word",
                                data=word_bytes,
                                file_name=filename,
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                use_container_width=True,
                                key="word_download_conflicts"
                            )
                            st.success("✅ Word report ready!")
                        
                    except ImportError:
                        st.error("📦 Install python-docx: `pip install python-docx`")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

# ============= DRUG DATABASE PAGE =============
elif page == "Drug Database":
    st.header("💊 Drug Database")
    
    # CRUD buttons (Admin only)
    if has_permission(Permission.ADD_DRUG):
        col1, col2, _ = st.columns([1, 1, 6])
        with col1:
            if st.button("➕ Add Drug", type="primary"):
                st.session_state.show_add_drug = True
                st.session_state.show_edit_drug = False
                st.rerun()
        with col2:
            if st.button("✏️ Edit Drug"):
                st.session_state.show_edit_drug = True
                st.session_state.show_add_drug = False
                st.rerun()
        
        st.divider()
    
    # Add Drug Form
    if st.session_state.get('show_add_drug', False):
        with st.form("add_drug_form", clear_on_submit=True):
            st.subheader("➕ Add New Drug")
            
            new_drug_name = st.text_input("Drug Name*", placeholder="e.g., Aspirin")
            new_condition = st.text_input("Condition*", placeholder="e.g., Pain")
            new_category = st.text_input("Category*", placeholder="e.g., Painkiller")
            new_replacements = st.text_area("Replacements (one per line)", 
                                            placeholder="e.g., Paracetamol\nIbuprofen",
                                            help="Optional: List alternative drugs, one per line")
            
            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("Add Drug", type="primary")
            with col2:
                cancel = st.form_submit_button("Cancel")
            
            if cancel:
                st.session_state.show_add_drug = False
                st.rerun()
            
            if submit:
                if not new_drug_name.strip():
                    st.error("Drug Name is required")
                elif not new_condition.strip():
                    st.error("Condition is required")
                elif not new_category.strip():
                    st.error("Category is required")
                else:
                    # Check for duplicate drug name - read raw CSV
                    drugs_df = pd.read_csv('drugs.csv')
                    if new_drug_name.strip().lower() in drugs_df['drug'].str.lower().values:
                        st.error(f"Drug '{new_drug_name.strip()}' already exists")
                    else:
                        # Sanitize inputs
                        from validation import sanitize_string
                        
                        # Process replacements (textarea to semicolon-separated)
                        replacements_list = [r.strip() for r in new_replacements.split('\n') if r.strip()]
                        replacements_str = ';'.join(replacements_list) if replacements_list else ''
                        
                        new_drug = {
                            'drug': sanitize_string(new_drug_name.strip()),
                            'condition': sanitize_string(new_condition.strip()),
                            'category': sanitize_string(new_category.strip()),
                            'replacements': replacements_str if replacements_str else ''
                        }
                        
                        # Add to CSV
                        drugs_df = pd.concat([drugs_df, pd.DataFrame([new_drug])], ignore_index=True)
                        drugs_df.to_csv('drugs.csv', index=False)
                        
                        st.success(f"Drug '{new_drug_name}' added successfully!")
                        time.sleep(2)
                        st.session_state.show_add_drug = False
                        st.rerun()
        
        st.divider()
    
    # Edit Drug Form
    if st.session_state.get('show_edit_drug', False):
        # Read raw CSV to keep replacements as strings
        drugs_df_raw = pd.read_csv('drugs.csv')
        
        if len(drugs_df_raw) == 0:
            st.warning("No drugs available to edit")
            st.session_state.show_edit_drug = False
        else:
            drug_options = {row['drug']: row for _, row in drugs_df_raw.iterrows()}
            selected = st.selectbox("Select Drug to Edit:", list(drug_options.keys()))
            
            if selected:
                drug = drug_options[selected]
                
                with st.form("edit_drug_form"):
                    st.subheader(f"✏️ Edit Drug: {drug['drug']}")
                    
                    original_name = st.text_input("Original Drug Name", value=drug['drug'], disabled=True,
                                                  help="Reference - cannot be changed")
                    edit_drug_name = st.text_input("Drug Name*", value=drug['drug'])
                    edit_condition = st.text_input("Condition*", value=drug['condition'])
                    edit_category = st.text_input("Category*", value=drug.get('category', ''))
                    
                    # Convert semicolon-separated string to newline-separated for textarea
                    replacements = drug.get('replacements', '')
                    if pd.isna(replacements) or replacements == '' or str(replacements).lower() == 'nan':
                        replacements_display = ''
                    else:
                        replacements_display = str(replacements).replace(';', '\n')
                    
                    edit_replacements = st.text_area("Replacements (one per line)", 
                                                      value=replacements_display,
                                                      help="Optional: List alternative drugs, one per line")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        save = st.form_submit_button("Save Changes", type="primary")
                    with col2:
                        cancel = st.form_submit_button("Cancel")
                    with col3:
                        if has_permission(Permission.DELETE_DRUG):
                            # Check if delete confirmation is pending
                            if st.session_state.get('confirm_delete_drug') == drug['drug']:
                                confirm_delete = st.form_submit_button("⚠️ CONFIRM DELETE", type="secondary")
                            else:
                                delete = st.form_submit_button("🗑️ Delete", type="secondary")
                                confirm_delete = False
                        else:
                            delete = False
                            confirm_delete = False
                    
                    if cancel:
                        # Clear any pending delete confirmation
                        if 'confirm_delete_drug' in st.session_state:
                            del st.session_state.confirm_delete_drug
                        st.session_state.show_edit_drug = False
                        st.rerun()
                    
                    # Handle delete button click - show confirmation
                    if 'delete' in locals() and delete and has_permission(Permission.DELETE_DRUG):
                        st.session_state.confirm_delete_drug = drug['drug']
                        st.warning(f"⚠️ You are about to delete drug '{drug['drug']}'. This may affect conflict detection rules! Click 'CONFIRM DELETE' to proceed.")
                        time.sleep(2)
                        st.rerun()
                    
                    # Handle confirm delete button click - actually delete
                    if 'confirm_delete' in locals() and confirm_delete and has_permission(Permission.DELETE_DRUG):
                        # Delete drug
                        drugs_df_raw = pd.read_csv('drugs.csv')
                        drugs_df_raw = drugs_df_raw[drugs_df_raw['drug'] != drug['drug']]
                        drugs_df_raw.to_csv('drugs.csv', index=False)
                        
                        # Clear confirmation state
                        if 'confirm_delete_drug' in st.session_state:
                            del st.session_state.confirm_delete_drug
                        
                        st.success(f"✅ Drug '{drug['drug']}' has been permanently deleted.")
                        time.sleep(2)
                        st.session_state.show_edit_drug = False
                        st.rerun()
                    
                    if save:
                        if not edit_drug_name.strip():
                            st.error("Drug Name is required")
                        elif not edit_condition.strip():
                            st.error("Condition is required")
                        elif not edit_category.strip():
                            st.error("Category is required")
                        else:
                            # Sanitize inputs
                            from validation import sanitize_string
                            
                            # Process replacements
                            replacements_list = [r.strip() for r in edit_replacements.split('\n') if r.strip()]
                            replacements_str = ';'.join(replacements_list) if replacements_list else ''
                            
                            # Update drug in raw CSV
                            drugs_df_raw = pd.read_csv('drugs.csv')
                            mask = drugs_df_raw['drug'] == drug['drug']
                            drugs_df_raw.loc[mask, 'drug'] = sanitize_string(edit_drug_name.strip())
                            drugs_df_raw.loc[mask, 'condition'] = sanitize_string(edit_condition.strip())
                            drugs_df_raw.loc[mask, 'category'] = sanitize_string(edit_category.strip())
                            drugs_df_raw.loc[mask, 'replacements'] = replacements_str if replacements_str else ''
                            drugs_df_raw.to_csv('drugs.csv', index=False)
                            
                            st.success(f"Drug '{edit_drug_name}' updated successfully!")
                            time.sleep(2)
                            st.session_state.show_edit_drug = False
                            st.rerun()
        
        st.divider()
    
    _, drugs_data, _ = load_data()
    
    # Search
    search_term = st.text_input("🔍 Search drugs by name, condition, or category:", "")
    
    drugs_df = pd.DataFrame(drugs_data)
    
    if search_term:
        drugs_df = drugs_df[
            drugs_df.apply(lambda row: search_term.lower() in str(row).lower(), axis=1)
        ]
    
    st.dataframe(drugs_df, use_container_width=True, height=400)
    
    st.divider()
    
    # Drug details
    st.subheader("Drug Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**By Category:**")
        category_counts = drugs_df['category'].value_counts()
        for cat, count in category_counts.items():
            st.markdown(f"- {cat}: {count} drug(s)")
    
    with col2:
        st.write("**By Condition:**")
        condition_counts = drugs_df['condition'].value_counts()
        for cond, count in condition_counts.items():
            st.markdown(f"- {cond}: {count} drug(s)")

# ============= RULES ENGINE PAGE =============
elif page == "Rules Engine":
    st.header("⚙️ Conflict Detection Rules")
    
    # CRUD buttons (Admin only)
    if has_permission(Permission.ADD_RULE):
        col1, col2, _ = st.columns([1, 1, 6])
        with col1:
            if st.button("➕ Add Rule", type="primary"):
                st.session_state.show_add_rule = True
                st.session_state.show_edit_rule = False
                st.rerun()
        with col2:
            if st.button("✏️ Edit Rule"):
                st.session_state.show_edit_rule = True
                st.session_state.show_add_rule = False
                st.rerun()
        
        st.divider()
    
    # Add Rule Form
    if st.session_state.get('show_add_rule', False):
        with st.form("add_rule_form", clear_on_submit=True):
            st.subheader("➕ Add New Rule")
            
            col1, col2 = st.columns(2)
            with col1:
                new_type = st.selectbox("Type*", ["drug-drug", "drug-condition"], index=0)
            with col2:
                new_severity = st.selectbox("Severity*", ["Minor", "Moderate", "Major"], index=1)
            
            new_item_a = st.text_input("Item A*", placeholder="e.g., Aspirin (drug name)")
            new_item_b = st.text_input("Item B*", placeholder="e.g., Warfarin (drug name) or Bleeding Disorder (condition)")
            new_recommendation = st.text_area("Recommendation*", 
                                              placeholder="e.g., Avoid combination. Consider alternative pain management.",
                                              help="Describe the recommended action")
            new_notes = st.text_area("Notes", 
                                     placeholder="Additional information about the conflict (optional)",
                                     help="Optional: Any additional context or information")
            
            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("Add Rule", type="primary")
            with col2:
                cancel = st.form_submit_button("Cancel")
            
            if cancel:
                st.session_state.show_add_rule = False
                st.rerun()
            
            if submit:
                if not new_item_a.strip():
                    st.error("Item A is required")
                elif not new_item_b.strip():
                    st.error("Item B is required")
                elif not new_recommendation.strip():
                    st.error("Recommendation is required")
                else:
                    # Check for duplicate rule
                    _, _, rules_data = load_data()
                    if any(r['type'] == new_type and r['item_a'].lower() == new_item_a.strip().lower() and r['item_b'].lower() == new_item_b.strip().lower() for r in rules_data):
                        st.error(f"Rule for '{new_item_a}' and '{new_item_b}' already exists")
                    else:
                        # Sanitize inputs
                        from validation import sanitize_string
                        
                        new_rule = {
                            'type': new_type,
                            'item_a': sanitize_string(new_item_a.strip()),
                            'item_b': sanitize_string(new_item_b.strip()),
                            'severity': new_severity,
                            'recommendation': sanitize_string(new_recommendation.strip()),
                            'notes': sanitize_string(new_notes.strip()) if new_notes.strip() else ''
                        }
                        
                        # Add to CSV
                        rules_df = pd.DataFrame(rules_data)
                        rules_df = pd.concat([rules_df, pd.DataFrame([new_rule])], ignore_index=True)
                        rules_df.to_csv('rules.csv', index=False)
                        
                        st.success(f"Rule for '{new_item_a}' & '{new_item_b}' added successfully!")
                        time.sleep(2)
                        st.session_state.show_add_rule = False
                        st.rerun()
        
        st.divider()
    
    # Edit Rule Form
    if st.session_state.get('show_edit_rule', False):
        _, _, rules_data = load_data()
        
        if len(rules_data) == 0:
            st.warning("No rules available to edit")
            st.session_state.show_edit_rule = False
        else:
            rule_options = {f"{r['type']}: {r['item_a']} & {r['item_b']} ({r['severity']})": r for r in rules_data}
            selected = st.selectbox("Select Rule to Edit:", list(rule_options.keys()))
            
            if selected:
                rule = rule_options[selected]
                
                with st.form("edit_rule_form"):
                    st.subheader(f"✏️ Edit Rule: {rule['item_a']} & {rule['item_b']}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        type_index = 0 if rule['type'] == 'drug-drug' else 1
                        edit_type = st.selectbox("Type*", ["drug-drug", "drug-condition"], index=type_index)
                    with col2:
                        severity_options = ["Minor", "Moderate", "Major"]
                        severity_index = severity_options.index(rule['severity']) if rule['severity'] in severity_options else 1
                        edit_severity = st.selectbox("Severity*", severity_options, index=severity_index)
                    
                    edit_item_a = st.text_input("Item A*", value=rule['item_a'])
                    edit_item_b = st.text_input("Item B*", value=rule['item_b'])
                    edit_recommendation = st.text_area("Recommendation*", value=rule['recommendation'])
                    edit_notes = st.text_area("Notes", value=rule.get('notes', ''))
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        save = st.form_submit_button("Save Changes", type="primary")
                    with col2:
                        cancel = st.form_submit_button("Cancel")
                    with col3:
                        if has_permission(Permission.DELETE_RULE):
                            # Check if delete confirmation is pending
                            rule_key = f"{rule['type']}_{rule['item_a']}_{rule['item_b']}"
                            if st.session_state.get('confirm_delete_rule') == rule_key:
                                confirm_delete = st.form_submit_button("⚠️ CONFIRM DELETE", type="secondary")
                            else:
                                delete = st.form_submit_button("🗑️ Delete", type="secondary")
                                confirm_delete = False
                        else:
                            delete = False
                            confirm_delete = False
                    
                    if cancel:
                        # Clear any pending delete confirmation
                        if 'confirm_delete_rule' in st.session_state:
                            del st.session_state.confirm_delete_rule
                        st.session_state.show_edit_rule = False
                        st.rerun()
                    
                    # Handle delete button click - show confirmation
                    if 'delete' in locals() and delete and has_permission(Permission.DELETE_RULE):
                        rule_key = f"{rule['type']}_{rule['item_a']}_{rule['item_b']}"
                        st.session_state.confirm_delete_rule = rule_key
                        st.warning(f"⚠️ You are about to delete the conflict rule between '{rule['item_a']}' and '{rule['item_b']}'. This will affect conflict detection! Click 'CONFIRM DELETE' to proceed.")
                        time.sleep(2)
                        st.rerun()
                    
                    # Handle confirm delete button click - actually delete
                    if 'confirm_delete' in locals() and confirm_delete and has_permission(Permission.DELETE_RULE):
                        # Delete rule
                        rules_df = pd.DataFrame(rules_data)
                        # Remove the rule by matching type, item_a, and item_b
                        mask = (rules_df['type'] == rule['type']) & (rules_df['item_a'] == rule['item_a']) & (rules_df['item_b'] == rule['item_b'])
                        rules_df = rules_df[~mask]
                        rules_df.to_csv('rules.csv', index=False)
                        
                        # Clear confirmation state
                        if 'confirm_delete_rule' in st.session_state:
                            del st.session_state.confirm_delete_rule
                        
                        st.success(f"✅ Rule for '{rule['item_a']}' & '{rule['item_b']}' has been permanently deleted.")
                        time.sleep(2)
                        st.session_state.show_edit_rule = False
                        st.rerun()
                    
                    if save:
                        if not edit_item_a.strip():
                            st.error("Item A is required")
                        elif not edit_item_b.strip():
                            st.error("Item B is required")
                        elif not edit_recommendation.strip():
                            st.error("Recommendation is required")
                        else:
                            # Sanitize inputs
                            from validation import sanitize_string
                            
                            # Update rule
                            rules_df = pd.DataFrame(rules_data)
                            # Find the rule by matching original type, item_a, and item_b
                            mask = (rules_df['type'] == rule['type']) & (rules_df['item_a'] == rule['item_a']) & (rules_df['item_b'] == rule['item_b'])
                            rules_df.loc[mask, 'type'] = edit_type
                            rules_df.loc[mask, 'item_a'] = sanitize_string(edit_item_a.strip())
                            rules_df.loc[mask, 'item_b'] = sanitize_string(edit_item_b.strip())
                            rules_df.loc[mask, 'severity'] = edit_severity
                            rules_df.loc[mask, 'recommendation'] = sanitize_string(edit_recommendation.strip())
                            rules_df.loc[mask, 'notes'] = sanitize_string(edit_notes.strip()) if edit_notes.strip() else ''
                            rules_df.to_csv('rules.csv', index=False)
                            
                            st.success(f"Rule '{edit_item_a} & {edit_item_b}' updated successfully!")
                            time.sleep(2)
                            st.session_state.show_edit_rule = False
                            st.rerun()
        
        st.divider()
    
    _, _, rules_data = load_data()
    
    rules_df = pd.DataFrame(rules_data)
    
    # Convert all columns to strings to avoid Arrow serialization issues
    for col in rules_df.columns:
        rules_df[col] = rules_df[col].astype(str)
    
    # Search
    search_term = st.text_input("🔍 Search rules:", "")
    
    if search_term:
        rules_df = rules_df[
            rules_df.apply(lambda row: search_term.lower() in str(row).lower(), axis=1)
        ]
    
    st.dataframe(rules_df, use_container_width=True, height=400)
    
    st.divider()
    
    # Rule statistics
    if st.session_state.conflicts_df is not None and len(st.session_state.conflicts_df) > 0:
        st.subheader("📊 Rule Trigger Statistics")
        
        conflicts_df = st.session_state.conflicts_df
        
        # Count how many times each rule was triggered
        rule_triggers = {}
        for _, conflict in conflicts_df.iterrows():
            key = f"{conflict['item_a']} - {conflict['item_b']}"
            rule_triggers[key] = rule_triggers.get(key, 0) + 1
        
        if rule_triggers:
            # Sort by trigger count
            sorted_triggers = dict(sorted(rule_triggers.items(), key=lambda x: x[1], reverse=True)[:10])
            
            fig = px.bar(
                x=list(sorted_triggers.values()),
                y=list(sorted_triggers.keys()),
                orientation='h',
                title="Top 10 Most Frequently Triggered Rules",
                labels={'x': 'Trigger Count', 'y': 'Drug Interaction'},
                color=list(sorted_triggers.values()),
                color_continuous_scale='Reds',
                text=list(sorted_triggers.values())
            )
            fig.update_traces(
                textposition='outside',
                hovertemplate='<b>%{y}</b><br>Triggered: %{x} times<extra></extra>'
            )
            fig.update_layout(
                yaxis={'categoryorder':'total ascending'},
                showlegend=False,
                height=max(400, len(sorted_triggers) * 40)
            )
            st.plotly_chart(fig, use_container_width=True)

# ============= MANUAL TESTING PAGE =============
elif page == "Manual Testing":
    st.header("🧪 Manual Prescription Testing")
    
    st.write("Test drug combinations for a patient manually. Conflicts are detected in real-time as you select drugs.")
    
    _, drugs_data, _ = load_data()
    
    # Initialize session state for real-time testing
    if 'rt_conditions' not in st.session_state:
        st.session_state.rt_conditions = []
    if 'rt_allergies' not in st.session_state:
        st.session_state.rt_allergies = ["None"]
    if 'rt_drugs' not in st.session_state:
        st.session_state.rt_drugs = []
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Patient Information")
        
        patient_name = st.text_input("Patient Name:", "Test Patient")
        
        all_conditions = ["Hypertension", "Diabetes", "Infection", "Pain", "Anticoagulation", "Heart Failure", "GERD"]
        selected_conditions = st.multiselect("Select Conditions:", all_conditions, key="manual_conditions")
        
        all_allergies = ["Penicillin", "Aspirin", "Ibuprofen", "Sulfa"]
        selected_allergies = st.multiselect("Select Allergies:", all_allergies, key="manual_allergies")
    
    with col2:
        st.subheader("Prescription")
        
        drug_names = sorted([drug['drug'] for drug in drugs_data])
        selected_drugs = st.multiselect("Select Drugs:", drug_names, key="manual_drugs", 
                                       help="Conflicts are checked automatically as you select drugs",
                                       max_selections=15)
        
        if len(selected_drugs) > 10:
            st.info("💡 Large prescriptions may take a moment to analyze. Results are cached for better performance.")
    
    st.divider()
    
    # Real-time conflict checking with caching
    if selected_drugs:
        with st.spinner("🔍 Analyzing prescription..." if len(selected_drugs) > 5 else None):
            # Build KB once and cache it
            if st.session_state.cached_kb is None:
                base_dir = Path(__file__).parent
                rules = load_rules(base_dir / "rules.csv")
                st.session_state.cached_kb = build_rules_kb(rules)
            
            # Use optimized cached conflict detection
            from utils import make_condition_tokens
            conditions_tokens = make_condition_tokens(
                selected_conditions,
                selected_allergies if selected_allergies else []
            )
            
            conflicts_list = get_conflicts_cached(
                selected_drugs,
                conditions_tokens,
                st.session_state.cached_kb
            )
            
            # Convert Conflict objects to dicts for display
            conflicts = [
                {
                    'type': c.rtype,
                    'item_a': c.item_a,
                    'item_b': c.item_b,
                    'severity': c.severity,
                    'recommendation': c.recommendation,
                    'score': c.score
                }
                for c in conflicts_list
            ]
        
        # Display real-time results
        st.subheader("🔍 Real-Time Conflict Analysis")
        
        # Summary metrics
        col_a, col_b, col_c, col_d = st.columns(4)
        
        with col_a:
            st.metric("Drugs Selected", len(selected_drugs))
        
        with col_b:
            if conflicts:
                st.metric("Conflicts Found", len(conflicts), delta=f"-{len(conflicts)}", delta_color="inverse")
            else:
                st.metric("Conflicts Found", 0, delta="✓ Safe", delta_color="normal")
        
        with col_c:
            major_count = sum(1 for c in conflicts if c['severity'] == 'Major')
            if major_count > 0:
                st.metric("Major", major_count, delta="Critical", delta_color="inverse")
            else:
                st.metric("Major", 0)
        
        with col_d:
            moderate_count = sum(1 for c in conflicts if c['severity'] == 'Moderate')
            if moderate_count > 0:
                st.metric("Moderate", moderate_count, delta="Warning", delta_color="inverse")
            else:
                st.metric("Moderate", 0)
        
        st.divider()
        
        # Display conflicts with color coding
        if conflicts:
            st.error(f"⚠️ {len(conflicts)} conflict(s) detected in current prescription!")
            
            # Sort conflicts by severity
            severity_order = {'Major': 3, 'Moderate': 2, 'Minor': 1}
            conflicts.sort(key=lambda x: severity_order.get(x['severity'], 0), reverse=True)
            
            for conflict in conflicts:
                severity_class = f"conflict-{conflict['severity'].lower()}"
                
                # Color-coded emoji based on severity
                severity_emoji = {
                    'Major': '🔴',
                    'Moderate': '🟡',
                    'Minor': '🟢'
                }
                
                with st.container():
                    st.markdown(f'<div class="{severity_class}">', unsafe_allow_html=True)
                    
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"### {severity_emoji.get(conflict['severity'], '⚠️')} {conflict['severity']} Severity")
                        st.write(f"**Type:** {conflict['type']}")
                        st.write(f"**Conflict:** {conflict['item_a']} ↔️ {conflict['item_b']}")
                        st.write(f"**Recommendation:** {conflict['recommendation']}")
                    
                    with col2:
                        st.metric("Risk Score", conflict['score'])
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    st.write("")  # Spacing
        else:
            st.success("✅ No conflicts detected! This prescription is safe for the patient.")
            
            # Show safe prescription summary
            with st.expander("📋 Prescription Summary", expanded=True):
                st.write(f"**Patient:** {patient_name}")
                st.write(f"**Conditions:** {', '.join(selected_conditions) if selected_conditions else 'None'}")
                st.write(f"**Allergies:** {', '.join(selected_allergies) if selected_allergies else 'None'}")
                st.write(f"**Prescribed Drugs:**")
                for drug in selected_drugs:
                    st.markdown(f"- 💊 {drug}")
        
        # Export Report Section
        st.divider()
        st.subheader("📄 Export Report")
        
        col_exp1, col_exp2 = st.columns(2)
        
        with col_exp1:
            if st.button("📕 Download PDF Report", use_container_width=True):
                try:
                    from report_generator import ReportGenerator
                    
                    generator = ReportGenerator()
                    pdf_bytes = generator.generate_report_bytes(
                        format_type='pdf',
                        patient_name=patient_name,
                        patient_id=f"TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        conditions=selected_conditions if selected_conditions else [],
                        allergies=selected_allergies if selected_allergies else [],
                        prescription=selected_drugs,
                        conflicts=conflicts
                    )
                    
                    filename = f"conflict_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    st.download_button(
                        label="💾 Save PDF",
                        data=pdf_bytes,
                        file_name=filename,
                        mime="application/pdf",
                        use_container_width=True
                    )
                    st.success("✅ PDF report generated!")
                    
                except ImportError:
                    st.error("📦 Please install reportlab: `pip install reportlab`")
                except Exception as e:
                    st.error(f"❌ Error generating PDF: {str(e)}")
        
        with col_exp2:
            if st.button("📘 Download Word Report", use_container_width=True):
                try:
                    from report_generator import ReportGenerator
                    
                    generator = ReportGenerator()
                    word_bytes = generator.generate_report_bytes(
                        format_type='word',
                        patient_name=patient_name,
                        patient_id=f"TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        conditions=selected_conditions if selected_conditions else [],
                        allergies=selected_allergies if selected_allergies else [],
                        prescription=selected_drugs,
                        conflicts=conflicts
                    )
                    
                    filename = f"conflict_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
                    st.download_button(
                        label="💾 Save Word",
                        data=word_bytes,
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True
                    )
                    st.success("✅ Word report generated!")
                    
                except ImportError:
                    st.error("📦 Please install python-docx: `pip install python-docx`")
                except Exception as e:
                    st.error(f"❌ Error generating Word report: {str(e)}")
    else:
        st.info("👆 Select drugs above to begin real-time conflict checking")

# ============= IMPORT DATA PAGE =============
elif page == "Import Data":
    st.header("📁 Import Custom Data")
    
    st.write("""
    Upload your own CSV files to customize the database. The files should follow the same format as the default files.
    After uploading, run the simulation to see results with your custom data.
    """)
    
    st.divider()
    
    # Create tabs for different file types
    tab1, tab2, tab3 = st.tabs(["📋 Patients", "💊 Drugs", "⚙️ Rules"])
    
    with tab1:
        st.subheader("Upload Patients Database")
        
        st.write("**Required columns:** `id`, `name`, `conditions`, `allergies`")
        st.write("**Format:** Use semicolons (;) to separate multiple conditions or allergies")
        
        st.code("""id,name,conditions,allergies
1,John Doe,Hypertension;Diabetes,Penicillin
            2,Jane Smith,Infection,None""", language="csv")
        
        patients_file = st.file_uploader("Choose patients CSV file", type=['csv'], key="patients_upload")
        
        if patients_file is not None:
            # Show preview
            preview_df = pd.read_csv(patients_file)
            st.write("**Preview:**")
            st.dataframe(preview_df.head(), use_container_width=True)
            
            # Reset file pointer
            patients_file.seek(0)
            
            if st.button("✅ Upload Patients Data", key="upload_patients_btn"):
                success, message = save_uploaded_file(patients_file, "patients")
                if success:
                    st.success(message)
                    st.session_state.simulation_run = False  # Reset simulation
                else:
                    st.error(message)
        
        # Show current status
        if st.session_state.custom_patients is not None:
            st.info(f"✓ Custom patients data loaded ({len(st.session_state.custom_patients)} patients)")
        else:
            st.info("Using default patients database")
        
        # Reset button
        if st.session_state.custom_patients is not None:
            if st.button("🔄 Reset to Default", key="reset_patients"):
                st.session_state.custom_patients = None
                st.session_state.simulation_run = False
                st.success("Reset to default patients data")
                st.rerun()
    
    with tab2:
        st.subheader("Upload Drugs Database")
        
        st.write("**Required columns:** `drug`, `condition`, `category`, `replacements`")
        
        st.code("""drug,condition,category,replacements
Lisinopril,Hypertension,ACE Inhibitor,Losartan
Metformin,Diabetes,Biguanide,Glipizide""", language="csv")
        
        drugs_file = st.file_uploader("Choose drugs CSV file", type=['csv'], key="drugs_upload")
        
        if drugs_file is not None:
            # Show preview
            preview_df = pd.read_csv(drugs_file)
            st.write("**Preview:**")
            st.dataframe(preview_df.head(), use_container_width=True)
            
            # Reset file pointer
            drugs_file.seek(0)
            
            if st.button("✅ Upload Drugs Data", key="upload_drugs_btn"):
                success, message = save_uploaded_file(drugs_file, "drugs")
                if success:
                    st.success(message)
                    st.session_state.simulation_run = False
                else:
                    st.error(message)
        
        # Show current status
        if st.session_state.custom_drugs is not None:
            st.info(f"✓ Custom drugs data loaded ({len(st.session_state.custom_drugs)} drugs)")
        else:
            st.info("Using default drugs database")
        
        # Reset button
        if st.session_state.custom_drugs is not None:
            if st.button("🔄 Reset to Default", key="reset_drugs"):
                st.session_state.custom_drugs = None
                st.session_state.simulation_run = False
                st.success("Reset to default drugs data")
                st.rerun()
    
    with tab3:
        st.subheader("Upload Rules Database")
        
        st.write("**Required columns:** `type`, `item_a`, `item_b`, `severity`, `recommendation`, `notes`")
        
        st.code("""type,item_a,item_b,severity,recommendation,notes
drug-drug,Aspirin,Warfarin,Major,Avoid combination,Bleeding risk
drug-condition,Hypertension,Ibuprofen,Moderate,Prefer Paracetamol,May raise BP""", language="csv")
        
        rules_file = st.file_uploader("Choose rules CSV file", type=['csv'], key="rules_upload")
        
        if rules_file is not None:
            # Show preview
            preview_df = pd.read_csv(rules_file)
            st.write("**Preview:**")
            st.dataframe(preview_df.head(), use_container_width=True)
            
            # Reset file pointer
            rules_file.seek(0)
            
            if st.button("✅ Upload Rules Data", key="upload_rules_btn"):
                success, message = save_uploaded_file(rules_file, "rules")
                if success:
                    st.success(message)
                    st.session_state.simulation_run = False
                else:
                    st.error(message)
        
        # Show current status
        if st.session_state.custom_rules is not None:
            st.info(f"✓ Custom rules data loaded ({len(st.session_state.custom_rules)} rules)")
        else:
            st.info("Using default rules database")
        
        # Reset button
        if st.session_state.custom_rules is not None:
            if st.button("🔄 Reset to Default", key="reset_rules"):
                st.session_state.custom_rules = None
                st.session_state.simulation_run = False
                st.success("Reset to default rules data")
                st.rerun()
    
    st.divider()
    
    # Download templates
    st.subheader("📥 Download Templates")
    st.write("Download the current database files as templates for your custom data:")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        patients_data, _, _ = load_data()
        patients_df = pd.DataFrame(patients_data)
        if not patients_df.empty and 'conditions' in patients_df.columns:
            patients_df['conditions'] = patients_df['conditions'].apply(
                lambda x: ';'.join(x) if isinstance(x, list) else x
            )
        if not patients_df.empty and 'allergies' in patients_df.columns:
            patients_df['allergies'] = patients_df['allergies'].apply(
                lambda x: ';'.join(x) if isinstance(x, list) else x
            )
        st.download_button(
            label="📋 Download Patients Template",
            data=patients_df.to_csv(index=False),
            file_name="patients_template.csv",
            mime="text/csv"
        )
    
    with col2:
        _, drugs_data, _ = load_data()
        drugs_df = pd.DataFrame(drugs_data)
        st.download_button(
            label="💊 Download Drugs Template",
            data=drugs_df.to_csv(index=False),
            file_name="drugs_template.csv",
            mime="text/csv"
        )
    
    with col3:
        _, _, rules_data = load_data()
        rules_df = pd.DataFrame(rules_data)
        st.download_button(
            label="⚙️ Download Rules Template",
            data=rules_df.to_csv(index=False),
            file_name="rules_template.csv",
            mime="text/csv"
        )
    
    st.divider()
    
    # Reset all
    if st.session_state.custom_data_uploaded:
        st.subheader("🔄 Reset All Data")
        if st.button("⚠️ Reset All to Default", type="secondary"):
            st.session_state.custom_patients = None
            st.session_state.custom_drugs = None
            st.session_state.custom_rules = None
            st.session_state.custom_data_uploaded = False
            st.session_state.simulation_run = False
            st.success("All data reset to defaults!")
            st.rerun()

# ============= USER MANAGEMENT PAGE (Admin Only) =============
elif page == "User Management":
    require_permission(Permission.MANAGE_USERS)
    
    st.header("👥 User Management")
    st.markdown("Manage user accounts and permissions")
    
    from auth import get_all_users, add_user, delete_user, change_password
    from validation import validate_password_strength
    
    tabs = st.tabs(["User List", "Add New User", "Change Password"])
    
    # Tab 1: User List
    with tabs[0]:
        st.subheader("Current Users")
        
        users = get_all_users()
        if users:
            users_df = pd.DataFrame(users)
            
            st.dataframe(
                users_df,
                use_container_width=True,
                hide_index=True
            )
            
            st.info(f"Total Users: {len(users)}")
            
            # Delete user
            st.divider()
            st.subheader("Delete User")
            
            usernames = [u['username'] for u in users if u['username'] != user.username]
            
            if usernames:
                user_to_delete = st.selectbox("Select user to delete:", usernames)
                
                if st.button("🗑️ Delete User", type="secondary"):
                    success, error_msg = delete_user(user_to_delete)
                    if success:
                        st.success(f"User '{user_to_delete}' deleted successfully!")
                        st.rerun()
                    else:
                        st.error(f"Error: {error_msg}")
            else:
                st.warning("No other users to delete")
        else:
            st.warning("No users found")
    
    # Tab 2: Add New User
    with tabs[1]:
        st.subheader("Add New User")
        
        with st.form("add_user_form"):
            new_username = st.text_input("Username", placeholder="Enter username (alphanumeric only)")
            new_password = st.text_input("Password", type="password", placeholder="Enter password")
            new_role = st.selectbox("Role", ["Admin", "Doctor", "Pharmacist"])
            new_email = st.text_input("Email (optional)", placeholder="user@example.com")
            
            submit = st.form_submit_button("Add User", type="primary")
            
            if submit:
                if not new_username or not new_password:
                    st.error("Username and password are required")
                else:
                    # Validate password strength
                    is_strong, pwd_errors = validate_password_strength(new_password)
                    
                    if not is_strong:
                        st.error("Password does not meet requirements:")
                        for err in pwd_errors:
                            st.error(f"  - {err}")
                    else:
                        success, error_msg = add_user(new_username, new_password, new_role, new_email)
                        
                        if success:
                            st.success(f"User '{new_username}' added successfully!")
                            st.rerun()
                        else:
                            st.error(f"Error: {error_msg}")
        
        st.info("""
        **Password Requirements:**
        - At least 8 characters long
        - Contains uppercase and lowercase letters
        - Contains at least one digit
        - Contains at least one special character
        """)
    
    # Tab 3: Change Password
    with tabs[2]:
        st.subheader("Change Password")
        
        with st.form("change_password_form"):
            old_password = st.text_input("Current Password", type="password")
            new_password1 = st.text_input("New Password", type="password")
            new_password2 = st.text_input("Confirm New Password", type="password")
            
            submit = st.form_submit_button("Change Password", type="primary")
            
            if submit:
                if not old_password or not new_password1 or not new_password2:
                    st.error("All fields are required")
                elif new_password1 != new_password2:
                    st.error("New passwords do not match")
                else:
                    # Validate password strength
                    is_strong, pwd_errors = validate_password_strength(new_password1)
                    
                    if not is_strong:
                        st.error("Password does not meet requirements:")
                        for err in pwd_errors:
                            st.error(f"  - {err}")
                    else:
                        success, error_msg = change_password(user.username, old_password, new_password1)
                        
                        if success:
                            st.success("Password changed successfully!")
                        else:
                            st.error(f"Error: {error_msg}")

# Footer
st.divider()
st.markdown("""
    <div style='text-align: center; color: #666; padding: 1rem;'>
        <p>Drug Conflict Detection System | Powered by Mesa & Streamlit</p>
    </div>
""", unsafe_allow_html=True)
