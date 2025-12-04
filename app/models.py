from . import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)  # e.g. Super-Administrador, Almacenista, Consultor
    description = db.Column(db.String(200))

    users = db.relationship('User', backref='role', lazy=True)

class User(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Provider(db.Model):
    __tablename__ = 'proveedores'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    contacto = db.Column(db.String(150))
    telefono = db.Column(db.String(50))
    email = db.Column(db.String(120))

    productos = db.relationship('Product', backref='proveedor', lazy=True)

class Product(db.Model):
    __tablename__ = 'productos'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text)
    sku = db.Column(db.String(80), unique=True, nullable=False)
    cantidad = db.Column(db.Integer, default=0)
    stock_minimo = db.Column(db.Integer, default=1)
    precio_compra = db.Column(db.Float, default=0.0)
    precio_venta = db.Column(db.Float, default=0.0)
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedores.id'))

    movimientos = db.relationship(
    'InventoryMovement',
    backref='producto',
    lazy=True,
    cascade="all, delete-orphan"
)


class InventoryMovement(db.Model):
    __tablename__ = 'movimientos_inventario'
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # 'entrada' o 'salida' o 'ajuste'
    cantidad = db.Column(db.Integer, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    nota = db.Column(db.String(255))

    usuario = db.relationship('User', backref='movimientos')
