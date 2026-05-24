"""
Κεντρικές εξαιρέσεις επιχειρηματικής λογικής.
Ορίζονται εδώ ώστε κανένα επίπεδο να μην εξαρτάται από άλλο για τα errors.
"""


class AuthError(Exception):
    """Σφάλματα αυθεντικοποίησης / εγγραφής."""


class ServiceError(Exception):
    """Σφάλματα διαχείρισης υπηρεσιών κομμωτηρίου."""


class SalonError(Exception):
    """Σφάλματα διαχείρισης κομμωτηρίου."""


class EShopError(Exception):
    """Σφάλματα διαχείρισης e-shop / προϊόντων."""


class OrderError(Exception):
    """Σφάλματα δημιουργίας / επεξεργασίας παραγγελίας."""


class RefundError(Exception):
    """Η ακύρωση ολοκληρώθηκε αλλά η επιστροφή χρημάτων απέτυχε (alt flow 3)."""


class AppointmentError(Exception):
    """Σφάλματα κλεισίματος / διαχείρισης ραντεβού."""


class InventoryError(Exception):
    """Σφάλματα απογραφής / διαχείρισης αποθεμάτων."""


class ReviewError(Exception):
    """Σφάλματα υποβολής / διαχείρισης αξιολογήσεων."""
