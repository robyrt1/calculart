"""Regras de cálculo e armazenamento do Calcularte (sem interface gráfica)."""
import json
import os
import sys
from pathlib import Path


def parse_number(text: str) -> float:
    """Converte '12,50' ou '1.234,56' ou '12.5' em float. Vazio vira 0."""
    text = (text or "").strip().replace("R$", "").replace(" ", "")
    if not text:
        return 0.0
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    value = float(text)
    if value < 0:
        raise ValueError("valor negativo")
    return value


def format_money(value: float) -> str:
    s = f"{value:,.2f}"
    return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")


def unit_price(paid: float, pack_qty: float) -> float:
    """Preço por unidade de medida: quanto pagou / quanto veio na embalagem."""
    if pack_qty <= 0:
        raise ValueError("quantidade da embalagem deve ser maior que zero")
    return paid / pack_qty


def format_unit_money(value: float) -> str:
    """Como format_money, mas com até 4 casas para preços unitários pequenos."""
    s = f"{value:,.4f}".rstrip("0")
    if len(s.split(".")[1]) < 2:
        s = f"{value:,.2f}"
    return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")


def yield_units(pack_qty: float, qty_used: float) -> int:
    """Quantas unidades do produto uma embalagem rende (ex.: rolo de 50 m / 0,3 m = 166)."""
    if qty_used <= 0:
        return 0
    return int(pack_qty / qty_used + 1e-9)


def calculate(materials, minutes, hourly_rate, extra_percent, margin_percent, quantity=1):
    """Calcula tudo POR UMA UNIDADE do produto e também o total do pedido.

    materials: custos de material gastos em 1 unidade
    minutes: minutos de trabalho para fazer 1 unidade
    hourly_rate: valor da hora de trabalho
    extra_percent: % de custos extras (embalagem, taxas) sobre material + mão de obra
    margin_percent: % de lucro sobre o custo
    quantity: quantas unidades no pedido (só para o total)
    """
    quantity = max(int(quantity), 1)
    material = sum(materials)
    labor = minutes / 60 * hourly_rate
    base = material + labor
    extras = base * extra_percent / 100
    cost_unit = base + extras
    profit_unit = cost_unit * margin_percent / 100
    price_unit = cost_unit + profit_unit
    return {
        "material": material,
        "labor": labor,
        "extras": extras,
        "cost_unit": cost_unit,
        "profit_unit": profit_unit,
        "price_unit": price_unit,
        "quantity": quantity,
        "cost_total": cost_unit * quantity,
        "profit_total": profit_unit * quantity,
        "price_total": price_unit * quantity,
    }


def data_file(filename: str = "produtos.json") -> Path:
    base = os.environ.get("APPDATA") or os.path.join(Path.home(), ".local", "share")
    folder = Path(base) / "Calcularte"
    folder.mkdir(parents=True, exist_ok=True)
    return folder / filename


def load_products(path: Path | None = None, filename: str = "produtos.json") -> list:
    path = path or data_file(filename)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_products(products: list, path: Path | None = None, filename: str = "produtos.json") -> None:
    path = path or data_file(filename)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(products, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def load_materials(path: Path | None = None) -> list:
    """Catálogo: [{"nome", "unidade", "preco"}] (preço por unidade de medida)."""
    return load_products(path, "materiais.json")


def save_materials(materials: list, path: Path | None = None) -> None:
    save_products(materials, path, "materiais.json")
