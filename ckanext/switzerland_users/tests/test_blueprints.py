import pytest
from bs4 import BeautifulSoup
from ckan.lib.helpers import url_for

prepare_role_filter_data = [
    (
        "admin",
        [
            "org_0_admin",
            "org_1_admin",
            "org_2_admin",
            "org_3_admin",
            "org_4_admin",
        ],
    ),
    (
        "editor",
        [
            "org_0_editor",
            "org_1_editor",
            "org_2_editor",
            "org_3_editor",
            "org_4_editor",
        ],
    ),
    (
        "member",
        [
            "org_0_member",
            "org_0_member_sysadmin",
            "org_1_member",
            "org_1_member_sysadmin",
            "org_2_member",
            "org_2_member_sysadmin",
            "org_3_member",
            "org_3_member_sysadmin",
            "org_4_member",
            "org_4_member_sysadmin",
        ],
    ),
]

prepare_org_filter_data = [
    (
        "org_0",
        [
            "org_0_admin",
            "org_0_editor",
            "org_0_member",
        ],
    ),
    (
        "org_1",
        [
            "org_1_admin",
            "org_1_editor",
            "org_1_member",
        ],
    ),
    (
        "org_2",
        [
            "org_2_admin",
            "org_2_editor",
            "org_2_member",
        ],
    ),
    (
        "org_3",
        [
            "org_3_admin",
            "org_3_editor",
            "org_3_member",
        ],
    ),
    (
        "org_4",
        [
            "org_4_admin",
            "org_4_editor",
            "org_4_member",
        ],
    ),
]


prepare_non_admin_filter_data = [
    ("org_0_member", None, None),
    ("org_0_editor", None, None),
    ("org_0_member", "org_0", "admin"),
    ("org_0_editor", "org_0", "admin"),
    ("org_0_member", "org_0", "editor"),
    ("org_0_editor", "org_0", "editor"),
    ("org_0_member", "org_0", "member"),
    ("org_0_editor", "org_0", "member"),
]


def _request_user_list_and_get_users(app, auth_headers, role=None, organization=None):
    url = url_for("ogdch_users_blueprint.index")
    params = {}
    if role:
        params["role"] = role
    if organization:
        params["organization"] = organization

    response = app.get(url, params=params, headers=auth_headers)
    soup = BeautifulSoup(response.body, "html.parser")

    table = soup.find("table")
    fullnames = [td.text for td in table.find_all("td", class_="media")]
    usernames = [
        td.find("a")["href"].replace("/user/", "")
        for td in table.find_all("td", class_="media")
    ]

    return fullnames, usernames


@pytest.mark.ckan_config("ckan.plugins", "ogdch ogdch_users ogdch_org ogdch_showcase")
@pytest.mark.ckan_config("ckan.auth.public_user_details", False)
@pytest.mark.ckan_config("ckanext.switzerland.send_email_on_user_registration", False)
@pytest.mark.usefixtures("with_plugins", "clean_db", "clean_index")
class TestBlueprints(object):
    def test_list_all_users(self, app, users, sysadmins, sysadmin_headers):
        fullnames, usernames = _request_user_list_and_get_users(app, sysadmin_headers)

        assert len(fullnames) == 20
        assert fullnames == sorted(fullnames)
        assert sorted(usernames) == [
            "org_0_admin",
            "org_0_editor",
            "org_0_member",
            "org_0_member_sysadmin",
            "org_1_admin",
            "org_1_editor",
            "org_1_member",
            "org_1_member_sysadmin",
            "org_2_admin",
            "org_2_editor",
            "org_2_member",
            "org_2_member_sysadmin",
            "org_3_admin",
            "org_3_editor",
            "org_3_member",
            "org_3_member_sysadmin",
            "org_4_admin",
            "org_4_editor",
            "org_4_member",
            "org_4_member_sysadmin",
        ]

    @pytest.mark.parametrize("role, expected_users", prepare_role_filter_data)
    def test_role_filter(
        self, role, expected_users, app, users, sysadmins, sysadmin_headers
    ):
        # We should only see users who have the selected role, in any organization.
        fullnames, usernames = _request_user_list_and_get_users(
            app, sysadmin_headers, role=role
        )

        assert len(fullnames) == len(expected_users)
        assert fullnames == sorted(fullnames)
        assert sorted(usernames) == expected_users

    @pytest.mark.parametrize("organization, expected_users", prepare_org_filter_data)
    def test_organization_filter(
        self, organization, expected_users, app, users, sysadmins, sysadmin_headers
    ):
        # Sysadmins should not be included in the list even if they are members of the
        # selected organization
        fullnames, usernames = _request_user_list_and_get_users(
            app, sysadmin_headers, organization=organization
        )

        assert len(fullnames) == len(expected_users)
        assert fullnames == sorted(fullnames)
        assert sorted(usernames) == expected_users

    @pytest.mark.parametrize(
        "username, role, organization", prepare_non_admin_filter_data
    )
    def test_non_admin_cannot_access_user_list(
        self, username, role, organization, app, users, sysadmins
    ):
        # Users with only the editor or member roles should not be allowed to access
        # the user list page, even if filtering for their own organization
        user = {}
        for user in users:
            if user["name"] == username:
                break
        user_headers = {"Authorization": user["token"]}

        params = {}
        if role:
            params["role"] = role
        if organization:
            params["organization"] = organization

        url = url_for("ogdch_users_blueprint.index")

        response = app.get(url, params=params, headers=user_headers)
        assert response.status_code == 403
        assert "Not authorized to see this page" in response.body

    def test_anonymous_user_cannot_access_user_list(self, app, users, sysadmins):
        url = url_for("ogdch_users_blueprint.index")

        response = app.get(url)
        assert response.status_code == 403
        assert "Not authorized to see this page" in response.body
