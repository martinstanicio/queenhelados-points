# Queen Helados - Points

## Configuración del Adaptador de Google Drive

El adaptador de Google Drive utiliza una arquitectura de seguridad **Zero Trust**, implementando **Application Default Credentials (ADC)** y **Workload Identity Federation (WIF)** para gestionar el acceso sin almacenar credenciales estáticas. A continuación, se detallan los pasos para configurar la infraestructura requerida.

### Fase 1: Configuración en Google Cloud

Antes de interactuar con el código, es necesario preparar la infraestructura en la nube de Google utilizando la cuenta de desarrollo.

1. Ingresar a Google Cloud Console.
2. Crear un proyecto nuevo o seleccionar uno existente.
3. Tomar nota del **ID del Proyecto** (`PROJECT_ID`) y del **Número del Proyecto** (`PROJECT_NUMBER`).
4. Ir a **APIs y Servicios > Biblioteca**, buscar **Google Drive API** y hacer clic en **Habilitar**.
5. Buscar **IAM Service Account Credentials API** y hacer clic en **Habilitar**.

### Fase 2: Despliegue en Producción (GitHub Actions)

Para que el sistema se ejecute de forma autónoma en GitHub sin exponer contraseñas, se configura un entorno de confianza (WIF) y una cuenta de servicio.

#### 1. Crear la Service Account y asignar permisos en Drive

Esta será la identidad oficial del automatismo.

1. En Google Cloud Console, ir a **IAM y administración > Cuentas de servicio**.
2. Crear una nueva cuenta.
3. Tomar nota de su correo electrónico. Este valor corresponderá a la variable de entorno `TARGET_SERVICE_ACCOUNT`.
4. Ir a Google Drive web, hacer clic derecho sobre la carpeta raíz que contiene los archivos de Excel y compartirla con permisos de **Lector** a este correo electrónico.

> [!NOTE]
> No es necesario que la cuenta de desarrollo tenga acceso a esta carpeta de Drive; el acceso solo es necesario para la Service Account.

#### 2. Crear el Pool y el Provider (WIF)

Ejecutar los siguientes comandos en la terminal de Google Cloud Shell. Reemplazar `PROJECT_ID`:

```bash
# Crear el Pool (Grupo de confianza)
gcloud iam workload-identity-pools create "github-pool" \
  --project="PROJECT_ID" \
  --location="global" \
  --display-name="GitHub Actions Pool"

## Crear el Provider (Vincular a GitHub)
gcloud iam workload-identity-pools providers create-oidc "github-provider" \
  --project="PROJECT_ID" \
  --location="global" \
  --workload-identity-pool="github-pool" \
  --display-name="GitHub Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
  --issuer-uri="https://token.actions.githubusercontent.com"
```

#### 3. Otorgar permisos al Repositorio de GitHub

Este comando autoriza al repositorio a usar la identidad de la cuenta de servicio. Reemplazar `SERVICE_ACCOUNT_EMAIL`, `PROJECT_ID`, `PROJECT_NUMBER`, `USUARIO` y `REPOSITORIO`.

```bash
gcloud iam service-accounts add-iam-policy-binding "SERVICE_ACCOUNT_EMAIL" \
  --project="PROJECT_ID" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/attribute.repository/USUARIO/REPOSITORIO"
```

#### 4. Configurar Variables en GitHub

Inyectar los identificadores en la configuración del repositorio para que el pipeline funcione.

 1. Ir al repositorio en GitHub.
 2. Navegar a **Settings > Secrets and variables > Actions > Variables**.
 3. Hacer clic en **New repository variable** y agregar:

* **WIF_PROVIDER**: projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/providers/github-provider *(reemplazando PROJECT_NUMBER)*.
* **TARGET_SERVICE_ACCOUNT**: El correo electrónico de la cuenta de servicio.
* **FOLDER_ID**: El ID alfanumérico de la carpeta en Google Drive.

### Fase 3: Preparar el Entorno Local (WSL / Ubuntu)

Para ejecutar y probar el código localmente, se debe configurar la CLI de Google Cloud y solicitar un pase temporal vinculado a tu identidad de desarrollador. Esto permite al script impersonar a la Service Account de manera segura.

#### 1. Instalar dependencias y la CLI

```bash
# Instalar dependencias de seguridad
sudo apt update
sudo apt install apt-transport-https ca-certificates gnupg curl

# Descargar la llave criptográfica pública de Google
curl [https://packages.cloud.google.com/apt/doc/apt-key.gpg](https://packages.cloud.google.com/apt/doc/apt-key.gpg) | sudo gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg

# Agregar el repositorio
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] [https://packages.cloud.google.com/apt](https://packages.cloud.google.com/apt) cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list

# Instalar Google Cloud CLI
sudo apt update
sudo apt install google-cloud-cli
```

#### 2. Autenticación Local

Ejecutar el login y vincular el proyecto para evitar errores de cuota de API (reemplazar PROJECT_ID):

```bash
gcloud auth application-default login
gcloud auth application-default set-quota-project PROJECT_ID
```

#### 3. Permisos de Impersonación Local

Para que la impersonación funcione a nivel local, tu cuenta personal debe tener permiso para generar tokens en nombre de la Service Account. Ejecuta este comando reemplazando `SERVICE_ACCOUNT_EMAIL`, `PROJECT_ID` y `CUENTA_DESARROLLO` (el mail de la cuenta de desarrollo).

```bash
gcloud iam service-accounts add-iam-policy-binding "SERVICE_ACCOUNT_EMAIL" \
    --project="PROJECT_ID" \
    --member="user:CUENTA_DESARROLLO" \
    --role="roles/iam.serviceAccountTokenCreator"
```

> [!WARNING]
> Asegúrate de definir las variables FOLDER_ID y TARGET_SERVICE_ACCOUNT en el entorno (un archivo .env) antes de ejecutar localmente.
