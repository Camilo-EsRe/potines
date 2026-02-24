from flask import Flask, render_template, request, jsonify
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)

# ══════════════════════════════════════════════════════════
# CONFIGURACIÓN  ← edita solo esta sección
# ══════════════════════════════════════════════════════════
GMAIL_REMITENTE     = "c.estrada712017@gmail.com"        # Tu Gmail remitente
GMAIL_PASSWORD      = "mfdi nizt azlq jeng"       # Contraseña de APP de Gmail (16 chars)
CORREO_DESPACHADORA = "limpiezabrillux@gmail.com"    # Destinatario del pedido
COSTO_DOMICILIO     = 4500
# ══════════════════════════════════════════════════════════

_orden_counter = 0

def generar_numero_orden():
    global _orden_counter
    _orden_counter += 1
    return f"#{str(_orden_counter).zfill(6)}"

COMBO_NAMES  = {
    "clasico":  "COMBO 1 (Papas + Snack de Pollo + Bombón + Salchicha + Huevo)",
    "mega":     "COMBO 2 (3 Snacks + 2 Huevos + Papas + Salchicha)",
    "familiar": "COMBO 3 (Bombón + Papas + Salchicha + Huevo)",
    "papas":    "COMBO 4 (Papas + Salchicha + Huevo)"
}
SAUCE_NAMES  = {"casa":"Salsa de la Casa","enacorradora":"Salsa Enacorradora","rosada":"Salsa Rosada","sin_salsa":"Sin salsa"}
SODA_NAMES   = {"cocacola":"Coca-Cola","sprite":"Sprite","quatro":"Quatro","agua":"Agua"}
SODA_PRICES  = {"cocacola":3000,"sprite":3000,"quatro":3000,"agua":3000}
COMBO_PRICES = {"clasico":16000,"mega":15000,"familiar":14000,"papas":10000}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/enviar-pedido', methods=['POST'])
def enviar_pedido():
    datos     = request.json
    combos    = datos.get('combos', {})
    salsas    = datos.get('salsas', {})
    bebidas   = datos.get('bebidas', {})
    domicilio = datos.get('domicilio', {})

    numero_orden = generar_numero_orden()

    total_combos  = sum(COMBO_PRICES.get(k,0)*v for k,v in combos.items() if v>0)
    total_bebidas = sum(SODA_PRICES.get(k,0)*v  for k,v in bebidas.items() if v>0)
    total_general = total_combos + total_bebidas + COSTO_DOMICILIO

    # Resumen de texto
    lineas = [f"🍟 NUEVO PEDIDO POTINES 🍟","="*40,f"📋 ORDEN: {numero_orden}","="*40,"","📦 COMBOS:"]
    for k,v in combos.items():
        if v>0: lineas.append(f"  x{v} {COMBO_NAMES.get(k,k)}  →  ${COMBO_PRICES.get(k,0)*v:,}")
    lineas += ["","🥫 SALSAS:"]
    for ck,qty in combos.items():
        for i in range(1,qty+1):
            sk  = f"sauce_{ck}_{i}"
            sel = salsas.get(sk,[])
            lbl = (COMBO_NAMES.get(ck,ck)+f" #{i}") if qty>1 else COMBO_NAMES.get(ck,ck)
            lineas.append(f"  {lbl}: {', '.join(SAUCE_NAMES.get(s,s) for s in sel) if sel else 'Sin especificar'}")
    bped = {k:v for k,v in bebidas.items() if v>0}
    lineas += ["","🥤 BEBIDAS:" if bped else "🥤 BEBIDAS: Sin bebidas"]
    for k,v in bped.items(): lineas.append(f"  x{v} {SODA_NAMES.get(k,k)}  →  ${SODA_PRICES.get(k,0)*v:,}")
    lineas += ["","📍 DOMICILIO:",
        f"  Nombre:     {domicilio.get('nombre','N/A')}",
        f"  Celular:    {domicilio.get('celular','N/A')}",
        f"  Barrio:     {domicilio.get('barrio','N/A')}",
        f"  Dirección:  {domicilio.get('direccion','N/A')}",
        f"  Referencia: {domicilio.get('referencia','—') or '—'}",
        "","="*40,
        f"  Subtotal productos: ${total_combos+total_bebidas:,}",
        f"  Domicilio:          ${COSTO_DOMICILIO:,}",
        f"💰 TOTAL A COBRAR:    ${total_general:,}",
        "="*40]
    resumen_texto = "\n".join(lineas)
    print(resumen_texto)

    try:
        _enviar_correo(numero_orden, resumen_texto, domicilio, total_general)
        correo_ok = True
    except Exception as e:
        print(f"❌ Error correo: {e}")
        correo_ok = False

    return jsonify({"status":"success","numero_orden":numero_orden,"total":total_general,"correo_ok":correo_ok}), 200


def _enviar_correo(numero_orden, resumen_texto, domicilio, total):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🍟 POTINES — Nuevo pedido {numero_orden}"
    msg["From"]    = GMAIL_REMITENTE
    msg["To"]      = CORREO_DESPACHADORA

    html = f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;background:#f9f9f9;padding:20px;margin:0;">
<div style="max-width:520px;margin:0 auto;background:white;border-radius:16px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.1);">
  <div style="background:linear-gradient(135deg,#dc2626,#b91c1c);padding:24px;text-align:center;">
    <h1 style="color:white;margin:0;font-size:26px;letter-spacing:2px;">🍟 POTINES</h1>
    <p style="color:rgba(255,255,255,0.85);margin:6px 0 0;font-size:13px;">NUEVO PEDIDO RECIBIDO</p>
  </div>
  <div style="background:#1a1a1a;padding:18px;text-align:center;">
    <p style="color:#fbbf24;font-family:'Courier New',monospace;font-size:36px;font-weight:bold;margin:0;letter-spacing:4px;">{numero_orden}</p>
    <p style="color:rgba(255,255,255,0.5);font-size:11px;margin:4px 0 0;">NÚMERO DE ORDEN</p>
  </div>
  <div style="padding:24px;">
    <div style="background:#f3f4f6;border-radius:10px;padding:16px;font-family:'Courier New',monospace;font-size:13px;white-space:pre-line;color:#1f2937;line-height:1.7;">{resumen_texto}</div>
    <div style="margin-top:20px;background:#fef3c7;border:2px solid #fbbf24;border-radius:12px;padding:16px;">
      <h3 style="margin:0 0 12px;color:#92400e;font-size:15px;">📍 Datos del domicilio</h3>
      <table style="width:100%;border-collapse:collapse;font-size:14px;color:#1f2937;">
        <tr><td style="padding:4px 8px;font-weight:bold;width:110px;">Nombre</td><td style="padding:4px 8px;">{domicilio.get('nombre','—')}</td></tr>
        <tr style="background:rgba(255,255,255,0.5);"><td style="padding:4px 8px;font-weight:bold;">Celular</td><td style="padding:4px 8px;">{domicilio.get('celular','—')}</td></tr>
        <tr><td style="padding:4px 8px;font-weight:bold;">Barrio</td><td style="padding:4px 8px;">{domicilio.get('barrio','—')}</td></tr>
        <tr style="background:rgba(255,255,255,0.5);"><td style="padding:4px 8px;font-weight:bold;">Dirección</td><td style="padding:4px 8px;">{domicilio.get('direccion','—')}</td></tr>
        <tr><td style="padding:4px 8px;font-weight:bold;">Referencia</td><td style="padding:4px 8px;">{domicilio.get('referencia','—') or '—'}</td></tr>
      </table>
    </div>
    <div style="margin-top:16px;background:#dc2626;border-radius:12px;padding:16px;text-align:center;">
      <p style="color:rgba(255,255,255,0.8);margin:0;font-size:12px;text-transform:uppercase;">Total a cobrar (incluye domicilio $4.500)</p>
      <p style="color:white;font-size:32px;font-weight:bold;margin:4px 0 0;">${total:,}</p>
    </div>
  </div>
  <div style="background:#f9fafb;padding:14px;text-align:center;border-top:1px solid #e5e7eb;">
    <p style="color:#9ca3af;font-size:11px;margin:0;">POTINES · Caldas, Antioquia · pedido generado automáticamente</p>
  </div>
</div>
</body></html>"""

    msg.attach(MIMEText(resumen_texto, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_REMITENTE, GMAIL_PASSWORD)
        server.sendmail(GMAIL_REMITENTE, CORREO_DESPACHADORA, msg.as_string())

if __name__ == '__main__':
    app.run(debug=True, port=5000)