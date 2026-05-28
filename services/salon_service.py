from models.salon import Salon
from models.service import Service
from repositories.salon_repository import SalonRepository
from repositories.salon_service_repository import SalonServiceRepository
from services.errors import SalonError


class SalonService:

    @staticmethod
    def count() -> int:
        return SalonRepository.count()

    @staticmethod
    def get_all() -> list[Salon]:
        return SalonRepository.get_all()

    @staticmethod
    def search(
        name_kw: str = "",
        city_kw: str = "",
        service_id: int | None = None,
    ) -> list[Salon]:
        return SalonRepository.search(name_kw, city_kw, service_id)

    @staticmethod
    def create(name: str, address: str, city: str, phone: str, email: str) -> Salon:
        name    = name.strip()
        address = address.strip()
        city    = city.strip()
        phone   = phone.strip() or None
        email   = email.strip() or None

        errors = []
        if not name:
            errors.append("Το όνομα κομμωτηρίου είναι υποχρεωτικό.")
        if not address:
            errors.append("Η διεύθυνση είναι υποχρεωτική.")
        if not city:
            errors.append("Η πόλη είναι υποχρεωτική.")
        if errors:
            raise SalonError("\n".join(errors))

        if email and "@" not in email:
            raise SalonError("Το email δεν είναι έγκυρο.")

        salon_id = SalonRepository.create(name, address, city, phone, email)
        return Salon(
            id=salon_id,
            name=name, address=address, city=city,
            phone=phone, email=email,
            is_active=True,
        )

    @staticmethod
    def toggle_active(salon_id: int) -> bool:
        salon = SalonRepository.get_by_id(salon_id)
        if not salon:
            raise SalonError("Το κομμωτήριο δεν βρέθηκε.")
        new_state = not salon.is_active
        SalonRepository.set_active(salon_id, new_state)
        return new_state

    @staticmethod
    def get_services(salon_id: int) -> list[Service]:
        return SalonServiceRepository.get_assigned(salon_id)

    @staticmethod
    def get_available_services(salon_id: int) -> list[Service]:
        return SalonServiceRepository.get_available(salon_id)

    @staticmethod
    def add_service(salon_id: int, service_id: int) -> None:
        SalonServiceRepository.add(salon_id, service_id)

    @staticmethod
    def remove_service(salon_id: int, service_id: int) -> None:
        SalonServiceRepository.remove(salon_id, service_id)

    @staticmethod
    def get_employees(salon_id: int) -> list[dict]:
        return SalonRepository.get_employees(salon_id)