from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
from pymongo import MongoClient
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'clave-secreta-estudio-juridico-2024'

# Tomar la URI desde Render o fallback local
MONGO_URI = os.environ.get("MONGO_URI")
if not MONGO_URI:
    MONGO_URI = "mongodb+srv://stationnet2:chicha1330@cluster0.hvj9lvn.mongodb.net/?appName=Cluster0"

client = MongoClient(MONGO_URI)
db = client["estudio_juridico"]
coleccion = db["clientes"]

# =========================
# FUNCIONES AUXILIARES
# =========================
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
        print("ERROR guardando:", e)
        return False

def cargar_clientes():
    try:
        clientes = list(coleccion.find({}, {"_id": 0}))
        return clientes
    except Exception as e:
        print("ERROR cargando clientes:", e)
        return []

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
    return colores.get(estado.lower().strip(), 'bg-secondary') if estado else 'bg-secondary'

def obtener_color_puntuacion(p):
    if p >= 7: return 'bg-success'
    if p >= 4: return 'bg-warning'
    return 'bg-danger'

# =========================
# RUTAS PRINCIPALES
# =========================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/asesoria-gratuita', methods=['GET', 'POST'])
def asesoria_gratuita():
    if request.method == 'POST':
        cliente_data = {
            "id": int(datetime.now().timestamp()),
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
            flash('Complete los datos obligatorios', 'error')
            return render_template('asesoria.html')

        if guardar_cliente(cliente_data):
            return redirect(url_for('gracias'))
        else:
            flash('Ocurrió un error guardando los datos', 'error')

    return render_template('asesoria.html')

@app.route('/gracias')
def gracias():
    return render_template('gracias.html')

# =========================
# DASHBOARD ADMIN
# =========================
@app.route('/admin/')
def admin_dashboard():
    clientes = cargar_clientes()
    casos_pendientes = [c for c in clientes if c.get('estado','').strip().lower() in ['nuevo','en_revision']]
    ultimos_casos = sorted(clientes, key=lambda x: x.get('fecha_creacion',''), reverse=True)[:10]

    return render_template(
        'admin/dashboard.html',
        clientes=clientes,
        casos_pendientes=casos_pendientes,
        ultimos_casos=ultimos_casos,
        total_casos=len(clientes),
        casos_nuevos=len([c for c in clientes if c.get('estado','').strip().lower() == 'nuevo']),
        casos_aptos=len([c for c in clientes if c.get('estado','').strip().lower() == 'apto']),
        casos_revision=len([c for c in clientes if c.get('estado','').strip().lower() == 'en_revision']),
        casos_descartados=len([c for c in clientes if c.get('estado','').strip().lower() == 'descartado']),
        casos_contactados=len([c for c in clientes if c.get('estado','').strip().lower() == 'contactado']),
        obtener_color_estado=obtener_color_estado,
        obtener_color_puntuacion=obtener_color_puntuacion
    )

# =========================
# DETALLE Y ACTUALIZACIÓN DE CASO
# =========================
@app.route('/admin/caso/<int:id>')
def detalle_caso(id):
    clientes = cargar_clientes()
    caso = next((c for c in clientes if c['id'] == id), None)
    if not caso:
        return "Caso no encontrado", 404
    return render_template(
        'admin/detalle_caso.html',
        caso=caso,
        obtener_color_estado=obtener_color_estado,
        obtener_color_puntuacion=obtener_color_puntuacion
    )

@app.route('/admin/actualizar-caso/<int:id>', methods=['POST'])
def actualizar(id):
    nuevos_datos = {
        "estado": request.form.get("estado"),
        "prioridad": int(request.form.get("prioridad")),
        "observaciones_abogado": request.form.get("observaciones")
    }
    coleccion.update_one({"id": id}, {"$set": nuevos_datos})
    return redirect(f"/admin/caso/{id}")

# =========================
# BORRAR CASO
# =========================
@app.route('/admin/borrar-caso/<int:id>', methods=['POST'])
def borrar_caso(id):
    resultado = coleccion.delete_one({"id": id})
    if resultado.deleted_count:
        flash(f"Caso #{id} eliminado correctamente.", "success")
    else:
        flash(f"No se encontró el caso #{id}.", "error")
    return redirect(url_for('admin_dashboard'))

# =========================
# NUEVAS RUTAS PARA DASHBOARD MEJORADO
# =========================
@app.route('/admin/cambiar-prioridad/<int:id>', methods=['POST'])
def cambiar_prioridad(id):
    try:
        nueva_prioridad = int(request.form.get('prioridad'))
        coleccion.update_one(
            {"id": id}, 
            {"$set": {"prioridad": nueva_prioridad}}
        )
        flash(f"Prioridad del caso #{id} actualizada correctamente", "success")
    except Exception as e:
        flash(f"Error al actualizar prioridad: {str(e)}", "error")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/cambiar-estado/<int:id>', methods=['POST'])
def cambiar_estado(id):
    try:
        nuevo_estado = request.form.get('estado')
        coleccion.update_one(
            {"id": id}, 
            {"$set": {"estado": nuevo_estado}}
        )
        flash(f"Estado del caso #{id} actualizado a {nuevo_estado}", "success")
    except Exception as e:
        flash(f"Error al actualizar estado: {str(e)}", "error")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/eliminar-multiples', methods=['POST'])
def eliminar_multiples_casos():
    try:
        casos_ids = request.form.getlist('casos_seleccionados')
        if casos_ids:
            # Convertir a enteros
            casos_ids = [int(id) for id in casos_ids]
            resultado = coleccion.delete_many({"id": {"$in": casos_ids}})
            flash(f"{resultado.deleted_count} casos eliminados correctamente", "success")
        else:
            flash("No se seleccionaron casos para eliminar", "warning")
    except Exception as e:
        flash(f"Error al eliminar casos: {str(e)}", "error")
    return redirect(url_for('admin_dashboard'))

# =========================
# EJECUTAR SERVIDOR
# =========================
if __name__ == '__main__':
    app.run(debug=True, port=5000)