# -*- coding: utf-8 -*-
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import folium

st.set_page_config(layout="wide", page_title="Modelo de Dispersión Atmosférica")

st.title("💨 Simulación de Pluma de Dispersión (Modelo Klug)")

# --- BARRA LATERAL: PARÁMETROS DINÁMICOS ---
st.sidebar.header("Ubicación de la Fuente Emisora")
lat_src = st.sidebar.number_input("Latitud de la fuente", value=-41.1335, format="%.5f")
lon_src = st.sidebar.number_input("Longitud de la fuente", value=-71.3103, format="%.5f")

st.sidebar.header("Condiciones de Emisión y Clima")
CL = st.sidebar.selectbox("Clase de Estabilidad (Pasquill-Klug)", ['A', 'B', 'C', 'D', 'E', 'F'], index=0)
q = st.sidebar.number_input("Tasa de liberación q [g/s]", value=166.7, step=10.0)
u = st.sidebar.number_input("Velocidad del viento u [m/s]", value=2.86, min_value=0.1, step=0.1)
wind_dir = st.sidebar.slider("Dirección del viento (° desde donde sopla)", 0, 360, 270)
h = st.sidebar.number_input("Altura de liberación h [m]", value=5.0, step=1.0)
zr = st.sidebar.number_input("Altura de receptor zr [m]", value=0.1, step=0.1)
lim = st.sidebar.slider("Límite de alcance horizontal [m]", 100, 5000, 1000)

# --- COEFICIENTES DE KLUG (TUS ECUACIONES ORIGINALES) ---
if CL == 'A':
    ay, by, az, bz, f_e_y = 0.469, 0.903, 0.017, 1.380, 10
elif CL == 'B':
    ay, by, az, bz, f_e_y = 0.306, 0.885, 0.072, 1.021, 10
elif CL == 'C':
    ay, by, az, bz, f_e_y = 0.230, 0.855, 0.076, 0.879, 10
elif CL == 'D':
    ay, by, az, bz, f_e_y = 0.219, 0.764, 0.140, 0.727, 10
elif CL == 'E':
    ay, by, az, bz, f_e_y = 0.237, 0.691, 0.217, 0.610, 10
elif CL == 'F':
    ay, by, az, bz, f_e_y = 0.273, 0.594, 0.262, 0.500, 10

# --- CÁLCULO DE LA DISPERSIÓN (FÓRMULA GAUSSIANA EXACTA) ---
x = np.linspace(0.1, lim, 300)
y = np.linspace(-lim / f_e_y, lim / f_e_y, 300)

X, Y = np.meshgrid(x, y)

sig_y = ay * X ** by
sig_z = az * X ** bz

Conc_con = q / (2 * np.pi * u * sig_y * sig_z) * np.exp(-Y**2 / (2 * sig_y ** 2)) * np.exp(-(zr - h)**2 / (2 * sig_z ** 2))

# --- TRANSFORMACIÓN GEOGRÁFICA Y ROTACIÓN POR VIENTO ---
wind_rad = np.radians((270 - wind_dir) % 360)

X_rot = X * np.cos(wind_rad) - Y * np.sin(wind_rad)
Y_rot = X * np.sin(wind_rad) + Y * np.cos(wind_rad)

m_per_deg_lat = 111139.0
m_per_deg_lon = 111139.0 * np.cos(np.radians(lat_src))

lat_grid = lat_src + (Y_rot / m_per_deg_lat)
lon_grid = lon_src + (X_rot / m_per_deg_lon)

# --- GENERACIÓN DE ISOPLETAS / CONTORNOS CON MATPLOTLIB ---
fig, ax = plt.subplots(figsize=(8, 8))
fig.patch.set_alpha(0.0)
ax.patch.set_alpha(0.0)

levels = np.linspace(Conc_con.max() * 0.01, Conc_con.max(), 25)

contour = ax.contourf(lon_grid, lat_grid, Conc_con, levels=levels, cmap='turbo', alpha=0.65)
ax.axis('off')

plt.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)
plt.margins(0, 0)
ax.xaxis.set_major_locator(plt.NullLocator())
ax.yaxis.set_major_locator(plt.NullLocator())

fig.savefig("plume_contour.png", format='png', transparent=True, bbox_inches='tight', pad_inches=0)
plt.close(fig)

# --- RENDERIZADO EN EL MAPA FOLIUM ---
st.subheader(f"Mapa de Concentración de Pluma — Clase de Estabilidad {CL}")

m = folium.Map(location=[lat_src, lon_src], zoom_start=14, tiles="OpenStreetMap")

folium.Marker(
    [lat_src, lon_src],
    popup=f"Fuente Emisora (h={h}m)",
    icon=folium.Icon(color="red", icon="industry", prefix="fa")
).add_to(m)

bounds = [[lat_grid.min(), lon_grid.min()], [lat_grid.max(), lon_grid.max()]]
folium.raster_layers.ImageOverlay(
    image="plume_contour.png",
    bounds=bounds,
    opacity=0.75,
    interactive=True,
    cross_origin=False
).add_to(m)

st.components.v1.html(m._repr_html_(), height=600)
st.info(f"Concentración Máxima Calculada: **{Conc_con.max():.2e} g/m³**")
