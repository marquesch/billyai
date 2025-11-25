import datetime
from dataclasses import dataclass

from cfg import Session
from models import Bill
from models import Category
from models import Tenant
from models import User
from pydantic_ai import Agent
from pydantic_ai import FunctionToolset
from pydantic_ai import RunContext


@dataclass
class AgentDependencies:
    phone_number: str
    user: User | None
    db_session: Session


agent = Agent(
    "deepseek:deepseek-chat",
    instructions="Talk to the user by his name only if he's registered. If the user is not registered yet, try to register him. Ask his name if it's not clear. Ask for user consent before registering him. Be polite, but concise in your messages. Avoid small talk.",
    deps_type=AgentDependencies,
)


def register_user(ctx: RunContext[AgentDependencies], user_name: str) -> str:
    """Registers a user into the database.

    Args:
        user_name (str): Name of the user
    Returns:
        bool: True if user was registered. False otherwise.

    """
    session = ctx.deps.db_session
    phone_number = ctx.deps.phone_number

    if ctx.deps.user is not None:
        return False

    tenant = Tenant()
    default_category = Category(
        name="default",
        description="Default category for anything that doesn't fit other categories.",
        tenant=tenant,
    )
    user = User(phone_number=ctx.deps.phone_number, name=user_name, tenant=tenant)

    session.add_all([user, default_category, tenant])
    session.commit()
    session.refresh(user)

    ctx.deps.user = user

    return True


def get_user_name(ctx: RunContext[str]) -> str:
    """Gets the name of the user.

    Returns:
        str: the name of the current user

    """
    return ctx.deps.user.name


def register_category(
    ctx: RunContext[AgentDependencies], name: str, description: str
) -> str:
    """Registers a category for a user.

    Args:
        name (str): the name of the category
        description (str): a description of the category
    Returns:
        bool: True if category was registered. False otherwise.

    """
    session = ctx.deps.db_session
    tenant_id = ctx.deps.user.tenant_id

    category = Category.create(session, tenant_id, name, description)

    return category is not None


def get_categories(ctx: RunContext[AgentDependencies]):
    """Gets all categories from a tenant.

    Returns:
        list[dict]: A list of all categories from a tenant.

    """
    session = ctx.deps.db_session
    tenant_id = ctx.deps.user.tenant_id

    categories = Category.get_all(session, tenant_id)

    return [category.to_dict() for category in categories]


def register_bill(
    ctx: RunContext[AgentDependencies],
    date: datetime.datetime,
    value: float,
    category_id: int,
):
    """Registers a bill for a user.

    Args:
        value (float): the value of the bill
        date: (datetime.datetime): the date of the bill

    Returns:
        Bill: the registered bill

    """
    session = ctx.deps.db_session
    tenant_id = ctx.deps.user.tenant_id
    bill = Bill(tenant_id=tenant_id, value=value, date=date, category_id=category_id)

    session.add(bill)
    session.commit()
    session.refresh(bill)

    return f"Bill registered. value: {bill.value}, date: {bill.date}"


def edit_bill(
    ctx: RunContext[AgentDependencies],
    bill_id: int,
    date: datetime.datetime | None,
    value: float | None,
    category_id: int | None,
):
    """Edits a bill by its id

    Args:
        bill_id (int): the id of the bill to be editted
        date (datetime.datetime | None): the date to edit
        value (float | None): the value of the bill to edit,
        category_id (int | None): the id of category to edit

    Returns:
        str: explanation of the reason it failed or success

    """
    session = ctx.deps.db_session
    tenant_id = ctx.deps.user.tenant_id

    bill = Bill.get_by_id(session, tenant_id, bill_id)

    if date is not None:
        bill.date = date

    if value is not None:
        bill.value = value

    if category_id is not None:
        category = Category.get_by_id(session, tenant_id, category_id)

    session.commit()
    session.refresh(bill)

    return bill.to_dict()


def get_all_bills(ctx: RunContext[AgentDependencies]) -> str | list[dict]:
    session = ctx.deps.db_session
    user = ctx.deps.user
    if user is None:
        return "User is not yet registered"

    bills = Bill.get_all(session, user.tenant_id)
    bills = user.tenant.bills

    return [bill.to_dict() for bill in bills]


registered_toolset = FunctionToolset(
    tools=[
        get_user_name,
        register_bill,
        get_all_bills,
        register_category,
        get_categories,
        edit_bill,
    ],
)
unregistered_toolset = FunctionToolset(tools=[register_user])

if __name__ == "__main__":
    user_phone_number = input("Phone number: ")

    with Session() as session:
        user = User.get_by_phone_number(session, user_phone_number)
        print(f"User is {'REGISTERED' if user is not None else 'UNREGISTERED'}")

        deps = AgentDependencies(
            phone_number=user_phone_number,
            user=user,
            db_session=session,
        )

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
