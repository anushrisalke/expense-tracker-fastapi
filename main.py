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

app = FastAPI()

templates = Jinja2Templates(directory="Frontend")

# Database

engine = create_engine(
    "sqlite:///expenses.db",
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass

class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(String(50))

    amount: Mapped[float]

    category: Mapped[str] = mapped_column(String(30))

    date: Mapped[str] = mapped_column(String(20))

Base.metadata.create_all(bind=engine)

# Home Page

@app.get("/", response_class=HTMLResponse)
def home(request: Request):

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
        context={"expenses": expenses,
                 "total":total}
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
    db = SessionLocal()

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