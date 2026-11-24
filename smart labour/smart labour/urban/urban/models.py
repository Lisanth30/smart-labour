from dataclasses import dataclass

# simple data container representing a row from the customers table
@dataclass
class Customer:
    id: int
    full_name: str
    email: str
    phone: str = None
    address: str = None

    @classmethod
    def from_record(cls, record: dict):
        return cls(
            id=record['id'],
            full_name=record['full_name'],
            email=record['email'],
            phone=record.get('phone'),
            address=record.get('address')
        )
