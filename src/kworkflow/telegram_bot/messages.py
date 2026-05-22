from kworkflow.projects.models import Project


def project_message(project: Project) -> str:
    return (
        "🔔 Новый заказ!\n\n"
        f"📂 Категория: {project.category.title}\n\n"
        f"<b>📌 {project.title}</b>\n\n"
        f"💰 Бюджет: желаемый - {project.price} руб, допустимый - {project.possible_price_limit}\n\n"
        f"📝 {project.description}\n\n"
        f"🔗 https://kwork.ru/projects/{project.external_id}/view"
    )
