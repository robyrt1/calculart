"""Interface gráfica do Calcularte."""
import tkinter as tk
from tkinter import messagebox, ttk

import sv_ttk

from logic import (calculate, format_money, load_materials, load_products,
                   parse_number, save_materials, save_products)

UNITS = ["un", "m", "cm", "g", "kg", "ml", "L", "folha", "pacote", "rolo"]

FONT = ("Segoe UI", 12)
FONT_TITLE = ("Segoe UI", 20, "bold")
FONT_SECTION = ("Segoe UI", 13, "bold")
FONT_PRICE = ("Segoe UI", 30, "bold")
FONT_HINT = ("Segoe UI", 10)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Calcularte - Calculadora de Preços")
        self.geometry("1020x700")
        self.minsize(940, 700)
        self.dark = False
        sv_ttk.set_theme("light")
        self._style_widgets()
        self.products = load_products()
        self.catalog = load_materials()  # [{"nome","unidade","preco"}]
        self.materials = []  # usados no produto: [(nome, qtd, unidade, custo)]
        self._build()
        self._refresh_products()
        self._refresh_catalog()

    # ---------- layout ----------
    def _style_widgets(self):
        st = ttk.Style(self)
        st.configure(".", font=FONT)
        st.configure("Treeview", rowheight=32, font=FONT)
        st.configure("Treeview.Heading", font=("Segoe UI", 11, "bold"))
        st.configure("TNotebook.Tab", font=FONT, padding=(18, 8))
        st.configure("Title.TLabel", font=FONT_TITLE)
        st.configure("Section.TLabel", font=FONT_SECTION)
        st.configure("Hint.TLabel", font=FONT_HINT)
        st.configure("Price.TLabel", font=FONT_PRICE)
        self.option_add("*TCombobox*Listbox.font", FONT)

    def toggle_theme(self):
        self.dark = not self.dark
        sv_ttk.set_theme("dark" if self.dark else "light")
        self._style_widgets()
        self.theme_btn.config(text="Tema claro" if self.dark else "Tema escuro")

    def _build(self):
        head = ttk.Frame(self, padding=(20, 14, 20, 0))
        head.pack(fill="x")
        ttk.Label(head, text="Calcularte", style="Title.TLabel").pack(side="left")
        ttk.Label(head, text="   preço justo para o seu trabalho", style="Hint.TLabel").pack(side="left", pady=(10, 0))
        self.theme_btn = ttk.Button(head, text="Tema escuro", command=self.toggle_theme)
        self.theme_btn.pack(side="right")

        nb = self.nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=14, pady=12)
        calc = ttk.Frame(nb, padding=16)
        mats = ttk.Frame(nb, padding=16)
        saved = ttk.Frame(nb, padding=16)
        nb.add(calc, text="Calcular preço")
        nb.add(mats, text="Materiais")
        nb.add(saved, text="Produtos salvos")
        self._build_calc(calc)
        self._build_catalog(mats)
        self._build_saved(saved)

    def _build_calc(self, f):
        f.columnconfigure(0, weight=3)
        f.columnconfigure(1, weight=2)
        f.rowconfigure(0, weight=1)
        left = ttk.Frame(f)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        left.columnconfigure(0, weight=1)

        ttk.Label(left, text="Produto", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        self.name = ttk.Entry(left)
        self.name.grid(row=1, column=0, sticky="ew", pady=(4, 14))

        ttk.Label(left, text="Materiais usados", style="Section.TLabel").grid(row=2, column=0, sticky="w")
        pick = ttk.Frame(left)
        pick.grid(row=3, column=0, sticky="ew", pady=(4, 6))
        pick.columnconfigure(0, weight=1)
        self.mat_pick = ttk.Combobox(pick, state="readonly")
        self.mat_pick.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.mat_pick.bind("<<ComboboxSelected>>", lambda e: self._update_unit_label())
        self.mat_qty = ttk.Entry(pick, width=8)
        self.mat_qty.grid(row=0, column=1, padx=(0, 8))
        self.mat_qty.bind("<Return>", lambda e: self.add_material())
        ttk.Button(pick, text="Adicionar", style="Accent.TButton", command=self.add_material).grid(row=0, column=2)
        self.mat_unit = ttk.Label(left, text="Escolha o material e a quantidade usada", style="Hint.TLabel")
        self.mat_unit.grid(row=4, column=0, sticky="w")

        self.mat_list = ttk.Treeview(left, columns=("mat", "qtd", "custo"), show="headings", height=3)
        for c, t, w, an in (("mat", "Material", 220, "w"), ("qtd", "Quantidade", 110, "w"), ("custo", "Custo", 110, "e")):
            self.mat_list.heading(c, text=t, anchor=an)
            self.mat_list.column(c, width=w, anchor=an)
        self.mat_list.grid(row=5, column=0, sticky="ew", pady=6)
        ttk.Button(left, text="Remover selecionado", command=self.remove_material).grid(row=6, column=0, sticky="w")

        ttk.Label(left, text="Trabalho e lucro", style="Section.TLabel").grid(row=7, column=0, sticky="w", pady=(16, 4))
        grid = ttk.Frame(left)
        grid.grid(row=8, column=0, sticky="ew")
        grid.columnconfigure((0, 1, 2), weight=1, uniform="g")
        self.hours = self._field(grid, 0, 0, "Horas de trabalho", "0")
        self.rate = self._field(grid, 0, 1, "Valor da hora (R$)", "0")
        self.qty = self._field(grid, 0, 2, "Unidades produzidas", "1")
        self.extra = self._field(grid, 2, 0, "Custos extras (%)", "0")
        self.margin = self._field(grid, 2, 1, "Lucro desejado (%)", "50")
        ttk.Label(grid, text="Extras: embalagem, taxas, etc.", style="Hint.TLabel", wraplength=150).grid(
            row=2, column=2, sticky="w", pady=(0, 10))

        # ----- cartão de resultado -----
        right = ttk.LabelFrame(f, text=" Resultado ", padding=18)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        ttk.Label(right, text="Preço de venda (cada)", style="Hint.TLabel").grid(row=0, column=0, sticky="w")
        self.result = ttk.Label(right, text="R$ 0,00", style="Price.TLabel")
        self.result.grid(row=1, column=0, sticky="w", pady=(0, 14))
        self.detail = ttk.Label(right, text="Preencha os dados e clique em Calcular.", justify="left")
        self.detail.grid(row=2, column=0, sticky="w")
        ttk.Separator(right).grid(row=3, column=0, sticky="ew", pady=16)
        ttk.Button(right, text="Calcular", style="Accent.TButton", command=self.compute).grid(
            row=4, column=0, sticky="ew", ipady=4, pady=3)
        ttk.Button(right, text="Salvar produto", command=self.save_product).grid(
            row=5, column=0, sticky="ew", ipady=4, pady=3)
        ttk.Button(right, text="Limpar tudo", command=self.clear).grid(
            row=6, column=0, sticky="ew", ipady=4, pady=3)

    def _field(self, parent, row, col, label, default):
        ttk.Label(parent, text=label).grid(row=row, column=col, sticky="w", padx=(0, 10))
        e = ttk.Entry(parent)
        e.insert(0, default)
        e.grid(row=row + 1, column=col, sticky="ew", padx=(0, 10), pady=(2, 10))
        return e

    def _build_catalog(self, f):
        form = ttk.Frame(f)
        form.pack(fill="x")
        ttk.Label(form, text="Cadastrar / atualizar material", style="Section.TLabel").grid(
            row=0, column=0, columnspan=4, sticky="w", pady=(0, 6))
        ttk.Label(form, text="Nome").grid(row=1, column=0, sticky="w")
        ttk.Label(form, text="Unidade de compra").grid(row=1, column=1, sticky="w")
        ttk.Label(form, text="Preço por unidade (R$)").grid(row=1, column=2, sticky="w")
        self.cat_name = ttk.Entry(form, width=32)
        self.cat_name.grid(row=2, column=0, sticky="w", padx=(0, 10), pady=(2, 0))
        self.cat_unit = ttk.Combobox(form, values=UNITS, width=10)
        self.cat_unit.set("un")
        self.cat_unit.grid(row=2, column=1, sticky="w", padx=(0, 10), pady=(2, 0))
        self.cat_price = ttk.Entry(form, width=16)
        self.cat_price.grid(row=2, column=2, sticky="w", padx=(0, 10), pady=(2, 0))
        ttk.Button(form, text="Salvar material", style="Accent.TButton", command=self.save_catalog_item).grid(
            row=2, column=3, padx=(0, 8))
        ttk.Button(form, text="Limpar", command=self._clear_catalog_form).grid(row=2, column=4)
        ttk.Label(form, text="Exemplo: fita a R$ 3,00 o metro → unidade m, preço 3,00",
                  style="Hint.TLabel").grid(row=3, column=0, columnspan=4, sticky="w", pady=(6, 0))

        self.cat_tree = ttk.Treeview(f, columns=("nome", "unidade", "preco"), show="headings")
        for c, t, w in (("nome", "Material", 340), ("unidade", "Unidade", 100), ("preco", "Preço por unidade", 160)):
            self.cat_tree.heading(c, text=t)
            self.cat_tree.column(c, width=w)
        self.cat_tree.pack(fill="both", expand=True, pady=14)
        self.cat_tree.bind("<<TreeviewSelect>>", lambda e: self._fill_catalog_form())
        ttk.Button(f, text="Excluir selecionado", command=self.delete_catalog_item).pack(anchor="w")

    def _build_saved(self, f):
        cols = ("nome", "custo", "preco")
        self.tree = ttk.Treeview(f, columns=cols, show="headings")
        for c, t, w in (("nome", "Produto", 340), ("custo", "Custo unitário", 150), ("preco", "Preço de venda", 150)):
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w)
        self.tree.pack(fill="both", expand=True)
        row = ttk.Frame(f)
        row.pack(fill="x", pady=8)
        ttk.Button(row, text="Abrir para editar", command=self.load_selected).pack(side="left", padx=(0, 8))
        ttk.Button(row, text="Excluir", command=self.delete_selected).pack(side="left")

    # ---------- catálogo de materiais ----------
    def save_catalog_item(self):
        name = self.cat_name.get().strip()
        unit = self.cat_unit.get().strip() or "un"
        if not name:
            return messagebox.showerror("Erro", "Digite o nome do material.")
        try:
            price = parse_number(self.cat_price.get())
        except ValueError:
            return messagebox.showerror("Erro", "Preço inválido.")
        if price <= 0:
            return messagebox.showerror("Erro", "Informe o preço por unidade.")
        self.catalog = [m for m in self.catalog if m["nome"].lower() != name.lower()]
        self.catalog.append({"nome": name, "unidade": unit, "preco": price})
        save_materials(self.catalog)
        self._refresh_catalog()
        self._clear_catalog_form()

    def _clear_catalog_form(self):
        self.cat_name.delete(0, "end")
        self.cat_price.delete(0, "end")
        self.cat_unit.set("un")
        self.cat_tree.selection_remove(self.cat_tree.selection())

    def _fill_catalog_form(self):
        sel = self.cat_tree.selection()
        m = next((m for m in self.catalog if sel and m["nome"] == sel[0]), None)
        if m:
            self.cat_name.delete(0, "end")
            self.cat_name.insert(0, m["nome"])
            self.cat_unit.set(m["unidade"])
            self.cat_price.delete(0, "end")
            self.cat_price.insert(0, f"{m['preco']:.2f}".replace(".", ","))

    def delete_catalog_item(self):
        sel = self.cat_tree.selection()
        if sel and messagebox.askyesno("Excluir", f"Excluir '{sel[0]}' do cadastro?\n"
                                       "Produtos já salvos não são alterados."):
            self.catalog = [m for m in self.catalog if m["nome"] != sel[0]]
            save_materials(self.catalog)
            self._refresh_catalog()
            self._clear_catalog_form()

    def _refresh_catalog(self):
        items = sorted(self.catalog, key=lambda m: m["nome"].lower())
        self.cat_tree.delete(*self.cat_tree.get_children())
        for m in items:
            self.cat_tree.insert("", "end", iid=m["nome"], values=(
                m["nome"], m["unidade"], format_money(m["preco"])))
        self.mat_pick["values"] = [m["nome"] for m in items]
        if self.mat_pick.get() not in self.mat_pick["values"]:
            self.mat_pick.set("")
        self._update_unit_label()

    def _picked(self):
        return next((m for m in self.catalog if m["nome"] == self.mat_pick.get()), None)

    def _update_unit_label(self):
        m = self._picked()
        self.mat_unit.config(text=f"{format_money(m['preco'])} por {m['unidade']}" if m
                             else "Escolha o material e a quantidade usada")

    # ---------- materiais do produto ----------
    def add_material(self):
        m = self._picked()
        if not m:
            return messagebox.showerror(
                "Erro", "Escolha um material da lista.\nSe não aparecer, cadastre na aba 'Materiais'.")
        try:
            qty = parse_number(self.mat_qty.get())
        except ValueError:
            return messagebox.showerror("Erro", "Quantidade inválida.")
        if qty <= 0:
            return messagebox.showerror("Erro", "Informe a quantidade usada.")
        self.materials.append((m["nome"], qty, m["unidade"], qty * m["preco"]))
        self._refresh_materials()
        self.mat_qty.delete(0, "end")
        self.mat_pick.focus()

    def remove_material(self):
        sel = self.mat_list.selection()
        if sel:
            del self.materials[self.mat_list.index(sel[0])]
            self._refresh_materials()

    def _refresh_materials(self):
        self.mat_list.delete(*self.mat_list.get_children())
        for n, q, u, c in self.materials:
            self.mat_list.insert("", "end", values=(n, f"{q:g} {u}", format_money(c)))

    # ---------- cálculo ----------
    def _read(self):
        try:
            return calculate(
                [m[3] for m in self.materials],
                parse_number(self.hours.get()),
                parse_number(self.rate.get()),
                parse_number(self.extra.get()),
                parse_number(self.margin.get()),
                int(parse_number(self.qty.get()) or 1),
            )
        except ValueError:
            messagebox.showerror("Erro", "Confira os números digitados (use apenas números positivos).")
            return None

    def compute(self):
        r = self._read()
        if not r:
            return None
        self.result.config(text=format_money(r["price_unit"]))
        self.detail.config(text=(
            f"Materiais: {format_money(r['material'])}\n"
            f"Mão de obra: {format_money(r['labor'])}\n"
            f"Custos extras: {format_money(r['extras'])}\n"
            f"Custo total: {format_money(r['cost_total'])}  "
            f"(cada: {format_money(r['cost_unit'])})\n"
            f"Lucro total: {format_money(r['profit'])}\n"
            f"Total do lote ({r['quantity']} un.): {format_money(r['price_total'])}"
        ))
        return r

    def clear(self):
        self.materials = []
        self._refresh_materials()
        self.name.delete(0, "end")
        for e, v in ((self.hours, "0"), (self.rate, "0"), (self.extra, "0"), (self.margin, "50"), (self.qty, "1")):
            e.delete(0, "end")
            e.insert(0, v)
        self.result.config(text="R$ 0,00")
        self.detail.config(text="Preencha os dados e clique em Calcular.")

    # ---------- produtos salvos ----------
    def save_product(self):
        name = self.name.get().strip()
        if not name:
            return messagebox.showerror("Erro", "Digite o nome do produto.")
        r = self.compute()
        if not r:
            return
        item = {
            "nome": name,
            "materiais": self.materials,
            "horas": self.hours.get(), "hora_valor": self.rate.get(),
            "extras": self.extra.get(), "lucro": self.margin.get(), "qtd": self.qty.get(),
            "custo_unit": r["cost_unit"], "preco_unit": r["price_unit"],
        }
        self.products = [p for p in self.products if p["nome"].lower() != name.lower()] + [item]
        save_products(self.products)
        self._refresh_products()
        messagebox.showinfo("Salvo", f"Produto '{name}' salvo.")

    def _refresh_products(self):
        self.tree.delete(*self.tree.get_children())
        for i, p in enumerate(sorted(self.products, key=lambda p: p["nome"].lower())):
            self.tree.insert("", "end", iid=p["nome"], values=(
                p["nome"], format_money(p["custo_unit"]), format_money(p["preco_unit"])))

    def _selected(self):
        sel = self.tree.selection()
        return next((p for p in self.products if p["nome"] == sel[0]), None) if sel else None

    def load_selected(self):
        p = self._selected()
        if not p:
            return
        self.clear()
        self.name.insert(0, p["nome"])
        self.materials = [tuple(m) for m in p["materiais"]]
        self._refresh_materials()
        for e, k in ((self.hours, "horas"), (self.rate, "hora_valor"), (self.extra, "extras"),
                     (self.margin, "lucro"), (self.qty, "qtd")):
            e.delete(0, "end")
            e.insert(0, p[k])
        self.compute()
        self.nb.select(0)

    def delete_selected(self):
        p = self._selected()
        if p and messagebox.askyesno("Excluir", f"Excluir '{p['nome']}'?"):
            self.products.remove(p)
            save_products(self.products)
            self._refresh_products()


if __name__ == "__main__":
    App().mainloop()
