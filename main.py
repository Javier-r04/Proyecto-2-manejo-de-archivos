import os
import json
import uuid
from datetime import datetime
import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog

DATA_DIR = "fat_data"
MAX_BLOCK_SIZE = 20

def asegurar_carpetas():
    os.makedirs(DATA_DIR, exist_ok=True)

def fecha_actual():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def hash_contraseña(pwd):
    return str(sum(ord(c) for c in pwd))

def archivo_usuarios():
    return os.path.join(DATA_DIR, "usuarios.json")

def cargar_usuarios():
    asegurar_carpetas()
    if not os.path.exists(archivo_usuarios()):
        with open(archivo_usuarios(), 'w', encoding='utf-8') as f:
            json.dump([], f)
    with open(archivo_usuarios(), 'r', encoding='utf-8') as f:
        return json.load(f)

def guardar_usuarios(usuarios):
    with open(archivo_usuarios(), 'w', encoding='utf-8') as f:
        json.dump(usuarios, f, indent=2)

def registrar_usuario(usuario, contraseña):
    usuarios = cargar_usuarios()
    for u in usuarios:
        if u['usuario'] == usuario:
            return False
    usuarios.append({'usuario': usuario, 'contraseña': hash_contraseña(contraseña)})
    guardar_usuarios(usuarios)
    carpeta_usuario = os.path.join(DATA_DIR, usuario)
    os.makedirs(os.path.join(carpeta_usuario, 'bloques'), exist_ok=True)
    with open(os.path.join(carpeta_usuario, 'tabla_fat.json'), 'w', encoding='utf-8') as f:
        json.dump([], f)
    return True

def iniciar_sesion(usuario, contraseña):
    usuarios = cargar_usuarios()
    for u in usuarios:
        if u['usuario'] == usuario and u['contraseña'] == hash_contraseña(contraseña):
            return True
    return False

def ruta_fat(usuario):
    return os.path.join(DATA_DIR, usuario, 'tabla_fat.json')

def ruta_bloques(usuario):
    return os.path.join(DATA_DIR, usuario, 'bloques')

def cargar_fat(usuario):
    with open(ruta_fat(usuario), 'r', encoding='utf-8') as f:
        return json.load(f)

def guardar_fat(usuario, fat):
    with open(ruta_fat(usuario), 'w', encoding='utf-8') as f:
        json.dump(fat, f, indent=2)

def crear_bloques(usuario, contenido):
    carpeta = ruta_bloques(usuario)
    os.makedirs(carpeta, exist_ok=True)
    bloques = []
    for i in range(0, len(contenido), MAX_BLOCK_SIZE):
        parte = contenido[i:i+MAX_BLOCK_SIZE]
        id_bloque = str(uuid.uuid4()) + '.json'
        ruta = os.path.join(carpeta, id_bloque)
        bloques.append((ruta, parte))
    for i, (ruta, parte) in enumerate(bloques):
        siguiente = os.path.basename(bloques[i+1][0]) if i < len(bloques)-1 else None
        fin = (i == len(bloques)-1)
        datos = {"datos": parte, "siguiente_archivo": siguiente, "eof": fin}
        with open(ruta, 'w', encoding='utf-8') as f:
            json.dump(datos, f, indent=2)
    return os.path.basename(bloques[0][0]) if bloques else None

def leer_bloques(usuario, inicio):
    contenido = ""
    carpeta = ruta_bloques(usuario)
    actual = os.path.join(carpeta, inicio)
    while os.path.exists(actual):
        with open(actual, 'r', encoding='utf-8') as f:
            datos = json.load(f)
        contenido += datos['datos']
        if datos['eof']:
            break
        actual = os.path.join(carpeta, datos['siguiente_archivo'])
    return contenido

def eliminar_bloques(usuario, inicio):
    carpeta = ruta_bloques(usuario)
    actual = os.path.join(carpeta, inicio)
    while os.path.exists(actual):
        with open(actual, 'r', encoding='utf-8') as f:
            datos = json.load(f)
        siguiente = datos.get('siguiente_archivo')
        try:
            os.remove(actual)
        except:
            break
        if not siguiente:
            break
        actual = os.path.join(carpeta, siguiente)

class AplicacionFAT:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulador FAT - Modo Oscuro")
        self.root.geometry("900x600")
        self.root.configure(bg="black")
        self.usuario = None
        self.inicio_sesion()

    def limpiar_ventana(self):
        for w in self.root.winfo_children():
            w.destroy()

    def limpiar_panel(self):
        if hasattr(self, 'texto'):
            self.texto.delete(1.0, tk.END)

    def inicio_sesion(self):
        self.limpiar_ventana()
        self.root.configure(bg="black")
        tk.Label(self.root, text="Inicio de Sesión", font=('Arial', 16), bg="black", fg="white").pack(pady=10)
        tk.Label(self.root, text="Usuario:", bg="black", fg="white").pack()
        entrada_usuario = tk.Entry(self.root, bg="#333", fg="white", insertbackground="white")
        entrada_usuario.pack()
        tk.Label(self.root, text="Contraseña:", bg="black", fg="white").pack()
        entrada_contraseña = tk.Entry(self.root, show='*', bg="#333", fg="white", insertbackground="white")
        entrada_contraseña.pack()

        def login():
            u = entrada_usuario.get().strip()
            p = entrada_contraseña.get().strip()
            if iniciar_sesion(u, p):
                self.usuario = u
                self.menu_principal()
            else:
                messagebox.showerror("Error", "Usuario o contraseña incorrectos.")

        def registrar():
            u = entrada_usuario.get().strip()
            p = entrada_contraseña.get().strip()
            if registrar_usuario(u, p):
                messagebox.showinfo("Registro", f"Usuario '{u}' creado correctamente.")
            else:
                messagebox.showerror("Error", "El usuario ya existe.")

        tk.Button(self.root, text="Iniciar Sesión", command=login, bg="#007ACC", fg="white", width=20).pack(pady=5)
        tk.Button(self.root, text="Registrarse", command=registrar, bg="#444", fg="white", width=20).pack(pady=5)

    def menu_principal(self):
        self.limpiar_ventana()
        self.root.configure(bg="black")
        tk.Label(self.root, text=f"Usuario activo: {self.usuario}", font=('Arial', 14), bg="black", fg="white").pack(pady=5)
        marco_izq = tk.Frame(self.root, width=250, bg="black")
        marco_izq.pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=8)
        botones = [
            ("Crear archivo", self.crear_archivo, "#007ACC"),
            ("Cargar archivo .txt", self.cargar_txt, "#007ACC"),
            ("Listar archivos", self.listar_archivos, "#444"),
            ("Ver papelera", self.ver_papelera, "#444"),
            ("Abrir archivo", self.abrir_archivo, "#555"),
            ("Modificar archivo", self.modificar_archivo, "#555"),
            ("Eliminar archivo", self.eliminar_archivo, "#880000"),
            ("Recuperar archivo", self.recuperar_archivo, "#006600"),
            ("Cerrar sesión", self.cerrar_sesion, "#222")
        ]
        for t, c, color in botones:
            tk.Button(marco_izq, text=t, width=25, command=c, bg=color, fg="white", activebackground="#222", activeforeground="white", relief="flat", font=('Arial', 10, 'bold')).pack(pady=4)
        marco_der = tk.Frame(self.root, bg="black")
        marco_der.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)
        self.texto = tk.Text(marco_der, bg="#111", fg="white", insertbackground="white", relief="flat")
        self.texto.pack(expand=True, fill=tk.BOTH)
        self.registro(f"Sesión iniciada: {self.usuario}")

    def registro(self, msg):
        ts = datetime.now().strftime('%H:%M:%S')
        self.texto.insert(tk.END, f"[{ts}] {msg}\n")
        self.texto.see(tk.END)

    def cerrar_sesion(self):
        self.usuario = None
        self.inicio_sesion()

    def listar_archivos(self):
        self.limpiar_panel()
        fat = cargar_fat(self.usuario)
        activos = [f for f in fat if not f.get('papelera')]
        if not activos:
            self.registro("No hay archivos activos.")
            return
        self.registro("Archivos activos:")
        for e in activos:
            self.registro(f" - {e['nombre']} (tamaño={e['cantidad_caracteres']})")

    def crear_archivo(self):
        self.limpiar_panel()
        nombre = simpledialog.askstring("Crear", "Nombre del archivo:", parent=self.root)
        if not nombre:
            return
        contenido = simpledialog.askstring("Contenido", "Escribe el contenido:", parent=self.root)
        if contenido is None:
            return
        fat = cargar_fat(self.usuario)
        if any(f['nombre'] == nombre for f in fat):
            messagebox.showerror("Error", "Ya existe un archivo con ese nombre.")
            return
        inicio = crear_bloques(self.usuario, contenido)
        entrada = {
            'nombre': nombre,
            'ruta_datos': inicio,
            'papelera': False,
            'cantidad_caracteres': len(contenido),
            'fecha_creacion': fecha_actual(),
            'fecha_modificacion': fecha_actual(),
            'fecha_eliminacion': None
        }
        fat.append(entrada)
        guardar_fat(self.usuario, fat)
        self.registro(f"Archivo '{nombre}' creado correctamente.")

    def cargar_txt(self):
        self.limpiar_panel()
        ruta = filedialog.askopenfilename(filetypes=[('Archivos de texto', '*.txt')])
        if not ruta:
            return
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()
        nombre = os.path.basename(ruta)
        fat = cargar_fat(self.usuario)
        if any(f['nombre'] == nombre for f in fat):
            messagebox.showerror("Error", "Ya existe un archivo con ese nombre.")
            return
        inicio = crear_bloques(self.usuario, contenido)
        entrada = {
            'nombre': nombre,
            'ruta_datos': inicio,
            'papelera': False,
            'cantidad_caracteres': len(contenido),
            'fecha_creacion': fecha_actual(),
            'fecha_modificacion': fecha_actual(),
            'fecha_eliminacion': None
        }
        fat.append(entrada)
        guardar_fat(self.usuario, fat)
        self.registro(f"Archivo .txt '{nombre}' cargado exitosamente.")

    def abrir_archivo(self):
        self.limpiar_panel()
        nombre = simpledialog.askstring("Abrir", "Nombre del archivo:", parent=self.root)
        if not nombre:
            return
        fat = cargar_fat(self.usuario)
        entrada = next((f for f in fat if f['nombre'] == nombre and not f.get('papelera')), None)
        if not entrada:
            messagebox.showerror("Error", "Archivo no encontrado o en papelera.")
            return
        contenido = leer_bloques(self.usuario, entrada['ruta_datos'])
        self.registro(f"\n--- {nombre} ---\n{contenido}\n----------------\n")

    def modificar_archivo(self):
        self.limpiar_panel()
        nombre = simpledialog.askstring("Modificar", "Nombre del archivo:", parent=self.root)
        if not nombre:
            return
        fat = cargar_fat(self.usuario)
        entrada = next((f for f in fat if f['nombre'] == nombre and not f.get('papelera')), None)
        if not entrada:
            messagebox.showerror("Error", "Archivo no encontrado o en papelera.")
            return
        viejo = leer_bloques(self.usuario, entrada['ruta_datos'])
        nuevo = simpledialog.askstring("Editar", "Nuevo contenido:", initialvalue=viejo, parent=self.root)
        if nuevo is None:
            return
        eliminar_bloques(self.usuario, entrada['ruta_datos'])
        nuevo_inicio = crear_bloques(self.usuario, nuevo)
        entrada['ruta_datos'] = nuevo_inicio
        entrada['cantidad_caracteres'] = len(nuevo)
        entrada['fecha_modificacion'] = fecha_actual()
        guardar_fat(self.usuario, fat)
        self.registro(f"Archivo '{nombre}' modificado correctamente.")

    def eliminar_archivo(self):
        self.limpiar_panel()
        nombre = simpledialog.askstring("Eliminar", "Nombre del archivo:", parent=self.root)
        if not nombre:
            return
        fat = cargar_fat(self.usuario)
        for e in fat:
            if e['nombre'] == nombre and not e.get('papelera'):
                e['papelera'] = True
                e['fecha_eliminacion'] = fecha_actual()
                guardar_fat(self.usuario, fat)
                self.registro(f"Archivo '{nombre}' movido a papelera.")
                return
        messagebox.showerror("Error", "Archivo no encontrado o ya en papelera.")

    def ver_papelera(self):
        self.limpiar_panel()
        fat = cargar_fat(self.usuario)
        papelera = [f for f in fat if f.get('papelera')]
        if not papelera:
            self.registro("La papelera está vacía.")
            return
        self.registro("Archivos en papelera:")
        for e in papelera:
            self.registro(f" - {e['nombre']} (eliminado el {e['fecha_eliminacion']})")

    def recuperar_archivo(self):
        self.limpiar_panel()
        nombre = simpledialog.askstring("Recuperar", "Nombre del archivo a recuperar:", parent=self.root)
        if not nombre:
            return
        fat = cargar_fat(self.usuario)
        for e in fat:
            if e['nombre'] == nombre and e.get('papelera'):
                e['papelera'] = False
                e['fecha_eliminacion'] = None
                guardar_fat(self.usuario, fat)
                self.registro(f"Archivo '{nombre}' recuperado correctamente.")
                return
        messagebox.showerror("Error", "Archivo no encontrado en la papelera.")

def main():
    asegurar_carpetas()
    root = tk.Tk()
    app = AplicacionFAT(root)
    root.mainloop()

if __name__ == '__main__':
    main()