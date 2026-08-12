from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

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
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")


def ejecutar():

    # ==================================================
    # CONFIGURACIÓN
    # ==================================================

    options = Options()

    options.binary_location = "/usr/bin/google-chrome"

    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")

    # Perfil temporal
    temp_profile_dir = tempfile.mkdtemp()

    options.add_argument(
        f"--user-data-dir={temp_profile_dir}"
    )

    # ==================================================
    # CHROMEDRIVER
    # ==================================================

    service = Service(
        executable_path="/home/edo/programas/chromedriver"
    )

    driver = None

    try:

        driver = webdriver.Chrome(
            service=service,
            options=options
        )

        wait = WebDriverWait(driver, 20)

        print("✅ Navegador iniciado")

        # ==================================================
        # PÁGINA DE LOGIN
        # ==================================================

        driver.get(URL_LOGIN)

        print("🌐 Página de login cargada")

        # ==================================================
        # USUARIO
        # ==================================================

        username_input = wait.until(
            EC.visibility_of_element_located(
                (By.ID, "usu_cod")
            )
        )

        # ==================================================
        # CONTRASEÑA
        # ==================================================

        password_input = wait.until(
            EC.visibility_of_element_located(
                (By.ID, "pass")
            )
        )

        print("✅ Campos encontrados")

        # ==================================================
        # CREDENCIALES
        # ==================================================

        username_input.clear()
        username_input.send_keys(USERNAME)

        password_input.clear()
        password_input.send_keys(PASSWORD)

        print("🔐 Credenciales ingresadas")

        # ==================================================
        # LOGIN
        # ==================================================

        login_button = wait.until(
            EC.presence_of_element_located(
                (By.ID, "asis")
            )
        )

        print("✅ Botón login encontrado")

        login_button.click()

        print("🔓 Login enviado")

        # ==================================================
        # ESPERAR UN MOMENTO
        # ==================================================

        time.sleep(2)

        print("URL después del login:")
        print(driver.current_url)

        # ==================================================
        # IR A LA PÁGINA QUE DEBERÍA APARECER
        # ==================================================

        driver.get(URL_DESPUES_LOGIN)

        print("🌐 Página posterior al login cargada")
        print("URL actual:", driver.current_url)

        # ==================================================
        # LEER TODAS LAS PÁGINAS DE LA TABLA
        # ==================================================

        resultados = []

        pagina = 1

        while True:

            print(f"\n📄 Procesando página {pagina}")

            # ----------------------------------------------
            # ESPERAR TABLA
            # ----------------------------------------------

            wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "#tabla-asistencia tbody")
                )
            )

            # ----------------------------------------------
            # EXTRAER TODAS LAS FILAS MEDIANTE JAVASCRIPT
            # ----------------------------------------------
            #
            # No usamos objetos WebElement para las filas.
            # JavaScript lee directamente el DOM actual.
            #

            filas_data = driver.execute_script("""
                const filas = document.querySelectorAll(
                    '#tabla-asistencia tbody tr'
                );

                return Array.from(filas).map(fila => {

                    const celdas = fila.querySelectorAll('td');

                    return Array.from(celdas).map(
                        celda => celda.textContent.trim()
                    );

                });
            """)

            print(f"   Filas visibles: {len(filas_data)}")

            # ----------------------------------------------
            # PROCESAR FILAS
            # ----------------------------------------------

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
                    "fecha_solicitud": fecha_solicitud,
                    "fecha": fecha
                }

                resultados.append(resultado)

                print(
                    f"   {len(resultados):02d}. "
                    f"{rut} | "
                    f"{fecha_solicitud}"
                )

            # ----------------------------------------------
            # BUSCAR BOTÓN SIGUIENTE
            # ----------------------------------------------

            siguiente = driver.find_elements(
                By.CSS_SELECTOR,
                "#tabla-asistencia_next"
            )

            if not siguiente:

                print("⏹️ No se encontró botón siguiente")
                break

            # Obtener clase mediante JavaScript
            siguiente_disabled = driver.execute_script("""
                const boton = document.querySelector(
                    '#tabla-asistencia_next'
                );

                if (!boton) {
                    return true;
                }

                return boton.classList.contains('disabled');
            """)

            if siguiente_disabled:

                print("⏹️ Última página alcanzada")
                break

            # ----------------------------------------------
            # OBTENER IDENTIFICADOR DE LA PÁGINA ACTUAL
            # ----------------------------------------------

            pagina_actual = driver.execute_script("""
                const activa = document.querySelector(
                    '#tabla-asistencia_wrapper .paginate_button.current'
                );

                return activa ? activa.textContent.trim() : null;
            """)

            # ----------------------------------------------
            # CLICK EN SIGUIENTE
            # ----------------------------------------------

            driver.execute_script("""
                document.querySelector(
                    '#tabla-asistencia_next'
                ).click();
            """)

            # ----------------------------------------------
            # ESPERAR CAMBIO DE PÁGINA
            # ----------------------------------------------

            try:

                wait.until(
                    lambda d: d.execute_script("""
                        const activa = document.querySelector(
                            '#tabla-asistencia_wrapper .paginate_button.current'
                        );

                        return activa
                            ? activa.textContent.trim()
                            : null;
                    """) != pagina_actual
                )

            except Exception:

                # Si DataTables no cambia el botón current,
                # esperamos brevemente a que actualice el DOM.

                time.sleep(0.5)

            pagina += 1


        # ==================================================
        # RESULTADO FINAL
        # ==================================================

        print("\n========================================")
        print(f"✅ TOTAL DE REGISTROS: {len(resultados)}")
        print("========================================")

        return resultados
    except Exception as e:

        print("❌ Ocurrió un error:")
        traceback.print_exc()

        return None

    finally:

        if driver:
            driver.quit()
            print("👋 Navegador cerrado")
            print("Esto es un cambio de prueba")

        shutil.rmtree(
            temp_profile_dir,
            ignore_errors=True
        )


if __name__ == "__main__":

    resultado = ejecutar()

    print("\nRESULTADO:")
    print(resultado)
