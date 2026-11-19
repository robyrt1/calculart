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


def calculate(materials, hours, hourly_rate, extra_percent, margin_percent, quantity=1):
    """Retorna dict com custos e preço de venda.

    materials: lista de custos de material (para o lote inteiro)
    extra_percent: % de custos extras (embalagem, taxas) sobre material + mão de obra
    margin_percent: % de lucro sobre o custo total
    quantity: unidades produzidas no lote
    """
    quantity = max(int(quantity), 1)
    material_total = sum(materials)
    labor = hours * hourly_rate
    base = material_total + labor
    extras = base * extra_percent / 100
    cost_total = base + extras
    profit = cost_total * margin_percent / 100
    price_total = cost_total + profit
    return {
        "material": material_total,
        "labor": labor,
        "extras": extras,
        "cost_total": cost_total,
        "profit": profit,
        "price_total": price_total,
        "cost_unit": cost_total / quantity,
        "price_unit": price_total / quantity,
        "quantity": quantity,
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
