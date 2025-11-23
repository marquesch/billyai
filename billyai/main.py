import datetime
import json
from dataclasses import dataclass

from cfg import Session
from models import Bill
from models import User
from pydantic_ai import Agent
from pydantic_ai import FunctionToolset
from pydantic_ai import RunContext


@dataclass
class AgentDependencies:
    phone_number: str
    user: User | None
    session: Session


agent = Agent(
    "deepseek:deepseek-chat",
    instructions="Talk to the user by his name only if he's registered. If the user is not registered yet, try to register him. Ask his name if it's not clear. Ask for user consent before registering him.",
    deps_type=AgentDependencies,
)


def register_user(ctx: RunContext[AgentDependencies], user_name: str) -> str:
    """Registers a user into the database.

    Args:
        user_name (str): Name of the user
    Returns:
        bool: True if user was registered. False otherwise.

    """
    user = User(phone_number=ctx.deps.phone_number, name=user_name)

    session = ctx.deps.session
    session.add(user)
    session.commit()
    session.refresh(user)

    ctx.deps.user = user

    return f"User {user.name} registered with phone number {user.phone_number}"


def get_user_name(ctx: RunContext[str]) -> str:
    """Gets the name of the user
    Returns:
        str: the name of the current user
    """
    return ctx.deps.user.name


def register_bill(ctx: RunContext[AgentDependencies], date: datetime.datetime, value: float):
    """Registers a bill for a user
    Args:
        value (float): the value of the bill
        date: (datetime.datetime): the date of the bill

    Returns:
        Bill: the registered bill

    """
    session = ctx.deps.session
    user_id = ctx.deps.user.id
    bill = Bill(user_id=user_id, value=value, date=date)

    session.add(bill)
    session.commit()
    session.refresh(bill)

    return f"Bill registered. value: {bill.value}, date: {bill.date}"


def get_all_bills(ctx: RunContext[AgentDependencies]) -> str:
    session = ctx.deps.session

    bills = Bill.get_all(session)
    return json.dumps([{"value": bill.value, "date": bill.date.isoformat()} for bill in bills])


registered_toolset = FunctionToolset(tools=[get_user_name, register_bill, get_all_bills])
unregistered_toolset = FunctionToolset(tools=[register_user])

if __name__ == "__main__":
    user_phone_number = input("Phone number: ")

    with Session() as session:
        user = User.get_by_phone_number(session, user_phone_number)
        print(f"User is {'REGISTERED' if user is not None else 'UNREGISTERED'}")

        deps = AgentDependencies(
            phone_number=user_phone_number,
            user=user,
            session=session,
        )

        input_msg = input("You: ")
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
            print()
            print(deps)
            print()
            print(f"LLM: {result.output}")
            message_history = result.all_messages()
            input_msg = input("You: ")

        print("exitting")
