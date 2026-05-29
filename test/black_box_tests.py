"""
 BeautyHub — Black Box Testing

Δοκιμές "μαύρου κουτιού": ελέγχουμε τη ΣΥΜΠΕΡΙΦΟΡΑ της εφαρμογής μέσα από τα
δημόσια interfaces (controllers / services), ΧΩΡΙΣ να εξετάζουμε την εσωτερική
υλοποίηση. Δίνουμε εισόδους, ελέγχουμε εξόδους και αναμενόμενα σφάλματα.


Το script:
  * Χρησιμοποιεί ΠΡΟΣΩΡΙΝΗ βάση δεδομένων (δεν πειράζει τα πραγματικά σου δεδομένα).
  * Φορτώνει τα ίδια seed data με την εφαρμογή (γνωστοί χρήστες/κωδικοί).
  * Εμφανίζει αναλυτικά αποτελέσματα PASS / FAIL και τελική σύνοψη.

"""

from __future__ import annotations

import io
import os
import sys
import tempfile
import traceback
from contextlib import redirect_stdout
from pathlib import Path


try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

# Βεβαιωνόμαστε ότι το root του project είναι στο sys.path
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


#  ΠΡΟΣΩΡΙΝΗ ΒΑΣΗ — να μην μολύνουμε την πραγματική salon.db

import database.connection as dbconn 

_TMP_DIR = tempfile.mkdtemp(prefix="beautyhub_test_")
dbconn._DB_PATH = Path(_TMP_DIR) / "test_salon.db"

from database.connection import Database         
from database.seed import seed_database           

# Controllers (το "μαύρο κουτί" που τεστάρουμε)
from controllers.auth_controller import AuthController, AuthError                
from controllers.salon_controller import SalonController, SalonError             
from controllers.service_controller import ServiceController, ServiceError       
from controllers.eshop_controller import EShopController, EShopError            
from controllers.order_controller import OrderController, OrderError             
from controllers.appointment_controller import AppointmentController, AppointmentError  


#  Μικρό test framework με χρωματιστή έξοδο

class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"


# Ενεργοποίηση ANSI χρωμάτων στα Windows terminals
if os.name == "nt":
    os.system("")


class TestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.failures: list[tuple[str, str]] = []

    def section(self, title: str):
        print(f"\n{Colors.CYAN}{Colors.BOLD}── {title} {'─' * max(0, 56 - len(title))}{Colors.RESET}")

    def run(self, name: str, func):
        """Τρέχει ένα test. Το func κάνει raise AssertionError σε αποτυχία."""
        try:
            func()
        except Exception as exc:  
            self.failed += 1
            tb = traceback.format_exc()
            self.failures.append((name, tb))
            print(f"  {Colors.RED}✗ FAIL{Colors.RESET}  {name}")
            print(f"         {Colors.DIM}{exc}{Colors.RESET}")
        else:
            self.passed += 1
            print(f"  {Colors.GREEN}✓ PASS{Colors.RESET}  {name}")

    def summary(self) -> int:
        total = self.passed + self.failed
        print(f"\n{Colors.BOLD}{'=' * 62}{Colors.RESET}")
        print(f"{Colors.BOLD} ΣΥΝΟΨΗ ΑΠΟΤΕΛΕΣΜΑΤΩΝ{Colors.RESET}")
        print(f"{Colors.BOLD}{'=' * 62}{Colors.RESET}")
        print(f"  Σύνολο δοκιμών : {total}")
        print(f"  {Colors.GREEN}Επιτυχημένες   : {self.passed}{Colors.RESET}")
        color = Colors.RED if self.failed else Colors.GREEN
        print(f"  {color}Αποτυχημένες   : {self.failed}{Colors.RESET}")
        rate = (self.passed / total * 100) if total else 0
        print(f"  Ποσοστό επιτυχίας: {rate:.1f}%")

        if self.failed:
            print(f"\n{Colors.RED}{Colors.BOLD} Λεπτομέρειες αποτυχιών:{Colors.RESET}")
            for name, tb in self.failures:
                print(f"\n{Colors.RED}● {name}{Colors.RESET}")
                print(f"{Colors.DIM}{tb}{Colors.RESET}")
            print(f"\n{Colors.RED}{Colors.BOLD} ΑΠΟΤΕΛΕΣΜΑ: ΑΠΕΤΥΧΕ{Colors.RESET}")
            return 1

        print(f"\n{Colors.GREEN}{Colors.BOLD} ΑΠΟΤΕΛΕΣΜΑ: ΟΛΕΣ ΟΙ ΔΟΚΙΜΕΣ ΠΕΡΑΣΑΝ{Colors.RESET}")
        return 0



#  Βοηθητικά assertions

def assert_true(cond, msg="Αναμενόταν True"):
    if not cond:
        raise AssertionError(msg)


def assert_eq(a, b, msg=None):
    if a != b:
        raise AssertionError(msg or f"Αναμενόταν {b!r}, ελήφθη {a!r}")


def assert_raises(exc_type, func, *args, **kwargs):
    try:
        func(*args, **kwargs)
    except exc_type:
        return
    except Exception as other:  
        raise AssertionError(
            f"Αναμενόταν {exc_type.__name__}, ελήφθη {type(other).__name__}: {other}"
        )
    raise AssertionError(f"Αναμενόταν να γίνει raise {exc_type.__name__}, αλλά δεν έγινε.")



#  TEST SUITES


def test_auth(t: TestRunner):
    t.section("Αυθεντικοποίηση & Εγγραφή (AuthController)")

    def valid_admin_login():
        user = AuthController.login("admin", "admin123")
        assert_eq(user.role_name, "admin", "Ο admin πρέπει να έχει ρόλο 'admin'")
        assert_eq(user.username, "admin")

    def valid_customer_login():
        user = AuthController.login("petros", "petros123")
        assert_eq(user.role_name, "customer")
        assert_true(user.is_customer)

    def valid_employee_login():
        user = AuthController.login("nikos_k", "nikos123")
        assert_eq(user.role_name, "employee")

    def wrong_password():
        assert_raises(AuthError, AuthController.login, "admin", "λάθος_κωδικός")

    def nonexistent_user():
        assert_raises(AuthError, AuthController.login, "δεν_υπαρχω", "ο,τιδηποτε")

    def empty_credentials():
        assert_raises(AuthError, AuthController.login, "", "")

    def register_new_customer():
        user = AuthController.register_customer(
            "test_user_bb", "test_bb@mail.gr", "pass1234", "Δοκιμή", "Χρήστης", "6970000000"
        )
        assert_eq(user.role_name, "customer")
        assert_eq(user.username, "test_user_bb")
        # Πρέπει να μπορεί να κάνει login μετά την εγγραφή
        again = AuthController.login("test_user_bb", "pass1234")
        assert_eq(again.username, "test_user_bb")

    def register_duplicate_username():
        assert_raises(
            AuthError,
            AuthController.register_customer,
            "admin", "neo_email@mail.gr", "pass1234", "Α", "Β",
        )

    def register_missing_fields():
        assert_raises(
            AuthError,
            AuthController.register_customer,
            "", "", "", "", "",
        )

    t.run("Έγκυρη σύνδεση admin", valid_admin_login)
    t.run("Έγκυρη σύνδεση πελάτη", valid_customer_login)
    t.run("Έγκυρη σύνδεση υπαλλήλου", valid_employee_login)
    t.run("Λάθος κωδικός → απόρριψη", wrong_password)
    t.run("Ανύπαρκτος χρήστης → απόρριψη", nonexistent_user)
    t.run("Κενά στοιχεία → απόρριψη", empty_credentials)
    t.run("Εγγραφή νέου πελάτη", register_new_customer)
    t.run("Εγγραφή με υπάρχον username → απόρριψη", register_duplicate_username)
    t.run("Εγγραφή με κενά πεδία → απόρριψη", register_missing_fields)


def test_salons(t: TestRunner):
    t.section("Διαχείριση Κομμωτηρίων (SalonController)")

    def list_salons():
        salons = SalonController.get_all()
        assert_true(len(salons) >= 3, "Πρέπει να υπάρχουν τουλάχιστον 3 κομμωτήρια (seed)")

    def search_by_city():
        results = SalonController.search(city_kw="Αθήνα")
        assert_true(len(results) >= 1, "Πρέπει να βρεθεί κομμωτήριο στην Αθήνα")
        assert_true(any("Αθήνα" in s.city for s in results))

    def create_valid_salon():
        salon = SalonController.create(
            "Test Salon BB", "Οδός Δοκιμής 1", "Λάρισα", "2410123456", "test@bb.gr"
        )
        assert_eq(salon.name, "Test Salon BB")
        assert_eq(salon.city, "Λάρισα")
        assert_true(salon.is_active)

    def create_salon_missing_name():
        assert_raises(SalonError, SalonController.create, "", "Διεύθυνση", "Πόλη", "", "")

    def create_salon_invalid_email():
        assert_raises(
            SalonError, SalonController.create,
            "Salon X", "Διεύθυνση", "Πόλη", "210", "λάθος-email",
        )

    def toggle_salon():
        salon = SalonController.create("Toggle Salon", "Δ 2", "Βόλος", "", "")
        before = salon.is_active
        after = SalonController.toggle_active(salon.id)
        assert_eq(after, not before, "Η κατάσταση πρέπει να αντιστραφεί")

    t.run("Λίστα κομμωτηρίων (seed)", list_salons)
    t.run("Αναζήτηση ανά πόλη", search_by_city)
    t.run("Δημιουργία έγκυρου κομμωτηρίου", create_valid_salon)
    t.run("Δημιουργία χωρίς όνομα → απόρριψη", create_salon_missing_name)
    t.run("Δημιουργία με άκυρο email → απόρριψη", create_salon_invalid_email)
    t.run("Ενεργοποίηση/Απενεργοποίηση", toggle_salon)


def test_services(t: TestRunner):
    t.section("Υπηρεσίες Κομμωτηρίου (ServiceController)")

    def list_services():
        services = ServiceController.get_all()
        assert_true(len(services) >= 6, "Πρέπει να υπάρχουν τουλάχιστον 6 υπηρεσίες (seed)")

    def create_valid_service():
        svc = ServiceController.create("Δοκιμαστική Υπηρεσία", "Περιγραφή", "45", "25.50")
        assert_eq(svc.duration_min, 45)
        assert_eq(svc.price, 25.50)

    def create_service_no_name():
        assert_raises(ServiceError, ServiceController.create, "", "x", "30", "10")

    def create_service_bad_duration():
        assert_raises(ServiceError, ServiceController.create, "Υπ. Α", "x", "abc", "10")

    def create_service_negative_duration():
        assert_raises(ServiceError, ServiceController.create, "Υπ. Β", "x", "-5", "10")

    def create_service_negative_price():
        assert_raises(ServiceError, ServiceController.create, "Υπ. Γ", "x", "30", "-1")

    def create_service_comma_price():
        # Η εφαρμογή δέχεται κόμμα ως δεκαδικό διαχωριστή
        svc = ServiceController.create("Υπ. Κόμμα", "x", "30", "12,90")
        assert_eq(svc.price, 12.90)

    t.run("Λίστα υπηρεσιών (seed)", list_services)
    t.run("Δημιουργία έγκυρης υπηρεσίας", create_valid_service)
    t.run("Δημιουργία χωρίς όνομα → απόρριψη", create_service_no_name)
    t.run("Μη αριθμητική διάρκεια → απόρριψη", create_service_bad_duration)
    t.run("Αρνητική διάρκεια → απόρριψη", create_service_negative_duration)
    t.run("Αρνητική τιμή → απόρριψη", create_service_negative_price)
    t.run("Τιμή με κόμμα (12,90) → αποδεκτή", create_service_comma_price)


def test_eshop(t: TestRunner):
    t.section("E-Shop / Προϊόντα (EShopController)")

    def list_products():
        products = EShopController.get_all()
        assert_true(len(products) >= 8, "Πρέπει να υπάρχουν τουλάχιστον 8 προϊόντα (seed)")

    def search_products_latin():
        # Αναζήτηση με λατινικό όρο (το «Λάδι Argan» περιέχει "Argan")
        results = EShopController.search("Argan")
        assert_true(len(results) >= 1, "Πρέπει να βρεθεί προϊόν που περιέχει 'Argan'")

    def search_products_greek_uppercase():
        # ΓΝΩΣΤΟ ΣΦΑΛΜΑ: η αναζήτηση χρησιμοποιεί το SQL LOWER(), που στη SQLite
        # ΔΕΝ μετατρέπει ελληνικά κεφαλαία σε πεζά. Έτσι αναζήτηση "Σαμπουάν"
        # δεν βρίσκει το προϊόν «Σαμπουάν Αναδόμησης».
        results = EShopController.search("Σαμπουάν")
        assert_true(
            len(results) >= 1,
            "ΕΥΡΗΜΑ: η αναζήτηση ελληνικών κεφαλαίων αποτυγχάνει "
            "(SQLite LOWER() δεν χειρίζεται ελληνικά). Δες product_repository.py:51",
        )

    def create_valid_product():
        p = EShopController.create("Προϊόν BB", "Περιγραφή", "9.99", "5", None)
        assert_eq(p.price, 9.99)
        assert_eq(p.stock, 5)

    def create_duplicate_name():
        EShopController.create("Διπλό BB", "x", "5", "5", None)
        assert_raises(EShopError, EShopController.create, "Διπλό BB", "x", "5", "5", None)

    def create_no_name():
        assert_raises(EShopError, EShopController.create, "", "x", "5", "5", None)

    def create_bad_price():
        assert_raises(EShopError, EShopController.create, "Π. Α", "x", "abc", "5", None)

    def create_negative_stock():
        assert_raises(EShopError, EShopController.create, "Π. Β", "x", "5", "-3", None)

    t.run("Λίστα προϊόντων (seed)", list_products)
    t.run("Αναζήτηση προϊόντος (λατινικός όρος)", search_products_latin)
    t.run("Αναζήτηση ελληνικών κεφαλαίων [γνωστό σφάλμα]", search_products_greek_uppercase)
    t.run("Δημιουργία έγκυρου προϊόντος", create_valid_product)
    t.run("Διπλό όνομα προϊόντος → απόρριψη", create_duplicate_name)
    t.run("Προϊόν χωρίς όνομα → απόρριψη", create_no_name)
    t.run("Μη αριθμητική τιμή → απόρριψη", create_bad_price)
    t.run("Αρνητικό απόθεμα → απόρριψη", create_negative_stock)


def test_cart_and_orders(t: TestRunner):
    t.section("Καλάθι & Παραγγελίες (OrderController)")

    customer = AuthController.login("eleni", "eleni123")
    products = EShopController.get_all()

    def cart_add_and_total():
        OrderController.clear_cart()
        p = products[0]
        OrderController.add_to_cart(p.id, p.name, p.price, 2)
        assert_eq(OrderController.cart_total(), round(p.price * 2, 2),
                  "Το σύνολο καλαθιού πρέπει να ισούται με τιμή × ποσότητα")
        assert_true(not OrderController.cart_is_empty())

    def cart_set_quantity_zero_removes():
        OrderController.clear_cart()
        p = products[0]
        OrderController.add_to_cart(p.id, p.name, p.price, 1)
        OrderController.set_quantity(p.id, 0)
        assert_true(OrderController.cart_is_empty(), "Ποσότητα 0 πρέπει να αφαιρεί το προϊόν")

    def create_order_empty_cart():
        OrderController.clear_cart()
        assert_raises(OrderError, OrderController.create_order, customer.id)

    def create_valid_order():
        OrderController.clear_cart()
        p = products[1]
        stock_before = p.stock
        OrderController.add_to_cart(p.id, p.name, p.price, 1)
        order = OrderController.create_order(customer.id, "cod")
        assert_eq(order.customer_id, customer.id)
        assert_eq(order.status, "pending")
        # Το απόθεμα πρέπει να μειώθηκε
        refreshed = next(x for x in EShopController.get_all() if x.id == p.id)
        assert_eq(refreshed.stock, stock_before - 1, "Το απόθεμα πρέπει να μειωθεί κατά 1")
        # Το καλάθι πρέπει να άδειασε
        assert_true(OrderController.cart_is_empty())

    def cancel_pending_order():
        OrderController.clear_cart()
        p = products[2]
        OrderController.add_to_cart(p.id, p.name, p.price, 1)
        order = OrderController.create_order(customer.id, "cod")
        # Ακύρωση εκκρεμούς παραγγελίας → επιτυχία
        OrderController.cancel_order(order.id, customer.id)
        orders = OrderController.get_orders(customer.id)
        cancelled = next(o for o in orders if o.id == order.id)
        assert_eq(cancelled.status, "cancelled")

    def cancel_order_wrong_customer():
        OrderController.clear_cart()
        p = products[3]
        OrderController.add_to_cart(p.id, p.name, p.price, 1)
        order = OrderController.create_order(customer.id, "cod")
        # Άλλος πελάτης δεν μπορεί να ακυρώσει ξένη παραγγελία
        assert_raises(OrderError, OrderController.cancel_order, order.id, 99999)

    t.run("Προσθήκη στο καλάθι & σύνολο", cart_add_and_total)
    t.run("Ποσότητα 0 αφαιρεί προϊόν", cart_set_quantity_zero_removes)
    t.run("Παραγγελία με άδειο καλάθι → απόρριψη", create_order_empty_cart)
    t.run("Δημιουργία παραγγελίας & μείωση αποθέματος", create_valid_order)
    t.run("Ακύρωση εκκρεμούς παραγγελίας", cancel_pending_order)
    t.run("Ακύρωση από λάθος πελάτη → απόρριψη", cancel_order_wrong_customer)


def test_appointments(t: TestRunner):
    t.section("Ραντεβού (AppointmentController)")

    customer = AuthController.login("petros", "petros123")
    salon_id = SalonController.get_all()[0].id
    services = AppointmentController.get_active_services(salon_id)
    employees = [e for e in AppointmentController.get_employees(salon_id) if e["id"] is not None]

    def services_available():
        assert_true(len(services) >= 1, "Το κομμωτήριο πρέπει να έχει ενεργές υπηρεσίες")

    def employees_available():
        assert_true(len(employees) >= 1, "Το κομμωτήριο πρέπει να έχει υπαλλήλους")

    def available_slots():
        svc = services[0]
        slots = AppointmentController.get_available_slots("2026-07-15", svc.id, None, salon_id)
        assert_true(len(slots) >= 1, "Πρέπει να υπάρχουν διαθέσιμες ώρες σε άδεια μέρα")

    def create_and_overlap():
        svc = services[0]
        emp = employees[0]
        start = "2026-07-20 10:00"
        appt_id = AppointmentController.create_appointment(
            customer.id, emp["id"], svc.id, start, "Δοκιμή BB", salon_id
        )
        assert_true(appt_id > 0, "Πρέπει να επιστραφεί έγκυρο id ραντεβού")
        # Δεύτερο ραντεβού στην ίδια ώρα/υπάλληλο → σύγκρουση
        assert_raises(
            AppointmentError,
            AppointmentController.create_appointment,
            customer.id, emp["id"], svc.id, start, None, salon_id,
        )

    def create_invalid_service():
        emp = employees[0]
        assert_raises(
            AppointmentError,
            AppointmentController.create_appointment,
            customer.id, emp["id"], 999999, "2026-08-01 11:00", None, salon_id,
        )

    def customer_cancel():
        svc = services[0]
        emp = employees[0]
        appt_id = AppointmentController.create_appointment(
            customer.id, emp["id"], svc.id, "2026-07-25 12:00", None, salon_id
        )
        AppointmentController.customer_cancel_appointment(appt_id, customer.id)
        appts = AppointmentController.get_by_customer(customer.id)
        cancelled = next(a for a in appts if a.id == appt_id)
        assert_eq(cancelled.status, "cancelled")

    def employee_accept_pending():
        svc = services[0]
        emp = employees[0]
        appt_id = AppointmentController.create_appointment(
            customer.id, emp["id"], svc.id, "2026-07-28 09:00", None, salon_id
        )
        AppointmentController.accept_appointment(appt_id, emp["id"])
        appts = AppointmentController.get_by_employee(emp["id"])
        accepted = next(a for a in appts if a.id == appt_id)
        assert_eq(accepted.status, "confirmed")

    t.run("Υπάρχουν ενεργές υπηρεσίες κομμωτηρίου", services_available)
    t.run("Υπάρχουν υπάλληλοι κομμωτηρίου", employees_available)
    t.run("Διαθέσιμες ώρες σε άδεια μέρα", available_slots)
    t.run("Δημιουργία ραντεβού & σύγκρουση ώρας → απόρριψη", create_and_overlap)
    t.run("Ραντεβού με ανύπαρκτη υπηρεσία → απόρριψη", create_invalid_service)
    t.run("Ακύρωση ραντεβού από πελάτη", customer_cancel)
    t.run("Αποδοχή εκκρεμούς ραντεβού από υπάλληλο", employee_accept_pending)


#  MAIN

def main() -> int:
    print(f"{Colors.BOLD}{'=' * 62}{Colors.RESET}")
    print(f"{Colors.BOLD}  BeautyHub — BLACK BOX TESTING{Colors.RESET}")
    print(f"{Colors.BOLD}{'=' * 62}{Colors.RESET}")
    print(f"  Προσωρινή βάση: {dbconn._DB_PATH}")

    # Προετοιμασία βάσης (αθόρυβα — η seed τυπώνει πολλά μηνύματα)
    print(f"  {Colors.DIM}Αρχικοποίηση & seed βάσης δεδομένων...{Colors.RESET}")
    with redirect_stdout(io.StringIO()):
        Database.initialize()
        seed_database()

    t = TestRunner()
    try:
        test_auth(t)
        test_salons(t)
        test_services(t)
        test_eshop(t)
        test_cart_and_orders(t)
        test_appointments(t)
    finally:
        exit_code = t.summary()
        Database.close()
        # Καθαρισμός προσωρινής βάσης
        try:
            import shutil
            shutil.rmtree(_TMP_DIR, ignore_errors=True)
        except Exception: 
            pass

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
