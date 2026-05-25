import customtkinter as ctk
from views.base_dashboard import BaseDashboard
from views.notifications_page import NotificationsPage
from controllers.service_controller import ServiceController
from controllers.salon_controller import SalonController
from utils.session import Session
from controllers.appointment_controller import AppointmentController, AppointmentError
from datetime import datetime, timedelta




class CustomerDashboard(BaseDashboard):
    NAV_ITEMS = [
        ("Αρχική",           "home"),
        ("Κομμωτήρια",       "salons"),
        ("E-Shop",            "eshop"),
        ("Καλάθι",           "cart"),
        ("Παραγγελίες μου",  "orders"),
        ("Ραντεβού",         "appointments"),
        ("Ειδοποιήσεις",     "notifications"),
    ]

    def _build_pages(self):
        nav = self._show_page
        self._register_page("home",          _HomePage(self._content))
        self._register_page("salons",        _SalonSearchPage(self._content))
        self._register_page("eshop",         _PlaceholderPage(self._content, "E-Shop"))
        self._register_page("cart",          _PlaceholderPage(self._content, "Καλάθι"))
        self._register_page("orders",        _PlaceholderPage(self._content, "Παραγγελίες μου"))
        self._register_page("appointments",  _AppointmentsPage(self._content))
        self._register_page("notifications", NotificationsPage(self._content))

class _HomePage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        box = ctk.CTkFrame(self, corner_radius=16)
        box.grid(row=0, column=0)
        ctk.CTkLabel(box, text="", font=ctk.CTkFont(size=52)).pack(pady=(32, 8))
        ctk.CTkLabel(
            box, text="Καλωσήρθατε στο BeautyHub!",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(padx=40)
        ctk.CTkLabel(
            box,
            text="Ψωνίστε από το E-Shop, κλείστε ραντεβού\nκαι δείτε το ιστορικό παραγγελιών σας.",
            text_color="gray",
            justify="center",
        ).pack(pady=(8, 32), padx=40)


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




class _SalonSearchPage(ctk.CTkFrame):
    _RES_COLS = ["Όνομα", "Πόλη", "Διεύθυνση", "Τηλέφωνο", ""]
    _SVC_COLS = ["Υπηρεσία", "Διάρκεια", "Τιμή"]
    _ALL_SVC  = "Όλες οι υπηρεσίες"

    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self._services_map: dict[str, int] = {}
        self._build_search_view()
        self._build_profile_view()
        self._show_search()

    #  lifecycle
    def refresh(self):
        self._show_search()
        self._load_services_combo()
        self._do_search()

    #  SEARCH / RESULTS VIEW
    def _build_search_view(self):
        self._search_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._search_frame.columnconfigure(0, weight=1)
        self._search_frame.rowconfigure(2, weight=1)

        # title
        ctk.CTkLabel(
            self._search_frame, text="🔍 Αναζήτηση Κομμωτηρίων",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=32, pady=(24, 12))

        # filter search bar 
        bar = ctk.CTkFrame(self._search_frame, corner_radius=10)
        bar.grid(row=1, column=0, sticky="ew", padx=32, pady=(0, 12))
        bar.columnconfigure(1, weight=1)

        ctk.CTkLabel(bar, text="Αναζήτηση:", anchor="w").grid(
            row=0, column=0, padx=(16, 8), pady=14,
        )
        self._kw_entry = ctk.CTkEntry(
            bar, placeholder_text="Όνομα, πόλη ή διεύθυνση…", height=36,
        )
        self._kw_entry.grid(row=0, column=1, sticky="ew", padx=(0, 12), pady=14)
        self._kw_entry.bind("<Return>", lambda _: self._do_search())

        ctk.CTkLabel(bar, text="Υπηρεσία:", anchor="w").grid(
            row=0, column=2, padx=(0, 8), pady=14,
        )
        self._svc_combo = ctk.CTkComboBox(
            bar, values=[self._ALL_SVC], width=200, state="readonly",
        )
        self._svc_combo.grid(row=0, column=3, padx=(0, 12), pady=14)
        self._svc_combo.set(self._ALL_SVC)

        ctk.CTkButton(
            bar, text="🔍 Αναζήτηση", width=130,
            command=self._do_search,
        ).grid(row=0, column=4, padx=(0, 8), pady=14)
        ctk.CTkButton(
            bar, text="✕ Καθαρισμός", width=130,
            fg_color="transparent", border_width=1,
            text_color=("gray20", "gray80"), hover_color=("gray85", "gray25"),
            command=self._clear_filters,
        ).grid(row=0, column=5, padx=(0, 16), pady=14)

        # results table 
        self._res_table = ctk.CTkScrollableFrame(self._search_frame, corner_radius=10)
        self._res_table.grid(row=2, column=0, sticky="nsew", padx=32, pady=(0, 24))
        for i in range(len(self._RES_COLS)):
            self._res_table.columnconfigure(i, weight=1)

    def _load_services_combo(self):
        services = ServiceController.get_all()
        self._services_map = {s.name: s.id for s in services}
        self._svc_combo.configure(values=[self._ALL_SVC] + list(self._services_map.keys()))
        self._svc_combo.set(self._ALL_SVC)

    def _do_search(self):
        """Βήμα 2 — εκτέλεση αναζήτησης με τα τρέχοντα κριτήρια."""
        keyword    = self._kw_entry.get()
        svc_name   = self._svc_combo.get()
        service_id = self._services_map.get(svc_name) if svc_name != self._ALL_SVC else None
        results    = SalonController.search(keyword, service_id)
        self._render_results(results)

    def _clear_filters(self):
        """Εναλλακτική ροή 1 — καθαρισμός φίλτρων, επιστροφή στο βήμα 2."""
        self._kw_entry.delete(0, "end")
        self._svc_combo.set(self._ALL_SVC)
        self._do_search()

    def _render_results(self, salons: list):
        """Βήμα 3 — εμφάνιση αποτελεσμάτων (ή κενή κατάσταση)."""
        for w in self._res_table.winfo_children():
            w.destroy()

        if not salons:
            # εναλλακτική ροή 2 — δεν βρέθηκαν αποτελέσματα
            ctk.CTkLabel(
                self._res_table,
                text="Δεν βρέθηκαν κομμωτήρια με τα επιλεγμένα κριτήρια.",
                text_color="gray",
            ).grid(row=0, column=0, columnspan=len(self._RES_COLS), pady=(24, 6))
            ctk.CTkLabel(
                self._res_table,
                text="Δοκιμάστε να τροποποιήσετε τα φίλτρα αναζήτησης.",
                text_color=("gray55", "gray55"), font=ctk.CTkFont(size=12),
            ).grid(row=1, column=0, columnspan=len(self._RES_COLS), pady=(0, 24))
            return

        for col, h in enumerate(self._RES_COLS):
            ctk.CTkLabel(
                self._res_table, text=h,
                font=ctk.CTkFont(weight="bold"), anchor="w",
            ).grid(row=0, column=col, sticky="ew", padx=8, pady=6)
        ctk.CTkFrame(self._res_table, height=1, fg_color="gray40").grid(
            row=1, column=0, columnspan=len(self._RES_COLS), sticky="ew", padx=4,
        )

        for r_idx, salon in enumerate(salons, start=2):
            bg = ("gray92", "gray18") if r_idx % 2 == 0 else ("gray96", "gray15")
            for col, val in enumerate([
                salon.name, salon.city, salon.address, salon.phone or "—"
            ]):
                ctk.CTkLabel(
                    self._res_table, text=val, anchor="w",
                    fg_color=bg, corner_radius=4,
                ).grid(row=r_idx, column=col, sticky="ew", padx=4, pady=2)

            # βήμα 4 — επιλογή κομμωτηρίου
            ctk.CTkButton(
                self._res_table, text="Προφίλ →", width=100, height=26,
                fg_color=("gray70", "gray30"), hover_color=("gray60", "gray40"),
                font=ctk.CTkFont(size=11),
                command=lambda s=salon: self._open_profile(s),
            ).grid(row=r_idx, column=4, padx=4, pady=2)

    #  Salon PROFILE VIEW 
    def _build_profile_view(self):
        self._profile_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._profile_frame.columnconfigure(0, weight=1)
        self._profile_frame.rowconfigure(2, weight=1)

        # header
        hdr = ctk.CTkFrame(self._profile_frame, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=32, pady=(24, 4))
        hdr.columnconfigure(1, weight=1)
        ctk.CTkButton(
            hdr, text="← Πίσω", width=100,
            fg_color="transparent", border_width=1,
            text_color=("gray20", "gray80"), hover_color=("gray85", "gray25"),
            command=self._show_search,
        ).grid(row=0, column=0, sticky="w")
        self._profile_title = ctk.CTkLabel(
            hdr, text="", font=ctk.CTkFont(size=20, weight="bold"),
        )
        self._profile_title.grid(row=0, column=1, sticky="w", padx=20)

        # info card
        self._info_card = ctk.CTkFrame(self._profile_frame, corner_radius=12)
        self._info_card.grid(row=1, column=0, sticky="ew", padx=32, pady=(8, 12))
        self._info_card.columnconfigure((0, 1, 2, 3), weight=1)

        # services section
        svc_wrap = ctk.CTkFrame(self._profile_frame, fg_color="transparent")
        svc_wrap.grid(row=2, column=0, sticky="nsew", padx=32, pady=(0, 24))
        svc_wrap.columnconfigure(0, weight=1)
        svc_wrap.rowconfigure(1, weight=1)
        ctk.CTkLabel(
            svc_wrap, text="Υπηρεσίες κομμωτηρίου",
            font=ctk.CTkFont(size=14, weight="bold"), anchor="w",
        ).grid(row=0, column=0, sticky="w", pady=(0, 6))
        self._svc_table = ctk.CTkScrollableFrame(svc_wrap, corner_radius=10)
        self._svc_table.grid(row=1, column=0, sticky="nsew")
        for i in range(len(self._SVC_COLS)):
            self._svc_table.columnconfigure(i, weight=1)

    def _open_profile(self, salon):
        """Βήμα 5 — ανάκτηση και εμφάνιση προφίλ κομμωτηρίου."""
        self._profile_title.configure(text=salon.name)

        # info card fields
        for w in self._info_card.winfo_children():
            w.destroy()
        for col, (icon, label, val) in enumerate([
            ("", "Πόλη",       salon.city),
            ("", "Διεύθυνση",  salon.address),
            ("", "Τηλέφωνο",   salon.phone or "—"),
            ("",  "Email",      salon.email or "—"),
        ]):
            cell = ctk.CTkFrame(self._info_card, fg_color="transparent")
            cell.grid(row=0, column=col, padx=20, pady=16, sticky="nsew")
            ctk.CTkLabel(
                cell, text=f"{icon}  {label}",
                text_color="gray", font=ctk.CTkFont(size=11), anchor="w",
            ).pack(anchor="w")
            ctk.CTkLabel(
                cell, text=val,
                font=ctk.CTkFont(size=13, weight="bold"),
                anchor="w", wraplength=170,
            ).pack(anchor="w")

        # services table
        for w in self._svc_table.winfo_children():
            w.destroy()

        services = SalonController.get_services(salon.id)
        if not services:
            ctk.CTkLabel(
                self._svc_table,
                text="Δεν έχουν ανατεθεί υπηρεσίες σε αυτό το κομμωτήριο.",
                text_color="gray",
            ).grid(row=0, column=0, columnspan=3, pady=20)
        else:
            for col, h in enumerate(self._SVC_COLS):
                ctk.CTkLabel(
                    self._svc_table, text=h,
                    font=ctk.CTkFont(weight="bold"), anchor="w",
                ).grid(row=0, column=col, sticky="ew", padx=8, pady=6)
            ctk.CTkFrame(self._svc_table, height=1, fg_color="gray40").grid(
                row=1, column=0, columnspan=3, sticky="ew", padx=4,
            )
            for r_idx, svc in enumerate(services, start=2):
                bg = ("gray92", "gray18") if r_idx % 2 == 0 else ("gray96", "gray15")
                for col, val in enumerate([
                    svc.name, f"{svc.duration_min} λεπτά", f"{svc.price:.2f} €"
                ]):
                    ctk.CTkLabel(
                        self._svc_table, text=val, anchor="w",
                        fg_color=bg, corner_radius=4,
                    ).grid(row=r_idx, column=col, sticky="ew", padx=4, pady=2)

        self._show_profile()

    # navigation
    def _show_search(self):
        self._profile_frame.grid_remove()
        self._search_frame.grid(row=0, column=0, sticky="nsew")

    def _show_profile(self):
        self._search_frame.grid_remove()
        self._profile_frame.grid(row=0, column=0, sticky="nsew")




# ============================================================
#  Appointments — UC 2.2  
# ============================================================

_APPT_STATUS_MAP = {
    'pending':   (" Εκκρεμεί",    ("#e67e22", "#d68910")),
    'confirmed': ("✔ Επιβεβαιωμένο", ("#27ae60", "#2ecc71")),
    'done':      ("✔ Ολοκληρώθηκε",  ("#27ae60", "#2ecc71")),
    'cancelled': ("✘ Ακυρώθηκε",     ("#e74c3c", "#922b21")),
}


class _AppointmentsPage(ctk.CTkFrame):

    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # wizard state — new appointment
        self._sel_service   = None   # Service object
        self._sel_employee  = None   # dict {id, name}  (id may be None = «any»)
        self._sel_slot      = None   # dict {time_str, start_iso, employee_id, employee_name}
        self._cal_date      = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)

        # modification state — UC 2.12
        self._mod_appt      = None   # AppointmentDetail being modified
        self._mod_sel_slot  = None   # newly chosen slot for reschedule
        self._mod_cal_date  = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)


        # shared cal-frame mode ("new" | "mod")
        self._cal_mode        = "new"
        self._cal_back_action = None   # set by _go_cal / _go_mod_cal
        self._unavail_back_fn = None   # set by _go_unavailable


        self._build_list_frame()
        self._build_svc_frame()
        self._build_emp_frame()
        self._build_cal_frame()
        self._build_confirm_frame()
        self._build_unavailable_frame()
        self._build_mod_detail_frame()
        self._build_mod_confirm_frame()
        self._build_cancel_confirm_frame()

        self._go_list()

    # state router
    def _hide_all(self):
        for f in (
            self._list_frame, self._svc_frame, self._emp_frame,
            self._cal_frame, self._confirm_frame, self._unavailable_frame,
            self._mod_detail_frame, self._mod_confirm_frame, self._cancel_confirm_frame,


        ):
            f.grid_remove()

    def refresh(self):
        self._go_list()

    #LIST 
    def _build_list_frame(self):
        self._list_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._list_frame.columnconfigure(0, weight=1)
        self._list_frame.rowconfigure(2, weight=1)

        hdr = ctk.CTkFrame(self._list_frame, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=32, pady=(24, 8))
        hdr.columnconfigure(0, weight=1)
        ctk.CTkLabel(
            hdr, text=" Ραντεβού μου",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(
            hdr, text="+ Νέο Ραντεβού", width=150,
            command=self._go_svc,
        ).grid(row=0, column=1, sticky="e")

        self._list_msg_var = ctk.StringVar()
        ctk.CTkLabel(
            self._list_frame, textvariable=self._list_msg_var,
            font=ctk.CTkFont(size=12), text_color=("#27ae60", "#2ecc71"), anchor="w",
        ).grid(row=1, column=0, sticky="ew", padx=32, pady=(0, 4))

        self._list_container = ctk.CTkScrollableFrame(self._list_frame, corner_radius=10)
        self._list_container.grid(row=2, column=0, sticky="nsew", padx=32, pady=(0, 24))
        self._list_container.columnconfigure(0, weight=1)

    def _go_list(self):
        self._hide_all()
        self._list_frame.grid(row=0, column=0, sticky="nsew")
        self._refresh_list()

    def _refresh_list(self):
        for w in self._list_container.winfo_children():
            w.destroy()

        user = Session.current_user()
        appts = AppointmentController.get_by_customer(user.id)

        if not appts:
            ctk.CTkLabel(
                self._list_container,
                text="Δεν έχετε ραντεβού ακόμα.\nΠατήστε «+ Νέο Ραντεβού» για να κλείσετε.",
                text_color="gray", justify="center",
            ).grid(row=0, column=0, pady=48)
            return

        for i, appt in enumerate(appts):
            card = ctk.CTkFrame(self._list_container, corner_radius=10)
            card.grid(row=i, column=0, sticky="ew", padx=8, pady=6)
            card.columnconfigure(0, weight=1)

            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=16, pady=(12, 4))
            ctk.CTkLabel(
                top,
                text=f"📅  {appt.scheduled_at}  —  {appt.service_name}",
                font=ctk.CTkFont(size=13, weight="bold"),
            ).pack(side="left")
            status_text, status_color = _APPT_STATUS_MAP.get(
                appt.status, (appt.status, ("gray", "gray"))
            )
            ctk.CTkLabel(
                top, text=status_text, text_color=status_color,
                font=ctk.CTkFont(size=11, weight="bold"),
            ).pack(side="right")

            details = (
                f"Υπάλληλος: {appt.employee_name}   |   "
                f"Διάρκεια: {appt.duration_min} λεπτά   |   "
                f"Τιμή: {appt.price:.2f} €"
            )
            if appt.notes:
                details += f"   |   Σημείωση: {appt.notes}"
            ctk.CTkLabel(
                card, text=details, anchor="w",
                text_color="gray", font=ctk.CTkFont(size=12),
            ).pack(fill="x", padx=16, pady=(0, 6))

            if appt.status in ("pending", "confirmed"):
                footer = ctk.CTkFrame(card, fg_color="transparent")
                footer.pack(fill="x", padx=12, pady=(0, 10))
                ctk.CTkButton(
                    footer, text="Τροποποίηση →", width=140, height=28,
                    fg_color=("#2980b9", "#1a6fa0"), hover_color=("#2471a3", "#155f8a"),
                    font=ctk.CTkFont(size=11),
                    command=lambda a=appt: self._go_mod_detail(a),
                ).pack(side="right")

    #STEP 1 
    def _build_svc_frame(self):
        self._svc_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._svc_frame.columnconfigure(0, weight=1)
        self._svc_frame.rowconfigure(1, weight=1)

        hdr = ctk.CTkFrame(self._svc_frame, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=32, pady=(24, 12))
        hdr.columnconfigure(1, weight=1)
        ctk.CTkButton(
            hdr, text="← Πίσω", width=100,
            fg_color="transparent", border_width=1,
            text_color=("gray20", "gray80"), hover_color=("gray85", "gray25"),
            command=self._go_list,
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            hdr, text="Βήμα 1 — Επιλογή Υπηρεσίας",
       font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=1, sticky="w", padx=20)

        self._svc_cards = ctk.CTkScrollableFrame(self._svc_frame, corner_radius=10)
        self._svc_cards.grid(row=1, column=0, sticky="nsew", padx=32, pady=(0, 24))
        self._svc_cards.columnconfigure(0, weight=1)

    def _go_svc(self):
        self._sel_service  = None
        self._sel_employee = None
        self._sel_slot     = None
        self._hide_all()
        self._svc_frame.grid(row=0, column=0, sticky="nsew")
        self._load_svc_cards()

    def _load_svc_cards(self):
        for w in self._svc_cards.winfo_children():
            w.destroy()

        services = AppointmentController.get_active_services()
        if not services:
            ctk.CTkLabel(
                self._svc_cards,
                text="Δεν υπάρχουν διαθέσιμες υπηρεσίες.",
                text_color="gray",
            ).grid(row=0, column=0, pady=48)
            return

        for i, svc in enumerate(services):
            card = ctk.CTkFrame(self._svc_cards, corner_radius=10)
            card.grid(row=i, column=0, sticky="ew", padx=8, pady=5)
            card.columnconfigure(0, weight=1)

            info = ctk.CTkFrame(card, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True, padx=16, pady=14)
            ctk.CTkLabel(
                info, text=svc.name,
                font=ctk.CTkFont(size=13, weight="bold"), anchor="w",
            ).pack(anchor="w")
            ctk.CTkLabel(
                info,
                text=f"{svc.duration_min} λεπτά  •  {svc.price:.2f} €",
                text_color="gray", font=ctk.CTkFont(size=12), anchor="w",
            ).pack(anchor="w")

            ctk.CTkButton(
                card, text="Επιλογή →", width=110,
                command=lambda s=svc: self._pick_service(s),
            ).pack(side="right", padx=16, pady=14)

    def _pick_service(self, service):
        self._sel_service = service
        self._go_emp()

    #STEP 2 — choose employee
    def _build_emp_frame(self):
        self._emp_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._emp_frame.columnconfigure(0, weight=1)
        self._emp_frame.rowconfigure(1, weight=1)

        hdr = ctk.CTkFrame(self._emp_frame, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=32, pady=(24, 12))
        hdr.columnconfigure(1, weight=1)
        ctk.CTkButton(
            hdr, text="← Πίσω", width=100,
            fg_color="transparent", border_width=1,
            text_color=("gray20", "gray80"), hover_color=("gray85", "gray25"),
            command=self._go_svc,
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            hdr, text="Βήμα 2 — Επιλογή Υπαλλήλου",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=1, sticky="w", padx=20)

        self._emp_cards = ctk.CTkScrollableFrame(self._emp_frame, corner_radius=10)
        self._emp_cards.grid(row=1, column=0, sticky="nsew", padx=32, pady=(0, 24))
        self._emp_cards.columnconfigure(0, weight=1)

    def _go_emp(self):
        self._sel_employee = None
        self._sel_slot     = None
        self._hide_all()
        self._emp_frame.grid(row=0, column=0, sticky="nsew")
        self._load_emp_cards()

    def _load_emp_cards(self):
        for w in self._emp_cards.winfo_children():
            w.destroy()

        employees = AppointmentController.get_employees()  

        for i, emp in enumerate(employees):
            card = ctk.CTkFrame(self._emp_cards, corner_radius=10)
            card.grid(row=i, column=0, sticky="ew", padx=8, pady=5)
            card.columnconfigure(0, weight=1)
            ctk.CTkLabel(
                card, text=emp["name"],
                font=ctk.CTkFont(size=13, weight="bold"), anchor="w",
            ).pack(side="left", padx=16, pady=14)
            ctk.CTkButton(
                card, text="Επιλογή →", width=110,
                command=lambda e=emp: self._pick_employee(e),
            ).pack(side="right", padx=16, pady=14)

    def _pick_employee(self, emp: dict):
        self._sel_employee = emp
        self._cal_date = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        self._go_cal()

    # STEP 3 — calendar + slots
    def _build_cal_frame(self):
        self._cal_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._cal_frame.columnconfigure(0, weight=1)
        self._cal_frame.rowconfigure(2, weight=1)

        hdr = ctk.CTkFrame(self._cal_frame, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=32, pady=(24, 8))
        hdr.columnconfigure(1, weight=1)
        ctk.CTkButton(
            hdr, text="← Πίσω", width=100,
            fg_color="transparent", border_width=1,
            text_color=("gray20", "gray80"), hover_color=("gray85", "gray25"),
            command=lambda: self._cal_back_action(),
        ).grid(row=0, column=0, sticky="w")
        self._cal_title_label = ctk.CTkLabel(
            hdr, text="Βήμα 3 — Επιλογή Ημερομηνίας & Ώρας",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        self._cal_title_label.grid(row=0, column=1, sticky="w", padx=20)

        # week navigation
        week_nav = ctk.CTkFrame(self._cal_frame, corner_radius=8)
        week_nav.grid(row=1, column=0, sticky="ew", padx=32, pady=(0, 8))
        week_nav.columnconfigure(1, weight=1)
        ctk.CTkButton(
            week_nav, text="◀  Προηγ. εβδομάδα", width=170,
            fg_color="transparent", border_width=1,
            text_color=("gray20", "gray80"), hover_color=("gray85", "gray25"),
            command=self._prev_week,
        ).grid(row=0, column=0, padx=12, pady=10)
        self._week_label = ctk.CTkLabel(
            week_nav, text="", font=ctk.CTkFont(size=13, weight="bold"),
        )


        self._week_label.grid(row=0, column=1)
        ctk.CTkButton(
            week_nav, text="Επόμ. εβδομάδα  ▶", width=170,
            fg_color="transparent", border_width=1,
            text_color=("gray20", "gray80"), hover_color=("gray85", "gray25"),
            command=self._next_week,
        ).grid(row=0, column=2, padx=12, pady=10)

        # day buttons + slot grid (built dynamically)
        self._day_slot_area = ctk.CTkScrollableFrame(self._cal_frame, corner_radius=10)
        self._day_slot_area.grid(row=2, column=0, sticky="nsew", padx=32, pady=(0, 24))

    def _go_cal(self):
        self._cal_mode = "new"
        self._cal_back_action = self._go_emp
        self._cal_title_label.configure(text="Βήμα 3 — Επιλογή Ημερομηνίας & Ώρας")
        self._hide_all()
        self._cal_frame.grid(row=0, column=0, sticky="nsew")
        self._render_week()

    def _go_mod_cal(self):
        self._cal_mode = "mod"
        self._cal_back_action = self._go_mod_detail
        self._cal_title_label.configure(text="Νέα Ημερομηνία & Ώρα")
        self._mod_cal_date = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        self._hide_all()
        self._cal_frame.grid(row=0, column=0, sticky="nsew")
        self._render_week()

    def _prev_week(self):
        d = self._mod_cal_date if self._cal_mode == "mod" else self._cal_date
        candidate = d - timedelta(weeks=1)
        today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        if candidate < today:
            candidate = today
        if self._cal_mode == "mod":
            self._mod_cal_date = candidate
        else:
            self._cal_date = candidate
        self._render_week()

    def _next_week(self):
        if self._cal_mode == "mod":
            self._mod_cal_date += timedelta(weeks=1)
        else:
            self._cal_date += timedelta(weeks=1)
        self._render_week()

    def _render_week(self):
        today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        d = self._mod_cal_date if self._cal_mode == "mod" else self._cal_date
        # find Monday of the current week
        monday = d - timedelta(days=d.weekday())
        if monday < today:
            monday = today

        week_end = monday + timedelta(days=6)
        self._week_label.configure(
            text=f"{monday.strftime('%d/%m')} – {week_end.strftime('%d/%m/%Y')}"
        )

        for w in self._day_slot_area.winfo_children():
            w.destroy()

        GR_DAYS = ["Δευ", "Τρι", "Τετ", "Πεμ", "Παρ", "Σαβ", "Κυρ"]
        day_row = ctk.CTkFrame(self._day_slot_area, fg_color="transparent")
        day_row.pack(fill="x", pady=(4, 8))

        self._slots_container = ctk.CTkFrame(self._day_slot_area, fg_color="transparent")
        self._slots_container.pack(fill="both", expand=True)

        for d in range(7):
            day = monday + timedelta(days=d)
            label = f"{GR_DAYS[day.weekday()]}\n{day.strftime('%d/%m')}"
            btn = ctk.CTkButton(
                day_row, text=label, width=80, height=52,
                fg_color=("gray80", "gray30") if day >= today else ("gray60", "gray20"),
                hover_color=("gray70", "gray40"),
                state="normal" if day >= today else "disabled",
                command=lambda dt=day: self._pick_day(dt),
            )
            btn.pack(side="left", padx=4)

        # auto-load the first valid day
        self._pick_day(monday)

    def _pick_day(self, day: datetime):
        for w in self._slots_container.winfo_children():
            w.destroy()

        date_str = day.strftime("%Y-%m-%d")
        if self._cal_mode == "new":
            slots = AppointmentController.get_available_slots(
                date_str, self._sel_service.id, self._sel_employee["id"],
            )
        else:
            slots = AppointmentController.get_available_slots_for_reschedule(
                date_str,
                self._mod_appt.employee_id,
                self._mod_appt.duration_min,
                self._mod_appt.id,
            )

        if not slots:
            ctk.CTkLabel(
                self._slots_container,
                text=f"Δεν υπάρχουν διαθέσιμες ώρες για {day.strftime('%d/%m/%Y')}.",
                text_color="gray",
            ).pack(pady=32)
            return

        ctk.CTkLabel(
            self._slots_container,
            text=f"Διαθέσιμες ώρες — {day.strftime('%d/%m/%Y')}",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", padx=8, pady=(8, 4))

        wrap = ctk.CTkFrame(self._slots_container, fg_color="transparent")
        wrap.pack(fill="x", padx=8)

        for slot in slots:
            if self._cal_mode == "new":
                emp_note = "" if self._sel_employee["id"] is not None else f"  ({slot['employee_name']})"
            else:
                emp_note = ""
            ctk.CTkButton(
                wrap,
                text=f"{slot['time_str']}{emp_note}",
                width=130, height=36,
                fg_color=("#2980b9", "#1a6fa0"), hover_color=("#2471a3", "#155f8a"),
                command=lambda s=slot: self._pick_slot(s),
            ).pack(side="left", padx=4, pady=4)

    def _pick_slot(self, slot: dict):
        if self._cal_mode == "new":
            self._sel_slot = slot
            self._go_confirm()
        else:
            self._mod_sel_slot = slot
            self._go_mod_confirm()       

    # STEP 4 — confirm
    def _build_confirm_frame(self):
        self._confirm_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._confirm_frame.columnconfigure(0, weight=1)
        self._confirm_frame.rowconfigure(0, weight=1)

        card = ctk.CTkFrame(self._confirm_frame, corner_radius=16)
        card.grid(row=0, column=0)

        ctk.CTkLabel(
            card, text=" Επιβεβαίωση Ραντεβού",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(padx=52, pady=(36, 16))

        self._confirm_details = ctk.CTkLabel(
            card, text="", justify="left",
            font=ctk.CTkFont(size=13), text_color="gray",
        )
        self._confirm_details.pack(padx=52, pady=(0, 8))

        ctk.CTkLabel(card, text="Σημειώσεις (προαιρετικά):", anchor="w").pack(
            padx=52, anchor="w"
        )
        self._notes_entry = ctk.CTkEntry(card, width=340, placeholder_text="π.χ. αλλεργία σε χρώμα…")
        self._notes_entry.pack(padx=52, pady=(4, 16))

        self._confirm_msg = ctk.StringVar()
        self._confirm_msg_label = ctk.CTkLabel(
            card, textvariable=self._confirm_msg,
            font=ctk.CTkFont(size=12), wraplength=340,
        )
        self._confirm_msg_label.pack(padx=52, pady=(0, 8))

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(pady=(0, 36))
        ctk.CTkButton(
            btn_row, text="← Πίσω", width=110,
            fg_color="transparent", border_width=1,
            text_color=("gray20", "gray80"), hover_color=("gray85", "gray25"),
            command=self._go_cal,
        ).pack(side="left", padx=(0, 12))
        ctk.CTkButton(
            btn_row, text="✓ Κλείσιμο Ραντεβού", width=200,
            command=self._submit_appointment,
        ).pack(side="left")

    def _go_confirm(self):
        slot = self._sel_slot
        emp_name = slot["employee_name"] if self._sel_employee["id"] is not None else slot["employee_name"]
        self._confirm_details.configure(
            text=(
                f"Υπηρεσία:    {self._sel_service.name}\n"
                f"Υπάλληλος:  {emp_name}\n"
                f"Ημερομηνία: {slot['start_iso']}\n"
                f"Διάρκεια:    {self._sel_service.duration_min} λεπτά\n"
                f"Κόστος:       {self._sel_service.price:.2f} €"
            )
        )
        self._notes_entry.delete(0, "end")
        self._confirm_msg.set("")
        self._hide_all()
        self._confirm_frame.grid(row=0, column=0, sticky="nsew")

    def _submit_appointment(self):
        user  = Session.current_user()
        slot  = self._sel_slot
        notes = self._notes_entry.get().strip() or None
        try:
            AppointmentController.create_appointment(
                customer_id=user.id,
                employee_id=slot["employee_id"],
                service_id=self._sel_service.id,
                start_iso=slot["start_iso"],
                notes=notes,
            )
            self._list_msg_var.set("✔ Το ραντεβού κλείστηκε επιτυχώς!")
            self.after(5000, lambda: self._list_msg_var.set(""))
            self._go_list()
        except AppointmentError as e:
            if "δεν είναι πλέον διαθέσιμη" in str(e):
                self._go_unavailable(str(e))
            else:
                self._confirm_msg_label.configure(text_color=("#e74c3c", "#e74c3c"))
                self._confirm_msg.set(str(e))

    # ALT FLOW — slot taken
    def _build_unavailable_frame(self):
        self._unavailable_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._unavailable_frame.columnconfigure(0, weight=1)
        self._unavailable_frame.rowconfigure(0, weight=1)

        card = ctk.CTkFrame(self._unavailable_frame, corner_radius=16)
        card.grid(row=0, column=0)
        ctk.CTkLabel(
            card, text="⚠  Ώρα μη Διαθέσιμη",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(padx=52, pady=(36, 10))
        self._unavail_msg = ctk.CTkLabel(
            card, text="", text_color="gray", justify="center", wraplength=360,
        )
        self._unavail_msg.pack(padx=52, pady=(0, 28))
        ctk.CTkButton(
            card, text="← Επιλογή άλλης ώρας", width=210,
            command=lambda: self._unavail_back_fn(),
        ).pack(pady=(0, 36))
        self._unavail_back_fn = self._go_cal  # default; overridden by _go_unavailable

    def _go_unavailable(self, message: str, back_fn=None):
        self._unavail_back_fn = back_fn if back_fn is not None else self._go_cal
        self._unavail_msg.configure(text=message)
        self._hide_all()
        self._unavailable_frame.grid(row=0, column=0, sticky="nsew")

# UC 2.12 — MODIFICATION DETAIL
    def _build_mod_detail_frame(self):
        self._mod_detail_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._mod_detail_frame.columnconfigure(0, weight=1)
        self._mod_detail_frame.rowconfigure(0, weight=1)

        card = ctk.CTkFrame(self._mod_detail_frame, corner_radius=16)
        card.grid(row=0, column=0)

        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=40, pady=(28, 8))
        hdr.columnconfigure(1, weight=1)
        ctk.CTkButton(
            hdr, text="← Πίσω", width=90,
            fg_color="transparent", border_width=1,
            text_color=("gray20", "gray80"), hover_color=("gray85", "gray25"),
            command=self._go_list,
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            hdr, text="Στοιχεία Ραντεβού",
            font=ctk.CTkFont(size=17, weight="bold"),
        ).grid(row=0, column=1, sticky="w", padx=16)

        self._mod_detail_text = ctk.CTkLabel(
            card, text="", justify="left",
            font=ctk.CTkFont(size=13), text_color="gray",
        )
        self._mod_detail_text.pack(padx=40, pady=(4, 8), anchor="w")

        self._mod_detail_status_lbl = ctk.CTkLabel(
            card, text="", font=ctk.CTkFont(size=13, weight="bold"),
        )
        self._mod_detail_status_lbl.pack(padx=40, pady=(0, 16))

        self._mod_detail_btns = ctk.CTkFrame(card, fg_color="transparent")
        self._mod_detail_btns.pack(pady=(0, 36))

    def _go_mod_detail(self, appt=None):
        if appt is not None:
            self._mod_appt = appt

        a = self._mod_appt
        status_text, status_color = _APPT_STATUS_MAP.get(a.status, (a.status, ("gray", "gray")))

        self._mod_detail_text.configure(text=(
            f"Υπηρεσία:    {a.service_name}\n"
            f"Υπάλληλος:  {a.employee_name}\n"
            f"Ημερομηνία: {a.scheduled_at}\n"
            f"Διάρκεια:    {a.duration_min} λεπτά\n"
            f"Κόστος:       {a.price:.2f} €"
            + (f"\nΣημείωση:    {a.notes}" if a.notes else "")
        ))
        self._mod_detail_status_lbl.configure(text=status_text, text_color=status_color)

        for w in self._mod_detail_btns.winfo_children():
            w.destroy()

        if a.status in ("pending", "confirmed"):
            ctk.CTkButton(
                self._mod_detail_btns, text=" Αναπρογραμματισμός", width=210,
                fg_color=("#2980b9", "#1a6fa0"), hover_color=("#2471a3", "#155f8a"),
                command=self._go_mod_cal,
            ).pack(side="left", padx=(0, 12))
            ctk.CTkButton(
                self._mod_detail_btns, text="✘ Ακύρωση", width=130,
                fg_color=("#e74c3c", "#922b21"), hover_color=("#c0392b", "#7b241c"),
                command=self._go_cancel_confirm,
            ).pack(side="left")
        else:
            ctk.CTkLabel(
                self._mod_detail_btns,
                text="Δεν είναι δυνατή η τροποποίηση αυτού του ραντεβού.",
                text_color="gray",
            ).pack()

        self._hide_all()
        self._mod_detail_frame.grid(row=0, column=0, sticky="nsew")

    # UC 2.12 — RESCHEDULE CONFIRM
    def _build_mod_confirm_frame(self):
        self._mod_confirm_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._mod_confirm_frame.columnconfigure(0, weight=1)
        self._mod_confirm_frame.rowconfigure(0, weight=1)

        card = ctk.CTkFrame(self._mod_confirm_frame, corner_radius=16)
        card.grid(row=0, column=0)

        ctk.CTkLabel(
            card, text=" Επιβεβαίωση Αλλαγής Ραντεβού",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(padx=52, pady=(36, 16))

        self._mod_confirm_details = ctk.CTkLabel(
            card, text="", justify="left",
            font=ctk.CTkFont(size=13), text_color="gray",
        )
        self._mod_confirm_details.pack(padx=52, pady=(0, 16))

        self._mod_confirm_msg = ctk.StringVar()
        self._mod_confirm_msg_label = ctk.CTkLabel(
            card, textvariable=self._mod_confirm_msg,
            font=ctk.CTkFont(size=12), wraplength=360,
        )
        self._mod_confirm_msg_label.pack(padx=52, pady=(0, 8))

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(pady=(0, 36))
        ctk.CTkButton(
            btn_row, text="← Πίσω", width=110,
            fg_color="transparent", border_width=1,
            text_color=("gray20", "gray80"), hover_color=("gray85", "gray25"),
            command=self._go_mod_cal,
        ).pack(side="left", padx=(0, 12))
        ctk.CTkButton(
            btn_row, text="✓ Επιβεβαίωση Αλλαγής", width=210,
            command=self._submit_reschedule,
        ).pack(side="left")

    def _go_mod_confirm(self):
        a    = self._mod_appt
        slot = self._mod_sel_slot
        self._mod_confirm_details.configure(text=(
            f"Υπηρεσία:    {a.service_name}\n"
            f"Υπάλληλος:  {a.employee_name}\n"
            f"Παλαιά ώρα: {a.scheduled_at}\n"
            f"Νέα ώρα:     {slot['start_iso']}\n"
            f"Διάρκεια:    {a.duration_min} λεπτά"
        ))
        self._mod_confirm_msg.set("")
        self._hide_all()
        self._mod_confirm_frame.grid(row=0, column=0, sticky="nsew")

    def _submit_reschedule(self):
        user = Session.current_user()
        try:
            AppointmentController.customer_reschedule_appointment(
                appt_id=self._mod_appt.id,
                customer_id=user.id,
                new_scheduled_at=self._mod_sel_slot["start_iso"],
            )
            self._list_msg_var.set("✔ Το ραντεβού αναπρογραμματίστηκε επιτυχώς!")
            self.after(5000, lambda: self._list_msg_var.set(""))
            self._go_list()
        except AppointmentError as e:
            if "δεν είναι πλέον διαθέσιμη" in str(e):
                self._go_unavailable(str(e), back_fn=self._go_mod_cal)
            else:
                self._mod_confirm_msg_label.configure(text_color=("#e74c3c", "#e74c3c"))
                self._mod_confirm_msg.set(str(e))

    # UC 2.12 — CANCEL CONFIRM
    def _build_cancel_confirm_frame(self):
        self._cancel_confirm_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._cancel_confirm_frame.columnconfigure(0, weight=1)
        self._cancel_confirm_frame.rowconfigure(0, weight=1)

        card = ctk.CTkFrame(self._cancel_confirm_frame, corner_radius=16)
        card.grid(row=0, column=0)

        ctk.CTkLabel(
            card, text="✘  Ακύρωση Ραντεβού",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(padx=52, pady=(36, 10))

        self._cancel_confirm_text = ctk.CTkLabel(
            card, text="", text_color="gray", justify="center",
        )
        self._cancel_confirm_text.pack(padx=52, pady=(0, 20))

        self._cancel_msg = ctk.StringVar()
        self._cancel_msg_label = ctk.CTkLabel(
            card, textvariable=self._cancel_msg,
            font=ctk.CTkFont(size=12),
        )
        self._cancel_msg_label.pack(padx=52, pady=(0, 8))

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(pady=(0, 36))
        ctk.CTkButton(
            btn_row, text="Όχι, επιστροφή", width=150,
            fg_color="transparent", border_width=1,
            text_color=("gray20", "gray80"), hover_color=("gray85", "gray25"),
            command=self._go_mod_detail,
        ).pack(side="left", padx=(0, 12))
        ctk.CTkButton(
            btn_row, text="Ναι, ακύρωση", width=150,
            fg_color=("#e74c3c", "#922b21"), hover_color=("#c0392b", "#7b241c"),
            command=self._execute_cancel,
        ).pack(side="left")

    def _go_cancel_confirm(self):
        a = self._mod_appt
        self._cancel_confirm_text.configure(
            text=f"Θέλετε σίγουρα να ακυρώσετε το ραντεβού\n"
                 f"για «{a.service_name}» την {a.scheduled_at};"
        )
        self._cancel_msg.set("")
        self._hide_all()
        self._cancel_confirm_frame.grid(row=0, column=0, sticky="nsew")

    def _execute_cancel(self):
        user = Session.current_user()
        try:
            AppointmentController.customer_cancel_appointment(
                appt_id=self._mod_appt.id,
                customer_id=user.id,
            )
            self._list_msg_var.set("✔ Το ραντεβού ακυρώθηκε.")
            self.after(5000, lambda: self._list_msg_var.set(""))
            self._go_list()
        except AppointmentError as e:
            self._cancel_msg_label.configure(text_color=("#e74c3c", "#e74c3c"))
            self._cancel_msg.set(str(e))