# coding=UTF-8

import logging
from collections import namedtuple, defaultdict
from ckan import authz, model
import ckan.plugins.toolkit as tk

Membership = namedtuple('Membership', ['organization', 'capacity'])
Organization = namedtuple('Organization', ['name', 'title'])
AdminCapacity = namedtuple('admin', ['capacity', 'organizations'])
CAPACITY_SYSADMIN = 'sysadmin'
CAPACITY_ADMIN = 'admin'

log = logging.getLogger(__name__)


def get_username_dict():
    """get users with only minimal attributes and a simple query to
    avoid preformance issues"""
    users = model.Session.query(model.User).all()
    user_dict = {user.name: user for user in users}
    return user_dict


def get_organizations_id_dict():
    """get organizations with ids and title"""
    organizations = model.Session.query(model.Group).filter(
        model.Group.state == 'active').filter(
        model.Group.type == 'organization').all()
    organization_dict = {organization.id: Organization(name=organization.name,
                                                       title=organization.title
                                                       )
                         for organization in organizations}
    return organization_dict


def get_memberships(admin_organization_restriction, q_role, q_organization):
    """get members form the member table; filter out restrictions"""
    organization_restrictions = admin_organization_restriction or []
    if q_organization:
        organization_restrictions.append(q_organization)
    organizations_id_dict = get_organizations_id_dict()
    if organization_restrictions:
        organizations_ids = [id for id, organization in
                             organizations_id_dict.items() if
                             organization.name in organization_restrictions]
    else:
        organizations_ids = organizations_id_dict.keys()
    log.debug("get memberships with organization restriction {}".format(
        organization_restrictions))
    members = model.Session.query(model.Member).filter(
        model.Member.state == 'active').filter(
        model.Member.table_name == 'user').filter(
        model.Member.group_id.in_(organizations_ids)).all()
    membership_dict = defaultdict(list)
    role_restrictions = []
    if q_role and q_role != CAPACITY_SYSADMIN:
        role_restrictions.append(q_role)
    log.debug(
        "get memberships with role restriction {}".format(role_restrictions))
    for member in members:
        if not role_restrictions or member.capacity in role_restrictions:
            membership = Membership(
                organization=organizations_id_dict[member.group_id],
                capacity=member.capacity)
            membership_dict[member.table_id].append(membership)
    return membership_dict


def ogdch_get_admin_organizations_for_user(context, data_dict):
    """Get list of organization where a user is admin of"""
    organizations_for_user = tk.get_action('organization_list_for_user')(
        context, data_dict)
    organizations_where_user_is_admin = [organization.get('name') for
                                         organization in organizations_for_user
                                         if organization.get(
            'capacity') == CAPACITY_ADMIN]
    log.debug("admin organizations for current user {}".format(
        organizations_where_user_is_admin))
    return organizations_where_user_is_admin


def ogdch_user_list(context, data_dict):
    """custom user list for ogdch: list users that are visible to the current
    user
    - for sysadmins: list all users
    - for organization admins: list all users of their organizations
    """
    log.debug("user search called with context {} data_dict {}".format(
        context,
        data_dict
    ))
    current_user = context.get('user')
    if authz.is_sysadmin(current_user):
        admin_organization_restriction = None
    else:
        admin_organization_restriction = tk.get_action(
            'ogdch_get_admin_organizations_for_user')(context, data_dict)
    q = data_dict.get('q')
    q_organization = data_dict.get('organization')
    q_role = data_dict.get('role')
    user_list_names_only = tk.get_action('user_list')(
        context,
        {'q': q, 'all_fields': False}
    )
    username_dict = get_username_dict()
    membership_dict = get_memberships(admin_organization_restriction, q_role,
                                      q_organization)
    user_list = [{'name': username, 'id': username_dict[username].id,
                  'sysadmin': username_dict[username].sysadmin,
                  'email': username_dict[username].email,
                  'memberships': membership_dict.get(
                      username_dict[username].id, [])} for username in
                 user_list_names_only]
    if admin_organization_restriction:
        user_list = filter(lambda user: admin_membership_test(
            user,
            admin_organization_restriction
        ), user_list)
    if q_organization:
        user_list = filter(
            lambda user: organization_query_membership_test(
                user,
                q_organization,
                q_role
            ), user_list)
    if q_role and not q_organization:
        user_list = filter(
            lambda user: role_query_membership_test(user, q_role), user_list)
    return user_list


def admin_membership_test(user, organization_restrictions):
    """if organizations are restricted, filter out sysadmin users and
    users with no memberships in restricted organizations"""
    if not organization_restrictions:
        return True
    if user['sysadmin']:
        return False
    if user['memberships']:
        if [membership for membership in user['memberships'] if
                membership.organization.name in organization_restrictions]:
            return True
    return False


def organization_query_membership_test(user, q_organization, q_role):
    """filter out sysadmin users and users that have
    no membership in the organization"""
    if not q_organization:
        return True
    if user['sysadmin']:
        return False
    if user['memberships']:
        if [membership for membership in user['memberships'] if
                membership.organization.name == q_organization]:
            if not q_role:
                return True
            if [membership for membership in user['memberships'] if
                    membership.capacity == q_role]:
                return True
        return False
    return False


def role_query_membership_test(user, q_role):
    """filter out sysadmin users and users that
    have no membership in the organization"""
    if q_role == CAPACITY_SYSADMIN:
        if user['sysadmin']:
            return True
    if user['memberships']:
        if [membership for membership in user['memberships'] if
                membership.capacity == q_role]:
            return True
    return False
