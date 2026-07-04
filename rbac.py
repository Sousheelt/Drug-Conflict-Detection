"""
Role-Based Access Control (RBAC) Module

Defines roles, permissions, and access control for the drug conflict detection system:
- Role definitions (Admin, Doctor, Pharmacist, Viewer)
- Permission checking for pages and actions
- Access control decorators
- Role hierarchy and capabilities
"""

from typing import List, Dict, Set, Optional
from enum import Enum
import streamlit as st


class Role(Enum):
    """User roles in the system"""
    ADMIN = "Admin"
    DOCTOR = "Doctor"
    PHARMACIST = "Pharmacist"


class Permission(Enum):
    """System permissions"""
    # Page access
    VIEW_DASHBOARD = "view_dashboard"
    VIEW_PATIENTS = "view_patients"
    VIEW_DRUGS = "view_drugs"
    VIEW_RULES = "view_rules"
    VIEW_CONFLICTS = "view_conflicts"
    VIEW_REPORTS = "view_reports"
    VIEW_SIMULATION = "view_simulation"
    VIEW_ANALYTICS = "view_analytics"
    
    # Data operations
    ADD_PATIENT = "add_patient"
    EDIT_PATIENT = "edit_patient"
    DELETE_PATIENT = "delete_patient"
    
    ADD_DRUG = "add_drug"
    EDIT_DRUG = "edit_drug"
    DELETE_DRUG = "delete_drug"
    
    ADD_RULE = "add_rule"
    EDIT_RULE = "edit_rule"
    DELETE_RULE = "delete_rule"
    
    # Action permissions
    RUN_SIMULATION = "run_simulation"
    PRESCRIBE_DRUGS = "prescribe_drugs"
    GENERATE_REPORT = "generate_report"
    EXPORT_DATA = "export_data"
    IMPORT_DATA = "import_data"
    
    # Admin permissions
    MANAGE_USERS = "manage_users"
    CHANGE_SETTINGS = "change_settings"
    VIEW_AUDIT_LOG = "view_audit_log"


# Role-Permission Mapping
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.ADMIN: {
        # Full access to everything
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_PATIENTS,
        Permission.VIEW_DRUGS,
        Permission.VIEW_RULES,
        Permission.VIEW_CONFLICTS,
        Permission.VIEW_REPORTS,
        Permission.VIEW_SIMULATION,
        Permission.VIEW_ANALYTICS,
        
        Permission.ADD_PATIENT,
        Permission.EDIT_PATIENT,
        Permission.DELETE_PATIENT,
        
        Permission.ADD_DRUG,
        Permission.EDIT_DRUG,
        Permission.DELETE_DRUG,
        
        Permission.ADD_RULE,
        Permission.EDIT_RULE,
        Permission.DELETE_RULE,
        
        Permission.RUN_SIMULATION,
        Permission.PRESCRIBE_DRUGS,
        Permission.GENERATE_REPORT,
        Permission.EXPORT_DATA,
        Permission.IMPORT_DATA,
        
        Permission.MANAGE_USERS,
        Permission.CHANGE_SETTINGS,
        Permission.VIEW_AUDIT_LOG,
    },
    
    Role.DOCTOR: {
        # Medical professional with prescription rights
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_PATIENTS,
        Permission.VIEW_DRUGS,
        Permission.VIEW_RULES,
        Permission.VIEW_CONFLICTS,
        Permission.VIEW_REPORTS,
        Permission.VIEW_SIMULATION,
        Permission.VIEW_ANALYTICS,
        
        Permission.ADD_PATIENT,
        Permission.EDIT_PATIENT,
        
        Permission.RUN_SIMULATION,
        Permission.PRESCRIBE_DRUGS,
        Permission.GENERATE_REPORT,
        Permission.EXPORT_DATA,
    },
    
    Role.PHARMACIST: {
        # Pharmacist with drug database management rights
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_PATIENTS,
        Permission.VIEW_DRUGS,
        Permission.VIEW_RULES,
        Permission.VIEW_CONFLICTS,
        Permission.VIEW_REPORTS,
        Permission.VIEW_ANALYTICS,
        
        Permission.ADD_DRUG,
        Permission.EDIT_DRUG,
        Permission.DELETE_DRUG,
        
        Permission.RUN_SIMULATION,
        Permission.GENERATE_REPORT,
        Permission.EXPORT_DATA,
    }
}


# Page-Permission Mapping
PAGE_PERMISSIONS: Dict[str, Permission] = {
    "Dashboard": Permission.VIEW_DASHBOARD,
    "Patients": Permission.VIEW_PATIENTS,
    "Prescription Simulator": Permission.PRESCRIBE_DRUGS,
    "Conflicts": Permission.VIEW_CONFLICTS,
    "Drug Database": Permission.VIEW_DRUGS,
    "Rules Engine": Permission.VIEW_RULES,
    "Manual Testing": Permission.PRESCRIBE_DRUGS,
    "Import Data": Permission.IMPORT_DATA,
}


def get_role(role_name: str) -> Optional[Role]:
    """
    Convert role name string to Role enum
    
    Args:
        role_name: Role name as string
        
    Returns:
        Role enum or None if invalid
    """
    try:
        return Role(role_name)
    except ValueError:
        return None


def get_user_role() -> Optional[Role]:
    """
    Get current user's role
    
    Returns:
        Role enum or None if not authenticated
    """
    if 'user' not in st.session_state or st.session_state.user is None:
        return None
    
    return get_role(st.session_state.user.role)


def has_permission(permission: Permission, role: Optional[Role] = None) -> bool:
    """
    Check if user/role has a specific permission
    
    Args:
        permission: Permission to check
        role: Role to check (uses current user if None)
        
    Returns:
        True if permission granted
    """
    if role is None:
        role = get_user_role()
    
    if role is None:
        return False
    
    return permission in ROLE_PERMISSIONS.get(role, set())


def has_any_permission(permissions: List[Permission], role: Optional[Role] = None) -> bool:
    """
    Check if user/role has any of the specified permissions
    
    Args:
        permissions: List of permissions to check
        role: Role to check (uses current user if None)
        
    Returns:
        True if any permission granted
    """
    return any(has_permission(perm, role) for perm in permissions)


def has_all_permissions(permissions: List[Permission], role: Optional[Role] = None) -> bool:
    """
    Check if user/role has all of the specified permissions
    
    Args:
        permissions: List of permissions to check
        role: Role to check (uses current user if None)
        
    Returns:
        True if all permissions granted
    """
    return all(has_permission(perm, role) for perm in permissions)


def can_access_page(page_name: str, role: Optional[Role] = None) -> bool:
    """
    Check if user/role can access a specific page
    
    Args:
        page_name: Name of the page
        role: Role to check (uses current user if None)
        
    Returns:
        True if page access granted
    """
    if page_name not in PAGE_PERMISSIONS:
        return False
    
    required_permission = PAGE_PERMISSIONS[page_name]
    return has_permission(required_permission, role)


def get_accessible_pages(role: Optional[Role] = None) -> List[str]:
    """
    Get list of pages accessible to user/role
    
    Args:
        role: Role to check (uses current user if None)
        
    Returns:
        List of accessible page names
    """
    if role is None:
        role = get_user_role()
    
    if role is None:
        return []
    
    accessible = []
    for page_name, permission in PAGE_PERMISSIONS.items():
        if has_permission(permission, role):
            accessible.append(page_name)
    
    return accessible


def require_permission(permission: Permission):
    """
    Require a specific permission to access content
    Shows error and stops if permission denied
    
    Args:
        permission: Required permission
    """
    if not has_permission(permission):
        st.error("🚫 Access Denied")
        st.warning(f"You do not have permission to access this content. Required permission: {permission.value}")
        
        user = st.session_state.get('user')
        if user:
            st.info(f"Your role: **{user.role}**")
        
        st.stop()


def require_any_permission(permissions: List[Permission]):
    """
    Require any of the specified permissions
    Shows error and stops if all permissions denied
    
    Args:
        permissions: List of required permissions (at least one needed)
    """
    if not has_any_permission(permissions):
        st.error("🚫 Access Denied")
        st.warning(f"You do not have the required permissions to access this content.")
        
        user = st.session_state.get('user')
        if user:
            st.info(f"Your role: **{user.role}**")
        
        st.stop()


def require_role(required_roles: List[Role]):
    """
    Require user to have one of the specified roles
    Shows error and stops if role check fails
    
    Args:
        required_roles: List of allowed roles
    """
    current_role = get_user_role()
    
    if current_role not in required_roles:
        st.error("🚫 Access Denied")
        role_names = [role.value for role in required_roles]
        st.warning(f"This content is restricted to: {', '.join(role_names)}")
        
        user = st.session_state.get('user')
        if user:
            st.info(f"Your role: **{user.role}**")
        
        st.stop()


def get_role_badge_html(role: Role) -> str:
    """
    Get HTML for role badge display
    
    Args:
        role: User role
        
    Returns:
        HTML string for badge
    """
    colors = {
        Role.ADMIN: "#dc3545",      # Red
        Role.DOCTOR: "#0d6efd",     # Blue
        Role.PHARMACIST: "#198754", # Green
    }
    
    color = colors.get(role, "#6c757d")
    
    return f"""
    <span style="
        background-color: {color};
        color: white;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: bold;
        display: inline-block;
    ">
        {role.value}
    </span>
    """


def get_permission_description(permission: Permission) -> str:
    """
    Get human-readable description of a permission
    
    Args:
        permission: Permission enum
        
    Returns:
        Description string
    """
    descriptions = {
        Permission.VIEW_DASHBOARD: "View dashboard and statistics",
        Permission.VIEW_PATIENTS: "View patient information",
        Permission.VIEW_DRUGS: "View drug database",
        Permission.VIEW_RULES: "View conflict rules",
        Permission.VIEW_CONFLICTS: "View detected conflicts",
        Permission.VIEW_REPORTS: "View and access reports",
        Permission.VIEW_SIMULATION: "View simulation results",
        Permission.VIEW_ANALYTICS: "View analytics and insights",
        
        Permission.ADD_PATIENT: "Add new patients",
        Permission.EDIT_PATIENT: "Edit patient information",
        Permission.DELETE_PATIENT: "Delete patients",
        
        Permission.ADD_DRUG: "Add new drugs",
        Permission.EDIT_DRUG: "Edit drug information",
        Permission.DELETE_DRUG: "Delete drugs",
        
        Permission.ADD_RULE: "Add new conflict rules",
        Permission.EDIT_RULE: "Edit conflict rules",
        Permission.DELETE_RULE: "Delete conflict rules",
        
        Permission.RUN_SIMULATION: "Run agent simulations",
        Permission.PRESCRIBE_DRUGS: "Prescribe medications",
        Permission.GENERATE_REPORT: "Generate reports",
        Permission.EXPORT_DATA: "Export data",
        
        Permission.MANAGE_USERS: "Manage user accounts",
        Permission.CHANGE_SETTINGS: "Change system settings",
        Permission.VIEW_AUDIT_LOG: "View audit logs",
    }
    
    return descriptions.get(permission, permission.value)


def get_role_permissions_list(role: Role) -> List[str]:
    """
    Get list of permission descriptions for a role
    
    Args:
        role: User role
        
    Returns:
        List of permission description strings
    """
    permissions = ROLE_PERMISSIONS.get(role, set())
    return [get_permission_description(perm) for perm in sorted(permissions, key=lambda p: p.value)]


def is_admin() -> bool:
    """Check if current user is admin"""
    return get_user_role() == Role.ADMIN


def is_doctor() -> bool:
    """Check if current user is doctor"""
    return get_user_role() == Role.DOCTOR


def is_pharmacist() -> bool:
    """Check if current user is pharmacist"""
    return get_user_role() == Role.PHARMACIST
