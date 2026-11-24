"""Учет компьютерной техники в организации."""

import sqlite3
import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox

DB_PATH = Path(__file__).resolve().with_name("inventory.db")

USERS = {
    "admin": ("admin", "Администратор"),
    "operator": ("operator", "Оператор"),
    "viewer": ("viewer", "Наблюдатель"),
}

PERMISSIONS = {
    "Администратор": {"add", "edit", "delete", "report"},
    "Оператор": {"add", "edit", "report"},
    "Наблюдатель": {"report"},
}

STATUSES = ("На складе", "В эксплуатации", "В ремонте", "Списано")

COLUMNS = (
    ("inventory_number", "Инв. номер", 110),
    ("name", "Наименование", 140),
    ("model", "Модель", 140),
    ("serial_number", "Серийный номер", 130),
    ("department", "Подразделение", 140),
    ("responsible", "Ответственный", 140),
    ("purchase_date", "Дата поступления", 120),
    ("status", "Статус", 120),
    ("cost", "Стоимость, руб.", 110),
)

SEED = [
    ("ИНВ-0001", "Системный блок", "IRU Office 310", "SN-10001", "Бухгалтерия", "Иванова А.С.", "2024-02-12",
     "В эксплуатации", 54000, "Рабочее место бухгалтера"),
    ("ИНВ-0002", "Монитор", "AOC 24B2", "SN-10002", "Бухгалтерия", "Иванова А.С.", "2024-02-12", "В эксплуатации",
     12000, ""),
    ("ИНВ-0003", "Ноутбук", "Lenovo IdeaPad 3", "SN-10003", "Отдел кадров", "Петров И.В.", "2023-11-03",
     "В эксплуатации", 61000, ""),
    ("ИНВ-0004", "Принтер", "HP LaserJet M111", "SN-10004", "Канцелярия", "Сидорова Н.П.", "2022-06-20", "В ремонте",
     18000, "Замятие бумаги"),
    ("ИНВ-0005", "МФУ", "Kyocera M2135dn", "SN-10005", "Приемная", "Орлова Е.К.", "2025-01-15", "В эксплуатации", 42000,
     ""),
    ("ИНВ-0006", "Системный блок", "DEXP Atlas", "SN-10006", "Склад", "Смирнов П.А.", "2025-09-01", "На складе", 39000,
     "Резерв"),
    ("ИНВ-0007", "Монитор", "Samsung S24R", "SN-10007", "Склад", "Смирнов П.А.", "2025-09-01", "На складе", 15000,
     "Резерв"),
    ("ИНВ-0008", "Ноутбук", "ASUS VivoBook 15", "SN-10008", "ИТ-отдел", "Кузнецов Д.А.", "2021-04-18", "Списано", 48000,
     "Истек срок полезного использования"),
]


def connect():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS equipment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inventory_number TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                model TEXT,
                serial_number TEXT,
                department TEXT,
                responsible TEXT,
                purchase_date TEXT,
                status TEXT NOT NULL,
                cost REAL,
                note TEXT
            )
            """
        )
        count = connection.execute("SELECT COUNT(*) AS c FROM equipment").fetchone()["c"]
        if count == 0:
            connection.executemany(
                """
                INSERT INTO equipment (
                    inventory_number, name, model, serial_number, department,
                    responsible, purchase_date, status, cost, note
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                SEED,
            )


class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.credentials = None
        self.title("Учет компьютерной техники")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)
        ttk.Label(
            frame,
            text="Вход в программу учета техники",
            font=("Segoe UI", 12),
        ).grid(row=0, column=0, columnspan=2, pady=(0, 16))
        ttk.Label(frame, text="Логин").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Label(frame, text="Пароль").grid(row=2, column=0, sticky="w", pady=4)

        self.login_var = tk.StringVar(master=self)
        self.password_var = tk.StringVar(master=self)
        login_entry = ttk.Entry(frame, textvariable=self.login_var, width=28)
        login_entry.grid(row=1, column=1, pady=4)
        password_entry = ttk.Entry(frame, textvariable=self.password_var, width=28, show="*")
        password_entry.grid(row=2, column=1, pady=4)
        ttk.Button(frame, text="Войти", command=self.try_login).grid(
            row=3, column=0, columnspan=2, pady=16
        )
        ttk.Label(
            frame,
            text="Учебные учетные записи: admin, operator, viewer.\nПароль совпадает с логином.",
            justify="center",
        ).grid(row=4, column=0, columnspan=2)

        self.bind("<Return>", lambda event: self.try_login())
        self.update_idletasks()
        width, height = 440, 250
        x = (self.winfo_screenwidth() - width) // 2
        y = (self.winfo_screenheight() - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")
        login_entry.focus_set()

    def on_close(self):
        self.credentials = None
        self.destroy()

    def try_login(self):
        login = self.login_var.get().strip()
        password = self.password_var.get()
        record = USERS.get(login)
        if record is None or record[0] != password:
            messagebox.showerror("Ошибка входа", "Неверный логин или пароль.")
            return
        self.credentials = (login, record[1])
        self.destroy()


class EquipmentDialog(tk.Toplevel):
    def __init__(self, master, title, initial=None, readonly=False):
        super().__init__(master)
        self.title(title)
        self.resizable(False, False)
        self.result = None
        self.transient(master)
        self.grab_set()

        initial = initial or {}
        cost = initial.get("cost")
        self.vars = {
            "inventory_number": tk.StringVar(master=self, value=initial.get("inventory_number", "")),
            "name": tk.StringVar(master=self, value=initial.get("name", "")),
            "model": tk.StringVar(master=self, value=initial.get("model", "")),
            "serial_number": tk.StringVar(master=self, value=initial.get("serial_number", "")),
            "department": tk.StringVar(master=self, value=initial.get("department", "")),
            "responsible": tk.StringVar(master=self, value=initial.get("responsible", "")),
            "purchase_date": tk.StringVar(master=self, value=initial.get("purchase_date", "")),
            "status": tk.StringVar(master=self, value=initial.get("status") or STATUSES[0]),
            "cost": tk.StringVar(master=self, value="" if cost is None else str(cost)),
            "note": tk.StringVar(master=self, value=initial.get("note") or ""),
        }

        labels = [
            ("inventory_number", "Инвентарный номер"),
            ("name", "Наименование"),
            ("model", "Модель"),
            ("serial_number", "Серийный номер"),
            ("department", "Подразделение"),
            ("responsible", "Ответственный"),
            ("purchase_date", "Дата поступления (ГГГГ-ММ-ДД)"),
            ("status", "Статус"),
            ("cost", "Стоимость, руб."),
            ("note", "Примечание"),
        ]

        frame = ttk.Frame(self, padding=12)
        frame.pack(fill="both", expand=True)
        for row, (key, label) in enumerate(labels):
            ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", pady=3, padx=(0, 8))
            if key == "status":
                state = "disabled" if readonly else "readonly"
                widget = ttk.Combobox(
                    frame,
                    textvariable=self.vars[key],
                    values=STATUSES,
                    state=state,
                    width=36,
                )
            else:
                state = "readonly" if readonly else "normal"
                widget = ttk.Entry(frame, textvariable=self.vars[key], width=38, state=state)
            widget.grid(row=row, column=1, pady=3)

        buttons = ttk.Frame(frame)
        buttons.grid(row=len(labels), column=0, columnspan=2, pady=(12, 0))
        if readonly:
            ttk.Button(buttons, text="Закрыть", command=self.destroy).pack()
        else:
            ttk.Button(buttons, text="Сохранить", command=self.save).pack(side="left", padx=4)
            ttk.Button(buttons, text="Отмена", command=self.destroy).pack(side="left", padx=4)
        self.wait_window()

    def save(self):
        data = {key: variable.get().strip() for key, variable in self.vars.items()}
        if not data["inventory_number"] or not data["name"]:
            messagebox.showwarning(
                "Проверка",
                "Заполните инвентарный номер и наименование.",
                parent=self,
            )
            return
        if data["status"] not in STATUSES:
            messagebox.showwarning("Проверка", "Выберите статус из списка.", parent=self)
            return
        if data["purchase_date"]:
            parts = data["purchase_date"].split("-")
            valid_date = (
                    len(parts) == 3
                    and all(part.isdigit() for part in parts)
                    and len(parts[0]) == 4
                    and len(parts[1]) == 2
                    and len(parts[2]) == 2
            )
            if not valid_date:
                messagebox.showwarning(
                    "Проверка",
                    "Дата должна иметь вид ГГГГ-ММ-ДД.",
                    parent=self,
                )
                return
        if data["cost"]:
            try:
                value = float(data["cost"].replace(",", "."))
            except ValueError:
                messagebox.showwarning("Проверка", "Стоимость должна быть числом.", parent=self)
                return
            if value < 0:
                messagebox.showwarning(
                    "Проверка",
                    "Стоимость не может быть отрицательной.",
                    parent=self,
                )
                return
            data["cost"] = value
        else:
            data["cost"] = None
        self.result = data
        self.destroy()


class MainWindow(tk.Tk):
    def __init__(self, login, role):
        super().__init__()
        self.login = login
        self.role = role
        self.perms = PERMISSIONS[role]
        self.logged_out = False
        self.title("Учет компьютерной техники в организации")
        self.geometry("1180x640")
        self.minsize(980, 520)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.search_var = tk.StringVar(master=self)
        self.status_filter = tk.StringVar(master=self, value="Все статусы")
        self.department_filter = tk.StringVar(master=self, value="Все подразделения")

        top = ttk.Frame(self, padding=(10, 8))
        top.pack(fill="x")
        ttk.Label(top, text=f"Пользователь: {login}. Роль: {role}.").pack(side="left")
        ttk.Button(top, text="Выход", command=self.logout).pack(side="right")

        filters = ttk.Frame(self, padding=(10, 0))
        filters.pack(fill="x")
        ttk.Label(filters, text="Поиск").pack(side="left")
        search_entry = ttk.Entry(filters, textvariable=self.search_var, width=32)
        search_entry.pack(side="left", padx=6)
        search_entry.bind("<KeyRelease>", lambda event: self.refresh())

        ttk.Label(filters, text="Статус").pack(side="left", padx=(12, 4))
        status_box = ttk.Combobox(
            filters,
            textvariable=self.status_filter,
            values=("Все статусы",) + STATUSES,
            state="readonly",
            width=18,
        )
        status_box.pack(side="left")
        status_box.bind("<<ComboboxSelected>>", lambda event: self.refresh())

        ttk.Label(filters, text="Подразделение").pack(side="left", padx=(12, 4))
        self.department_box = ttk.Combobox(
            filters,
            textvariable=self.department_filter,
            state="readonly",
            width=22,
        )
        self.department_box.pack(side="left")
        self.department_box.bind("<<ComboboxSelected>>", lambda event: self.refresh())

        table_frame = ttk.Frame(self, padding=10)
        table_frame.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(
            table_frame,
            columns=[key for key, _, _ in COLUMNS],
            show="headings",
            selectmode="browse",
        )
        for key, title, width in COLUMNS:
            self.tree.heading(key, text=title)
            self.tree.column(key, width=width, anchor="w")
        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.tree.bind("<Double-1>", lambda event: self.open_selected(readonly=True))

        buttons = ttk.Frame(self, padding=(10, 0, 10, 10))
        buttons.pack(fill="x")
        self.btn_add = ttk.Button(buttons, text="Добавить", command=self.add_item)
        self.btn_edit = ttk.Button(buttons, text="Изменить", command=lambda: self.open_selected(False))
        self.btn_delete = ttk.Button(buttons, text="Удалить", command=self.delete_item)
        self.btn_view = ttk.Button(buttons, text="Карточка", command=lambda: self.open_selected(True))
        self.btn_report = ttk.Button(buttons, text="Отчет", command=self.show_report)
        for button in (self.btn_add, self.btn_edit, self.btn_delete, self.btn_view, self.btn_report):
            button.pack(side="left", padx=4)

        self.btn_add.configure(state="normal" if "add" in self.perms else "disabled")
        self.btn_edit.configure(state="normal" if "edit" in self.perms else "disabled")
        self.btn_delete.configure(state="normal" if "delete" in self.perms else "disabled")
        self.btn_report.configure(state="normal" if "report" in self.perms else "disabled")

        self.status_bar = ttk.Label(self, anchor="w", padding=(10, 4))
        self.status_bar.pack(fill="x")
        self.refresh()

    def on_close(self):
        self.logged_out = False
        self.destroy()

    def logout(self):
        self.logged_out = True
        self.destroy()

    def selected_id(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Выбор записи", "Выберите строку в таблице.")
            return None
        return int(selection[0])

    def load_departments(self):
        with connect() as connection:
            rows = connection.execute(
                """
                SELECT DISTINCT department
                FROM equipment
                WHERE department IS NOT NULL AND department != ''
                ORDER BY department
                """
            ).fetchall()
        values = ["Все подразделения"] + [row["department"] for row in rows]
        self.department_box.configure(values=values)
        if self.department_filter.get() not in values:
            self.department_filter.set("Все подразделения")

    def refresh(self):
        self.load_departments()
        query = "SELECT * FROM equipment WHERE 1 = 1"
        params = []
        text = self.search_var.get().strip()
        if text:
            query += """
                AND (
                    inventory_number LIKE ? OR name LIKE ? OR model LIKE ?
                    OR serial_number LIKE ? OR department LIKE ? OR responsible LIKE ?
                )
            """
            params.extend([f"%{text}%"] * 6)
        if self.status_filter.get() != "Все статусы":
            query += " AND status = ?"
            params.append(self.status_filter.get())
        if self.department_filter.get() != "Все подразделения":
            query += " AND department = ?"
            params.append(self.department_filter.get())
        query += " ORDER BY inventory_number"

        with connect() as connection:
            rows = connection.execute(query, params).fetchall()
        self.tree.delete(*self.tree.get_children())
        for row in rows:
            values = []
            for key, _, _ in COLUMNS:
                value = row[key]
                if key == "cost" and value is not None:
                    value = f"{value:.2f}"
                values.append("" if value is None else value)
            self.tree.insert("", "end", iid=str(row["id"]), values=values)
        self.status_bar.configure(text=f"Показано записей: {len(rows)}")

    def add_item(self):
        dialog = EquipmentDialog(self, "Новая единица техники")
        if dialog.result is None:
            return
        data = dialog.result
        try:
            with connect() as connection:
                connection.execute(
                    """
                    INSERT INTO equipment (
                        inventory_number, name, model, serial_number, department,
                        responsible, purchase_date, status, cost, note
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        data["inventory_number"], data["name"], data["model"], data["serial_number"],
                        data["department"], data["responsible"], data["purchase_date"], data["status"],
                        data["cost"], data["note"],
                    ),
                )
        except sqlite3.IntegrityError:
            messagebox.showerror("Сохранение", "Такой инвентарный номер уже есть в базе.")
            return
        self.refresh()

    def open_selected(self, readonly):
        if not readonly and "edit" not in self.perms:
            messagebox.showwarning("Права доступа", "Для этой роли изменение записей недоступно.")
            return
        item_id = self.selected_id()
        if item_id is None:
            return
        with connect() as connection:
            row = connection.execute(
                "SELECT * FROM equipment WHERE id = ?",
                (item_id,),
            ).fetchone()
        if row is None:
            return
        dialog = EquipmentDialog(
            self,
            "Карточка техники" if readonly else "Изменение записи",
            initial=dict(row),
            readonly=readonly,
        )
        if readonly or dialog.result is None:
            return
        data = dialog.result
        try:
            with connect() as connection:
                connection.execute(
                    """
                    UPDATE equipment SET
                        inventory_number = ?, name = ?, model = ?, serial_number = ?,
                        department = ?, responsible = ?, purchase_date = ?, status = ?,
                        cost = ?, note = ?
                    WHERE id = ?
                    """,
                    (
                        data["inventory_number"], data["name"], data["model"], data["serial_number"],
                        data["department"], data["responsible"], data["purchase_date"], data["status"],
                        data["cost"], data["note"], item_id,
                    ),
                )
        except sqlite3.IntegrityError:
            messagebox.showerror("Сохранение", "Такой инвентарный номер уже есть в базе.")
            return
        self.refresh()

    def delete_item(self):
        if "delete" not in self.perms:
            messagebox.showwarning("Права доступа", "Удаление доступно только администратору.")
            return
        item_id = self.selected_id()
        if item_id is None:
            return
        if not messagebox.askyesno("Удаление", "Удалить выбранную единицу техники?"):
            return
        with connect() as connection:
            connection.execute("DELETE FROM equipment WHERE id = ?", (item_id,))
        self.refresh()

    def show_report(self):
        with connect() as connection:
            by_status = connection.execute(
                "SELECT status, COUNT(*) AS qty FROM equipment GROUP BY status ORDER BY status"
            ).fetchall()
            by_department = connection.execute(
                """
                SELECT COALESCE(NULLIF(department, ''), 'Без подразделения') AS department,
                       COUNT(*) AS qty,
                       COALESCE(SUM(cost), 0) AS total
                FROM equipment
                GROUP BY department
                ORDER BY department
                """
            ).fetchall()
            total = connection.execute(
                "SELECT COUNT(*) AS qty, COALESCE(SUM(cost), 0) AS total FROM equipment"
            ).fetchone()

        window = tk.Toplevel(self)
        window.title("Сводка по технике")
        window.geometry("640x420")
        text = tk.Text(window, wrap="word", font=("Segoe UI", 11))
        text.pack(fill="both", expand=True, padx=10, pady=10)
        lines = [
            f"Всего единиц: {total['qty']}",
            f"Суммарная стоимость: {total['total']:.2f} руб.",
            "",
            "По статусам:",
        ]
        for row in by_status:
            lines.append(f"  {row['status']}: {row['qty']}")
        lines.append("")
        lines.append("По подразделениям:")
        for row in by_department:
            lines.append(f"  {row['department']}: {row['qty']} ед., {row['total']:.2f} руб.")
        text.insert("1.0", "\n".join(lines))
        text.configure(state="disabled")


def apply_theme(root):
    style = ttk.Style(root)
    if "vista" in style.theme_names():
        style.theme_use("vista")


def main():
    init_db()
    while True:
        login = LoginWindow()
        apply_theme(login)
        login.mainloop()
        if login.credentials is None:
            break
        application = MainWindow(*login.credentials)
        apply_theme(application)
        application.mainloop()
        if not application.logged_out:
            break


if __name__ == "__main__":
    main()
