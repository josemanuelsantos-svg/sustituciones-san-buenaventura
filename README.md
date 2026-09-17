# Sistema de Sustituciones Escolares - Colegio San Buenaventura

Aplicación web para la gestión ágil, equitativa e inteligente de sustituciones de profesores, conectada a Google Calendar y WhatsApp.

---

## 🚀 Opciones para Colgar la Aplicación en Internet (Gratis y Rápido)

### Opción 1: Render.com (Recomendada - 100% Gratuita)

1. Sube este proyecto a tu cuenta de **GitHub** (ver instrucciones abajo).
2. Entra en **[render.com](https://render.com/)** e inicia sesión con tu cuenta de GitHub.
3. Haz clic en **New +** ➔ **Web Service**.
4. Conecta el repositorio que acabas de subir.
5. Render detectará automáticamente el archivo `render.yaml` y `Procfile`.
6. Pulsa **Create Web Service**.
7. En 2 minutos tendrás una URL pública y segura (`https://sustituciones-san-buenaventura.onrender.com`) accesible desde cualquier móvil o navegador del centro.

---

### Opción 2: Railway.app (Rápida y Automática)

1. Entra en **[railway.app](https://railway.app/)**.
2. Haz clic en **New Project** ➔ **Deploy from GitHub repo**.
3. Selecciona este repositorio.
4. Railway detectará el `Dockerfile` y `Procfile` y desplegará la aplicación al instante dándote un dominio público `.up.railway.app`.

---

### Opción 3: Despliegue con Docker (En cualquier servidor o VPS propio)

```bash
# 1. Construir la imagen Docker
docker build -t sustituciones-colegio .

# 2. Ejecutar el contenedor en el puerto deseado (ej. 5055 u 80)
docker run -d -p 5055:5055 --name sustituciones sustituciones-colegio
```

---

## 📦 Comandos para subir el proyecto a GitHub:

Desde esta carpeta (`/Users/jose/.gemini/antigravity/scratch/sustituciones-colegio`):

```bash
# 1. Crear un nuevo repositorio vacío en github.com (ej. 'sustituciones-colegio')
# 2. Vincular y subir:
git remote add origin https://github.com/TU_USUARIO/sustituciones-colegio.git
git branch -M main
git push -u origin main
```
