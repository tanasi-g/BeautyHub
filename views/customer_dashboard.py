import customtkinter as ctk
from services.errors import OrderError
from services.errors import RefundError
from views.base_dashboard import BaseDashboard
from views.notifications_page import NotificationsPage
from controllers.service_controller import ServiceController
from controllers.salon_controller import SalonController
from utils.session import Session
from controllers.review_controller import ReviewController, ReviewError
from controllers.appointment_controller import AppointmentController, AppointmentError
from datetime import datetime, timedelta
from controllers.eshop_controller import EShopController
from controllers.order_controller import OrderController

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
        appts_page = _AppointmentsPage(self._content)

        def _start_booking():
            nav("appointments")
            appts_page._go_svc()

        self._register_page("home",          _HomePage(self._content))
        self._register_page("salons",        _SalonSearchPage(self._content, _start_booking))
        self._register_page("eshop",         _EShopStorePage(self._content, nav))
        self._register_page("cart",          _CartPage(self._content, nav))
        self._register_page("orders",        _OrderHistoryPage(self._content))
        self._register_page("appointments",  appts_page)
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

    def __init__(self, master, start_booking=None):
            super().__init__(master, fg_color="transparent")
            self._start_booking = start_booking
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



         # filter bar (step 1)
        bar = ctk.CTkFrame(self._search_frame, corner_radius=10)
        bar.grid(row=1, column=0, sticky="ew", padx=32, pady=(0, 12))
        bar.columnconfigure(1, weight=2)
        bar.columnconfigure(3, weight=1)

        ctk.CTkLabel(bar, text="Όνομα:", anchor="w").grid(
            row=0, column=0, padx=(16, 8), pady=14,
        )
        self._name_entry = ctk.CTkEntry(
            bar, placeholder_text="Όνομα κομμωτηρίου…", height=36,
        )
        self._name_entry.grid(row=0, column=1, sticky="ew", padx=(0, 12), pady=14)
        self._name_entry.bind("<Return>", lambda _: self._do_search())

        ctk.CTkLabel(bar, text="Περιοχή:", anchor="w").grid(
            row=0, column=2, padx=(0, 8), pady=14,
        )
        self._city_entry = ctk.CTkEntry(
            bar, placeholder_text="Πόλη / περιοχή…", height=36, width=160,
        )
        self._city_entry.grid(row=0, column=3, sticky="ew", padx=(0, 12), pady=14)
        self._city_entry.bind("<Return>", lambda _: self._do_search())

        ctk.CTkLabel(bar, text="Υπηρεσία:", anchor="w").grid(
            row=0, column=4, padx=(0, 8), pady=14,
        )
        self._svc_combo = ctk.CTkComboBox(
            bar, values=[self._ALL_SVC], width=190, state="readonly",
        )
        self._svc_combo.grid(row=0, column=5, padx=(0, 12), pady=14)
        self._svc_combo.set(self._ALL_SVC)

        ctk.CTkButton(
            bar, text="🔍 Αναζήτηση", width=130,
            command=self._do_search,
        ).grid(row=0, column=6, padx=(0, 8), pady=14)
        ctk.CTkButton(
            bar, text="✕ Καθαρισμός", width=130,
            fg_color="transparent", border_width=1,
            text_color=("gray20", "gray80"), hover_color=("gray85", "gray25"),
            command=self._clear_filters,
        ).grid(row=0, column=7, padx=(0, 16), pady=14)


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
        #Βήμα 2 — εκτέλεση αναζήτησης με τα τρέχοντα κριτήρια.
            name_kw    = self._name_entry.get()
            city_kw    = self._city_entry.get()
            svc_name   = self._svc_combo.get()
            service_id = self._services_map.get(svc_name) if svc_name != self._ALL_SVC else None
            results    = SalonController.search(name_kw, city_kw, service_id)
            self._render_results(results)

    def _clear_filters(self):
        """Εναλλακτική ροή 1 — καθαρισμός φίλτρων, επιστροφή στο βήμα 2."""
        self._name_entry.delete(0, "end")
        self._city_entry.delete(0, "end")
        self._svc_combo.set(self._ALL_SVC)
        self._do_search()

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
        svc_wrap.grid(row=2, column=0, sticky="nsew", padx=32, pady=(0, 16))
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

        # κουμπί κράτησης (κάτω από τις υπηρεσίες)
        book_bar = ctk.CTkFrame(self._profile_frame, fg_color="transparent")
        book_bar.grid(row=3, column=0, sticky="ew", padx=32, pady=(0, 24))
        book_bar.columnconfigure(0, weight=1)
        ctk.CTkButton(
            book_bar,
            text="📅  Κράτηση / Νέο Ραντεβού",
            width=240, height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._book_appointment,
        ).grid(row=0, column=0, sticky="e")




    def _open_profile(self, salon):
        #"""Βήμα 5 — ανάκτηση και εμφάνιση προφίλ κομμωτηρίου."""
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

    def _book_appointment(self):
        if self._start_booking:
         self._start_booking()


#  E-Shop Store — UC 2.11  


class _EShopStorePage(ctk.CTkFrame):
    _LIST_COLS = ["Όνομα", "Περιγραφή", "Τιμή", "Απόθεμα", ""]

    def __init__(self, master, navigate):
        super().__init__(master, fg_color="transparent")
        self._navigate  = navigate
        self._sel_product = None
        self._qty        = 1
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self._build_list_frame()
        self._build_detail_frame()
        self._go_list()

    # state router
    def _hide_all(self):
        self._list_frame.grid_remove()
        self._detail_frame.grid_remove()

    def refresh(self):
        self._go_list()

    # LIST 
    def _build_list_frame(self):
        self._list_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._list_frame.columnconfigure(0, weight=1)
        self._list_frame.rowconfigure(3, weight=1)

        # header
        hdr = ctk.CTkFrame(self._list_frame, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=32, pady=(24, 4))
        hdr.columnconfigure(0, weight=1)
        ctk.CTkLabel(
            hdr, text="🛍 E-Shop — Προϊόντα",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(
            hdr, text=" Δες Καλάθι", width=140,
            command=lambda: self._navigate("cart"),
        ).grid(row=0, column=1, sticky="e")

        # search bar 
        bar = ctk.CTkFrame(self._list_frame, corner_radius=10)
        bar.grid(row=1, column=0, sticky="ew", padx=32, pady=(0, 6))
        bar.columnconfigure(1, weight=1)
        ctk.CTkLabel(bar, text="Αναζήτηση:", anchor="w").grid(
            row=0, column=0, padx=(16, 8), pady=12,
        )
        self._search_entry = ctk.CTkEntry(
            bar, placeholder_text="Όνομα ή περιγραφή…", height=34,
        )
        self._search_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=12)
        self._search_entry.bind("<Return>", lambda _: self._do_search())
        ctk.CTkButton(
            bar, text=" Αναζήτηση", width=130, command=self._do_search,
        ).grid(row=0, column=2, padx=(0, 6), pady=12)
        ctk.CTkButton(
            bar, text="✕ Καθαρισμός", width=130,
            fg_color="transparent", border_width=1,
            text_color=("gray20", "gray80"), hover_color=("gray85", "gray25"),
            command=self._clear_search,
        ).grid(row=0, column=3, padx=(0, 16), pady=12)

        # feedback line 
        self._list_toast_var = ctk.StringVar()
        ctk.CTkLabel(
            self._list_frame, textvariable=self._list_toast_var,
            text_color=("#27ae60", "#2ecc71"),
            font=ctk.CTkFont(size=12), anchor="w",
        ).grid(row=2, column=0, sticky="w", padx=32)

        # results table
        self._table = ctk.CTkScrollableFrame(self._list_frame, corner_radius=10)
        self._table.grid(row=3, column=0, sticky="nsew", padx=32, pady=(2, 24))
        for i in range(len(self._LIST_COLS)):
            self._table.columnconfigure(i, weight=1)

    def _go_list(self):
        self._hide_all()
        self._list_frame.grid(row=0, column=0, sticky="nsew")
        self._do_search()

    def _do_search(self):
        keyword  = self._search_entry.get()
        products = EShopController.search(keyword)  
        self._render_products(products)

    def _clear_search(self):
        self._search_entry.delete(0, "end")
        self._do_search()

    def _render_products(self, products: list):
        for w in self._table.winfo_children():
            w.destroy()

        #δεν βρέθηκαν προϊόντα
        if not products:
            no_kw = not self._search_entry.get().strip()
            msg = (
                "Δεν υπάρχουν διαθέσιμα προϊόντα αυτή τη στιγμή."
                if no_kw else
                "Δεν βρέθηκαν προϊόντα για την αναζήτησή σας."
            )
            ctk.CTkLabel(
                self._table, text=msg, text_color="gray",
            ).grid(row=0, column=0, columnspan=len(self._LIST_COLS), pady=36)
            return

        for col, h in enumerate(self._LIST_COLS):
            ctk.CTkLabel(
                self._table, text=h,
                font=ctk.CTkFont(weight="bold"), anchor="w",
            ).grid(row=0, column=col, sticky="ew", padx=8, pady=6)
        ctk.CTkFrame(self._table, height=1, fg_color="gray40").grid(
            row=1, column=0, columnspan=len(self._LIST_COLS), sticky="ew", padx=4,
        )

        for r_idx, p in enumerate(products, start=2):
            bg = ("gray92", "gray18") if r_idx % 2 == 0 else ("gray96", "gray15")
            for col, val in enumerate([
                p.name,
                (p.description or "—")[:40],
                f"{p.price:.2f} €",
                str(p.stock),
            ]):
                ctk.CTkLabel(
                    self._table, text=val, anchor="w",
                    fg_color=bg, corner_radius=4,
                ).grid(row=r_idx, column=col, sticky="ew", padx=4, pady=2)

            #επιλογή προϊόντος
            ctk.CTkButton(
                self._table, text="Λεπτομέρειες →", width=130, height=26,
                fg_color=("gray70", "gray30"), hover_color=("gray60", "gray40"),
                font=ctk.CTkFont(size=11),
                command=lambda prod=p: self._open_detail(prod),
            ).grid(row=r_idx, column=4, padx=4, pady=2)

    # DETAIL 
    def _build_detail_frame(self):
        self._detail_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._detail_frame.columnconfigure(0, weight=1)
        self._detail_frame.rowconfigure(0, weight=1)

        card = ctk.CTkFrame(self._detail_frame, corner_radius=16)
        card.grid(row=0, column=0)

        # header inside card
        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=40, pady=(28, 4))
        hdr.columnconfigure(1, weight=1)
        ctk.CTkButton(
            hdr, text="← Πίσω", width=90,
            fg_color="transparent", border_width=1,
            text_color=("gray20", "gray80"), hover_color=("gray85", "gray25"),
            command=self._go_list,
        ).grid(row=0, column=0, sticky="w")
        self._detail_title = ctk.CTkLabel(
            hdr, text="", font=ctk.CTkFont(size=17, weight="bold"),
        )
        self._detail_title.grid(row=0, column=1, sticky="w", padx=16)
        ctk.CTkButton(
            hdr, text=" Δες Καλάθι", width=130,
            command=lambda: self._navigate("cart"),
        ).grid(row=0, column=2, sticky="e")

        # product info
        self._detail_desc = ctk.CTkLabel(
            card, text="", justify="left",
            text_color="gray", wraplength=420, anchor="w",
        )
        self._detail_desc.pack(fill="x", padx=40, pady=(4, 0))

        info_row = ctk.CTkFrame(card, fg_color="transparent")
        info_row.pack(fill="x", padx=40, pady=(10, 0))
        self._detail_price = ctk.CTkLabel(
            info_row, text="",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        self._detail_price.pack(side="left")
        self._detail_stock = ctk.CTkLabel(
            info_row, text="",
            text_color="gray", font=ctk.CTkFont(size=12),
        )
        self._detail_stock.pack(side="left", padx=(16, 0))

        # quantity selector 
        qty_section = ctk.CTkFrame(card, fg_color="transparent")
        qty_section.pack(pady=(18, 0))
        ctk.CTkLabel(qty_section, text="Ποσότητα:", font=ctk.CTkFont(size=13)).pack(side="left", padx=(0, 12))
        ctk.CTkButton(
            qty_section, text="−", width=34, height=34,
            fg_color=("gray72", "gray32"), hover_color=("gray60", "gray40"),
            command=self._dec_qty,
        ).pack(side="left")
        self._qty_label = ctk.CTkLabel(
            qty_section, text="1", width=44,
            font=ctk.CTkFont(size=15, weight="bold"), anchor="center",
        )
        self._qty_label.pack(side="left")
        ctk.CTkButton(
            qty_section, text="+", width=34, height=34,
            fg_color=("gray72", "gray32"), hover_color=("gray60", "gray40"),
            command=self._inc_qty,
        ).pack(side="left")

        self._detail_msg = ctk.StringVar()
        self._detail_msg_label = ctk.CTkLabel(
            card, textvariable=self._detail_msg,
            font=ctk.CTkFont(size=12),
        )
        self._detail_msg_label.pack(pady=(10, 0))

        ctk.CTkButton(
            card, text="+ Προσθήκη στο Καλάθι", width=240, height=40,
            font=ctk.CTkFont(size=14),
            command=self._add_to_cart,
        ).pack(pady=(12, 32))

    def _open_detail(self, product):
        """εμφάνιση στοιχείων προϊόντος."""
        self._sel_product = product
        self._qty         = 1
        self._detail_title.configure(text=product.name)
        self._detail_desc.configure(text=product.description or "Δεν υπάρχει περιγραφή.")
        self._detail_price.configure(text=f"{product.price:.2f} €")
        self._detail_stock.configure(text=f"Διαθέσιμα: {product.stock} τεμ.")
        self._qty_label.configure(text="1")
        self._detail_msg.set("")
        self._hide_all()
        self._detail_frame.grid(row=0, column=0, sticky="nsew")

    def _dec_qty(self):
        if self._qty > 1:
            self._qty -= 1
            self._qty_label.configure(text=str(self._qty))

    def _inc_qty(self):
        if self._qty < self._sel_product.stock:
            self._qty += 1
            self._qty_label.configure(text=str(self._qty))

    def _add_to_cart(self):
        """προσθήκη ποσότητας στο καλάθι."""
        p = self._sel_product
        OrderController.add_to_cart(p.id, p.name, p.price, self._qty)

        # ενημέρωση υπάρχοντος καλαθιού 
        self._list_toast_var.set(
            f"✔  {self._qty} × «{p.name}» προστέθηκε στο καλάθι."
        )
        self.after(3000, lambda: self._list_toast_var.set(""))
        self._go_list()


#  Cart page 

class _CartPage(ctk.CTkFrame):
    def __init__(self, master, navigate):
        super().__init__(master, fg_color="transparent")
        self._navigate = navigate
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self._pay_card_holder = ""
        self._pay_card_number = ""
        self._pay_card_expiry = ""
        self._pay_txn_id      = ""
        self._last_order_id   = None
        self._build_cart_view()
        self._build_summary_view()
        self._build_cancel_confirm_view()
        self._build_insufficient_view()
        self._build_pay_form_frame()
        self._build_pay_review_frame()
        self._build_pay_result_frame()



    
    def _hide_all(self):
        for f in (
            self._cart_frame, self._summary_frame,
            self._cancel_frame, self._insufficient_frame,
            self._pay_form_frame, self._pay_review_frame, self._pay_result_frame,
        ):
            f.grid_remove()

    def refresh(self):
        self._go_cart()

    #  CART VIEW 
    def _build_cart_view(self):
        self._cart_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._cart_frame.columnconfigure(0, weight=1)
        self._cart_frame.rowconfigure(1, weight=1)

        hdr = ctk.CTkFrame(self._cart_frame, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=32, pady=(24, 12))
        hdr.columnconfigure(0, weight=1)
        ctk.CTkLabel(
            hdr, text=" Καλάθι Αγορών",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        self._cart_table = ctk.CTkScrollableFrame(self._cart_frame, corner_radius=10)
        self._cart_table.grid(row=1, column=0, sticky="nsew", padx=32, pady=(0, 8))
        self._cart_table.columnconfigure((0, 1, 2, 3), weight=1)

        self._cart_total_var = ctk.StringVar()
        ctk.CTkLabel(
            self._cart_frame, textvariable=self._cart_total_var,
            font=ctk.CTkFont(size=15, weight="bold"), anchor="e",
        ).grid(row=2, column=0, sticky="e", padx=40, pady=(0, 8))

        btn_row = ctk.CTkFrame(self._cart_frame, fg_color="transparent")
        btn_row.grid(row=3, column=0, sticky="ew", padx=32, pady=(0, 24))
        btn_row.columnconfigure(0, weight=1)
        ctk.CTkButton(
            btn_row, text="🗑 Άδειασμα", width=140,
            fg_color="transparent", border_width=1,
            text_color=("#e74c3c", "#e74c3c"),
            hover_color=("gray85", "gray25"),
            command=self._clear_cart,
        ).grid(row=0, column=0, sticky="w")
        self._proceed_btn = ctk.CTkButton(
            btn_row, text="Προχώρηση →", width=160,
            command=self._go_summary,
        )
        self._proceed_btn.grid(row=0, column=1, sticky="e")

    def _go_cart(self):
        self._hide_all()
        self._cart_frame.grid(row=0, column=0, sticky="nsew")
        self._refresh_cart()

    def _refresh_cart(self):
        for w in self._cart_table.winfo_children():
            w.destroy()

        lines = OrderController.get_cart_lines()

        if not lines:
            ctk.CTkLabel(
                self._cart_table,
                text="Το καλάθι είναι άδειο.\nΜεταβείτε στο E-Shop για να επιλέξετε προϊόντα.",
                text_color="gray", justify="center",
            ).grid(row=0, column=0, columnspan=4, pady=36)
            self._cart_total_var.set("")
            self._proceed_btn.configure(state="disabled")
            return
        self._proceed_btn.configure(state="normal")
        for col, h in enumerate(["Προϊόν", "Τιμή/τεμ.", "Ποσότητα", "Υποσύνολο"]):
            ctk.CTkLabel(
                self._cart_table, text=h,
                font=ctk.CTkFont(weight="bold"), anchor="w",
            ).grid(row=0, column=col, sticky="ew", padx=8, pady=6)
        ctk.CTkFrame(self._cart_table, height=1, fg_color="gray40").grid(
            row=1, column=0, columnspan=4, sticky="ew", padx=4
        )

        for r_idx, line in enumerate(lines, start=2):
            bg = ("gray92", "gray18") if r_idx % 2 == 0 else ("gray96", "gray15")
            ctk.CTkLabel(
                self._cart_table, text=line.name, anchor="w",
                fg_color=bg, corner_radius=4,
            ).grid(row=r_idx, column=0, sticky="ew", padx=4, pady=2)
            ctk.CTkLabel(
                self._cart_table, text=f"{line.price:.2f} €", anchor="w",
                fg_color=bg, corner_radius=4,
            ).grid(row=r_idx, column=1, sticky="ew", padx=4, pady=2)

            qty_frame = ctk.CTkFrame(self._cart_table, fg_color=bg, corner_radius=4)
            qty_frame.grid(row=r_idx, column=2, sticky="ew", padx=4, pady=2)
            ctk.CTkButton(
                qty_frame, text="−", width=28, height=26,
                fg_color=("gray72", "gray32"), hover_color=("gray60", "gray40"),
                command=lambda pid=line.product_id, q=line.quantity: self._change_qty(pid, q - 1),
            ).pack(side="left", padx=(4, 2), pady=2)
            ctk.CTkLabel(
                qty_frame, text=str(line.quantity), width=32, anchor="center"
            ).pack(side="left")
            ctk.CTkButton(
                qty_frame, text="+", width=28, height=26,
                fg_color=("gray72", "gray32"), hover_color=("gray60", "gray40"),
                command=lambda pid=line.product_id, q=line.quantity: self._change_qty(pid, q + 1),
            ).pack(side="left", padx=(2, 4), pady=2)

            ctk.CTkLabel(
                self._cart_table, text=f"{line.subtotal:.2f} €", anchor="w",
                fg_color=bg, corner_radius=4,
            ).grid(row=r_idx, column=3, sticky="ew", padx=4, pady=2)

        self._cart_total_var.set(f"Σύνολο: {OrderController.cart_total():.2f} €")

    def _change_qty(self, product_id: int, new_qty: int):
        OrderController.set_quantity(product_id, new_qty)
        self._refresh_cart()

    def _clear_cart(self):
        OrderController.clear_cart()
        self._refresh_cart()

    def _build_summary_view(self):
        self._summary_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._summary_frame.columnconfigure(0, weight=1)
        self._summary_frame.rowconfigure(1, weight=1)

        hdr = ctk.CTkFrame(self._summary_frame, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=32, pady=(24, 12))
        hdr.columnconfigure(0, weight=1)
        ctk.CTkLabel(
            hdr, text="📋 Σύνοψη Παραγγελίας",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        self._summary_table = ctk.CTkScrollableFrame(self._summary_frame, corner_radius=10)
        self._summary_table.grid(row=1, column=0, sticky="nsew", padx=32, pady=(0, 8))
        self._summary_table.columnconfigure((0, 1, 2, 3), weight=1)

        self._summary_total_var = ctk.StringVar()
        ctk.CTkLabel(
            self._summary_frame, textvariable=self._summary_total_var,
            font=ctk.CTkFont(size=16, weight="bold"), anchor="e",
        ).grid(row=2, column=0, sticky="e", padx=40, pady=(0, 8))

        btn_row = ctk.CTkFrame(self._summary_frame, fg_color="transparent")
        btn_row.grid(row=3, column=0, sticky="ew", padx=32, pady=(0, 24))
        btn_row.columnconfigure(0, weight=1)
        ctk.CTkButton(
            btn_row, text="← Ακύρωση", width=130,
            fg_color="transparent", border_width=1,
            text_color=("gray20", "gray80"),
            hover_color=("gray85", "gray25"),
            command=self._go_cancel_confirm,
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(
            btn_row, text="💳 Πληρωμή →", width=160,
            command=self._confirm_order,
        ).grid(row=0, column=1, sticky="e")

    def _go_summary(self):
        self._hide_all()
        self._summary_frame.grid(row=0, column=0, sticky="nsew")
        self._refresh_summary()

    def _refresh_summary(self):
        for w in self._summary_table.winfo_children():
            w.destroy()

        for col, h in enumerate(["Προϊόν", "Τιμή/τεμ.", "Ποσότητα", "Υποσύνολο"]):
            ctk.CTkLabel(
                self._summary_table, text=h,
                font=ctk.CTkFont(weight="bold"), anchor="w",
            ).grid(row=0, column=col, sticky="ew", padx=8, pady=6)
        ctk.CTkFrame(self._summary_table, height=1, fg_color="gray40").grid(
            row=1, column=0, columnspan=4, sticky="ew", padx=4
        )

        for r_idx, line in enumerate(OrderController.get_cart_lines(), start=2):
            bg = ("gray92", "gray18") if r_idx % 2 == 0 else ("gray96", "gray15")
            for col, val in enumerate([
                line.name, f"{line.price:.2f} €", str(line.quantity), f"{line.subtotal:.2f} €"
            ]):
                ctk.CTkLabel(
                    self._summary_table, text=val, anchor="w",
                    fg_color=bg, corner_radius=4,
                ).grid(row=r_idx, column=col, sticky="ew", padx=4, pady=2)

        self._summary_total_var.set(f"Σύνολο: {OrderController.cart_total():.2f} €")

    def _confirm_order(self):
        problems = OrderController.check_stock()
        if problems:
            self._go_insufficient(problems)
        else:
            self._go_pay_form()

    # ================================================================ CANCEL CONFIRM VIEW (alt flow 1)
    def _build_cancel_confirm_view(self):
        self._cancel_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._cancel_frame.columnconfigure(0, weight=1)
        self._cancel_frame.rowconfigure(0, weight=1)

        card = ctk.CTkFrame(self._cancel_frame, corner_radius=16)
        card.grid(row=0, column=0)
        ctk.CTkLabel(
            card, text="❌  Ακύρωση Παραγγελίας",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(padx=52, pady=(36, 10))
        ctk.CTkLabel(
            card,
            text="Είστε σίγουροι ότι θέλετε να ακυρώσετε;\nΤο καλάθι θα παραμείνει αναλλοίωτο.",
            text_color="gray", justify="center",
        ).pack(padx=52, pady=(0, 28))

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(pady=(0, 36))
        ctk.CTkButton(
            btn_row, text="Όχι, επιστροφή", width=160,
            fg_color="transparent", border_width=1,
            text_color=("gray20", "gray80"),
            hover_color=("gray85", "gray25"),
            command=self._go_summary,
        ).pack(side="left", padx=(0, 12))
        ctk.CTkButton(
            btn_row, text="Ναι, ακύρωση", width=160,
            fg_color=("#e74c3c", "#922b21"), hover_color=("#c0392b", "#7b241c"),
            command=self._go_cart,
        ).pack(side="left")

    def _go_cancel_confirm(self):
        self._hide_all()
        self._cancel_frame.grid(row=0, column=0, sticky="nsew")

    # ================================================================ INSUFFICIENT STOCK VIEW (alt flow 2)
    def _build_insufficient_view(self):
        self._insufficient_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._insufficient_frame.columnconfigure(0, weight=1)
        self._insufficient_frame.rowconfigure(0, weight=1)

        card = ctk.CTkFrame(self._insufficient_frame, corner_radius=16)
        card.grid(row=0, column=0)
        ctk.CTkLabel(
            card, text="⚠  Μη Επαρκές Απόθεμα",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(padx=52, pady=(36, 8))
        ctk.CTkLabel(
            card,
            text="Τα παρακάτω προϊόντα δεν έχουν επαρκές απόθεμα:",
            text_color="gray",
        ).pack(padx=52, pady=(0, 12))

        self._insuf_items_frame = ctk.CTkFrame(
            card, fg_color=("gray88", "gray22"), corner_radius=8
        )
        self._insuf_items_frame.pack(padx=52, pady=(0, 24), fill="x")

        ctk.CTkButton(
            card, text="← Επιστροφή στο Καλάθι", width=220,
            command=self._go_cart,
        ).pack(pady=(0, 36))

    def _go_insufficient(self, problems: list[str]):
        for w in self._insuf_items_frame.winfo_children():
            w.destroy()
        for problem in problems:
            ctk.CTkLabel(
                self._insuf_items_frame, text=f"• {problem}",
                text_color=("#e74c3c", "#e74c3c"), anchor="w",
            ).pack(fill="x", padx=16, pady=4)
        self._hide_all()
        self._insufficient_frame.grid(row=0, column=0, sticky="nsew")

    # ================================================================ UC 2.5 — PAY FORM (steps 2–4 + alt flow 1)
    def _build_pay_form_frame(self):
        self._pay_form_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._pay_form_frame.columnconfigure(0, weight=1)
        self._pay_form_frame.rowconfigure(0, weight=1)

        card = ctk.CTkFrame(self._pay_form_frame, corner_radius=16)
        card.grid(row=0, column=0)

        # secure header (step 2 — ασφαλές περιβάλλον)
        ctk.CTkLabel(
            card, text="🔒  Ασφαλής Πληρωμή — Στοιχεία Κάρτας",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(padx=52, pady=(32, 4))

        self._pay_form_total_var = ctk.StringVar()
        ctk.CTkLabel(
            card, textvariable=self._pay_form_total_var,
            font=ctk.CTkFont(size=28, weight="bold"),
        ).pack(padx=52, pady=(0, 18))

        # helper: labelled field
        def _field(parent, label, placeholder, show=""):
            ctk.CTkLabel(parent, text=label, anchor="w").pack(
                fill="x", padx=52, pady=(6, 0)
            )
            e = ctk.CTkEntry(
                parent, width=340,
                placeholder_text=placeholder,
                show=show,
            )
            e.pack(padx=52)
            return e

        self._entry_holder = _field(card, "Κάτοχος κάρτας *",   "Ονοματεπώνυμο")
        self._entry_number = _field(card, "Αριθμός κάρτας *",   "1234 5678 9012 3456")

        # expiry + CVV side-by-side
        row2 = ctk.CTkFrame(card, fg_color="transparent")
        row2.pack(padx=52, fill="x", pady=(6, 0))

        exp_col = ctk.CTkFrame(row2, fg_color="transparent")
        exp_col.pack(side="left", expand=True, fill="x", padx=(0, 8))
        ctk.CTkLabel(exp_col, text="Ημ. λήξης *", anchor="w").pack(anchor="w")
        self._entry_expiry = ctk.CTkEntry(exp_col, placeholder_text="ΜΜ/ΕΕ")
        self._entry_expiry.pack(fill="x")

        cvv_col = ctk.CTkFrame(row2, fg_color="transparent")
        cvv_col.pack(side="left", expand=True, fill="x")
        ctk.CTkLabel(cvv_col, text="CVV *", anchor="w").pack(anchor="w")
        self._entry_cvv = ctk.CTkEntry(cvv_col, placeholder_text="123", show="*")
        self._entry_cvv.pack(fill="x")

        # error label (alt flow 1)
        self._pay_form_error = ctk.StringVar()
        ctk.CTkLabel(
            card, textvariable=self._pay_form_error,
            text_color=("#e74c3c", "#e74c3c"),
            font=ctk.CTkFont(size=12), wraplength=340,
        ).pack(padx=52, pady=(10, 0))

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(pady=(10, 32))
        ctk.CTkButton(
            btn_row, text="← Πίσω", width=110,
            fg_color="transparent", border_width=1,
            text_color=("gray20", "gray80"), hover_color=("gray85", "gray25"),
            command=self._go_summary,
        ).pack(side="left", padx=(0, 12))
        ctk.CTkButton(
            btn_row, text="Συνέχεια →", width=160,
            command=self._validate_and_advance,
        ).pack(side="left")

    def _go_pay_form(self):
        """Step 2 — redirect to secure form; reset all fields."""
        self._pay_form_total_var.set(f"{OrderController.cart_total():.2f} €")
        self._pay_form_error.set("")
        for e in (self._entry_holder, self._entry_number,
                  self._entry_expiry, self._entry_cvv):
            e.delete(0, "end")
            e.configure(border_color=("gray60", "gray40"))
        self._hide_all()
        self._pay_form_frame.grid(row=0, column=0, sticky="nsew")

    def _validate_and_advance(self):
        """Steps 4–5: validate fields; highlight errors or advance to review."""
        name = self._entry_holder.get().strip()
        num  = self._entry_number.get().replace(" ", "").replace("-", "")
        exp  = self._entry_expiry.get().strip()
        cvv  = self._entry_cvv.get().strip()

        # reset highlights
        _ok  = ("gray60", "gray40")
        _err = ("#e74c3c", "#e74c3c")
        for e in (self._entry_holder, self._entry_number,
                  self._entry_expiry, self._entry_cvv):
            e.configure(border_color=_ok)

        errors: list[str] = []

        if not name:
            self._entry_holder.configure(border_color=_err)
            errors.append("Κάτοχος κάρτας")

        if not num.isdigit() or len(num) != 16:
            self._entry_number.configure(border_color=_err)
            errors.append("Αριθμός κάρτας (16 ψηφία)")

        exp_ok = False
        parts = exp.split("/")
        if (len(parts) == 2
                and len(parts[0]) == 2 and parts[0].isdigit()
                and len(parts[1]) == 2 and parts[1].isdigit()):
            m, y = int(parts[0]), int(parts[1]) + 2000
            today = datetime.today()
            if 1 <= m <= 12 and (
                y > today.year or (y == today.year and m >= today.month)
            ):
                exp_ok = True
        if not exp_ok:
            self._entry_expiry.configure(border_color=_err)
            errors.append("Ημερομηνία λήξης (ΜΜ/ΕΕ π.χ. 12/27)")

        if not cvv.isdigit() or len(cvv) not in (3, 4):
            self._entry_cvv.configure(border_color=_err)
            errors.append("CVV (3 ψηφία)")

        if errors:
            # alt flow 1 — επισήμανση κενών/λανθασμένων πεδίων
            self._pay_form_error.set("Ελέγξτε: " + ",  ".join(errors) + ".")
            return

        # all valid — save and go to review (step 5)
        self._pay_card_holder = name
        self._pay_card_number = num
        self._pay_card_expiry = exp
        self._pay_form_error.set("")
        self._go_pay_review()

    # ================================================================ UC 2.5 — PAY REVIEW (steps 5–6 + alt flow 2)
    def _build_pay_review_frame(self):
        self._pay_review_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._pay_review_frame.columnconfigure(0, weight=1)
        self._pay_review_frame.rowconfigure(0, weight=1)

        card = ctk.CTkFrame(self._pay_review_frame, corner_radius=16)
        card.grid(row=0, column=0)

        ctk.CTkLabel(
            card, text="📋  Επιβεβαίωση Πληρωμής",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(padx=52, pady=(36, 16))

        self._review_details = ctk.CTkLabel(
            card, text="", justify="left",
            font=ctk.CTkFont(size=13), text_color="gray",
        )
        self._review_details.pack(padx=52, pady=(0, 8))

        self._review_total_var = ctk.StringVar()
        ctk.CTkLabel(
            card, textvariable=self._review_total_var,
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(padx=52, pady=(0, 24))

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(pady=(0, 36))
        ctk.CTkButton(
            btn_row, text="← Ακύρωση", width=130,
            fg_color="transparent", border_width=1,
            text_color=("gray20", "gray80"), hover_color=("gray85", "gray25"),
            command=self._go_summary,          # alt flow 2 — back to summary
        ).pack(side="left", padx=(0, 12))
        ctk.CTkButton(
            btn_row, text="✓  Πληρωμή", width=160,
            command=self._simulate_payment,    # step 6 — confirm
        ).pack(side="left")

    def _go_pay_review(self):
        """Step 5 — show masked card summary before final confirm."""
        masked = "**** **** **** " + self._pay_card_number[-4:]
        self._review_details.configure(text=(
            f"Κάτοχος:  {self._pay_card_holder}\n"
            f"Κάρτα:    {masked}\n"
            f"Λήξη:      {self._pay_card_expiry}"
        ))
        self._review_total_var.set(f"{OrderController.cart_total():.2f} €")
        self._hide_all()
        self._pay_review_frame.grid(row=0, column=0, sticky="nsew")

    def _simulate_payment(self):
        """Steps 7–8: simulate payment gateway; create order on approval."""
        # Simulation rule: card starting with "0000" → decline (useful for testing)
        if self._pay_card_number.startswith("0000"):
            self._go_pay_result(
                approved=False,
                reason="Η κάρτα απορρίφθηκε από τον πάροχο πληρωμών.\n"
                        "Ελέγξτε τα στοιχεία ή χρησιμοποιήστε άλλη κάρτα.",
            )
            return

        user = Session.current_user()
        try:
            order = OrderController.create_order(user.id, payment_method="card")
            self._last_order_id = order.id
            self._pay_txn_id = datetime.now().strftime("TXN-%Y%m%d%H%M%S")
            self._go_pay_result(approved=True)
        except OrderError as e:
            self._go_pay_result(approved=False, reason=str(e))

    # ================================================================ UC 2.5 — PAY RESULT (step 8 + alt flow 3)
    def _build_pay_result_frame(self):
        self._pay_result_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._pay_result_frame.columnconfigure(0, weight=1)
        self._pay_result_frame.rowconfigure(0, weight=1)

        card = ctk.CTkFrame(self._pay_result_frame, corner_radius=16)
        card.grid(row=0, column=0)

        self._result_icon = ctk.CTkLabel(card, text="",
                                         font=ctk.CTkFont(size=44))
        self._result_icon.pack(padx=52, pady=(36, 6))

        self._result_title = ctk.CTkLabel(card, text="",
                                          font=ctk.CTkFont(size=18, weight="bold"))
        self._result_title.pack(padx=52, pady=(0, 10))

        self._result_details = ctk.CTkLabel(
            card, text="", justify="center",
            font=ctk.CTkFont(size=13), text_color="gray", wraplength=360,
        )
        self._result_details.pack(padx=52, pady=(0, 24))

        # button row rebuilt dynamically per result
        self._result_btn_row = ctk.CTkFrame(card, fg_color="transparent")
        self._result_btn_row.pack(pady=(0, 36))

    def _go_pay_result(self, *, approved: bool, reason: str = ""):
        """Step 8 / alt flow 3 — show receipt or decline message."""
        for w in self._result_btn_row.winfo_children():
            w.destroy()

        if approved:
            # step 8 — αποδεικτικό συναλλαγής
            self._result_icon.configure(
                text="✔", text_color=("#27ae60", "#2ecc71"))
            self._result_title.configure(
                text="Η πληρωμή εγκρίθηκε!",
                text_color=("#27ae60", "#2ecc71"))
            self._result_details.configure(
                text=f"Κωδικός συναλλαγής: {self._pay_txn_id}\n"
                     f"Παραγγελία #{self._last_order_id} καταχωρήθηκε επιτυχώς.")
            ctk.CTkButton(
                self._result_btn_row,
                text="📦 Δες τις Παραγγελίες", width=230,
                command=lambda: self._navigate("orders"),
            ).pack()
        else:
            # alt flow 3 — απόρριψη συναλλαγής
            msg = reason or ("Η συναλλαγή απορρίφθηκε.\n"
                             "Ελέγξτε τα στοιχεία της κάρτας σας.")
            self._result_icon.configure(
                text="✘", text_color=("#e74c3c", "#e74c3c"))
            self._result_title.configure(
                text="Η πληρωμή απορρίφθηκε",
                text_color=("#e74c3c", "#e74c3c"))
            self._result_details.configure(text=msg)
            ctk.CTkButton(
                self._result_btn_row,
                text="← Δοκιμάστε ξανά", width=180,
                command=self._go_pay_form,
            ).pack(side="left", padx=(0, 12))
            ctk.CTkButton(
                self._result_btn_row,
                text="Ακύρωση", width=130,
                fg_color="transparent", border_width=1,
                text_color=("gray20", "gray80"), hover_color=("gray85", "gray25"),
                command=self._go_cart,
            ).pack(side="left")

        self._hide_all()
        self._pay_result_frame.grid(row=0, column=0, sticky="nsew")

 

#  Order History

_STATUS_MAP = {
    'pending':   ("Εκκρεμεί",      ("#e67e22", "#d68910")),
    'cancelled': ("✘ Ακυρωμένη",      ("#e74c3c", "#922b21")),
    'completed': ("✔ Ολοκληρωμένη",   ("#27ae60", "#2ecc71")),
}


class _OrderHistoryPage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        self._build()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=32, pady=(24, 4))
        ctk.CTkLabel(
            hdr, text="Ιστορικό Παραγγελιών",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(side="left")

        self._msg_var = ctk.StringVar()
        self._msg_label = ctk.CTkLabel(
            self, textvariable=self._msg_var,
            font=ctk.CTkFont(size=12), anchor="w",
        )
        self._msg_label.grid(row=1, column=0, sticky="ew", padx=32, pady=(0, 4))

        self._container = ctk.CTkScrollableFrame(self, corner_radius=10)
        self._container.grid(row=2, column=0, sticky="nsew", padx=32, pady=(0, 24))
        self._container.columnconfigure(0, weight=1)

    def refresh(self):
        self._load_orders()

    def _load_orders(self):
        for w in self._container.winfo_children():
            w.destroy()

        user = Session.current_user()
        orders = OrderController.get_orders(user.id)

        if not orders:
            ctk.CTkLabel(
                self._container,
                text="Δεν έχετε παραγγελίες ακόμα.",
                text_color="gray",
            ).grid(row=0, column=0, pady=48)
            return

        for i, order in enumerate(orders):
            card = ctk.CTkFrame(self._container, corner_radius=10)
            card.grid(row=i, column=0, sticky="ew", padx=8, pady=6)
            card.columnconfigure(0, weight=1)

            # header: order id | date | status badge
            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=16, pady=(12, 6))
            ctk.CTkLabel(
                top, text=f"Παραγγελία #{order.id}",
                font=ctk.CTkFont(size=13, weight="bold"),
            ).pack(side="left")

            status_text, status_color = _STATUS_MAP.get(
                order.status, (order.status, ("gray", "gray"))
            )
            ctk.CTkLabel(
                top, text=status_text, text_color=status_color,
                font=ctk.CTkFont(size=11, weight="bold"),
            ).pack(side="right", padx=(8, 0))
            ctk.CTkLabel(
                top, text=order.created_at[:16],
                text_color="gray", font=ctk.CTkFont(size=11),
            ).pack(side="right")

            # items
            for item in order.items:
                ctk.CTkLabel(
                    card,
                    text=f"  • {item.product_name}  ×{item.quantity}  —  {item.subtotal:.2f} €",
                    anchor="w", text_color="gray", font=ctk.CTkFont(size=12),
                ).pack(fill="x", padx=16)

            # footer: total + cancel button (step 2)
            footer = ctk.CTkFrame(card, fg_color="transparent")
            footer.pack(fill="x", padx=16, pady=(6, 12))
            ctk.CTkLabel(
                footer,
                text=f"Σύνολο: {order.total_price:.2f} €",
                font=ctk.CTkFont(size=13, weight="bold"),
            ).pack(side="left")

            if order.status == 'pending':
                ctk.CTkButton(
                    footer, text="Ακύρωση", width=110, height=28,
                    fg_color=("#e74c3c", "#922b21"), hover_color=("#c0392b", "#7b241c"),
                    font=ctk.CTkFont(size=11),
                    command=lambda oid=order.id: self._request_cancel(oid),
                ).pack(side="right")

    # messages
    def _show_msg(self, text: str, *, success: bool = True, info: bool = False):
        if success:
            color = ("#27ae60", "#2ecc71")
        elif info:
            color = ("#e67e22", "#d68910")
        else:
            color = ("#e74c3c", "#e74c3c")
        self._msg_label.configure(text_color=color)
        self._msg_var.set(text)
        self.after(5000, lambda: self._msg_var.set(""))

    # cancel flow
    def _request_cancel(self, order_id: int):
        """Βήμα 2 — ο πελάτης επιλέγει ακύρωση. Εμφάνιση επιβεβαίωσης."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Ακύρωση Παραγγελίας")
        dialog.geometry("420x200")
        dialog.resizable(False, False)
        dialog.grab_set()
        dialog.lift()
        dialog.focus_force()

        ctk.CTkLabel(
            dialog,
            text=f"Ακύρωση παραγγελίας #{order_id}",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(pady=(28, 8))
        ctk.CTkLabel(
            dialog,
            text="Θέλετε σίγουρα να ακυρώσετε αυτή την παραγγελία;",
            text_color="gray",
        ).pack(pady=(0, 24))

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack()
        ctk.CTkButton(
            btn_frame, text="Όχι", width=120,
            fg_color="transparent", border_width=1,
            text_color=("gray20", "gray80"), hover_color=("gray85", "gray25"),
            command=dialog.destroy,
        ).pack(side="left", padx=(0, 12))
        ctk.CTkButton(
            btn_frame, text="Ναι, ακύρωση", width=150,
            fg_color=("#e74c3c", "#922b21"), hover_color=("#c0392b", "#7b241c"),
            command=lambda: (dialog.destroy(), self._execute_cancel(order_id)),
        ).pack(side="left")

    def _execute_cancel(self, order_id: int):
        """Βήματα 3–7 — εκτέλεση ακύρωσης μέσω service layer."""
        user = Session.current_user()
        try:
            OrderController.cancel_order(order_id, user.id)
            # βήμα 7 — επιστροφή στο ιστορικό με ενημερωμένη λίστα
            self._show_msg(
                f"✔ Η παραγγελία #{order_id} ακυρώθηκε επιτυχώς!", success=True
            )
        except RefundError as e:
            # alt flow 3 — ακύρωση ΟΚ, refund απέτυχε
            self._show_msg(str(e), info=True)
        except OrderError as e:
            # alt flow 1 ή 2
            self._show_msg(str(e), success=False)
        self._load_orders()



#  Appointments — UC 2.2  


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

        # review state — UC 2.6
        self._rev_appt  = None   # AppointmentDetail being reviewed
        self._rev_rating = 0     # 1–5, 0 = not yet selected
        self._star_btns: list[ctk.CTkButton] = []


        self._build_list_frame()
        self._build_svc_frame()
        self._build_emp_frame()
        self._build_cal_frame()
        self._build_confirm_frame()
        self._build_unavailable_frame()
        self._build_mod_detail_frame()
        self._build_mod_confirm_frame()
        self._build_cancel_confirm_frame()
        self._build_review_form_frame()
        self._build_review_preview_frame()
        self._build_review_cancel_confirm_frame()

        self._go_list()

    # state router
    def _hide_all(self):
        for f in (
            self._list_frame, self._svc_frame, self._emp_frame,
            self._cal_frame, self._confirm_frame, self._unavailable_frame,
            self._mod_detail_frame, self._mod_confirm_frame, self._cancel_confirm_frame, self._review_form_frame, self._review_preview_frame,
            self._review_cancel_confirm_frame,


        ):
            f.grid_remove()

    def refresh(self):
        self._go_list()

       #  LIST (existing appointments)
    def _build_list_frame(self):
        self._list_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._list_frame.columnconfigure(0, weight=1)
        self._list_frame.rowconfigure(2, weight=1)

        hdr = ctk.CTkFrame(self._list_frame, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=32, pady=(24, 8))
        ctk.CTkLabel(
            hdr, text=" Ραντεβού μου",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(side="left")




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
                text="Δεν έχετε ραντεβού ακόμα.\nΜεταβείτε στα Κομμωτήρια για να κλείσετε ραντεβού.",
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
                text=f" {appt.scheduled_at}  —  {appt.service_name}",
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
            if appt.status == "done" and not ReviewController.exists_for_appointment(appt.id):
                review_footer = ctk.CTkFrame(card, fg_color="transparent")
                review_footer.pack(fill="x", padx=12, pady=(0, 10))
                ctk.CTkButton(
                    review_footer, text="⭐ Αξιολόγηση", width=140, height=28,
                    fg_color=("#f39c12", "#d68910"), hover_color=("#d68910", "#b7770d"),
                    font=ctk.CTkFont(size=11),
                    command=lambda a=appt: self._go_review_form(a),
                ).pack(side="right")

            if appt.status == "done" and ReviewController.exists_for_appointment(appt.id):
                ctk.CTkLabel(
                    card,
                    text="✔ Έχετε αξιολογήσει αυτό το ραντεβού.",
                    text_color=("gray50", "gray60"),
                    font=ctk.CTkFont(size=11),
                    anchor="e",
                ).pack(fill="x", padx=20, pady=(0, 8))

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
   
    def _build_review_form_frame(self):
        self._review_form_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._review_form_frame.columnconfigure(0, weight=1)
        self._review_form_frame.rowconfigure(0, weight=1)

        card = ctk.CTkFrame(self._review_form_frame, corner_radius=16)
        card.grid(row=0, column=0)
        card.columnconfigure(0, weight=1)

        # header
        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=52, pady=(32, 0))
        hdr.columnconfigure(1, weight=1)
        ctk.CTkButton(
            hdr, text="← Πίσω", width=100,
            fg_color="transparent", border_width=1,
            text_color=("gray20", "gray80"), hover_color=("gray85", "gray25"),
            command=self._go_list,
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            hdr, text="⭐  Αξιολόγηση Υπηρεσίας",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=1, sticky="w", padx=16)

        # appointment info
        self._rev_info_label = ctk.CTkLabel(
            card, text="", justify="left",
            font=ctk.CTkFont(size=13), text_color="gray",
        )
        self._rev_info_label.grid(row=1, column=0, sticky="w", padx=52, pady=(20, 0))

        # star rating row
        ctk.CTkLabel(
            card, text="Βαθμολογία:", anchor="w",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=2, column=0, sticky="w", padx=52, pady=(20, 4))

        star_row = ctk.CTkFrame(card, fg_color="transparent")
        star_row.grid(row=3, column=0, sticky="w", padx=48)
        self._star_btns = []
        for i in range(1, 6):
            btn = ctk.CTkButton(
                star_row,
                text="☆",
                width=44, height=44,
                font=ctk.CTkFont(size=28),
                fg_color="transparent",
                hover_color=("gray85", "gray25"),
                text_color=("#f39c12", "#f5b041"),
                corner_radius=6,
                command=lambda n=i: self._set_rating(n),
            )
            btn.pack(side="left", padx=2)
            self._star_btns.append(btn)

        self._rev_rating_hint = ctk.CTkLabel(
            card, text="", text_color="gray", font=ctk.CTkFont(size=11),
        )
        self._rev_rating_hint.grid(row=4, column=0, sticky="w", padx=52, pady=(2, 0))

        # comment
        ctk.CTkLabel(
            card, text="Σχόλιο (προαιρετικό):", anchor="w",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=5, column=0, sticky="w", padx=52, pady=(20, 4))
        self._rev_comment = ctk.CTkEntry(
            card, width=380, placeholder_text="Γράψτε την εμπειρία σας…",
        )
        self._rev_comment.grid(row=6, column=0, sticky="w", padx=52)

        # validation message
        self._rev_form_msg = ctk.StringVar()
        self._rev_form_msg_label = ctk.CTkLabel(
            card, textvariable=self._rev_form_msg,
            text_color=("#e74c3c", "#e74c3c"),
            font=ctk.CTkFont(size=12),
        )
        self._rev_form_msg_label.grid(row=7, column=0, sticky="w", padx=52, pady=(8, 0))

        # action button
        ctk.CTkButton(
            card, text="Προεπισκόπηση →", width=200,
            command=self._go_review_preview,
        ).grid(row=8, column=0, pady=(16, 40))

    def _go_review_form(self, appt=None):
        """Βήμα 3: εμφάνιση φόρμας αξιολόγησης. Alt flow 1: έλεγχος status."""
        if appt is not None:
            self._rev_appt = appt

        a = self._rev_appt
        # alt flow 1 — το ραντεβού δεν έχει ολοκληρωθεί
        if a.status != "done":
            self._list_msg_var.set(
                "ℹ Μπορείτε να αξιολογήσετε μόνο ολοκληρωμένα ραντεβού."
            )
            self.after(4000, lambda: self._list_msg_var.set(""))
            self._go_list()
            return

        self._rev_info_label.configure(
            text=(
                f"Υπηρεσία:    {a.service_name}\n"
                f"Υπάλληλος:  {a.employee_name}\n"
                f"Ημερομηνία: {a.scheduled_at}"
            )
        )
        self._rev_rating = 0
        self._update_stars()
        self._rev_comment.delete(0, "end")
        self._rev_form_msg.set("")

        self._hide_all()
        self._review_form_frame.grid(row=0, column=0, sticky="nsew")

    def _set_rating(self, n: int):
        self._rev_rating = n
        self._update_stars()
        self._rev_form_msg.set("")

    def _update_stars(self):
        _RATING_LABELS = {1: "Κακή", 2: "Μέτρια", 3: "Καλή", 4: "Πολύ καλή", 5: "Εξαιρετική"}
        for i, btn in enumerate(self._star_btns, start=1):
            btn.configure(text="★" if i <= self._rev_rating else "☆")
        hint = _RATING_LABELS.get(self._rev_rating, "Κάντε κλικ για να επιλέξετε βαθμολογία")
        self._rev_rating_hint.configure(text=hint)

    # UC 2.6 — REVIEW PREVIEW 
    def _build_review_preview_frame(self):
        self._review_preview_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._review_preview_frame.columnconfigure(0, weight=1)
        self._review_preview_frame.rowconfigure(0, weight=1)

        card = ctk.CTkFrame(self._review_preview_frame, corner_radius=16)
        card.grid(row=0, column=0)

        ctk.CTkLabel(
            card, text="  Προεπισκόπηση Αξιολόγησης",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(padx=60, pady=(36, 16))

        self._rev_preview_text = ctk.CTkLabel(
            card, text="", justify="left",
            font=ctk.CTkFont(size=13), text_color="gray",
        )
        self._rev_preview_text.pack(padx=60, pady=(0, 8))

        self._rev_preview_msg = ctk.StringVar()
        self._rev_preview_msg_label = ctk.CTkLabel(
            card, textvariable=self._rev_preview_msg,
            font=ctk.CTkFont(size=12), text_color=("#e74c3c", "#e74c3c"),
        )
        self._rev_preview_msg_label.pack(padx=60, pady=(0, 8))

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(pady=(4, 36))
        ctk.CTkButton(
            btn_row, text="← Επεξεργασία", width=140,
            fg_color="transparent", border_width=1,
            text_color=("gray20", "gray80"), hover_color=("gray85", "gray25"),
            command=self._go_review_form,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            btn_row, text="Ακύρωση", width=110,
            fg_color=("gray80", "gray30"), hover_color=("gray70", "gray25"),
            text_color=("gray10", "gray90"),
            command=self._go_review_cancel_confirm,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            btn_row, text="✓  Υποβολή", width=140,
            command=self._submit_review,
        ).pack(side="left")

    def _go_review_preview(self):
        """Βήμα 6: προεπισκόπηση. Alt flow 3: έλεγχος αν υπάρχει βαθμολογία."""
        # alt flow 3 — ελλιπή στοιχεία (χωρίς βαθμολογία)
        if self._rev_rating == 0:
            self._rev_form_msg.set("⚠  Επιλέξτε βαθμολογία (1–5 αστέρια).")
            return

        a       = self._rev_appt
        stars   = "★" * self._rev_rating + "☆" * (5 - self._rev_rating)
        comment = self._rev_comment.get().strip()

        self._rev_preview_text.configure(
            text=(
                f"Υπηρεσία:    {a.service_name}\n"
                f"Υπάλληλος:  {a.employee_name}\n"
                f"Ημερομηνία: {a.scheduled_at}\n"
                f"Βαθμολογία: {stars}  ({self._rev_rating}/5)\n"
                f"Σχόλιο:      {comment if comment else '—'}"
            )
        )
        self._rev_preview_msg.set("")
        self._hide_all()
        self._review_preview_frame.grid(row=0, column=0, sticky="nsew")

    def _submit_review(self):
        """Βήμα 8-9: υποβολή αξιολόγησης."""
        user    = Session.current_user()
        a       = self._rev_appt
        comment = self._rev_comment.get().strip() or None
        try:
            ReviewController.submit(
                appointment_id=a.id,
                customer_id=user.id,
                employee_id=a.employee_id,
                service_id=a.service_id,
                service_name=a.service_name,
                rating=self._rev_rating,
                comment=comment,
            )
            self._list_msg_var.set(
                f"✔ Η αξιολόγησή σας για «{a.service_name}» υποβλήθηκε επιτυχώς!"
            )
            self.after(6000, lambda: self._list_msg_var.set(""))
            self._go_list()
        except ReviewError as e:
            self._rev_preview_msg_label.configure(text_color=("#e74c3c", "#e74c3c"))
            self._rev_preview_msg.set(str(e))

    # UC 2.6 — REVIEW CANCEL CONFIRM 
    def _build_review_cancel_confirm_frame(self):
        self._review_cancel_confirm_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._review_cancel_confirm_frame.columnconfigure(0, weight=1)
        self._review_cancel_confirm_frame.rowconfigure(0, weight=1)

        card = ctk.CTkFrame(self._review_cancel_confirm_frame, corner_radius=16)
        card.grid(row=0, column=0)

        ctk.CTkLabel(
            card, text="✘  Ακύρωση Αξιολόγησης",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(padx=60, pady=(36, 10))

        ctk.CTkLabel(
            card,
            text="Θέλετε σίγουρα να ακυρώσετε την υποβολή\nτης αξιολόγησης;",
            text_color="gray", justify="center",
        ).pack(padx=60, pady=(0, 24))

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(pady=(0, 36))
        ctk.CTkButton(
            btn_row, text="Όχι, επιστροφή", width=160,
            fg_color="transparent", border_width=1,
            text_color=("gray20", "gray80"), hover_color=("gray85", "gray25"),
            command=self._go_review_preview,
        ).pack(side="left", padx=(0, 12))
        ctk.CTkButton(
            btn_row, text="Ναι, ακύρωση", width=150,
            fg_color=("#e74c3c", "#922b21"), hover_color=("#c0392b", "#7b241c"),
            command=self._go_list,
        ).pack(side="left")

    def _go_review_cancel_confirm(self):
        """Alt flow 2: ζητά επιβεβαίωση ακύρωσης πριν την οριστικοποίηση."""
        self._hide_all()
        self._review_cancel_confirm_frame.grid(row=0, column=0, sticky="nsew")
