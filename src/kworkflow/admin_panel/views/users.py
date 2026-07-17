from starlette_admin.contrib.sqla import ModelView

from kworkflow.users.models import User


class UserView(ModelView):
    fields = [  # noqa: RUF012
        User.id,
        User.telegram_id,
        User.created_at,
        User.updated_at,
    ]
