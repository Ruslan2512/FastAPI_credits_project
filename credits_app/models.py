from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey
from sqlalchemy.orm import relationship
from config import Base


class User(Base):
    __tablename__ = "Users"

    id = Column(Integer, primary_key=True, index=True)
    login = Column(String(50), unique=True, index=True)
    registration_date = Column(Date)

    credits = relationship("Credit", back_populates="user")


class Credit(Base):
    __tablename__ = "Credits"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("Users.id"))
    issuance_date = Column(Date)
    return_date = Column(Date)
    actual_return_date = Column(Date)
    body = Column(Float)
    percent = Column(Float)

    user = relationship("User", back_populates="credits")
    payments = relationship("Payment", back_populates="credit")


class Payment(Base):
    __tablename__ = "Payments"

    id = Column(Integer, primary_key=True, index=True)
    sum = Column(Float)
    payment_date = Column(Date)
    credit_id = Column(Integer, ForeignKey("Credits.id"))
    type_id = Column(Integer, ForeignKey("Dictionary.id"))

    credit = relationship("Credit", back_populates="payments")


class Plan(Base):
    __tablename__ = "Plans"

    id = Column(Integer, primary_key=True, index=True)
    period = Column(Date)
    sum = Column(Float)
    category_id = Column(Integer, ForeignKey("Dictionary.id"))


class Dictionary(Base):
    __tablename__ = "Dictionary"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50))
