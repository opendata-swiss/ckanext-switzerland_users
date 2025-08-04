import logging

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.lib.plugins import DefaultTranslation

from ckanext.switzerland_users import helpers as ogdch_user_helpers
from ckanext.switzerland_users import logic as ogdch_user_logic

log = logging.getLogger(__name__)


class OgdchUsersPlugin(plugins.SingletonPlugin, DefaultTranslation):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.ITranslation)
    plugins.implements(plugins.IBlueprint)

    # ITranslation

    def i18n_domain(self):
        return "ckanext-switzerland_users"

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, "templates")

    def get_actions(self):
        """
        Expose new API methods
        """
        return {
            "ogdch_get_admin_organizations_for_user": ogdch_user_logic.ogdch_get_admin_organizations_for_user,
            "ogdch_user_list": ogdch_user_logic.ogdch_user_list,
        }

    # ITemplateHelpers

    def get_helpers(self):
        """
        Provide template helper functions
        """
        return {
            "ogdch_list_user": ogdch_user_helpers.ogdch_list_user,
        }

    # IBlueprint

    def get_blueprint(self):
        return []

    # IRouter

    def before_map(self, map):
        """adding custom routes to the ckan mapping"""

        map.connect(
            "user_index",
            "/user/",
            controller="ckanext.switzerland_users.controllers:OgdchUserController",
            action="index",
        )

        map.connect(
            "/user",
            controller="ckanext.switzerland_users.controllers:OgdchUserController",
            action="index",
        )

        map.connect(
            "/users_csv",
            controller="ckanext.switzerland_users.controllers:OgdchUserController",
            action="csv",
        )

        return map
