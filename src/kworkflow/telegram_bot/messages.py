from kworkflow.projects.models import Project


def project_message(project: Project) -> str:
    return (
        "🔔 Новый проект\n\n"
        f"📂 {project.category.title}\n\n"
        f"<b>📌 {project.title}</b>\n\n"
        f"💰 Бюджет\n"
        f"• Желаемый: {project.price} ₽\n"
        f"• Допустимый: {project.possible_price_limit} ₽\n\n"
        f"📝 {project.description}\n\n"
        f"🔗 https://kwork.ru/projects/{project.external_id}/view"
    )


FREELANCER_PROFILE_TEMPLATE_TEXT = """
Отправьте одним сообщением информацию о себе:
• Кто вы и чем занимаетесь
• Ваш стек технологий / навыки
• Опыт работы
• Ссылки на портфолио
• Релевантные проекты и специализацию

Чем подробнее профиль — тем качественнее будут отклики.

Пример:

Я frontend-разработчик с опытом 5+ лет.
Работаю с HTML, CSS, JavaScript, TypeScript, React, Next.js.
Разрабатываю лендинги, интернет-магазины и CRM-системы.

Есть опыт интеграции API, Telegram-ботов и админ-панелей.

Портфолио:
https://example.com
https://github.com/example
"""


GENERATE_PROPOSAL_PROFILE_REQUIRED_TEXT = (
    "⚠️ Чтобы сгенерировать отклик, сначала заполните информацию о себе."
)

EDIT_FREELANCER_PROFILE_TEXT = (
    "✏️ Обновите информацию о себе для генерации более точных откликов."
)
