from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional
from datetime import date

class FormularioAsesoria(FlaskForm):
    # Información personal
    nombre = StringField('Nombre Completo', 
                        validators=[DataRequired(), Length(max=100)],
                        render_kw={"placeholder": "Ej: Juan Pérez"})
    
    email = StringField('Email', 
                       validators=[DataRequired(), Email()],
                       render_kw={"placeholder": "Ej: juan@email.com"})
    
    telefono = StringField('Teléfono', 
                          validators=[DataRequired(), Length(max=20)],
                          render_kw={"placeholder": "Ej: +54 11 1234-5678"})
    
    # Información del accidente
    tipo_accidente = SelectField('Tipo de Accidente', 
        choices=[
            ('', 'Seleccione el tipo de accidente'),
            ('vehicular', 'Choque entre Vehículos'),
            ('peatonal', 'Atropello a Peatón'),
            ('motocicleta', 'Accidente de Motocicleta'),
            ('transporte_publico', 'Accidente en Transporte Público')
        ],
        validators=[DataRequired()])
    
    rol_usuario = SelectField('Su rol en el accidente',
        choices=[
            ('', 'Seleccione su rol'),
            ('victima', 'Víctima / Afectado'),
            ('causante', 'Causante / Responsable')
        ],
        validators=[DataRequired()])
    
    fecha_accidente = DateField('Fecha del Accidente', 
                               validators=[DataRequired()],
                               default=date.today)
    
    # Detalles específicos
    hay_lesiones = BooleanField('¿Hubo lesiones personales o heridos?')
    hay_danos_materiales = BooleanField('¿Hubo daños materiales en los vehículos?')
    tiene_seguro = BooleanField('¿Hay seguros involucrados?')
    
    seguro_propio = StringField('Su compañía de seguro',
                               validators=[Optional(), Length(max=100)],
                               render_kw={"placeholder": "Ej: MAPFRE, SANCOR, ALLIANZ..."})
    
    seguro_contrario = StringField('Compañía de seguro del otro involucrado',
                                  validators=[Optional(), Length(max=100)],
                                  render_kw={"placeholder": "Ej: SANCOR, RÍO URUGUAY, etc."})
    
    descripcion = TextAreaField('Describa el accidente', 
        validators=[DataRequired(), Length(min=30, max=2000)],
        render_kw={
            "placeholder": "Describa en detalle cómo ocurrió el accidente, calles involucradas, testigos, daños visibles, lesiones, etc.",
            "rows": 6
        })
    
    submit = SubmitField('Solicitar Asesoría Gratuita')