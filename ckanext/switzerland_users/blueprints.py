import logging
from typing import Any

import ckan.lib.base as base
import ckan.logic as logic
from ckan.common import (
    _,
    config,
    current_user,
    request,
)
from ckan.lib.dictization import model_dictize
from ckan.lib.helpers import Page
from ckan.lib.helpers import helper_functions as h
from ckan.types import Context
from flask import Blueprint

log = logging.getLogger(__name__)

user = Blueprint("ogdch_user", __name__, url_prefix="/user")


def index():
    """Copied from ckan.views.user.index to allow custom user search by organization
    and role.
    """
    page_number = h.get_page_number(request.args)
    q = request.args.get("q", "")
    order_by = request.args.get("order_by", "name")
    default_limit: int = config.get("ckan.user_list_limit")
    limit = int(request.args.get("limit", default_limit))
    offset = page_number * limit - limit

    # get SQLAlchemy Query object from the action to avoid dictizing all
    # existing users at once
    context: Context = {
        "return_query": True,
        "user": current_user.name,
        "auth_user_obj": current_user,
    }

    data_dict = {
        "q": q,
        "order_by": order_by,
    }

    try:
        logic.check_access("user_list", context, data_dict)
    except logic.NotAuthorized:
        base.abort(403, _("Not authorized to see this page"))

    users_list = logic.get_action("user_list")(context, data_dict)

    # in template we don't need complex row objects from query. Let's dictize
    # subset of users that are shown on the current page
    users = [
        model_dictize.user_dictize(user[0], context)
        for user in users_list.limit(limit).offset(offset)
    ]

    page = Page(
        collection=users,
        page=page_number,
        presliced_list=True,
        url=h.pager_url,
        item_count=users_list.count(),
        items_per_page=limit,
    )

    extra_vars: dict[str, Any] = {"page": page, "q": q, "order_by": order_by}
    return base.render("user/list.html", extra_vars)
