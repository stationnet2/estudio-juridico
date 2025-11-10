from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
from pymongo import MongoClient

app = Flask(__name__)
app.config['SECRET_KEY'] = 'clave-secreta-estudio-juridico-2024'

# ✅ Conexión a MongoDB Atlas
MONGO_URI = "mongodb+srv://stationnet2:chicha1330@cluster0.lnook.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)

# ✅ Base de datos y colección
db = client["estudio_juridico"]
coleccion = db["clientes"]


# ✅ GUARDAR CLIENTE
def guardar_cliente(cliente_data):
    try:
        cliente_data['fecha_creacion'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cliente_data['puntuacion_viabilidad'] = calcular_viabilidad(cliente_data)
        cliente_data['estado'] = evaluar_caso_automatico(cliente_data)
        cliente_data['prioridad'] = calcular_prioridad(cliente_data)
        cliente_data['observaciones_abogado'] = ""

        coleccion.insert_one(cliente_data)
        return True

    except Exception as e:
        print("❌ ERROR guardando:", e)
        return False


# ✅ CARGAR CLIENTES
def cargar_clientes():
    try:
        clientes = list(coleccion.find({}, {"_id": 0}))
        return clientes
    except Exception as e:
        print("❌ ERROR cargando clientes:", e)
        return []


# ✅ BUSCAR POR ID
def obtener_caso_por_id(id):
    try:
        caso = coleccion.find_one({"id": id}, {"_id": 0})
        return caso
    except:
        return None


# ✅ ACTUALIZAR CASO
def actualizar_caso(id, nuevos_datos):
    try:
        coleccion.update_one({"id": id}, {"$set": nuevos_datos})
        return True
    except:
        return False


# ============================================
#   SISTEMA DE PUNTUACIÓN Y ESTADOS
# ============================================

def calcular_viabilidad(cliente):
    p = 0
    if cliente.get('hay_lesiones') == 'on': p += 3
    if cliente.get('hay_danos_materiales') == 'on': p += 2
    if cliente.get('tiene_seguro') == 'on': p += 2
    if cliente.get('rol_usuario') == 'victima': p += 2
    if cliente.get('tipo_accidente') == 'peatonal': p += 1
    return min(10, p)


def evaluar_caso_automatico(cliente):
    p = calcular_viabilidad(cliente)
    if p >= 8 or (cliente.get('hay_lesiones') == 'on' and p >= 7):
        return 'apto'
    if p >= 5 or cliente.get('hay_danos_materiales') == 'on' or cliente.get('tiene_seguro') == 'on':
        return 'en_revision'
    return 'descartado'


def calcular_prioridad(cliente):
    estado = evaluar_caso_automatico(cliente)
    if estado == 'apto' and cliente.get('hay_lesiones') == 'on': return 5
    if estado == 'apto': return 4
    if estado == 'en_revision': return 3
    if estado == 'nuevo': return 2
    return 1


def obtener_color_estado(estado):
    colores = {
        'nuevo': 'bg-primary',
        'en_revision': 'bg-warning',
        'apto': 'bg-success',
        'descartado': 'bg-secondary',
        'contactado': 'bg-info'
    }
    return colores.get(estado, 'bg-secondary')


def obtener_color_puntuacion(p):
    if p >= 7: return 'bg-success'
    if p >= 4: return 'bg-warning'
    return 'bg-danger'


# ============================================
#                  RUTAS
# ============================================

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/asesoria-gratuita', methods=['GET', 'POST'])
def asesoria_gratuita():
    if request.method == 'POST':
        cliente_data = {
            "id": int(datetime.now().timestamp()),  # ✅ Genera ID único
            'nombre': request.form.get('nombre'),
            'email': request.form.get('email'),
            'telefono': request.form.get('telefono'),
            'tipo_accidente': request.form.get('tipo_accidente'),
            'rol_usuario': request.form.get('rol_usuario'),
            'fecha_accidente': request.form.get('fecha_accidente'),
            'descripcion': request.form.get('descripcion'),
            'hay_lesiones': request.form.get('hay_lesiones'),
            'hay_danos_materiales': request.form.get('hay_danos_materiales'),
            'tiene_seguro': request.form.get('tiene_seguro'),
            'seguro_propio': request.form.get('seguro_propio', ''),
            'seguro_contrario': request.form.get('seguro_contrario', '')
        }

        if not all([cliente_data['nombre'], cliente_data['email'], cliente_data['telefono']]):
            flash('❗ Complete los datos obligatorios', 'error')
            return render_template('asesoria.html')

        if guardar_cliente(cliente_data):
            return redirect(url_for('gracias'))
        else:
            flash('⚠ Ocurrió un error guardando los datos. Intente nuevamente.', 'error')

    return render_template('asesoria.html')


@app.route('/gracias')
def gracias():
    return render_template('gracias.html')


# ✅ DASHBOARD
@app.route('/admin/')
def admin_dashboard():
    clientes = cargar_clientes()

    casos_pendientes = [c for c in clientes if c.get('estado') in ['nuevo', 'en_revision']]

    ultimos_casos = sorted(clientes, key=lambda x: x['fecha_creacion'], reverse=True)[:10]

    return render_template(
        'admin/dashboard.html',
        clientes=clientes,
        casos_pendientes=casos_pendientes,
        ultimos_casos=ultimos_casos,
        total_casos=len(clientes),
        casos_nuevos=len([c for c in clientes if c.get('estado') == 'nuevo']),
        casos_aptos=len([c for c in clientes if c.get('estado') == 'apto']),
        casos_revision=len([c for c in clientes if c.get('estado') == 'en_revision']),
        casos_descartados=len([c for c in clientes if c.get('estado') == 'descartado']),
        casos_contactados=len([c for c in clientes if c.get('estado') == 'contactado']),
        obtener_color_estado=obtener_color_estado,
        obtener_color_puntuacion=obtener_color_puntuacion
    )


# ✅ ✅ RUTA DE DETALLE DE CASO
@app.route('/admin/caso/<int:id>')
def detalle_caso(id):
    clientes = cargar_clientes()
    caso = next((c for c in clientes if c['id'] == id), None)

    if not caso:
        return "❌ Caso no encontrado", 404

    return render_template(
        'admin/detalle_caso.html',
        caso=caso,
        obtener_color_estado=obtener_color_estado,
        obtener_color_puntuacion=obtener_color_puntuacion
    )


# ✅ ✅ RUTA PARA ACTUALIZAR CASO
@app.route('/admin/actualizar-caso/<int:id>', methods=['POST'])
def actualizar(id):
    nuevos_datos = {
        "estado": request.form.get("estado"),
        "prioridad": int(request.form.get("prioridad")),
        "observaciones_abogado": request.form.get("observaciones")
    }

    coleccion.update_one({"id": id}, {"$set": nuevos_datos})

    return redirect(f"/admin/caso/{id}")


# ============================================
#           EJECUTAR SERVIDOR
# ============================================
if __name__ == '__main__':
    app.run(debug=True, port=5000)
