from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, FloatField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, NumberRange, Optional

class LoginForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Iniciar sesión')

class RegisterForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired(), Length(3,80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired(), Length(6,128)])
    password2 = PasswordField('Repetir Contraseña', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Rol', coerce=int)
    submit = SubmitField('Registrar')

class ProductForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired()])
    descripcion = TextAreaField('Descripción', validators=[Optional()])
    sku = StringField('SKU', validators=[DataRequired()])
    cantidad = IntegerField('Cantidad', validators=[DataRequired(), NumberRange(min=0)])
    stock_minimo = IntegerField('Stock mínimo', default=1)
    precio_compra = FloatField('Precio de compra', validators=[Optional()])
    precio_venta = FloatField('Precio de venta', validators=[Optional()])
    proveedor_id = SelectField('Proveedor', coerce=int, validators=[Optional()])
    submit = SubmitField('Guardar')

class ProviderForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired()])
    contacto = StringField('Contacto', validators=[Optional()])
    telefono = StringField('Teléfono', validators=[Optional()])
    email = StringField('Email', validators=[Optional(), Email()])
    submit = SubmitField('Guardar')

class MovementForm(FlaskForm):
    producto_id = SelectField('Producto', coerce=int, validators=[DataRequired()])
    tipo = SelectField('Tipo', choices=[('entrada','Entrada'),('salida','Salida'),('ajuste','Ajuste')], validators=[DataRequired()])
    cantidad = IntegerField('Cantidad', validators=[DataRequired(), NumberRange(min=1)])
    nota = StringField('Nota', validators=[Optional()])
    submit = SubmitField('Registrar Movimiento')
