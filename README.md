# 📊 Bonificación Ingreso Ético Familiar

Aplicación desarrollada en **Python** y **Streamlit** que consume datos desde la **API pública de datos.gob.cl** para analizar la distribución de la **Bonificación del Ingreso Ético Familiar** en Chile.  
Permite filtrar por **región**, visualizar métricas resumidas y explorar gráficos dinámicos.

---

## 🚀 Demo en línea
La aplicación está desplegada en **Streamlit Community Cloud** y disponible en el siguiente enlace:

🔗 **[Abrir aplicación](https://bonificacion-ief-6qkwcsc77kkz5fx6bt2pwf.streamlit.app/)**

---

## 📌 Funcionalidades principales

- **Consumo de API pública**:  
  Obtiene los datos actualizados desde el portal [datos.gob.cl](https://datos.gob.cl).
- **Limpieza y normalización**:  
  Convierte montos y campos para análisis correcto.
- **Interfaz interactiva**:  
  - Selector de **región** con nombres oficiales.
  - Visualización de **tabla completa** con los datos.
  - Métricas resumidas de **montos totales**.
  - **Gráficos dinámicos**:
    - Top 20 comunas por monto total.
    - Comparativa de montos **hombres vs mujeres**.
- **Formato chileno** para los montos (puntos como separador de miles).

---

## 🛠️ Tecnologías utilizadas

- **Python 3.11**
- [Streamlit](https://streamlit.io/) → UI interactiva.
- [Pandas](https://pandas.pydata.org/) → Análisis y limpieza de datos.
- [Matplotlib](https://matplotlib.org/) → Gráficos estáticos.
- [Requests](https://docs.python-requests.org/) → Consumo de API.

---

## 🗂️ Estructura del repositorio

```text
bonificacion-ief/
├── app.py           # Código principal de la aplicación
├── requirements.txt # Dependencias necesarias para ejecutar la app
├── runtime.txt      # Versión de Python utilizada (3.11)
└── README.md        # Documentación del proyecto
```
