"""Generates presentation/Urban_Data_Tender_Presentation.odp from the
content below. Re-run after editing SLIDES to regenerate the file --
the .odp itself is a build artifact, this script is the source of truth.
"""
from odf.opendocument import OpenDocumentPresentation
from odf.style import (
    Style, MasterPage, PageLayout, PageLayoutProperties,
    TextProperties, ParagraphProperties, GraphicProperties,
    ListLevelProperties,
)
from odf.draw import Page, Frame, TextBox
from odf.text import P, List, ListItem, ListStyle, ListLevelStyleBullet, LineBreak

PAGE_W, PAGE_H = "33.87cm", "19.05cm"  # 16:9 widescreen
MARGIN_X = "1.3cm"
CONTENT_W = "31.27cm"

ACCENT = "#1f4e79"
DARK = "#1a1a1a"
GREY = "#555555"


def build():
    doc = OpenDocumentPresentation()

    pagelayout = PageLayout(name="Layout")
    doc.automaticstyles.addElement(pagelayout)
    pagelayout.addElement(PageLayoutProperties(
        margin="0cm", pagewidth=PAGE_W, pageheight=PAGE_H,
        printorientation="landscape",
    ))

    masterpage = MasterPage(name="Master", pagelayoutname=pagelayout)
    doc.masterstyles.addElement(masterpage)

    # ---- reusable frame/text styles -------------------------------------
    def add_style(name, fontsize, bold=False, color=DARK, align=None,
                  font="Calibri"):
        st = Style(name=name, family="presentation")
        st.addElement(GraphicProperties(fill="none", stroke="none"))
        pp_kwargs = {}
        if align:
            pp_kwargs["textalign"] = align
        st.addElement(ParagraphProperties(**pp_kwargs) if pp_kwargs else ParagraphProperties())
        st.addElement(TextProperties(
            fontsize=fontsize, fontweight="bold" if bold else "normal",
            color=color, fontfamily=font,
        ))
        doc.styles.addElement(st)
        return st

    kicker_style = add_style("Kicker", "16pt", bold=True, color=ACCENT)
    title_style = add_style("TitleBig", "40pt", bold=True, color=DARK)
    subtitle_style = add_style("Subtitle", "20pt", color=GREY)
    heading_style = add_style("Heading", "28pt", bold=True, color=ACCENT)
    body_style = add_style("Body", "18pt", color=DARK)
    mono_style = add_style("Mono", "14pt", color=DARK, font="Consolas")
    footer_style = add_style("Footer", "11pt", color=GREY)

    # bullet list style
    liststyle = ListStyle(name="BulletList")
    for level in range(1, 4):
        bullet = ListLevelStyleBullet(level=str(level), bulletchar="•" if level == 1 else "–")
        bullet.addElement(ListLevelProperties(spacebefore=f"{0.6 * level}cm", minlabelwidth="0.6cm"))
        liststyle.addElement(bullet)
    doc.styles.addElement(liststyle)

    def new_page():
        page = Page(masterpagename=masterpage)
        doc.presentation.addElement(page)
        return page

    def add_frame(page, style, x, y, w, h):
        frame = Frame(stylename=style, width=w, height=h, x=x, y=y)
        page.addElement(frame)
        box = TextBox()
        frame.addElement(box)
        return box

    def footer(page, text):
        box = add_frame(page, footer_style, "1.3cm", "18.3cm", CONTENT_W, "0.6cm")
        box.addElement(P(stylename=footer_style, text=text))

    def title_slide(kicker, title, subtitle, note):
        page = new_page()
        k = add_frame(page, kicker_style, MARGIN_X, "5.8cm", CONTENT_W, "1cm")
        k.addElement(P(stylename=kicker_style, text=kicker))
        t = add_frame(page, title_style, MARGIN_X, "6.9cm", CONTENT_W, "3cm")
        t.addElement(P(stylename=title_style, text=title))
        s = add_frame(page, subtitle_style, MARGIN_X, "9.8cm", CONTENT_W, "2cm")
        s.addElement(P(stylename=subtitle_style, text=subtitle))
        if note:
            footer(page, note)
        return page

    def bullets_slide(heading, bullets, note=None):
        """bullets: list of str (top-level) or (str, [sub-bullets])."""
        page = new_page()
        h = add_frame(page, heading_style, MARGIN_X, "1.1cm", CONTENT_W, "1.6cm")
        h.addElement(P(stylename=heading_style, text=heading))

        body = add_frame(page, body_style, MARGIN_X, "3.1cm", CONTENT_W, "14.5cm")
        lst = List(stylename=liststyle)
        body.addElement(lst)
        for item in bullets:
            if isinstance(item, tuple):
                text, subs = item
            else:
                text, subs = item, []
            li = ListItem()
            lst.addElement(li)
            li.addElement(P(stylename=body_style, text=text))
            if subs:
                sublst = List(stylename=liststyle)
                li.addElement(sublst)
                for sub in subs:
                    sli = ListItem()
                    sublst.addElement(sli)
                    sli.addElement(P(stylename=body_style, text=sub))
        if note:
            footer(page, note)
        return page

    def mono_slide(heading, lines, note=None):
        page = new_page()
        h = add_frame(page, heading_style, MARGIN_X, "1.1cm", CONTENT_W, "1.6cm")
        h.addElement(P(stylename=heading_style, text=heading))
        body = add_frame(page, mono_style, MARGIN_X, "3.1cm", CONTENT_W, "14.5cm")
        for i, line in enumerate(lines):
            p = P(stylename=mono_style, text=line)
            body.addElement(p)
        if note:
            footer(page, note)
        return page

    def table_slide(heading, header_row, rows, note=None):
        widths = [max(len(str(r[c])) for r in [header_row] + rows) + 3 for c in range(len(header_row))]
        def fmt(row):
            return "".join(str(c).ljust(w) for c, w in zip(row, widths))
        lines = [fmt(header_row), fmt(["-" * (w - 2) for w in widths])] + [fmt(r) for r in rows]
        mono_slide(heading, lines, note=note)

    NOTE = "Urban Data — Ambient Sensing Platform — Tender Proposal"

    # ---- 1. Title ---------------------------------------------------------
    title_slide(
        "TENDER PROPOSAL",
        "Urban Data",
        "An Ambient, Multi-Sensor Situational Awareness Platform for Cities",
        "Prepared for: [Issuing Authority]   |   Date: [Date]   |   Contact: [Name / Email]",
    )

    # ---- 2. The Problem -----------------------------------------------------
    bullets_slide(
        "The Problem",
        [
            "Cities monitor incidents through disconnected, single-purpose systems — traffic cameras, 911 audio, seismic networks, RF spectrum monitors — that never talk to each other.",
            "Operators must manually correlate feeds across modalities under time pressure, which does not scale to city-wide, multi-domain events.",
            "Emerging risks — drone incursions, coordinated multi-site incidents, infrastructure attacks — require fusing signals across sensor types faster than manual triage allows.",
            "Existing situational-awareness products are typically single-modality, cloud-dependent, and vendor-locked — not built for edge deployment or open extension.",
        ],
        note=NOTE,
    )

    # ---- 3. The Solution ------------------------------------------------
    bullets_slide(
        "The Solution",
        [
            "Urban Data ingests five sensor modalities — photo, video, audio, RF, and seismic — into one fusion pipeline.",
            "Related signals across modalities are automatically grouped into a single incident, rather than left as isolated alerts.",
            "Each incident is resolved into three explainable outputs:",
            ("", ["Main Event — what is confirmed to be happening", "Prediction — what is likely to happen next", "Suggestion — recommended operator action"]),
            "Built so every “fake” demo module (analysis logic, agent reasoning) is a clean drop-in point for production ML — the architecture doesn't change post-funding, only what's behind each block.",
        ],
        note=NOTE,
    )

    # ---- 4. Architecture --------------------------------------------------
    mono_slide(
        "System Architecture",
        [
            "  Sensor Sources            AI Source        AI Events         Operator UI",
            "  (photo/video/audio/  ---> Analyzer   --->  Processor   ---> (map, event feed,",
            "   RF/seismic)               (per-source        (cross-source     agents panel)",
            "                              classify)          correlation)",
            "",
            "  Demo mode:      a Scenario Controller feeds the pipeline over ZMQ.",
            "  Production mode: real hardware sources replace the Scenario Controller —",
            "                    the rest of the pipeline and the UI are unchanged.",
            "",
            "  Built on GNU Radio (GRC) — an industry-standard, modular DSP / message-",
            "  passing framework — so the flowgraph itself is a visible, inspectable",
            "  proof of the architecture, not just a slide diagram.",
        ],
        note=NOTE,
    )

    # ---- 5. Sensor fusion ---------------------------------------------
    bullets_slide(
        "Multi-Modal Sensor Fusion",
        [
            ("Photo / Video — visual confirmation", ["drones, vehicles, crowds, infrastructure damage"]),
            ("Audio — acoustic signatures", ["engines, explosions, gunshots, distress calls"]),
            ("RF / FFT — radio-spectrum detection", ["drone control links, jamming, unregistered transmitters"]),
            ("Seismic — ground-vibration sensing", ["vehicle convoys, impacts, structural events"]),
            "Each modality detects independently; the Events Processor raises confidence and reduces false positives by requiring corroboration across modalities before escalating an incident.",
        ],
        note=NOTE,
    )

    # ---- 6. Explainability ----------------------------------------------
    bullets_slide(
        "Explainable, Auditable Reasoning",
        [
            "Every incident-level conclusion (Main Event / Prediction / Suggestion) is traceable back to the specific source events that produced it — not a black-box score.",
            "Roadmap: one independently-reasoning AI agent per active incident, briefed automatically the moment an incident is confirmed.",
            "Agent actions are exposed through a constrained tool-calling surface (dispatch a unit, issue an alert, lock a zone) — human operators stay in the loop for every action taken.",
            "Operators can chat directly with an incident's agent to question or override its reasoning before any action is taken.",
        ],
        note=NOTE,
    )

    # ---- 7. Demo scenarios -----------------------------------------------
    table_slide(
        "Demonstrated Scenarios",
        ["Scenario", "Events", "Content"],
        [
            ["Everyday Baseline", "8 (loop)", "Nothing-happening baseline across Toronto/Ottawa/Vancouver"],
            ["Small Events", "15", "Traffic stop, crash, ambulance, street fight, gas leak"],
            ["Flood", "20", "River flooding, water rescue, citizen radio reports"],
            ["Coordinated Civil Unrest", "17", "Simultaneous multi-city riots, pattern correlation"],
            ["Full-Scale Invasion", "45+", "Drone swarm to armored columns to urban incursion"],
        ],
        note=NOTE + "  —  demonstrates scaling from routine monitoring to major multi-domain crisis",
    )

    # ---- 8. Privacy --------------------------------------------------------
    bullets_slide(
        "Privacy by Design",
        [
            "Every source asset passes through a real (not simulated) face and license-plate anonymization stage before entering the pipeline.",
            "This is the one pipeline stage that is genuinely production-grade in the current build — privacy protection was treated as a first-class requirement, not an afterthought bolted on later.",
            "Downstream analysis, storage, and the operator UI only ever see anonymized media.",
        ],
        note=NOTE,
    )

    # ---- 9. Edge deployability --------------------------------------------
    bullets_slide(
        "Edge Deployability",
        [
            "Target hardware: NVIDIA Jetson Orin Nano / Xavier / Orin NX — field-portable, no continuous cloud dependency for core detection.",
            "Sensor-to-decision pipeline runs locally; only optional higher-level services (e.g. LLM reasoning) need network access, and even that can be swapped for a local model.",
            "Directly addresses distributed, field-deployable, low-connectivity requirements for municipal and public-safety infrastructure.",
        ],
        note=NOTE,
    )

    # ---- 10. Status ---------------------------------------------------
    table_slide(
        "Development Status",
        ["Step", "Status", "Output"],
        [
            ["1. Scenario data model", "Done", "scenarios/ — multi-scenario event library"],
            ["1.1 Scenario Controller", "Done", "Playback engine + live ZMQ feed"],
            ["2. AI Source Analyzer", "Logic done", "Per-source classification"],
            ["3. AI Events Processor", "Logic done", "Cross-source correlation"],
            ["4. Operator UI", "In progress", "Map, event feed, agents panel"],
            ["5. Media assets", "In progress", "Real + generated sensor media"],
            ["6. Live agents + MCP", "Planned", "Real LLM reasoning per incident"],
        ],
        note=NOTE,
    )

    # ---- 11. Why us --------------------------------------------------------
    bullets_slide(
        "Why Urban Data",
        [
            "Multi-domain fusion, where most alternatives are single-sensor.",
            "Explainable and auditable at every level — conclusions trace back to source evidence.",
            "Modular by construction: production ML slots into the same architecture already proven in this build, with no rework.",
            "Edge-ready from day one, not retrofitted for offline use later.",
            "Privacy safeguards built into the pipeline itself, ahead of the analysis stage.",
        ],
        note=NOTE,
    )

    # ---- 12. Ask -----------------------------------------------------------
    bullets_slide(
        "Proposal & Next Steps",
        [
            "Requesting funding to complete Phase 2 (full real + synthetic media integration across all sensor modalities) and Phase 3 (live per-incident AI agents, MCP tool integration, field pilot).",
            "Proposed timeline: [Timeline]",
            "Proposed budget: [Budget]",
            "Deliverable: a field-deployable pilot system ready for evaluation on live municipal sensor feeds.",
        ],
        note=NOTE,
    )

    # ---- 13. Contact ---------------------------------------------------
    title_slide(
        "THANK YOU",
        "Questions & Discussion",
        "[Name]  —  [Email]  —  [Phone]",
        NOTE,
    )

    out_path = "/home/radiolab9/github/urban_data/presentation/Urban_Data_Tender_Presentation.odp"
    doc.save(out_path)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    build()
