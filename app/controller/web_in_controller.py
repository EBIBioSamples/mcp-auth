from fastapi import Request, Form, APIRouter
from fastapi.responses import HTMLResponse, RedirectResponse
from app.service.auth_service import AuthService

router = APIRouter()
auth_service = AuthService()

@router.get("/", response_class=HTMLResponse)
async def home():
    return RedirectResponse("/login", status_code=303)

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    message = request.session.pop("message", None)

    return auth_service.render_login(request,message=message)

@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    ):
    return await auth_service.web_in_token(request = request,
        username=username,password=password)