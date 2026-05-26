import customtkinter as ctk
from views.base_dashboard import BaseDashboard
from controllers.auth_controller import AuthController
from views.notifications_page import NotificationsPage
from controllers.eshop_controller import EShopController, EShopError
from pathlib import Path
from tkinter import filedialog
from controllers.service_controller import ServiceController, ServiceError
from controllers.inventory_controller import InventoryController, InventoryError

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
        self._register_page("services",      _ServicesPage(self._content))
        self._register_page("eshop",         _EShopPage(self._content))
        self._register_page("appointments",  _PlaceholderPage(self._content, "Ραντεβού"))
        self._register_page("inventory",     _InventoryPage(self._content))
        self._register_page("notifications", NotificationsPage(self._content))


# pages

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


class _EShopPage(ctk.CTkFrame):
    """Λίστα προϊόντων e-shop + inline φόρμα δημιουργίας."""

    _COLS = ["#", "Όνομα", "Περιγραφή", "Τιμή", "Απόθεμα", "Εικόνα"]

    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self._pending_image: str | None = None
        self._build_list_view()
        self._build_form_view()
        self._show_list()

    # list
    def _build_list_view(self):
        self._list_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._list_frame.columnconfigure(0, weight=1)
        self._list_frame.rowconfigure(1, weight=1)

        hdr = ctk.CTkFrame(self._list_frame, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=32, pady=(24, 12))
        hdr.columnconfigure(0, weight=1)
        ctk.CTkLabel(
            hdr, text="E-Shop — Προϊόντα",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(
            hdr, text="+ Νέο Προϊόν", width=150,
            command=self._show_form,
        ).grid(row=0, column=1, sticky="e")

        self._table = ctk.CTkScrollableFrame(self._list_frame, corner_radius=10)
        self._table.grid(row=1, column=0, sticky="nsew", padx=32, pady=(0, 24))
        for i in range(len(self._COLS)):
            self._table.columnconfigure(i, weight=1)

    def _refresh_table(self):
        for w in self._table.winfo_children():
            w.destroy()

        for col, h in enumerate(self._COLS):
            ctk.CTkLabel(
                self._table, text=h,
                font=ctk.CTkFont(weight="bold"), anchor="w",
            ).grid(row=0, column=col, sticky="ew", padx=8, pady=6)

        ctk.CTkFrame(self._table, height=1, fg_color="gray40").grid(
            row=1, column=0, columnspan=len(self._COLS), sticky="ew", padx=4
        )

        products = EShopController.get_all()

        if not products:
            ctk.CTkLabel(
                self._table,
                text="Δεν υπάρχουν προϊόντα ακόμα. Πατήστε «+ Νέο Προϊόν».",
                text_color="gray",
            ).grid(row=2, column=0, columnspan=len(self._COLS), pady=24)
            return

        for r_idx, p in enumerate(products, start=2):
            img_label = Path(p.image_path).name if p.image_path else "—"
            values = [
                str(p.id),
                p.name,
                (p.description or "—")[:40],
                f"{p.price:.2f} €",
                str(p.stock),
                img_label,
            ]
            bg = ("gray92", "gray18") if r_idx % 2 == 0 else ("gray96", "gray15")
            for col, val in enumerate(values):
                ctk.CTkLabel(
                    self._table, text=val, anchor="w",
                    fg_color=bg, corner_radius=4,
                ).grid(row=r_idx, column=col, sticky="ew", padx=4, pady=2)

    # form
    def _build_form_view(self):
        self._form_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._form_frame.columnconfigure(0, weight=1)

        hdr = ctk.CTkFrame(self._form_frame, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=32, pady=(24, 4))
        hdr.columnconfigure(0, weight=1)
        ctk.CTkLabel(
            hdr, text="Νέο Προϊόν",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        card = ctk.CTkFrame(self._form_frame, corner_radius=12)
        card.grid(row=1, column=0, sticky="ew", padx=32, pady=12)
        card.columnconfigure(1, weight=1)

        text_fields = [
            ("Όνομα *",         "_p_name",  "π.χ. Σαμπουάν βαθύ καθαρισμού"),
            ("Περιγραφή",       "_p_desc",  "Προαιρετική περιγραφή"),
            ("Τιμή (€) *",      "_p_price", "π.χ. 12.50"),
            ("Απόθεμα (τεμ.) *","_p_stock", "π.χ. 50"),
        ]
        for row_idx, (label, attr, ph) in enumerate(text_fields):
            ctk.CTkLabel(card, text=label, anchor="w").grid(
                row=row_idx, column=0, sticky="w", padx=(20, 12), pady=(14, 2)
            )
            entry = ctk.CTkEntry(card, placeholder_text=ph, height=36)
            entry.grid(row=row_idx, column=1, sticky="ew", padx=(0, 20), pady=(14, 2))
            setattr(self, attr, entry)

        # image upload row
        img_row_idx = len(text_fields)
        ctk.CTkLabel(card, text="Φωτογραφία", anchor="w").grid(
            row=img_row_idx, column=0, sticky="w", padx=(20, 12), pady=(14, 2)
        )
        img_frame = ctk.CTkFrame(card, fg_color="transparent")
        img_frame.grid(row=img_row_idx, column=1, sticky="ew", padx=(0, 20), pady=(14, 2))
        img_frame.columnconfigure(0, weight=1)

        self._img_label = ctk.CTkLabel(
            img_frame, text="Δεν έχει επιλεγεί εικόνα",
            text_color="gray", anchor="w",
        )
        self._img_label.grid(row=0, column=0, sticky="w")

        self._img_msg = ctk.StringVar()
        self._img_msg_label = ctk.CTkLabel(
            img_frame, textvariable=self._img_msg,
            font=ctk.CTkFont(size=11), text_color=("#e74c3c", "#e74c3c"),
            wraplength=300, anchor="w",
        )
        self._img_msg_label.grid(row=1, column=0, sticky="w")

        ctk.CTkButton(
            img_frame, text="Επιλογή εικόνας", width=160, height=32,
            fg_color=("gray70", "gray30"), hover_color=("gray60", "gray40"),
            command=self._pick_image,
        ).grid(row=0, column=1, padx=(12, 0))

        # feedback label
        self._form_msg = ctk.StringVar()
        self._form_msg_label = ctk.CTkLabel(
            card, textvariable=self._form_msg,
            font=ctk.CTkFont(size=12), wraplength=500,
        )
        self._form_msg_label.grid(
            row=img_row_idx + 1, column=0, columnspan=2, pady=(8, 4)
        )

        # action buttons
        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.grid(
            row=img_row_idx + 2, column=0, columnspan=2,
            pady=(4, 20), padx=20, sticky="e",
        )
        ctk.CTkButton(
            btn_row, text="Ακύρωση", width=110,
            fg_color="transparent", border_width=1,
            text_color=("gray20", "gray80"),
            hover_color=("gray85", "gray25"),
            command=self._cancel_form,
        ).pack(side="left", padx=(0, 10))
        ctk.CTkButton(
            btn_row, text="Αποθήκευση", width=130,
            command=self._submit_form,
        ).pack(side="left")

    # image
    def _pick_image(self):
        path = filedialog.askopenfilename(
            title="Επιλογή φωτογραφίας προϊόντος",
            filetypes=[
                ("Εικόνες", "*.jpg *.jpeg *.png *.webp *.gif *.bmp"),
                ("Όλα τα αρχεία", "*.*"),
            ],
        )
        if not path:
            return
        self._img_msg.set("")
        try:
            saved = EShopController.upload_image(path)
            self._pending_image = saved
            self._img_label.configure(
                text=Path(saved).name, text_color=("#27ae60", "#2ecc71")
            )
        except EShopError as e:
            self._pending_image = None
            self._img_label.configure(
                text="Αποτυχία — επιλέξτε άλλη εικόνα", text_color=("gray40", "gray60")
            )
            self._img_msg.set(str(e))

    # navigation
    def refresh(self):
        self._show_list()

    def _show_list(self):
        self._form_frame.grid_remove()
        self._list_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self._refresh_table()

    def _show_form(self):
        self._list_frame.grid_remove()
        for attr in ("_p_name", "_p_desc", "_p_price", "_p_stock"):
            getattr(self, attr).delete(0, "end")
        self._pending_image = None
        self._img_label.configure(text="Δεν έχει επιλεγεί εικόνα", text_color="gray")
        self._img_msg.set("")
        self._form_msg.set("")
        self._form_msg_label.configure(text_color=("gray40", "gray60"))
        self._form_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")

    # actions
    def _cancel_form(self):
        self._show_list()

    def _submit_form(self):
        self._form_msg.set("")
        try:
            EShopController.create(
                name=self._p_name.get(),
                description=self._p_desc.get(),
                price=self._p_price.get(),
                stock=self._p_stock.get(),
                image_path=self._pending_image,
            )
            self._form_msg_label.configure(text_color=("#27ae60", "#2ecc71"))
            self._form_msg.set("Το προϊόν δημιουργήθηκε επιτυχώς!")
            self.after(1200, self._show_list)
        except EShopError as e:
            self._form_msg_label.configure(text_color=("#e74c3c", "#e74c3c"))
            self._form_msg.set(str(e))

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

class _ServicesPage(ctk.CTkFrame):
    """
    Λίστα υπηρεσιών + inline φόρμα δημιουργίας.
    Εναλλάσσεται μεταξύ list-view και form-view.
    """

    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self._build_list_view()
        self._build_form_view()
        self._show_list()

    # list
    def _build_list_view(self):
        self._list_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._list_frame.columnconfigure(0, weight=1)
        self._list_frame.rowconfigure(1, weight=1)

        # header row
        hdr = ctk.CTkFrame(self._list_frame, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=32, pady=(24, 12))
        hdr.columnconfigure(0, weight=1)
        ctk.CTkLabel(
            hdr, text="Υπηρεσίες",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(
            hdr, text="+ Νέα Υπηρεσία", width=150,
            command=self._show_form,
        ).grid(row=0, column=1, sticky="e")

        # scrollable table
        self._table = ctk.CTkScrollableFrame(self._list_frame, corner_radius=10)
        self._table.grid(row=1, column=0, sticky="nsew", padx=32, pady=(0, 24))
        self._table.columnconfigure((0, 1, 2, 3, 4), weight=1)

    def _refresh_table(self):
        for w in self._table.winfo_children():
            w.destroy()

        headers = ["#", "Όνομα", "Περιγραφή", "Διάρκεια", "Τιμή"]
        for col, h in enumerate(headers):
            ctk.CTkLabel(
                self._table, text=h,
                font=ctk.CTkFont(weight="bold"), anchor="w",
            ).grid(row=0, column=col, sticky="ew", padx=8, pady=6)

        ctk.CTkFrame(self._table, height=1, fg_color="gray40").grid(
            row=1, column=0, columnspan=5, sticky="ew", padx=4
        )

        services = ServiceController.get_all()

        if not services:
            ctk.CTkLabel(
                self._table,
                text="Δεν υπάρχουν υπηρεσίες ακόμα. Πατήστε «+ Νέα Υπηρεσία».",
                text_color="gray",
            ).grid(row=2, column=0, columnspan=5, pady=24)
            return

        for r_idx, svc in enumerate(services, start=2):
            values = [
                str(svc.id),
                svc.name,
                svc.description or "—",
                f"{svc.duration_min} λεπτά",
                f"{svc.price:.2f} €",
            ]
            bg = ("gray92", "gray18") if r_idx % 2 == 0 else ("gray96", "gray15")
            for col, val in enumerate(values):
                ctk.CTkLabel(
                    self._table, text=val, anchor="w",
                    fg_color=bg, corner_radius=4,
                ).grid(row=r_idx, column=col, sticky="ew", padx=4, pady=2)

    # form
    def _build_form_view(self):
        self._form_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._form_frame.columnconfigure(0, weight=1)

        # header
        hdr = ctk.CTkFrame(self._form_frame, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=32, pady=(24, 4))
        hdr.columnconfigure(0, weight=1)
        ctk.CTkLabel(
            hdr, text="Νέα Υπηρεσία",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        # card
        card = ctk.CTkFrame(self._form_frame, corner_radius=12)
        card.grid(row=1, column=0, sticky="ew", padx=32, pady=12)
        card.columnconfigure(1, weight=1)

        fields = [
            ("Όνομα *",              "_f_name",     False, "π.χ. Κούρεμα γυναικείο"),
            ("Περιγραφή",            "_f_desc",     False, "Προαιρετική περιγραφή"),
            ("Διάρκεια (λεπτά) *",   "_f_duration", False, "π.χ. 45"),
            ("Τιμή (€) *",           "_f_price",    False, "π.χ. 20.00"),
        ]
        for row_idx, (label, attr, secret, ph) in enumerate(fields):
            ctk.CTkLabel(card, text=label, anchor="w").grid(
                row=row_idx, column=0, sticky="w", padx=(20, 12), pady=(14, 2)
            )
            entry = ctk.CTkEntry(card, placeholder_text=ph, show="•" if secret else "", height=36)
            entry.grid(row=row_idx, column=1, sticky="ew", padx=(0, 20), pady=(14, 2))
            setattr(self, attr, entry)

        # feedback label
        self._form_msg = ctk.StringVar()
        self._form_msg_label = ctk.CTkLabel(
            card, textvariable=self._form_msg,
            font=ctk.CTkFont(size=12), wraplength=480,
        )
        self._form_msg_label.grid(row=len(fields), column=0, columnspan=2, pady=(8, 4))

        # buttons
        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.grid(row=len(fields) + 1, column=0, columnspan=2, pady=(4, 20), padx=20, sticky="e")
        ctk.CTkButton(
            btn_row, text="Ακύρωση", width=110,
            fg_color="transparent",
            border_width=1,
            text_color=("gray20", "gray80"),
            hover_color=("gray85", "gray25"),
            command=self._cancel_form,
        ).pack(side="left", padx=(0, 10))
        ctk.CTkButton(
            btn_row, text="Αποθήκευση", width=130,
            command=self._submit_form,
        ).pack(side="left")

    # navigation
    def refresh(self):
        self._show_list()

    def _show_list(self):
        self._form_frame.grid_remove()
        self._list_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self._refresh_table()

    def _show_form(self):
        self._list_frame.grid_remove()
        for attr in ("_f_name", "_f_desc", "_f_duration", "_f_price"):
            getattr(self, attr).delete(0, "end")
        self._form_msg.set("")
        self._form_msg_label.configure(text_color=("gray40", "gray60"))
        self._form_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")

    # actions
    def _cancel_form(self):
        self._show_list()

    def _submit_form(self):
        self._form_msg.set("")
        try:
            ServiceController.create(
                name=self._f_name.get(),
                description=self._f_desc.get(),
                duration_min=self._f_duration.get(),
                price=self._f_price.get(),
            )
            self._form_msg_label.configure(text_color=("#27ae60", "#2ecc71"))
            self._form_msg.set("Η υπηρεσία δημιουργήθηκε επιτυχώς!")
            self.after(1200, self._show_list)
        except ServiceError as e:
            self._form_msg_label.configure(text_color=("#e74c3c", "#e74c3c"))
            self._form_msg.set(str(e))

#  Inventory — UC 2.4 


_INV_STATUS_MAP = {
    'completed': ("✔ Ολοκληρώθηκε", ("#27ae60", "#2ecc71")),
    'draft':     ("Προσωρινή",    ("#e67e22", "#d68910")),
    'cancelled': ("✘ Ακυρώθηκε",    ("#e74c3c", "#922b21")),
}


class _InventoryPage(ctk.CTkFrame):

    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self._current_inv      = None   # Inventory object in progress
        self._count_entries: dict[int, ctk.CTkEntry] = {}  # line_id → entry
        self._actual_qtys: dict[int, int] = {}             # line_id → int
        self._cancel_back_fn   = None   

        self._build_home_frame()
        self._build_filter_frame()
        self._build_count_frame()
        self._build_review_frame()
        self._build_cancel_confirm_frame()
        self._build_result_frame()
        self._go_home()

    # router
    def _hide_all(self):
        for f in (self._home_frame, self._filter_frame, self._count_frame,
                  self._review_frame, self._cancel_confirm_frame, self._result_frame):
            f.grid_remove()

    def refresh(self):
        self._go_home()

        #HOME
    def _build_home_frame(self):
        self._home_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._home_frame.columnconfigure(0, weight=1)
        self._home_frame.rowconfigure(4, weight=1)

        ctk.CTkLabel(
            self._home_frame, text=" Διαχείριση Αποθεμάτων",
            font=ctk.CTkFont(size=20, weight="bold"), anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=32, pady=(24, 12))

        # action card
        act = ctk.CTkFrame(self._home_frame, corner_radius=10)
        act.grid(row=1, column=0, sticky="ew", padx=32, pady=(0, 4))
        act.columnconfigure((0, 1, 2), weight=1)

        ctk.CTkButton(
            act, text=" Πλήρης Απογραφή", height=44,
            command=self._start_full,
        ).grid(row=0, column=0, padx=16, pady=16, sticky="ew")

        ctk.CTkButton(
            act, text=" Μερική Απογραφή", height=44,
            fg_color=("gray72", "gray32"), hover_color=("gray60", "gray40"),
            text_color=("gray10", "gray90"),
            command=self._go_filter,
        ).grid(row=0, column=1, padx=16, pady=16, sticky="ew")

        self._draft_btn = ctk.CTkButton(
            act, text=" Συνέχεια Απογραφής", height=44,
            fg_color=("#e67e22", "#d35400"), hover_color=("#d35400", "#b7770d"),
            command=self._resume_draft,
        )


        # message line
        self._home_msg_var = ctk.StringVar()
        self._home_msg_lbl = ctk.CTkLabel(
            self._home_frame, textvariable=self._home_msg_var,
            font=ctk.CTkFont(size=12), anchor="w",
        )
        self._home_msg_lbl.grid(row=2, column=0, sticky="w", padx=32, pady=(0, 4))

        ctk.CTkLabel(
            self._home_frame, text="Ιστορικό Απογραφών",
            font=ctk.CTkFont(size=14, weight="bold"), anchor="w",
        ).grid(row=3, column=0, sticky="w", padx=32, pady=(8, 4))

        self._history_box = ctk.CTkScrollableFrame(self._home_frame, corner_radius=10)
        self._history_box.grid(row=4, column=0, sticky="nsew", padx=32, pady=(0, 24))
        self._history_box.columnconfigure(0, weight=1)

    def _go_home(self):
        self._hide_all()
        self._home_frame.grid(row=0, column=0, sticky="nsew")
        self._refresh_home()


    def _refresh_home(self):
        # draft button
        draft = InventoryController.get_draft()
        if draft:
            type_lbl = "Πλήρης" if draft.inv_type == "full" else f"Μερική ({draft.filter_kw})"
            self._draft_btn.configure(text=f"↩  Συνέχεια Απογραφής ({type_lbl})")
            self._draft_btn.grid(row=0, column=2, padx=16, pady=16, sticky="ew")
        else:
            self._draft_btn.grid_remove()

        # history
        for w in self._history_box.winfo_children():
            w.destroy()

        inventories = InventoryController.get_all()
        completed   = [iv for iv in inventories if iv.status != 'draft']

        if not completed:
            ctk.CTkLabel(
                self._history_box,
                text="Δεν υπάρχουν ολοκληρωμένες απογραφές ακόμα.",
                text_color="gray",
            ).grid(row=0, column=0, pady=32)
            return

        for i, inv in enumerate(completed):
            card = ctk.CTkFrame(self._history_box, corner_radius=8)
            card.grid(row=i, column=0, sticky="ew", padx=8, pady=4)
            card.columnconfigure(0, weight=1)

            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=16, pady=(10, 4))
            type_lbl = "Πλήρης" if inv.inv_type == "full" else f"Μερική ({inv.filter_kw or '—'})"
            ctk.CTkLabel(
                top, text=f"Απογραφή #{inv.id}  —  {type_lbl}",
                font=ctk.CTkFont(size=13, weight="bold"),
            ).pack(side="left")
            status_text, status_color = _INV_STATUS_MAP.get(
                inv.status, (inv.status, ("gray", "gray"))
            )
            ctk.CTkLabel(
                top, text=status_text, text_color=status_color,
                font=ctk.CTkFont(size=11, weight="bold"),
            ).pack(side="right")

            date_lbl = (inv.completed_at or inv.created_at)[:16]
            ctk.CTkLabel(
                card,
                text=f"Ημερομηνία: {date_lbl}   |   Προϊόντα: {len(inv.lines)}",
                text_color="gray", font=ctk.CTkFont(size=12), anchor="w",
            ).pack(fill="x", padx=16, pady=(0, 10))

    def _show_home_msg(self, text: str, *, error: bool = False):
        color = ("#e74c3c", "#e74c3c") if error else ("#27ae60", "#2ecc71")
        self._home_msg_lbl.configure(text_color=color)
        self._home_msg_var.set(text)
        self.after(5000, lambda: self._home_msg_var.set(""))

    # FILTER 
    def _build_filter_frame(self):
        self._filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._filter_frame.columnconfigure(0, weight=1)
        self._filter_frame.rowconfigure(0, weight=1)

        card = ctk.CTkFrame(self._filter_frame, corner_radius=16)
        card.grid(row=0, column=0)

        ctk.CTkLabel(
            card, text=" Μερική Απογραφή — Κριτήρια",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(padx=52, pady=(36, 8))
        ctk.CTkLabel(
            card,
            text="Εισάγετε λέξη-κλειδί για φιλτράρισμα προϊόντων\n"
                 "(αναζητά σε όνομα και περιγραφή).",
            text_color="gray", justify="center",
        ).pack(padx=52, pady=(0, 16))

        self._filter_entry = ctk.CTkEntry(card, width=320, placeholder_text="π.χ. σαμπουάν, serum…")
        self._filter_entry.pack(padx=52)
        self._filter_entry.bind("<Return>", lambda _: self._start_partial())

        self._filter_err = ctk.StringVar()
        ctk.CTkLabel(
            card, textvariable=self._filter_err,
            text_color=("#e74c3c", "#e74c3c"), font=ctk.CTkFont(size=12),
        ).pack(padx=52, pady=(8, 0))

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(pady=(10, 36))
        ctk.CTkButton(
            btn_row, text="← Πίσω", width=110,
            fg_color="transparent", border_width=1,
            text_color=("gray20", "gray80"), hover_color=("gray85", "gray25"),
            command=self._go_home,
        ).pack(side="left", padx=(0, 12))
        ctk.CTkButton(
            btn_row, text="🔍  Αναζήτηση", width=160,
            command=self._start_partial,
        ).pack(side="left")

    def _go_filter(self):
        self._filter_entry.delete(0, "end")
        self._filter_err.set("")
        self._hide_all()
        self._filter_frame.grid(row=0, column=0, sticky="nsew")


    # COUNT 
    def _build_count_frame(self):
        self._count_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._count_frame.columnconfigure(0, weight=1)
        self._count_frame.rowconfigure(2, weight=1)

        hdr = ctk.CTkFrame(self._count_frame, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=32, pady=(24, 8))
        hdr.columnconfigure(1, weight=1)
        ctk.CTkButton(
            hdr, text="← Ακύρωση", width=110,
            fg_color="transparent", border_width=1,
            text_color=("gray20", "gray80"), hover_color=("gray85", "gray25"),
            command=lambda: self._go_cancel_confirm(back_fn=self._go_home),
        ).grid(row=0, column=0, sticky="w")
        self._count_title = ctk.CTkLabel(
            hdr, text="Βήμα 1 — Καταγραφή Ποσοτήτων",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        self._count_title.grid(row=0, column=1, sticky="w", padx=20)

       # column headers
        cols = ctk.CTkFrame(self._count_frame, fg_color="transparent")
        cols.grid(row=1, column=0, sticky="ew", padx=32, pady=(0, 2))
        cols.columnconfigure(0, weight=1)
        for c, (txt, w) in enumerate([("Προϊόν", 0), ("Τρέχον\nΑπόθεμα", 110), ("Νέα Ποσότητα\n(απογραφή)", 130)]):
            ctk.CTkLabel(
                cols, text=txt, font=ctk.CTkFont(weight="bold"), anchor="w" if c == 0 else "center",
                width=w if w else 0,
            ).grid(row=0, column=c, sticky="ew" if c == 0 else "", padx=(8, 4))
        cols.columnconfigure(0, weight=1)

        self._count_scroll = ctk.CTkScrollableFrame(self._count_frame, corner_radius=10)
        self._count_scroll.grid(row=2, column=0, sticky="nsew", padx=32, pady=(0, 8))
        self._count_scroll.columnconfigure(0, weight=1)

        btn_row = ctk.CTkFrame(self._count_frame, fg_color="transparent")
        btn_row.grid(row=3, column=0, sticky="e", padx=32, pady=(0, 24))
        ctk.CTkButton(
            btn_row, text="Επόμενο →", width=160,
            command=self._collect_and_review,
        ).pack()


    def _go_count(self, resuming: bool = False):

        for w in self._count_scroll.winfo_children():
            w.destroy()
        self._count_entries.clear()

        inv = self._current_inv
        type_lbl = "Πλήρης" if inv.inv_type == "full" else f"Μερική — «{inv.filter_kw}»"
        self._count_title.configure(text=f"Βήμα 1 — Καταγραφή Ποσοτήτων  ({type_lbl})")

        for i, line in enumerate(inv.lines):
            bg = ("gray92", "gray18") if i % 2 == 0 else ("gray96", "gray15")
            row_f = ctk.CTkFrame(self._count_scroll, fg_color=bg, corner_radius=4)
            row_f.grid(row=i, column=0, sticky="ew", padx=4, pady=2)
            row_f.columnconfigure(0, weight=1)

            ctk.CTkLabel(row_f, text=line.product_name, anchor="w").grid(
                row=0, column=0, sticky="ew", padx=8, pady=6)
            ctk.CTkLabel(row_f, text=str(line.system_qty), width=110, anchor="center").grid(
                row=0, column=1, padx=4)

            entry = ctk.CTkEntry(row_f, width=110, placeholder_text="0", justify="center")
            if resuming and line.actual_qty > 0:
                entry.insert(0, str(line.actual_qty))
            entry.grid(row=0, column=2, padx=(4, 8), pady=6)
            self._count_entries[line.id] = entry

        self._hide_all()
        self._count_frame.grid(row=0, column=0, sticky="nsew")

    def _collect_and_review(self):
       
        self._actual_qtys = {}
        for line_id, entry in self._count_entries.items():
            raw = entry.get().strip()
            try:
                self._actual_qtys[line_id] = max(0, int(raw)) if raw else 0
            except ValueError:
                self._actual_qtys[line_id] = 0
        self._go_review()


    # REVIEW 
    def _build_review_frame(self):
        self._review_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._review_frame.columnconfigure(0, weight=1)
        self._review_frame.rowconfigure(2, weight=1)

        hdr = ctk.CTkFrame(self._review_frame, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=32, pady=(24, 8))
        hdr.columnconfigure(1, weight=1)
        ctk.CTkButton(
            hdr, text="← Πίσω", width=110,
            fg_color="transparent", border_width=1,
            text_color=("gray20", "gray80"), hover_color=("gray85", "gray25"),
            command=lambda: self._go_count(),
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            hdr, text="Βήμα 2 — Επιβεβαίωση Αποκλίσεων",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=1, sticky="w", padx=20)

        # summary stats
        self._review_stats = ctk.CTkLabel(
            self._review_frame, text="", text_color="gray",
            font=ctk.CTkFont(size=12), anchor="w",
        )
        self._review_stats.grid(row=1, column=0, sticky="w", padx=32, pady=(0, 4))

        self._review_scroll = ctk.CTkScrollableFrame(self._review_frame, corner_radius=10)
        self._review_scroll.grid(row=2, column=0, sticky="nsew", padx=32, pady=(0, 8))
        self._review_scroll.columnconfigure(0, weight=1)

        btn_row = ctk.CTkFrame(self._review_frame, fg_color="transparent")
        btn_row.grid(row=3, column=0, sticky="ew", padx=32, pady=(0, 24))
        btn_row.columnconfigure(0, weight=1)

        ctk.CTkButton(
            btn_row, text="✘  Ακύρωση", width=140,
            fg_color=("#e74c3c", "#922b21"), hover_color=("#c0392b", "#7b241c"),
            command=lambda: self._go_cancel_confirm(back_fn=self._go_review),
        ).grid(row=0, column=0, sticky="w")

        right = ctk.CTkFrame(btn_row, fg_color="transparent")
        right.grid(row=0, column=1, sticky="e")
        ctk.CTkButton(
            right, text=" Αποθήκευση Προσωρινής", width=210,
            fg_color=("#e67e22", "#d35400"), hover_color=("#d35400", "#b7770d"),
            command=self._save_draft,
        ).pack(side="left", padx=(0, 12))
        ctk.CTkButton(
            right, text="✓  Ολοκλήρωση", width=160,
            command=self._complete,
        ).pack(side="left")

    def _go_review(self):
        """Step 6: render deviation table."""
        for w in self._review_scroll.winfo_children():
            w.destroy()

        # column headers
        for c, txt in enumerate(["Προϊόν", "Τρέχον", "Νέο", "Απόκλιση"]):
            ctk.CTkLabel(
                self._review_scroll, text=txt,
                font=ctk.CTkFont(weight="bold"),
                anchor="w" if c == 0 else "center",
            ).grid(row=0, column=c, sticky="ew" if c == 0 else "", padx=8, pady=6)
        self._review_scroll.columnconfigure(0, weight=1)
        ctk.CTkFrame(self._review_scroll, height=1, fg_color="gray40").grid(
            row=1, column=0, columnspan=4, sticky="ew", padx=4)

        n_diff = 0
        for i, line in enumerate(self._current_inv.lines, start=2):
            actual = self._actual_qtys.get(line.id, 0)
            dev    = actual - line.system_qty
            if dev != 0:
                n_diff += 1
            bg = ("gray92", "gray18") if i % 2 == 0 else ("gray96", "gray15")

            ctk.CTkLabel(
                self._review_scroll, text=line.product_name, anchor="w", fg_color=bg, corner_radius=4,
            ).grid(row=i, column=0, sticky="ew", padx=4, pady=2)
            ctk.CTkLabel(
                self._review_scroll, text=str(line.system_qty), anchor="center", fg_color=bg, corner_radius=4,
            ).grid(row=i, column=1, padx=4, pady=2)
            ctk.CTkLabel(
                self._review_scroll, text=str(actual), anchor="center", fg_color=bg, corner_radius=4,
            ).grid(row=i, column=2, padx=4, pady=2)

            if dev == 0:
                dev_txt, dev_color = "0", ("gray50", "gray50")
            elif dev > 0:
                dev_txt, dev_color = f"+{dev}", ("#27ae60", "#2ecc71")
            else:
                dev_txt, dev_color = str(dev), ("#e74c3c", "#e74c3c")
            ctk.CTkLabel(
                self._review_scroll, text=dev_txt,
                text_color=dev_color, anchor="center",
                font=ctk.CTkFont(weight="bold"),
                fg_color=bg, corner_radius=4,
            ).grid(row=i, column=3, padx=4, pady=2)

        n_total = len(self._current_inv.lines)
        self._review_stats.configure(
            text=f"Σύνολο προϊόντων: {n_total}   |   Αποκλίσεις: {n_diff}"
        )
        self._hide_all()
        self._review_frame.grid(row=0, column=0, sticky="nsew")

    # CANCEL CONFIRM 
    def _build_cancel_confirm_frame(self):
        self._cancel_confirm_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._cancel_confirm_frame.columnconfigure(0, weight=1)
        self._cancel_confirm_frame.rowconfigure(0, weight=1)

        card = ctk.CTkFrame(self._cancel_confirm_frame, corner_radius=16)
        card.grid(row=0, column=0)

        ctk.CTkLabel(
            card, text="✘  Ακύρωση Απογραφής",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(padx=52, pady=(36, 10))
        ctk.CTkLabel(
            card,
            text="Είστε σίγουροι;\nΔεν θα ενημερωθούν τα αποθέματα.",
            text_color="gray", justify="center",
        ).pack(padx=52, pady=(0, 28))

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(pady=(0, 36))
        ctk.CTkButton(
            btn_row, text="Όχι, επιστροφή", width=160,
            fg_color="transparent", border_width=1,
            text_color=("gray20", "gray80"), hover_color=("gray85", "gray25"),
            command=lambda: self._cancel_back_fn(),
        ).pack(side="left", padx=(0, 12))
        ctk.CTkButton(
            btn_row, text="Ναι, ακύρωση", width=160,
            fg_color=("#e74c3c", "#922b21"), hover_color=("#c0392b", "#7b241c"),
            command=self._execute_cancel,
        ).pack(side="left")

    def _go_cancel_confirm(self, back_fn):
        self._cancel_back_fn = back_fn
        self._hide_all()
        self._cancel_confirm_frame.grid(row=0, column=0, sticky="nsew")

    def _execute_cancel(self):
        if self._current_inv:
            InventoryController.cancel_inventory(self._current_inv.id)
            self._current_inv = None
        self._go_home()
        self._show_home_msg("Η απογραφή ακυρώθηκε.")

    # RESULT
    def _build_result_frame(self):
        self._result_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._result_frame.columnconfigure(0, weight=1)
        self._result_frame.rowconfigure(2, weight=1)

        hdr = ctk.CTkFrame(self._result_frame, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=32, pady=(24, 4))
        hdr.columnconfigure(1, weight=1)
        ctk.CTkButton(
            hdr, text="← Νέα Απογραφή", width=150,
            fg_color="transparent", border_width=1,
            text_color=("gray20", "gray80"), hover_color=("gray85", "gray25"),
            command=self._go_home,
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            hdr, text="✔  Απογραφή Ολοκληρώθηκε",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=("#27ae60", "#2ecc71"),
        ).grid(row=0, column=1, sticky="w", padx=20)

        self._result_meta = ctk.CTkLabel(
            self._result_frame, text="",
            text_color="gray", font=ctk.CTkFont(size=12), anchor="w",
        )
        self._result_meta.grid(row=1, column=0, sticky="w", padx=32, pady=(0, 4))

        self._result_scroll = ctk.CTkScrollableFrame(self._result_frame, corner_radius=10)
        self._result_scroll.grid(row=2, column=0, sticky="nsew", padx=32, pady=(0, 24))
        self._result_scroll.columnconfigure(0, weight=1)

    def _go_result(self):
     
        for w in self._result_scroll.winfo_children():
            w.destroy()

        inv = self._current_inv
        type_lbl = "Πλήρης" if inv.inv_type == "full" else f"Μερική ({inv.filter_kw})"
        date_lbl = (inv.completed_at or "")[:16]
        self._result_meta.configure(
            text=f"Απογραφή #{inv.id}   |   {type_lbl}   |   {date_lbl}"
        )

        for c, txt in enumerate(["Προϊόν", "Παλαιό Απόθεμα", "Νέο Απόθεμα", "Απόκλιση"]):
            ctk.CTkLabel(
                self._result_scroll, text=txt,
                font=ctk.CTkFont(weight="bold"),
                anchor="w" if c == 0 else "center",
            ).grid(row=0, column=c, sticky="ew" if c == 0 else "", padx=8, pady=6)
        self._result_scroll.columnconfigure(0, weight=1)
        ctk.CTkFrame(self._result_scroll, height=1, fg_color="gray40").grid(
            row=1, column=0, columnspan=4, sticky="ew", padx=4)

        for i, line in enumerate(inv.lines, start=2):
            dev = line.deviation
            bg  = ("gray92", "gray18") if i % 2 == 0 else ("gray96", "gray15")

            ctk.CTkLabel(
                self._result_scroll, text=line.product_name, anchor="w",
                fg_color=bg, corner_radius=4,
            ).grid(row=i, column=0, sticky="ew", padx=4, pady=2)
            ctk.CTkLabel(
                self._result_scroll, text=str(line.system_qty), anchor="center",
                fg_color=bg, corner_radius=4,
            ).grid(row=i, column=1, padx=4, pady=2)
            ctk.CTkLabel(
                self._result_scroll, text=str(line.actual_qty), anchor="center",
                fg_color=bg, corner_radius=4,
            ).grid(row=i, column=2, padx=4, pady=2)

            if dev == 0:
                dev_txt, dev_col = "0", ("gray50", "gray50")
            elif dev > 0:
                dev_txt, dev_col = f"+{dev}", ("#27ae60", "#2ecc71")
            else:
                dev_txt, dev_col = str(dev), ("#e74c3c", "#e74c3c")
            ctk.CTkLabel(
                self._result_scroll, text=dev_txt,
                text_color=dev_col, anchor="center",
                font=ctk.CTkFont(weight="bold"),
                fg_color=bg, corner_radius=4,
            ).grid(row=i, column=3, padx=4, pady=2)

        self._hide_all()
        self._result_frame.grid(row=0, column=0, sticky="nsew")

    # actions
    def _start_full(self):
        try:
            self._current_inv = InventoryController.start_full_inventory()
            self._go_count(resuming=False)
        except InventoryError as e:
            self._show_home_msg(str(e), error=True)

    def _go_filter(self):
        self._filter_entry.delete(0, "end")
        self._filter_err.set("")
        self._hide_all()
        self._filter_frame.grid(row=0, column=0, sticky="nsew")

    def _start_partial(self):
        kw = self._filter_entry.get().strip()
        try:
            self._current_inv = InventoryController.start_partial_inventory(kw)
            self._go_count(resuming=False)
        except InventoryError as e:
            self._filter_err.set(str(e))

    def _resume_draft(self):
        draft = InventoryController.get_draft()
        if draft:
            self._current_inv = draft
            self._go_count(resuming=True)

    def _save_draft(self):
        """Alt flow 2: save progress without updating product stocks."""
        InventoryController.save_draft(self._current_inv.id, self._actual_qtys)
        self._current_inv = None
        self._go_home()
        self._show_home_msg("✔ Η απογραφή αποθηκεύτηκε προσωρινά.")

    def _complete(self):
        """Basic flow steps 7–10: finalize, update stocks, show receipt."""
        inv = InventoryController.complete_inventory(
            self._current_inv.id, self._actual_qtys
        )
        self._current_inv = inv
        self._go_result()
