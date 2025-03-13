from flask import Flask, request, render_template, redirect, url_for, session, flash
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail as SendGridMail
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask_mail import Mail, Message
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
bcrypt = Bcrypt(app)

# Clave secreta para sesiones
app.secret_key = os.getenv('FLASK_SECRET_KEY', '123')

# Configuración de MongoDB
MONGO_URI = os.getenv('MONGO_URI', "mongodb://localhost:27017/")
client = MongoClient("aqui colocan la contraseña creada por mongodb de tu servidro")
db = client['nombre de la base de datos']  # Base de datos
collection = db['nombre de su coleccion']  # Colección de usuarios

# Configuración de SendGrid
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
SENDGRID_SENDER_EMAIL = os.getenv('SENDGRID_SENDER_EMAIL')

# Configuración de Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = app.config['MAIL_USERNAME']

mail = Mail(app)

# Serializador para tokens de recuperación de contraseña
serializer = Serializer(app.secret_key, salt='password-reset-salt')

# 📧 Función para enviar correos con SendGrid
def enviar_email(destinatario, asunto, cuerpo):
    mensaje = SendGridMail(
        from_email=SENDGRID_SENDER_EMAIL,
        to_emails=destinatario,
        subject=asunto,
        html_content=cuerpo
    )
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        sg.send(mensaje)
        print(f"✅ Correo enviado a {destinatario}")
    except Exception as e:
        print(f"❌ Error al enviar el correo: {e}")

# 🔹 Página principal
@app.route('/')
def home():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('pagina_principal'))

# 🔹 Registro de usuarios
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        usuario = request.form['usuario']
        email = request.form['email']
        contrasena = request.form['contrasena']

        if collection.find_one({'email': email}):
            flash("El correo ya está registrado.", "danger")
            return redirect(url_for('registro'))

        hashed_password = bcrypt.generate_password_hash(contrasena).decode('utf-8')

        collection.insert_one({
            'usuario': usuario,
            'email': email,
            'contrasena': hashed_password
        })
        
        session['usuario'] = usuario
        return redirect(url_for('pagina_principal'))

    return render_template('register.html')

# 🔹 Inicio de sesión
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        contrasena = request.form['contrasena']

        user = collection.find_one({'usuario': usuario})

        if user and bcrypt.check_password_hash(user['contrasena'], contrasena):
            session['usuario'] = usuario
            flash("Inicio de sesión exitoso.", "success")
            return redirect(url_for('pagina_principal'))
        else:
            flash("Usuario o contraseña incorrectos.", "danger")

    return render_template('login.html')

# 🔹 Página principal después del login
@app.route('/pagina_principal')
def pagina_principal():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', usuario=session['usuario'])

# 🔹 Cerrar sesión
@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('login'))

# 🔹 Perfil del usuario
@app.route('/mi_perfil')
def mi_perfil():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    usuario = session['usuario']
    user_data = collection.find_one({'usuario': usuario})
    return render_template('mi_perfil.html', usuario=user_data['usuario'], email=user_data['email'])

# 🔹 Recuperar contraseña
@app.route('/recuperar_contrasena', methods=['GET', 'POST'])
def recuperar_contrasena():
    if request.method == 'POST':
        email = request.form['email']
        usuario = collection.find_one({'email': email})

        if usuario:
            token = serializer.dumps(email, salt='password-reset-salt')
            enlace = url_for('restablecer_contrasena', token=token, _external=True)
            enviar_email(email, "Recuperación de contraseña", f"<p>Para restablecer tu contraseña, haz clic <a href='{enlace}'>aquí</a></p>")
            flash("Te enviamos un correo para recuperar tu contraseña.", "success")
        else:
            flash("El correo no está registrado.", "danger")

    return render_template('recuperar_contrasena.html')

# 🔹 Restablecer contraseña
@app.route('/restablecer_contrasena/<token>', methods=['GET', 'POST'])
def restablecer_contrasena(token):
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=3600)
    except:
        flash("El enlace ha caducado o es inválido.", "danger")
        return redirect(url_for('recuperar_contrasena'))

    if request.method == 'POST':
        nueva_contrasena = request.form['nueva_contrasena']
        hashed_password = bcrypt.generate_password_hash(nueva_contrasena).decode('utf-8')
        collection.update_one({'email': email}, {'$set': {'contrasena': hashed_password}})
        flash("Tu contraseña ha sido restablecida.", "success")
        return redirect(url_for('login'))

    return render_template('restablecer_contrasena.html')

# 🔹 Enviar correo de contacto
@app.route('/send_email', methods=['POST'])
def send_email():
    try:
        nombre = request.form['nombre']
        correo = request.form['correo']
        mensaje = request.form['mensaje']

        msg = Message('Nuevo mensaje de contacto',
                      sender=app.config['MAIL_USERNAME'],
                      recipients=[app.config['MAIL_USERNAME']])
        msg.body = f"Nombre: {nombre}\nCorreo: {correo}\nMensaje: {mensaje}"

        mail.send(msg)
        return "success"  # 🔹 Enviar solo una respuesta simple para evitar duplicados
    except Exception as e:
        print(f"❌ Error: {e}")
        return "error"  # 🔹 Enviar error si algo falla
  # ✅ Se almacena en sesión

    return redirect(url_for('pagina_principal'))  # ✅ Redirige para evitar reenvío del formulario


if __name__ == '__main__':
    app.run(debug=True)
