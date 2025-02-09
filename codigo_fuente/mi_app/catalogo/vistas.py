from flask  import request, jsonify, Blueprint
from mi_app import db, login_manager
from mi_app.catalogo.modelos import Videojuegos, Compras, Categoria, Detalles, User, compras_videojuegos, videojuegos_usuarios, Comentarios
from flask import render_template
from flask import flash
from flask import redirect, url_for
from flask_login import current_user, login_user, logout_user, login_required
import json
import stripe

from sqlalchemy import column,select, insert


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

catalog = Blueprint('catalog',__name__)


# Ruta para renderizar el home o index
@catalog.route('/')
@catalog.route('/home')
def home():
    datos_comentarios_python = Comentarios.query.all()

    return render_template('index.html', datos_comentarios_html = datos_comentarios_python)

# Ruta para insertar las categorías del JSON en la base de datos

@catalog.route('/insertarcategorias')
def insertar_categorias():
    with open('./mi_app/static/data/categorias.json', 'r') as datos_cat:
        datos_categorias = json.load(datos_cat)
    # Obtenemos los datos del archivo y hacemos un bucle para obtener los datos de cada categoría, en este caso están en un array

    for dato_cat in datos_categorias['categorias']:
         nueva_categoria = Categoria(
                nombre_categoria = dato_cat['nombre_categoria'] 
            )
         db.session.add(nueva_categoria)
         db.session.commit()
         # Inserta los datos a la tabla de Categoria
   
    return redirect(url_for('catalog.home'))

# Ruta para insertar los videojuegos del JSON en la base de datos

@catalog.route('/insertarvideojuegos')
def insertar_videojuegos():
    with open('./mi_app/static/data/videojuegos.json', 'r') as datos_vid:
        datos_videojuegos = json.load(datos_vid)

    # Obtenemos los datos del archivo y hacemos un bucle para obtener los datos de cada videojuego, en este caso están en un array y más datos que en la anterior ruta
    for dato_vid in datos_videojuegos:
         categoria = Categoria.query.get(dato_vid['id_categoria'])
         
         nuevo_videojuego = Videojuegos(
                titulo = dato_vid['Nombre'],
                precio = dato_vid['Precio'],
                imagen = dato_vid['imagen'],
                categoria = categoria
            )
         db.session.add(nuevo_videojuego)
         db.session.commit()
         # Inserta los datos a la tabla de Videojuegos
    return redirect(url_for('catalog.home'))


# Ruta para el tema del login
@catalog.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:        
        return redirect(url_for('catalog.home')) # Si el usuario está con la sesión iniciada , lo redirige a la página principal
    
    username = request.args.get('username')
    correo_electronico = request.args.get('correo_electronico')
    password = request.args.get('password')
    existing_user = User.query.filter_by(username=username).first()
    # Obtiene los datos y a continuación hace la comparación
    if not (existing_user and existing_user.check_password(password)):
        return render_template('login.html')

    login_user(existing_user, remember=True) # recuerda usuario al cerrar la ventana
    return redirect(url_for('catalog.home'))
    


# Ruta para el tema del registro
@catalog.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('catalog.home')) # Si el usuario está con la sesión iniciada , lo redirige a la página principal

    username = request.args.get('username')
    correo_electronico = request.args.get('correo_electronico')
    password = request.args.get('password')
    # Obtiene los datos y a continuación hace la comparación para saber si hay datos en los campos del formulario
    if (username and correo_electronico and password ):
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:            
            return render_template('login.html') # Si el usuario existe lo lleva al login
        user = User(username,correo_electronico, password)
        db.session.add(user)
        db.session.commit()
        # Inserta los datos a la tabla de User
        return redirect(url_for('catalog.login'))
    return render_template('register.html')

    
# Ruta para cerrar la sesión
@catalog.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('catalog.home'))


# Ruta de prueba para ver que se visualizan los datos
@catalog.route('/articulo_db/<id>')
@login_required
def articulo(id):
    articulo_db = Videojuegos.query.get_or_404(id)
    return render_template('articulo_individual.html', articulo_html=articulo_db)


# Ruta para poder visulizar datos en la página de artículos
@catalog.route('/articulos')
@catalog.route('/articulos/<int:page>')
@login_required
def videojuegos_paginados(page=1):
    videojuegos_python = Videojuegos.query.paginate(page=page, per_page=30) # Una paginación de 30 artículos por pagina
    detalle_db = Detalles.query.all() # Obtenermos los datos de la tabla Detalles
    usuario_actual = current_user
    favoritos = usuario_actual.videojuegos

    # Y gracias a favoritos podemos obtener los videojuegos que el usuario ha agregado a sus favoritos
    
    # Bucle para poder sumar todos los precios y así poder obtener el precio final
    precio_total=0
    for i in detalle_db:
        precio_total += i.videojuego.precio
        

    return render_template('articulos.html', videojuegos_html=videojuegos_python,  detalle_html=detalle_db, precio_total_html= precio_total, favoritos_html=favoritos) # Pasamos los parámetros a la página de artículos



# A continuación tenemos el proceso de compra
stripe.api_key = "sk_test_51Qp3ndIwJEPIdHzX87JRwkuA5Q7gqKCwzRGb6aGSnFUXWaPqMvcEa9hLu5nCXqCXgapATvsJXWgkv9MdI6Rp5LFZ00LDPfkECg" # Clave privada de nuestra cuenta de Stripe


# Ruta para poder realizar la compra
@catalog.route('/proceso_compra/<int:total>', methods=['GET'])
@login_required

def proceso_compra(total):

    try:

    
        intent = stripe.PaymentIntent.create(

            amount=total*100, 

    
            currency="eur",

            payment_method_types=["card"],

        ) # Creamos el pago, multiplicamos por 100 para pasarlo de céntimos a euros y decimos que la compra será realizada en euros
        dato_compra = Compras(current_user)
        db.session.add(dato_compra)
        db.session.commit()
        # Insertamos los datos en la tabla de Compras

        detalles_carrito = Detalles.query.filter_by(id_usuario=current_user.id).all()  # Obtenemos datos de la tabla detalles para poder trabajar con estos


        for detalle in detalles_carrito:

            videojuego_python = detalle.videojuego 
            db.session.execute(
                compras_videojuegos.insert().values(

                    id_compra=dato_compra.id,

                    id_videojuego=videojuego_python.id,

                    precio_compra=videojuego_python.precio  

                )

            )
            db.session.commit()
        
            # Al ser una tabla N:M tenemos que hacer la insercción de la siguiente manera y accediendo mediante los backref a su vez obtenemos los datos que nos interesan

        return redirect(url_for('catalog.vaciar_carro'))

    except Exception as e:

        print(f'Error al procesar el pago: {str(e)}')
        

    return redirect(url_for('catalog.home'))

# Ruta para insertar los productos en el carrito
@catalog.route('/insertar_datos_detalles/<id_usuario>/<id_videojuego>')
@login_required
def metodo_insertar_carrito(id_usuario, id_videojuego): 
    detalle_usuario = User.query.filter_by(id=id_usuario).first() # Obtenemos el id del usuario meidante el parámetro de la ruta
    detalle_videojuego = Videojuegos.query.filter_by(id=id_videojuego).first() # Obtenemos el id del videojuego meidante el parámetro de la ruta

    existe_detalle = Detalles.query.filter_by(id_usuario=id_usuario, id_videojuego=id_videojuego).first()

    # Hemos obtenido los valores para compararlos y ver si el usuario ya tiene el videojuego en el carrito o no, si existe no se añade pero si no está en el carrito si
    if existe_detalle:
        return redirect(url_for('catalog.home'))
    

    dato_detalle_final = Detalles(detalle_usuario, detalle_videojuego)
    db.session.add(dato_detalle_final)
    db.session.commit()

    return redirect(url_for('catalog.home'))


# Ruta para vaciar el carrito
@catalog.route('/vaciar_carrito')
@login_required
def vaciar_carro():
 
    borrar_items = Detalles.query.filter_by(id_usuario=current_user.id).all() # Obtenemos todos los videojuegos que el usuario tiene en el carrito y los eliminamos
    for item in borrar_items:
        db.session.delete(item)

    db.session.commit()

    return redirect(url_for('catalog.home'))

# Ruta para vaciar la lista de favoritos
@catalog.route('/vaciar_favoritos')
@login_required
def vaciar_fav():
    usuario_actual = current_user
    favoritos = usuario_actual.videojuegos

    # Obtenemos todos los videojuegos mediante el atributo backref que el usuario tiene en la lista de favoritos y los eliminamos

    for favorito in favoritos:
        usuario_actual.videojuegos.clear() # al ser un db.table y no un db.model tengo que borrarlo con el método clear

    db.session.commit() 
    return redirect(url_for('catalog.home'))


# Ruta para borrar 1 solo videojuego del carrito
@catalog.route('/vaciar_individual_detalles/<int:detalle_id>')
@login_required
def vaciar_individual_detalles(detalle_id):

    usuario_actual = current_user

    detalle_a_eliminar = Detalles.query.filter_by(id=detalle_id, id_usuario=usuario_actual.id).first() # Obtenemos el dato del videojuego que el usuario quiere quitar y lo eliminamos

  
    db.session.delete(detalle_a_eliminar)
    db.session.commit()


    return redirect(url_for('catalog.home'))

# Ruta para borrar 1 solo videojuego de la lista de favoritos
@catalog.route('/vaciar_individual_fav')
@login_required
def vaciar_individual_favoritos():
    usuario_actual = current_user
    favoritos = usuario_actual.videojuegos

    # Obtenemos el dato del videojuego que el usuario quiere quitar mediante el atributo backref y lo eliminamos

    for favorito in favoritos:
        usuario_actual.videojuegos.remove(favorito) # al ser un db.table y no un db.model tengo que borrarlo con el método remove para borrar solo ese

    db.session.commit() 
    return redirect(url_for('catalog.home'))


# Ruta para insertar un videojuego en la lista de favoritos
@catalog.route('/insertar_datos_favoritos/<id_usuario>/<id_videojuego>')
@login_required

def metodo_insertar_favoritos(id_usuario, id_videojuego):

    fav_usuario = User.query.filter_by(id=id_usuario).first() # Obtenemos el id del usuario meidante el parámetro de la ruta

    fav_videojuego = Videojuegos.query.filter_by(id=id_videojuego).first() # Obtenemos el id del videojuego meidante el parámetro de la ruta

    existe_favorito = db.session.query(videojuegos_usuarios).filter_by(id_usuario=fav_usuario.id, id_videojuego=fav_videojuego.id).first()

    # Hemos obtenido los valores para compararlos y ver si el usuario ya tiene el videojuego en la lista de favoritos o no, si existe no se añade pero si no está en la lista si

    if existe_favorito:

       return redirect(url_for('catalog.home'))
    
    else:
        db.session.execute(

            videojuegos_usuarios.insert().values(

                id_usuario=fav_usuario.id,

                id_videojuego=fav_videojuego.id

            )

        )

        db.session.commit()
        # Al ser un db.table tenemos que introducir datos de esta manera de arriba
    return redirect(url_for('catalog.home'))


# Ruta para insertar datos a la tabla de Comentarios
@catalog.route('/comentarios', methods=['GET', 'POST'])
def comentario():
    if current_user.is_authenticated:

        comentario = request.args.get('comentario') # Obtenemos el comentario del usuario que ha escrito en un input de formulario


        if comentario:
            comentario_insertar = Comentarios(comentario,current_user)
            db.session.add(comentario_insertar)
            db.session.commit()
            # Si el usuario ha introducido un comentario se añade a la base de datos y se vuelve a la página de inicio
            return redirect(url_for('catalog.home'))
    return render_template('catalog.home')


# Ruta para obtener datos de la tabla del historial y mandarla a la página de historial
@catalog.route('/leer_historial')
@login_required
def metodo_mostrar_historial():
    usuario_actual = current_user
   
    compras = usuario_actual.compras.all()

    # Obtenemos los datos que nos interesan de la tabla Compras gracias al backref del usuario
    detalles_historial_python = {} # Para retener y mandar a la página los datos hemos utilizado un diccionario

    for compra in compras:

        for videojuego in compra.videojuegos:
            obtener_dato = db.session.query(compras_videojuegos).filter_by(id_compra=compra.id, id_videojuego=videojuego.id).first()
            # Hacemos una consulta teniendo en cuenta el id de la compra y el del videojuego para obtener el precio

            if obtener_dato:
                detalles_historial_python[videojuego.id] = {
                    'titulo': videojuego.titulo,
                    'precio': obtener_dato.precio_compra,
                    'imagen': videojuego.imagen
                    
                }
                # Gracias al id del videojuego podemos acceder a su título, imagen, precio... ya que estos son necesarios a la hora de visualizar la página del historial

    return render_template('historialcompras.html', detalles_historial_html=detalles_historial_python) # Mandamos los datos a la página del historial