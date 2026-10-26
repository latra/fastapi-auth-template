from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db
from dependencies import get_current_user
from schemas import TokenResponse, UserRegister, UserResponse
from services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(body: UserRegister, db: AsyncSession = Depends(get_db)):
    return await auth_service.register(db, body)


@router.post("/login", response_model=TokenResponse)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    return await auth_service.login(db, form.username, form.password)


@router.get("/me", response_model=UserResponse)
async def me(current_user=Depends(get_current_user)):
    return current_user


if settings.google.enabled:
    import secrets
    from urllib.parse import urlencode

    from fastapi import Request
    from fastapi.responses import RedirectResponse
    from services import google_auth_service
    from services.google_auth_service import GoogleAuthError

    _STATE_COOKIE = "google_oauth_state"
    _STATE_COOKIE_PATH = "/auth/google"

    def _frontend_redirect(**fragment: str) -> RedirectResponse:
        response = RedirectResponse(f"{settings.google.frontend_url}/#{urlencode(fragment)}")
        response.delete_cookie(_STATE_COOKIE, path=_STATE_COOKIE_PATH)
        return response

    @router.get("/google/login", summary="Redirect to Google OAuth consent screen")
    async def google_login():
        state = google_auth_service.generate_state()
        response = RedirectResponse(google_auth_service.build_authorization_url(state))
        response.set_cookie(
            _STATE_COOKIE,
            state,
            max_age=600,
            path=_STATE_COOKIE_PATH,
            httponly=True,
            secure=settings.google.redirect_uri.startswith("https://"),
            samesite="lax",
        )
        return response

    @router.get("/google/callback", summary="Google OAuth callback")
    async def google_callback(
        request: Request,
        code: str | None = None,
        state: str | None = None,
        error: str | None = None,
        db: AsyncSession = Depends(get_db),
    ):
        # Google sends ?error=access_denied when the user cancels the consent screen
        if error:
            return _frontend_redirect(error=error)

        expected_state = request.cookies.get(_STATE_COOKIE)
        if not state or not expected_state or not secrets.compare_digest(state, expected_state):
            return _frontend_redirect(error="invalid_state")
        if not code:
            return _frontend_redirect(error="missing_code")

        try:
            result = await google_auth_service.handle_callback(db, code)
        except GoogleAuthError as e:
            return _frontend_redirect(error=e.code)
        return _frontend_redirect(token=result.access_token)
