from openai import AsyncOpenAI
from pydantic import BaseModel

from kworkflow.projects.exceptions import ProjectProposalGenerationError


class ProjectProposalResponse(BaseModel):
    text: str


class ProjectProposalGenerator:
    def __init__(self, client: AsyncOpenAI):
        self.client = client

    def build_prompt(self, freelancer_info: str, project_info: str):
        return f"""Ты опытный фрилансер. Напиши отклик на заказ для фриланс-биржи.
 
## Данные о фрилансере
{freelancer_info}
 
## Данные о заказе
{project_info}
 
## Структура отклика (строго соблюдай порядок блоков)
1. hook — первое предложение цепляет и показывает, что ты внимательно прочитал заказ. Упомяни специфику задачи. Не начинай с «Здравствуйте» или «Готов взяться».
2. hidden_needs — покажи понимание того, что стоит за заказом: настоящий результат, который нужен клиенту, его вероятные риски и боли.
3. solution — кратко опиши подход: из каких шагов состоит работа и почему именно так.
4. proof — один конкретный релевантный пример из опыта с измеримым результатом. Не «делал похожее», а «сделал X — получилось Y». Если есть ссылки — упомяни их наличие естественно, например: «детали — в портфолио», но саму ссылку в текст блока не вставляй.
5. cta — конкретный следующий шаг: уточняющий вопрос, предложение обсудить детали или созвониться.
 
## Работа со ссылками
Если в данных фрилансера есть ссылки (портфолио, GitHub, Behance и т.д.) — вставь их в конец текста отклика.
 
## Требования к тексту
- Тон: профессиональный, но живой
- Каждый блок: 1–3 предложения
- Длина отклика: 150-300 символов
- Без шаблонных фраз: «готов к сотрудничеству», «качественно и в срок», «ответственный подход»
- Без канцелярита и вводных конструкций
"""

    async def generate(
        self,
        freelancer_info: str,
        project_info: str,
    ) -> tuple[ProjectProposalResponse, str]:
        prompt = self.build_prompt(
            freelancer_info,
            project_info,
        )
        completion = await self.client.chat.completions.parse(
            model="google/gemini-3.5-flash",
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            response_format=ProjectProposalResponse,
        )
        result = completion.choices[0].message.parsed
        if result is None:
            raise ProjectProposalGenerationError
        return result, prompt
