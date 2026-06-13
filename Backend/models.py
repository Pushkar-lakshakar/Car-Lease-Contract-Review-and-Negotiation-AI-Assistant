from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from Backend.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, nullable=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    # Role is strictly 'client' for this table now
    full_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    contracts = relationship("Contract", back_populates="user", foreign_keys="Contract.user_id")
    rooms = relationship("NegotiationRoom", back_populates="client", foreign_keys="NegotiationRoom.client_id")
    # messages relationship updated to a more generic form or handled via logic

class Dealer(Base):
    __tablename__ = "dealers"

    id = Column(String, primary_key=True, default=generate_uuid)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=True)
    
    # Business Info
    name = Column(String, nullable=True) # Dealership Name
    address_line1 = Column(String, nullable=True)
    address_line2 = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    postal_code = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    website = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    contracts = relationship("Contract", back_populates="dealer", foreign_keys="Contract.dealer_id")
    rooms = relationship("NegotiationRoom", back_populates="dealer", foreign_keys="NegotiationRoom.dealer_id")

class Lender(Base):
    __tablename__ = "lenders"

    id = Column(String, primary_key=True, default=generate_uuid)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=True)
    
    # Financial Institution Info
    name = Column(String, nullable=True)
    nmls_id = Column(String, nullable=True)
    website = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    address = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    contracts = relationship("Contract", back_populates="lender", foreign_keys="Contract.lender_id")

class Vehicle(Base):
    __tablename__ = "vehicles"

    vin = Column(String, primary_key=True)
    make = Column(String, nullable=True)
    model = Column(String, nullable=True)
    year = Column(Integer, nullable=True)
    trim = Column(String, nullable=True)
    mileage = Column(Float, nullable=True)
    condition = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    contracts = relationship("Contract", back_populates="vehicle")

class VehicleApiCache(Base):
    __tablename__ = "vehicle_api_cache"

    vin = Column(String, primary_key=True)
    api_response = Column(JSON, nullable=False)
    cached_at = Column(DateTime(timezone=True), server_default=func.now())

class Contract(Base):
    __tablename__ = "contracts"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=True) # Linked to Client
    dealer_id = Column(String, ForeignKey("dealers.id"), nullable=True) # Linked to Dealer
    lender_id = Column(String, ForeignKey("lenders.id"), nullable=True) # Linked to Lender
    vehicle_vin = Column(String, ForeignKey("vehicles.vin"), nullable=True)
    
    status = Column(String, default="draft") # draft, analyzed, negotiating, signed
    contract_date = Column(DateTime(timezone=True), nullable=True)
    
    # File info
    original_filename = Column(String, nullable=True)
    file_path = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="contracts")
    dealer = relationship("Dealer", foreign_keys=[dealer_id], back_populates="contracts")
    lender = relationship("Lender", foreign_keys=[lender_id], back_populates="contracts")
    vehicle = relationship("Vehicle", back_populates="contracts")
    sla = relationship("ContractSLA", uselist=False, back_populates="contract", cascade="all, delete-orphan")
    negotiation_room = relationship("NegotiationRoom", uselist=False, back_populates="contract")

class ContractSLA(Base):
    __tablename__ = "contract_slas"

    id = Column(String, primary_key=True, default=generate_uuid)
    contract_id = Column(String, ForeignKey("contracts.id"), nullable=False)
    
    # Financials
    monthly_payment = Column(Float, nullable=True)
    down_payment = Column(Float, nullable=True)
    term_months = Column(Integer, nullable=True)
    annual_mileage = Column(Integer, nullable=True)
    residual_value = Column(Float, nullable=True)
    money_factor = Column(Float, nullable=True)
    
    # Analysis
    score = Column(Float, nullable=True) # 0-100
    risk_level = Column(String, nullable=True) # Low, Medium, High
    extracted_data = Column(JSON, nullable=True) # Full raw JSON extraction
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    contract = relationship("Contract", back_populates="sla")

class NegotiationRoom(Base):
    __tablename__ = "negotiation_rooms"

    id = Column(String, primary_key=True, default=generate_uuid)
    contract_id = Column(String, ForeignKey("contracts.id"), nullable=False)
    client_id = Column(String, ForeignKey("users.id"), nullable=True)
    dealer_id = Column(String, ForeignKey("dealers.id"), nullable=True)
    
    name = Column(String, nullable=True)
    status = Column(String, default="active")
    access_code = Column(String(6), unique=True, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    contract = relationship("Contract", back_populates="negotiation_room")
    client = relationship("User", foreign_keys=[client_id], back_populates="rooms")
    dealer = relationship("Dealer", foreign_keys=[dealer_id], back_populates="rooms")
    messages = relationship("NegotiationMessage", back_populates="room", cascade="all, delete-orphan")

class NegotiationMessage(Base):
    __tablename__ = "negotiation_messages"

    id = Column(String, primary_key=True, default=generate_uuid)
    room_id = Column(String, ForeignKey("negotiation_rooms.id"), nullable=False)
    
    # We use sender_id as a string to reference any of the account tables
    sender_id = Column(String, nullable=False)
    sender_role = Column(String, nullable=False) # client, dealer, ai
    content = Column(Text, nullable=False)
    is_ai_generated = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    room = relationship("NegotiationRoom", back_populates="messages")
