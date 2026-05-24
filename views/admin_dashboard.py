import customtkinter as ctk
from views.base_dashboard import BaseDashboard
from controllers.auth_controller import AuthController
from views.notifications_page import NotificationsPage
class AdminDashboard(BaseDashboard):
    NAV_ITEMS = [
        ("Αρχική",          "home"),
        ("Κομμωτήρια",      "salons"),
        ("Χρήστες",         "users"),
        ("Υπηρεσίες",       "services"),
        ("E-Shop",           "eshop"),
        ("Ραντεβού",        "appointments"),
        ("Αποθήκη",         "inventory"),
        ("Ειδοποιήσεις",    "notifications"),
    ]

    def _build_pages(self):
        self._register_page("home",          _HomePage(self._content))
        self._register_page("salons",        _PlaceholderPage(self._content, "Κομμωτήρια"))
        self._register_page("users",         _UsersPage(self._content))
        self._register_page("services",      _PlaceholderPage(self._content, "Υπηρεσίες"))
        self._register_page("eshop",         _PlaceholderPage(self._content, "E-Shop"))
        self._register_page("appointments",  _PlaceholderPage(self._content, "Ραντεβού"))
        self._register_page("inventory",     _PlaceholderPage(self._content, "Αποθήκη"))
        self._register_page("notifications", NotificationsPage(self._content))


# ------------------------------------------------------------------ pages

class _HomePage(ctk.CTkFrame):
    _STATS = [
        ("🏪", "Κομμωτήρια", lambda: 0),
        ("👥", "Χρήστες",    lambda: AuthController.count_users()),
        ("💇", "Υπηρεσίες",  lambda: 0),
        ("📅", "Ραντεβού",   lambda: 0),
    ]

    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self, text="Πίνακας Ελέγχου",
            font=ctk.CTkFont(size=24, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=32, pady=(32, 4))
        ctk.CTkLabel(
            self, text="Καλωσήρθατε στο σύστημα διαχείρισης κομμωτηρίων.",
            text_color="gray",
        ).grid(row=1, column=0, sticky="w", padx=32, pady=(0, 24))

        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.grid(row=2, column=0, sticky="ew", padx=32)
        stats_frame.columnconfigure((0, 1, 2, 3), weight=1)

        # αποθηκεύουμε references στις ετικέτες αριθμών για γρήγορη ανανέωση
        self._count_labels: list[ctk.CTkLabel] = []
        for col, (icon, label, _) in enumerate(self._STATS):
            card = ctk.CTkFrame(stats_frame, corner_radius=12)
            card.grid(row=0, column=col, padx=8, pady=8, sticky="ew")
            ctk.CTkLabel(card, text=icon, font=ctk.CTkFont(size=32)).pack(pady=(20, 4))
            lbl = ctk.CTkLabel(card, text="—", font=ctk.CTkFont(size=28, weight="bold"))
            lbl.pack()
            ctk.CTkLabel(card, text=label, text_color="gray").pack(pady=(0, 20))
            self._count_labels.append(lbl)

    def refresh(self):
        for lbl, (_, _, fn) in zip(self._count_labels, self._STATS):
            lbl.configure(text=str(fn()))


class _UsersPage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=32, pady=(24, 12))
        header.columnconfigure(0, weight=1)
        ctk.CTkLabel(
            header, text="Διαχείριση Χρηστών",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        self._table = ctk.CTkScrollableFrame(self, corner_radius=10)
        self._table.grid(row=1, column=0, sticky="nsew", padx=32, pady=(0, 24))
        self._table.columnconfigure((0, 1, 2, 3, 4), weight=1)

        self._load_users()

    def refresh(self):
        self._load_users()

    def _load_users(self):
        for w in self._table.winfo_children():
            w.destroy()

        headers = ["#", "Χρήστης", "Email", "Ρόλος", "Κατάσταση"]
        for col, h in enumerate(headers):
            ctk.CTkLabel(
                self._table, text=h,
                font=ctk.CTkFont(weight="bold"),
                anchor="w",
            ).grid(row=0, column=col, sticky="ew", padx=8, pady=6)

        ctk.CTkFrame(self._table, height=1, fg_color="gray40").grid(
            row=1, column=0, columnspan=5, sticky="ew", padx=4
        )

        rows = AuthController.get_all_users()

        for r_idx, row in enumerate(rows, start=2):
            values = [
                str(row["id"]),
                row["username"],
                row["email"],
                row["display_name"],
                "✔ Ενεργός" if row["is_active"] else "✘ Ανενεργός",
            ]
            bg = ("gray92", "gray18") if r_idx % 2 == 0 else ("gray96", "gray15")
            for col, val in enumerate(values):
                ctk.CTkLabel(
                    self._table, text=val, anchor="w",
                    fg_color=bg, corner_radius=4,
                ).grid(row=r_idx, column=col, sticky="ew", padx=4, pady=2)


class _PlaceholderPage(ctk.CTkFrame):
    def __init__(self, master, title: str):
        super().__init__(master, fg_color="transparent")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        ctk.CTkLabel(
            self, text=f"{title}\n\nΈρχεται σύντομα…",
            font=ctk.CTkFont(size=18),
            text_color="gray",
            justify="center",
        ).grid(row=0, column=0)
