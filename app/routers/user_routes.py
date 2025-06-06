"""
This Python file is part of a FastAPI application, demonstrating user management functionalities including creating, reading,
updating, and deleting (CRUD) user information. It uses OAuth2 with Password Flow for security, ensuring that only authenticated
users can perform certain operations. Additionally, the file showcases the integration of FastAPI with SQLAlchemy for asynchronous
database operations, enhancing performance by non-blocking database calls.

The implementation emphasizes RESTful API principles, with endpoints for each CRUD operation and the use of HTTP status codes
and exceptions to communicate the outcome of operations. It introduces the concept of HATEOAS (Hypermedia as the Engine of
Application State) by including navigational links in API responses, allowing clients to discover other related operations dynamically.

OAuth2PasswordBearer is employed to extract the token from the Authorization header and verify the user's identity, providing a layer
of security to the operations that manipulate user data.

Key Highlights:
- Use of FastAPI's Dependency Injection system to manage database sessions and user authentication.
- Demonstrates how to perform CRUD operations in an asynchronous manner using SQLAlchemy with FastAPI.
- Implements HATEOAS by generating dynamic links for user-related actions, enhancing API discoverability.
- Utilizes OAuth2PasswordBearer for securing API endpoints, requiring valid access tokens for operations.
"""

from builtins import dict, int, len, str
from datetime import timedelta
from uuid import UUID, uuid4
from io import BytesIO
import logging

from fastapi import APIRouter, Depends, HTTPException, Response, status, Request, UploadFile, File
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.dependencies import get_current_user, get_db, get_email_service, require_role, get_settings
from app.schemas.pagination_schema import EnhancedPagination
from app.schemas.token_schema import TokenResponse
from app.schemas.user_schemas import LoginRequest, UserBase, UserCreate, UserListResponse, UserResponse, UserUpdate
from app.services.user_service import UserService
from app.services.jwt_service import create_access_token
from app.services.email_service import EmailService
from app.utils.link_generation import create_user_links, generate_pagination_links
from app.utils.minio_client import upload_profile_picture, get_profile_picture_url
from app.models.user_model import User

logger = logging.getLogger(__name__)

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
settings = get_settings()


@router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    name="get_user",
    tags=["User Management Requires (Admin or Manager Roles)"]
)
async def get_user(
    user_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme),
    current_user: dict = Depends(require_role(["ADMIN", "MANAGER"]))
):
    user = await UserService.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return UserResponse.model_construct(
        id=user.id,
        nickname=user.nickname,
        first_name=user.first_name,
        last_name=user.last_name,
        bio=user.bio,
        profile_picture_url=user.profile_picture_url,
        github_profile_url=user.github_profile_url,
        linkedin_profile_url=user.linkedin_profile_url,
        role=user.role,
        email=user.email,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        updated_at=user.updated_at,
        links=create_user_links(user.id, request)
    )


@router.put(
    "/users/{user_id}",
    response_model=UserResponse,
    name="update_user",
    tags=["User Management Requires (Admin or Manager Roles)"]
)
async def update_user(
    user_id: UUID,
    user_update: UserUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme),
    current_user: dict = Depends(require_role(["ADMIN", "MANAGER"]))
):
    user_data = user_update.model_dump(exclude_unset=True)
    updated_user = await UserService.update(db, user_id, user_data)
    if not updated_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return UserResponse.model_construct(
        id=updated_user.id,
        bio=updated_user.bio,
        first_name=updated_user.first_name,
        last_name=updated_user.last_name,
        nickname=updated_user.nickname,
        email=updated_user.email,
        role=updated_user.role,
        last_login_at=updated_user.last_login_at,
        profile_picture_url=updated_user.profile_picture_url,
        github_profile_url=updated_user.github_profile_url,
        linkedin_profile_url=updated_user.linkedin_profile_url,
        created_at=updated_user.created_at,
        updated_at=updated_user.updated_at,
        links=create_user_links(updated_user.id, request)
    )


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    name="delete_user",
    tags=["User Management Requires (Admin or Manager Roles)"]
)
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme),
    current_user: dict = Depends(require_role(["ADMIN", "MANAGER"]))
):
    success = await UserService.delete(db, user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/users/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["User Management Requires (Admin or Manager Roles)"],
    name="create_user"
)
async def create_user(
    user: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    email_service: EmailService = Depends(get_email_service),
    token: str = Depends(oauth2_scheme),
    current_user: dict = Depends(require_role(["ADMIN", "MANAGER"]))
):
    existing_user = await UserService.get_by_email(db, user.email)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")

    created_user = await UserService.create(db, user.model_dump(), email_service)
    if not created_user:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create user")

    return UserResponse.model_construct(
        id=created_user.id,
        bio=created_user.bio,
        first_name=created_user.first_name,
        last_name=created_user.last_name,
        profile_picture_url=created_user.profile_picture_url,
        nickname=created_user.nickname,
        email=created_user.email,
        role=created_user.role,
        last_login_at=created_user.last_login_at,
        created_at=created_user.created_at,
        updated_at=created_user.updated_at,
        links=create_user_links(created_user.id, request)
    )


@router.get(
    "/users/",
    response_model=UserListResponse,
    tags=["User Management Requires (Admin or Manager Roles)"]
)
async def list_users(
    request: Request,
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(["ADMIN", "MANAGER"]))
):
    total_users = await UserService.count(db)
    users = await UserService.list_users(db, skip, limit)

    user_responses = [UserResponse.model_validate(user) for user in users]
    pagination_links = generate_pagination_links(request, skip, limit, total_users)

    return UserListResponse(
        items=user_responses,
        total=total_users,
        page=skip // limit + 1,
        size=len(user_responses),
        links=pagination_links
    )


@router.post("/register/", response_model=UserResponse, tags=["Login and Registration"])
async def register(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_db),
    email_service: EmailService = Depends(get_email_service)
):
    user = await UserService.register_user(session, user_data.model_dump(), email_service)
    if user:
        return user
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")


@router.post("/login/", response_model=TokenResponse, tags=["Login and Registration"])
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_db)
):
    if await UserService.is_account_locked(session, form_data.username):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Account locked due to too many failed login attempts.")

    user = await UserService.login_user(session, form_data.username, form_data.password)
    if user:
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": user.email, "role": str(user.role.name), "id": str(user.id)},
            expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password.")


@router.post("/login/", include_in_schema=False, response_model=TokenResponse, tags=["Login and Registration"])
async def login_hidden(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_db)
):
    if await UserService.is_account_locked(session, form_data.username):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Account locked due to too many failed login attempts.")

    user = await UserService.login_user(session, form_data.username, form_data.password)
    if user:
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": user.email, "role": str(user.role.name), "id": str(user.id)},
            expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password.")


@router.get(
    "/verify-email/{user_id}/{token}",
    status_code=status.HTTP_200_OK,
    name="verify_email",
    tags=["Login and Registration"]
)
async def verify_email(
    user_id: UUID,
    token: str,
    db: AsyncSession = Depends(get_db),
    email_service: EmailService = Depends(get_email_service)
):
    if await UserService.verify_email_with_token(db, user_id, token):
        return {"message": "Email verified successfully"}
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired verification token")


@router.get("/profile-picture/{file_name}")
def get_profile_picture(file_name: str):
    try:
        url = get_profile_picture_url(file_name)
        return {"url": url}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post(
    "/users/me/upload-profile-picture",
    status_code=status.HTTP_200_OK,
    name="upload_profile_picture",
    tags=["User Management Requires Authenticated Users"],
)
async def upload_profile_picture_endpoint(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _=Depends(require_role(["ADMIN", "MANAGER", "AUTHENTICATED"]))
):
    """
    Uploads a profile picture to MinIO and updates the user's profile_picture_url in the database.
    """
    try:
        # 1) Validate file type
        if not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Only images are allowed."
            )

        # 2) Read file into memory so we know its length
        data = await file.read()
        stream = BytesIO(data)

        # 3) Build a secure filename: <user_id>.<ext>
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not identify current user."
            )
        ext = file.filename.rsplit(".", 1)[-1]
        secure_filename = f"{user_id}.{ext}"

        # 4) Upload to MinIO
        url = upload_profile_picture(stream, secure_filename)
        logger.info(f"Uploaded '{secure_filename}' to MinIO: {url}")

        # 5) Fetch and update the user record
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found in database."
            )

        user.profile_picture_url = url
        db.add(user)
        await db.commit()
        await db.refresh(user)
        logger.info(f"Updated DB for user {user_id}: profile_picture_url = {url}")

        return {
            "message": "Profile picture uploaded successfully.",
            "profile_picture_url": url
        }

    except HTTPException:
        raise

    except Exception as exc:
        # Log full traceback
        logger.error("upload_profile_picture_endpoint failed", exc_info=True)
        try:
            await db.rollback()
        except Exception:
            logger.warning("Failed to rollback DB session after error", exc_info=True)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload image: {str(exc)}"
        )
