from app import create_app, db
from app.models import Role, User, Provider, Product, InventoryMovement

app = create_app()

def seed():
    with app.app_context():
        db.drop_all()
        db.create_all()

        # Roles
        r_admin = Role(name='Super-Administrador', description='Acceso total')
        r_alm = Role(name='Almacenista', description='Gestiona productos y movimientos')
        r_cons = Role(name='Consultor', description='Solo lectura')
        db.session.add_all([r_admin, r_alm, r_cons])
        db.session.commit()

        # Usuarios
        u1 = User(username='admin', email='admin@example.com', role_id=r_admin.id)
        u1.set_password('admin123')
        u2 = User(username='almacen', email='almacen@example.com', role_id=r_alm.id)
        u2.set_password('almacen123')
        u3 = User(username='consulta', email='consulta@example.com', role_id=r_cons.id)
        u3.set_password('consulta123')
        db.session.add_all([u1,u2,u3])
        db.session.commit()

        # Proveedores
        p1 = Provider(nombre='Proveedor A', contacto='Juan', telefono='999111222', email='provA@ejemplo.com')
        p2 = Provider(nombre='Proveedor B', contacto='María', telefono='999333444', email='provB@ejemplo.com')
        db.session.add_all([p1,p2])
        db.session.commit()

        # Productos
        prod1 = Product(nombre='Camiseta', descripcion='Algodón', sku='SKU-001', cantidad=20, stock_minimo=5, precio_compra=10, precio_venta=15, proveedor_id=p1.id)
        prod2 = Product(nombre='Pantalón', descripcion='Jean', sku='SKU-002', cantidad=3, stock_minimo=5, precio_compra=20, precio_venta=30, proveedor_id=p2.id)
        db.session.add_all([prod1, prod2])
        db.session.commit()

        # Movimientos iniciales
        m1 = InventoryMovement(producto_id=prod1.id, tipo='entrada', cantidad=20, usuario_id=u1.id, nota='Carga inicial')
        m2 = InventoryMovement(producto_id=prod2.id, tipo='entrada', cantidad=3, usuario_id=u1.id, nota='Carga inicial')
        db.session.add_all([m1,m2])
        db.session.commit()

        print("Seed completo.")

if __name__ == '__main__':
    seed()
