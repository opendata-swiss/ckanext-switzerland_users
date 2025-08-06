import csv
import logging
from io import StringIO
from typing import Any

import ckan.lib.base as base
import ckan.logic as logic
import ckan.plugins.toolkit as tk
from ckan import authz
from ckan.common import (
    _,
    config,
    current_user,
    request,
)
from ckan.lib.helpers import Page
from ckan.lib.helpers import helper_functions as h
from ckan.types import Context
from flask import Blueprint, make_response

from ckanext.switzerland.helpers.frontend_helpers import get_localized_value_for_display
from ckanext.switzerland_users.helpers import ogdch_display_memberships

log = logging.getLogger(__name__)

user = Blueprint("ogdch_users_blueprint", __name__, url_prefix="/user")


def index():
    """Copied from ckan.views.user.index to allow custom user search by organization
    and role.
    """
    page_number = h.get_page_number(request.args)
    q = request.args.get("q", "")
    organization = request.args.get("organization", None)
    role = request.args.get("role", None)
    order_by = request.args.get("order_by", "name")
    default_limit: int = config.get("ckan.user_list_limit")
    limit = int(request.args.get("limit", default_limit))
    offset = page_number * limit - limit

    context: Context = {
        "user": current_user.name,
        "auth_user_obj": current_user,
    }

    data_dict = {
        "q": q,
        "order_by": order_by,
        "organization": organization,
        "role": role,
    }

    try:
        logic.check_access("user_list", context, data_dict)
    except logic.NotAuthorized:
        base.abort(403, _("Not authorized to see this page"))

    user_admin_organizations = tk.get_action("ogdch_get_admin_organizations_for_user")(
        context, {}
    )
    if not user_admin_organizations:
        tk.abort(403, _("Not authorized to see this page"))

    users_list = logic.get_action("ogdch_user_list")(context, data_dict)
    organization_tree = tk.get_action("group_tree")(context, {"type": "organization"})
    userroles = tk.get_action("member_roles_list")(
        context, {"group_type": "organization"}
    )
    user_admin_organizations = tk.get_action("ogdch_get_admin_organizations_for_user")(
        context, {}
    )

    roles = _get_role_selection(current_user.name, userroles)
    organizations = _get_organization_selection(
        organization_tree, user_admin_organizations
    )

    page = Page(
        collection=users_list[offset : offset + limit],
        page=page_number,
        presliced_list=True,
        url=h.pager_url,
        item_count=len(users_list),
        items_per_page=limit,
        organization=organization,
        role=role,
    )

    extra_vars: dict[str, Any] = {
        "page": page,
        "q": q,
        "order_by": order_by,
        "selected_organization": organization,
        "selected_role": role,
        "organizations": organizations,
        "roles": roles,
    }
    return base.render("user/ogdch_list.html", extra_vars)


def _get_role_selection(current_user, userroles):
    """Get the roles that the user is authorized to search for."""
    userroles_display = [{"text": _("Role: all"), "value": ""}]
    if authz.is_sysadmin(current_user):
        userroles_display.append({"text": "Sysadmin", "value": "sysadmin"})
    userroles_display.extend(list(userroles))
    return userroles_display


def _get_organization_selection(organization_tree, allowed_organizations):
    """Get the organizations that the user is allowed to search for users in."""
    if not allowed_organizations:
        return []
    organizations_display = [{"text": _("Organization: all"), "value": ""}]
    for organization in organization_tree:
        if organization["name"] in allowed_organizations:
            organizations_display.append(
                _prepare_organization_select_item(organization)
            )
        for suborganization in organization.get("children"):
            if suborganization["name"] in allowed_organizations:
                organizations_display.append(
                    _prepare_organization_select_item(
                        suborganization, is_suborganization=True
                    )
                )
    return organizations_display


def _prepare_organization_select_item(organization, is_suborganization=False):
    """Format one organization select item."""
    organization_text = get_localized_value_for_display(organization.get("title"))
    if is_suborganization:
        organization_text = f"- {organization_text}"
    return {"text": organization_text, "value": organization.get("name")}


def download_csv():
    is_sysadmin = False
    if current_user.is_authenticated:
        is_sysadmin = authz.is_sysadmin(current_user.name)

    if not is_sysadmin:
        tk.abort(403, _("Not authorized to see this page"))

    context = {
        "user": current_user.name,
        "auth_user_obj": current_user,
    }
    users = tk.get_action("ogdch_user_list")(context, {})

    content = StringIO()
    writer = csv.writer(
        content, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL
    )
    writer.writerow([_("Username"), _("Email"), _("Role")])
    for user in users:
        email = user.get("email", "")
        if not email:
            email = ""
        writer.writerow(
            [
                user["name"],
                email,
                ogdch_display_memberships(user),
            ]
        )

    response = make_response(content.getvalue())
    response.headers.update({"Content-type": "text/csv"})

    return response


user.add_url_rule("/", view_func=index, strict_slashes=False)
user.add_url_rule("/users_csv", view_func=download_csv)
