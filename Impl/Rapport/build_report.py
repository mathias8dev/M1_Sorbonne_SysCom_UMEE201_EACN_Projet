"""
build_report.py
Builds the Session 1 lab report (.docx) directly with python-docx.
LaTeX-style equations are emitted as native Word OMML so that they remain
editable in Word's equation editor.
"""

from pathlib import Path
from docx import Document
from docx.shared import Cm, Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn, nsmap
from lxml import etree

ROOT          = Path(__file__).resolve().parent.parent          # .../Impl
SCREENSHOTS   = ROOT / "Screen Shots"
OUT_PATH      = Path(__file__).resolve().parent / "rapport_session1.docx"

OMML_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
W_NS    = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


# ---------------------------------------------------------------------------
# Equation helpers — emit raw OMML
# ---------------------------------------------------------------------------

def _omml(xml):
    """Parse an OMML XML fragment and return an lxml Element."""
    return etree.fromstring(xml)


def _wrap_inline(inner):
    return f'<m:oMath xmlns:m="{OMML_NS}">{inner}</m:oMath>'


def _wrap_display(inner):
    return (
        f'<m:oMathPara xmlns:m="{OMML_NS}">'
        f'<m:oMathParaPr><m:jc m:val="center"/></m:oMathParaPr>'
        f'<m:oMath>{inner}</m:oMath>'
        f'</m:oMathPara>'
    )


def add_inline_math(paragraph, omml_inner):
    """Append an inline equation (m:oMath) at the end of a paragraph."""
    paragraph._p.append(_omml(_wrap_inline(omml_inner)))


def add_display_math(doc, omml_inner):
    """Add a centered display equation as a new paragraph."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p._p.append(_omml(_wrap_display(omml_inner)))
    return p


# OMML primitives ------------------------------------------------------------

def m_run(text, italic=True):
    """A simple math run.  By default text is italicised (variable style)."""
    if italic:
        return f"<m:r><m:t xml:space=\"preserve\">{text}</m:t></m:r>"
    return (
        f"<m:r><m:rPr><m:sty m:val=\"p\"/></m:rPr>"
        f"<m:t xml:space=\"preserve\">{text}</m:t></m:r>"
    )


def m_text(text):
    """Upright math text (units, function names, plain digits)."""
    return m_run(text, italic=False)


def m_sub(base, sub):
    return (
        f"<m:sSub><m:e>{base}</m:e>"
        f"<m:sub>{sub}</m:sub></m:sSub>"
    )


def m_sup(base, sup):
    return (
        f"<m:sSup><m:e>{base}</m:e>"
        f"<m:sup>{sup}</m:sup></m:sSup>"
    )


def m_frac(num, den):
    return (
        f"<m:f><m:num>{num}</m:num>"
        f"<m:den>{den}</m:den></m:f>"
    )


# Variables ------------------------------------------------------------------

VAR_RS    = m_sub(m_run("R"), m_run("s"))
VAR_FS    = m_sub(m_run("f"), m_run("s"))
VAR_FC    = m_sub(m_run("f"), m_run("c"))
VAR_F1    = m_sub(m_run("f"), m_text("1"))
VAR_F2    = m_sub(m_run("f"), m_text("2"))
VAR_BETA  = m_run("β")
VAR_GTX   = m_sub(m_run("g"), m_text("tx"))
VAR_NB    = m_sub(m_run("N"), m_run("b"))
VAR_BW    = m_text("BW")


# ---------------------------------------------------------------------------
# Document content
# ---------------------------------------------------------------------------

def set_default_font(doc):
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)


def add_title(doc, title, subtitle=None):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(title)
    r.bold = True
    r.font.size = Pt(20)
    if subtitle:
        p2 = doc.add_paragraph()
        p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r2 = p2.add_run(subtitle)
        r2.italic = True
        r2.font.size = Pt(13)


def add_h(doc, text, level=1):
    doc.add_heading(text, level=level)


def add_p(doc, text=None):
    return doc.add_paragraph(text or "")


def add_var(paragraph, base, sub=None, sup=None):
    """Inline variable formatted as italic with subscript/superscript runs."""
    r = paragraph.add_run(base)
    r.italic = True
    if sub:
        rs = paragraph.add_run(sub)
        rs.italic = True
        rs.font.subscript = True
    if sup:
        rsup = paragraph.add_run(sup)
        rsup.italic = True
        rsup.font.superscript = True


def add_image(doc, rel_path, caption=None, width_cm=14):
    full = ROOT / rel_path
    if not full.exists():
        # also try relative to script dir
        full = (Path(__file__).resolve().parent.parent / rel_path)
    doc.add_picture(str(full), width=Cm(width_cm))
    last = doc.paragraphs[-1]
    last.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if caption:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(f"Figure : {caption}")
        r.italic = True
        r.font.size = Pt(9)


def add_table(doc, headers, rows, header_bold=True):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Light Grid Accent 1"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = table.rows[0].cells
    for i, h in enumerate(headers):
        hdr[i].text = h
        if header_bold:
            for run in hdr[i].paragraphs[0].runs:
                run.bold = True
    for ri, row in enumerate(rows, start=1):
        cells = table.rows[ri].cells
        for ci, val in enumerate(row):
            cells[ci].text = str(val)
    return table


# ---------------------------------------------------------------------------
# Build the report
# ---------------------------------------------------------------------------

def build():
    doc = Document()
    set_default_font(doc)

    # -----------------------------------------------------------------------
    # Title block
    # -----------------------------------------------------------------------
    add_title(
        doc,
        "UM4EE201 — EACN — Wireless Communications",
        "Compte-rendu de la Session 1 : génération de la forme d'onde TX",
    )
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run("Mathias KALIPE — 5 mai 2026").italic = True
    doc.add_paragraph()

    # -----------------------------------------------------------------------
    # 1. Objectif
    # -----------------------------------------------------------------------
    add_h(doc, "1. Objectif et matériel", 1)
    add_p(doc,
        "L'objectif de la première session est d'implémenter, sur du matériel "
        "réel, la chaîne d'émission développée dans les LiveScripts de "
        "simulation. Le banc de mesure se compose de :")
    for item in (
        "un USRP Ettus B210 (numéro de série 3241A58),",
        "un analyseur de spectre R&S (mode Spectrum, RBW 30 kHz, VBW 3 MHz par défaut),",
        "un PC sous MATLAB R2025b avec les drivers usrpradio.mlpkginstall et la Communications Toolbox.",
    ):
        doc.add_paragraph(item, style="List Bullet")
    add_p(doc,
        "La sortie TX1 du B210 est connectée à l'analyseur ; la sortie TX2 est "
        "terminée sur charge 50 Ω pour éviter toute réflexion susceptible "
        "d'endommager l'étage de sortie.")

    # -----------------------------------------------------------------------
    # 2. Chaîne d'émission
    # -----------------------------------------------------------------------
    add_h(doc, "2. Chaîne d'émission", 1)
    add_p(doc,
        "Le script projet.m génère un signal de modulation 16-QAM avec mise "
        "en forme par filtre Root Raised Cosine (RRC), puis pilote l'USRP en "
        "boucle infinie. Les étapes principales :")
    for item in (
        "génération aléatoire de N_b = N_d · log₂ M bits (M = 16, N_d = 1000, N_p = 10),",
        "mapping QAM,",
        "concaténation [symb_pilot ; symb_data],",
        "convolution avec la réponse impulsionnelle RRC,",
        "normalisation dans [-1 ; +1] pour éviter la saturation du DAC,",
        "envoi vers l'USRP via comm.SDRuTransmitter.",
    ):
        doc.add_paragraph(item, style="List Number")

    add_h(doc, "2.1. Bande passante du signal", 2)
    p = add_p(doc,
        "Pour un filtre RRC de débit symbole ")
    add_var(p, "R", sub="s")
    p.add_run(" et de roll-off ")
    p.add_run("β").italic = True
    p.add_run(", la bande occupée en bande de base est :")

    add_display_math(doc,
        VAR_BW + m_text(" = ") + VAR_RS + m_text(" (1 + ") + VAR_BETA + m_text(")")
    )

    p = add_p(doc, "Avec ")
    add_var(p, "R", sub="s")
    p.add_run(" = 5 MHz et ")
    p.add_run("β").italic = True
    p.add_run(" = 0,5, on obtient ")
    p.add_run("BW").italic = False
    p.add_run(" = 7,5 MHz.")

    add_h(doc, "2.2. Fréquence d'échantillonnage", 2)
    p = add_p(doc,
        "La fréquence d'échantillonnage doit satisfaire le critère de Nyquist "
        "tout en respectant la limite de l'AD9361 :")
    add_display_math(doc,
        VAR_FS + m_text(" = sps · ") + VAR_RS + m_text("    avec   ") +
        VAR_FS + m_text(" ∈ [5 ; 56] MHz")
    )
    p = add_p(doc, "Avec sps = 2 et ")
    add_var(p, "R", sub="s")
    p.add_run(" = 5 MHz, ")
    add_var(p, "f", sub="s")
    p.add_run(" = 10 MHz, ce qui rentre confortablement dans la fenêtre du B210.")

    # -----------------------------------------------------------------------
    # 3. Tâche 1 — span
    # -----------------------------------------------------------------------
    add_h(doc, "3. Tâche 1 — Influence du span du filtre RRC", 1)
    add_p(doc,
        "Le span est la durée du filtre RRC, exprimée en nombre de périodes "
        "symbole. Il définit la troncature appliquée à la réponse "
        "impulsionnelle théorique (qui est infinie). On compare ici quatre "
        "valeurs : 4, 16, 32 et 64.")

    add_table(
        doc,
        headers=["span", "Longueur du filtre", "Observation principale"],
        rows=[
            ["4",  "9",   "Lobes secondaires nettement visibles, plancher remonté"],
            ["16", "33",  "Lobes atténués, transition marquée"],
            ["32", "65",  "Transition abrupte, plancher propre"],
            ["64", "129", "Quasi identique à span = 32, gain marginal"],
        ],
    )
    doc.add_paragraph()

    add_image(doc, "spectrum_sr5MHz_span4_ro0.5_sps2_05052026_080719.png",
              "Spectre baseband Matlab — span = 4")
    add_image(doc, "spectrum_sr5MHz_span16_ro0.5_sps2_05052026_080633.png",
              "Spectre baseband Matlab — span = 16")
    add_image(doc, "spectrum_sr5MHz_span32_ro0.5_sps2_05052026_080805.png",
              "Spectre baseband Matlab — span = 32")
    add_image(doc, "Screen Shots/Measurement0106.png",
              "Spectre RF analyseur — premiers essais (Measurement 0106)")

    p = add_p(doc, "")
    p.add_run("Choix retenu pour la suite : ").bold = True
    p.add_run("span = 32. Au-delà, l'amélioration spectrale devient marginale "
              "alors que la longueur du signal augmente proportionnellement, "
              "ce qui rapproche de la limite de 30 500 échantillons par frame USRP.")

    # -----------------------------------------------------------------------
    # 4. Tâche 2 — roll-off
    # -----------------------------------------------------------------------
    add_h(doc, "4. Tâche 2 — Influence du roll-off β", 1)
    p = add_p(doc,
        "Le roll-off contrôle la largeur de la zone de transition du RRC. Sa "
        "valeur fait varier la bande occupée selon ")
    p.add_run("BW").italic = False
    p.add_run(" = ")
    add_var(p, "R", sub="s")
    p.add_run("(1 + β) :")

    add_display_math(doc,
        VAR_BETA + m_text(" ∈ {0,2 ; 0,4 ; 0,5 ; 0,6 ; 0,8 ; 1,0}  ⇒  ") +
        VAR_BW + m_text(" ∈ {6 ; 7 ; 7,5 ; 8 ; 9 ; 10} MHz")
    )

    add_image(doc, "spectrum_sr5MHz_span32_ro0.2_sps2_05052026_081804.png", "β = 0,2")
    add_image(doc, "spectrum_sr5MHz_span32_ro0.5_sps2_05052026_081326.png", "β = 0,5")
    add_image(doc, "spectrum_sr5MHz_span32_ro1_sps2_05052026_082253.png",   "β = 1,0")

    add_p(doc, "Observations.").runs[0].bold = True
    bullets = [
        "La largeur de la zone plate (f₁ = (1−β) R_s/2) diminue quand β croît : à β = 1, le sommet plat disparaît.",
        "La transition f₁ → f₂ s'élargit avec β ; à β = 0,2 elle est presque verticale, à β = 1 l'allure devient cosinusoïdale sur toute la bande.",
        "L'efficacité spectrale est maximale à β → 0 (BW → R_s), au prix d'une réponse impulsionnelle qui décroît lentement et nécessite un span plus grand.",
    ]
    for b in bullets:
        doc.add_paragraph(b, style="List Bullet")

    p = add_p(doc, "")
    p.add_run("Choix retenu : ").bold = True
    p.add_run("β = 0,5. Compromis canonique entre étalement spectral et simplicité de filtrage.")

    # -----------------------------------------------------------------------
    # 5. Tâche 3 — débit symbole
    # -----------------------------------------------------------------------
    add_h(doc, "5. Tâche 3 — Influence du débit symbole R_s", 1)
    add_p(doc,
        "Le débit symbole est balayé entre 1 MHz et 30 MHz "
        "(paramètres fixés : β = 0,5, span = 16, sps = 2).")

    add_table(
        doc,
        headers=["R_s (MHz)", "BW (MHz)", "f_s (MHz)", "Statut B210"],
        rows=[
            ["1",   "1,5",  "2",  "f_s < 5 MHz, hors specs"],
            ["5",   "7,5",  "10", "OK"],
            ["10",  "15",   "20", "OK"],
            ["15",  "22,5", "30", "OK"],
            ["20",  "30",   "40", "OK"],
            ["25",  "37,5", "50", "OK"],
            ["28",  "42",   "56", "À la limite"],
            ["30",  "45",   "60", "Au-delà du MasterClockRate max (56 MHz)"],
        ],
    )
    doc.add_paragraph()

    add_image(doc, "spectrum_sr1MHz_span16_ro0.5_sps2_05052026_083128.png",  "R_s = 1 MHz")
    add_image(doc, "spectrum_sr10MHz_span16_ro0.5_sps2_05052026_083254.png", "R_s = 10 MHz")
    add_image(doc, "spectrum_sr20MHz_span16_ro0.5_sps2_05052026_083451.png", "R_s = 20 MHz")
    add_image(doc, "spectrum_sr30MHz_span16_ro0.5_sps2_05052026_083703.png", "R_s = 30 MHz — sortie des specs")

    add_p(doc, "Observations.").runs[0].bold = True
    bullets = [
        "Sur l'analyseur, la largeur du lobe principal varie linéairement avec R_s, conformément à BW = R_s (1+β).",
        "À puissance émise constante, la densité spectrale de puissance diminue à mesure que R_s augmente : la même puissance totale est étalée sur une bande plus large.",
        "À partir de R_s ≈ 28 MHz, l'amplitude observée chute brutalement vers le plancher de bruit. À R_s = 30 MHz le signal est quasi inexistant.",
    ]
    for b in bullets:
        doc.add_paragraph(b, style="List Bullet")

    add_p(doc, "Trois facteurs cumulés expliquent ce phénomène :")
    for b in (
        "f_s = 60 MHz dépasse le MasterClockRate maximum du B210 (56 MHz),",
        "la bande propre du frontend RF (AD9361) est de l'ordre de 40 MHz — au-delà, la chaîne analogique atténue fortement,",
        "avec InterpolationFactor = 1, on ne bénéficie pas des étages de filtrage interpolant internes du DAC.",
    ):
        doc.add_paragraph(b, style="List Number")

    p = add_p(doc, "")
    p.add_run("Conclusion : ").bold = True
    p.add_run("le débit symbole maximal exploitable sur ce banc est R_s ≈ 28 MHz.")

    # -----------------------------------------------------------------------
    # 6. Tâche 4 — caractérisation gain
    # -----------------------------------------------------------------------
    add_h(doc, "6. Tâche 4 — Caractérisation de la puissance USRP", 1)
    add_p(doc, "Configuration imposée par l'énoncé :")
    add_display_math(doc,
        VAR_NB + m_text(" = ") + m_sup(m_text("10"), m_text("4")) +
        m_text(" ,   ") +
        m_sub(m_text("log"), m_text("2")) + m_run(" M") + m_text(" = 4 ,   ") +
        VAR_BETA + m_text(" = 0,5 ,   ") +
        VAR_RS + m_text(" = 5 MHz ,   span = 32 ,   ") +
        VAR_FC + m_text(" = 900 MHz")
    )
    add_p(doc,
        "Le gain de l'étage TX du B210 est balayé de 10 dB à 89,5 dB ; pour "
        "chaque valeur, la puissance dans le canal est mesurée sur l'analyseur "
        "via la fonction Channel Power (intégration sur BW = 7,5 MHz).")

    add_p(doc, "Tableau de mesure").runs[0].bold = True
    add_table(
        doc,
        headers=["g_tx (dB)", "10", "20", "30", "40", "50", "60", "70", "80", "89,5"],
        rows=[
            ["P (dBm)",        "−58,4", "−47,9", "−37,7", "−27,5", "−16,9", "−7,5", "−4,1", "−4,7", "−4,7"],
            ["ΔP / 10 dB",     "—",     "+10,5", "+10,2", "+10,2", "+10,6", "+9,4", "+3,4", "−0,6", "0"],
        ],
    )
    doc.add_paragraph()

    add_image(doc, "Screen Shots/Capture d’écran 2026-05-05 094632.png",
              "Tableau de mesure — caractérisation g_tx vs puissance canal")

    add_p(doc, "Analyse.").runs[0].bold = True
    add_p(doc, "Trois régimes apparaissent nettement :")

    p = add_p(doc, "")
    p.add_run("Zone linéaire (g_tx ∈ [10 ; 60] dB) : ").bold = True
    p.add_run("la puissance de sortie suit le gain demandé avec un facteur de "
              "proportionnalité de 1 dB/dB (les écarts ΔP varient entre +9,4 "
              "et +10,6 dB). Comportement attendu pour un amplificateur "
              "travaillant sous son point de compression à 1 dB.")

    p = add_p(doc, "")
    p.add_run("Zone de compression (g_tx ∈ [60 ; 70] dB) : ").bold = True
    p.add_run("seulement +3,4 dB d'augmentation pour un pas de 10 dB demandé. "
              "L'étage de sortie entre dans son régime non linéaire.")

    p = add_p(doc, "")
    p.add_run("Zone de saturation (g_tx ≥ 70 dB) : ").bold = True
    p.add_run("la puissance de sortie plafonne à ≈ −4,5 dBm, voire diminue "
              "légèrement à 80 dB (−4,7 dBm) — phénomène classique de gain "
              "compression au-delà du point de compression à 3 dB.")

    add_p(doc, "Effets sur le spectre observé.").runs[0].bold = True
    for b in (
        "Dans la zone linéaire, le spectre conserve sa forme RRC.",
        "Dans la zone de compression, on voit apparaître un élargissement spectral (regrowth) : la non-linéarité de l'étage RF crée des produits d'intermodulation hors de la bande utile, le plancher hors bande remonte de plusieurs dB.",
        "En saturation, le signal ressemble à un signal écrêté : étalement spectral marqué et perte de la mise en forme RRC.",
    ):
        doc.add_paragraph(b, style="List Bullet")

    p = add_p(doc, "")
    p.add_run("Recommandation pratique : ").bold = True
    p.add_run("opérer à g_tx ≤ 60 dB pour préserver la qualité spectrale.")

    # -----------------------------------------------------------------------
    # 7. Tâche 5 — fc = 200 MHz
    # -----------------------------------------------------------------------
    add_h(doc, "7. Tâche 5 — Fréquence porteuse à 200 MHz", 1)
    add_p(doc,
        "Réglages : f_c = 200 MHz, g_tx = 80 dB, analyseur sur la plage "
        "0 — 1 GHz.")
    add_image(doc, "Screen Shots/Measurement0137.png",
              "Spectre 0 — 1 GHz avec f_c = 200 MHz")

    add_p(doc, "Observations.").runs[0].bold = True
    add_p(doc, "Sur la trace, on distingue trois raies :")
    for b in (
        "une raie à environ 200 MHz — la fondamentale, à la fréquence porteuse demandée,",
        "une raie à environ 600 MHz — le 3ᵉ harmonique (3 f_c),",
        "une raie à environ 1 GHz — le 5ᵉ harmonique (5 f_c).",
    ):
        doc.add_paragraph(b, style="List Bullet")

    add_p(doc, "Explication.").runs[0].bold = True
    add_p(doc,
        "L'étage de sortie de l'USRP en régime fortement non linéaire (ici "
        "g_tx = 80 dB, dans la zone de saturation identifiée à la T4) produit "
        "des distorsions harmoniques :")

    add_display_math(doc,
        m_run("y") + m_text("(") + m_run("t") + m_text(") = ") +
        m_sub(m_run("a"), m_text("1")) + m_run(" x") + m_text("(") + m_run("t") + m_text(") + ") +
        m_sub(m_run("a"), m_text("2")) + m_sup(m_run(" x"), m_text("2")) + m_text("(") + m_run("t") + m_text(") + ") +
        m_sub(m_run("a"), m_text("3")) + m_sup(m_run(" x"), m_text("3")) + m_text("(") + m_run("t") + m_text(") + …")
    )

    add_p(doc,
        "Pour une porteuse x(t) = cos(2π f_c t), le terme cubique génère une "
        "composante à 3 f_c, le terme d'ordre 5 une composante à 5 f_c, etc. "
        "Les harmoniques paires (2 f_c, 4 f_c) sont nettement plus faibles "
        "car :")
    for b in (
        "l'amplificateur est nominalement push-pull (symétrique), ce qui supprime théoriquement les harmoniques paires,",
        "le filtre passe-bande de sortie atténue davantage les multiples non utilisés du fondamental.",
    ):
        doc.add_paragraph(b, style="List Bullet")

    add_p(doc,
        "À f_c basse comme 200 MHz, les harmoniques d'ordre élevé tombent dans "
        "la plage de fréquences observable de l'analyseur, ce qui les rend "
        "visibles. À f_c = 900 MHz, les harmoniques seraient au-delà de "
        "2,7 GHz et donc invisibles dans la plage 0 — 1 GHz.")

    p = add_p(doc, "")
    p.add_run("Conséquence en exploitation : ").bold = True
    p.add_run("pour respecter les normes spectrales (ARCEP, FCC), il faut soit "
              "travailler à plus faible g_tx, soit insérer un filtre passe-bas "
              "après la sortie TX.")

    # -----------------------------------------------------------------------
    # 8. Synthèse
    # -----------------------------------------------------------------------
    add_h(doc, "8. Synthèse et choix retenus", 1)
    add_table(
        doc,
        headers=["Paramètre", "Valeur retenue", "Justification"],
        rows=[
            ["Modulation", "16-QAM", "Imposée par l'énoncé"],
            ["span",       "32",    "Lobes hors bande < −40 dB, gain marginal au-delà"],
            ["β",          "0,5",   "Compromis efficacité spectrale / longueur du filtre"],
            ["R_s",        "≤ 28 MHz", "Limite imposée par f_s ≤ 56 MHz du B210"],
            ["sps",        "2",     "Minimum Nyquist pour un RRC"],
            ["f_c",        "≥ 500 MHz", "Évite les harmoniques visibles dans la bande utile"],
            ["g_tx",       "≤ 60 dB", "Reste dans la zone linéaire de l'étage de sortie"],
        ],
    )

    # -----------------------------------------------------------------------
    # 9. Conclusion
    # -----------------------------------------------------------------------
    add_h(doc, "9. Conclusion", 1)
    add_p(doc,
        "Cette première session a permis de valider la chaîne TX et de "
        "caractériser le comportement réel du matériel B210. Les principaux "
        "enseignements sont :")
    for b in (
        "un filtre RRC de longueur span = 32 offre une atténuation hors bande satisfaisante sans surcoût significatif sur la longueur du frame ;",
        "le choix d'un roll-off β = 0,5 constitue un bon compromis entre étalement spectral et compacité temporelle ;",
        "le débit symbole R_s est borné par les capacités matérielles du B210 (f_s ≤ 56 MHz) et non par la simulation ;",
        "l'amplificateur de sortie se comporte linéairement entre g_tx = 10 et 60 dB ; au-delà, on entre en compression puis en saturation, ce qui dégrade le spectre par spectral regrowth ;",
        "les harmoniques créées par la non-linéarité sont visibles à basse fréquence porteuse et imposent un filtrage ou un fonctionnement à gain modéré pour respecter les normes spectrales.",
    ):
        doc.add_paragraph(b, style="List Bullet")

    add_p(doc,
        "Ces résultats fixent les paramètres pour la Session 2, qui consistera "
        "à mettre en place une chaîne TX/RX complète avec synchronisation, "
        "estimation de canal par pilotes et calcul du BER.")

    # -----------------------------------------------------------------------
    # Save
    # -----------------------------------------------------------------------
    doc.save(OUT_PATH)
    print(f"Saved: {OUT_PATH}")


if __name__ == "__main__":
    build()
