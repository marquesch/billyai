from pydantic import BaseModel


class UserModel(BaseModel):
    phone_number: str
    name: str

