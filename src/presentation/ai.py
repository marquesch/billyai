import datetime
from dataclasses import dataclass

from pydantic_ai import Agent
from pydantic_ai import FunctionToolset
from pydantic_ai import RunContext

from application.services.ai_agent_service import AIAgentService
from domain.entities import Bill
from domain.entities import Category
from domain.entities import User
from domain.exceptions import CategoryAlreadyExistsException
from domain.exceptions import PhoneNumberTakenException
from infrastructure.persistence.database import db_session


@dataclass
class AgentDependencies:
    agent_service: AIAgentService
    user: User


agent = Agent(
    "deepseek:deepseek-chat",
    instructions="Talk to the user by his name only if he's registered. If the user is not registered yet, try to register him. Ask his name if it's not clear. Ask for user consent before registering him. Be polite, but concise in your messages. Avoid small talk.",
    deps_type=AgentDependencies,
)


def register_user(ctx: RunContext[AgentDependencies], user_name: str) -> User | None:
    """Registers a user into the database.

    Args:
        user_name (str): Name of the user
    Returns:
        User | None: User if user was successfully registered. None otherwise.

    """
    try:
        ctx.deps.user = ctx.deps.agent_service.create_user(user_name)
    except PhoneNumberTakenException:
        return None


def get_user_name(ctx: RunContext[str]) -> str:
    """Gets the name of the user.

    Returns:
        str: the name of the current user

    """
    return ctx.deps.user.name


def create_category(
    ctx: RunContext[AgentDependencies],
    name: str,
    description: str,
) -> Category:
    """Registers a category for a user.

    Args:
        name (str): the name of the category
        description (str): a description of the category
    Returns:
        Category | None: Category if one was successfully created. None otherwise.

    """
    try:
        return ctx.deps.agent_service.create_category(name, description)
    except CategoryAlreadyExistsException:
        return None


def get_all_categories(ctx: RunContext[AgentDependencies]) -> list[dict]:
    """Gets all categories from a tenant.

    Returns:
        list[Category]: A list of all categories from a tenant.

    """
    return ctx.deps.agent_service.get_all_categories()


def register_bill(
    ctx: RunContext[AgentDependencies],
    date: datetime.datetime,
    value: float,
    category_id: int,
) -> Bill:
    """Registers an expense for a user.

    Args:
        value (float): the value of the bill
        date (datetime.datetime): the date of the bill
        category_id (int): the id of a category to link the bill to

    Returns:
        Bill: A dataclass representing the bill

    """
    return ctx.deps.agent_service.create_bill(date, value, category_id)


def edit_bill(
    ctx: RunContext[AgentDependencies],
    bill_id: int,
    date: datetime.datetime | None = None,
    value: float | None = None,
    category_id: int | None = None,
):
    """Edits a bill by its id

    Args:
        bill_id (int): the id of the bill to be editted
        date (datetime.datetime, optional): an optional new date for the bill.
        value (float, optional): an optional new value of the bill to edit,
        category_id (int, optional): an optional category_id to assign a new category.

    Returns:
        Bill: A dataclass representing the bill

    """
    return ctx.deps.agent_service.update_bill(bill_id, date, value, category_id)


def get_bills(
    ctx: RunContext[AgentDependencies],
    date_range: tuple[datetime.datetime, datetime.datetime] | None = None,
    category_id: int | None = None,
    value_range: tuple[float, float] | None = None,
) -> list[Bill]:
    """Returns bills with optional filters. Limited to 10 bills each time.

    Args:
        date_range (tuple[datetime.datetime, datetime.datetime], optional): an optional date range (two dates) to filter the bills by their date
        category_id (int, optional): an optional id of a category to filter bills by their category
        value_range (tuple[float, float], optional): an optional value range (two floats) to filter bills by their value
    Return:
        list[Bill]: a list of Bill, a dataclass representing a bill

    """
    return ctx.deps.agent_service.get_bills(category_id, date_range, value_range)


def get_time_now():
    """Returns what time is now

    Return:
        str: an ISO formatted string representing the current moment in time

    """
    return datetime.datetime.now().isoformat()


registered_toolset = FunctionToolset(
    tools=[
        get_user_name,
        register_bill,
        get_bills,
        register_category,
        get_all_categories,
        edit_bill,
    ],
)
unregistered_toolset = FunctionToolset(tools=[register_user])

if __name__ == "__main__":
    from infrastructure.persistence.database.repositories.bill_repository import DBBillRepository
    from infrastructure.persistence.database.repositories.category_repository import DBCategoryRepository
    from infrastructure.persistence.database.repositories.user_repository import DBUserRepository
    from infrastructure.persistence.database.repositories.tenant_repository import DBTenantRepository
    phone_number = input("Phone number: ")

    session = next(db_session())

    user_repo = DBUserRepository(session)
    category_repo = DBCategoryRepository(session)
    bill_repo = DBBillRepository(session)
    tenant_repo = DBTenantRepository(session)

    agent_service = AIAgentService(phone_number, user_repo, bill_repo, category_repo, tenant_repo)
    user = user_repo.get_by_phone_number(phone_number)
    deps = AgentDependencies(agent_service, user)

    print(f"User is {'REGISTERED' if user is not None else 'UNREGISTERED'}")

    input_msg = input("You: ")
    print()
    message_history = []

    while input_msg != "exit":
        toolset = unregistered_toolset
        if deps.user is not None:
            toolset = registered_toolset
        result = agent.run_sync(
            input_msg,
            message_history=message_history,
            deps=deps,
            toolsets=[toolset],
        )
        print(f"LLM: {result.output}")
        print()
        message_history = result.all_messages()
        input_msg = input("You: ")
        print()

    print("exitting")
