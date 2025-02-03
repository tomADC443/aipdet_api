from pydantic import BaseModel, EmailStr, Field


class UserSignupRequest(BaseModel):
    firstName: str = Field(
        ..., min_length=2, max_length=50,
        examples=["John"],
        description="The first name of the user."
    )
    lastName: str = Field(
        ..., min_length=2, max_length=50,
        examples=["Doe"],
        description="The last name of the user."
    )
    email: EmailStr = Field(
        ..., examples=["johndoe@example.com"],
        description="The user's email address."
    )
    password: str = Field(
        ..., min_length=8, max_length=254,
        examples=["StrongPassword123"],
        description="The user's password. Must be at least 8 characters long."
    )

# Request model


class UserLoginRequest(BaseModel):
    email: EmailStr = Field(
        ...,
        examples=["johndoe@example.com"],
        description="The user's email address."
    )
    password: str = Field(
        ...,
        max_length=254,
        examples=["StrongPassword123"],
        description="The user's password."
    )


class newPasswordDataRequest(BaseModel):

    token: str = Field(
        ...,
        min_length=1,
        examples=["1234456"],
        description="A temporary token to authorize the user to change their password."
    )

    userId: str = Field(

        ...,
        min_length=1,
        examples=['1234-1234-1234-1234'],
        description="The user's id (as submitted in the email action link)."
    )

    password: str = Field(
        ..., min_length=8, max_length=254,
        examples=["StrongPassword123"],
        description="The user's password. Must be at least 8 characters long."
    )


# Response model
class UserLoginResponse(BaseModel):
    message: str = Field(
        ...,
        examples=["Login successful"],
        description="A message indicating the outcome of the login operation."
    )
    expires: int = Field(
        ...,
        examples=["1733308210"],
        description="The date and time when the login token expires as unix timestamp (seconds)."
    )
    data: dict = Field(
        ...,
        examples={
            "sub": "1234-1234-1234-1234",
            "email": "some@email.com",
            "firstName": "John",
            "lastName": "Doe"
        },
        description="The user's data."
    )


class ResetPasswordRequest(BaseModel):
    email: EmailStr = Field(
        ...,
        examples=["johndoe@example.com"],
        description="The user's email address."
    )


class UserSignupResponse(BaseModel):
    message: str
    userId: str


class ErrorResponse(BaseModel):
    errorNote: str
