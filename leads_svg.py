"""Electrode-placement diagrams (inline SVG) for the lead-placement pages.

Schematic front view of the chest (patient's right = viewer's left).
Colours follow the AHA (US) convention; IEC colours are given in the page text.
"""
from html import escape as _esc

# AHA colours
COL = {"RA": "#ffffff", "LA": "#111111", "RL": "#16a34a", "LL": "#dc2626", "V": "#8b5a2b",
       "V1": "#dc2626", "V2": "#eab308", "V3": "#16a34a", "V4": "#2563eb", "V5": "#f97316", "V6": "#7c3aed"}
POS = {"RA": (96, 128), "LA": (324, 128), "RL": (150, 432), "LL": (270, 432),
       "V1": (187, 214), "V2": (233, 214), "V3": (259, 232), "V4": (285, 248), "V5": (320, 250), "V6": (352, 252)}

TORSO = ("M150 52 C170 64 250 64 270 52 L330 74 C352 84 362 104 364 132 L366 300 "
         "C360 352 336 380 312 400 L300 470 L120 470 L108 400 C84 380 60 352 54 300 "
         "L56 132 C58 104 68 84 90 74 Z")


def _dot(name, x, y, label=None, color=None):
    c = color or COL.get(name, "#8b5a2b")
    txt = "#111" if c in ("#ffffff", "#eab308") else "#fff"
    lab = _esc(label or name)
    fs = 9.5 if len(lab) <= 2 else 8
    return (f'<g><circle cx="{x}" cy="{y}" r="12.5" fill="{c}" stroke="#1f2937" stroke-width="1.6"/>'
            f'<text x="{x}" y="{y + 3.4}" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" '
            f'font-size="{fs}" font-weight="700" fill="{txt}">{lab}</text></g>')


def diagram(kind):
    """kind: '12', '5' or '3'"""
    title = {"12": "12-lead ECG electrode placement: 4 limb electrodes and 6 chest electrodes V1 to V6",
             "5": "5-lead ECG electrode placement: RA, LA, RL, LL and one chest electrode (V)",
             "3": "3-lead ECG electrode placement: RA, LA and LL"}[kind]
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 486" width="420" height="486" role="img" aria-label="{_esc(title)}">',
         f'<title>{_esc(title)}</title>',
         '<rect width="420" height="486" rx="14" fill="#fff8f8"/>',
         f'<path d="{TORSO}" fill="#fde7e2" stroke="#b07a72" stroke-width="2"/>',
         # clavicles
         '<path d="M112 92 Q160 104 204 96 M216 96 Q260 104 308 92" fill="none" stroke="#b07a72" stroke-width="2.2" stroke-linecap="round"/>',
         # sternum
         '<path d="M202 98 L218 98 L216 262 L210 276 L204 262 Z" fill="#f7d3cc" stroke="#b07a72" stroke-width="1.4"/>']
    if kind == "12":
        # intercostal guides
        o.append('<path d="M150 214 Q210 222 270 214" fill="none" stroke="#c99891" stroke-width="1" stroke-dasharray="3 3"/>')
        o.append('<path d="M232 247 Q300 256 368 246" fill="none" stroke="#c99891" stroke-width="1" stroke-dasharray="3 3"/>')
        o.append('<path d="M285 100 L285 300" stroke="#9aa3ae" stroke-width="1" stroke-dasharray="2 4"/>')
        o.append('<text x="112" y="208" font-family="Arial,Helvetica,sans-serif" font-size="9" fill="#7a4a44">4th ICS</text>')
        o.append('<text x="236" y="276" font-family="Arial,Helvetica,sans-serif" font-size="9" fill="#7a4a44">5th ICS</text>')
        o.append('<text x="289" y="112" font-family="Arial,Helvetica,sans-serif" font-size="9" fill="#5b6470">mid-clavicular line</text>')
        for v in ("V1", "V2", "V3", "V4", "V5", "V6"):
            o.append(_dot(v, *POS[v]))
        for v in ("RA", "LA", "RL", "LL"):
            o.append(_dot(v, *POS[v]))
    elif kind == "5":
        for v in ("RA", "LA", "RL", "LL"):
            o.append(_dot(v, *POS[v]))
        o.append(_dot("V", *POS["V1"], color=COL["V"]))
        o.append('<text x="150" y="190" font-family="Arial,Helvetica,sans-serif" font-size="9" fill="#7a4a44">V: 4th ICS, right of sternum (V1 position)</text>')
    else:
        o.append('<path d="M96 128 L324 128 L270 432 Z" fill="none" stroke="#1d4ed8" stroke-width="1.2" stroke-dasharray="5 4"/>')
        for v in ("RA", "LA", "LL"):
            o.append(_dot(v, *POS[v]))
        o.append('<text x="210" y="122" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" font-size="9.5" fill="#1d4ed8">Lead I</text>')
        o.append('<text x="150" y="290" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" font-size="9.5" fill="#1d4ed8">Lead II</text>')
        o.append('<text x="314" y="290" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" font-size="9.5" fill="#1d4ed8">Lead III</text>')
    o.append('<text x="22" y="30" font-family="Arial,Helvetica,sans-serif" font-size="10" fill="#5b6470">Patient\'s right</text>')
    o.append('<text x="398" y="30" text-anchor="end" font-family="Arial,Helvetica,sans-serif" font-size="10" fill="#5b6470">Patient\'s left</text>')
    o.append('<text x="410" y="478" text-anchor="end" font-family="Arial,Helvetica,sans-serif" font-size="8.5" fill="#8a5a5e">AHA colours · schematic · ecgmeans.com</text>')
    o.append('</svg>')
    return "".join(o)


CAPTIONS = {
    "12": "Standard 12-lead electrode positions (AHA colours). V1 and V2 sit in the 4th intercostal space either side of the sternum; V4 in the 5th space at the mid-clavicular line; V3 halfway between V2 and V4; V5 and V6 level with V4 at the anterior and mid-axillary lines. Limb electrodes go on the arms and legs (or shoulders and lower abdomen for monitoring).",
    "5": "5-lead monitoring positions (AHA colours): white RA under the right clavicle, black LA under the left clavicle, green RL and red LL on the lower abdomen or hips, brown chest electrode usually at the V1 position.",
    "3": "3-lead monitoring positions (AHA colours): white RA right shoulder, black LA left shoulder, red LL left lower abdomen. The dashed triangle is Einthoven's triangle, which forms leads I, II and III.",
}

KIND = {"12-lead-ecg-placement": "12", "5-lead-ecg-placement": "5", "3-lead-ecg-placement": "3"}


def figure_html(slug):
    k = KIND.get(slug)
    if not k:
        return ""
    return (f'<figure class="ecg-fig lead-fig" style="max-width:440px">{diagram(k)}'
            f'<figcaption>{_esc(CAPTIONS[k])}</figcaption></figure>')
