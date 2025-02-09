from mi_app import db
from decimal import Decimal
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import json


# Clase formada debido a una relación N:M entre Videojuegos y Usuarios
videojuegos_usuarios = db.Table(
    'videojuegos_usuarios',
    db.Column('id_usuario', db.Integer, db.ForeignKey('user.id')),
    db.Column('id_videojuego', db.Integer, db.ForeignKey('videojuegos.id'))
)

# Clase formada debido a una relación N:M entre Videojuegos y Compras
compras_videojuegos = db.Table(
    'compras_videojuegos',
    db.Column('id_compra', db.Integer, db.ForeignKey('compras.id')),
    db.Column('id_videojuego', db.Integer, db.ForeignKey('videojuegos.id')),
    db.Column('precio_compra', db.Integer)
)




# A parir de aquí comenzamos con las tablas db.Model

class Videojuegos(db.Model):
    
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(255))
    precio = db.Column(db.Integer)
    imagen = db.Column(db.String(255))
    
    id_categoria = db.Column(db.Integer, db.ForeignKey('categoria.id'))
    categoria = db.relationship('Categoria', backref=db.backref('videojuegos', lazy='dynamic')) # Relación con la tabla categoria

    def __init__(self, titulo, precio, imagen, categoria):
        self.titulo = titulo
        self.precio = precio
        self.imagen = imagen
        self.categoria = categoria

    def __repr__(self):
        return f'<Videojuego {self.id}>'




class Categoria(db.Model):
 
    id = db.Column(db.Integer, primary_key=True)
    nombre_categoria = db.Column(db.String(120))

    def __init__(self, nombre_categoria):
        self.nombre_categoria = nombre_categoria
    
    def __repr__(self):
        return f'<Categoria {self.id}>'



class Detalles(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    id_usuario = db.Column(db.Integer, db.ForeignKey('user.id'))
    id_videojuego = db.Column(db.Integer, db.ForeignKey('videojuegos.id'))
    usuario = db.relationship('User', backref=db.backref('detalle_carrito', lazy='dynamic')) # Relación con la tabla user
    videojuego = db.relationship('Videojuegos', backref=db.backref('detalle_carrito', lazy='dynamic')) # Relación con la tabla videojuegos

    def __init__(self, usuario, videojuego):
        self.usuario = usuario
        self.videojuego = videojuego
     
    def __repr__(self):
        return f'<Detalles {self.id}>'



class Compras(db.Model):
  
    id = db.Column(db.Integer, primary_key=True)

    id_usuario = db.Column(db.Integer, db.ForeignKey('user.id'))
    usuario = db.relationship('User', backref=db.backref('compras', lazy='dynamic')) # Relación con la tabla user

    videojuegos = db.relationship('Videojuegos', secondary=compras_videojuegos, backref='compra') # Atributo que vamos a emplear para formar la tabla N:M de compras_videojuegos

    def __init__(self, usuario):
        self.usuario = usuario

    def __repr__(self):
        return f'<Compras {self.id}>'




class User(db.Model, UserMixin):
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    correo_electronico = db.Column(db.String(150))
    pwdhash = db.Column(db.String())

    videojuegos = db.relationship('Videojuegos', secondary=videojuegos_usuarios, backref='usuarios') # Atributo que vamos a emplear para formar la tabla N:M de videojuegos_usuarios
 
    def __init__(self, username, correo_electronico, password ):
        self.username = username
        self.correo_electronico = correo_electronico
        self.pwdhash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.pwdhash, password)


class Comentarios (db.Model):
    id = db.Column(db.Integer, primary_key=True)
    comentario = db.Column(db.String(255))

    id_usuario = db.Column(db.Integer, db.ForeignKey('user.id'))
    id_videojuego = db.Column(db.Integer, db.ForeignKey('videojuegos.id'))
    usuario = db.relationship('User', backref=db.backref('comentario', lazy='dynamic')) # Relación con la tabla user
    videojuego = db.relationship('Videojuegos', backref=db.backref('comentario', lazy='dynamic')) # Relación con la tabla videojuegos



    def __init__(self, comentario,  usuario):
        self.comentario = comentario
        self.usuario = usuario


    def __repr__(self):
        return f'<Comentario {self.id}>'