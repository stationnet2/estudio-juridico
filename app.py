from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
from pymongo import MongoClient
import os
from bson import ObjectId

app = Flask(__name__)
app.config['SECRET_KEY'] = 'clave-secreta-estudio-juridico-2024'

# Tomar la URI desde Render o fallback local
MONGO_URI = os.environ.get("MONGO_URI")
if not MONGO_URI:
    MONGO_URI = "mongodb+srv://stationnet2:chicha1330@cluster0.hvj9lvn.mongodb.net/?appName=Cluster0"

try:
    client = MongoClient(MONGO_URI)
    db = client["estudio_juridico"]
    coleccion = db["clientes"]
    print("✅ Conectado a MongoDB Atlas correctamente")
except Exception as e:
    print(f"❌ Error conectando a MongoDB: {e}")
    client = None
    db = None
    coleccion = None

# =========================
# FUNCIONES AUXILIARES
# =========================
def guardar_cliente(cliente_data):
    try:
        if coleccion is None:
            print("❌ No hay conexión a MongoDB")
            return False
            
        cliente_data['fecha_creacion'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cliente_data['puntuacion_viabilidad'] = calcular_viabilidad(cliente_data)
        cliente_data['estado'] = evaluar_caso_automatico(cliente_data)
        cliente_data['prioridad'] = calcular_prioridad(cliente_data)
        cliente_data['observaciones_abogado'] = ""
        
        # Asegurar que siempre tenga un ID
        if 'id' not in cliente_data:
            cliente_data['id'] = int(datetime.now().timestamp())
            
        resultado = coleccion.insert_one(cliente_data)
        print(f"✅ Cliente guardado con ID: {cliente_data['id']}")
        return True
    except Exception as e:
        print(f"❌ ERROR guardando cliente: {e}")
        return False

def cargar_clientes():
    try:
        if coleccion is None:
            print("❌ No hay conexión a MongoDB")
            return []
            
        # Proyectar _id también para usarlo como fallback
        clientes = list(coleccion.find({}))
        print(f"✅ Se cargaron {len(clientes)} clientes de MongoDB")
        
        # Normalizar los datos para asegurar que siempre tengan ID
        for cliente in clientes:
            # Si no tiene 'id', usar el _id de MongoDB como string
            if 'id' not in cliente:
                cliente['id'] = str(cliente['_id'])
            # Convertir ObjectId a string para que sea serializable
            if '_id' in cliente and isinstance(cliente['_id'], ObjectId):
                cliente['_id'] = str(cliente['_id'])
                
        return clientes
    except Exception as e:
        print(f"❌ ERROR cargando clientes: {e}")
        return []

def calcular_viabilidad(cliente):
    try:
        p = 0
        if cliente.get('hay_lesiones') == 'on': p += 3
        if cliente.get('hay_danos_materiales') == 'on': p += 2
        if cliente.get('tiene_seguro') == 'on': p += 2
        if cliente.get('rol_usuario') == 'victima': p += 2
        if cliente.get('tipo_accidente') == 'peatonal': p += 1
        return min(10, p)
    except Exception as e:
        print(f"❌ ERROR calculando viabilidad: {e}")
        return 0

def evaluar_caso_automatico(cliente):
    try:
        p = calcular_viabilidad(cliente)
        if p >= 8 or (cliente.get('hay_lesiones') == 'on' and p >= 7):
            return 'apto'
        if p >= 5 or cliente.get('hay_danos_materiales') == 'on' or cliente.get('tiene_seguro') == 'on':
            return 'en_revision'
        return 'descartado'
    except Exception as e:
        print(f"❌ ERROR evaluando caso: {e}")
        return 'nuevo'

def calcular_prioridad(cliente):
    try:
        estado = evaluar_caso_automatico(cliente)
        if estado == 'apto' and cliente.get('hay_lesiones') == 'on': return 5
        if estado == 'apto': return 4
        if estado == 'en_revision': return 3
        if estado == 'nuevo': return 2
        return 1
    except Exception as e:
        print(f"❌ ERROR calculando prioridad: {e}")
        return 1

def obtener_color_estado(estado):
    try:
        # Convertir a string y manejar None
        estado_str = str(estado) if estado is not None else ''
        colores = {
            'nuevo': 'bg-primary',
            'en_revision': 'bg-warning',
            'apto': 'bg-success',
            'descartado': 'bg-secondary',
            'contactado': 'bg-info'
        }
        return colores.get(estado_str.lower().strip(), 'bg-secondary')
    except Exception as e:
        print(f"❌ ERROR obteniendo color estado: {e}")
        return 'bg-secondary'

def obtener_color_puntuacion(p):
    try:
        if p is None:
            return 'bg-secondary'
        if p >= 7: return 'bg-success'
        if p >= 4: return 'bg-warning'
        return 'bg-danger'
    except Exception as e:
        print(f"❌ ERROR obteniendo color puntuación: {e}")
        return 'bg-secondary'

# =========================
# RUTAS PRINCIPALES
# =========================
@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        print(f"❌ ERROR en ruta index: {e}")
        return "Error cargando la página principal", 500

@app.route('/asesoria-gratuita', methods=['GET', 'POST'])
def asesoria_gratuita():
    try:
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
    except Exception as e:
        print(f"❌ ERROR en ruta asesoria: {e}")
        flash('Error interno del servidor', 'error')
        return render_template('asesoria.html')

@app.route('/gracias')
def gracias():
    try:
        return render_template('gracias.html')
    except Exception as e:
        print(f"❌ ERROR en ruta gracias: {e}")
        return "Error cargando página de gracias", 500

# =========================
# DASHBOARD ADMIN
# =========================
@app.route('/admin/')
def admin_dashboard():
    try:
        clientes = cargar_clientes()
        
        # DEBUG DETALLADO
        print(f"=== DEBUG DASHBOARD ===")
        print(f"Total clientes cargados: {len(clientes)}")
        
        for i, cliente in enumerate(clientes):
            estado = cliente.get('estado', 'NO TIENE ESTADO')
            id_val = cliente.get('id', 'NO TIENE ID')
            nombre = cliente.get('nombre', 'NO TIENE NOMBRE')
            print(f"Cliente {i}: ID={id_val}, Estado='{estado}', Nombre='{nombre}'")
        
        # MOSTRAR TODOS LOS CASOS
        casos_pendientes = clientes  # Mostrar todos los casos
        
        print(f"Casos a mostrar: {len(casos_pendientes)}")
        print("=== FIN DEBUG ===")
        
        ultimos_casos = sorted(clientes, key=lambda x: x.get('fecha_creacion',''), reverse=True)[:10]

        return render_template(
            'admin/dashboard.html',
            clientes=clientes,
            casos_pendientes=casos_pendientes,
            ultimos_casos=ultimos_casos,
            total_casos=len(clientes),
            casos_nuevos=len([c for c in clientes if str(c.get('estado','')).strip().lower() == 'nuevo']),
            casos_aptos=len([c for c in clientes if str(c.get('estado','')).strip().lower() == 'apto']),
            casos_revision=len([c for c in clientes if str(c.get('estado','')).strip().lower() == 'en_revision']),
            casos_descartados=len([c for c in clientes if str(c.get('estado','')).strip().lower() == 'descartado']),
            casos_contactados=len([c for c in clientes if str(c.get('estado','')).strip().lower() == 'contactado']),
            obtener_color_estado=obtener_color_estado,
            obtener_color_puntuacion=obtener_color_puntuacion
        )
    except Exception as e:
        print(f"❌ ERROR en ruta admin_dashboard: {e}")
        return f"Error interno del servidor: {str(e)}", 500

# =========================
# DETALLE Y ACTUALIZACIÓN DE CASO
# =========================
@app.route('/admin/caso/<id>')
def detalle_caso(id):
    try:
        if coleccion is None:
            return "Error de conexión a la base de datos", 500
            
        # Intentar buscar por ID numérico primero
        try:
            id_num = int(id)
            caso = coleccion.find_one({"id": id_num})
        except ValueError:
            # Si no es numérico, buscar por _id de MongoDB
            caso = coleccion.find_one({"_id": ObjectId(id)})
        
        if not caso:
            return "Caso no encontrado", 404
            
        # Convertir ObjectId a string para el template
        if '_id' in caso and isinstance(caso['_id'], ObjectId):
            caso['_id'] = str(caso['_id'])
            
        return render_template(
            'admin/detalle_caso.html',
            caso=caso,
            obtener_color_estado=obtener_color_estado,
            obtener_color_puntuacion=obtener_color_puntuacion
        )
    except Exception as e:
        print(f"❌ ERROR en ruta detalle_caso: {e}")
        return f"Error al cargar el caso: {str(e)}", 500

@app.route('/admin/actualizar-caso/<id>', methods=['POST'])
def actualizar(id):
    try:
        if coleccion is None:
            flash("Error de conexión a la base de datos", "error")
            return redirect(f"/admin/caso/{id}")
            
        nuevos_datos = {
            "estado": request.form.get("estado"),
            "prioridad": int(request.form.get("prioridad")),
            "observaciones_abogado": request.form.get("observaciones")
        }
        
        # Intentar actualizar por ID numérico primero
        try:
            id_num = int(id)
            coleccion.update_one({"id": id_num}, {"$set": nuevos_datos})
        except ValueError:
            # Si no es numérico, actualizar por _id de MongoDB
            coleccion.update_one({"_id": ObjectId(id)}, {"$set": nuevos_datos})
            
        return redirect(f"/admin/caso/{id}")
    except Exception as e:
        flash(f"Error al actualizar caso: {str(e)}", "error")
        return redirect(f"/admin/caso/{id}")

# =========================
# BORRAR CASO
# =========================
@app.route('/admin/borrar-caso/<id>', methods=['POST'])
def borrar_caso(id):
    try:
        if coleccion is None:
            flash("Error de conexión a la base de datos", "error")
            return redirect(url_for('admin_dashboard'))
            
        # Intentar eliminar por ID numérico primero
        try:
            id_num = int(id)
            resultado = coleccion.delete_one({"id": id_num})
        except ValueError:
            # Si no es numérico, eliminar por _id de MongoDB
            resultado = coleccion.delete_one({"_id": ObjectId(id)})
            
        if resultado.deleted_count:
            flash(f"Caso #{id} eliminado correctamente.", "success")
        else:
            flash(f"No se encontró el caso #{id}.", "error")
    except Exception as e:
        flash(f"Error al eliminar caso: {str(e)}", "error")
        
    return redirect(url_for('admin_dashboard'))

# =========================
# NUEVAS RUTAS PARA DASHBOARD MEJORADO
# =========================
@app.route('/admin/cambiar-prioridad/<id>', methods=['POST'])
def cambiar_prioridad(id):
    try:
        if coleccion is None:
            flash("Error de conexión a la base de datos", "error")
            return redirect(url_for('admin_dashboard'))
            
        nueva_prioridad = int(request.form.get('prioridad'))
        
        # Intentar actualizar por ID numérico primero
        try:
            id_num = int(id)
            coleccion.update_one({"id": id_num}, {"$set": {"prioridad": nueva_prioridad}})
        except ValueError:
            # Si no es numérico, actualizar por _id de MongoDB
            coleccion.update_one({"_id": ObjectId(id)}, {"$set": {"prioridad": nueva_prioridad}})
            
        flash(f"Prioridad del caso #{id} actualizada correctamente", "success")
    except Exception as e:
        flash(f"Error al actualizar prioridad: {str(e)}", "error")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/cambiar-estado/<id>', methods=['POST'])
def cambiar_estado(id):
    try:
        if coleccion is None:
            flash("Error de conexión a la base de datos", "error")
            return redirect(url_for('admin_dashboard'))
            
        nuevo_estado = request.form.get('estado')
        
        # Intentar actualizar por ID numérico primero
        try:
            id_num = int(id)
            coleccion.update_one({"id": id_num}, {"$set": {"estado": nuevo_estado}})
        except ValueError:
            # Si no es numérico, actualizar por _id de MongoDB
            coleccion.update_one({"_id": ObjectId(id)}, {"$set": {"estado": nuevo_estado}})
            
        flash(f"Estado del caso #{id} actualizado a {nuevo_estado}", "success")
    except Exception as e:
        flash(f"Error al actualizar estado: {str(e)}", "error")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/eliminar-multiples', methods=['POST'])
def eliminar_multiples_casos():
    try:
        if coleccion is None:
            flash("Error de conexión a la base de datos", "error")
            return redirect(url_for('admin_dashboard'))
            
        casos_ids = request.form.getlist('casos_seleccionados')
        if casos_ids:
            deleted_count = 0
            for caso_id in casos_ids:
                try:
                    # Intentar eliminar por ID numérico primero
                    try:
                        id_num = int(caso_id)
                        resultado = coleccion.delete_one({"id": id_num})
                    except ValueError:
                        # Si no es numérico, eliminar por _id de MongoDB
                        resultado = coleccion.delete_one({"_id": ObjectId(caso_id)})
                    
                    if resultado.deleted_count:
                        deleted_count += 1
                except Exception as e:
                    print(f"Error eliminando caso {caso_id}: {e}")
                    
            flash(f"{deleted_count} casos eliminados correctamente", "success")
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