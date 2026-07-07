from decimal import Decimal

from kworkflow.preferences.consts import MAX_STOP_WORDS
from kworkflow.projects.models import Project, ProjectCategory
from kworkflow.subscriptions.models import PlanSlug


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


def start_message() -> str:
    return (
        "👋 Добро пожаловать в <b>KworkFlow</b>\n\n"
        "Мониторю проекты на бирже Kwork и присылаю новые мгновенно.\n\n"
        "⚡ Что я делаю:\n"
        "• Мониторинг новых проектов\n"
        "• Мгновенные уведомления\n"
        "• Генерация автоматических откликов\n\n"
        "📂 Настрой категории — и я начну мониторинг"
    )


def menu_message(follow_categories: list[ProjectCategory]) -> str:
    follow_categories_str = "\n".join(
        f"• {cat.title}" for cat in follow_categories
    )
    if not follow_categories:
        follow_categories_str = "• Нет отслеживаемых категорий"
    return (
        "🏠 <b>Главное меню KworkFlow</b>\n\n"
        "⚡ <b>KworkFlow</b> отслеживает новые проекты на бирже <b>Kwork</b> "
        "и присылает подходящие задания автоматически.\n\n"
        "<b>📂 Отслеживаемые категории:\n</b>"
        f"{follow_categories_str}\n\n"
        "⚙️ Используйте меню ниже для управления настройками"
    )


def categories_saved_message(follow_categories: list[ProjectCategory]) -> str:
    follow_categories_str = "\n".join(
        f"• {cat.title}" for cat in follow_categories
    )
    if not follow_categories:
        follow_categories_str = "• Нет отслеживаемых категорий"
    return (
        "✅ Настройка завершена.\n\n"
        "📂Выбранные категории:\n"
        f"{follow_categories_str}\n\n"
        "Мониторинг активирован — уведомления о новых проектах будут приходить автоматически."
    )


def unfollow_all_categories_message() -> str:
    return (
        "🗑️ Отписка от всех категорий выполнена.\n\n"
        "Уведомления о новых проектах приходить не будут.\n"
        "Чтобы возобновить мониторинг — выберите категории в меню."
    )


def profile_not_set_message() -> str:
    return (
        "👤 <b>Профиль фрилансера</b>\n\n"
        "Профиль ещё не заполнен.\n\n"
        "ℹ️ Профиль используется для генерации "
        "персонализированных откликов на проекты.\n"
        "Чем подробнее вы опишете себя и свои навыки — "
        "тем качественнее будут отклики.\n\n"
        "Нажмите «✏️ Редактировать», чтобы заполнить профиль."
    )


def profile_info_message(about: str) -> str:
    return (
        "👤 <b>Профиль фрилансера</b>\n\n"
        f"{about}\n\n"
        "ℹ️ Этот профиль используется для генерации откликов.\n"
        "Вы можете отредактировать его в любой момент."
    )


def start_edit_profile_message() -> str:
    return (
        "<b>Отправьте одним сообщением информацию о себе:</b>\n\n"
        "• Кто вы и чем занимаетесь\n"
        "• Ваш стек технологий / навыки\n"
        "• Опыт работы\n"
        "• Ссылки на портфолио\n"
        "• Релевантные проекты и специализацию\n\n"
        "<b>Чем подробнее профиль — тем качественнее будут отклики.</b>\n\n"
        "<b>Пример:</b>\n\n"
        "Я frontend-разработчик с опытом 5+ лет.\n"
        "Работаю с HTML, CSS, JavaScript, TypeScript, React, Next.js.\n"
        "Разрабатываю лендинги, интернет-магазины и CRM-системы.\n\n"
        "Есть опыт интеграции API, Telegram-ботов и админ-панелей.\n\n"
        "Портфолио:\n"
        "https://example.com\n"
        "https://github.com/example\n"
    )


def stop_words_menu_message(words: list[str]) -> str:
    stop_words_list = "\n".join(
        f"{i}. {word}" for i, word in enumerate(words, start=1)
    )
    return (
        "🛑 <b>Стоп-слова</b>\n\n"
        "Стоп-слова — это фильтр для уведомлений.\n\n"
        "Если в названии или описании нового проекта "
        "встретится такое слово — вы <b>не получите</b> "
        "уведомление об этом проекте.\n\n"
        f"📝 Ваши стоп-слова ({len(words)}/{MAX_STOP_WORDS})\n\n"
        f"{stop_words_list}"
    )


def start_add_stop_words_message() -> str:
    return (
        "✏️ <b>Добавление стоп-слов</b>\n\n"
        "Введите одно или несколько слов через запятую.\n\n"
        "Проекты, содержащие эти слова в названии или описании, "
        "не будут приходить вам в уведомления.\n\n"
        "<b>Пример:</b>\n"
        "работа, тест, копирайтинг, telegram\n\n"
        'Чтобы отменить — нажмите кнопку "✖️ Отмена"'
    )


def start_delete_stop_words_message(words: list[str]) -> str:
    stop_words_list = "\n".join(
        f"{i}. {word}" for i, word in enumerate(words, start=1)
    )
    return (
        "🗑 <b>Удаление стоп-слов</b>\n\n"
        "Введите одно или несколько слов через запятую, "
        "которые хотите удалить из стоп-листа.\n\n"
        "<b>Текущие стоп-слова:</b>\n"
        f"{stop_words_list}\n\n"
        "<b>Пример:</b>\n"
        "тест, копирайтинг\n\n"
        'Чтобы отменить — нажмите кнопку "✖️ Отмена"'
    )


def empty_stop_words_delete_message() -> str:
    return "У вас пока нет стоп-слов, поэтому удалять нечего."


def stop_words_limit_exceeded_message() -> str:
    return f"❌ Достигнут лимит в {MAX_STOP_WORDS} стоп-слов."


def select_categories_message() -> str:
    return "📂 Выберите категории для мониторинга"


def generating_proposal_message() -> str:
    return "🔄 Генерирую"


def already_generating_proposal_message() -> str:
    return "⏳ Уже генерирую"


def project_proposal_generation_permission_error_message() -> str:
    return (
        "🔒 Упс, пока что генерация доступна не всем пользователям\n\n"
        "Связаться: @askanonagent"
    )


def pro_subscription_info_message(plan_slug: PlanSlug) -> str:
    text = (
        "👑 PRO подписка\n\n"
        "Открой полный доступ к возможностям бота:\n\n"
        "📂 Все категории — подписывайся не на 2, а на любое "
        "количество категорий и не пропускай ни одного нового проекта\n\n"
        "🔔 Мгновенные уведомления — узнавай о новых заказах "
        "в выбранных категориях первым, пока их не разобрали конкуренты\n\n"
        "🤖 100 генераций откликов — вместо 3 бесплатных получи 100 откликов, "
        "сгенерированных нейросетью, которые помогут выделиться среди фрилансеров\n\n"
        "⚡️ Экономия времени — не нужно придумывать текст отклика самому, "
        "ИИ сделает это за секунды\n\n"
    )
    if plan_slug == PlanSlug.PRO_INITIAL:
        text += (
            "🎁 Попробуй PRO всего за 1₽ на 3 дня, "
            "далее — 499₽/мес. Отменить можно в любой момент."
        )
    else:
        text += (
            "💎 Оформи полную PRO подписку и "
            "получи безлимитный доступ ко всем функциям бота"
        )
    return text


def payment_message(
    payment_id: str, email: str, amount: Decimal, link: str
) -> str:
    return (
        f"🛒 Платеж: <b>{payment_id}</b>\n\n"
        f"💰 Cумма: {amount:.0f}₽\n\n"
        f"✅ Используется email: {email}\n\n"
        f"💳 Перейди по ссылке для оплаты: {link}\n\n"
        "Либо жми оплатить 👇"
    )


def payment_email_message() -> str:
    return "✍️ Введи свой email (он нужен для чека):"


def payment_email_validation_error_message() -> str:
    return "❌ Такой email не подходит. Попробуй ещё раз:"
