# HTML → PDF Exporter

**HTML → PDF Exporter** is a user-friendly web app that converts your HTML documents (or ZIP archives containing HTML and assets) into high-fidelity PDFs, preserving hyperlinks and print styling. Powered by Streamlit and Chromium via Playwright, it’s perfect for creating printable, shareable versions of web content, reports, documentation, or articles.

---

## Key Features

- **Upload HTML or ZIP**: Accepts single HTML files or ZIPs with `index.html` and all required assets (CSS, images, fonts).
- **Customizable Export**: Choose paper size (A4, Letter, Legal, Tabloid, or custom), margins, orientation, scale, and print background.
- **Header & Footer Support**: Add custom HTML for headers and footers in your PDF.
- **Print CSS Fidelity**: Honors your print styles and `@page` rules for pixel-perfect output.
- **Clickable Links**: Hyperlinks in your HTML remain interactive in the exported PDF.
- **Preview & Download**: Instantly preview both HTML and PDF before downloading.

---

## Who Is This For?

- **Writers & Publishers**: Export articles, documentation, or e-books for print or sharing.
- **Developers & Designers**: Test print layouts and CSS fidelity.
- **Educators & Students**: Create printable handouts or assignments from web content.

---

## How It Works

1. **Upload** your HTML file or ZIP archive.
2. **Configure** export options in the sidebar (paper size, margins, scale, etc.).
3. **Generate PDF** with a single click.
4. **Preview** your HTML and PDF side-by-side.
5. **Download** your PDF with preserved links and styling.

---

## Getting Started

### 1. Installation

#### Requirements

- Python 3.8+
- Linux, macOS, or Windows

#### Steps

```sh
# Clone the repository
git clone <your-repo-url>
cd html2pdf

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install streamlit playwright

# Install Chromium for Playwright
playwright install
```

### 2. Launch the App

```sh
streamlit run app.py
```

Open the provided local URL in your browser.

---

## Usage Tips

- **ZIP Uploads**: Include all assets and ensure `index.html` is present.
- **Base URL**: For single HTML files with relative paths, set the base URL for correct asset resolution.
- **Print CSS**: Use `@media print` and `@page` in your CSS for best results.
- **Fonts**: Self-host or embed fonts for accurate rendering.
- **Hyperlinks**: Standard `<a href="...">` links are preserved and clickable in the PDF.

---

## Troubleshooting

- **Timeouts**: Increase the “Load timeout” in the sidebar if your page loads slowly.
- **Missing Assets**: Use ZIP uploads for complex pages with many assets.
- **PDF Links Not Clickable**: Try opening the PDF in a dedicated reader (some browser viewers may not support interactive links).

---

## License & Credits

- Created by Raghav.
- Powered by [Streamlit](https://streamlit.io/) and [Playwright](https://playwright.dev/).
- Chromium is used for rendering and PDF export.

---

## Support & Feedback

For questions, feature requests, or bug reports, please open an issue or contact the author.

---

**Transform your HTML into beautiful, interactive PDFs—quickly and easily!**