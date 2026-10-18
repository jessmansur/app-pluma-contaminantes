# -*- coding: utf-8 -*-
import streamlit as st
import numpy as np
import folium
from folium.plugins import HeatMap

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

# --- COEFICIENTES DE KLUG ---
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

# --- CÁLCULO DE LA DISPERSIÓN ---
x = np.arange(0.1, lim, lim / 100)
y = np.arange(-lim / f_e_y, lim / f_e_y, (2 * lim / f_e_y) / 100)

X, Y = np.meshgrid(x, y)

sig_y = ay * X ** by
sig_z = az * X ** bz

Conc_con = q / (2 * 3.14159 * u * sig_y * sig_z) * np.exp(-Y**2 / (2 * sig_y ** 2)) * np.exp(-(zr - h)**2 / (2 * sig_z ** 2))

# --- TRANSFORMACIÓN GEOGRÁFICA Y ROTACIÓN POR VIENTO ---
wind_rad = np.radians((270 - wind_dir) % 360)

X_rot = X * np.cos(wind_rad) - Y * np.sin(wind_rad)
Y_rot = X * np.sin(wind_rad) + Y * np.cos(wind_rad)

m_per_deg_lat = 111139.0
m_per_deg_lon = 111139.0 * np.cos(np.radians(lat_src))

lat_grid = lat_src + (Y_rot / m_per_deg_lat)
lon_grid = lon_src + (X_rot / m_per_deg_lon)

heat_data = []
c_max = Conc_con.max()

for i in range(Conc_con.shape[0]):
    for j in range(Conc_con.shape[1]):
        val = Conc_con[i, j]
        if val > (c_max * 1e-4):
            heat_data.append([lat_grid[i, j], lon_grid[i, j], float(val)])

# --- RENDERIZADO DEL MAPA ---
st.subheader(f"Mapa de Concentración de Pluma — Clase de Estabilidad {CL}")

m = folium.Map(location=[lat_src, lon_src], zoom_start=13, tiles="OpenStreetMap")

folium.Marker(
    [lat_src, lon_src],
    popup=f"Fuente Emisora (h={h}m)",
    icon=folium.Icon(color="red", icon="industry", prefix="fa")
).add_to(m)

if heat_data:
    HeatMap(
        heat_data,
        radius=15,
        blur=20,
        max_zoom=1,
        gradient={0.2: 'blue', 0.4: 'cyan', 0.6: 'lime', 0.8: 'yellow', 1.0: 'red'}
    ).add_to(m)

st.components.v1.html(m._repr_html_(), height=600)
st.info(f"Concentración Máxima Calculada: **{c_max:.2e} g/m³**")
