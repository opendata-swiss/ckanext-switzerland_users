import pytest
import ckan.model as model
import ckan.plugins.toolkit as tk
from ckan.tests import factories, helpers


def get_context():
    user = tk.get_action("get_site_user")({"ignore_auth": True})["name"]
    return {
        "model": model,
        "session": model.Session,
        "user": user,
        "ignore_auth": True,
    }


@pytest.fixture
def users():
    users = []
    for i in range(5):
        factories.Organization(name=f"org_{i}")
        for role in ["admin", "editor", "member"]:
            user = factories.UserWithToken(name=f"org_{i}_{role}")
            data_dict = {"id": f"org_{i}", "username": f"org_{i}_{role}", "role": role}
            tk.get_action("organization_member_create")(get_context(), data_dict)
            users.append(user)

    return users


@pytest.fixture
def sysadmins():
    sysadmins = []
    for i in range(5):
        sysadmin = factories.SysadminWithToken(name=f"org_{i}_member_sysadmin")
        data_dict = {
            "id": f"org_{i}",
            "username": f"org_{i}_member_sysadmin",
            "role": "member",
        }
        tk.get_action("organization_member_create")(get_context(), data_dict)
        sysadmins.append(sysadmin)

    return sysadmins


@pytest.fixture
def sysadmin_headers(sysadmins):
    headers = {"Authorization": sysadmins[0]["token"]}
    return headers
