from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from dotenv import load_dotenv

import pyodbc
import os
import tempfile
import shutil
import traceback
import time


# ==================================================
# VARIABLES DE ENTORNO
# ==================================================

load_dotenv()

URL_DESPUES_LOGIN = os.getenv("URL_DESPUES_LOGIN")
URL_LOGIN = os.getenv("URL_LOGIN")

WEB_USERNAME = os.getenv("USERNAME")
WEB_PASSWORD = os.getenv("PASSWORD")

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "1433")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

PERFIL_RUTA = int(os.getenv("PERFIL_RUTA", "2448"))


# ==================================================
# CONFIGURACIÓN
# ==================================================

CHROME_BINARY = "/usr/bin/google-chrome"

CHROMEDRIVER = "/home/edo/programas/chromedriver"


# ==================================================
# CONEXIÓN SQL SERVER
# ==================================================

def conectar_bd():

    connection_string = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={DB_HOST},{DB_PORT};"
        f"DATABASE={DB_NAME};"
        f"UID={DB_USER};"
        f"PWD={DB_PASSWORD};"
        "Encrypt=no;"
        "TrustServerCertificate=yes;"
    )

    conn = pyodbc.connect(connection_string)

    print("✅ CONEXIÓN SQL SERVER OK")

    return conn


# ==================================================
# BUSCAR PERSONA POR RUT
# ==================================================

def buscar_tarjeta(conn, rut):

    sql = """
        SELECT
            PT.Id AS PersonaId,
            PT.DNI,
            PT.NOMBRE,
            PT.Apellidos,
            T.Id AS TarjetaId
        FROM dbo.PERSONAST PT
        INNER JOIN dbo.TARJETAS T
            ON T.FKPERSONAACTUAL = PT.Id
        WHERE REPLACE(REPLACE(PT.DNI, '.', ''), '-', '') =
              REPLACE(REPLACE(?, '.', ''), '-', '')
    """

    cursor = conn.cursor()

    cursor.execute(sql, rut)

    row = cursor.fetchone()

    cursor.close()

    return row


# ==================================================
# BUSCAR HORARIO
# ==================================================

def buscar_horario(conn, hora):

    hora = int(hora)

    descripcion = f"Horario {hora} a {hora + 1}"

    sql = """
        SELECT
            Id,
            Codigo,
            Descripcion
        FROM dbo.HorariosAccesos
        WHERE Descripcion = ?
          AND Habilitado = 'V'
    """

    cursor = conn.cursor()

    cursor.execute(sql, descripcion)

    row = cursor.fetchone()

    cursor.close()

    return row


# ==================================================
# VERIFICAR SI YA EXISTE
# ==================================================

def acceso_ya_existe(conn, tarjeta_id, perfil_id, horario_id, fecha_baja):

    sql = """
        SELECT TOP 1
            Id
        FROM dbo.PerfilesAccesosTarjetas
        WHERE FkTarjeta = ?
          AND FkPerfil = ?
          AND FkHorarioAccesos = ?
          AND FechaBaja = ?
    """

    cursor = conn.cursor()

    cursor.execute(
        sql,
        tarjeta_id,
        perfil_id,
        horario_id,
        fecha_baja
    )

    row = cursor.fetchone()

    cursor.close()

    return row is not None


# ==================================================
# CREAR ACCESO
# ==================================================

def crear_acceso(
    conn,
    tarjeta_id,
    perfil_id,
    horario_id,
    fecha_baja
):

    sql = """
        INSERT INTO dbo.PerfilesAccesosTarjetas
        (
            FkTarjeta,
            FkPerfil,
            FkHorarioAccesos,
            FechaBaja
        )
        VALUES
        (
            ?,
            ?,
            ?,
            ?
        )
    """

    cursor = conn.cursor()

    cursor.execute(
        sql,
        tarjeta_id,
        perfil_id,
        horario_id,
        fecha_baja
    )

    conn.commit()

    cursor.close()


# ==================================================
# PROCESAR REGISTRO
# ==================================================

def procesar_registro(conn, registro):

    rut = registro["rut"]
    hora = registro["horario"]
    fecha = registro["fecha"]

    print("")
    print("========================================")
    print("PROCESANDO")
    print("========================================")

    print(f"Nombre : {registro['nombre']}")
    print(f"RUT    : {rut}")
    print(f"Hora   : {hora}")
    print(f"Fecha  : {fecha}")

    # ----------------------------------------------
    # PERSONA / TARJETA
    # ----------------------------------------------

    persona = buscar_tarjeta(conn, rut)

    if not persona:

        print(f"❌ No se encontró tarjeta para RUT {rut}")

        return

    persona_id = persona.PersonaId
    nombre = persona.NOMBRE
    apellidos = persona.Apellidos
    tarjeta_id = persona.TarjetaId

    print("")
    print("PERSONA EN BD")
    print(f"PersonaId : {persona_id}")
    print(f"Nombre    : {nombre} {apellidos}")
    print(f"TarjetaId : {tarjeta_id}")

    # ----------------------------------------------
    # HORARIO
    # ----------------------------------------------

    horario = buscar_horario(conn, hora)

    if not horario:

        print(
            f"❌ No existe HorariosAccesos "
            f"para horario {hora}"
        )

        return

    horario_id = horario.Id
    horario_descripcion = horario.Descripcion

    print("")
    print("HORARIO")
    print(f"HorarioId   : {horario_id}")
    print(f"Descripción : {horario_descripcion}")

    # ----------------------------------------------
    # FECHA BAJA
    # ----------------------------------------------

    fecha_baja = fecha.replace("-", "") + "0000"

    print("")
    print(f"FechaBaja : {fecha_baja}")

    # ----------------------------------------------
    # VERIFICAR DUPLICADO
    # ----------------------------------------------

    existe = acceso_ya_existe(
        conn,
        tarjeta_id,
        PERFIL_RUTA,
        horario_id,
        fecha_baja
    )

    if existe:

        print("")
        print("⚠️ El acceso ya existe.")
        print("No se crea nuevamente.")

        return

    # ----------------------------------------------
    # CREAR
    # ----------------------------------------------

    crear_acceso(
        conn,
        tarjeta_id,
        PERFIL_RUTA,
        horario_id,
        fecha_baja
    )

    print("")
    print("========================================")
    print("✅ ACCESO CREADO")
    print("========================================")

    print(f"Tarjeta       : {tarjeta_id}")
    print(f"Perfil/Ruta   : {PERFIL_RUTA}")
    print(f"Horario       : {horario_descripcion}")
    print(f"FechaBaja     : {fecha_baja}")
    print("========================================")


# ==================================================
# SCRAPER
# ==================================================

def ejecutar():

    options = Options()

    options.binary_location = CHROME_BINARY

    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")

    temp_profile_dir = tempfile.mkdtemp()

    options.add_argument(
        f"--user-data-dir={temp_profile_dir}"
    )

    service = Service(
        executable_path=CHROMEDRIVER
    )

    driver = None

    conn = None

    try:

        # ==========================================
        # SQL SERVER
        # ==========================================

        conn = conectar_bd()

        # ==========================================
        # CHROME
        # ==========================================

        driver = webdriver.Chrome(
            service=service,
            options=options
        )

        wait = WebDriverWait(driver, 20)

        print("✅ Navegador iniciado")

        # ==========================================
        # LOGIN
        # ==========================================

        driver.get(URL_LOGIN)

        print("🌐 Página de login cargada")

        username_input = wait.until(
            EC.visibility_of_element_located(
                (By.ID, "usu_cod")
            )
        )

        password_input = wait.until(
            EC.visibility_of_element_located(
                (By.ID, "pass")
            )
        )

        username_input.clear()
        username_input.send_keys(WEB_USERNAME)

        password_input.clear()
        password_input.send_keys(WEB_PASSWORD)

        login_button = wait.until(
            EC.presence_of_element_located(
                (By.ID, "asis")
            )
        )

        login_button.click()

        print("🔓 Login enviado")

        time.sleep(2)

        # ==========================================
        # PÁGINA DE ASISTENCIA
        # ==========================================

        driver.get(URL_DESPUES_LOGIN)

        print(
            "🌐 Página posterior al login cargada"
        )

        # ==========================================
        # LEER PÁGINAS
        # ==========================================

        resultados = []

        pagina = 1

        while True:

            print("")
            print(
                f"📄 Procesando página {pagina}"
            )

            wait.until(
                EC.presence_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        "#tabla-asistencia tbody"
                    )
                )
            )

            filas_data = driver.execute_script("""
                const filas =
                    document.querySelectorAll(
                        '#tabla-asistencia tbody tr'
                    );

                return Array.from(filas).map(fila => {

                    const celdas =
                        fila.querySelectorAll('td');

                    return Array.from(celdas).map(
                        celda =>
                            celda.textContent.trim()
                    );

                });
            """)

            print(
                f"   Filas visibles: "
                f"{len(filas_data)}"
            )

            # ======================================
            # PROCESAR FILAS
            # ======================================

            for datos in filas_data:

                if len(datos) < 5:
                    continue

                nombre = datos[0]
                rut = datos[1]
                horario = datos[2]
                fecha_solicitud = datos[3]
                fecha = datos[4]

                resultado = {
                    "nombre": nombre,
                    "rut": rut,
                    "horario": horario,
                    "fecha_solicitud":
                        fecha_solicitud,
                    "fecha": fecha
                }

                resultados.append(resultado)

                print(
                    f"   {len(resultados):02d}. "
                    f"{rut} | "
                    f"{horario} | "
                    f"{fecha}"
                )

                # ==================================
                # ACTUALIZAR BD
                # ==================================

                procesar_registro(
                    conn,
                    resultado
                )

            # ======================================
            # SIGUIENTE
            # ======================================

            siguiente = driver.find_elements(
                By.CSS_SELECTOR,
                "#tabla-asistencia_next"
            )

            if not siguiente:

                print(
                    "⏹️ No se encontró "
                    "botón siguiente"
                )

                break

            siguiente_disabled = driver.execute_script("""
                const boton =
                    document.querySelector(
                        '#tabla-asistencia_next'
                    );

                if (!boton) {
                    return true;
                }

                return boton.classList.contains(
                    'disabled'
                );
            """)

            if siguiente_disabled:

                print(
                    "⏹️ Última página alcanzada"
                )

                break

            pagina_actual = driver.execute_script("""
                const activa =
                    document.querySelector(
                        '#tabla-asistencia_wrapper '
                        + '.paginate_button.current'
                    );

                return activa
                    ? activa.textContent.trim()
                    : null;
            """)

            driver.execute_script("""
                document.querySelector(
                    '#tabla-asistencia_next'
                ).click();
            """)

            try:

                wait.until(
                    lambda d:
                        d.execute_script("""
                            const activa =
                                document.querySelector(
                                    '#tabla-asistencia_wrapper '
                                    + '.paginate_button.current'
                                );

                            return activa
                                ? activa.textContent.trim()
                                : null;
                        """) != pagina_actual
                )

            except Exception:

                time.sleep(0.5)

            pagina += 1

        # ==========================================
        # RESULTADO
        # ==========================================

        print("")
        print("========================================")
        print(
            f"✅ TOTAL REGISTROS: "
            f"{len(resultados)}"
        )
        print("========================================")

        return resultados

    except Exception:

        print("❌ Ocurrió un error:")

        traceback.print_exc()

        return None

    finally:

        if conn:

            conn.close()

            print(
                "🔌 Conexión SQL Server cerrada"
            )

        if driver:

            driver.quit()

            print(
                "👋 Navegador cerrado"
            )

        shutil.rmtree(
            temp_profile_dir,
            ignore_errors=True
        )


# ==================================================
# MAIN
# ==================================================

if __name__ == "__main__":

    resultado = ejecutar()

    print("")
    print("RESULTADO:")
    print(resultado)