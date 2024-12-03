from fastapi import HTTPException, Depends, APIRouter, status, Response
from sqlalchemy.orm import Session
from sqlalchemy.future import select
import bcrypt
from src.database import get_db  # Database dependency
from src.user.models import User
from src.user.schemas import UserSignupResponse, UserSignupRequest, UserLoginRequest, UserLoginResponse, newPasswordDataRequest, ResetPasswordRequest
import requests
import os
from fastapi.responses import HTMLResponse
from src.config import get_settings
from src.user.constants import HTML_RESPONSE_SUCCESS, HTML_RESPONSE_ERROR
from src.user.exceptions import UnauthenticatedLoginException, BadTokenException
import jwt
from datetime import timedelta, datetime
# User router
user_router = APIRouter()
settings = get_settings()


@user_router.post("/signup", response_model=UserSignupResponse)
def signup(user: UserSignupRequest, db: Session = Depends(get_db)):
    """
        Handles user signup requests.
        Validates input data and saves the user to the database.
        Returns success or error response.
        """

    result = db.execute(select(User).where(User.email == user.email))
    existing_user = result.scalars().first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists."
        )

    # Hash and salt the password
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), salt)

    new_user = User(
        email=user.email,
        password=hashed_password.decode('utf-8'),
        first_name=user.firstName,
        last_name=user.lastName,
        verify_secret=os.urandom(6).hex(),
        verified=False,
    )
    try:
        db.add(new_user)
        db.commit()

        # Refresh the instance to ensure the ID is populated
        db.refresh(new_user)

        # Send email verification
        postmark_response = requests.post(
            "https://api.postmarkapp.com/email/withTemplate",
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-Postmark-Server-Token": settings.POSTMARK_API_TOKEN
            },
            json={
                "From": "noreply@aipdet.com",
                "To": new_user.email,
                "TemplateId": 38173126,  # Replace with your actual template ID
                "TemplateModel": {
                    "name": new_user.first_name + ' ' + new_user.last_name,
                    "action_url": f"{settings.BASE_URL}/api/user/verify-email?user={new_user.id}&secret={new_user.verify_secret}",
                    "product_name": "AIPDET",
                    "product_url": "www.aipdet.com",
                    "company_name": "AIPDET",
                }
            }
        )

        # Check for success
        if postmark_response.status_code != 200:
            print("Failed to send email verification:", postmark_response.text)
            raise HTTPException(
                status_code=500,
                detail="User was created, but the email verification failed to send."
            )

        return {"message": "User successfully registered.", "userId": str(new_user.id)}

    except Exception as e:
        # Catch-all for unexpected errors
        print(e)
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@user_router.post("/login", response_model=UserLoginResponse)
def login(user: UserLoginRequest, response: Response, db: Session = Depends(get_db)):
    """
    Handles user login requests.
    Validates user credentials and sets a JWT as a secure cookie.
    """
    # Fetch the user from the database
    db_user = db.execute(select(User).where(
        User.email == user.email)).scalars().first()

    if not db_user:
        raise UnauthenticatedLoginException

    # Verify the password
    if not bcrypt.checkpw(user.password.encode('utf-8'), db_user.password.encode('utf-8')):
        raise UnauthenticatedLoginException

    # Ensure the account is verified
    if not db_user.verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please check your inbox."
        )

    # Generate JWT token
    jwt_payload = {
        "sub": str(db_user.id),
        "email": db_user.email,
        "firstName": db_user.first_name,
        "lastName": db_user.last_name,
    }
    # Replace with a secure secret key
    jwt_secret = os.getenv("JWT_SECRET", "your_jwt_secret")
    jwt_algorithm = "HS256"
    token = jwt.encode(jwt_payload, jwt_secret, algorithm=jwt_algorithm)

    # Set the token in a secure cookie
    response.set_cookie(
        key="auth_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="Strict",
        max_age=14400  # 4 hours
    )

    return {"message": "Login successful."}


@user_router.get("/verify-email", response_class=HTMLResponse)
def verify_email(user: str, secret: str, db: Session = Depends(get_db)):
    """
    Handles user email validation.
    Validates email by comparing verify secrets.
    """
    try:
        result = db.get(User, user)
    except Exception:
        return HTML_RESPONSE_ERROR

    if not result or result.verify_secret != secret:
        return HTML_RESPONSE_ERROR

    result.verified = True
    db.commit()
    db.refresh(result)

    return HTML_RESPONSE_SUCCESS


@user_router.post("/set-new-password")
def set_new_password(newPasswordData: newPasswordDataRequest, db: Session = Depends(get_db)
                     ):
    """
    Set a new password for the user.
    Validate the reset token, check expiration, and update the user's password.
    """

    user = db.get(User, newPasswordData.userId)

    if not user:
        print("User not found")
        raise BadTokenException

    if not user.reset_token == newPasswordData.token:
        print("Token mismatch")
        raise BadTokenException

    if user.reset_token_expiry < datetime.utcnow():
        print(user.reset_token_expiry)
        print(datetime.utcnow())
        print("Token expired")
        raise BadTokenException

    # Hash and set the new password
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(
        newPasswordData.password.encode('utf-8'), salt)
    user.password = hashed_password.decode('utf-8')

    # Clear the reset token and expiry fields
    user.reset_token = None
    user.reset_token_expiry = None

    db.commit()

    return {"message": "Password successfully updated. You can now log in with your new password."}


@user_router.post("/reset-password")
def reset_password(user_info: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Handles user password reset via email.
    Issues a token which the use can use to reset their password.
    """

    user = db.execute(select(User).where(
        User.email == user_info.email)).scalars().first()

    if not user:
        # always return success to avoid email scraping
        return {"message": "Password reset initiated"}

    # Generate a reset token
    user.reset_token = os.urandom(12).hex()
    user.reset_token_expiry = datetime.utcnow() + timedelta(hours=24)
    db.commit()
    db.refresh(user)

    postmark_response = requests.post(
        "https://api.postmarkapp.com/email/withTemplate",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Postmark-Server-Token": settings.POSTMARK_API_TOKEN
        },
        json={
            "From": "noreply@aipdet.com",
            "To": user.email,
            "TemplateId": 38232223,  # Replace with your actual template ID
            "TemplateModel": {
                "name": user.first_name + ' ' + user.last_name,
                "action_url": f"{settings.FRONTEND_BASE_URL}/auth/set-new-password?user={user.id}&token={user.reset_token}",
                "product_name": "AIPDET",
                "product_url": "www.aipdet.com",
                "company_name": "AIPDET",
            }
        }
    )

    # Check for success
    if postmark_response.status_code != 200:
        print("Failed to send email verification:", postmark_response.text)
        raise HTTPException(
            status_code=500,
            detail="User was created, but the email verification failed to send."
        )

    return {"message": "Password reset initiated"}
