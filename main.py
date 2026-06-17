from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, String, select

from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    sessionmaker
)
import jwt
import bcrypt

from datetime import (
    datetime,
    timedelta,
    timezone
)

app = FastAPI()

SECRET_KEY = "my_secret_key"

ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 60

templates = Jinja2Templates(directory="Frontend")

# Database

engine = create_engine(
    "sqlite:///expenses.db",
    connect_args={"check_same_thread": False} #Allow the database connection to
                                             # be used by multiple threads.
)

SessionLocal = sessionmaker(bind=engine)

def get_password_hash(password):

    return bcrypt.hashpw(
        password.encode(),
        bcrypt.gensalt()
    ).decode()


def verify_password(
    plain_password,
    hashed_password
):

    return bcrypt.checkpw(
        plain_password.encode(),
        hashed_password.encode()
    )

def create_access_token(data: dict):

    expire = (
        datetime.now(timezone.utc)
        + timedelta(minutes=60)
    )

    data.update(
        {"exp": expire}
    )

    return jwt.encode(
        data,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

class Base(DeclarativeBase):
    pass

class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(String(50))

    amount: Mapped[float]

    category: Mapped[str] = mapped_column(String(30))

    date: Mapped[str] = mapped_column(String(20))


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    username: Mapped[str] = mapped_column(
        String(50),
        unique=True
    )

    password: Mapped[str] = mapped_column(
        String(255)
    )

Base.metadata.create_all(bind=engine)

@app.get("/signup", response_class=HTMLResponse)
def signup_page(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="signup.html"
    )

@app.post("/signup")
def signup(
    username: str = Form(...),
    password: str = Form(...)
):
    db = SessionLocal()

    existing_user = db.scalars(
        select(User).where(
            User.username == username
        )
    ).first()

    if existing_user:
        db.close()
        return {
            "message": "Username already exists"
        }

    user = User(
        username=username,
        password=get_password_hash(password)
    )

    db.add(user)
    db.commit()
    db.close()

    return RedirectResponse(
        url="/login",
        status_code=303
    )

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="login.html"
    )

@app.post("/login")
def login(
    username: str = Form(...),
    password: str = Form(...)
):

    db = SessionLocal()

    user = db.scalars(
        select(User).where(
            User.username == username
        )
    ).first()

    if user and verify_password(
        password,
        user.password
    ):

        token = create_access_token(
            {"sub": username}
        )

        response = RedirectResponse(

            url="/",

            status_code=303

        )

        response.set_cookie(

            key="access_token",

            value=token

        )

        return response

    return {

        "message": "Invalid username or password"

    }

def get_current_user(request: Request):

    token = request.cookies.get(
        "access_token"
    )

    if not token:
        return None

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        return payload.get("sub")

    except:

        return None
    
def get_current_user(request: Request):

    token = request.cookies.get(
        "access_token"
    )

    if not token:
        return None

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        return payload.get("sub")

    except:

        return None
    
@app.get("/logout")
def logout():

    response = RedirectResponse(
        url="/login",
        status_code=303
    )

    response.delete_cookie(
        "access_token"
    )

    return response
# Home Page

@app.get("/", response_class=HTMLResponse)
def home(request: Request):

    current_user = get_current_user(
        request
    )

    if not current_user:

        return RedirectResponse(
            url="/login",
            status_code=303
        )

    db = SessionLocal()

    expenses = db.scalars(
        select(Expense)
    ).all()

    total = sum(
        expense.amount
        for expense in expenses
    )

    db.close()

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "expenses": expenses,
            "total": total
        }
    )

# Create Page

@app.get("/create", response_class=HTMLResponse)
def create_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="create.html"
    )

@app.post("/create")
def create_expense(
    title: str = Form(...),
    amount: float = Form(...),
    category: str = Form(...),
    date: str = Form(...)
):
    db = SessionLocal()

    expense = Expense(
        title=title,
        amount=amount,
        category=category,
        date=date
    )

    db.add(expense)
    db.commit()
    db.close()

    return RedirectResponse(
    url="/",
    status_code=303
)

@app.get("/delete/{expense_id}")
def delete_expense(expense_id: int):

    db = SessionLocal()

    expense = db.get(Expense, expense_id)

    if expense:
        db.delete(expense)
        db.commit()

    db.close()

    return RedirectResponse(
        url="/",
        status_code=303
    )

@app.get("/update/{expense_id}", response_class=HTMLResponse)
def update_page(
    request: Request,
    expense_id: int
):
    db = SessionLocal()

    expense = db.get(
        Expense,
        expense_id
    )

    db.close()

    return templates.TemplateResponse(
        request=request,
        name="update.html",
        context={"expense": expense}
    )

@app.post("/update/{expense_id}")
def update_expense(
    expense_id: int,
    title: str = Form(...),
    amount: float = Form(...),
    category: str = Form(...),
    date: str = Form(...)
):
    db = SessionLocal()   #creates a database session.

    expense = db.get(
        Expense,
        expense_id
    )

    if expense:
        expense.title = title
        expense.amount = amount
        expense.category = category
        expense.date = date

        db.commit()

    db.close()

    return RedirectResponse(
        url="/",
        status_code=303
    )