# app.py
# Streamlit HTML → PDF exporter (keeps links), using Playwright/Chromium
# Author: Raghav

import io
import os
import zipfile
import tempfile
from pathlib import Path
from typing import Optional, Tuple

import streamlit as st
import base64
# Playwright (sync API)
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError

APP_TITLE = "HTML → PDF Export (links preserved)"


# ---------- Utilities ----------

def find_html_in_zip(zip_path: Path) -> Optional[Path]:
    """Extracts ZIP to a temp dir and returns the best HTML entry (index.html preferred)."""
    extract_dir = Path(tempfile.mkdtemp(prefix="html2pdf_zip_"))
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_dir)
    # Prefer index.html
    idx = (extract_dir / "index.html")
    if idx.exists():
        return idx
    # else first .html we can find
    html_files = list(extract_dir.rglob("*.html")) + list(extract_dir.rglob("*.htm"))
    return html_files[0] if html_files else None


def normalize_paper(paper_choice: str, custom_w: Optional[str], custom_h: Optional[str]) -> Tuple[
    Optional[str], Optional[str], Optional[str]]:
    """
    Returns (format, width, height) for Playwright's page.pdf().
    If 'Custom', width/height must be strings like '210mm' or '8.5in'.
    """
    if paper_choice == "Custom":
        width = (custom_w or "").strip() or None
        height = (custom_h or "").strip() or None
        return None, width, height
    else:
        return paper_choice, None, None


def render_pdf(
    html: str,
    base_url: Optional[str],
    format_name: Optional[str],
    width: Optional[str],
    height: Optional[str],
    margins: dict,
    landscape: bool,
    print_background: bool,
    scale: float,
    header_template: Optional[str],
    footer_template: Optional[str],
    prefer_css_page_size: bool,
    wait_timeout_ms: int
) -> bytes:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(java_script_enabled=True)
        page = context.new_page()

        try:
            page.set_content(html, wait_until="networkidle", timeout=wait_timeout_ms)

            # This line forces all margins to be zero in the HTML's
            # @page context, guaranteeing that the margins from page.pdf()
            # are the only ones applied.
            page.add_style_tag(content='''
                @page {
                    margin-top: 0 !important;
                    margin-right: 0 !important;
                    margin-bottom: 0 !important;
                    margin-left: 0 !important;
                    padding: 0 !important;
                }
            ''')
            #

            pdf_args = {
                "print_background": print_background,
                "landscape": landscape,
                "scale": scale,
                "margin": margins,
                "display_header_footer": bool(header_template or footer_template),
                "prefer_css_page_size": prefer_css_page_size
            }

            if header_template:
                pdf_args["header_template"] = header_template
            if footer_template:
                pdf_args["footer_template"] = footer_template

            if format_name:
                pdf_args["format"] = format_name
            else:
                if width:
                    pdf_args["width"] = width
                if height:
                    pdf_args["height"] = height

            buf = page.pdf(**pdf_args)
            return buf

        finally:
            try:
                page.close()
                context.close()
                browser.close()
            except Exception:
                pass


# ---------- UI ----------

st.set_page_config(page_title=APP_TITLE, page_icon="🖨️", layout="wide")
st.title(APP_TITLE)
st.caption("Pixel-accurate export with @media print / @page support. Hyperlinks remain clickable in the PDF.")

with st.sidebar:
    st.header("Options")

    paper_choice = st.selectbox(
        "Paper size",
        ["A4", "Letter", "Legal", "Tabloid", "Custom"],
        index=0,
        help="Choose a preset or pick Custom to set width/height."
    )

    col_w, col_h = st.columns(2)
    custom_w = col_w.text_input("Custom width (e.g., 210mm or 8.5in)",
                                value="210mm" if paper_choice == "Custom" else "", disabled=(paper_choice != "Custom"))
    custom_h = col_h.text_input("Custom height (e.g., 297mm or 11in)",
                                value="297mm" if paper_choice == "Custom" else "", disabled=(paper_choice != "Custom"))

    st.markdown("**Margins** (accepts units like `mm`, `in`, `px`; e.g., `15mm`)")
    mcol1, mcol2, mcol3, mcol4 = st.columns(4)
    m_top = mcol1.text_input("Top", value="15mm")
    m_right = mcol2.text_input("Right", value="15mm")
    m_bottom = mcol3.text_input("Bottom", value="15mm")
    m_left = mcol4.text_input("Left", value="15mm")

    landscape = st.checkbox("Landscape", value=False)
    print_background = st.checkbox("Print background graphics", value=True)
    prefer_css_page_size = st.checkbox("Prefer CSS @page size", value=True,
                                       help="If your HTML uses `@page { size: ... }`, this will honor it.")
    scale = st.slider("Scale", min_value=0.1, max_value=2.0, value=1.0, step=0.05,
                      help="Zoom the page before printing (useful to fit more/less per page).")

    st.markdown("**Header/Footer (optional HTML)**")
    header_template = st.text_area(
        "Header HTML",
        value="",
        height=80
    )
    footer_template = st.text_area(
        "Footer HTML",
        value="",
        height=80
    )
    st.caption("Tip: Chromium fills `.pageNumber`, `.totalPages`, `.date`, `.title`. Keep inline CSS simple.")

    wait_timeout_ms = st.number_input("Load timeout (ms)", min_value=1000, max_value=120000, value=30000, step=1000)

st.subheader("Upload")
st.write("Upload either a single **HTML file** _or_ a **ZIP** containing `index.html` and assets (CSS, images, fonts).")

uploaded = st.file_uploader("Choose HTML or ZIP", type=["html", "htm", "zip"])
base_url_manual = st.text_input(
    "Optional base URL (for resolving relative paths when using a single HTML file)",
    placeholder="https://example.com/articles/",
    help="If your HTML references relative assets (CSS/images), provide a base URL. For ZIP uploads, this is not required."
)

col_a, col_b = st.columns([1, 2])

with col_a:
    generate = st.button("Generate PDF", type="primary", use_container_width=True)

with col_b:
    st.write("")

st.divider()

# ---------- Generate PDF ----------

if generate:
    if not uploaded:
        st.error("Please upload an HTML file or a ZIP.")
        st.stop()

    html_text: Optional[str] = None
    base_url: Optional[str] = None
    cleanup_paths = []

    try:
        suffix = Path(uploaded.name).suffix.lower()

        if suffix == ".zip":
            tmp_zip = Path(tempfile.mkstemp(prefix="html2pdf_", suffix=".zip")[1])
            with open(tmp_zip, "wb") as f:
                f.write(uploaded.read())
            cleanup_paths.append(tmp_zip)

            entry = find_html_in_zip(tmp_zip)
            if not entry or not entry.exists():
                st.error("No HTML file found inside the ZIP (looked for index.html or any .html).")
                st.stop()

            html_text = entry.read_text(encoding="utf-8", errors="ignore")
            base_url = entry.parent.as_uri()

        else:
            html_bytes = uploaded.read()
            try:
                html_text = html_bytes.decode("utf-8")
            except UnicodeDecodeError:
                html_text = html_bytes.decode("latin-1", errors="ignore")

            base_url = base_url_manual.strip() or None

        format_name, width, height = normalize_paper(paper_choice, custom_w, custom_h)
        margins = {"top": m_top, "right": m_right, "bottom": m_bottom, "left": m_left}

        with st.spinner("Rendering PDF with Chromium..."):
            try:
                pdf_bytes = render_pdf(
                    html=html_text,
                    base_url=base_url,
                    format_name=format_name,
                    width=width,
                    height=height,
                    margins=margins,
                    landscape=landscape,
                    print_background=print_background,
                    scale=scale,
                    header_template=header_template.strip() or None,
                    footer_template=footer_template.strip() or None,
                    prefer_css_page_size=prefer_css_page_size,
                    wait_timeout_ms=int(wait_timeout_ms),
                )
            except PWTimeoutError:
                st.error("Timed out while loading content. Increase the timeout or check network/asset paths.")
                st.stop()
            except Exception as e:
                st.exception(e)
                st.stop()

        fname_base = Path(uploaded.name).stem or "export"
        st.success("PDF generated successfully. Hyperlinks remain clickable 🎉")

        col_preview_html, col_preview_pdf = st.columns(2)

        with col_preview_html:
            st.subheader("HTML Preview")
            if suffix == ".zip":
                st.info("HTML preview is not available for ZIP files due to asset dependencies.")
            else:
                st.components.v1.html(html_text, height=500, scrolling=True)

        with col_preview_pdf:
            st.subheader("PDF Preview")
            base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="500" type="application/pdf"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)

        st.download_button(
            label="⬇️ Download PDF",
            data=pdf_bytes,
            file_name=f"{fname_base}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
        st.caption(
            "If links don’t appear clickable in your viewer, try opening in a dedicated PDF reader (they’re embedded).")

    finally:
        for p in cleanup_paths:
            try:
                os.remove(p)
            except Exception:
                pass

# ---------- Help / Tips ----------
with st.expander("Tips for perfect fidelity & links"):
    st.markdown("""
- **Keep links standard**: `<a href="https://...">Label</a>` — Chromium embeds them in the PDF automatically.
- Add print CSS in your HTML:
  ```css
  @page { size: A4; margin: 15mm; } /* honored when 'Prefer CSS @page size' is on */
  @media print {
    a { text-decoration: underline; }        /* keep visible */
    img, svg, figure, .card { break-inside: avoid; }
    h1, h2, h3 { break-after: avoid; }
  }
Fonts: self-host or include via @font-face or data-URIs so they embed in the PDF.

Assets: for single-file uploads, set Base URL if you use relative paths. For many files, upload a ZIP with index.html.

Async content: this app waits for networkidle so SPAs usually render correctly before export.
""")
