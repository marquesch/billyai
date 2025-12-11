import datetime
from dataclasses import dataclass

from pydantic_ai import Agent
from pydantic_ai import FunctionToolset
from pydantic_ai import RunContext

from domain.entities import Bill
from domain.entities import Category
from domain.entities import User
from domain.exceptions import CategoryAlreadyExistsException
from domain.exceptions import PhoneNumberTakenException
from domain.ports.repositories import BillRepository
from domain.ports.repositories import CategoryRepository
from domain.ports.repositories import TenantRepository
from domain.ports.repositories import UserRepository
from infrastructure.persistence.database import db_session


@dataclass
class AgentDependencies:
    user_repository: UserRepository
    bill_repository: BillRepository
    category_repository: CategoryRepository
    tenant_repository: TenantRepository
    phone_number: str
    user: User


agent = Agent(
    "deepseek:deepseek-chat",
    instructions="Talk to the user by his name only if he's registered. If the user is not registered yet, try to register him. Ask his name if it's not clear. Ask for user consent before registering him. Be polite, but concise in your messages. Avoid small talk. Avoind using the default category. Prefer to use a custom one instead.",
    deps_type=AgentDependencies,
)


def register_user(ctx: RunContext[AgentDependencies], user_name: str) -> User | None:
    """Registers a user into the database.

    Args:
        user_name (str): Name of the user
    Returns:
        User | None: User if user was successfully registered. None otherwise.

    """
    tenant = ctx.deps.tenant_repository.create()

    default_category = ctx.deps.category_repository.create(
        tenant.id,
        "default",
        "Default category, for everything that doesn't fit other categories",
    )

    try:
        ctx.deps.user = ctx.deps.user_repository.create(
            phone_number=ctx.deps.phone_number,
            name=user_name,
            tenant_id=tenant.id,
        )
        return ctx.deps.user
    except PhoneNumberTakenException:
        return None


def get_user_name(ctx: RunContext[str]) -> str:
    """Gets the name of the user.

    Returns:
        str: the name of the current user

    """
    return ctx.deps.user.name


def register_category(
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
        return ctx.deps.category_repository.create(ctx.deps.user.tenant_id, name, description)
    except CategoryAlreadyExistsException:
        return None


def get_all_categories(ctx: RunContext[AgentDependencies]) -> list[dict]:
    """Gets all categories from a tenant.

    Returns:
        list[Category]: A list of all categories from a tenant.

    """
    return ctx.deps.category_repository.get_all(ctx.deps.user.tenant_id)


def register_bill(
    ctx: RunContext[AgentDependencies],
    date: datetime.date,
    value: float,
    category_id: int,
) -> Bill:
    """Registers an expense for a user.

    Args:
        value (float): the value of the bill
        date (datetime.date): the date of the bill
        category_id (int): the id of a category to link the bill to

    Returns:
        Bill: A dataclass representing the bill

    """
    return ctx.deps.bill_repository.create(ctx.deps.user.tenant_id, date, value, category_id)


def edit_bill(
    ctx: RunContext[AgentDependencies],
    bill_id: int,
    date: datetime.date | None = None,
    value: float | None = None,
    category_id: int | None = None,
):
    """Edits a bill by its id

    Args:
        bill_id (int): the id of the bill to be editted
        date (datetime.date, optional): an optional new date for the bill.
        value (float, optional): an optional new value of the bill to edit,
        category_id (int, optional): an optional category_id to assign a new category.

    Returns:
        Bill: A dataclass representing the bill

    """
    return ctx.deps.bill_repository.update(ctx.deps.user.tenant_id, bill_id, date, value, category_id)


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
    return ctx.deps.bill_repository.get_many(ctx.deps.user.tenant_id, category_id, date_range, value_range)


def get_today():
    """Returns a date object representing the current day

    Return:
        datetime.date: a date representing the current day

    """
    return datetime.date.today()


registered_toolset = FunctionToolset(
    tools=[
        get_user_name,
        register_bill,
        get_bills,
        register_category,
        get_all_categories,
        edit_bill,
        get_today,
    ],
)
unregistered_toolset = FunctionToolset(tools=[register_user])

if __name__ == "__main__":
    from infrastructure.persistence.database.repositories.bill_repository import DBBillRepository
    from infrastructure.persistence.database.repositories.category_repository import DBCategoryRepository
    from infrastructure.persistence.database.repositories.tenant_repository import DBTenantRepository
    from infrastructure.persistence.database.repositories.user_repository import DBUserRepository

    phone_number = input("Phone number: ")

    with db_session() as session:
        user_repo = DBUserRepository(session)
        category_repo = DBCategoryRepository(session)
        bill_repo = DBBillRepository(session)
        tenant_repo = DBTenantRepository(session)

        user = user_repo.get_by_phone_number(phone_number)

        deps = AgentDependencies(
            user_repository=user_repo,
            bill_repository=bill_repo,
            category_repository=category_repo,
            user=user,
        )

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
