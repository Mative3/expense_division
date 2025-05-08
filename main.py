from fasthtml.common import *
from fastapi import Request
from fastapi.responses import HTMLResponse
import numpy as np

app, rt = fast_app()

@rt('/')
def get():
    return Titled(
        Div(
            P('División de Gastos', style="margin-left: 60px;"),  # Título principal
            P('by Matías Vera-Rueda', style="font-size: 0.7em; margin-left: 80px; color: gray;")),  # Subtítulo
            Div(  # Contenedor para el texto y el dropdown
                "Número de Participantes: ",  # Texto descriptivo
                Select(  # Menú desplegable
                    *[Option(i, value=i) for i in range(3, 21)],  # Opciones del 1 al 10
                    id="participants",  # Atributo opcional (para formularios)
                    style="width: 70px; padding: 3px; margin-left: 10px;",  # Espaciado a la derecha del texto
                    onchange="updateInputs()"
                ),
                style="margin-top: 50px; margin-left: 70px;"  # Separación del subtítulo
            ),
            # Formulario con método POST y acción /calcular
            Form(
                Div(id="inputContainer"),  # Aquí aparecerán los campos dinámicos
                Button("Calcular Resultados", type="submit", 
                        style="margin-top: 20px; width: 200px; margin-left: 100px; padding: 8px 15px; background: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer;"),
                action="/calcular",
                method="post",
                id="mainForm"  # Añadido ID para referencia
            ),
            Script("""
                function updateInputs() {
                    const N = parseInt(document.getElementById("participants").value);
                    const container = document.getElementById("inputContainer");
                    container.innerHTML = ""; 

                    // Asegurarnos de incluir el campo num_participants en el formulario
                    const form = document.getElementById("mainForm");
                    const hiddenInput = document.createElement("input");
                    hiddenInput.type = "hidden";
                    hiddenInput.name = "num_participants";
                    hiddenInput.value = N;
                    form.appendChild(hiddenInput);            
    
                    for (let i = 1; i <= N; i++) {
                        const row = document.createElement("tr");
                        const div = document.createElement("div");
                        div.style.marginBottom = "10px";
                        
                        const textInput = document.createElement("input");
                        textInput.type = "text";
                        textInput.name = "nombre_" + i;
                        textInput.placeholder = "Nombre " + i;
                        textInput.style.marginRight = "10px";
                        textInput.style.marginLeft = "50px";
                        textInput.style.padding = "5px";
                        textInput.style.width = "30%";
                        
                        const numberInput = document.createElement("input");
                        numberInput.type = "real";
                        numberInput.name = "monto_" + i;
                        numberInput.placeholder = "Monto";
                        numberInput.style.padding = "5px";
                        numberInput.style.width = "30%";
                        
                        div.appendChild(textInput);
                        div.appendChild(numberInput);
                        container.appendChild(div);
                    }
                }
                // Llamar a updateInputs al cargar la página si hay un valor seleccionado
                document.addEventListener("DOMContentLoaded", function() {
                    const select = document.getElementById("participants");
                    if (select.value) {
                        updateInputs();
                    }
                });
            """)
        )

# Ruta para procesar los datos (POST)
@rt('/calcular', methods=['POST'])
async def calcular_resultados(request: Request):
    form_data = await request.form()
    
    # Debug: Imprimir todos los datos recibidos
    print("Datos recibidos:", form_data)
    
    try:
        num_participants = int(form_data["num_participants"])
    except KeyError:
        return HTMLResponse(content="""
            <html>
                <body>
                    <h2>Error</h2>
                    <p>No se recibió el número de participantes</p>
                    <a href="/">Volver</a>
                </body>
            </html>
        """, status_code=400)
    
    dict = {}
    for i in range(1, num_participants + 1):
        try:
            nombre = form_data.get(f"nombre_{i}", "")
            monto = float(form_data.get(f"monto_{i}", 0))
            dict.update({nombre: monto})
        except ValueError:
            return HTMLResponse(content=f"""
                <html>
                    <body>
                        <h2>Error</h2>
                        <p>Datos inválidos para el participante {i}</p>
                        <a href="/">Volver</a>
                    </body>
                </html>
            """, status_code=400)
    
    # --- Tu lógica de cálculo aquí ---
    N = len(dict)
    names = np.array(list(dict.keys()))
    values = np.array(list(dict.values()))
    total = np.sum(values)

    resultados = []

    n = total / N

    idx = np.argsort(values)[::-1]
    values = values[idx]
    names = names[idx]

    cuanto_puso = []
    for j in range(N):
        string1 = "{} puso ${:.2f}.".format(names[j],values[j])
        resultados.append(string1)    

    resultados.append("  ")
    resultados.append("El total gastado fue de ${:.2f}".format(total))
    resultados.append("  ")
    resultados.append("Cada uno debe poner ${:.2f}".format(n))
    resultados.append("  ")

    j,k = 0,0
    values = values - n
    while True:
        if j == N:
            break
        if values[j] >= 0:
            string2 = "{} no debe tranferir a nadie.".format(names[j])
            resultados.append(string2)
            resultados.append("  ")
            j += 1
        else:
            if values[k] >= abs(values[j]):
                string3 = "{} debe transferir ${:.2f} a {}.".format(names[j],abs(values[j]),names[k])
                resultados.append(string3)
                resultados.append("  ")
                values[k] -= abs(values[j])
                values[j] = 0
                j += 1
            else:
                if abs(values[j].item()) > 1e-3:
                    string4 = "{} debe transferir ${:.2f} a {}.".format(names[j],abs(values[k]),names[k])
                    resultados.append(string4)
                    values[j] += abs(values[k])
                    values[k] = 0
                    k += 1
                else:
                    break
 
    return HTMLResponse(content=f"""
        <html>
            <head>
                <title>Resultados</title>
                <style>
                    body {{
                        font-size: 28px;  /* Tamaño base para toda la página */
                    }}
                    h2 {{
                        font-size: 34px;  /* Tamaño específico para títulos */
                    }}
                    p {{
                        font-size: 26px;  /* Tamaño para párrafos */
                    }}
                </style>
            </head>
            <body>
                <h2>Resultados</h2>
                <p>{'<br>'.join(resultados)}</p>
                <a href="/" style="margin-top: 20px; display: inline-block;">Volver</a>
            </body>
        </html>
    """)

serve()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
