import ckan.plugins.toolkit as tk
from ckan.lib.helpers import link_to, linked_user, url_for

from ckanext.switzerland.helpers.frontend_helpers import get_localized_value_for_display


def ogdch_list_user(user, maxlength=0):
    """Display user in user list"""
    user_memberships = user.get("memberships", [])
    memberships_display = []
    if not user.get("sysadmin"):
        for role in user_memberships:
            text = (
                role.capacity.capitalize()
                + ": "
                + get_localized_value_for_display(role.organization.title)
            )
            memberships_display.append(
                link_to(
                    text,
                    url_for(
                        "organization.read", action="read", id=role.organization.name
                    ),
                )
            )
    display_email = user.get("email")
    if not display_email:
        display_email = ""
    return {
        "link": linked_user(user.get("name"), maxlength=20),
        "email": display_email,
        "userroles": memberships_display,
    }


def ogdch_display_memberships(user):
    """Format user memberships for writing to csv"""
    user_memberships = user.get("memberships", [])
    memberships_display = []
    if user.get("sysadmin"):
        memberships_display = "Sysadmin"
    else:
        for role in user_memberships:
            memberships_display.append(
                role.capacity.capitalize()
                + ": "
                + get_localized_value_for_display(role.organization.title)
            )
        memberships_display = ", ".join(memberships_display)

    return memberships_display


def ogdch_get_env():
    return tk.config.get("ckanext.switzerland_users.env", "test")
