"""
EShopService — επιχειρηματική λογική για τα προϊόντα e-shop.
"""
import shutil
from pathlib import Path

from models.product import Product
from repositories.product_repository import ProductRepository
from services.errors import EShopError

_IMAGES_DIR = Path(__file__).parent.parent / "resources" / "product_images"
_ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}


class EShopService:

    @staticmethod
    def count() -> int:
        return ProductRepository.count()

    @staticmethod
    def get_all() -> list[Product]:
        return ProductRepository.get_all()

    @staticmethod
    def search(keyword: str) -> list[Product]:
        """Returns active products matching keyword, with stock > 0."""
        return [p for p in ProductRepository.search(keyword) if p.stock > 0]

    @staticmethod
    def upload_image(src_path: str) -> str:
        """
        Αντιγράφει την εικόνα στον φάκελο resources/product_images και
        επιστρέφει το απόλυτο path.  Πετά EShopError αν αποτύχει.
        """
        src = Path(src_path)
        if not src.exists():
            raise EShopError("Το αρχείο εικόνας δεν βρέθηκε.")
        if src.suffix.lower() not in _ALLOWED_EXT:
            raise EShopError(
                f"Μη αποδεκτός τύπος αρχείου ({src.suffix}). "
                "Επιτρέπονται: JPG, PNG, WEBP, GIF, BMP."
            )
        try:
            _IMAGES_DIR.mkdir(parents=True, exist_ok=True)
            dst = _IMAGES_DIR / src.name
            # αποφυγή conflicts ονομάτων
            counter = 1
            while dst.exists():
                dst = _IMAGES_DIR / f"{src.stem}_{counter}{src.suffix}"
                counter += 1
            shutil.copy2(src, dst)
            return str(dst)
        except OSError as exc:
            raise EShopError(f"Αποτυχία μεταφόρτωσης: {exc}") from exc

    @staticmethod
    def create(
        name: str,
        description: str,
        price: str,
        stock: str,
        image_path: str | None,
    ) -> Product:
        name        = name.strip()
        description = description.strip() or None

        if not name:
            raise EShopError("Το όνομα προϊόντος είναι υποχρεωτικό.")

        if ProductRepository.exists_by_name(name):
            raise EShopError(
                f"Υπάρχει ήδη προϊόν με το όνομα «{name}». "
                "Παρακαλώ επιλέξτε διαφορετικό όνομα."
            )

        try:
            prc = float(price.replace(",", "."))
        except ValueError:
            raise EShopError("Η τιμή πρέπει να είναι αριθμός.")
        if prc < 0:
            raise EShopError("Η τιμή δεν μπορεί να είναι αρνητική.")

        try:
            stk = int(stock)
        except ValueError:
            raise EShopError("Το απόθεμα πρέπει να είναι ακέραιος αριθμός.")
        if stk < 0:
            raise EShopError("Το απόθεμα δεν μπορεί να είναι αρνητικό.")

        product_id = ProductRepository.create(name, description, prc, stk, image_path)
        return Product(
            id=product_id,
            name=name,
            description=description,
            price=prc,
            stock=stk,
            image_path=image_path,
            is_active=True,
        )
