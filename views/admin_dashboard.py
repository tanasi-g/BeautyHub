import customtkinter as ctk
from views.base_dashboard import BaseDashboard
from controllers.auth_controller import AuthController
from views.notifications_page import NotificationsPage
from controllers.eshop_controller import EShopController, EShopError
from pathlib import Path
from tkinter import filedialog
from controllers.service_controller import ServiceController, ServiceError

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
        self._register_page("inventory",     _PlaceholderPage(self._content, "Αποθήκη"))
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

