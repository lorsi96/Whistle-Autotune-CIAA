# Whistle-Autotune-CIAA

## Propuesta
El objetivo del trabajo consiste en corregir el _pitch_ de silbidos humanos
en tiempo real. Para ello se deasorrallará un programa en la EDU-CIAA capaz
de capturar silbidos mediante un micrófono electret y procesarlos de tal manera
que se pueda determinar la frecuencia de "tono musical" más cercano al silbido
detectado. Esta información se transmitirá a la PC a fines poder reconstruir
la melodía silbada "corregida" desde Python. 

## Diagrama en bloques del sistema
![uml](https://www.plantuml.com/plantuml/svg/XOynJiDG38RtTmhhxRa2QWXgnPQ1aSNASy5IdXqSHmoeX-4CtLXpCM8GKYKGdIpRt-zFtisEvaiTKyAbi49Z_FJipGrK7cmz7rKqJMZEpYhGtRSjl2M0YpLiS7lNRSCeqUN9TA0PAvEumgEGW3FLINDG_wmZlTy_11KrsdoxViml2nM4Gk0Xd8oALXOKfnpiLUZhK8yRuHH4GTSvfzF5QtqNZ_sclhC74Z8SU3tBZo7CVywXAVegMwf76qD_5JpO-dxaGTCffRGZAKiTFm40)


## Expectativas
* Procesar silbidos y poder _ajustarlos_ a distintas escalas (cromática, DO mayor). 
* Poder realizar la detección en la CIAA (tiempo real), y la reproducción en la PC.
* En principio se intentará que la reproducción sea también en tiempo real, pero puede resultar confuso para el usuario (silbar y escuchar el tono corregido a la vez impacta en la usabilidad). En su defecto, se almacenarán los datos en la PC (provenientes de la CIAA) y se reproduciran a posteriori. 

