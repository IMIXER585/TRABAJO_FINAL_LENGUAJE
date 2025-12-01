from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, login_required, logout_user, current_user
from . import db
from .models import User, Role, Product, Provider, InventoryMovement
from .forms import LoginForm, RegisterForm, ProductForm, ProviderForm, MovementForm
from .utils import roles_required
from datetime import datetime

bp = Blueprint('main', __name__)

# --- AUTH ---
@bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('main.login'))

@bp.route('/login', methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Bienvenido, {}'.format(user.username), 'success')
            return redirect(url_for('main.dashboard'))
        flash('Usuario o contraseña incorrectos', 'danger')
    return render_template('login.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada', 'info')
    return redirect(url_for('main.login'))

@bp.route('/register', methods=['GET','POST'])
@login_required
@roles_required('Super-Administrador')
def register():
    form = RegisterForm()
    # llenar choices con roles
    form.role.choices = [(r.id, r.name) for r in Role.query.all()]
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, role_id=form.role.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Usuario creado', 'success')
        return redirect(url_for('main.users_list'))
    return render_template('register.html', form=form)

@bp.route('/users')
@login_required
@roles_required('Super-Administrador')
def users_list():
    users = User.query.all()
    return render_template('users_list.html', users=users)

# --- DASHBOARD ---
@bp.route('/dashboard')
@login_required
def dashboard():
    total_products = Product.query.count()
    total_value = sum([p.cantidad * (p.precio_compra or 0) for p in Product.query.all()])
    low_stock = Product.query.filter(Product.cantidad <= Product.stock_minimo).order_by(Product.cantidad.asc()).limit(5).all()
    return render_template('dashboard.html', total_products=total_products, total_value=total_value, low_stock=low_stock)

# --- PRODUCTS CRUD ---
@bp.route('/productos')
@login_required
def productos_list():
    productos = Product.query.all()
    return render_template('productos_list.html', productos=productos)

@bp.route('/producto/nuevo', methods=['GET','POST'])
@login_required
@roles_required('Super-Administrador','Almacenista')
def producto_nuevo():
    form = ProductForm()
    form.proveedor_id.choices = [(0,'-- Ninguno --')] + [(p.id,p.nombre) for p in Provider.query.all()]
    if form.validate_on_submit():
        proveedor_id = form.proveedor_id.data or None
        if proveedor_id == 0:
            proveedor_id = None
        prod = Product(
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            sku=form.sku.data,
            cantidad=form.cantidad.data,
            stock_minimo=form.stock_minimo.data,
            precio_compra=form.precio_compra.data or 0,
            precio_venta=form.precio_venta.data or 0,
            proveedor_id=proveedor_id
        )
        db.session.add(prod)
        db.session.commit()
        # crear movimiento de entrada si cantidad > 0
        if prod.cantidad and prod.cantidad > 0:
            mov = InventoryMovement(producto_id=prod.id, tipo='entrada', cantidad=prod.cantidad, usuario_id=current_user.id, nota='Creación de producto')
            db.session.add(mov)
            db.session.commit()
        flash('Producto creado', 'success')
        return redirect(url_for('main.productos_list'))
    return render_template('producto_form.html', form=form)

@bp.route('/producto/editar/<int:id>', methods=['GET','POST'])
@login_required
@roles_required('Super-Administrador','Almacenista')
def producto_editar(id):
    prod = Product.query.get_or_404(id)
    form = ProductForm(obj=prod)
    form.proveedor_id.choices = [(0,'-- Ninguno --')] + [(p.id,p.nombre) for p in Provider.query.all()]
    if request.method == 'GET':
        form.proveedor_id.data = prod.proveedor_id or 0
    if form.validate_on_submit():
        old_qty = prod.cantidad
        prod.nombre = form.nombre.data
        prod.descripcion = form.descripcion.data
        prod.sku = form.sku.data
        prod.cantidad = form.cantidad.data
        prod.stock_minimo = form.stock_minimo.data
        prod.precio_compra = form.precio_compra.data or 0
        prod.precio_venta = form.precio_venta.data or 0
        proveedor_id = form.proveedor_id.data or None
        if proveedor_id == 0:
            proveedor_id = None
        prod.proveedor_id = proveedor_id
        db.session.commit()

        # si cambia la cantidad -> crear movimiento
        if prod.cantidad != old_qty:
            tipo = 'entrada' if prod.cantidad > old_qty else 'salida'
            cant = abs(prod.cantidad - old_qty)
            mov = InventoryMovement(producto_id=prod.id, tipo=tipo, cantidad=cant, usuario_id=current_user.id, nota='Ajuste en edición')
            db.session.add(mov)
            db.session.commit()

        flash('Producto actualizado', 'success')
        return redirect(url_for('main.productos_list'))
    return render_template('producto_form.html', form=form, producto=prod)

@bp.route('/producto/eliminar/<int:id>', methods=['POST'])
@login_required
@roles_required('Super-Administrador')
def producto_eliminar(id):
    prod = Product.query.get_or_404(id)
    db.session.delete(prod)
    db.session.commit()
    flash('Producto eliminado', 'info')
    return redirect(url_for('main.productos_list'))

# --- PROVEEDORES CRUD ---
@bp.route('/proveedores')
@login_required
def proveedores_list():
    proveedores = Provider.query.all()
    return render_template('proveedores_list.html', proveedores=proveedores)

@bp.route('/proveedor/nuevo', methods=['GET','POST'])
@login_required
@roles_required('Super-Administrador')
def proveedor_nuevo():
    form = ProviderForm()
    if form.validate_on_submit():
        prov = Provider(nombre=form.nombre.data, contacto=form.contacto.data, telefono=form.telefono.data, email=form.email.data)
        db.session.add(prov)
        db.session.commit()
        flash('Proveedor creado', 'success')
        return redirect(url_for('main.proveedores_list'))
    return render_template('proveedor_form.html', form=form)

@bp.route('/proveedor/editar/<int:id>', methods=['GET','POST'])
@login_required
@roles_required('Super-Administrador')
def proveedor_editar(id):
    prov = Provider.query.get_or_404(id)
    form = ProviderForm(obj=prov)
    if form.validate_on_submit():
        prov.nombre = form.nombre.data
        prov.contacto = form.contacto.data
        prov.telefono = form.telefono.data
        prov.email = form.email.data
        db.session.commit()
        flash('Proveedor actualizado', 'success')
        return redirect(url_for('main.proveedores_list'))
    return render_template('proveedor_form.html', form=form, proveedor=prov)

@bp.route('/proveedor/eliminar/<int:id>', methods=['POST'])
@login_required
@roles_required('Super-Administrador')
def proveedor_eliminar(id):
    prov = Provider.query.get_or_404(id)
    db.session.delete(prov)
    db.session.commit()
    flash('Proveedor eliminado', 'info')
    return redirect(url_for('main.proveedores_list'))

# --- MOVIMIENTOS ---
@bp.route('/movimientos', methods=['GET','POST'])
@login_required
def movimientos_list():
    form = MovementForm()
    form.producto_id.choices = [(p.id, p.nombre) for p in Product.query.order_by(Product.nombre).all()]
    # filtros
    tipo = request.args.get('tipo')
    fecha_inicio = request.args.get('inicio')
    fecha_fin = request.args.get('fin')
    query = InventoryMovement.query
    if tipo:
        query = query.filter_by(tipo=tipo)
    if fecha_inicio:
        try:
            dt = datetime.fromisoformat(fecha_inicio)
            query = query.filter(InventoryMovement.fecha >= dt)
        except:
            pass
    if fecha_fin:
        try:
            dt = datetime.fromisoformat(fecha_fin)
            query = query.filter(InventoryMovement.fecha <= dt)
        except:
            pass
    movimientos = query.order_by(InventoryMovement.fecha.desc()).all()
    return render_template('movimientos_list.html', movimientos=movimientos, form=form)

@bp.route('/movimiento/nuevo', methods=['POST'])
@login_required
@roles_required('Super-Administrador','Almacenista')
def movimiento_nuevo():
    form = MovementForm()
    form.producto_id.choices = [(p.id, p.nombre) for p in Product.query.order_by(Product.nombre).all()]
    if form.validate_on_submit():
        prod = Product.query.get(form.producto_id.data)
        if not prod:
            flash('Producto no encontrado', 'danger')
            return redirect(url_for('main.movimientos_list'))
        tipo = form.tipo.data
        cantidad = form.cantidad.data
        # ajustar stock
        if tipo == 'entrada':
            prod.cantidad += cantidad
        elif tipo == 'salida':
            if prod.cantidad < cantidad:
                flash('Stock insuficiente', 'danger')
                return redirect(url_for('main.movimientos_list'))
            prod.cantidad -= cantidad
        else:  # ajuste
            # para ajuste asumimos que nota indica + o -; pero aquí pedimos cantidad absoluta -> realízalo como ajuste negativo o positivo por cantidad en nota
            # por simplicidad, preguntamos si la nota contiene '-' para reducir; pero el form no trae eso. Haremos ajuste sumando (podrías mejorar).
            prod.cantidad += cantidad

        mov = InventoryMovement(producto_id=prod.id, tipo=tipo, cantidad=cantidad, usuario_id=current_user.id, nota=form.nota.data)
        db.session.add(mov)
        db.session.commit()
        flash('Movimiento registrado', 'success')
    else:
        flash('Error en el formulario', 'danger')
    return redirect(url_for('main.movimientos_list'))

# --- REPORTES ---
@bp.route('/reportes/bajo_stock')
@login_required
def reportes_bajo_stock():
    productos = Product.query.filter(Product.cantidad <= Product.stock_minimo).order_by(Product.cantidad.asc()).all()
    return render_template('reportes_low_stock.html', productos=productos)

@bp.route('/reportes/movimientos')
@login_required
def reportes_movimientos():
    # reutiliza filtros en movimientos_list; aquí devolvemos todos para reporte
    tipo = request.args.get('tipo')
    query = InventoryMovement.query
    if tipo:
        query = query.filter_by(tipo=tipo)
    movimientos = query.order_by(InventoryMovement.fecha.desc()).all()
    return render_template('reportes_movimientos.html', movimientos=movimientos)
@bp.route('/user/editar/<int:id>', methods=['GET','POST'])
@login_required
@roles_required('Super-Administrador')
def user_edit(id):
    user = User.query.get_or_404(id)
    form = RegisterForm(obj=user)

    # cargar roles
    form.role.choices = [(r.id, r.name) for r in Role.query.all()]

    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.role_id = form.role.data

        if form.password.data:  # si quiere cambiar contraseña
            user.set_password(form.password.data)

        db.session.commit()
        flash('Usuario actualizado correctamente', 'success')
        return redirect(url_for('main.users_list'))

    return render_template('register.html', form=form, edit=True, user=user)




@bp.route('/user/eliminar/<int:id>', methods=['POST'])
@login_required
@roles_required('Super-Administrador')
def user_delete(id):
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    flash('Usuario eliminado', 'info')
    return redirect(url_for('main.users_list'))

