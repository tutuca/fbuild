Introducción
===============

`fudepan-build` provee manejo de dependencias y uniformidad en el build (utilizando scons). Ademas, se puede utilizar como un entorno reducido donde mantener una instalación y proveer comandos personalizados.

Estructura de fudepan-build


    fudepan-build/
         projects/
         conf/
            projects.xml
         install/
         env.sh
         start.sh

 

`projects/` es el directorio donde se almacenara el código de los distintos proyectos.
conf/ archivos de configuración
conf/projects.xml contiene la configuración de cada proyecto, la url de descarga, etc
`install/` es el directorio de instalación por defecto.
env.sh es el script que prepara el ambiente del sistema.
`start.sh` es el script que intenta actualizar fbuild a la versión más reciente.

Uso
===============

Antes que nada, hacer un source del archivo start.sh en la raiz del proyecto.


    $ source start.sh

Para descargar un proyecto (listado en projects.xml):

    $ fbuild <nombre-proyecto>:checkout

Esto lo descargará en el directorio projects y lo dejará listo para trabajar.

Para ejecutar el build:

    $ fbuild <nombre-proyecto> 

Para ejecutar los tests de un proyecto:

    $ fbuild <nombre-proyecto>:test 

Por defecto, fudepan-build utiliza `install/` como entorno reducido, por lo que todas las libs, binarios, includes, etc, se instalaran ahí, dejando limpio el sistema:

    $ fbuild install <nombre-proyecto> 

Tambien es posible pisar los directorios de instalación, por ejemplo:

    $ fbuild INSTALL_HEADERS_DIR=/usr/local/include/ INSTALL_BIN_DIR=/usr/local/bin/ INSTALL_LIB_DIR=/usr/local/lib/ 

Para limpiar los archivos generados al ejecutar un target:

    $ fbuild -c <target>

Para obtener una lista de los 'targets' disponibles:

    $ fbuild targets

Para obtener el reporte de coverage via lcov

    $ fbuild <proyecto>:coverage

Para ver la ayuda de scons:

    $ fbuild --help

Para obtener una salida más completa:

    $ fbuild --verbose ....

*Sconscificando* un proyecto
===============

Hay 4 tipos basicos de builders:

* Header only
* Program
* Static Library
* Shared Library
* Test

En general un proyecto contendra la siguiente estructura:

    biopp/
       biopp/         <--- contendrá los headers
       src/
       tests/
          SConscript
       SConscript

Ejemplos de cada tipo de proyecto:

    Header Only: mili
    Static Library: getoptpp
    Shared Library: biopp
    Program: backbones-generator

Variables de entorno
===============

Algunas variables de entorno a tener en cuenta:

Qt (ejemplo para Arch, para Ubuntu no es necesario agregar esto):

    export QT_INCLUDE_ROOT=/usr/include
    export QT_INCLUDE=/usr/include/Qt

Prevenir que fbuild se actualice automaticamente (no recomendado):

    export FBUILD_NO_UPDATE=1 

Tips
===============

Es extremadamente util agregar un alias en el archivo ~/.bashrc que nos ahorre el recordar hacer el source de env.sh, por ejemplo:

    alias go-fudepan='cd /home/usuario/fudepan-build && source start.sh'

Otra ventaja colateral es que se puede utilizar el archivo `start.sh` para definir alias y comandos extras que seran solamente visibles cuando se haga el source del mismo.