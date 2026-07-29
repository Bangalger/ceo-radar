"""Captura screenshots del dashboard para validar el diseño.

Uso: py -3 scripts/capture_dashboard.py [url] [output_dir]
Requiere que el dashboard esté corriendo (streamlit run app.py).
"""

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

DEFAULT_URL = "http://localhost:8501"
DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / ".playwright"
WIDTHS = (1366, 1920, 2560)
TALL_HEIGHT = 3400


def _count_cards_per_row(page) -> int:
    """Cuenta cuántas cards colapsadas caben en la primera fila del grid."""
    return page.evaluate(
        """() => {
            const cards = [...document.querySelectorAll('[class*="st-key-collapsed_"]')];
            if (!cards.length) return 0;
            const firstTop = cards[0].getBoundingClientRect().top;
            return cards.filter(
                (card) => Math.abs(card.getBoundingClientRect().top - firstTop) < 8
            ).length;
        }"""
    )


def capture(url: str, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1920, "height": 1000}, device_scale_factor=1)

        console_errors: list[str] = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg.text) if msg.type == "error" else None,
        )

        page.goto(url, wait_until="networkidle")
        page.wait_for_timeout(4000)

        for width in WIDTHS:
            page.set_viewport_size({"width": width, "height": TALL_HEIGHT})
            page.wait_for_timeout(1500)
            page.screenshot(path=str(output_dir / f"radar-{width}.png"))
            cards_per_row = _count_cards_per_row(page)
            print(f"Ancho {width}px -> {cards_per_row} cards por fila")

        # Arranque colapsado: no debería haber botón "Contraer Detalles"
        initial_expanded = page.get_by_role("button", name="Contraer Detalles").count()
        print(
            "Arranque colapsado -> "
            + ("FALLA: hay evento expandido" if initial_expanded else "OK")
        )

        # Expandir y luego contraer
        expand_button = page.get_by_role("button", name="Expandir Detalles")
        if expand_button.count():
            expand_button.first.click()
            page.wait_for_timeout(2500)
            page.screenshot(path=str(output_dir / "radar-expanded.png"))

            collapse_button = page.get_by_role("button", name="Contraer Detalles")
            if collapse_button.count():
                collapse_button.first.click()
                page.wait_for_timeout(2500)
                page.screenshot(path=str(output_dir / "radar-collapsed.png"))
                still_expanded = page.get_by_role("button", name="Contraer Detalles").count()
                print(
                    "Expandir/Contraer -> "
                    + ("FALLA: sigue expandido" if still_expanded else "OK")
                )
            else:
                print("Expandir/Contraer -> FALLA: no apareció Contraer Detalles")
        else:
            print("Expandir/Contraer -> SKIP: no hay botones Expandir Detalles")

        audit_button = page.get_by_role("button", name="Auditoría")
        if audit_button.count():
            audit_button.first.click()
            page.wait_for_timeout(3000)
            page.screenshot(path=str(output_dir / "auditoria-tall.png"))
            print("Auditoría capturada")

        browser.close()

        if console_errors:
            print("Errores de consola:")
            for error in console_errors:
                print(f"  - {error}")


if __name__ == "__main__":
    target_url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL
    target_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUTPUT
    capture(target_url, target_dir)
