from ckan.lib.helpers import link_to, url_for

from ckanext.switzerland.helpers.frontend_helpers import get_localized_value_for_display


def ogdch_list_user(user, maxlength=0):
    """display user in user list"""
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
                        "organization_read", action="read", id=role.organization.name
                    ),
                )
            )
    display_email = user.get("email")
    if not display_email:
        display_email = ""
    return {
        "link": link_to(user["name"], url_for("user.read", id=user["name"])),
        "email": display_email,
        "userroles": memberships_display,
    }


def ogdch_display_memberships(user):
    """format user memberships for writing to csv"""
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
