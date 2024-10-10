from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session

from config import get_db, engine, Base
from models import Credit, Payment, User, Dictionary, Plan

credits_app = FastAPI()

Base.metadata.create_all(bind=engine)


@credits_app.get("/user_credits/{user_id}")
def get_user_credits(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    credits = db.query(Credit).filter(Credit.user_id == user_id).all()
    result = []
    for credit in credits:
        if credit.actual_return_date:
            payments = db.query(Payment).filter(Payment.credit_id == credit.id).all()
            sum_payment = sum(payment.sum for payment in payments)
            result.append({
                "issuance_date": credit.issuance_date,
                "is_closed": True,
                "return_date": credit.actual_return_date,
                "body": credit.body,
                "percent": credit.percent,
                "total_payments": sum_payment
            })
        else:
            overdue_days = (credit.return_date - credit.issuance_date).days
            body_payments = sum(a.sum for a in credit.payments if a.type_id == 1)
            percent_payments = sum(a.sum for a in credit.payments if a.type_id == 2)
            result.append({
                "issuance_date": credit.issuance_date,
                "is_closed": False,
                "return_date": credit.return_date,
                "overdue_days": overdue_days,
                "body": credit.body,
                "percent": credit.percent,
                "body_payments": body_payments,
                "percent_payments": percent_payments
            })

    return result


@credits_app.post("/plans_insert")
async def plans_insert(file: UploadFile = File(), db: Session = Depends(get_db)):
    df = pd.read_excel(file.file)

    if not all(df['period'].dt.day == 1):
        raise HTTPException(status_code=400, detail="Must be first number of month")

    for index, row in df.iterrows():
        category = db.query(Dictionary).filter(Dictionary.name == row['category']).first()
        if not category:
            raise HTTPException(status_code=400, detail=f"Category {row['category']} not found")

        existing_plan = db.query(Plan).filter(Plan.period == row['period'], Plan.category_id == category.id).first()
        if existing_plan:
            raise HTTPException(status_code=400, detail="Plan for this period and category already exists")

        new_plan = Plan(period=row['period'], sum=row['sum'], category_id=category.id)
        db.add(new_plan)

    db.commit()
    return {"detail": "Plans successfully added"}


@credits_app.get("/plans_performance")
def get_plans_performance(date: str, db: Session = Depends(get_db)):
    from datetime import datetime
    query_date = datetime.strptime(date, "%Y-%m-%d").date()

    plans = db.query(Plan).filter(Plan.period <= query_date).all()

    result = []
    for plan in plans:
        category = db.query(Dictionary).filter(Dictionary.id == plan.category_id).first().name

        if category == "Видача":
            # Сума виданих кредитів за період
            issued_credits_sum = db.query(Credit).filter(
                Credit.issuance_date >= plan.period,
                Credit.issuance_date <= query_date
            ).with_entities(func.sum(Credit.body)).scalar() or 0
            performance = (issued_credits_sum / plan.sum) * 100 if plan.sum != 0 else 0
        elif category == "Збір":
            # Сума платежів за період
            collected_payments_sum = db.query(Payment).join(Credit).filter(
                Credit.issuance_date >= plan.period,
                Payment.payment_date <= query_date
            ).with_entities(func.sum(Payment.sum)).scalar() or 0
            performance = (collected_payments_sum / plan.sum) * 100 if plan.sum != 0 else 0

        result.append({
            "plan_month": plan.period,
            "category": category,
            "plan_sum": plan.sum,
            "achieved_sum": issued_credits_sum if category == "Видача" else collected_payments_sum,
            "performance_percent": performance
        })
    return result


@credits_app.get("/year_performance/{year}")
def get_year_performance(year: int, db: Session = Depends(get_db)):
    from datetime import datetime
    start_date = datetime(year, 1, 1)
    end_date = datetime(year, 12, 31)

    # Суми виданих кредитів і платежів за рік
    year_credits_sum = db.query(func.sum(Credit.body)).filter(
        Credit.issuance_date >= start_date,
        Credit.issuance_date <= end_date
    ).scalar() or 0
    year_payments_sum = db.query(func.sum(Payment.sum)).join(Credit).filter(
        Payment.payment_date >= start_date,
        Payment.payment_date <= end_date
    ).scalar() or 0

    # Отримання планів за кожен місяць року
    result = []
    for month in range(1, 13):
        month_start = datetime(year, month, 1)
        month_end = datetime(year, month + 1, 1) if month < 12 else end_date

        # Сума виданих кредитів за місяць
        monthly_credits_sum = db.query(func.sum(Credit.body)).filter(
            Credit.issuance_date >= month_start,
            Credit.issuance_date < month_end
        ).scalar() or 0

        # Сума платежів за місяць
        monthly_payments_sum = db.query(func.sum(Payment.sum)).join(Credit).filter(
            Payment.payment_date >= month_start,
            Payment.payment_date < month_end
        ).scalar() or 0

        # Отримання планів видачі та збору за місяць
        issuance_plan = db.query(Plan).join(Dictionary).filter(
            Plan.period == month_start,
            Dictionary.name == "Видача"
        ).first()
        collection_plan = db.query(Plan).join(Dictionary).filter(
            Plan.period == month_start,
            Dictionary.name == "Збір"
        ).first()

        issuance_plan_sum = issuance_plan.sum if issuance_plan else 0
        collection_plan_sum = collection_plan.sum if collection_plan else 0

        issuance_performance = (monthly_credits_sum / issuance_plan_sum * 100) if issuance_plan_sum else 0
        collection_performance = (monthly_payments_sum / collection_plan_sum * 100) if collection_plan_sum else 0

        result.append({
            "month": month_start.strftime("%Y-%m"),
            "issuance_count": db.query(Credit).filter(
                Credit.issuance_date >= month_start,
                Credit.issuance_date < month_end
            ).count(),
            "issuance_plan_sum": issuance_plan_sum,
            "monthly_issuance_sum": monthly_credits_sum,
            "issuance_performance_percent": issuance_performance,
            "payment_count": db.query(Payment).filter(
                Payment.payment_date >= month_start,
                Payment.payment_date < month_end
            ).count(),
            "collection_plan_sum": collection_plan_sum,
            "monthly_payments_sum": monthly_payments_sum,
            "collection_performance_percent": collection_performance,
            "issuance_percent_of_year": (monthly_credits_sum / year_credits_sum * 100) if year_credits_sum else 0,
            "payments_percent_of_year": (monthly_payments_sum / year_payments_sum * 100) if year_payments_sum else 0
        })

    return result

