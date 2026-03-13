from flask import Flask, render_template, request, jsonify
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)

# ══════════════════════════════════════════════════════════
# CONFIGURACIÓN  ← edita solo esta sección
# ══════════════════════════════════════════════════════════
GMAIL_REMITENTE     = "potinesdomiclios@gmail.com"
GMAIL_PASSWORD      = "cssh uvlx jgrc daki"
CORREO_DESPACHADORA = "potinesdomiclios@gmail.com"
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

SAUCE_NAMES  = {
    "rosada":"Salsa Rosada",
    "enacorradora":"Salsa Encacorradora",
    "bbq":"Salsa BBQ",
    "pina":"Salsa de Piña",
    "sin_salsa":"Sin salsa"
}

SODA_NAMES   = {
    "cocacola":"Coca-Cola",
    "quatro":"Cuatro",
    "aguamanzana":"Agua de Manzana",
    "aguamaracuya":"Agua de Maracuyá",
    "delvalle":"Del Valle"
}

SODA_PRICES  = {
    "cocacola":3000,
    "quatro":3000,
    "aguamanzana":3000,
    "aguamaracuya":3000,
    "delvalle":3000
}

COMBO_PRICES = {
    "clasico":16000,
    "mega":15000,
    "familiar":14000,
    "papas":10000
}

# NUEVAS ADICIONES
ADICION_PRICES = {
    "bombon":6000,
    "snack":4000,
    "huevos":800,
    "salchicha":800
}


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/enviar-pedido', methods=['POST'])
def enviar_pedido():

    datos     = request.json
    combos    = datos.get('combos', {})
    salsas    = datos.get('salsas', {})
    bebidas   = datos.get('bebidas', {})
    adiciones = datos.get('adiciones', {})
    domicilio = datos.get('domicilio', {})

    numero_orden = generar_numero_orden()

    total_combos  = sum(COMBO_PRICES.get(k,0)*v for k,v in combos.items() if v>0)
    total_bebidas = sum(SODA_PRICES.get(k,0)*v for k,v in bebidas.items() if v>0)
    total_adiciones = sum(ADICION_PRICES.get(k,0)*v for k,v in adiciones.items() if v>0)

    costo_domicilio = datos.get('costo_domicilio', 0)

    total_general = total_combos + total_bebidas + total_adiciones + costo_domicilio

    # ══════════════════════════════════════════════════════
    # RESUMEN DEL PEDIDO
    # ══════════════════════════════════════════════════════

    lineas = [
        "🍟 NUEVO PEDIDO POTINES 🍟",
        "="*40,
        f"📋 ORDEN: {numero_orden}",
        "="*40,
        "",
        "📦 COMBOS:"
    ]

    for k,v in combos.items():
        if v>0:
            lineas.append(
                f"  x{v} {COMBO_NAMES.get(k,k)}  →  ${COMBO_PRICES.get(k,0)*v:,}"
            )

    lineas += ["","🥫 SALSAS:"]

    for ck,qty in combos.items():

        for i in range(1,qty+1):

            sk  = f"sauce_{ck}_{i}"
            sel = salsas.get(sk,[])

            lbl = (COMBO_NAMES.get(ck,ck)+f" #{i}") if qty>1 else COMBO_NAMES.get(ck,ck)

            lineas.append(
                f"  {lbl}: {', '.join(SAUCE_NAMES.get(s,s) for s in sel) if sel else 'Sin especificar'}"
            )


    # BEBIDAS
    bped = {k:v for k,v in bebidas.items() if v>0}

    lineas += ["","🥤 BEBIDAS:" if bped else "🥤 BEBIDAS: Sin bebidas"]

    for k,v in bped.items():
        lineas.append(
            f"  x{v} {SODA_NAMES.get(k,k)}  →  ${SODA_PRICES.get(k,0)*v:,}"
        )


    # ADICIONES
    aped = {k:v for k,v in adiciones.items() if v>0}

    lineas += ["","➕ ADICIONES:" if aped else "➕ ADICIONES: Sin adiciones"]

    for k,v in aped.items():

        nombre = k.capitalize()

        lineas.append(
            f"  x{v} {nombre}  →  ${ADICION_PRICES.get(k,0)*v:,}"
        )


    # DOMICILIO
    lineas += [
        "",
        "📍 DOMICILIO:",
        f"  Nombre:     {domicilio.get('nombre','N/A')}",
        f"  Celular:    {domicilio.get('celular','N/A')}",
        f"  Barrio:     {domicilio.get('barrio','N/A')}",
        f"  Dirección:  {domicilio.get('direccion','N/A')}",
        f"  Referencia: {domicilio.get('referencia','—') or '—'}",
        "",
        "="*40,
        f"  Subtotal productos: ${total_combos+total_bebidas+total_adiciones:,}",
        f"  Domicilio:          ${costo_domicilio:,}",
        f"💰 TOTAL A COBRAR:    ${total_general:,}",
        "="*40
    ]

    resumen_texto = "\n".join(lineas)

    print(resumen_texto)


    try:
        _enviar_correo(numero_orden, resumen_texto, domicilio, total_general)
        correo_ok = True

    except Exception as e:
        print(f"❌ Error correo: {e}")
        correo_ok = False


    return jsonify({
        "status":"success",
        "numero_orden":numero_orden,
        "total":total_general,
        "correo_ok":correo_ok
    }), 200



# ══════════════════════════════════════════════════════
# ENVÍO DE CORREO
# ══════════════════════════════════════════════════════

def _enviar_correo(numero_orden, resumen_texto, domicilio, total):

    msg = MIMEMultipart("alternative")

    msg["Subject"] = f"🍟 POTINES — Nuevo pedido {numero_orden}"
    msg["From"]    = GMAIL_REMITENTE
    msg["To"]      = CORREO_DESPACHADORA

    html = f"""
<!DOCTYPE html>
<html>
<body style="font-family:Arial;background:#f9f9f9;padding:20px;">

<h2>🍟 POTINES</h2>

<pre style="background:white;padding:20px;border-radius:10px;">
{resumen_texto}
</pre>

<h3>Total a cobrar: ${total:,}</h3>

</body>
</html>
"""

    msg.attach(MIMEText(resumen_texto,"plain","utf-8"))
    msg.attach(MIMEText(html,"html","utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com",465) as server:

        server.login(GMAIL_REMITENTE, GMAIL_PASSWORD)

        server.sendmail(
            GMAIL_REMITENTE,
            CORREO_DESPACHADORA,
            msg.as_string()
        )


if __name__ == '__main__':
    app.run(debug=True, port=5000)
