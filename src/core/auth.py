import os
from typing import Optional
from cryptography.fernet import Fernet
from sqlalchemy import create_engine, Column, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Credential(Base):
    __tablename__ = 'credentials'
    id = Column(String, primary_key=True) # Composite: service_name + account_id
    service_name = Column(String, nullable=False)
    account_id = Column(String, nullable=False)
    encrypted_value = Column(Text, nullable=False)

class SecretStore:
    def __init__(self, master_key: str):
        try:
            self.fernet = Fernet(master_key.encode())
        except Exception as e:
            raise ValueError(f"Invalid master key: {e}")

    def encrypt(self, value: str) -> str:
        return self.fernet.encrypt(value.encode()).decode()

    def decrypt(self, encrypted_value: str) -> str:
        return self.fernet.decrypt(encrypted_value.encode()).decode()

class CredentialManager:
    def __init__(self, db_path: str = "credentials.db", master_key: Optional[str] = None):
        if master_key is None:
            master_key = os.environ.get("PUBLISHER_MASTER_KEY")
        
        if not master_key:
            raise EnvironmentError("PUBLISHER_MASTER_KEY environment variable is not set")
            
        self.secret_store = SecretStore(master_key)
        self.engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def save_credential(self, service_name: str, account_id: str, value: str):
        encrypted_value = self.secret_store.encrypt(value)
        session = self.Session()
        try:
            # Use a composite ID to allow multiple accounts per service
            cred_id = f"{service_name}_{account_id}"
            cred = session.query(Credential).filter_by(id=cred_id).first()
            if cred:
                cred.encrypted_value = encrypted_value
            else:
                cred = Credential(id=cred_id, service_name=service_name, account_id=account_id, encrypted_value=encrypted_value)
                session.add(cred)
            session.commit()
        finally:
            session.close()

    def get_credential(self, service_name: str, account_id: str) -> Optional[str]:
        session = self.Session()
        try:
            cred_id = f"{service_name}_{account_id}"
            cred = session.query(Credential).filter_by(id=cred_id).first()
            if cred:
                return self.secret_store.decrypt(cred.encrypted_value)
            return None
        finally:
            session.close()
