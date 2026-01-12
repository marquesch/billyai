import datetime
from dataclasses import dataclass
from string import Template

from pydantic_ai import Agent
from pydantic_ai import FunctionToolset
from pydantic_ai import ModelMessagesTypeAdapter
from pydantic_ai import RunContext
from pydantic_ai.messages import ModelMessage
from pydantic_ai.messages import ModelRequest
from pydantic_ai.messages import ModelResponse
from pydantic_ai.messages import TextPart
from pydantic_ai.messages import UserPromptPart
from pydantic_core import to_jsonable_python

from application.services.bill_service import BillService
from application.services.category_service import CategoryService
from application.services.registration_service import RegistrationService
from domain.entities import Bill
from domain.entities import Category
from domain.entities import Message
from domain.entities import MessageAuthor
from domain.entities import User
from domain.exceptions import BillNotFoundException
from domain.exceptions import CategoryAlreadyExistsException
from domain.exceptions import CategoryNotFoundException
from domain.exceptions import KeyNotFoundException
from domain.ports.repositories import MessageRepository
from domain.ports.repositories import UserRepository
from domain.ports.services import TemporaryStorageService

USER_MESSAGE_HISTORY_KEY_TEMPLATE = Template("user:$user_id:message_history")


@dataclass
class AgentDependencies:
    registration_service: RegistrationService
    category_service: CategoryService
    bill_service: BillService
    user: User


agent = Agent(
    "deepseek:deepseek-chat",
    instructions="""
    You are an assistant that helps people have more control over their expenses.
    Your main goal is to save users expenses in the form of bills, with value, date and category.
    You should avoid at all costs to use the default category for the user. Always try to incentivize
    the user to create new categories to help categorize their expenses.
    Avoid creating more than 10 categories for the user, unless they tell you to.
    You won't be able to help the user if they are still not registered. If that's the case, tell them
    you'll only be able to help once they're registered.

    You are professional and pragmatic. No small talk.
    """,
    deps_type=AgentDependencies,
)


class PydanticAIAgentService:
    def __init__(
        self,
        registration_service: RegistrationService,
        temp_storage_service: TemporaryStorageService,
        message_repository: MessageRepository,
        user_repository: UserRepository,
        bill_service: BillService,
        category_service: CategoryService,
        message_history_ttl_seconds: int,
    ):
        self._user_repository = user_repository
        self._message_repository = message_repository
        self._registration_service = registration_service
        self._bill_service = bill_service
        self._category_service = category_service
        self._message_history_ttl_seconds = message_history_ttl_seconds

        self._temp_storage_service = temp_storage_service

        self._agent = agent

        self._user_toolset = user_toolset
        self._guest_toolset = guest_toolset

    def _load_agent_dependencies(self, user: User | None):
        return AgentDependencies(
            registration_service=self._registration_service,
            bill_service=self._bill_service,
            category_service=self._category_service,
            user=user,
        )

    def _convert_message_history_to_pydantic_ai(self, messages: list[Message]) -> list[ModelMessage]:
        pydantic_messages = []
        for message in messages:
            match message.author:
                case MessageAuthor.USER.value:
                    pydantic_messages.append(ModelRequest(parts=[UserPromptPart(content=message.body)]))
                case MessageAuthor.BILLY.value:
                    pydantic_messages.append(ModelResponse(parts=[TextPart(content=message.body)]))

        return pydantic_messages

    def _load_user_message_history(self, user: User) -> list[ModelMessage]:
        try:
            message_history = self._temp_storage_service.get(
                USER_MESSAGE_HISTORY_KEY_TEMPLATE.substitute(user_id=user.id),
            )
            return ModelMessagesTypeAdapter.validate_python(message_history)
        except KeyNotFoundException:
            messages = self._message_repository.get_all(user_id=user.id, tenant_id=user.tenant_id)
            return self._convert_message_history_to_pydantic_ai(messages)

    def _cache_user_message_history(self, user: User, messages_bytes: bytes) -> None:
        self._temp_storage_service.set(
            USER_MESSAGE_HISTORY_KEY_TEMPLATE.substitute(user_id=user.id),
            messages_bytes,
            self._message_history_ttl_seconds,
        )

    async def run(self, message_body: str, user: User) -> str:
        agent_dependencies = self._load_agent_dependencies(user)
        toolset = user_toolset if user.is_registered else guest_toolset

        message_history = self._load_user_message_history(user)

        result = await self._agent.run(
            message_body,
            message_history=message_history,
            deps=agent_dependencies,
            toolsets=[toolset],
        )

        self._cache_user_message_history(user, to_jsonable_python(result.all_messages()))

        return result.output


user_toolset = FunctionToolset()
guest_toolset = FunctionToolset()


@guest_toolset.tool
def register_user(ctx: RunContext[AgentDependencies], user_name: str) -> User | str:
    """Registers a user into the database.

    Args:
        user_name (str): Name of the user
    Returns:
        User | str: User if user was successfully registered or the reason why it failed

    """
    return ctx.deps.registration_service.finish_registration(ctx.deps.user.id, user_name)


@user_toolset.tool
def get_user_name(ctx: RunContext[str]) -> str:
    """Gets the name of the user.

    Returns:
        str: the name of the current user

    """
    return ctx.deps.user.name


@user_toolset.tool
def register_category(
    ctx: RunContext[AgentDependencies],
    name: str,
    description: str,
) -> Category | str:
    """Registers a category for a user.

    Args:
        name (str): the name of the category
        description (str): a description of the category
    Returns:
        Category | str: Category if one was successfully created or the reason why it failed to create one

    """
    try:
        return ctx.deps.category_service.create(ctx.deps.user.tenant_id, name, description)
    except CategoryAlreadyExistsException:
        return "Category with this name already exists"


@user_toolset.tool
def get_all_categories(ctx: RunContext[AgentDependencies]) -> list[dict]:
    """Gets all categories from a tenant.

    Returns:
        list[Category]: A list of all categories from a tenant.

    """
    return ctx.deps.category_service.get_all(ctx.deps.user.tenant_id)


@user_toolset.tool
def register_bill(
    ctx: RunContext[AgentDependencies],
    date: datetime.date,
    value: float,
    category_id: int,
) -> Bill | str:
    """Registers an expense for a user.

    Args:
        value (float): the value of the bill
        date (datetime.date): the date of the bill
        category_id (int): the id of a category to link the bill to

    Returns:
        Bill | str: A dataclass representing the bill or a reason why it failed

    """
    try:
        return ctx.deps.bill_service.create(ctx.deps.user.tenant_id, date, value, category_id)
    except CategoryNotFoundException:
        return "Category not found"


@user_toolset.tool
def edit_bill(
    ctx: RunContext[AgentDependencies],
    bill_id: int,
    date: datetime.date | None = None,
    value: float | None = None,
    category_id: int | None = None,
) -> Bill | str:
    """Edits a bill by its id

    Args:
        bill_id (int): the id of the bill to be editted
        date (datetime.date, optional): an optional new date for the bill.
        value (float, optional): an optional new value of the bill to edit,
        category_id (int, optional): an optional category_id to assign a new category.

    Returns:
        Bill | str: A dataclass representing the bill or a reason why it failed

    """
    try:
        return ctx.deps.bill_service.update(ctx.deps.user.tenant_id, bill_id, date, value, category_id)
    except CategoryNotFoundException:
        return "Category not found"
    except BillNotFoundException:
        return "Bill not found"


@user_toolset.tool
def get_bills(
    ctx: RunContext[AgentDependencies],
    date_range: tuple[datetime.date, datetime.date] | None = None,
    category_id: int | None = None,
    value_range: tuple[float, float] | None = None,
) -> list[Bill]:
    """Returns bills with optional filters. Limited to 10 bills each time.

    Args:
        date_range (tuple[datetime.date, datetime.date], optional): an optional date range (two dates) to filter the bills by their date
        category_id (int, optional): an optional id of a category to filter bills by their category
        value_range (tuple[float, float], optional): an optional value range (two floats) to filter bills by their value
    Return:
        list[Bill]: a list of Bill, a dataclass representing a bill

    """
    return ctx.deps.bill_service.get_many(ctx.deps.user.tenant_id, category_id, date_range, value_range)


@user_toolset.tool
def get_today():
    """Returns a date object representing the current day

    Return:
        datetime.date: a date representing the current day

    """
    return datetime.date.today()
