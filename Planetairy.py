import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import astropy.units as u
import astropy.time as time
import astropy.coordinates as coords
import datetime

# --- Interface Setup ---
st.title("Planetary Sky Map 🪐")

st.markdown("""
Welcome! Ever wondered which bright dots in the night sky are actually planets? This tool helps you find out in seconds.
*Pick a date and time to see if planets like Jupiter, Mars, or Venus are currently above the horizon.
*Find your planet by comparing the constellations with your planet.
*View a sky map showing how the visible planets move through the constellations over the next 14 days.
*The observation point is currently set to the center of the Netherlands.

Select a date and time below to see what's in the sky tonight!
""")
# Maak twee kolommen voor datum en tijd input
col1, col2 = st.columns(2)
with col1:
    selected_date = st.date_input("Choose a date", datetime.date.today())
with col2:
    selected_time = st.time_input("Choose a time", datetime.time(0, 0))

# Combineer input tot een formaat dat astropy begrijpt
date_str = f"{selected_date} {selected_time}"
obs_date = time.Time(date_str)
st.success(f"Tijdstip ingesteld op: {obs_date}")

# --- Data & Berekeningen ---
# Let op: de coördinaten wijzen naar Apeldoorn ;)
location = coords.EarthLocation(lat=52.2*u.deg, lon=5.9*u.deg, height=0*u.m)
planets = ['Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune']
altaz_coords = coords.AltAz(obstime=obs_date, location=location)

st.subheader("Zichtbare planeten op dit moment:")
for p in planets:
    p_coord = coords.get_body(p, obs_date, location)
    altaz = p_coord.transform_to(altaz_coords)
    if altaz.alt > 0*u.deg:
        st.write(f"✅ **{p}** is observable (Height: {altaz.alt:.2f}, Azimut: {altaz.az:.2f}) in {coords.get_constellation(p_coord)}.")
    else:
        st.write(f"❌ {p} is not observable.")

# --- Grafiek Maken ---
st.subheader("The celestial map for the upcoming 14 days")

dates = obs_date + np.arange(0, 14 + 1, 1)*u.day 

try:
    ra_stars, dec_stars, pen = np.loadtxt('Database.txt', usecols=(2, 3, 4), unpack=True)
    ra_stars = ra_stars*u.deg 
    dec_stars = dec_stars*u.deg
    star_coords = coords.SkyCoord(ra=ra_stars, dec=dec_stars) 
    star_altaz = star_coords.transform_to(altaz_coords)

    # Maak de figuur aan (belangrijk voor Streamlit)
    fig, ax = plt.subplots(figsize=(15, 6))

    # Teken de sterrenbeelden
    for i in range(0, len(star_altaz)):
        if pen[i] == 1:
            x1, x2 = [star_altaz[i-1].az.deg, star_altaz[i].az.deg]
            y1, y2 = [star_altaz[i-1].alt.deg, star_altaz[i].alt.deg]
            if abs(x1-x2) < 180:
                if y1 > 0 and y2 > 0:
                    ax.plot([x1, x2], [y1, y2], color='lightgray')

    # Teken de planeten
    for p in planets:
        p_coords = coords.get_body(p, dates, location)
        p_altaz = p_coords.transform_to(coords.AltAz(obstime=dates, location=location))
        horizon = p_altaz.alt > 0*u.deg
        if horizon.any():
            ax.plot(p_altaz.az.deg[horizon], p_altaz.alt.deg[horizon], linestyle='--', label=f"{p}'s path")
            if horizon[-1]:
                ax.scatter(p_altaz.az.deg[-1], p_altaz.alt.deg[-1], label=p)

    ax.set_title(f'Planeten zichtbaar vanaf {obs_date}')
    ax.set_xlabel('Azimut (graden) North = 0, east = 90, south = 180, west = 270')
    ax.set_ylabel('Altitude (graden)')
    ax.legend()
    
    # Stuur de plot naar de website in plaats van plt.show()
    st.pyplot(fig)

except FileNotFoundError:
    st.error("Let op: Het bestand 'Database.txt' is niet gevonden. Zorg dat deze in dezelfde map staat als dit script!")
