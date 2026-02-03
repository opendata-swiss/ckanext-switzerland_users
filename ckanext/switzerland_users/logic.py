import logging
from collections import defaultdict, namedtuple

import ckan.plugins.toolkit as tk
from ckan import authz, model
from sqlalchemy import case as _case
from sqlalchemy import or_ as _or_

Membership = namedtuple("Membership", ["organization", "capacity"])
Organization = namedtuple("Organization", ["name", "title"])
AdminCapacity = namedtuple("admin", ["capacity", "organizations"])
CAPACITY_SYSADMIN = "sysadmin"
CAPACITY_ADMIN = "admin"

log = logging.getLogger(__name__)


def get_user_list(q, current_user):
    """A simplified version of ckan.logic.action.get.user_list, which does not include
    the extra search for packages created by each user. This improves performance.
    """
    query = model.Session.query(model.User)

    # Filter out the site user
    site_id = tk.config.get("ckan.site_id")
    query = query.filter(model.User.name != site_id)

    # Pass in any query the user has entered
    query = model.User.search(q, query, user_name=current_user)
    # Order by user.display_name: this is the default ordering.
    query = query.order_by(
        _case(
            (
                _or_(model.User.fullname.is_(None), model.User.fullname == ""),
                model.User.name,
            ),
            else_=model.User.fullname,
        )
    )

    # Filter out deleted users
    query = query.filter(model.User.state != model.State.DELETED)

    return query.all()


def get_organizations_id_dict():
    """get organizations with ids and title"""
    organizations = (
        model.Session.query(model.Group)
        .filter(model.Group.state == "active")
        .filter(model.Group.type == "organization")
        .all()
    )
    organization_dict = {
        organization.id: Organization(name=organization.name, title=organization.title)
        for organization in organizations
    }
    return organization_dict


def get_memberships(admin_organization_restriction, q_role, q_organization):
    """Get members from the member table; filter out restrictions"""
    organization_restrictions = admin_organization_restriction or []
    if q_organization:
        organization_restrictions.append(q_organization)
    organizations_id_dict = get_organizations_id_dict()
    if organization_restrictions:
        organizations_ids = [
            id
            for id, organization in list(organizations_id_dict.items())
            if organization.name in organization_restrictions
        ]
    else:
        organizations_ids = list(organizations_id_dict.keys())
    log.debug(
        f"get memberships with organization restriction {organization_restrictions}"
    )
    members = (
        model.Session.query(model.Member)
        .filter(model.Member.state == "active")
        .filter(model.Member.table_name == "user")
        .filter(model.Member.group_id.in_(organizations_ids))
        .all()
    )
    membership_dict = defaultdict(list)
    role_restrictions = []
    if q_role and q_role != CAPACITY_SYSADMIN:
        role_restrictions.append(q_role)
    log.debug(f"get memberships with role restriction {role_restrictions}")
    for member in members:
        if not role_restrictions or member.capacity in role_restrictions:
            membership = Membership(
                organization=organizations_id_dict[member.group_id],
                capacity=member.capacity,
            )
            membership_dict[member.table_id].append(membership)
    return membership_dict


def ogdch_get_admin_organizations_for_user(context, data_dict):
    """Get list of organization of which a user is admin"""
    organizations_for_user = tk.get_action("organization_list_for_user")(
        context, data_dict
    )
    organizations_where_user_is_admin = [
        organization.get("name")
        for organization in organizations_for_user
        if organization.get("capacity") == CAPACITY_ADMIN
    ]
    log.debug(
        f"admin organizations for current user {organizations_where_user_is_admin}"
    )
    return organizations_where_user_is_admin


def ogdch_user_list(context, data_dict):
    """Custom user list for ogdch: list users that are visible to the current
    user
    - for sysadmins: list all users
    - for organization admins: list all users of their organizations
    """
    log.debug(f"user search called with context {context} data_dict {data_dict}")
    current_user = context.get("user")

    if authz.is_sysadmin(current_user):
        admin_organization_restriction = None
    else:
        admin_organization_restriction = tk.get_action(
            "ogdch_get_admin_organizations_for_user"
        )(context, data_dict)

    q = data_dict.get("q", "")
    q_organization = data_dict.get("organization")
    q_role = data_dict.get("role")

    user_object_list = get_user_list(q, current_user)
    membership_dict = get_memberships(
        admin_organization_restriction, q_role, q_organization
    )
    user_list = [
        {
            "name": user.name,
            "id": user.id,
            "sysadmin": user.sysadmin,
            "email": user.email,
            "memberships": membership_dict.get(user.id, []),
        }
        for user in user_object_list
    ]
    if admin_organization_restriction:
        user_list = [
            user
            for user in user_list
            if admin_membership_test(user, admin_organization_restriction)
        ]
    if q_organization:
        user_list = [
            user
            for user in user_list
            if organization_query_membership_test(user, q_organization, q_role)
        ]
    if q_role and not q_organization:
        user_list = [
            user for user in user_list if role_query_membership_test(user, q_role)
        ]
    return user_list


def admin_membership_test(user, organization_restrictions):
    """If organizations are restricted, filter out sysadmin users and users with no
    memberships in restricted organizations
    """
    if not organization_restrictions:
        return True
    if user["sysadmin"]:
        return False
    if user["memberships"]:
        if [
            membership
            for membership in user["memberships"]
            if membership.organization.name in organization_restrictions
        ]:
            return True
    return False


def organization_query_membership_test(user, q_organization, q_role):
    """Filter out sysadmin users and users that have no membership in the organization"""
    if not q_organization:
        return True
    if user["sysadmin"]:
        return False
    if user["memberships"]:
        if [
            membership
            for membership in user["memberships"]
            if membership.organization.name == q_organization
        ]:
            if not q_role:
                return True
            if [
                membership
                for membership in user["memberships"]
                if membership.capacity == q_role
            ]:
                return True
        return False
    return False


def role_query_membership_test(user, q_role):
    """Filter out sysadmin users and users that have no membership in the organization"""
    if q_role == CAPACITY_SYSADMIN:
        if user["sysadmin"]:
            return True
    if user["memberships"]:
        if [
            membership
            for membership in user["memberships"]
            if membership.capacity == q_role
        ]:
            return True
    return False
